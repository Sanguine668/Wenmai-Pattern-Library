#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合并三份数据（我方 / 罗云祥 / 欧阳宇康），输出去重后的主数据集与统计。"""

import collections
import csv
import json
import pathlib
import sys

PROJECT = pathlib.Path(__file__).resolve().parent.parent
OUT = PROJECT / "data_master"
OUT.mkdir(parents=True, exist_ok=True)

OURS = PROJECT / "data_starter/all_records.csv"
OUR_ANN = PROJECT / "data_starter/annotations.json"
LUO_ANN = PROJECT / "all_records_annotated.csv"
LUO_FIXED = PROJECT / "罗云祥_Cleveland_ArtIC采集成果/质量检查/records_merged_fixed.csv"
LUO_BASE = PROJECT / "罗云祥_Cleveland_ArtIC采集成果"
OUYANG = PROJECT / "欧阳宇康_Met采集/met_final.csv"
OUYANG_BASE = PROJECT / "欧阳宇康_Met采集"
MAJUN = PROJECT / "马军_提交/质量检查/records_fixed.csv"

FIELDS = [
    "source", "source_id", "title", "date_text", "century", "dynasty", "carrier",
    "motif_type", "motif_type_secondary", "description", "image_urls", "local_images",
    "license", "source_url", "status", "annotator", "notes", "dataset_origin",
]


def key_of(source: str, sid: str):
    return (source.strip().lower(), str(sid).strip())


def rel(path: pathlib.Path) -> str:
    return path.resolve().relative_to(PROJECT).as_posix()


