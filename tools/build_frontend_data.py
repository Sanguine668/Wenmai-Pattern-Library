#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从已标注主数据生成前端演示数据与图片（真实记录，不使用占位图）。"""

import collections
import colorsys
import csv
import json
import pathlib
import re
import sys

from PIL import Image, ImageChops, ImageOps

PROJECT = pathlib.Path(__file__).resolve().parent.parent
TRAIN = PROJECT / "data_master/training_set.csv"
MASTER = PROJECT / "data_master/all_records_master.csv"
FINAL = PROJECT / "data_master/all_records_final_annotated.csv"
OUT_IMG = PROJECT / "frontend/public/patterns"
OUT_CATEGORY = PROJECT / "frontend/public/categories"
HERO_CANDIDATES = [
    PROJECT / "主页背景.png",
    PROJECT / "素材/主页背景.png",
]
HERO_DEST = PROJECT / "frontend/public/hero-background.jpg"
OUT_JS = PROJECT / "frontend/src/data/patterns.js"
OUT_IMG.mkdir(parents=True, exist_ok=True)
OUT_CATEGORY.mkdir(parents=True, exist_ok=True)
OUT_JS.parent.mkdir(parents=True, exist_ok=True)

CLASSES = ["龙纹", "凤纹", "花卉纹", "缠枝/卷草纹", "云纹", "几何纹", "文字纹", "人物纹", "其他"]
CLASS_EN = {
    "龙纹": "DRAGON", "凤纹": "PHOENIX", "花卉纹": "FLORA",
    "缠枝/卷草纹": "SCROLL", "云纹": "CLOUD", "几何纹": "GEOMETRY",
    "文字纹": "INSCRIPTION", "人物纹": "FIGURE", "其他": "OTHER",
}

CATEGORY_FILES = {
    "龙纹": "龙纹.png",
    "凤纹": "凤纹.png",
    "花卉纹": "花卉纹.png",
    "缠枝/卷草纹": "卷草纹.png",
    "云纹": "云纹.png",
    "几何纹": "几何纹.png",
    "文字纹": "文字纹.png",
    "人物纹": "人物纹.png",
    "其他": "其他纹.png",
}
DYNASTY_MAP = {
    "Ming": "明", "Qing": "清", "Tang": "唐", "Song": "宋", "Yuan": "元",
    "Han": "汉", "Zhou": "周", "Shang": "商", "Qin": "秦", "Sui": "隋",
    "Jin": "金", "Liao": "辽", "Five Dynasties": "五代", "Neolithic": "新石器",
}
SOURCE_MAP = {
    "met": "大都会艺术博物馆", "cleveland": "克利夫兰艺术博物馆",
    "commons": "Wikimedia Commons", "dunhuang": "数字敦煌",
    "artic": "芝加哥艺术博物馆",
}

