from __future__ import annotations

import argparse
import colorsys
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from .config import DATA_FILE, DEMO_USERNAME, PROJECT_ROOT
from .database import Base, SessionLocal, engine
from .models import BrowseLog, Favorite, Pattern, PatternImage, Tag, User, pattern_tags


CLASSES = ["龙纹", "凤纹", "花卉纹", "缠枝/卷草纹", "云纹", "几何纹", "文字纹", "人物纹", "其他"]
DYNASTY_MAP = {
    "Ming": "明",
    "Qing": "清",
    "Tang": "唐",
    "Song": "宋",
    "Yuan": "元",
    "Han": "汉",
    "Zhou": "周",
    "Shang": "商",
    "Qin": "秦",
    "Sui": "隋",
    "Jin": "金",
    "Liao": "辽",
    "Five Dynasties": "五代",
    "Neolithic": "新石器",
}
CARRIER_RULES = [
    ("lacquer", "漆器"),
    ("jade", "玉器"),
    ("bronze", "金属器"),
    ("porcelain", "瓷器"),
    ("ceramic", "瓷器"),
    ("silk", "织锦"),
    ("textile", "织锦"),
    ("tapestry", "织锦"),
    ("embroidery", "织锦"),
    ("robe", "织锦"),
    ("mural", "壁画"),
]
TRADITIONAL_COLORS = {
    "朱砂": "#9E4B3B",
    "青绿": "#7E8C6B",
    "墨绿": "#2F3A2A",
    "青灰": "#8A9A9A",
    "黛蓝": "#2E4A4A",
    "靛蓝": "#1B3B6F",
    "石青": "#2E6B8A",
    "古金": "#9C7C43",
    "棕褐": "#4A3728",
    "月白": "#E8EDEC",
    "墨黑": "#1C1A17",
}


