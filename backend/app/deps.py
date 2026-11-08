from __future__ import annotations

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .security import BEARER_CHALLENGE, decode_access_token, password_fingerprint


def get_optional_user(
    request: Request, db: Session = Depends(get_db)
) -> User | None:
    header = request.headers.get("Authorization")
    if header is None or not header.strip():
        return None
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=401,
            detail="登录凭证无效，请重新登录",
            headers=BEARER_CHALLENGE,
        )
    payload = decode_access_token(token.strip())
    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as error:
        raise HTTPException(
            status_code=401,
            detail="登录凭证无效，请重新登录",
            headers=BEARER_CHALLENGE,
        ) from error
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="账号不存在，请重新登录",
            headers=BEARER_CHALLENGE,
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已停用，请联系管理员")
    if payload.get("pwd") != password_fingerprint(user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="登录状态已失效，请重新登录",
            headers=BEARER_CHALLENGE,
        )
    return user


def get_current_user(user: User | None = Depends(get_optional_user)) -> User:
    if user is None:
        raise HTTPException(
            status_code=401, detail="请先登录", headers=BEARER_CHALLENGE
        )
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user
