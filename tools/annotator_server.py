#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
纹样数据标注工具（本地网页，零第三方依赖）

启动：python tools/annotator_server.py
然后浏览器打开 http://127.0.0.1:8765

功能：逐条看图 → 确认自动标签 / 归入 8 类 / 舍弃（无纹样载体）；自动保存进度；
导出 data_starter/all_records_annotated.csv。
"""

import argparse
import csv
import json
import mimetypes
import pathlib
import sys
import threading
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PROJECT = pathlib.Path(__file__).resolve().parent.parent
HTML_PATH = pathlib.Path(__file__).resolve().parent / "annotator.html"

parser = argparse.ArgumentParser(description="纹样标注台")
parser.add_argument("--csv", default="", help="标注数据 CSV，默认 data_starter/all_records.csv")
parser.add_argument("--annotations", default="", help="进度文件，默认与 CSV 同目录的 annotations.json")
parser.add_argument("--port", type=int, default=8765, help="端口，默认 8765")
ARGS = parser.parse_args()

CSV_PATH = pathlib.Path(ARGS.csv) if ARGS.csv else PROJECT / "data_starter" / "all_records.csv"
if not CSV_PATH.is_absolute():
    CSV_PATH = PROJECT / CSV_PATH
ANN_PATH = pathlib.Path(ARGS.annotations) if ARGS.annotations else CSV_PATH.parent / "annotations.json"
if not ANN_PATH.is_absolute():
    ANN_PATH = PROJECT / ANN_PATH
HOST, PORT = "127.0.0.1", ARGS.port

FIELDS = [
    "source", "source_id", "title", "date_text", "century", "dynasty",
    "carrier", "motif_type", "motif_hint", "description", "image_urls",
    "local_images", "license", "source_url", "annotator", "notes",
]
EXTRA_FIELDS = ["status", "motif_type_secondary", "note"]
LOCK = threading.Lock()


def load_records() -> list[dict]:
    if not CSV_PATH.exists():
        raise SystemExit(f"找不到 {CSV_PATH}")
    records = []
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        for i, row in enumerate(csv.DictReader(f)):
            images = [p.strip() for p in (row.get("local_images") or "").split(" | ") if p.strip()]
            row["_index"] = i
            row["_images"] = images
            records.append(row)
    return records


def load_annotations() -> dict:
    if ANN_PATH.exists():
        return json.loads(ANN_PATH.read_text(encoding="utf-8"))
    return {}


def save_annotations(data: dict) -> None:
    tmp = ANN_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(ANN_PATH)


RECORDS = load_records()
ANNOTATIONS = load_annotations()


class Handler(BaseHTTPRequestHandler):
    server_version = "WenmaiAnnotator/1.0"

    def log_message(self, fmt, *args):  # 静默日志
        pass

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            self._send(200, HTML_PATH.read_bytes(), "text/html; charset=utf-8")
            return

        if path == "/api/records":
            payload = []
            for r in RECORDS:
                key = f"{r['source']}:{r['source_id']}"
                ann = ANNOTATIONS.get(key, {})
                payload.append({
                    "index": r["_index"],
                    "source": r.get("source", ""),
                    "source_id": r.get("source_id", ""),
                    "title": r.get("title", ""),
                    "date_text": r.get("date_text", ""),
                    "century": r.get("century", ""),
                    "dynasty": r.get("dynasty", ""),
                    "carrier": r.get("carrier", ""),
                    "motif_hint": r.get("motif_hint", ""),
                    "motif_type": ann.get("motif_type") or r.get("motif_type", ""),
                    "description": r.get("description", ""),
                    "license": r.get("license", ""),
                    "source_url": r.get("source_url", ""),
                    "images": [f"/img/{r['_index']}/{k}" for k in range(len(r["_images"]))],
                    "annotation": ann,
                })
            self._send(200, json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                       "application/json; charset=utf-8")
            return

        if path.startswith("/img/"):
            parts = path.strip("/").split("/")
            try:
                idx, k = int(parts[1]), int(parts[2])
                rel = RECORDS[idx]["_images"][k]
            except (IndexError, ValueError):
                self._send(404, b"not found", "text/plain")
                return
            file_path = (PROJECT / rel).resolve()
            if not str(file_path).startswith(str(PROJECT)) or not file_path.exists():
                self._send(404, b"not found", "text/plain")
                return
            ctype = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
            self._send(200, file_path.read_bytes(), ctype)
            return

        if path == "/api/export":
            fields = FIELDS + EXTRA_FIELDS
            import io
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=fields)
            writer.writeheader()
            for r in RECORDS:
                key = f"{r['source']}:{r['source_id']}"
                ann = ANNOTATIONS.get(key, {})
                row = {k: r.get(k, "") for k in FIELDS}
                if ann.get("motif_type"):
                    row["motif_type"] = ann["motif_type"]
                row["status"] = ann.get("status", "pending")
                row["motif_type_secondary"] = ann.get("motif_type_secondary", "")
                row["note"] = ann.get("note", "")
                writer.writerow(row)
            body = buf.getvalue().encode("utf-8-sig")
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", "attachment; filename=all_records_annotated.csv")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:  # noqa: N802
        if urllib.parse.urlparse(self.path).path != "/api/save":
            self._send(404, b"not found", "text/plain")
            return
        length = int(self.headers.get("Content-Length") or 0)
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            self._send(400, b"bad request", "text/plain")
            return
        key = f"{payload.get('source')}:{payload.get('source_id')}"
        if not key or ":" not in key:
            self._send(400, b"bad key", "text/plain")
            return
        with LOCK:
            ann = ANNOTATIONS.setdefault(key, {})
            for field in ("status", "motif_type", "motif_type_secondary", "note"):
                if field in payload:
                    ann[field] = payload[field]
            ann["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_annotations(ANNOTATIONS)
        self._send(200, b'{"ok":true}', "application/json")


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    print(f"标注工具已启动：http://{HOST}:{PORT}")
    print(f"数据：{CSV_PATH}（{len(RECORDS)} 条）")
    print(f"进度文件：{ANN_PATH}")
    print("按 Ctrl+C 结束。")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
