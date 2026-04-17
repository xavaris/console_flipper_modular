from __future__ import annotations

import asyncio
import json
import sqlite3
from pathlib import Path
from typing import Any

from .models import Offer
from .utils.misc import compact_spaces, normalize_url, now_ts


class StateStore:
    def __init__(self, path: str):
        self.path = path
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = asyncio.Lock()
        self._init_db()

    def _init_db(self) -> None:
        cur = self._conn.cursor()
        cur.executescript(
            """
            PRAGMA journal_mode=WAL;

            CREATE TABLE IF NOT EXISTS seen_offers (
                dedupe_key TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                console_key TEXT NOT NULL,
                offer_id TEXT NOT NULL,
                url TEXT NOT NULL,
                title TEXT,
                price INTEGER,
                created_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS kv (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS run_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at INTEGER NOT NULL,
                finished_at INTEGER,
                status TEXT NOT NULL,
                posted_count INTEGER NOT NULL DEFAULT 0,
                discovered_count INTEGER NOT NULL DEFAULT 0,
                error_message TEXT
            );
            """
        )
        self._conn.commit()

    async def close(self) -> None:
        async with self._lock:
            self._conn.commit()
            self._conn.close()

    async def has_seen(self, dedupe_key: str) -> bool:
        async with self._lock:
            row = self._conn.execute(
                "SELECT 1 FROM seen_offers WHERE dedupe_key = ?",
                (dedupe_key,),
            ).fetchone()
            return row is not None

    async def mark_seen(self, offer: Offer) -> None:
        async with self._lock:
            self._conn.execute(
                """
                INSERT OR IGNORE INTO seen_offers
                (dedupe_key, source, console_key, offer_id, url, title, price, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    offer.dedupe_key,
                    offer.source,
                    offer.console_key,
                    offer.offer_id,
                    normalize_url(offer.url),
                    offer.title,
                    offer.price,
                    int(now_ts()),
                ),
            )
            self._conn.commit()

    async def get_list(self, key: str, default: list[str] | None = None) -> list[str]:
        default = default or []
        async with self._lock:
            row = self._conn.execute("SELECT value FROM kv WHERE key = ?", (key,)).fetchone()
            if not row:
                return list(default)
            try:
                data = json.loads(row["value"])
            except json.JSONDecodeError:
                return list(default)
            if isinstance(data, list):
                return [str(x) for x in data]
            return list(default)

    async def set_list(self, key: str, values: list[str]) -> None:
        unique = sorted({compact_spaces(v).lower() for v in values if compact_spaces(v)})
        async with self._lock:
            self._conn.execute(
                "INSERT INTO kv(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, json.dumps(unique, ensure_ascii=False)),
            )
            self._conn.commit()

    async def add_list_item(self, key: str, value: str) -> list[str]:
        current = await self.get_list(key)
        current.append(value)
        await self.set_list(key, current)
        return await self.get_list(key)

    async def remove_list_item(self, key: str, value: str) -> list[str]:
        needle = compact_spaces(value).lower()
        current = [v for v in await self.get_list(key) if v.lower() != needle]
        await self.set_list(key, current)
        return current

    async def get_json(self, key: str, default: dict[str, Any] | None = None) -> dict[str, Any]:
        default = default or {}
        async with self._lock:
            row = self._conn.execute("SELECT value FROM kv WHERE key = ?", (key,)).fetchone()
            if not row:
                return dict(default)
            try:
                data = json.loads(row["value"])
            except json.JSONDecodeError:
                return dict(default)
            return data if isinstance(data, dict) else dict(default)

    async def set_json(self, key: str, value: dict[str, Any]) -> None:
        async with self._lock:
            self._conn.execute(
                "INSERT INTO kv(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, json.dumps(value, ensure_ascii=False)),
            )
            self._conn.commit()

    async def log_run_start(self) -> int:
        async with self._lock:
            cur = self._conn.execute(
                "INSERT INTO run_log(started_at, status, posted_count, discovered_count) "
                "VALUES(?, 'running', 0, 0)",
                (int(now_ts()),),
            )
            self._conn.commit()
            return int(cur.lastrowid)

    async def log_run_finish(
        self,
        run_id: int,
        status: str,
        discovered: int,
        posted: int,
        error_message: str = "",
    ) -> None:
        async with self._lock:
            self._conn.execute(
                """
                UPDATE run_log
                SET finished_at = ?, status = ?, posted_count = ?, discovered_count = ?, error_message = ?
                WHERE id = ?
                """,
                (int(now_ts()), status, posted, discovered, error_message[:2000], run_id),
            )
            self._conn.commit()

    async def get_last_run(self) -> dict[str, Any] | None:
        async with self._lock:
            row = self._conn.execute("SELECT * FROM run_log ORDER BY id DESC LIMIT 1").fetchone()
            return dict(row) if row else None
