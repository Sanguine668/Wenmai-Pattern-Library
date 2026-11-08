#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""列出前端生成数据中的标题与分类，用于命名审校。"""

import json
import pathlib
import sys

path = pathlib.Path(__file__).resolve().parent.parent / "frontend/src/data/patterns.js"
text = path.read_text(encoding="utf-8")
start = text.find("export const patterns")
data = json.loads(text[text.find("[", start):])

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
for index, item in enumerate(data, 1):
    print(
        f"{index:02d} | {item['name']} | {item['originalTitle']} | "
        f"{item['motifType']} | {item['carrier']} | {item['dynasty']}"
    )
