from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any


class VerifyCache:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
        self._lock = threading.Lock()
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute(
            """CREATE TABLE IF NOT EXISTS verify_cache (
                key TEXT PRIMARY KEY,
                response_json TEXT NOT NULL,
                created_at REAL NOT NULL,
                last_hit_at REAL NOT NULL,
                hits INTEGER NOT NULL DEFAULT 0
            )"""
        )

    def get(self, key: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT response_json FROM verify_cache WHERE key=?",
                (key,),
            ).fetchone()
            if row is None:
                return None
            self._conn.execute(
                "UPDATE verify_cache SET last_hit_at=?, hits=hits+1 WHERE key=?",
                (time.time(), key),
            )
        return json.loads(row[0])

    def put(self, key: str, response: dict[str, Any]) -> None:
        payload = json.dumps(response, ensure_ascii=False)
        now = time.time()
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO verify_cache "
                "(key, response_json, created_at, last_hit_at, hits) "
                "VALUES (?, ?, ?, ?, 0)",
                (key, payload, now, now),
            )

    def summary(self) -> dict[str, int]:
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(LENGTH(response_json)), 0), COALESCE(SUM(hits), 0) "
                "FROM verify_cache"
            ).fetchone()
        return {
            "cache_entries": int(row[0]),
            "cache_bytes": int(row[1]),
            "cache_total_hits": int(row[2]),
        }

    def close(self) -> None:
        with self._lock:
            self._conn.close()

