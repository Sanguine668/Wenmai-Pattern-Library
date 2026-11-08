#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""启动标注任务的统一入口（bat 只调用它，避免中文路径进入 cmd）。"""

import argparse
import pathlib
import subprocess
import sys

PROJECT = pathlib.Path(__file__).resolve().parent.parent
SERVER = pathlib.Path(__file__).resolve().parent / "annotator_server.py"

TASKS = {
    "starter": ("data_starter/all_records.csv", "data_starter/annotations.json", 8765),
    "other": ("data_review/other_review.csv", "data_review/annotations_其他复核.json", 8765),
    "supplement": ("data_review/supplement_review.csv", "data_review/annotations_补充复核.json", 8765),
    "part1": ("data_annotation/part1_欧阳宇康.csv", "data_annotation/annotations_欧阳宇康.json", 8765),
    "part2": ("data_annotation/part2_罗云祥.csv", "data_annotation/annotations_罗云祥.json", 8765),
    "part3": ("data_annotation/part3_马军.csv", "data_annotation/annotations_马军.json", 8765),
    "all": ("data_master/all_records_with_images.csv", "data_master/annotations.json", 8765),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("task", choices=sorted(TASKS))
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()

    csv_rel, ann_rel, port = TASKS[args.task]
    port = args.port or port
    csv_path = PROJECT / csv_rel
    ann_path = PROJECT / ann_rel
    if not csv_path.exists():
        print(f"找不到数据文件：{csv_path}")
        sys.exit(1)

    print("=" * 52)
    print("中华纹脉标注台")
    print(f"任务：{args.task}")
    print(f"数据：{csv_rel}（{sum(1 for _ in csv_path.open(encoding='utf-8-sig')) - 1} 条）")
    print(f"进度：{ann_rel}")
    print(f"地址：http://127.0.0.1:{port}")
    print("按 Ctrl+C 结束服务。")
    print("=" * 52)

    cmd = [
        sys.executable, str(SERVER),
        "--csv", str(csv_path),
        "--annotations", str(ann_path),
        "--port", str(port),
    ]
    subprocess.run(cmd, check=False)


if __name__ == "__main__":
    main()
