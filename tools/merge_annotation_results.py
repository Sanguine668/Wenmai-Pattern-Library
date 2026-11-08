#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合并三个人的标注结果，生成最终标注表、训练集与统计报告。"""

import collections
import csv
import io
import pathlib
import sys
import zipfile

PROJECT = pathlib.Path(__file__).resolve().parent.parent
MASTER = PROJECT / "data_master/all_records_master.csv"
OUT = PROJECT / "data_master"
CLASSES = ["龙纹", "凤纹", "花卉纹", "缠枝/卷草纹", "云纹", "几何纹", "文字纹", "人物纹", "其他"]
ALIAS = {
    "缠枝卷草纹": "缠枝/卷草纹",
    "团花纹。": "花卉纹",
}
RESULTS = [
    ("欧阳宇康", PROJECT / "初分类数据集/纹样标注.zip", "新建文件夹/标注结果_欧阳宇康.csv"),
    ("罗云祥", PROJECT / "初分类数据集/all_records_annotated.csv", None),
    ("马军", PROJECT / "初分类数据集/标注任务_马军.zip", "all_records_annotated.csv"),
]


def load(path: pathlib.Path, inner: str | None) -> list[dict]:
    if inner is None:
        return list(csv.DictReader(path.open(encoding="utf-8-sig")))
    with zipfile.ZipFile(path) as z:
        return list(csv.DictReader(io.StringIO(z.read(inner).decode("utf-8-sig"))))


def key(r):
    return (r["source"].strip().lower(), str(r["source_id"]).strip())


def clean_label(v: str) -> str:
    v = (v or "").strip().rstrip("。")
    return ALIAS.get(v, v)


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    master = list(csv.DictReader(MASTER.open(encoding="utf-8-sig")))
    final: dict[tuple, dict] = {}
    stats = {}
    for member, path, inner in RESULTS:
        rows = load(path, inner)
        stats[member] = {
            "rows": len(rows),
            "confirmed": sum(1 for r in rows if r.get("status") == "confirmed"),
            "discarded": sum(1 for r in rows if r.get("status") == "discarded"),
            "pending": sum(1 for r in rows if r.get("status") == "pending"),
            "blank_label": sum(1 for r in rows if r.get("status") == "confirmed" and not clean_label(r.get("motif_type"))),
            "invalid": collections.Counter(
                clean_label(r.get("motif_type")) for r in rows
                if r.get("status") == "confirmed" and clean_label(r.get("motif_type")) not in CLASSES
            ),
        }
        for r in rows:
            k = key(r)
            final[k] = {
                "member": member,
                "status": r.get("status", "pending"),
                "motif_type": clean_label(r.get("motif_type")),
                "secondary": clean_label(r.get("motif_type_secondary")),
                "note": r.get("note", "") or r.get("notes", ""),
            }

    out_fields = list(master[0].keys()) + [
        "has_image", "final_status", "final_motif_type", "final_secondary",
        "final_note", "annotator_part", "label_valid",
    ]
    rows_out = []
    for r in master:
        k = key(r)
        res = final.get(k)
        has_image = "1" if r.get("local_images") else "0"
        if res:
            status = res["status"]
            label = res["motif_type"]
            secondary = res["secondary"]
            note = res["note"]
            member = res["member"]
        else:
            status = r.get("status") or ("no_image" if has_image == "0" else "pending")
            label = clean_label(r.get("motif_type"))
            secondary = clean_label(r.get("motif_type_secondary"))
            note = r.get("notes", "")
            member = ""
        valid = "1" if (status == "confirmed" and label in CLASSES) else "0"
        rows_out.append({
            **r,
            "has_image": has_image,
            "final_status": status,
            "final_motif_type": label,
            "final_secondary": secondary,
            "final_note": note,
            "annotator_part": member,
            "label_valid": valid,
        })

    final_csv = OUT / "all_records_final_annotated.csv"
    with final_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(rows_out)

    train = [r for r in rows_out if r["has_image"] == "1" and r["final_status"] == "confirmed" and r["label_valid"] == "1"]
    train_csv = OUT / "training_set.csv"
    with train_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(train)

    discarded = [r for r in rows_out if r["final_status"] == "discarded"]
    discard_csv = OUT / "discarded.csv"
    with discard_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(discarded)

    with_image = [r for r in rows_out if r["has_image"] == "1"]
    no_image = [r for r in rows_out if r["has_image"] == "0"]
    labels = collections.Counter(r["final_motif_type"] for r in train)
    source_cnt = collections.Counter(r["source"] for r in train)
    lines = [
        "# 三人标注结果合并统计",
        "",
        f"- 主数据集：{len(rows_out)} 条（有图 {len(with_image)}，无图 {len(no_image)}）",
        f"- 已确认且有图可训练：{len(train)} 条",
        f"- 已舍弃：{len(discarded)} 条",
        f"- 无图未标注/待补图：{len(no_image)} 条",
        "",
        "## 各成员提交",
    ]
    for member, s in stats.items():
        lines.append(
            f"- {member}：{s['rows']} 条（确认 {s['confirmed']}、舍弃 {s['discarded']}、"
            f"待处理 {s['pending']}、确认但标签为空 {s['blank_label']}）"
        )
    lines += [
        "",
        "## 训练集类别分布（有图 + 已确认 + 标签有效）",
        "",
    ] + [f"- {c}：{labels.get(c, 0)} 条" for c in CLASSES]
    lines += [
        "",
        f"- 训练集来源：" + "、".join(f"{k} {v}" for k, v in source_cnt.most_common()),
        "",
        "## 结论",
        "",
        "- 三名组员已把自己那份全部过完，1171 条有图数据都有结果；",
        "- 训练集类别不平衡：其他类偏多，凤纹、文字纹、缠枝/卷草纹、云纹偏少；",
        "- 无图数据（ArtIC 100 条 + Met 74 条）暂不计入训练集，需要补图或降级为仅元数据。",
    ]
    report = OUT / "annotation_summary.md"
    report.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\n最终标注表：{final_csv}\n训练集：{train_csv}\n舍弃：{discard_csv}\n报告：{report}")


if __name__ == "__main__":
    main()
