from __future__ import annotations

import argparse
import secrets
from pathlib import Path

from sqlalchemy import select

from .config import ADMIN_PASSWORD_FILE, ADMIN_USERNAME, DEMO_USERNAME
from .database import Base, SessionLocal, engine
from .models import User
from .security import hash_password


def set_password(username: str, password: str, write_file: bool) -> int:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == username))
        if user is None:
            print(f"用户 {username} 不存在，未做修改。")
            return 1
        if user.username == DEMO_USERNAME:
            print("游客兜底账号不允许设置密码。")
            return 1
        user.password_hash = hash_password(password)
        if username == ADMIN_USERNAME:
            user.is_admin = True
            user.is_active = True
        db.commit()
    if write_file:
        Path(ADMIN_PASSWORD_FILE).write_text(password, encoding="utf-8")
        print(f"已重置 {username} 的密码，新密码写入 {ADMIN_PASSWORD_FILE}")
    else:
        print(f"已重置 {username} 的密码。")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.admin_tool",
        description="管理员账号维护：重置密码、重新启用账号。",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    reset = subparsers.add_parser("set-password", help="重置管理员密码")
    reset.add_argument("--password", help="新密码；不填则使用随机密码")
    reset.add_argument("--username", default=ADMIN_USERNAME)
    reset.add_argument(
        "--generate",
        action="store_true",
        help="生成随机密码并写入 data/admin-initial-password.txt",
    )
    args = parser.parse_args(argv)

    if args.command != "set-password":
        parser.print_help()
        return 1

    password = args.password
    generated = False
    if args.generate or not password:
        password = secrets.token_urlsafe(12)
        generated = True
    return set_password(args.username, password, write_file=generated)


if __name__ == "__main__":
    raise SystemExit(main())
