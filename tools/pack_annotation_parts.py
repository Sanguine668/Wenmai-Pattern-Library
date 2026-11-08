#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把三份标注任务打包成自包含 zip（CSV + 图片 + 标注工具），方便发给组员。"""

import csv
import pathlib
import shutil
import sys
import zipfile

PROJECT = pathlib.Path(__file__).resolve().parent.parent
PARTS = PROJECT / "data_annotation"
OUT = PROJECT / "annotation_packages"
TOOLS = PROJECT / "tools"
MEMBERS = [
    ("part1_欧阳宇康.csv", "annotations_欧阳宇康.json", "欧阳宇康"),
    ("part2_罗云祥.csv", "annotations_罗云祥.json", "罗云祥"),
    ("part3_马军.csv", "annotations_马军.json", "马军"),
]


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    OUT.mkdir(parents=True, exist_ok=True)
    for csv_name, ann_name, member in MEMBERS:
        src_csv = PARTS / csv_name
        if not src_csv.exists():
            print(f"跳过缺失文件：{src_csv}")
            continue
        pkg = OUT / f"标注任务_{member}"
        if pkg.exists():
            shutil.rmtree(pkg)
        (pkg / "images").mkdir(parents=True)
        (pkg / "tools").mkdir(parents=True)
        shutil.copy2(TOOLS / "annotator_server.py", pkg / "tools")
        shutil.copy2(TOOLS / "annotator.html", pkg / "tools")
        guide = PARTS / "使用说明.md"
        if guide.exists():
            shutil.copy2(guide, pkg / "使用说明.md")

        rows = list(csv.DictReader(src_csv.open(encoding="utf-8-sig")))
        fields = list(rows[0].keys())
        copied = 0
        for r in rows:
            new_paths = []
            for p in (r.get("local_images") or "").split("|"):
                p = p.strip()
                if not p:
                    continue
                src = PROJECT / p
                if not src.exists():
                    continue
                dest = pkg / "images" / r["source"] / r["source_id"] / src.name
                dest.parent.mkdir(parents=True, exist_ok=True)
                if not dest.exists():
                    shutil.copy2(src, dest)
                    copied += 1
                new_paths.append(f"images/{r['source']}/{r['source_id']}/{src.name}")
            r["local_images"] = "|".join(new_paths)

        with (pkg / "records.csv").open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

        shutil.copy2(PARTS / ann_name, pkg / ann_name) if (PARTS / ann_name).exists() else (
            pkg / ann_name
        ).write_text("{}", encoding="utf-8")

        (pkg / "启动标注.bat").write_text(
            "@echo off\r\n"
            "cd /d \"%~dp0\"\r\n"
            "where python >nul 2>nul\r\n"
            "if %errorlevel%==0 (\r\n"
            "  python tools\\annotator_server.py --csv records.csv\r\n"
            ") else (\r\n"
            "  py -3 tools\\annotator_server.py --csv records.csv\r\n"
            ")\r\n"
            "pause\r\n",
            encoding="ascii",
            newline="",
        )

        zip_path = OUT / f"标注任务_{member}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=3) as z:
            for f in pkg.rglob("*"):
                if f.is_file():
                    z.write(f, f.relative_to(pkg.parent))
        size_mb = zip_path.stat().st_size / 1024 / 1024
        print(f"{member}: {len(rows)} 条，复制图片 {copied} 张，压缩包 {size_mb:.1f} MB -> {zip_path}")


if __name__ == "__main__":
    main()
