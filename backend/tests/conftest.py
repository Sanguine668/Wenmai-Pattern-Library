from __future__ import annotations

import os
import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

TEST_DB = Path(tempfile.gettempdir()) / f"wenmai-test-{uuid.uuid4().hex}.db"
SAMPLE_IMAGE_REL = "frontend/public/favicon.ico"

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"
os.environ["WENMAI_JWT_SECRET"] = "test-secret-do-not-use-in-production"
os.environ["WENMAI_ADMIN_USERNAME"] = "admin"
os.environ["WENMAI_ADMIN_PASSWORD"] = "admin123456"
os.environ["WENMAI_TOKEN_MINUTES"] = "60"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import delete  # noqa: E402


def seed_patterns(session_factory) -> None:
    from app.models import Pattern, PatternImage, Tag

    with session_factory() as db:
        patterns = [
            Pattern(
                id="cleveland-101142",
                catalog="CLEVELAND-101142",
                name="云纹 · 织锦",
                original_title="Book Cover",
                motif_type="云纹",
                dynasty="清",
                carrier="织锦",
                source="cleveland",
                source_id="101142",
                status="confirmed",
                has_image=True,
                colors_json=[{"name": "朱砂", "hex": "#B92C2A"}],
            ),
            Pattern(
                id="met-200",
                catalog="MET-200",
                name="龙纹 · 瓷器",
                original_title="Dragon Jar",
                motif_type="龙纹",
                dynasty="明",
                carrier="瓷器",
                source="met",
                source_id="200",
                status="discarded",
                has_image=False,
            ),
            Pattern(
                id="commons-300",
                catalog="COMMONS-300",
                name="花卉纹 · 壁画",
                original_title="Floral Mural",
                motif_type="花卉纹",
                dynasty="宋",
                carrier="壁画",
                source="commons",
                source_id="300",
                status="confirmed",
                has_image=True,
            ),
        ]
        db.add_all(patterns)
        db.flush()

        tag_defs = {
            ("motif", "云纹"),
            ("motif", "龙纹"),
            ("motif", "花卉纹"),
            ("dynasty", "清"),
            ("dynasty", "明"),
            ("dynasty", "宋"),
            ("carrier", "织锦"),
            ("carrier", "瓷器"),
            ("carrier", "壁画"),
            ("status", "confirmed"),
            ("status", "discarded"),
        }
        tags = {}
        for dimension, name in sorted(tag_defs):
            tag = Tag(dimension=dimension, name=name)
            db.add(tag)
            db.flush()
            tags[(dimension, name)] = tag

        patterns[0].tags.extend(
            [
                tags[("motif", "云纹")],
                tags[("dynasty", "清")],
                tags[("carrier", "织锦")],
                tags[("status", "confirmed")],
            ]
        )
        patterns[1].tags.extend(
            [
                tags[("motif", "龙纹")],
                tags[("dynasty", "明")],
                tags[("carrier", "瓷器")],
                tags[("status", "discarded")],
            ]
        )
        patterns[2].tags.extend(
            [
                tags[("motif", "花卉纹")],
                tags[("dynasty", "宋")],
                tags[("carrier", "壁画")],
                tags[("status", "confirmed")],
            ]
        )

        db.add_all(
            [
                PatternImage(
                    pattern_id="cleveland-101142",
                    relative_path=SAMPLE_IMAGE_REL,
                    alt_text="云纹 · 织锦",
                    is_primary=True,
                    sort_order=0,
                ),
                PatternImage(
                    pattern_id="commons-300",
                    relative_path=SAMPLE_IMAGE_REL,
                    alt_text="花卉纹 · 壁画",
                    is_primary=True,
                    sort_order=0,
                ),
            ]
        )
        db.commit()


def clear_data(session_factory) -> None:
    from app.models import (
        BrowseLog,
        Favorite,
        Pattern,
        PatternImage,
        Tag,
        User,
        pattern_tags,
    )

    with session_factory() as db:
        db.execute(delete(Favorite))
        db.execute(delete(BrowseLog))
        db.execute(delete(pattern_tags))
        db.execute(delete(PatternImage))
        db.execute(delete(Pattern))
        db.execute(delete(Tag))
        db.execute(delete(User).where(User.username.not_in(["demo", "admin"])))
        db.commit()


@pytest.fixture(scope="session")
def client():
    from app.database import Base, SessionLocal, engine
    from app.main import app

    assert "wenmai.db" not in str(engine.url), "测试不得连接正式数据库"
    Base.metadata.create_all(engine)
    seed_patterns(SessionLocal)
    with TestClient(app) as test_client:
        yield test_client


def pytest_sessionfinish(session, exitstatus):
    from app.database import engine

    try:
        engine.dispose()
    except Exception:
        pass
    for suffix in ("", "-wal", "-shm"):
        try:
            Path(f"{TEST_DB}{suffix}").unlink()
        except FileNotFoundError:
            pass
        except OSError:
            pass


@pytest.fixture(autouse=True)
def reset_data(client):
    from app.database import SessionLocal
    from app.importer import ensure_admin_user, ensure_demo_user

    clear_data(SessionLocal)
    seed_patterns(SessionLocal)
    with SessionLocal() as db:
        ensure_demo_user(db)
        ensure_admin_user(db)
    yield


def login(client, username: str = "admin", password: str = "admin123456") -> str:
    response = client.post(
        "/api/auth/login", json={"username": username, "password": password}
    )
    assert response.status_code == 200, response.text
    return response.json()["token"]


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_token(client) -> str:
    return login(client)


@pytest.fixture
def user_token(client) -> str:
    response = client.post(
        "/api/auth/register",
        json={
            "username": "reader",
            "display_name": "测试读者",
            "password": "reader123456",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["token"]
