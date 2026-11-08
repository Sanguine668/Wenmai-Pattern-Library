from __future__ import annotations


def ids_of(response) -> list[str]:
    return [item["id"] for item in response.json()["items"]]


def test_default_list_is_paginated_and_curated(client):
    response = client.get("/api/patterns")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["limit"] == 24
    assert body["offset"] == 0
    assert ids_of(response) == ["cleveland-101142", "commons-300", "met-200"]


def test_pagination_slices_the_catalogue(client):
    response = client.get("/api/patterns?limit=1&offset=1")
    assert ids_of(response) == ["commons-300"]


def test_limit_above_maximum_is_rejected(client):
    assert client.get("/api/patterns?limit=101").status_code == 422


def test_keyword_searches_name_and_original_title(client):
    assert ids_of(client.get("/api/patterns?keyword=云纹")) == ["cleveland-101142"]
    assert ids_of(client.get("/api/patterns?keyword=Dragon")) == ["met-200"]
    assert ids_of(client.get("/api/patterns?keyword=101142")) == ["cleveland-101142"]
    assert ids_of(client.get("/api/patterns?keyword=不存在")) == []


def test_filters_combine(client):
    assert ids_of(client.get("/api/patterns?motif=云纹")) == ["cleveland-101142"]
    assert ids_of(client.get("/api/patterns?dynasty=明")) == ["met-200"]
    assert ids_of(client.get("/api/patterns?carrier=瓷器")) == ["met-200"]
    assert ids_of(client.get("/api/patterns?source=commons")) == ["commons-300"]
    assert ids_of(client.get("/api/patterns?status=discarded")) == ["met-200"]
    assert ids_of(client.get("/api/patterns?has_image=true")) == [
        "cleveland-101142",
        "commons-300",
    ]
    assert ids_of(client.get("/api/patterns?has_image=false")) == ["met-200"]
    assert ids_of(client.get("/api/patterns?motif=云纹&dynasty=明")) == []


def test_sort_title(client):
    assert ids_of(client.get("/api/patterns?sort=title")) == [
        "cleveland-101142",
        "commons-300",
        "met-200",
    ]


def test_detail_includes_images_colors_and_related(client):
    body = client.get("/api/patterns/cleveland-101142").json()
    assert body["name"] == "云纹 · 织锦"
    assert body["source"] == "克利夫兰艺术博物馆"
    assert body["image"].startswith("/api/images/")
    assert body["imageCount"] == 1
    assert body["colors"][0]["name"] == "朱砂"
    assert isinstance(body["related"], list)
    assert all(item["id"] != "cleveland-101142" for item in body["related"])


def test_detail_missing_pattern_is_404(client):
    assert client.get("/api/patterns/not-exist").status_code == 404


def test_image_endpoint_serves_real_file(client):
    detail = client.get("/api/patterns/cleveland-101142").json()
    response = client.get(detail["image"])
    assert response.status_code == 200
    assert len(response.content) > 0


def test_image_endpoint_missing_image_is_404(client):
    assert client.get("/api/images/999999").status_code == 404


def test_tags_endpoint_returns_usage_counts(client):
    rows = client.get("/api/tags").json()
    assert rows
    motifs = {
        row["name"]: row["count"] for row in rows if row["dimension"] == "motif"
    }
    assert motifs == {"云纹": 1, "龙纹": 1, "花卉纹": 1}


def test_keyword_searches_motif_and_carrier_labels(client, admin_token):
    created = client.post(
        "/api/patterns",
        json={
            "name": "测试书衣",
            "motif_type": "云纹",
            "carrier": "玉器",
            "dynasty": "清",
            "source": "manual",
            "source_id": "keyword-labels",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert created.status_code == 201, created.text
    created_id = created.json()["id"]
    assert created_id in ids_of(client.get("/api/patterns?keyword=云纹"))
    assert created_id in ids_of(client.get("/api/patterns?keyword=玉器"))
