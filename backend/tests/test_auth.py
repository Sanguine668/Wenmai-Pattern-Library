from __future__ import annotations

import hashlib

from sqlalchemy import select


def register(client, username="reader", password="reader123456", **extra):
    payload = {"username": username, "display_name": "测试读者", "password": password}
    payload.update(extra)
    return client.post("/api/auth/register", json=payload)


def test_register_returns_token_and_user(client):
    response = register(client, username="newreader", display_name="新读者")
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["token"]
    assert body["user"]["username"] == "newreader"
    assert body["user"]["displayName"] == "新读者"
    assert body["user"]["isAdmin"] is False
    assert "password" not in body["user"]


def test_register_duplicate_username_conflicts(client):
    assert register(client, username="dupe").status_code == 201
    assert register(client, username="dupe").status_code == 409


def test_register_duplicate_email_conflicts(client):
    assert register(client, username="mail-one", email="same@example.com").status_code == 201
    response = register(client, username="mail-two", email="same@example.com")
    assert response.status_code == 409


def test_register_rejects_short_password(client):
    assert register(client, username="shortpw", password="123").status_code == 422


def test_register_rejects_blank_username(client):
    assert register(client, username=" ").status_code == 422


def test_login_success_returns_token(client):
    register(client, username="loginuser", password="loginpass1")
    response = client.post(
        "/api/auth/login", json={"username": "loginuser", "password": "loginpass1"}
    )
    assert response.status_code == 200, response.text
    assert response.json()["user"]["username"] == "loginuser"


def test_login_wrong_password_is_401(client):
    register(client, username="loginuser", password="loginpass1")
    response = client.post(
        "/api/auth/login", json={"username": "loginuser", "password": "wrongpass"}
    )
    assert response.status_code == 401


def test_login_unknown_user_is_401(client):
    response = client.post(
        "/api/auth/login", json={"username": "nobody", "password": "whatever1"}
    )
    assert response.status_code == 401


def test_login_disabled_user_is_403(client):
    from app.database import SessionLocal
    from app.models import User

    register(client, username="sleepy", password="sleeppass1")
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == "sleepy"))
        user.is_active = False
        db.commit()
    response = client.post(
        "/api/auth/login", json={"username": "sleepy", "password": "sleeppass1"}
    )
    assert response.status_code == 403


def test_me_returns_current_user(client, user_token):
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 200
    assert response.json()["username"] == "reader"


def test_me_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401


def test_me_rejects_garbage_token(client):
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer nonsense"})
    assert response.status_code == 401


def test_demo_user_has_no_password_and_cannot_login(client):
    response = client.post(
        "/api/auth/login", json={"username": "demo", "password": "demo123456"}
    )
    assert response.status_code == 401


def test_legacy_sha256_login_is_upgraded_to_bcrypt(client):
    from app.database import SessionLocal
    from app.models import User

    legacy = hashlib.sha256("legacy-pass".encode("utf-8")).hexdigest()
    with SessionLocal() as db:
        db.add(
            User(
                username="legacyuser",
                display_name="旧账号",
                password_hash=legacy,
                is_admin=False,
                is_active=True,
            )
        )
        db.commit()

    response = client.post(
        "/api/auth/login", json={"username": "legacyuser", "password": "legacy-pass"}
    )
    assert response.status_code == 200, response.text
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == "legacyuser"))
        assert user.password_hash.startswith("$2")


def test_long_chinese_password_is_supported(client):
    password = "纹样密码" * 30
    assert register(client, username="longpw", password=password).status_code == 201
    response = client.post(
        "/api/auth/login", json={"username": "longpw", "password": password}
    )
    assert response.status_code == 200


def test_password_change_invalidates_existing_token(client):
    body = register(client, username="rotate", password="rotate123456").json()
    headers = {"Authorization": f"Bearer {body['token']}"}
    own_id = body["user"]["id"]
    changed = client.patch(
        f"/api/users/{own_id}",
        json={"password": "rotated123456"},
        headers=headers,
    )
    assert changed.status_code == 200
    assert client.get("/api/auth/me", headers=headers).status_code == 401
    assert (
        client.post(
            "/api/auth/login",
            json={"username": "rotate", "password": "rotated123456"},
        ).status_code
        == 200
    )


def test_disabled_user_token_is_rejected(client):
    from app.database import SessionLocal
    from app.models import User

    body = register(client, username="frozen", password="frozen123456").json()
    headers = {"Authorization": f"Bearer {body['token']}"}
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == "frozen"))
        user.is_active = False
        db.commit()
    assert client.get("/api/auth/me", headers=headers).status_code == 403


def test_login_attempts_are_rate_limited(client):
    username = "bruteforce"
    assert register(client, username=username, password="correct123456").status_code == 201
    for _ in range(5):
        response = client.post(
            "/api/auth/login", json={"username": username, "password": "wrong-pass"}
        )
        assert response.status_code == 401
    blocked = client.post(
        "/api/auth/login", json={"username": username, "password": "correct123456"}
    )
    assert blocked.status_code == 429
    assert blocked.headers.get("Retry-After")


def test_non_bearer_authorization_is_rejected(client):
    response = client.post(
        "/api/me/favorites/cleveland-101142",
        headers={"Authorization": "Basic YWJjOmRlZg=="},
    )
    assert response.status_code == 401


def test_empty_bearer_token_is_rejected(client):
    response = client.post(
        "/api/me/favorites/cleveland-101142",
        headers={"Authorization": "Bearer   "},
    )
    assert response.status_code == 401
