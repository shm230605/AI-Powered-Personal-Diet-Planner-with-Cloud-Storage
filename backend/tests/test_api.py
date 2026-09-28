import os
import tempfile
import unittest
import json
from pathlib import Path
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

from app import storage
from app.database import Base, get_db, make_engine
from app.main import app


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        url = URL.create("sqlite", database=str(Path(self.temp_dir.name) / "test.db"))
        self.engine = make_engine(url)
        Base.metadata.create_all(bind=self.engine)
        sessions = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)

        def override_db():
            with sessions() as session:
                yield session

        app.dependency_overrides[get_db] = override_db
        self.storage_patch = patch.object(storage, "LOCAL_ROOT", Path(self.temp_dir.name) / "uploads")
        self.storage_patch.start()
        self.client = TestClient(app)
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        app.dependency_overrides.clear()
        self.storage_patch.stop()
        self.engine.dispose()
        self.temp_dir.cleanup()

    def register(self, email):
        response = self.client.post("/api/auth/register", json={"name": "Demo User", "email": email, "password": "demo-password-123"})
        self.assertEqual(response.status_code, 201)
        result = response.json()
        return result, {"Authorization": f"Bearer {result['access_token']}"}

    def test_registration_login_duplicate_and_protected_profile(self):
        result, headers = self.register("demo@example.test")
        self.assertEqual(result["user"]["email"], "demo@example.test")
        duplicate = self.client.post("/api/auth/register", json={"name": "Again", "email": "DEMO@example.test", "password": "demo-password-123"})
        self.assertEqual(duplicate.status_code, 409)
        login = self.client.post("/api/auth/login", json={"email": "DEMO@example.test", "password": "demo-password-123"})
        self.assertEqual(login.status_code, 200)
        invalid_login = self.client.post("/api/auth/login", json={"email": "demo@example.test", "password": "wrong-password"})
        self.assertEqual(invalid_login.status_code, 401)
        self.assertEqual(self.client.get("/api/profile").status_code, 401)
        self.assertEqual(self.client.get("/api/profile", headers=headers).json()["name"], "Demo User")

    def test_vegan_plan_respects_allergies_and_is_saved(self):
        _, headers = self.register("vegan@example.test")
        profile = {
            "name": "Demo Vegan", "age": 24, "height_cm": 168, "weight_kg": 64,
            "activity_level": "moderate", "dietary_preference": "vegan", "goal": "fitness",
            "allergies": ["sesame"], "preferences": "simple meals",
        }
        self.assertEqual(self.client.put("/api/profile", json=profile, headers=headers).status_code, 200)
        created = self.client.post("/api/plans", headers=headers)
        self.assertEqual(created.status_code, 201)
        plan = created.json()
        self.assertEqual(plan["generation_mode"], "local-rules")
        self.assertTrue(plan["disclaimer"].startswith("General wellness example"))
        for meal_name in ("breakfast", "lunch", "snack", "dinner"):
            self.assertNotIn("sesame", plan[meal_name]["description"].lower())
            self.assertNotIn("chicken", plan[meal_name]["name"].lower())
            self.assertNotIn("salmon", plan[meal_name]["name"].lower())
        self.assertEqual(self.client.get("/api/plans", headers=headers).json()[0]["id"], plan["id"])

    def test_user_cannot_read_or_delete_another_users_plan(self):
        _, alice = self.register("alice@example.test")
        _, bob = self.register("bob@example.test")
        plan = self.client.post("/api/plans", headers=alice).json()
        self.assertEqual(self.client.get(f"/api/plans/{plan['id']}", headers=bob).status_code, 404)
        self.assertEqual(self.client.delete(f"/api/plans/{plan['id']}", headers=bob).status_code, 404)
        self.assertEqual(self.client.get(f"/api/plans/{plan['id']}", headers=alice).status_code, 200)

    def test_upload_download_validation_and_file_isolation(self):
        _, alice = self.register("file-owner@example.test")
        _, bob = self.register("another-user@example.test")
        image = b"\x89PNG\r\n\x1a\n" + b"synthetic demo image"
        uploaded = self.client.post("/api/files", headers=alice, files={"file": ("meal\r\n.png", image, "image/png")})
        self.assertEqual(uploaded.status_code, 201)
        self.assertEqual(uploaded.json()["filename"], "meal_0D_0A.png")
        file_id = uploaded.json()["id"]
        self.assertEqual(self.client.get(f"/api/files/{file_id}/download", headers=alice).content, image)
        self.assertEqual(self.client.get(f"/api/files/{file_id}/download", headers=bob).status_code, 404)
        self.assertEqual(self.client.get("/api/files", headers=bob).json(), [])
        bad_file = self.client.post("/api/files", headers=alice, files={"file": ("bad.txt", b"no", "text/plain")})
        self.assertEqual(bad_file.status_code, 415)
        bad_signature = self.client.post("/api/files", headers=alice, files={"file": ("fake.png", b"not a png", "image/png")})
        self.assertEqual(bad_signature.status_code, 415)

    def test_optional_ai_provider_failure_uses_local_rules(self):
        _, headers = self.register("fallback@example.test")
        with patch.dict(os.environ, {"AI_API_URL": "https://provider.example.test/chat/completions", "AI_API_KEY": "test-key"}):
            with patch("app.diet_engine.httpx.post", side_effect=OSError("provider unavailable")):
                plan = self.client.post("/api/plans", headers=headers).json()
        self.assertEqual(plan["generation_mode"], "local-rules-fallback")

    def test_valid_ai_response_is_structured_and_summarized(self):
        _, headers = self.register("ai@example.test")
        profile = {"name": "Demo", "dietary_preference": "vegan", "allergies": ["sesame"]}
        self.client.put("/api/profile", json=profile, headers=headers)
        meals = {
            "breakfast": {"name": "Apple oats", "description": "Oats and apple", "calories": 350},
            "lunch": {"name": "Lentil greens", "description": "Lentils and greens", "calories": 500},
            "snack": {"name": "Fresh pear", "description": "Pear", "calories": 180},
            "dinner": {"name": "Roasted vegetables", "description": "Vegetables and quinoa", "calories": 520},
        }
        response = Mock()
        response.json.return_value = {"choices": [{"message": {"content": json.dumps(meals)}}]}
        with patch.dict(os.environ, {"AI_API_URL": "https://provider.example.test/chat/completions", "AI_API_KEY": "test-key"}):
            with patch("app.diet_engine.httpx.post", return_value=response):
                plan_response = self.client.post("/api/plans", headers=headers)
        self.assertEqual(plan_response.status_code, 201)
        plan = plan_response.json()
        self.assertEqual(plan["generation_mode"], "optional-ai")
        self.assertEqual(plan["nutrition_summary"]["approximate_calories"], 1550)
        self.assertIn("protein", plan["nutrition_summary"]["approximate_macros_g"])


if __name__ == "__main__":
    unittest.main()
