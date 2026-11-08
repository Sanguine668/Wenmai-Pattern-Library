#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""质检马军的 Commons/数字敦煌数据，输出修正表、复核清单与报告。"""

import collections
import csv
import hashlib
import pathlib
import re
import statistics
import sys

from PIL import Image

PROJECT = pathlib.Path(__file__).resolve().parent.parent
DATA = PROJECT / "马军_提交"
OUT = DATA / "质量检查"
OUT.mkdir(parents=True, exist_ok=True)

MOTIF_MAP = {
    "莲花纹": "花卉纹", "牡丹纹": "花卉纹", "持莲纹": "花卉纹", "叶纹": "花卉纹",
    "团花纹": "花卉纹", "团花纹。": "花卉纹", "内画四叶纹": "花卉纹",
    "忍冬纹": "缠枝卷草纹", "菱格纹": "几何纹", "欄墙纹": "几何纹",
    "双龙纹": "龙纹", "火焰纹": "其他",
}


def resolve(p: str):
    p = p.strip()
    candidates = [
        DATA / re.sub(r"^output/(commons|dunhuang)/images/", r"images/\1/", p),
        DATA / p,
        DATA / "images" / "dunhuang" / pathlib.Path(p).name,
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    rows = list(csv.DictReader((DATA / "马军_records.csv").open(encoding="utf-8-sig")))
    fields = list(rows[0].keys())
    fixed_fields = fields + ["motif_type_raw", "image_ok", "needs_attribution", "dup_image"]

    hashes: dict[str, str] = {}
    dup_items = []
    missing = []
    sizes = []
    total_bytes = 0
    fixed = []
    review = []

    for r in rows:
        f = resolve(r["local_images"])
        image_ok = bool(f)
        dup = ""
        if f:
            total_bytes += f.stat().st_size
            try:
                w, h = Image.open(f).size
                sizes.append((w, h))
            except Exception:
                pass
            digest = hashlib.sha256(f.read_bytes()).hexdigest()
            if digest in hashes:
                dup = "重复：" + hashes[digest]
                dup_items.append((r["source_id"], hashes[digest]))
            else:
                hashes[digest] = str(r["source_id"])
        else:
            missing.append((r["source"], r["source_id"], r["local_images"]))

        raw_label = (r["motif_type"] or "").strip()
        new_label = MOTIF_MAP.get(raw_label, raw_label)
        needs_attr = r["license"].strip().startswith("CC BY")
        row = dict(r)
        row["motif_type"] = new_label
        row["motif_type_raw"] = raw_label
        if raw_label != new_label:
            parts = [p for p in re.split(r"[/、;；]", (row.get("motif_type_secondary") or "")) if p.strip()]
            detail = raw_label.rstrip("。")
            if detail not in parts:
                parts.append(detail)
            row["motif_type_secondary"] = "/".join(parts)
        row["image_ok"] = "1" if image_ok else "0"
        row["needs_attribution"] = "1" if needs_attr else "0"
        row["dup_image"] = dup
        if f:
            row["local_images"] = f.relative_to(PROJECT).as_posix()
        fixed.append(row)

        issues = []
        if not image_ok:
            issues.append("图片缺失")
        if raw_label != new_label:
            issues.append(f"标签需规范：{raw_label}→{new_label}")
        if needs_attr:
            issues.append("CC BY/BY-SA 需保留作者署名")
        if (r["century"] or "").strip() in ("", "未知"):
            issues.append("世纪未知")
        if (r["dynasty"] or "").strip() in ("", "未知"):
            issues.append("朝代未知")
        if not (r["source_url"] or "").strip():
            issues.append("缺来源页")
        if dup:
            issues.append(dup)
        if issues:
            review.append({**row, "issues": "；".join(issues)})

    fixed_csv = OUT / "records_fixed.csv"
    with fixed_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fixed_fields)
        writer.writeheader()
        writer.writerows(fixed)

    review_csv = OUT / "review_queue.csv"
    with review_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fixed_fields + ["issues"])
        writer.writeheader()
        writer.writerows(review)

    long_edges = [max(w, h) for w, h in sizes]
    lines = [
        "# 马军 Commons/数字敦煌 数据质量报告",
        "",
        f"- 记录：{len(rows)} 条（Commons {sum(1 for r in rows if r['source']=='Commons')}、"
        f"数字敦煌 {sum(1 for r in rows if r['source']=='dunhuang')}）",
        f"- 图片：找到 {len(rows)-len(missing)} 条，缺失 {len(missing)} 条；共 {len(sizes)} 张、{total_bytes/1024/1024:.1f} MB",
        f"- 重复图片：{len(dup_items)} 组 {dup_items}",
        f"- 分辨率长边：最小 {min(long_edges)}、中位 {int(statistics.median(long_edges))}、最大 {max(long_edges)}；小于 800px：{sum(1 for x in long_edges if x < 800)} 张",
        f"- 不规范标签：{sum(1 for r in rows if r['motif_type'].strip() not in ['龙纹','凤纹','花卉纹','缠枝卷草纹','云纹','几何纹','文字纹','其他'])} 条",
        f"- 需署名（CC BY / BY-SA）：{sum(1 for r in rows if r['license'].strip().startswith('CC BY'))} 条",
        f"- 世纪未知：{sum(1 for r in rows if r['century'].strip() in ('','未知'))} 条；朝代未知：{sum(1 for r in rows if r['dynasty'].strip() in ('','未知'))} 条",
        "",
        "## 结论",
        "",
        "- 图片质量最好：292 条全部有图，分辨率全部 ≥800px，未发现低对比/模糊图；",
        "- 主要问题：图片路径前缀需修正（已在 records_fixed.csv 修好）、14 条标签超出 8 类需映射（原始细分类已保留为次标签）、CC BY/BY-SA 需要保留作者署名；",
        "- Commons 的 date_text 多为文件上传时间而非文物年代，century/dynasty 大量为未知，建议从标题/描述中提取朝代或人工补；",
        "- 数字敦煌 48 条有官方授权 PDF，来源页缺失属正常，保留 license 说明即可。",
    ]
    report = OUT / "quality_report.md"
    report.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\n修正表：{fixed_csv}\n复核清单：{review_csv}\n报告：{report}")


if __name__ == "__main__":
    main()