CURATED_NAMES = {
    "Brush Holder": "龙纹笔筒",
    "Western Zhou Jade Dragon 01": "西周玉龙",
    "Wine Container (Bianhu)": "周代龙纹扁壶",
    "Box with Ink Cakes": "龙纹漆盒",
    "Spring & Autumn Jade Dragon 04": "春秋玉龙",
    "Incense Burner with Dragons Chasing Pearl": "龙戏珠纹香炉",
    "Bowl": "凤纹碗",
    "Late Shang Bronze Jia with Phoenix 1": "商代凤纹青铜斝",
    "Blue Phoenix": "青凤纹",
    "Rank Badge (buzi)": "凤纹补子",
    "Late Shang Bronze Jia with Phoenix 1a": "商代凤纹青铜斝（另一面）",
    "Circular Box with Geometric Design": "几何纹圆盒",
    "Fragments": "花卉纹织片",
    "Northern Song Porcelain Pillow with Two Phoenixes, Chengguan Kiln, Henan, 11th-12th C. (9967328073)": "北宋双凤纹瓷枕",
    "六瓣莲花藻井图案": "六瓣莲花藻井图案",
    "Narcissus": "水仙纹织品",
    "Silk Damask Fragment": "花卉纹丝织残片",
    "HK Mid-levels Pokfulam Road 香港大學 HKU campus Art Gallery exhibition 海上絲路 sea ocean silk road n Chinese porcelain June 2023 Px3 08": "海上丝路青花纹样",
    "Border": "缠枝边饰",
    "Brush (Bi) with Carp and Dragon LACMA M.80.152.1": "鱼龙纹漆刷",
    "华盖": "华盖",
    "Rug": "卷草纹毯",
    "Silk Shawl": "缠枝纹丝披肩",
    "Qing Porcelain Vase with Dragons": "清代龙纹瓷瓶",
    "Book Cover": "云纹书衣",
    "Warring States Jade Dragon 36": "战国玉龙",
    "边饰": "云纹边饰",
    "Hat box with stylized chi dragons": "云纹螭龙帽盒",
    "Warring States Jade Dragon 37": "战国玉龙",
    "Fragment": "几何纹织片",
    "Early Western Zhou Bronze Jiao Wine Vessel": "西周青铜角",
    "藻井": "几何纹藻井",
    "Jar with Handles": "几何纹双耳罐",
    "20241018 Blue and White Porcelain Vase with Kui-Dragon Design and Qianlong Reign Mark, Qing Dynasty": "清乾隆青花夔龙纹瓶",
    "Scepter (Gui) with Miscellaneous Poems by Tao Qian (365–427 CE)": "清御题诗玉圭",
    "Late Western Zhou Bronze Pan": "西周铭文铜盘",
    "供养人题记": "供养人题记",
    "Ritual Axe": "汉铭文玉钺",
    "Disc (bi) with Imperial Poem in Seal Script (zhuanshu) by the Qianlong Emperor": "清御题诗玉璧",
    "Bronze Ritual Vessels in Tomb of Marquis Yi of Zeng (10167198605)": "曾侯乙墓青铜礼器",
    "Mirror in a Lacquer Case": "人物纹漆盒镜",
    "Ritual Bronze Wine Vessel, Southeast Asia Gallery, Royal Ontario Museum, front": "人物纹青铜酒器",
    "巾舞": "巾舞",
    "Element from a Lacquered Leather Cuirass": "漆甲残片",
    "Miniature Mountain with Daoist Paradise": "清道教仙境玉山",
    "Ritual Bronze Wine Vessel, Southeast Asia Gallery, Royal Ontario Museum, back": "人物纹青铜酒器（另一面）",
    "Fragment from Book of Textiles": "织物图录残片",
    "Western Zhou Bronze Fangyi Wine Vessel": "西周青铜方彝",
    "Pair of Blue Bottle Vases": "清蓝釉双瓶",
    "Late Western Zhou Bronze Lid of Fangyi Square Wine Vessel": "西周青铜方彝盖",
}
TRADITIONAL_COLORS = {
    "朱砂": "#9E4B3B", "朱红": "#B33B26", "赭石": "#8C6239", "赭红": "#8C4A36",
    "青绿": "#7E8C6B", "墨绿": "#2F3A2A", "青灰": "#8A9A9A", "黛蓝": "#2E4A4A",
    "靛蓝": "#1B3B6F", "石青": "#2E6B8A", "浅金": "#C9A85C", "金色": "#B08C50",
    "古金": "#9C7C43", "棕褐": "#4A3728", "月白": "#E8EDEC", "墨黑": "#1C1A17",
    "米白": "#F4E9DC", "柿橙": "#BE7137", "藤萝紫": "#8E60A9", "铜色": "#9A6B43",
}


