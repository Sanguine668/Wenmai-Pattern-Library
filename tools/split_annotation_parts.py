#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把有图数据均衡切成三份，供三名组员分别标注。"""

import collections
import csv
import hashlib
import json
import pathlib
import sys

PROJECT = pathlib.Path(__file__).resolve().parent.parent
SRC = PROJECT / "data_master/all_records_with_images.csv"
FIG = PROJECT / "data_master/figure_candidates.csv"
OUT = PROJECT / "data_annotation"
OUT.mkdir(parents=True, exist_ok=True)

MEMBERS = ["欧阳宇康", "罗云祥", "马军"]


def sort_key(r):
    sid = r["source_id"]
    return int(sid) if sid.isdigit() else 10**12


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    rows = list(csv.DictReader(SRC.open(encoding="utf-8-sig")))
    fields = list(rows[0].keys())

    figure_keys = set()
    if FIG.exists():
        for r in csv.DictReader(FIG.open(encoding="utf-8-sig")):
            figure_keys.add((r["source"], r["source_id"]))

    groups = collections.defaultdict(list)
    for r in rows:
        groups[r["source"]].append(r)

    parts = {m: [] for m in MEMBERS}
    for source, group in sorted(groups.items()):
        group.sort(key=lambda r: hashlib.md5(f"{r['source']}:{r['source_id']}".encode()).hexdigest())
        for i, r in enumerate(group):
            parts[MEMBERS[i % len(MEMBERS)]].append(r)

    summary = []
    for idx, member in enumerate(MEMBERS, 1):
        part = sorted(parts[member], key=sort_key)
        csv_path = OUT / f"part{idx}_{member}.csv"
        with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(part)
        ann_path = OUT / f"annotations_{member}.json"
        if not ann_path.exists():
            ann_path.write_text("{}", encoding="utf-8")
        src_count = collections.Counter(r["source"] for r in part)
        fig_count = sum(1 for r in part if (r["source"], r["source_id"]) in figure_keys)
        pending = sum(1 for r in part if r.get("status") == "pending")
        summary.append(
            f"- {member}：{len(part)} 条（待处理 {pending}，人物纹候选 {fig_count}）；"
            f"来源 " + "、".join(f"{k} {v}" for k, v in sorted(src_count.items()))
        )

    readme = [
        "# 数据标注任务（三人分工）",
        "",
        "## 分配结果",
        "",
        *summary,
        "",
        "## 怎么标",
        "",
        "1. 双击自己名字对应的启动脚本（tools/启动标注-姓名.bat），浏览器打开 http://127.0.0.1:8765；",
        "2. 逐条看图：有明确纹样 → 点 9 类按钮之一（龙纹/凤纹/花卉纹/缠枝卷草纹/云纹/几何纹/文字纹/人物纹/其他）；",
        "3. 素面无纹、只有器物造型或立体造像 → 点“舍弃”；",
        "4. 人物题材图案（婴戏、仕女、高士、供养人、佛教人物、故事场景）→ 人物纹；",
        "5. 细分类写“次标签”（如双龙纹、莲花纹、忍冬纹）；有疑问写在备注；",
        "6. 每步自动保存，顶部可筛选“待处理/有提示/已确认/已舍弃”；",
        "7. 标完点“导出标注 CSV”，把自己的 partX_姓名.csv、annotations_姓名.json 和导出 CSV 一起打包交回。",
        "",
        "## 统一标准",
        "",
        "- 只按图片里实际可见的纹样判断，不按标题猜；",
        "- 标签控制在 9 类内，细分放次标签；",
        "- 舍弃的条目不进入训练集；",
        "- 进度文件不要删，换电脑时一起带走。",
    ]
    (OUT / "README.md").write_text("\n".join(readme), encoding="utf-8")
    print("\n".join(readme))
    print(f"\n输出目录：{OUT}")


if __name__ == "__main__":
    main()
