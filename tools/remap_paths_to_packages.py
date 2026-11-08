#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把主数据集的图片路径重映射到 annotation_packages 里的任务包图片。"""

import csv
import pathlib
import sys

PROJECT = pathlib.Path(__file__).resolve().parent.parent
PACKAGES = PROJECT / "annotation_packages"
PARTS = [
    ("欧阳宇康", PROJECT / "data_annotation/part1_欧阳宇康.csv"),
    ("罗云祥", PROJECT / "data_annotation/part2_罗云祥.csv"),
    ("马军", PROJECT / "data_annotation/part3_马军.csv"),
]
TARGETS = [
    PROJECT / "data_master/all_records_master.csv",
    PROJECT / "data_master/all_records_with_images.csv",
    PROJECT / "data_master/all_records_final_annotated.csv",
    PROJECT / "data_master/training_set.csv",
    PROJECT / "data_master/discarded.csv",
    PROJECT / "data_master/review_queue.csv",
]


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    owner = {}
    for member, part in PARTS:
        if not part.exists():
            print("缺少分片：", part)
            continue
        for r in csv.DictReader(part.open(encoding="utf-8-sig")):
            owner[(r["source"].strip().lower(), str(r["source_id"]).strip())] = member

    def new_paths(source, sid):
        member = owner.get((source.strip().lower(), str(sid).strip()))
        if not member:
            return []
        base = PACKAGES / f"标注任务_{member}" / "images" / source / str(sid)
        if not base.exists():
            return []
        return [p.relative_to(PROJECT).as_posix() for p in sorted(base.glob("*")) if p.is_file()]

    for target in TARGETS:
        if not target.exists():
            continue
        rows = list(csv.DictReader(target.open(encoding="utf-8-sig")))
        if not rows:
            continue
        fields = list(rows[0].keys())
        fixed = 0
        empty = 0
        for r in rows:
            paths = new_paths(r.get("source", ""), r.get("source_id", ""))
            if paths:
                r["local_images"] = " | ".join(paths)
                fixed += 1
            elif r.get("local_images"):
                r["local_images"] = ""
                empty += 1
        with target.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        print(f"{target.name}: {len(rows)} 行，重映射 {fixed}，清空失效路径 {empty}")


if __name__ == "__main__":
    main()
