from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = PROJECT_ROOT / "data_master" / "all_records_final_annotated.csv"
DATABASE_DIR = PROJECT_ROOT / "data"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_DATABASE_URL = f"sqlite:///{(DATABASE_DIR / 'wenmai.db').as_posix()}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
DEMO_USERNAME = os.getenv("DEMO_USERNAME", "demo")
API_TITLE = "中华纹脉资源库 API"
API_VERSION = "1.0.0"

# 认证配置：密钥优先取环境变量，否则生成一次并落盘到 data/.jwt_secret。
JWT_ALGORITHM = "HS256"
JWT_SECRET_FILE = DATABASE_DIR / ".jwt_secret"


def _resolve_jwt_secret() -> str:
    configured = os.getenv("WENMAI_JWT_SECRET", "").strip()
    if configured:
        if len(configured) < 32:
            print(
                "[auth] WENMAI_JWT_SECRET 长度不足 32，建议更换为更长的随机密钥。",
                file=sys.stderr,
                flush=True,
            )
        return configured

    try:
        existing = JWT_SECRET_FILE.read_text(encoding="utf-8").strip()
        if existing:
            return existing
    except FileNotFoundError:
        pass

    generated = secrets.token_urlsafe(48)
    try:
        fd = os.open(JWT_SECRET_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(generated)
        return generated
    except FileExistsError:
        existing = JWT_SECRET_FILE.read_text(encoding="utf-8").strip()
        if existing:
            return existing
        return generated
    except OSError as error:
        print(
            f"[auth] 无法写入 {JWT_SECRET_FILE}（{error}），本次使用临时密钥；"
            "重启后已签发令牌会失效，请配置 WENMAI_JWT_SECRET。",
            file=sys.stderr,
            flush=True,
        )
        return generated


JWT_SECRET = _resolve_jwt_secret()
TOKEN_MINUTES = int(os.getenv("WENMAI_TOKEN_MINUTES", "720"))

# 管理员账号：密码只从环境变量或初始化文件读取，代码中不再内置默认口令。
ADMIN_USERNAME = os.getenv("WENMAI_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("WENMAI_ADMIN_PASSWORD", "").strip()
ADMIN_PASSWORD_FILE = DATABASE_DIR / "admin-initial-password.txt"
ADMIN_DISPLAY_NAME = os.getenv("WENMAI_ADMIN_DISPLAY_NAME", "系统管理员")
ADMIN_EMAIL = os.getenv("WENMAI_ADMIN_EMAIL", "admin@wenmai.local")
