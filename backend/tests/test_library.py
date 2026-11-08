from __future__ import annotations

from sqlalchemy import func, select

from conftest import auth_header


def user_id_of(client, token):
    return client.get("/api/auth/me", headers=auth_header(token)).json()["id"]


def demo_id_of(client, admin_token):
    users = client.get("/api/users", headers=auth_header(admin_token)).json()
    return next(item["id"] for item in users if item["username"] == "demo")


def favorite_ids(client, token=None):
    headers = auth_header(token) if token else {}
    response = client.get("/api/me/favorites", headers=headers)
    assert response.status_code == 200, response.text
    return [item["id"] for item in response.json()["items"]]


def test_guest_favorites_fall_back_to_demo(client, admin_token, user_token):
    demo_id = demo_id_of(client, admin_token)
    own_id = user_id_of(client, user_token)
    assert demo_id != own_id

    assert client.post("/api/me/favorites/cleveland-101142").status_code == 201
    assert (
        client.post(
            "/api/me/favorites/met-200", headers=auth_header(user_token)
        ).status_code
        == 201
    )

    assert favorite_ids(client) == ["cleveland-101142"]
    assert favorite_ids(client, user_token) == ["met-200"]


def test_guest_can_remove_favorite(client):
    assert client.post("/api/me/favorites/cleveland-101142").status_code == 201
    assert client.delete("/api/me/favorites/cleveland-101142").status_code == 204
    assert favorite_ids(client) == []


def test_favorite_is_idempotent(client):
    assert client.post("/api/me/favorites/cleveland-101142").status_code == 201
    assert client.post("/api/me/favorites/cleveland-101142").status_code == 201
    assert favorite_ids(client) == ["cleveland-101142"]


def test_legacy_favorite_routes_require_login_and_self(client, admin_token, user_token):
    own_id = user_id_of(client, user_token)
    demo_id = demo_id_of(client, admin_token)

    assert client.get(f"/api/users/{own_id}/favorites").status_code == 401
    assert (
        client.get(
            f"/api/users/{demo_id}/favorites", headers=auth_header(user_token)
        ).status_code
        == 403
    )
    assert (
        client.get(
            f"/api/users/{own_id}/favorites", headers=auth_header(user_token)
        ).status_code
        == 200
    )


def test_admin_can_read_any_user_favorites(client, admin_token, user_token):
    own_id = user_id_of(client, user_token)
    response = client.get(
        f"/api/users/{own_id}/favorites", headers=auth_header(admin_token)
    )
    assert response.status_code == 200


def test_guest_view_history_is_deduplicated(client):
    from app.database import SessionLocal
    from app.models import BrowseLog

    assert client.post("/api/me/views/cleveland-101142").status_code == 201
    assert client.post("/api/me/views/cleveland-101142").status_code == 201

    history = client.get("/api/me/history").json()["items"]
    assert [item["id"] for item in history] == ["cleveland-101142"]

    with SessionLocal() as db:
        count = db.scalar(
            select(func.count()).select_from(BrowseLog).where(
                BrowseLog.pattern_id == "cleveland-101142"
            )
        )
        assert count == 1


def test_history_limit_is_applied(client):
    client.post("/api/me/views/cleveland-101142")
    client.post("/api/me/views/commons-300")
    history = client.get("/api/me/history?limit=1").json()["items"]
    assert len(history) == 1
    assert history[0]["id"] == "commons-300"


def test_logged_in_history_is_separate_from_guest(client, user_token):
    client.post("/api/me/views/cleveland-101142")
    client.post("/api/me/views/commons-300", headers=auth_header(user_token))

    guest_history = client.get("/api/me/history").json()["items"]
    user_history = client.get(
        "/api/me/history", headers=auth_header(user_token)
    ).json()["items"]
    assert [item["id"] for item in guest_history] == ["cleveland-101142"]
    assert [item["id"] for item in user_history] == ["commons-300"]


def test_legacy_view_route_requires_self_or_admin(client, user_token):
    own_id = user_id_of(client, user_token)
    assert client.post(f"/api/users/{own_id}/views/cleveland-101142").status_code == 401
    assert (
        client.post(
            f"/api/users/{own_id}/views/cleveland-101142",
            headers=auth_header(user_token),
        ).status_code
        == 201
    )