def has_cjk(value: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", value or ""))


def normalize_dynasty(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return "年代未定"
    if has_cjk(value):
        for cn in DYNASTY_MAP.values():
            if cn in value:
                return cn
        return value[:64]
    lowered = value.lower()
    for en, cn in DYNASTY_MAP.items():
        if en.lower() in lowered:
            return cn
    return "年代未定"


def normalize_carrier(value: str, title: str) -> str:
    value = (value or "").strip()
    haystack = f"{value} {title}".lower()
    for needle, carrier in CARRIER_RULES:
        if needle in haystack:
            return carrier
    return value[:64] if value else "其他"


def normalize_motif(value: str) -> tuple[str, str | None]:
    value = (value or "").strip()
    for name in CLASSES:
        if value == name:
            return name, None
    if "/" in value:
        parts = [part.strip() for part in value.split("/") if part.strip()]
        if parts and parts[0] in CLASSES:
            secondary = "、".join(parts[1:]) or None
            return parts[0], secondary
    return "其他", value or None


def resolve_images(raw: str) -> list[Path]:
    paths = []
    for item in (raw or "").split("|"):
        item = item.strip()
        if not item:
            continue
        path = (PROJECT_ROOT / item).resolve()
        if path.is_file() and path.is_relative_to(PROJECT_ROOT):
            paths.append(path)
    return paths


def nearest_color(hex_value: str) -> tuple[str, str]:
    rgb = tuple(int(hex_value[i : i + 2], 16) for i in (1, 3, 5))
    best_name, best_distance = "提取色", 10**9
    for name, candidate in TRADITIONAL_COLORS.items():
        other = tuple(int(candidate[i : i + 2], 16) for i in (1, 3, 5))
        distance = sum((a - b) ** 2 for a, b in zip(rgb, other)) ** 0.5
        if distance < best_distance:
            best_name, best_distance = name, distance
    return (best_name if best_distance <= 92 else "提取色", hex_value)


def extract_palette(path: Path) -> list[dict]:
    try:
        image = Image.open(path).convert("RGB")
        image.thumbnail((128, 128))
        buckets = defaultdict(list)
        for r, g, b in image.getdata():
            _, saturation, value = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if saturation < 0.16 or value < 0.16 or value > 0.96:
                continue
            buckets[(r // 32, g // 32, b // 32)].append((r, g, b))
        colors = []
        for values in sorted(buckets.values(), key=len, reverse=True):
            if len(values) < 6:
                continue
            rgb = tuple(sum(item[i] for item in values) // len(values) for i in range(3))
            hex_value = "#%02X%02X%02X" % rgb
            if all(
                sum(
                    (a - b) ** 2
                    for a, b in zip(
                        rgb,
                        tuple(int(color["hex"][i : i + 2], 16) for i in (1, 3, 5)),
                    )
                )
                > 1800
                for color in colors
            ):
                name, value = nearest_color(hex_value)
                colors.append({"name": name, "hex": value})
            if len(colors) == 3:
                break
        return colors or [{"name": "墨黑", "hex": "#1C1A17"}]
    except Exception:
        return []


def get_or_create_tag(db: Session, cache: dict, dimension: str, name: str | None) -> Tag | None:
    name = (name or "").strip()
    if not name:
        return None
    key = (dimension, name)
    if key in cache:
        return cache[key]
    tag = db.scalar(select(Tag).where(Tag.dimension == dimension, Tag.name == name))
    if tag is None:
        tag = Tag(dimension=dimension, name=name)
        db.add(tag)
        db.flush()
    cache[key] = tag
    return tag


def ensure_demo_user(db: Session) -> User:
    """游客兜底账号：没有密码、永远不是管理员、始终保持启用。"""
    user = db.scalar(select(User).where(User.username == DEMO_USERNAME))
    if user is None:
        user = User(
            username=DEMO_USERNAME,
            display_name="本机读者",
            email="demo@wenmai.local",
            is_admin=False,
            is_active=True,
        )
        db.add(user)
        db.commit()
        return user
    changed = False
    if user.is_admin:
        user.is_admin = False
        changed = True
    if user.password_hash:
        user.password_hash = None
        changed = True
    if not user.is_active:
        user.is_active = True
        changed = True
    if changed:
        db.commit()
    return user


def ensure_admin_user(db: Session) -> User | None:
    """只在管理员账号不存在时初始化一次，已存在则完全不动。"""
    import secrets

    from .config import (
        ADMIN_DISPLAY_NAME,
        ADMIN_EMAIL,
        ADMIN_PASSWORD,
        ADMIN_PASSWORD_FILE,
        ADMIN_USERNAME,
    )
    from .security import hash_password

    user = db.scalar(select(User).where(User.username == ADMIN_USERNAME))
    if user is not None:
        return user

    password = ADMIN_PASSWORD or secrets.token_urlsafe(12)
    user = User(
        username=ADMIN_USERNAME,
        display_name=ADMIN_DISPLAY_NAME,
        email=ADMIN_EMAIL,
        password_hash=hash_password(password),
        is_admin=True,
        is_active=True,
    )
    db.add(user)
    db.commit()
    if not ADMIN_PASSWORD:
        ADMIN_PASSWORD_FILE.write_text(password, encoding="utf-8")
        print(
            "[auth] 已创建管理员账号 admin；初始密码写入 "
            "data/admin-initial-password.txt，请登录后尽快修改。",
            flush=True,
        )
    else:
        print("[auth] 已创建管理员账号（密码来自 WENMAI_ADMIN_PASSWORD）。", flush=True)
    return user


def import_master_data(db: Session, reset: bool = False, extract_colors: bool = True) -> dict:
    if reset:
        db.execute(delete(pattern_tags))
        db.execute(delete(Favorite))
        db.execute(delete(BrowseLog))
        db.execute(delete(PatternImage))
        db.execute(delete(Pattern))
        db.execute(delete(Tag))
        db.commit()

    ensure_demo_user(db)
    with DATA_FILE.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    tags: dict[tuple[str, str], Tag] = {}
    created = updated = image_count = color_count = 0
    for index, row in enumerate(rows, start=1):
        source = (row.get("source") or "manual").strip()
        source_id = (row.get("source_id") or str(index)).strip()
        pattern_id = f"{source}-{source_id}"
        catalog = f"{source.upper()}-{source_id}"
        title = re.sub(r"\s+", " ", (row.get("title") or "").strip())
        motif, compound_secondary = normalize_motif(row.get("final_motif_type") or "")
        secondary = (row.get("final_secondary") or compound_secondary or "").strip() or None
        carrier = normalize_carrier(row.get("carrier") or "", title)
        # 名称取文物标题；类型与载体只作为标签。导入后可运行
        # `python tools/localize_names.py --apply` 生成中文文物名。
        display_name = title or f"{motif} · {carrier}"
        paths = resolve_images(row.get("local_images") or "")
        has_image = bool(paths)
        colors = extract_palette(paths[0]) if paths and extract_colors else []
        if colors:
            color_count += 1

        pattern = db.get(Pattern, pattern_id)
        values = {
            "catalog": catalog,
            "name": display_name,
            "original_title": title,
            "motif_type": motif,
            "secondary": secondary,
            "dynasty": normalize_dynasty(row.get("dynasty") or row.get("date_text") or ""),
            "date_text": (row.get("date_text") or "").strip(),
            "century": (row.get("century") or "").strip(),
            "carrier": carrier,
            "description": re.sub(r"\s+", " ", (row.get("description") or "")).strip(),
            "source": source,
            "source_id": source_id,
            "source_url": (row.get("source_url") or "").strip(),
            "license": (row.get("license") or "").strip(),
            "status": (row.get("final_status") or "confirmed").strip(),
            "annotator": (row.get("annotator") or "").strip(),
            "notes": (row.get("final_note") or row.get("notes") or "").strip(),
            "dataset_origin": (row.get("dataset_origin") or "").strip(),
            "has_image": has_image,
            "label_valid": row.get("label_valid") == "1",
            "colors_json": colors,
        }
        if pattern is None:
            pattern = Pattern(id=pattern_id, **values)
            db.add(pattern)
            created += 1
        else:
            for key, value in values.items():
                setattr(pattern, key, value)
            pattern.images.clear()
            updated += 1
        db.flush()

        for order, path in enumerate(paths):
            db.add(
                PatternImage(
                    pattern_id=pattern.id,
                    relative_path=str(path.relative_to(PROJECT_ROOT)),
                    alt_text=display_name,
                    is_primary=(order == 0),
                    sort_order=order,
                )
            )
            image_count += 1

        pattern.tags = []
        for dimension, name in (
            ("motif", motif),
            ("secondary", secondary),
            ("dynasty", pattern.dynasty),
            ("carrier", carrier),
            ("status", pattern.status),
        ):
            tag = get_or_create_tag(db, tags, dimension, name)
            if tag is not None:
                pattern.tags.append(tag)
        if index % 100 == 0:
            db.commit()

    db.commit()
    return {
        "rows": len(rows),
        "created": created,
        "updated": updated,
        "images": image_count,
        "withColors": color_count,
        "tags": len(tags),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="导入中华纹脉主数据集到 MySQL")
    parser.add_argument("--reset", action="store_true", help="清空现有资源后重新导入")
    parser.add_argument("--skip-colors", action="store_true", help="跳过主色提取")
    args = parser.parse_args()
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        result = import_master_data(
            db,
            reset=args.reset,
            extract_colors=not args.skip_colors,
        )
    print(result)


if __name__ == "__main__":
    main()

