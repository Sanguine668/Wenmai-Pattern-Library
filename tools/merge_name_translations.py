"""合并批次译文，生成最终文物名并可选写库。

用法：
    python tools/merge_name_translations.py --preview data/_name_final.csv
    python tools/merge_name_translations.py --apply
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "tools"))
import localize_names as fallback  # noqa: E402

DB = PROJECT / "data" / "wenmai.db"
BATCH_DIR = PROJECT / "data" / "name_batches"
OVERRIDES_FILE = PROJECT / "data" / "name_overrides.json"

LATIN_RE = re.compile(r"[A-Za-z]")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def load_batches() -> dict[str, dict]:
    translations: dict[str, dict] = {}
    for input_path in sorted(BATCH_DIR.glob("in_*.json")):
        index = input_path.stem.split("_")[1]
        output_path = BATCH_DIR / f"out_{index}.json"
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        if not output_path.is_file():
            print(f"[warn] 缺少输出批次 {output_path.name}，{len(payload)} 条将回退规则引擎")
            continue
        output = json.loads(output_path.read_text(encoding="utf-8"))
        by_id = {item["id"]: item for item in output if isinstance(item, dict) and item.get("id")}
        missing = [item["id"] for item in payload if item["id"] not in by_id]
        if missing:
            print(f"[warn] {output_path.name} 缺 {len(missing)} 条：{missing[:5]}")
        for item in payload:
            translated = by_id.get(item["id"])
            if translated:
                translations[item["id"]] = translated
    return translations


def valid_name(name: str) -> bool:
    name = (name or "").strip()
    return bool(name) and bool(CJK_RE.search(name)) and not LATIN_RE.search(name) and len(name) <= 32


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", default="")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    translations = load_batches()
    overrides: dict[str, str] = {}
    if OVERRIDES_FILE.is_file():
        overrides = json.loads(OVERRIDES_FILE.read_text(encoding="utf-8"))
    connection = sqlite3.connect(DB)
    connection.row_factory = sqlite3.Row
    rows = [
        dict(r)
        for r in connection.execute(
            "select id, name, original_title, motif_type, carrier, dynasty from patterns order by id"
        )
    ]

    results = []
    stats = {"llm": 0, "rule": 0, "chinese": 0, "generic": 0, "override": 0}
    for row in rows:
        title = row["original_title"] or ""
        translated: dict = {}
        if row["id"] in overrides:
            name = overrides[row["id"]]
            source = "override"
        elif CJK_RE.search(title):
            name = fallback.clean_title(title)
            if not valid_name(name):
                name = row["name"]
            source = "chinese"
        else:
            translated = translations.get(row["id"], {})
            name = (translated.get("name") or "").strip()
            if valid_name(name):
                source = "llm"
            else:
                name, confidence = fallback.translate_title(title)
                source = "rule" if valid_name(name) else "generic"
            if not valid_name(name):
                carrier = (row["carrier"] or "").strip()
                name = f"馆藏{carrier}" if carrier and carrier != "其他" else "馆藏文物"
                source = "generic"
        confidence = translated.get("confidence", "") if source == "llm" else ""
        stats[source] = stats.get(source, 0) + 1
        results.append(
            {
                "id": row["id"],
                "old_name": row["name"],
                "original_title": title,
                "new_name": name,
                "motif": row["motif_type"],
                "carrier": row["carrier"],
                "dynasty": row["dynasty"],
                "source": source,
                "confidence": confidence,
            }
        )

    print("stats", stats)
    print("unique names", len({item["new_name"] for item in results}))

    if args.preview:
        path = Path(args.preview)
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(results[0].keys()))
            writer.writeheader()
            writer.writerows(results)
        print("preview", path)

    if args.apply:
        with connection:
            for item in results:
                connection.execute(
                    "update patterns set name = ? where id = ?",
                    (item["new_name"], item["id"]),
                )
        print("applied", len(results))
    connection.close()


if __name__ == "__main__":
    main()
