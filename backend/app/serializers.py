from __future__ import annotations

from .models import Pattern, User


SOURCE_MAP = {
    "met": "大都会艺术博物馆",
    "cleveland": "克利夫兰艺术博物馆",
    "commons": "Wikimedia Commons",
    "dunhuang": "数字敦煌",
    "artic": "芝加哥艺术博物馆",
    "manual": "手工录入",
}
CLASS_EN = {
    "龙纹": "DRAGON",
    "凤纹": "PHOENIX",
    "花卉纹": "FLORA",
    "缠枝/卷草纹": "SCROLL",
    "云纹": "CLOUD",
    "几何纹": "GEOMETRY",
    "文字纹": "INSCRIPTION",
    "人物纹": "FIGURE",
    "其他": "OTHER",
}


def image_url(image) -> str | None:
    if image is None:
        return None
    if image.external_url:
        return image.external_url
    return f"/api/images/{image.id}"


def serialize_pattern(pattern: Pattern, related: list[dict] | None = None) -> dict:
    primary = next((item for item in pattern.images if item.is_primary), None)
    if primary is None and pattern.images:
        primary = pattern.images[0]
    payload = {
        "id": pattern.id,
        "catalog": pattern.catalog,
        "name": pattern.name,
        "originalTitle": pattern.original_title or "",
        "motifType": pattern.motif_type,
        "motifEn": CLASS_EN.get(pattern.motif_type, pattern.motif_type),
        "secondary": pattern.secondary or "",
        "dynasty": pattern.dynasty,
        "dateText": pattern.date_text or "",
        "century": pattern.century or "",
        "carrier": pattern.carrier,
        "description": pattern.description or "",
        "source": SOURCE_MAP.get(pattern.source, pattern.source),
        "sourceCode": pattern.source,
        "sourceId": pattern.source_id,
        "sourceUrl": pattern.source_url or "",
        "license": pattern.license or "",
        "status": pattern.status,
        "annotator": pattern.annotator or "",
        "notes": pattern.notes or "",
        "hasImage": pattern.has_image,
        "labelValid": pattern.label_valid,
        "image": image_url(primary),
        "imageCount": len(pattern.images),
        "images": [image_url(item) for item in pattern.images if image_url(item)],
        "colors": pattern.colors_json or [],
        "tags": [
            {"id": tag.id, "dimension": tag.dimension, "name": tag.name}
            for tag in pattern.tags
        ],
        "createdAt": pattern.created_at.isoformat() if pattern.created_at else None,
        "updatedAt": pattern.updated_at.isoformat() if pattern.updated_at else None,
    }
    if related is not None:
        payload["related"] = related
    return payload


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "displayName": user.display_name,
        "email": user.email or "",
        "isAdmin": user.is_admin,
        "isActive": user.is_active,
        "createdAt": user.created_at.isoformat() if user.created_at else None,
    }

