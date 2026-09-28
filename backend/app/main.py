import os
import re
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import diet_engine, storage
from .database import Base, engine, get_db
from .models import Plan, StoredFile, User
from .security import create_token, hash_password, read_token, verify_password

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGES = {"image/jpeg": (b"\xff\xd8\xff", ".jpg"), "image/png": (b"\x89PNG\r\n\x1a\n", ".png"), "image/webp": (b"RIFF", ".webp")}
bearer = HTTPBearer(auto_error=False)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if os.getenv("APP_ENV") == "production" and not os.getenv("JWT_SECRET"):
        raise RuntimeError("JWT_SECRET must be configured before production startup")
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Goodplate API", version="1.0.0", description="Demo wellness meal planner API", lifespan=lifespan)
origins = [origin.strip() for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if origin.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False, allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], allow_headers=["Authorization", "Content-Type"])


class Credentials(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=10, max_length=128)
    name: str = Field(min_length=1, max_length=80)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", normalized):
            raise ValueError("Enter a valid email address")
        return normalized

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name is required")
        return value


class LoginInput(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", normalized):
            raise ValueError("Enter a valid email address")
        return normalized


class ProfileInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=80)
    age: int | None = Field(default=None, ge=18, le=100)
    height_cm: float | None = Field(default=None, ge=120, le=230)
    weight_kg: float | None = Field(default=None, ge=35, le=300)
    activity_level: str = "light"
    dietary_preference: str = "omnivore"
    goal: str = "balanced"
    allergies: list[str] = Field(default_factory=list, max_length=10)
    preferences: str = Field(default="", max_length=300)

    @field_validator("activity_level")
    @classmethod
    def valid_activity(cls, value: str) -> str:
        if value not in {"low", "light", "moderate", "high"}:
            raise ValueError("Choose a listed activity level")
        return value

    @field_validator("dietary_preference")
    @classmethod
    def valid_diet(cls, value: str) -> str:
        if value not in {"omnivore", "vegetarian", "vegan"}:
            raise ValueError("Choose a listed dietary preference")
        return value

    @field_validator("goal")
    @classmethod
    def valid_goal(cls, value: str) -> str:
        if value not in {"balanced", "weight-management", "fitness"}:
            raise ValueError("Choose a listed general wellness goal")
        return value

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("allergies")
    @classmethod
    def normalize_allergies(cls, value: list[str]) -> list[str]:
        allowed = {"dairy", "lactose", "nuts", "peanut", "gluten", "sesame", "soy", "fish", "egg"}
        normalized = list(dict.fromkeys(item.strip().lower() for item in value))
        if any(item not in allowed for item in normalized):
            raise ValueError("Use supported allergy labels: dairy, nuts, gluten, sesame, soy, fish, egg")
        return normalized


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    user_id = read_token(credentials.credentials) if credentials else None
    user = db.get(User, user_id) if user_id else None
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in to continue", headers={"WWW-Authenticate": "Bearer"})
    return user


def _user_json(user: User) -> dict:
    return {"id": user.id, "name": user.name, "email": user.email, "profile": user.profile or {}, "created_at": user.created_at.isoformat()}


def _plan_json(plan: Plan) -> dict:
    return {"id": plan.id, "created_at": plan.created_at.isoformat(), **plan.data}


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "goodplate-api"}


@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
def register(body: Credentials, db: Session = Depends(get_db)) -> dict:
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(email=body.email, name=body.name, password_hash=hash_password(body.password), profile={})
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"access_token": create_token(user.id), "token_type": "bearer", "user": _user_json(user)}


@app.post("/api/auth/login")
def login(body: LoginInput, db: Session = Depends(get_db)) -> dict:
    user = db.scalar(select(User).where(User.email == body.email))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email or password is incorrect")
    return {"access_token": create_token(user.id), "token_type": "bearer", "user": _user_json(user)}


@app.post("/api/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(_: User = Depends(current_user)) -> Response:
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/profile")
def get_profile(user: User = Depends(current_user)) -> dict:
    return _user_json(user)


@app.put("/api/profile")
def save_profile(body: ProfileInput, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    user.name = body.name
    user.profile = body.model_dump()
    db.commit()
    db.refresh(user)
    return _user_json(user)


@app.post("/api/plans", status_code=status.HTTP_201_CREATED)
def create_plan(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    try:
        data = diet_engine.generate_plan(user.profile or {})
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    plan = Plan(user_id=user.id, data=data)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return _plan_json(plan)


@app.get("/api/plans")
def list_plans(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[dict]:
    plans = db.scalars(select(Plan).where(Plan.user_id == user.id).order_by(Plan.created_at.desc())).all()
    return [_plan_json(plan) for plan in plans]


@app.get("/api/plans/{plan_id}")
def get_plan(plan_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    plan = db.scalar(select(Plan).where(Plan.id == plan_id, Plan.user_id == user.id))
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return _plan_json(plan)


@app.delete("/api/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(plan_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> Response:
    plan = db.scalar(select(Plan).where(Plan.id == plan_id, Plan.user_id == user.id))
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    db.delete(plan)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/api/files", status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...), user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    content_type = file.content_type or ""
    image_spec = ALLOWED_IMAGES.get(content_type)
    if not image_spec:
        raise HTTPException(status_code=415, detail="Upload a JPEG, PNG or WebP meal image")
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Images must be 5 MB or smaller")
    signature, extension = image_spec
    if not content.startswith(signature) or (content_type == "image/webp" and content[8:12] != b"WEBP"):
        raise HTTPException(status_code=415, detail="File content does not match its image type")
    file_id = str(uuid4())
    key = f"{user.id}/{file_id}{extension}"
    safe_name = re.sub(r"[^A-Za-z0-9._ -]", "_", Path(file.filename or f"meal{extension}").name)[:255]
    try:
        storage.put_object(key, content, content_type)
    except Exception as error:
        raise HTTPException(status_code=503, detail="File storage is temporarily unavailable") from error
    record = StoredFile(id=file_id, user_id=user.id, filename=safe_name, object_key=key, content_type=content_type, size_bytes=len(content))
    db.add(record)
    db.commit()
    return {"id": record.id, "filename": record.filename, "content_type": record.content_type, "size_bytes": record.size_bytes, "created_at": record.created_at.isoformat()}


@app.get("/api/files")
def list_files(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[dict]:
    files = db.scalars(select(StoredFile).where(StoredFile.user_id == user.id).order_by(StoredFile.created_at.desc())).all()
    return [{"id": item.id, "filename": item.filename, "content_type": item.content_type, "size_bytes": item.size_bytes, "created_at": item.created_at.isoformat()} for item in files]


@app.get("/api/files/{file_id}/download")
def download_file(file_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> Response:
    item = db.scalar(select(StoredFile).where(StoredFile.id == file_id, StoredFile.user_id == user.id))
    if not item:
        raise HTTPException(status_code=404, detail="File not found")
    try:
        content = storage.get_object(item.object_key)
    except Exception as error:
        raise HTTPException(status_code=503, detail="File storage is temporarily unavailable") from error
    return Response(content, media_type=item.content_type, headers={"Content-Disposition": f'attachment; filename="{item.filename}"'})


@app.delete("/api/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(file_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> Response:
    item = db.scalar(select(StoredFile).where(StoredFile.id == file_id, StoredFile.user_id == user.id))
    if not item:
        raise HTTPException(status_code=404, detail="File not found")
    try:
        storage.delete_object(item.object_key)
    except FileNotFoundError:
        pass
    except Exception as error:
        raise HTTPException(status_code=503, detail="File storage is temporarily unavailable") from error
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)