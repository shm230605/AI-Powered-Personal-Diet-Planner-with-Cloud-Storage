import base64
import hashlib
import hmac
import json
import os
import secrets
import time


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return f"{base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_text, digest_text = stored.split("$", 1)
        salt = base64.urlsafe_b64decode(salt_text)
        expected = base64.urlsafe_b64decode(digest_text)
    except (ValueError, TypeError):
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return hmac.compare_digest(actual, expected)


def _secret() -> str:
    if os.getenv("APP_ENV", "development") == "production" and not os.getenv("JWT_SECRET"):
        raise RuntimeError("JWT_SECRET must be set in production")
    return os.getenv("JWT_SECRET", "local-only-change-this-secret-before-deploying")


def create_token(user_id: str, expires_in: int = 43_200) -> str:
    encode = lambda value: base64.urlsafe_b64encode(value).rstrip(b"=").decode()
    header = encode(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = encode(json.dumps({"sub": user_id, "exp": int(time.time()) + expires_in}, separators=(",", ":")).encode())
    signing_input = f"{header}.{payload}"
    signature = encode(hmac.new(_secret().encode(), signing_input.encode(), hashlib.sha256).digest())
    return f"{signing_input}.{signature}"


def read_token(token: str) -> str | None:
    try:
        header, payload, signature = token.split(".")
        signing_input = f"{header}.{payload}"
        expected = hmac.new(_secret().encode(), signing_input.encode(), hashlib.sha256).digest()
        supplied = base64.urlsafe_b64decode(signature + "=" * (-len(signature) % 4))
        if not hmac.compare_digest(expected, supplied):
            return None
        decoded = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
        data = json.loads(decoded)
        if data.get("exp", 0) <= time.time():
            return None
        return data.get("sub")
    except (ValueError, TypeError, json.JSONDecodeError):
        return None