def has_cjk(s: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", s or ""))


def dynasty_cn(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return "年代未定"
    if has_cjk(value):
        for k in DYNASTY_MAP.values():
            if k in value:
                return k
        return value.split("dynasty")[0].strip() or value
    for en, cn in DYNASTY_MAP.items():
        if en.lower() in value.lower():
            return cn
    return "年代未定"


def nearest_color(name: str, hex_value: str):
    rgb = tuple(int(hex_value[i:i + 2], 16) for i in (1, 3, 5))
    best, best_dist = None, 10**9
    for n, h in TRADITIONAL_COLORS.items():
        r = tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
        dist = sum((a - b) ** 2 for a, b in zip(rgb, r)) ** 0.5
        if dist < best_dist:
            best, best_dist = n, dist
    return (best, hex_value) if best_dist <= 92 else (f"提取色 {name}", hex_value)


def auto_trim(image: Image.Image) -> Image.Image:
    """裁掉图片外部接近纯色的空白区域。"""
    alpha = image.getchannel("A")
    if alpha.getextrema()[0] < 250:
        box = alpha.getbbox()
    else:
        rgb = image.convert("RGB")
        w, h = rgb.size
        border = []
        step_x, step_y = max(1, w // 40), max(1, h // 40)
        for x in range(0, w, step_x):
            border.extend([rgb.getpixel((x, 0)), rgb.getpixel((x, h - 1))])
        for y in range(0, h, step_y):
            border.extend([rgb.getpixel((0, y)), rgb.getpixel((w - 1, y))])
        bg = tuple(sorted(channel)[len(border) // 2] for channel in zip(*border))
        diff = ImageChops.difference(rgb, Image.new("RGB", rgb.size, bg)).convert("L")
        mask = diff.point(lambda p: 255 if p > 18 else 0)
        box = mask.getbbox()
    if box:
        pad_x = max(3, (box[2] - box[0]) // 20)
        pad_y = max(3, (box[3] - box[1]) // 20)
        image = image.crop((
            max(0, box[0] - pad_x), max(0, box[1] - pad_y),
            min(image.width, box[2] + pad_x), min(image.height, box[3] + pad_y),
        ))
    return image


def trim_and_square(src: pathlib.Path, dest: pathlib.Path, size: int = 640) -> None:
    """裁掉图片外部空白，放进统一尺寸的纸色方形画布。"""
    image = auto_trim(ImageOps.exif_transpose(Image.open(src)).convert("RGBA"))
    image.thumbnail((int(size * 0.86), int(size * 0.86)), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.alpha_composite(image, ((size - image.width) // 2, (size - image.height) // 2))
    canvas.save(dest, "PNG", optimize=True)


def prepare_assets() -> dict[str, str]:
    category_images = {}
    for label, filename in CATEGORY_FILES.items():
        source = PROJECT / "素材" / filename
        if not source.exists():
            continue
        slug = CLASS_EN.get(label, "other").lower()
        dest = OUT_CATEGORY / f"{slug}.png"
        trim_and_square(source, dest)
        category_images[label] = f"/categories/{slug}.png"
    hero_source = next((path for path in HERO_CANDIDATES if path.exists()), None)
    if hero_source:
        hero = ImageOps.exif_transpose(Image.open(hero_source)).convert("RGB")
        hero.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
        hero.save(HERO_DEST, "JPEG", quality=86, optimize=True)
    return category_images


def palette(path: pathlib.Path) -> list[dict]:
    try:
        im = Image.open(path).convert("RGB")
        im.thumbnail((180, 180))
        buckets = collections.defaultdict(list)
        for r, g, b in im.getdata():
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if s < 0.16 or v < 0.16 or v > 0.96:
                continue
            key = (r // 28, g // 28, b // 28)
            buckets[key].append((r, g, b))
        colors = []
        for values in sorted(buckets.values(), key=len, reverse=True):
            if len(values) < 8:
                continue
            rgb = tuple(sum(v[i] for v in values) // len(values) for i in range(3))
            hx = "#%02X%02X%02X" % rgb
            if all(
                sum(
                    (a - b) ** 2
                    for a, b in zip(
                        rgb,
                        tuple(int(color["hex"][i:i + 2], 16) for i in (1, 3, 5)),
                    )
                ) > 1800
                for color in colors
            ):
                name, value = nearest_color(str(len(colors) + 1), hx)
                colors.append({"name": name, "hex": value})
            if len(colors) == 3:
                break
        return colors or [{"name": "墨黑", "hex": "#1C1A17"}]
    except Exception:
        return []


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    category_images = prepare_assets()
    rows = list(csv.DictReader(TRAIN.open(encoding="utf-8-sig")))
    by_class = collections.defaultdict(list)
    for r in rows:
        if r["final_status"] == "confirmed" and r["has_image"] == "1" and r["final_motif_type"] in CLASSES:
            by_class[r["final_motif_type"]].append(r)

    selected = []
    for cls in CLASSES:
        items = by_class[cls][:]
        items.sort(key=lambda r: (r["source"], r["source_id"]))
        # 每个来源轮流取，保证来源多样
        by_source = collections.defaultdict(list)
        for r in items:
            by_source[r["source"]].append(r)
        queues = [by_source[k] for k in sorted(by_source)]
        picked = 0
        while picked < 6 and any(queues):
            for q in queues:
                if q and picked < 6:
                    selected.append(q.pop(0))
                    picked += 1

    patterns = []
    for r in selected:
        first = [p.strip() for p in (r["local_images"] or "").split("|") if p.strip()]
        if not first:
            continue
        src_path = PROJECT / first[0]
        if not src_path.exists():
            continue
        slug = f"{r['source']}-{r['source_id']}"
        dest = OUT_IMG / f"{slug}.jpg"
        try:
            art = ImageOps.exif_transpose(Image.open(src_path)).convert("RGBA")
            art = auto_trim(art)
            art.thumbnail((900, 1125), Image.Resampling.LANCZOS)
            canvas = Image.new("RGB", (1000, 1250), (237, 226, 206))
            canvas.paste(art.convert("RGB"), ((1000 - art.width) // 2, (1250 - art.height) // 2))
            canvas.save(dest, "JPEG", quality=90, optimize=True)
        except Exception:
            continue
        motif = r["final_motif_type"]
        carrier = r["carrier"] or "器物"
        title = (r["title"] or "").strip()
        clean_title = re.sub(r"\.(?:jpe?g|png|tiff?)$", "", title, flags=re.I).strip()
        title_lower = title.lower()
        if "jade" in title_lower:
            carrier = "玉器"
        elif "bronze" in title_lower:
            carrier = "金属器"
        elif "porcelain" in title_lower:
            carrier = "瓷器"
        display = CURATED_NAMES.get(clean_title)
        if not display:
            display = title if has_cjk(title) else f"{motif}{carrier}"
        description = re.sub(r"\s+", " ", r["description"] or "").strip()
        if not description:
            description = f"来源记录：{title or display}"
        colors = palette(dest)
        if not colors:
            colors = [{"name": "墨黑", "hex": "#1C1A17"}]
        patterns.append({
            "id": slug,
            "catalog": f"{r['source'].upper()}-{r['source_id']}",
            "name": display,
            "originalTitle": clean_title,
            "motifType": motif,
            "motifEn": CLASS_EN[motif],
            "secondary": r["final_secondary"] or "",
            "dynasty": dynasty_cn(r["dynasty"] or r["date_text"]),
            "dateText": (r["date_text"] or "")[:80],
            "carrier": carrier,
            "description": description[:220],
            "source": SOURCE_MAP.get(r["source"], r["source"]),
            "license": r["license"] or "",
            "sourceUrl": r["source_url"] or "",
            "image": f"/patterns/{slug}.jpg",
            "colors": colors,
        })

    # 全库统计（真实数据）
    all_rows = list(csv.DictReader(FINAL.open(encoding="utf-8-sig")))
    stats = {
        "total": len(all_rows),
        "withImages": sum(1 for r in all_rows if r.get("local_images")),
        "trainable": sum(1 for r in rows if r["has_image"] == "1" and r["final_status"] == "confirmed"),
        "discarded": sum(1 for r in all_rows if r.get("final_status") == "discarded"),
        "noImage": sum(1 for r in all_rows if not r.get("local_images")),
    }
    motif_counts = collections.Counter(r["final_motif_type"] for r in rows if r["has_image"] == "1" and r["final_status"] == "confirmed")
    dynasty_counts = collections.Counter(dynasty_cn(r["dynasty"] or r["date_text"]) for r in rows if r["has_image"] == "1")
    carrier_counts = collections.Counter(r["carrier"] or "其他" for r in rows if r["has_image"] == "1")

    motif_index = [{"label": c, "en": CLASS_EN[c], "count": motif_counts.get(c, 0)} for c in CLASSES]
    dynasty_index = [{"label": k, "count": v} for k, v in dynasty_counts.most_common(10)
                     if k not in ("年代未定", "未知")][:8]
    carrier_index = [{"label": k, "count": v} for k, v in carrier_counts.most_common(8)]

    sample_motif_counts = collections.Counter(p["motifType"] for p in patterns)
    sample_dynasty_counts = collections.Counter(p["dynasty"] for p in patterns)
    sample_carrier_counts = collections.Counter(p["carrier"] for p in patterns)
    sample_motif_index = [
        {
            "label": c,
            "en": CLASS_EN[c],
            "count": sample_motif_counts.get(c, 0),
            "image": category_images.get(c, ""),
        }
        for c in CLASSES
    ]
    sample_dynasty_index = [
        {"label": k, "count": v}
        for k, v in sample_dynasty_counts.most_common()
        if k not in ("年代未定", "未知")
    ]
    sample_carrier_index = [
        {"label": k, "count": v}
        for k, v in sample_carrier_counts.most_common()
    ]

    body = "// 由 tools/build_frontend_data.py 从已标注真实数据生成\n"
    body += f"export const libraryStats = {json.dumps(stats, ensure_ascii=False, indent=2)}\n\n"
    body += f"export const motifIndex = {json.dumps(motif_index, ensure_ascii=False, indent=2)}\n\n"
    body += f"export const dynastyIndex = {json.dumps(dynasty_index, ensure_ascii=False, indent=2)}\n\n"
    body += f"export const carrierIndex = {json.dumps(carrier_index, ensure_ascii=False, indent=2)}\n\n"
    body += f"export const sampleMotifIndex = {json.dumps(sample_motif_index, ensure_ascii=False, indent=2)}\n\n"
    body += f"export const sampleDynastyIndex = {json.dumps(sample_dynasty_index, ensure_ascii=False, indent=2)}\n\n"
    body += f"export const sampleCarrierIndex = {json.dumps(sample_carrier_index, ensure_ascii=False, indent=2)}\n\n"
    body += f"export const patterns = {json.dumps(patterns, ensure_ascii=False, indent=2)}\n"
    OUT_JS.write_text(body, encoding="utf-8")
    print("selected", len(patterns), "images", len(list(OUT_IMG.glob('*.jpg'))))
    print("stats", stats)
    print("motif counts", motif_counts)
    print("output", OUT_JS)


if __name__ == "__main__":
    main()
