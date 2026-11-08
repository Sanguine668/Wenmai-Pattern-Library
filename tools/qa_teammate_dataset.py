#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""质检罗云祥的 Cleveland/ArtIC 采集成果，输出修复 CSV、复核清单与报告。"""

import collections
import csv
import hashlib
import pathlib
import statistics
import sys

from PIL import Image, ImageFilter, ImageStat

PROJECT = pathlib.Path(__file__).resolve().parent.parent
DATA = PROJECT / "罗云祥_Cleveland_ArtIC采集成果"
OUT = DATA / "质量检查"
MERGED = DATA / "records_merged.csv"
OUT.mkdir(parents=True, exist_ok=True)


def fix_path(p: str) -> str:
    return p.replace("output/cleveland/", "cleveland/")


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    rows = list(csv.DictReader(MERGED.open(encoding="utf-8-sig")))
    fields = list(rows[0].keys())

    # 1) 去重 + 修正图片路径
    dedup = {}
    for r in rows:
        images = [fix_path(p.strip()) for p in (r.get("local_images") or "").split("|") if p.strip()]
        r["local_images"] = "|".join(images)
        dedup[(r["source"], r["source_id"])] = r
    fixed = sorted(dedup.values(), key=lambda r: (r["source"], r["source_id"]))

    # 2) 图片质检
    missing, sizes, blur = [], [], []
    hashes = {}
    dup_img = 0
    total_bytes = 0
    per_record = {}
    for r in fixed:
        key = (r["source"], r["source_id"])
        images = [p for p in (r.get("local_images") or "").split("|") if p]
        ok = 0
        for p in images:
            f = DATA / p
            if not f.exists():
                missing.append((key, p))
                continue
            ok += 1
            total_bytes += f.stat().st_size
            im = Image.open(f).convert("RGB")
            w, h = im.size
            sizes.append((w, h))
            edges = im.convert("L").filter(ImageFilter.FIND_EDGES)
            v = ImageStat.Stat(edges).var[0]
            blur.append(v)
            digest = hashlib.sha256(f.read_bytes()).hexdigest()
            if digest in hashes:
                dup_img += 1
            hashes[digest] = p
        per_record[key] = {"ok": ok, "blur": blur[-1] if ok else None}

    long_edges = [max(w, h) for w, h in sizes]
    low_blur = [k for k, v in per_record.items() if v["ok"] and v["blur"] is not None and v["blur"] < 60]
    no_image = [k for k, v in per_record.items() if v["ok"] == 0]
    other_label = [(r["source"], r["source_id"]) for r in fixed if r["motif_type"] == "其他"]
    review = sorted(set(no_image + low_blur + other_label))

    # 3) 写修复后的总表
    fixed_csv = OUT / "records_merged_fixed.csv"
    with fixed_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(fixed)

    # 4) 写复核清单
    review_csv = OUT / "review_queue.csv"
    with review_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["source", "source_id", "title", "carrier", "motif_type",
                         "issue", "local_images"])
        for r in fixed:
            key = (r["source"], r["source_id"])
            if key not in review:
                continue
            issues = []
            if key in no_image:
                issues.append("无本地图片")
            if key in low_blur:
                issues.append("疑似模糊/低对比")
            if key in other_label:
                issues.append("标签为其他，需确认是否有纹样")
            writer.writerow([r["source"], r["source_id"], r["title"], r["carrier"],
                             r["motif_type"], "；".join(issues), r["local_images"]])

    # 5) 报告
    lines = [
        "# 罗云祥 Cleveland/ArtIC 采集成果质量报告",
        "",
        f"- 原始记录：{len(rows)} 条；去重后：{len(fixed)} 条",
        f"- 来源分布：" + "、".join(f"{k} {v}" for k, v in
                                  collections.Counter(r["source"] for r in fixed).items()),
        f"- 载体分布：" + "、".join(f"{k} {v}" for k, v in
                                  collections.Counter(r["carrier"] for r in fixed).most_common()),
        f"- 标签分布：" + "、".join(f"{k} {v}" for k, v in
                                  collections.Counter(r["motif_type"] for r in fixed).most_common()),
        f"- 有本地图片的记录：{len(fixed) - len(no_image)} / {len(fixed)}",
        f"- 图片文件：{len(sizes)} 张，合计 {total_bytes / 1024 / 1024:.1f} MB",
    ]
    if long_edges:
        lines += [
            f"- 图片长边：最小 {min(long_edges)}，中位 {int(statistics.median(long_edges))}，最大 {max(long_edges)}；小于 800px：{sum(1 for x in long_edges if x < 800)} 张",
            f"- 边缘方差（模糊参考）：P10={int(statistics.quantiles(blur, n=10)[0])}，中位={int(statistics.median(blur))}；低于 60 的疑似低对比图：{len(low_blur)} 张",
        ]
    lines += [
        f"- 完全重复图片：{dup_img} 张",
        f"- 无本地图片记录：{len(no_image)} 条（全部为 ArtIC）",
        f"- 标签为“其他”的记录：{len(other_label)} 条（需人工判断是纹样还是素面器物）",
        "",
        "## 主要问题",
        "",
        "1. **图片路径错误**：原 CSV 写作 `output/cleveland/images/...`，实际文件在 `cleveland/images/...`；已生成修正版 `records_merged_fixed.csv`。",
        "2. **ArtIC 100 条没有本地图片**：只有图片 URL，需要重新下载或用其他源替换，否则无法用于训练。",
        "3. **标签质量偏弱**：223 条（56%）标为“其他”，其中包含大量素面器物（Jar、Dish、Charger 等），应改为“舍弃”，而不是“其他”。",
        "4. **疑似低对比/模糊图 79 张**：建议人工复核，必要时舍弃。",
        "5. **Cleveland 原始 CSV 有 6 个重复 id**；合并表已去掉重复，但源文件也应清理。",
        "",
        "## 可用性结论",
        "",
        "- Cleveland 部分：299 条记录、299 张高分辨率图片，字段完整、来源与许可清楚，**修正路径后可直接进入标注与建库流程**；",
        "- ArtIC 部分：100 条元数据可用，但没有图片，**目前不能计入可用数据集**；",
        "- 建议用 `review_queue.csv` 逐条复核，把素面器物标记为舍弃、把误标“其他”的改成正确类别。",
    ]
    report = OUT / "quality_report.md"
    report.write_text("\n".join(lines), encoding="utf-8")

    print("\n".join(lines))
    print(f"\n修复总表：{fixed_csv}")
    print(f"复核清单：{review_csv}")
    print(f"质量报告：{report}")


if __name__ == "__main__":
    main()
