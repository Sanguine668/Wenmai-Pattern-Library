from __future__ import annotations


def test_health_reports_database_and_pattern_count(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "sqlite"
    assert body["patterns"] == 3


def test_stats_counts_seeded_library(client):
    body = client.get("/api/stats").json()
    assert body == {
        "total": 3,
        "withImages": 2,
        "trainable": 2,
        "discarded": 1,
        "noImage": 1,
    }


def test_browse_log_unique_index_is_installed(client):
    from sqlalchemy import text

    from app.database import engine

    with engine.connect() as connection:
        names = [
            row[0]
            for row in connection.execute(
                text(
                    "SELECT name FROM sqlite_master "
                    "WHERE type = 'index' AND tbl_name = 'browse_logs'"
                )
            )
        ]
    assert "uq_browse_logs_user_pattern" in names


def test_meta_groups_facets(client):
    body = client.get("/api/meta").json()
    motifs = {item["label"]: item["count"] for item in body["motifs"]}
    assert motifs == {"云纹": 1, "龙纹": 1, "花卉纹": 1}

    dynasties = {item["label"] for item in body["dynasties"]}
    assert dynasties == {"清", "明", "宋"}

    sources = {item["value"]: item["label"] for item in body["sources"]}
    assert sources["cleveland"] == "克利夫兰艺术博物馆"
    assert sources["met"] == "大都会艺术博物馆"
    assert sources["commons"] == "Wikimedia Commons"

    statuses = {item["label"]: item["count"] for item in body["statuses"]}
    assert statuses == {"confirmed": 2, "discarded": 1}
