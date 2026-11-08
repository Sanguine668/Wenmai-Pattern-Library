from __future__ import annotations

from sqlalchemy import select

from conftest import auth_header


def register(client, username="second", password="second123456", display="第二读者"):
    return client.post(
        "/api/auth/register",
        json={"username": username, "display_name": display, "password": password},
    )


def find_user_id(client, admin_token, username):
    users = client.get("/api/users", headers=auth_header(admin_token)).json()
    return next(item["id"] for item in users if item["username"] == username)


def pattern_payload(name="测试纹样"):
    return {
        "name": name,
        "motif_type": "云纹",
        "dynasty": "清",
        "carrier": "瓷器",
        "source": "manual",
        "source_id": "rbac-1",
    }


def test_anonymous_cannot_create_pattern(client):
    response = client.post("/api/patterns", json=pattern_payload())
    assert response.status_code == 401


def test_regular_user_cannot_create_pattern(client, user_token):
    response = client.post(
        "/api/patterns", json=pattern_payload(), headers=auth_header(user_token)
    )
    assert response.status_code == 403


def test_admin_can_create_update_and_delete_pattern(client, admin_token):
    headers = auth_header(admin_token)
    created = client.post("/api/patterns", json=pattern_payload(), headers=headers)
    assert created.status_code == 201, created.text
    pattern_id = created.json()["id"]

    updated = client.patch(
        f"/api/patterns/{pattern_id}", json={"name": "改名纹样"}, headers=headers
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "改名纹样"

    deleted = client.delete(f"/api/patterns/{pattern_id}", headers=headers)
    assert deleted.status_code == 204
    assert client.get(f"/api/patterns/{pattern_id}").status_code == 404


def test_user_list_requires_admin(client, user_token, admin_token):
    assert client.get("/api/users").status_code == 401
    assert (
        client.get("/api/users", headers=auth_header(user_token)).status_code == 403
    )
    response = client.get("/api/users", headers=auth_header(admin_token))
    assert response.status_code == 200
    usernames = {item["username"] for item in response.json()}
    assert {"demo", "admin"} <= usernames


def test_user_can_read_self_but_not_others(client, user_token, admin_token):
    own_id = client.get("/api/auth/me", headers=auth_header(user_token)).json()["id"]
    other_id = find_user_id(client, admin_token, "admin")
    assert (
        client.get(f"/api/users/{own_id}", headers=auth_header(user_token)).status_code
        == 200
    )
    assert (
        client.get(f"/api/users/{other_id}", headers=auth_header(user_token)).status_code
        == 403
    )


def test_user_can_update_own_display_name(client, user_token):
    own_id = client.get("/api/auth/me", headers=auth_header(user_token)).json()["id"]
    response = client.patch(
        f"/api/users/{own_id}",
        json={"display_name": "改名读者"},
        headers=auth_header(user_token),
    )
    assert response.status_code == 200
    assert response.json()["displayName"] == "改名读者"


def test_user_cannot_promote_or_deactivate_self(client, user_token):
    own_id = client.get("/api/auth/me", headers=auth_header(user_token)).json()["id"]
    for payload in ({"is_admin": True}, {"is_active": False}):
        response = client.patch(
            f"/api/users/{own_id}", json=payload, headers=auth_header(user_token)
        )
        assert response.status_code == 403
    me = client.get("/api/auth/me", headers=auth_header(user_token)).json()
    assert me["isAdmin"] is False
    assert me["isActive"] is True


def test_admin_can_update_other_user(client, admin_token, user_token):
    target_id = client.get("/api/auth/me", headers=auth_header(user_token)).json()["id"]
    response = client.patch(
        f"/api/users/{target_id}",
        json={"display_name": "管理员改名", "is_active": True},
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200
    assert response.json()["displayName"] == "管理员改名"


def test_cannot_delete_self(client, admin_token):
    admin_id = client.get("/api/auth/me", headers=auth_header(admin_token)).json()["id"]
    response = client.delete(f"/api/users/{admin_id}", headers=auth_header(admin_token))
    assert response.status_code == 400


def test_cannot_demote_self(client, admin_token):
    admin_id = client.get("/api/auth/me", headers=auth_header(admin_token)).json()["id"]
    response = client.patch(
        f"/api/users/{admin_id}",
        json={"is_admin": False},
        headers=auth_header(admin_token),
    )
    assert response.status_code == 400
    me = client.get("/api/auth/me", headers=auth_header(admin_token)).json()
    assert me["isAdmin"] is True


def test_admin_cannot_create_duplicate_email(client, admin_token):
    headers = auth_header(admin_token)
    payload = {
        "username": "admin-created-one",
        "display_name": "管理员新建",
        "password": "created123456",
        "email": "duplicate@example.com",
    }
    first = client.post("/api/users", json=payload, headers=headers)
    assert first.status_code == 201, first.text
    second = client.post(
        "/api/users",
        json={**payload, "username": "admin-created-two"},
        headers=headers,
    )
    assert second.status_code == 409


def test_admin_can_clear_email_for_multiple_users(client, admin_token):
    headers = auth_header(admin_token)
    created_ids = []
    for index in (1, 2):
        created = client.post(
            "/api/users",
            json={
                "username": f"no-mail-{index}",
                "display_name": f"无邮箱用户{index}",
                "password": "nomail123456",
            },
            headers=headers,
        )
        assert created.status_code == 201, created.text
        created_ids.append(created.json()["id"])
    for user_id in created_ids:
        response = client.patch(
            f"/api/users/{user_id}", json={"email": ""}, headers=headers
        )
        assert response.status_code == 200, response.text
        assert response.json()["email"] == ""


def test_admin_cannot_set_duplicate_email_on_update(client, admin_token):
    headers = auth_header(admin_token)
    first = client.post(
        "/api/users",
        json={
            "username": "mail-owner",
            "display_name": "邮箱拥有者",
            "password": "mailowner123",
            "email": "owner@example.com",
        },
        headers=headers,
    )
    second = client.post(
        "/api/users",
        json={
            "username": "mail-other",
            "display_name": "另一用户",
            "password": "mailother123",
        },
        headers=headers,
    )
    assert first.status_code == 201 and second.status_code == 201
    response = client.patch(
        f"/api/users/{second.json()['id']}",
        json={"email": "owner@example.com"},
        headers=headers,
    )
    assert response.status_code == 409


def test_create_user_requires_password(client, admin_token):
    response = client.post(
        "/api/users",
        json={"username": "no-password", "display_name": "无密码用户"},
        headers=auth_header(admin_token),
    )
    assert response.status_code == 422


def test_demo_account_cannot_be_edited_as_system_account(client, admin_token):
    demo_id = find_user_id(client, admin_token, "demo")
    headers = auth_header(admin_token)
    for payload in ({"is_admin": True}, {"is_active": False}, {"password": "hacked123456"}):
        response = client.patch(f"/api/users/{demo_id}", json=payload, headers=headers)
        assert response.status_code == 400, payload


def test_demo_account_cannot_be_deleted(client, admin_token):
    demo_id = find_user_id(client, admin_token, "demo")
    assert (
        client.delete(f"/api/users/{demo_id}", headers=auth_header(admin_token)).status_code
        == 400
    )


def test_demo_account_stays_non_admin(client):
    from app.database import SessionLocal
    from app.models import User
    from app.security import verify_password

    with SessionLocal() as db:
        demo = db.scalar(select(User).where(User.username == "demo"))
        assert demo is not None
        assert demo.is_admin is False
        assert demo.password_hash is None
        assert verify_password("anything", demo.password_hash) is False
