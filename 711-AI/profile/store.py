"""
画像存储 - MVP 用 JSON 文件,生产换 DB(Redis / Postgres) 改这一个文件即可。
"""
from __future__ import annotations
import json
import os
import threading
import time
from pathlib import Path
from profile.schema import UserProfile


_LOCK = threading.Lock()


def _store_path() -> Path:
    p = os.getenv("PROFILE_STORE_PATH", "./data/user_profiles.json")
    return Path(p)


def _read_all() -> dict:
    path = _store_path()
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _write_all(data: dict) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def load_profile(user_id: str) -> UserProfile:
    """读出画像,不存在则新建(不写盘)。"""
    with _LOCK:
        data = _read_all()
        d = data.get(user_id)
        if d:
            return UserProfile.from_dict(d)
        return UserProfile.new(user_id)


def save_profile(profile: UserProfile) -> None:
    """覆盖写。"""
    with _LOCK:
        data = _read_all()
        profile.last_updated = time.time()
        data[profile.user_id] = profile.to_dict()
        _write_all(data)
