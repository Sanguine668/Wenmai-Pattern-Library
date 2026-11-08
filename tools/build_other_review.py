#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从训练集中筛出“其他”类，按标题/描述给出类别建议，生成复核清单。"""

import collections
import csv
import pathlib
import sys

PROJECT = pathlib.Path(__file__).resolve().parent.parent
TRAIN = PROJECT / "data_master/training_set.csv"
OUT = PROJECT / "data_review"
OUT.mkdir(parents=True, exist_ok=True)

SUGGEST = [
    ("云纹", ("cloud", "clouds", "ruyi cloud", "云纹", "云头", "如意云")),
    ("缠枝/卷草纹", ("scroll", "vine", "arabesque", "tendril", "foliage", "卷草", "缠枝", "忍冬")),
    ("凤纹", ("phoenix", "fenghuang", "凤")),
    ("龙纹", ("dragon", "龙")),
    ("花卉纹", ("lotus", "peony", "flower", "floral", "chrysanthemum", "plum", "莲", "牡丹", "花")),
    ("几何纹", ("geometric", "wave", "fret", "meander", "diaper", "diamond", "菱", "回纹", "锦")),
    ("文字纹", ("longevity", "shou", "fu", "character", "inscription", "寿", "福", "囍", "文字")),
    ("人物纹", ("figure", "figures", "children", "boy", "lady", "scholar", "immortal",
                "arhat", "lohan", "deity", "guanyin", "bodhisattva", "仕女", "童子", "婴戏", "高士")),
]

FIELDS = [
    "source", "source_id", "title", "date_text", "century", "dynasty", "carrier",
    "motif_type", "motif_hint", "description", "image_urls", "local_images",
    "license", "source_url", "annotator", "notes", "status", "motif_type_secondary", "note",
]


def suggest(r: dict) -> str:
    text = (r["title"] + " " + r["description"]).lower()
    for label, keys in SUGGEST:
        if any(k in text for k in keys):
            return label
    return ""


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    rows = list(csv.DictReader(TRAIN.open(encoding="utf-8-sig")))
    other = [r for r in rows if r["final_motif_type"] == "其他" and r["has_image"] == "1"]
    out_rows = []
    for r in other:
        s = suggest(r)
        out_rows.append({
            "source": r["source"], "source_id": r["source_id"], "title": r["title"],
            "date_text": r["date_text"], "century": r["century"], "dynasty": r["dynasty"],
            "carrier": r["carrier"], "motif_type": "其他", "motif_hint": s,
            "description": r["description"], "image_urls": r["image_urls"],
            "local_images": r["local_images"], "license": r["license"],
            "source_url": r["source_url"], "annotator": "待复核",
            "notes": "其他类复核", "status": "pending",
            "motif_type_secondary": r["final_secondary"], "note": r["final_note"],
        })
    # 有建议的排前面，方便一键确认
    out_rows.sort(key=lambda r: (r["motif_hint"] == "", r["source"], r["source_id"]))

    review_csv = OUT / "other_review.csv"
    with review_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(out_rows)
    (OUT / "annotations_其他复核.json").write_text("{}", encoding="utf-8")

    hint_cnt = collections.Counter(r["motif_hint"] or "无建议" for r in out_rows)
    lines = [
        "# “其他”类复核任务",
        "",
        f"- 共 {len(out_rows)} 条（全部有图）",
        f"- 自动建议：{len(out_rows) - hint_cnt.get('无建议', 0)} 条有建议，{hint_cnt.get('无建议', 0)} 条无建议",
        "- 建议分布：" + "、".join(f"{k} {v}" for k, v in hint_cnt.most_common()),
        "",
        "## 怎么复核",
        "",
        "1. 双击 tools/启动复核-其他类.bat；",
        "2. 有建议的会显示“自动提示”，认同就按 Enter / 点“确认自动提示”；",
        "3. 建议不对就点正确类别；没有图案就点“舍弃”；",
        "4. 建议为空的逐条看图判断；",
        "5. 标完导出 CSV，与 annotations_其他复核.json 一起交回。",
    ]
    (OUT / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\n复核清单：{review_csv}")


if __name__ == "__main__":
    main()