def existing(paths: list[pathlib.Path]) -> list[str]:
    return [rel(p) for p in paths if p.exists()]


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    records: dict[tuple, dict] = {}
    origins: dict[tuple, set] = collections.defaultdict(set)

    def upsert(src, sid, row, images, status=None, annotator="", origin=""):
        k = key_of(src, sid)
        cur = records.get(k)
        if cur is None:
            cur = {f: "" for f in FIELDS}
            cur.update({"source": src.strip().lower(), "source_id": str(sid)})
            records[k] = cur
        for f, v in row.items():
            if f in FIELDS and not cur.get(f) and v:
                cur[f] = v
        if images:
            cur["local_images"] = " | ".join(images)
        if status:
            cur["status"] = status
        if annotator:
            cur["annotator"] = annotator
        if origin:
            origins[k].add(origin)
        return cur

    # 1) 欧阳宇康 Met
    ou = list(csv.DictReader(OUYANG.open(encoding="utf-8-sig")))
    for r in ou:
        imgs = existing([OUYANG_BASE / p.strip() for p in (r.get("local_images") or "").split("|") if p.strip()])
        upsert("met", r["source_id"], {
            "title": r.get("title", ""), "date_text": r.get("period", ""),
            "dynasty": r.get("dynasty", ""), "carrier": r.get("carrier", ""),
            "motif_type": r.get("motif_type", ""), "description": r.get("description", ""),
            "image_urls": r.get("image_urls", ""), "license": r.get("license", ""),
            "source_url": r.get("source_url", ""), "notes": "欧阳宇康自动标签，待人工复核",
        }, imgs, status="pending", annotator="欧阳宇康", origin="欧阳宇康_Met采集")

    # 2) 我方起步集 + 标注
    ours = list(csv.DictReader(OURS.open(encoding="utf-8-sig")))
    ann = json.loads(OUR_ANN.read_text(encoding="utf-8")) if OUR_ANN.exists() else {}
    for r in ours:
        imgs = existing([PROJECT / p.strip() for p in (r.get("local_images") or "").split("|") if p.strip()])
        a = ann.get(f"{r['source']}:{r['source_id']}", {})
        upsert(r["source"], r["source_id"], {
            "title": r.get("title", ""), "date_text": r.get("date_text", ""),
            "century": r.get("century", ""), "dynasty": r.get("dynasty", ""),
            "carrier": r.get("carrier", ""), "description": r.get("description", ""),
            "image_urls": r.get("image_urls", ""), "license": r.get("license", ""),
            "source_url": r.get("source_url", ""),
        }, imgs, status=a.get("status"), annotator="欧阳宇康" if a else "",
            origin="data_starter")
        if a:
            cur = records[key_of(r["source"], r["source_id"])]
            cur["motif_type"] = a.get("motif_type") or cur["motif_type"]
            cur["motif_type_secondary"] = a.get("motif_type_secondary", "")
            cur["notes"] = a.get("note", "")

    # 3) 罗云祥标注结果（Cleveland + Met）
    luo = list(csv.DictReader(LUO_ANN.open(encoding="utf-8-sig")))
    for r in luo:
        src = r["source"].strip().lower()
        imgs = []
        for p in (r.get("local_images") or "").split("|"):
            p = p.strip()
            if not p:
                continue
            if src == "cleveland":
                imgs += existing([LUO_BASE / p.replace("output/cleveland/", "cleveland/")])
            else:
                imgs += existing([OUYANG_BASE / p.replace("output/met/", "")])
        cur = upsert(src, r["source_id"], {
            "title": r.get("title", ""), "date_text": r.get("date_text", ""),
            "century": r.get("century", ""), "dynasty": r.get("dynasty", ""),
            "carrier": r.get("carrier", ""), "description": r.get("description", ""),
            "image_urls": r.get("image_urls", ""), "license": r.get("license", ""),
            "source_url": r.get("source_url", ""),
            "motif_type": r.get("annotated_motif") or r.get("motif_type", ""),
            "motif_type_secondary": r.get("annotated_secondary", ""),
            "notes": r.get("annotated_note", ""),
        }, imgs, status=r.get("status"), annotator="罗云祥", origin="罗云祥_初步分类")
        if not imgs:
            cur["notes"] = (cur["notes"] + "；无本地图片").strip("；")

    # 4) ArtIC 元数据（无图）
    fixed = list(csv.DictReader(LUO_FIXED.open(encoding="utf-8-sig")))
    for r in fixed:
        if r["source"].strip().lower() != "artic":
            continue
        k = key_of("artic", r["source_id"])
        if k in records:
            continue
        upsert("artic", r["source_id"], {
            "title": r.get("title", ""), "date_text": r.get("date_text", ""),
            "century": r.get("century", ""), "dynasty": r.get("dynasty", ""),
            "carrier": r.get("carrier", ""), "motif_type": r.get("motif_type", ""),
            "description": r.get("description", ""), "image_urls": r.get("image_urls", ""),
            "license": r.get("license", ""), "source_url": r.get("source_url", ""),
            "notes": "ArtIC 图片未下载（403）",
        }, [], status="no_image", annotator="罗云祥", origin="罗云祥_ArtIC元数据")

    # 5) 马军 Commons / 数字敦煌（records_fixed.csv 已修正路径与标签）
    if MAJUN.exists():
        for r in csv.DictReader(MAJUN.open(encoding="utf-8-sig")):
            src = r["source"].strip().lower()
            imgs = existing([PROJECT / p.strip() for p in (r.get("local_images") or "").split(" | ") if p.strip()])
            upsert(src, r["source_id"], {
                "title": r.get("title", ""), "date_text": r.get("date_text", ""),
                "century": r.get("century", ""), "dynasty": r.get("dynasty", ""),
                "carrier": r.get("carrier", ""), "motif_type": r.get("motif_type", ""),
                "motif_type_secondary": r.get("motif_type_secondary", ""),
                "description": r.get("description", ""), "image_urls": r.get("image_urls", ""),
                "license": r.get("license", ""), "source_url": r.get("source_url", ""),
                "notes": r.get("notes", ""),
            }, imgs, status="pending", annotator="马军", origin="马军_提交")

    rows = []
    for k, cur in records.items():
        cur["dataset_origin"] = " + ".join(sorted(origins[k]))
        if not cur.get("status"):
            cur["status"] = "pending"
        if not cur.get("local_images"):
            cur["status"] = "no_image" if cur["status"] == "pending" else cur["status"]
        rows.append(cur)
    rows.sort(key=lambda r: (r["source"], r["source_id"]))

    out_csv = OUT / "all_records_master.csv"
    with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    with_image = [r for r in rows if r["local_images"]]
    with_image_csv = OUT / "all_records_with_images.csv"
    with with_image_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(with_image)
    by_source = collections.Counter(r["source"] for r in rows)
    by_status = collections.Counter(r["status"] for r in rows)
    labels = collections.Counter(r["motif_type"] for r in rows if r["status"] == "confirmed")
    review = [r for r in rows if r["status"] in ("pending", "no_image")]
    review_csv = OUT / "review_queue.csv"
    with review_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(review)

    summary = [
        "# 主数据集合并统计",
        "",
        f"- 唯一记录：{len(rows)} 条（有本地图片 {len(with_image)} 条）",
        f"- 来源分布：" + "、".join(f"{k} {v}" for k, v in by_source.most_common()),
        f"- 状态分布：" + "、".join(f"{k} {v}" for k, v in by_status.most_common()),
        f"- 已确认标签分布：" + "、".join(f"{k} {v}" for k, v in labels.most_common()),
        f"- 待处理/无图复核：{len(review)} 条（review_queue.csv）",
        "",
        "> 数据来源：我方起步集、罗云祥 Cleveland/ArtIC、欧阳宇康 Met；按 (source, source_id) 去重。",
        "> status=pending 表示标签未人工确认；no_image 表示暂无本地图片。",
    ]
    (OUT / "summary.md").write_text("\n".join(summary), encoding="utf-8")
    print("\n".join(summary))
    print(f"\n主表：{out_csv}\n有图子集：{with_image_csv}\n复核：{review_csv}")


if __name__ == "__main__":
    main()
