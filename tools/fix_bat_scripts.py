#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把所有 .bat 统一为纯 ASCII + CRLF，并修复任务包内的启动脚本。"""

import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"

PACKAGE_BAT = (
    "@echo off\r\n"
    'cd /d "%~dp0"\r\n'
    "where python >nul 2>nul\r\n"
    "if %errorlevel%==0 (\r\n"
    "  python tools\\annotator_server.py --csv records.csv\r\n"
    ") else (\r\n"
    "  py -3 tools\\annotator_server.py --csv records.csv\r\n"
    ")\r\n"
    "pause\r\n"
)


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    for p in sorted(TOOLS.glob("*.bat")):
        text = p.read_text(encoding="utf-8", errors="ignore")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        bad = [c for c in text if ord(c) > 127]
        p.write_bytes(text.replace("\n", "\r\n").encode("ascii", errors="replace"))
        print(f"{p.name}: {'含非 ASCII 已替换' if bad else '纯 ASCII'}，已改为 CRLF")

    for member in ("欧阳宇康", "罗云祥", "马军"):
        pkg = ROOT / "annotation_packages" / f"标注任务_{member}"
        if not pkg.exists():
            continue
        (pkg / "启动标注.bat").write_bytes(PACKAGE_BAT.encode("ascii"))
        src = pkg / f"annotations_{member}.json"
        dst = pkg / "annotations.json"
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)
        print(f"任务包 {member}: 启动脚本已修复，annotations.json 存在={dst.exists()}")


if __name__ == "__main__":
    main()
