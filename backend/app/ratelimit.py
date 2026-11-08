from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque

MAX_ATTEMPTS = int(os.getenv("WENMAI_LOGIN_MAX_ATTEMPTS", "5"))
WINDOW_SECONDS = int(os.getenv("WENMAI_LOGIN_WINDOW_SECONDS", "900"))

_lock = threading.Lock()
_failures: dict[str, deque[float]] = defaultdict(deque)


def login_key(username: str, client_host: str | None) -> str:
    return f"{(username or '').strip().lower()}|{client_host or 'unknown'}"


def _prune(entries: deque[float], now: float) -> None:
    while entries and now - entries[0] > WINDOW_SECONDS:
        entries.popleft()


def remaining_lock_seconds(key: str) -> int:
    with _lock:
        now = time.monotonic()
        entries = _failures[key]
        _prune(entries, now)
        if len(entries) < MAX_ATTEMPTS:
            return 0
        return max(1, int(WINDOW_SECONDS - (now - entries[0])))


def record_failure(key: str) -> None:
    with _lock:
        now = time.monotonic()
        entries = _failures[key]
        _prune(entries, now)
        entries.append(now)


def clear_failures(key: str) -> None:
    with _lock:
        _failures.pop(key, None)


def reset_all() -> None:
    with _lock:
        _failures.clear()
