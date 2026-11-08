from __future__ import annotations

import hashlib

import pytest
from fastapi import HTTPException

from app.models import User
from app.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    password_needs_rehash,
    verify_password,
)


def build_user(**overrides) -> User:
    values = {
        "id": 7,
        "username": "reader",
        "display_name": "读者",
        "is_admin": False,
        "is_active": True,
    }
    values.update(overrides)
    return User(**values)


def test_bcrypt_hash_roundtrip():
    stored = hash_password("secret123")
    assert stored.startswith("$2")
    assert stored != "secret123"
    assert verify_password("secret123", stored) is True
    assert verify_password("wrong", stored) is False


def test_bcrypt_hash_is_salted():
    first = hash_password("same-password")
    second = hash_password("same-password")
    assert first != second
    assert verify_password("same-password", first)
    assert verify_password("same-password", second)


def test_legacy_sha256_still_verifies_and_is_flagged_for_rehash():
    legacy = hashlib.sha256("legacy-pass".encode("utf-8")).hexdigest()
    assert verify_password("legacy-pass", legacy) is True
    assert verify_password("nope", legacy) is False
    assert password_needs_rehash(legacy) is True


def test_bcrypt_hash_does_not_need_rehash():
    assert password_needs_rehash(hash_password("secret123")) is False


def test_missing_hash_never_matches():
    assert verify_password("anything", None) is False
    assert password_needs_rehash(None) is False


def test_token_roundtrip_carries_identity_claims():
    user = build_user(password_hash=hash_password("secret123"))
    token = create_access_token(user)
    payload = decode_access_token(token)
    assert payload["sub"] == "7"
    assert payload["username"] == "reader"
    assert payload["is_admin"] is False
    assert payload["pwd"] == hashlib.sha256(
        user.password_hash.encode("utf-8")
    ).hexdigest()[:12]
    assert payload["exp"] > payload["iat"]


def test_tampered_token_is_rejected():
    token = create_access_token(build_user())
    tampered = token[:-2] + ("aa" if token[-2:] != "aa" else "bb")
    with pytest.raises(HTTPException) as excinfo:
        decode_access_token(tampered)
    assert excinfo.value.status_code == 401


def test_garbage_token_is_rejected():
    with pytest.raises(HTTPException) as excinfo:
        decode_access_token("not-a-token")
    assert excinfo.value.status_code == 401


def test_expired_token_is_rejected():
    token = create_access_token(build_user(), expires_minutes=-1)
    with pytest.raises(HTTPException) as excinfo:
        decode_access_token(token)
    assert excinfo.value.status_code == 401


def test_token_without_expiry_is_rejected():
    import jwt

    from app import security

    token = jwt.encode(
        {"sub": "7", "username": "reader", "is_admin": False},
        security.JWT_SECRET,
        algorithm="HS256",
    )
    with pytest.raises(HTTPException) as excinfo:
        decode_access_token(token)
    assert excinfo.value.status_code == 401


def test_token_signed_with_other_secret_is_rejected(monkeypatch):
    import jwt

    from app import security

    token = jwt.encode(
        {"sub": "1", "username": "x", "is_admin": False, "exp": 9999999999},
        "another-secret-key-with-enough-length",
        algorithm="HS256",
    )
    with pytest.raises(HTTPException) as excinfo:
        security.decode_access_token(token)
    assert excinfo.value.status_code == 401
