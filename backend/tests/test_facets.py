from __future__ import annotations


def facet_map(payload, key):
    return {item["label"]: item["count"] for item in payload[key]}


def test_facets_without_filters_return_global_counts(client):
    body = client.get("/api/facets").json()
    assert facet_map(body, "motifs") == {"云纹": 1, "龙纹": 1, "花卉纹": 1}
    assert facet_map(body, "dynasties") == {"清": 1, "明": 1, "宋": 1}
    assert facet_map(body, "carriers") == {"织锦": 1, "瓷器": 1, "壁画": 1}
    assert body["total"] == 3


def test_facets_with_dynasty_filter_narrow_other_dimensions(client):
    body = client.get("/api/facets?dynasty=明").json()
    assert facet_map(body, "motifs") == {"云纹": 0, "龙纹": 1, "花卉纹": 0}
    assert facet_map(body, "carriers") == {"织锦": 0, "瓷器": 1, "壁画": 0}
    # 自身维度不参与过滤，仍显示全局分布
    assert facet_map(body, "dynasties") == {"清": 1, "明": 1, "宋": 1}
    assert body["total"] == 1


def test_facets_with_motif_filter_narrow_other_dimensions(client):
    body = client.get("/api/facets?motif=云纹").json()
    assert facet_map(body, "dynasties") == {"清": 1, "明": 0, "宋": 0}
    assert facet_map(body, "carriers") == {"织锦": 1, "瓷器": 0, "壁画": 0}
    assert facet_map(body, "motifs") == {"云纹": 1, "龙纹": 1, "花卉纹": 1}
    assert body["total"] == 1


def test_facets_with_keyword_filter(client):
    body = client.get("/api/facets?keyword=Dragon").json()
    assert facet_map(body, "motifs") == {"云纹": 0, "龙纹": 1, "花卉纹": 0}
    assert facet_map(body, "dynasties") == {"清": 0, "明": 1, "宋": 0}
    assert facet_map(body, "carriers") == {"织锦": 0, "瓷器": 1, "壁画": 0}
    assert body["total"] == 1


def test_facets_with_combined_filters(client):
    body = client.get("/api/facets?motif=云纹&dynasty=清").json()
    assert facet_map(body, "motifs") == {"云纹": 1, "龙纹": 0, "花卉纹": 0}
    assert facet_map(body, "dynasties") == {"清": 1, "明": 0, "宋": 0}
    assert facet_map(body, "carriers") == {"织锦": 1, "瓷器": 0, "壁画": 0}
    assert body["total"] == 1
