#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把前端样式中所有小于 18px 的 font-size 统一提升到 18px。"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent / "frontend/src"
PATTERN = re.compile(r"font-size:\s*(\d+(?:\.\d+)?)px")


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    changed = 0
    for path in [*ROOT.rglob("*.css"), *ROOT.rglob("*.vue")]:
        text = path.read_text(encoding="utf-8")

        def replace(match: re.Match) -> str:
            nonlocal changed
            if float(match.group(1)) < 18:
                changed += 1
                return "font-size: 18px"
            return match.group(0)

        updated = PATTERN.sub(replace, text)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
    print(f"replaced={changed}")
    remaining = []
    for path in [*ROOT.rglob("*.css"), *ROOT.rglob("*.vue")]:
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            match = PATTERN.search(line)
            if match and float(match.group(1)) < 18:
                remaining.append((str(path), line_no, line.strip()))
    print(f"remaining={len(remaining)}")
    for item in remaining[:10]:
        print(item)


if __name__ == "__main__":
    main()
