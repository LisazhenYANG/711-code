from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import sqlite3
from typing import Any


DEFAULT_DB_PATH = Path(__file__).resolve().parent / "data" / "manyou.sqlite3"
ALLOWED_TABLES = {"kv", "trips", "feedback", "ai_tickets", "ai_reservations"}


def app_db_path() -> Path:
    configured = os.environ.get("MANYOU_DB_PATH")
    return Path(configured) if configured else DEFAULT_DB_PATH


def db() -> sqlite3.Connection:
    path = app_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS kv (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    for table in ("trips", "feedback", "ai_tickets", "ai_reservations"):
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table} (
                id TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
    conn.commit()
    return conn


def db_get_json(table: str, key: str) -> dict[str, Any] | None:
    _ensure_table(table)
    column = "key" if table == "kv" else "id"
    conn = db()
    try:
        row = conn.execute(
            f"SELECT value FROM {table} WHERE {column} = ?", (key,)
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    return json.loads(row["value"])


def db_put_json(table: str, key: str, value: dict[str, Any]) -> None:
    _ensure_table(table)
    now = datetime.now().isoformat(timespec="seconds")
    column = "key" if table == "kv" else "id"
    conn = db()
    try:
        conn.execute(
            f"""
            INSERT INTO {table} ({column}, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT({column}) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (key, json.dumps(value, ensure_ascii=False), now),
        )
        conn.commit()
    finally:
        conn.close()


def db_list_json(table: str) -> list[dict[str, Any]]:
    _ensure_table(table)
    conn = db()
    try:
        rows = conn.execute(
            f"SELECT value FROM {table} ORDER BY updated_at DESC"
        ).fetchall()
    finally:
        conn.close()
    return [json.loads(row["value"]) for row in rows]


def db_delete_json(table: str, key: str) -> bool:
    _ensure_table(table)
    column = "key" if table == "kv" else "id"
    conn = db()
    try:
        cursor = conn.execute(f"DELETE FROM {table} WHERE {column} = ?", (key,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def _ensure_table(table: str) -> None:
    if table not in ALLOWED_TABLES:
        raise ValueError(f"unsupported table: {table}")
