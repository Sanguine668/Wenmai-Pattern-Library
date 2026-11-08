from __future__ import annotations

from PIL import Image


def test_tiff_mural_served_as_jpeg(client, tmp_path, monkeypatch):
    import app.main as main
    from app.database import SessionLocal
    from app.models import PatternImage

    tiff = tmp_path / "mural.tif"
    Image.new("RGB", (60, 80), (170, 40, 30)).save(tiff, "TIFF")
    monkeypatch.setattr(main, "PROJECT_ROOT", tmp_path)

    with SessionLocal() as db:
        image = PatternImage(
            pattern_id="commons-300",
            relative_path="mural.tif",
            is_primary=True,
            sort_order=1,
        )
        db.add(image)
        db.commit()
        image_id = image.id

    response = client.get(f"/api/images/{image_id}")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/jpeg")
    assert response.content.startswith(b"\xff\xd8\xff")
    assert list((tmp_path / "data" / "image_cache").glob("*.jpg"))
