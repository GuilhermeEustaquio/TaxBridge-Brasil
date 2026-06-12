import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import get_settings

settings = get_settings()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def _create_token(subject: str, organization_id: str, role: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "org": organization_id,
        "role": role,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_token_pair(user_id: str, organization_id: str, role: str) -> dict[str, str]:
    return {
        "access_token": _create_token(
            user_id, organization_id, role, "access", timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        ),
        "refresh_token": _create_token(
            user_id, organization_id, role, "refresh", timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        ),
        "token_type": "bearer",
    }


def decode_token(token: str, expected_type: str = "access") -> dict[str, Any] | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
    if payload.get("type") != expected_type:
        return None
    return payload


def generate_api_key() -> tuple[str, str, str]:
    """Retorna (segredo_completo, prefixo, sha256). O segredo é exibido uma única vez."""
    secret = f"tbk_{secrets.token_urlsafe(32)}"
    return secret, secret[:12], hashlib.sha256(secret.encode()).hexdigest()
