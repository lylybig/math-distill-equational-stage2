from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
import hashlib
from pathlib import Path
from typing import Any


TERMINAL_STATUSES = {"done", "failed", "cancelled"}


class ControlStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
        self._lock = threading.Lock()
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                request_key TEXT NOT NULL,
                request_json TEXT NOT NULL,
                status TEXT NOT NULL,
                result_json TEXT,
                error TEXT,
                backend_url TEXT,
                attempts INTEGER NOT NULL DEFAULT 0,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                started_at REAL,
                finished_at REAL
            )"""
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_jobs_request_key_status ON jobs(request_key, status)"
        )
        self._conn.execute(
            """CREATE TABLE IF NOT EXISTS verify_cache (
                request_key TEXT PRIMARY KEY,
                result_json TEXT NOT NULL,
                created_at REAL NOT NULL,
                last_hit_at REAL NOT NULL,
                hits INTEGER NOT NULL DEFAULT 0
            )"""
        )
        self._redact_terminal_requests()

    def create_or_get_job(self, *, request_key: str, request: dict[str, Any]) -> tuple[str, bool]:
        now = time.time()
        request_json = json.dumps(request, ensure_ascii=False, sort_keys=True)
        with self._lock:
            cached = self._cache_get_locked(request_key)
            if cached is not None:
                job_id = uuid.uuid4().hex
                self._conn.execute(
                    "INSERT INTO jobs "
                    "(job_id, request_key, request_json, status, result_json, attempts, created_at, "
                    "updated_at, started_at, finished_at) "
                    "VALUES (?, ?, ?, 'done', ?, 0, ?, ?, ?, ?)",
                    (
                        job_id,
                        request_key,
                        _terminal_request_json(request),
                        json.dumps(cached, ensure_ascii=False),
                        now,
                        now,
                        now,
                        now,
                    ),
                )
                return job_id, False

            row = self._conn.execute(
                "SELECT job_id FROM jobs WHERE request_key=? AND status NOT IN ('done', 'failed', 'cancelled') "
                "ORDER BY created_at ASC LIMIT 1",
                (request_key,),
            ).fetchone()
            if row is not None:
                return str(row[0]), False

            job_id = uuid.uuid4().hex
            self._conn.execute(
                "INSERT INTO jobs "
                "(job_id, request_key, request_json, status, attempts, created_at, updated_at) "
                "VALUES (?, ?, ?, 'queued', 0, ?, ?)",
                (job_id, request_key, request_json, now, now),
            )
            return job_id, True

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT job_id, request_key, request_json, status, result_json, error, backend_url, "
                "attempts, created_at, updated_at, started_at, finished_at "
                "FROM jobs WHERE job_id=?",
                (job_id,),
            ).fetchone()
        if row is None:
            return None
        return _row_to_job(row)

    def mark_running(self, job_id: str, *, backend_url: str) -> None:
        now = time.time()
        with self._lock:
            self._conn.execute(
                "UPDATE jobs SET status='running', backend_url=?, attempts=attempts+1, "
                "updated_at=?, started_at=COALESCE(started_at, ?) WHERE job_id=?",
                (backend_url, now, now, job_id),
            )

    def mark_queued(self, job_id: str, *, error: str | None = None) -> None:
        now = time.time()
        with self._lock:
            self._conn.execute(
                "UPDATE jobs SET status='queued', error=?, updated_at=? WHERE job_id=?",
                (error, now, job_id),
            )

    def mark_done(self, job_id: str, *, result: dict[str, Any], cache: bool = True) -> None:
        now = time.time()
        result_json = json.dumps(result, ensure_ascii=False)
        with self._lock:
            row = self._conn.execute(
                "SELECT request_key, request_json FROM jobs WHERE job_id=?",
                (job_id,),
            ).fetchone()
            self._conn.execute(
                "UPDATE jobs SET status='done', request_json=?, result_json=?, error=NULL, "
                "updated_at=?, finished_at=? "
                "WHERE job_id=?",
                (_terminal_request_json_from_db_row(row), result_json, now, now, job_id),
            )
            if cache:
                if row is not None:
                    self._cache_put_locked(str(row[0]), result)

    def mark_failed(self, job_id: str, *, error: str) -> None:
        now = time.time()
        with self._lock:
            row = self._conn.execute(
                "SELECT request_key, request_json FROM jobs WHERE job_id=?",
                (job_id,),
            ).fetchone()
            self._conn.execute(
                "UPDATE jobs SET status='failed', request_json=?, error=?, updated_at=?, "
                "finished_at=? WHERE job_id=?",
                (_terminal_request_json_from_db_row(row), error, now, now, job_id),
            )

    def list_recent_jobs(self, *, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT job_id, request_key, request_json, status, result_json, error, backend_url, "
                "attempts, created_at, updated_at, started_at, finished_at "
                "FROM jobs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [_row_to_job(row) for row in rows]

    def stats(self) -> dict[str, Any]:
        with self._lock:
            job_rows = self._conn.execute(
                "SELECT status, COUNT(*) FROM jobs GROUP BY status"
            ).fetchall()
            cache_row = self._conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(hits), 0) FROM verify_cache"
            ).fetchone()
        return {
            "jobs_by_status": {str(status): int(count) for status, count in job_rows},
            "cache_entries": int(cache_row[0]),
            "cache_total_hits": int(cache_row[1]),
        }

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def _cache_get_locked(self, request_key: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT result_json FROM verify_cache WHERE request_key=?",
            (request_key,),
        ).fetchone()
        if row is None:
            return None
        self._conn.execute(
            "UPDATE verify_cache SET last_hit_at=?, hits=hits+1 WHERE request_key=?",
            (time.time(), request_key),
        )
        result = json.loads(row[0])
        result["control_cached"] = True
        return result

    def _cache_put_locked(self, request_key: str, result: dict[str, Any]) -> None:
        now = time.time()
        self._conn.execute(
            "INSERT OR REPLACE INTO verify_cache "
            "(request_key, result_json, created_at, last_hit_at, hits) "
            "VALUES (?, ?, ?, ?, 0)",
            (request_key, json.dumps(result, ensure_ascii=False), now, now),
        )

    def _redact_terminal_requests(self) -> None:
        rows = self._conn.execute(
            "SELECT job_id, request_json FROM jobs WHERE status IN ('done', 'failed', 'cancelled')"
        ).fetchall()
        for job_id, request_json in rows:
            redacted = _terminal_request_json_from_request_json(str(request_json))
            if redacted != request_json:
                self._conn.execute(
                    "UPDATE jobs SET request_json=? WHERE job_id=?",
                    (redacted, job_id),
                )


def _row_to_job(row: sqlite3.Row | tuple[Any, ...]) -> dict[str, Any]:
    result = json.loads(row[4]) if row[4] else None
    return {
        "job_id": row[0],
        "request_key": row[1],
        "request": json.loads(row[2]),
        "status": row[3],
        "result": result,
        "error": row[5],
        "backend_url": row[6],
        "attempts": row[7],
        "created_at": row[8],
        "updated_at": row[9],
        "started_at": row[10],
        "finished_at": row[11],
    }


def _terminal_request_json(request: dict[str, Any]) -> str:
    return json.dumps(_redact_request_code(request), ensure_ascii=False, sort_keys=True)


def _terminal_request_json_from_db_row(row: sqlite3.Row | tuple[Any, ...] | None) -> str:
    if row is None:
        return _terminal_request_json({})
    return _terminal_request_json_from_request_json(str(row[1]))


def _terminal_request_json_from_request_json(request_json: str) -> str:
    try:
        request = json.loads(request_json)
    except json.JSONDecodeError:
        return request_json
    if not isinstance(request, dict):
        return request_json
    return _terminal_request_json(request)


def _redact_request_code(request: dict[str, Any]) -> dict[str, Any]:
    redacted = dict(request)
    code = redacted.get("code")
    if isinstance(code, str):
        if redacted.get("code_redacted") is True:
            return redacted
        redacted["code_sha256"] = hashlib.sha256(code.encode("utf-8")).hexdigest()
        redacted["code_bytes"] = len(code.encode("utf-8"))
        redacted["code"] = "<redacted after terminal job>"
        redacted["code_redacted"] = True
    return redacted
