from __future__ import annotations

import base64
import hashlib
import hmac
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import HTTPException

from .config import JWT_ALGORITHM, JWT_SECRET, TOKEN_MINUTES
from .models import User

LEGACY_HASH_LENGTH = 64
BEARER_CHALLENGE = {"WWW-Authenticate": "Bearer"}


def _bcrypt_input(password: str) -> bytes:
    """把任意长度密码折叠成 44 字节，避免 bcrypt 72 字节上限与中文截断问题。"""
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    return base64.b64encode(digest)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_bcrypt_input(password), bcrypt.gensalt()).decode("utf-8")


def _is_bcrypt(stored: str) -> bool:
    return stored.startswith(("$2a$", "$2b$", "$2y$"))


def verify_password(password: str, stored: str | None) -> bool:
    if not password or not stored:
        return False
    if _is_bcrypt(stored):
        try:
            return bcrypt.checkpw(_bcrypt_input(password), stored.encode("utf-8"))
        except ValueError:
            return False
    if len(stored) == LEGACY_HASH_LENGTH:
        legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(legacy, stored.lower())
    return False


def password_needs_rehash(stored: str | None) -> bool:
    return bool(stored) and not _is_bcrypt(stored)


def password_fingerprint(stored: str | None) -> str:
    return hashlib.sha256((stored or "").encode("utf-8")).hexdigest()[:12]


def create_access_token(user: User, expires_minutes: int | None = None) -> str:
    issued_at = datetime.now(timezone.utc)
    minutes = TOKEN_MINUTES if expires_minutes is None else expires_minutes
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "is_admin": bool(user.is_admin),
        "pwd": password_fingerprint(user.password_hash),
        "iat": issued_at,
        "exp": issued_at + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError as error:
        raise HTTPException(
            status_code=401,
            detail="登录已过期，请重新登录",
            headers=BEARER_CHALLENGE,
        ) from error
    except jwt.PyJWTError as error:
        raise HTTPException(
            status_code=401,
            detail="登录凭证无效，请重新登录",
            headers=BEARER_CHALLENGE,
        ) from error
    if not payload.get("sub"):
        raise HTTPException(
            status_code=401,
            detail="登录凭证无效，请重新登录",
            headers=BEARER_CHALLENGE,
        )
    return payload
