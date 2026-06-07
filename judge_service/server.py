"""Judge service: stateless HTTP wrapper around judge.verify.verify_answer.

Run:
  JUDGE_REPO=/abs/path/to/third_party/equational-theories-lean-stage2 \
  LEAN_BIN=lean LAKE_BIN=lake \
  JUDGE_WORKERS=4 \
  JUDGE_CACHE_PATH=/var/lib/judge/cache.sqlite \
  uvicorn judge_service.server:app --host 0.0.0.0 --port 9000

Endpoints:
  POST /verify   verify a candidate proof, with sqlite cache by problem.id
  GET  /health   service revs + worker / cache stats
  GET  /stats    cache hit aggregates

Per the agreed scope:
  - internal-only, no auth
  - ProcessPool sandbox (no docker)
  - cache key keyed on problem.id (problems are immutable fixtures)
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import sqlite3
import subprocess
import sys
import threading
import time
import uuid
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

JUDGE_REPO = Path(os.environ["JUDGE_REPO"]).expanduser().resolve()
sys.path.insert(0, str(JUDGE_REPO))
from judge.verify import (  # noqa: E402
    JudgeConfig,
    JudgeConfigurationError,
    JudgeInfrastructureError,
    verify_answer,
)

WORKERS = int(os.environ.get("JUDGE_WORKERS", str(max(1, (os.cpu_count() or 4) // 2))))
DEFAULT_TIMEOUT = int(os.environ.get("JUDGE_DEFAULT_TIMEOUT_SECONDS", "120"))
TIMEOUT_HARD_CAP = int(os.environ.get("JUDGE_TIMEOUT_CAP_SECONDS", "180"))
CACHE_PATH = Path(os.environ.get("JUDGE_CACHE_PATH", "judge_cache.sqlite")).resolve()
STDOUT_CAP = 16 * 1024
STDERR_CAP = 16 * 1024
CACHEABLE_ERROR_CODES = {
    "ACCEPTED",
    "LEAN_REJECTED",
    "BANNED_PLACEHOLDER",
    "DISALLOWED_AXIOMS",
    "DISALLOWED_DECLARATIONS",
    "FALSE_CERT_TOO_LARGE",
    "CODE_TOO_LONG",
    "DUPLICATE_JSON_KEYS",
    "ANSWER_NOT_OBJECT",
    "ANSWER_SCHEMA_ERROR",
    "INVALID_VERDICT",
    "INVALID_CODE_FIELD",
    "UNPARSED_JSON",
}

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("judge_service")


def _judge_code_rev() -> str:
    return hashlib.sha256(
        (JUDGE_REPO / "judge" / "verify.py").read_bytes()
    ).hexdigest()[:12]


def _lean_version() -> str:
    try:
        r = subprocess.run(
            [os.environ.get("LEAN_BIN", "lean"), "--version"],
            capture_output=True, text=True, timeout=10,
        )
        return r.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _mathlib_rev() -> str:
    manifest = JUDGE_REPO / ".lake" / "manifest.json"
    if not manifest.exists():
        return "unknown"
    try:
        data = json.loads(manifest.read_text())
        for p in data.get("packages", []):
            if p.get("name") == "mathlib":
                return str(p.get("rev", "unknown"))[:12]
    except Exception:
        pass
    return "unknown"


SERVICE_REV = (
    f"judge-{_judge_code_rev()}"
    f"-lean-{hashlib.sha256(_lean_version().encode()).hexdigest()[:8]}"
    f"-mathlib-{_mathlib_rev()}"
)


def _open_cache() -> sqlite3.Connection:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(CACHE_PATH, isolation_level=None, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute(
        """CREATE TABLE IF NOT EXISTS verify_cache (
            key TEXT PRIMARY KEY,
            response_json TEXT NOT NULL,
            created_at REAL NOT NULL,
            last_hit_at REAL NOT NULL,
            hits INTEGER NOT NULL DEFAULT 0
        )"""
    )
    return conn


_cache_conn = _open_cache()
_cache_lock = threading.Lock()
_pool = ProcessPoolExecutor(max_workers=WORKERS)
_busy = 0
_busy_lock = threading.Lock()

app = FastAPI(title="judge-service")


class VerifyReq(BaseModel):
    problem: dict
    verdict: str
    code: str
    timeout_seconds: int | None = None


def _cache_key(problem_id: str, verdict: str, code: str) -> str:
    h = hashlib.sha256()
    for part in (problem_id, verdict, code, SERVICE_REV):
        h.update(part.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()


def _cache_get(key: str) -> dict | None:
    with _cache_lock:
        row = _cache_conn.execute(
            "SELECT response_json FROM verify_cache WHERE key=?", (key,)
        ).fetchone()
        if row is None:
            return None
        _cache_conn.execute(
            "UPDATE verify_cache SET last_hit_at=?, hits=hits+1 WHERE key=?",
            (time.time(), key),
        )
    return json.loads(row[0])


def _cache_put(key: str, response: dict) -> None:
    payload = json.dumps(response, ensure_ascii=False)
    now = time.time()
    with _cache_lock:
        _cache_conn.execute(
            "INSERT OR REPLACE INTO verify_cache "
            "(key, response_json, created_at, last_hit_at, hits) "
            "VALUES (?, ?, ?, ?, 0)",
            (key, payload, now, now),
        )


def _cap(s: str | None, n: int) -> str:
    if not s:
        return ""
    if len(s) <= n:
        return s
    return s[: n - 32] + f"\n... (truncated, {len(s) - n + 32} more chars)"


def _verify_blocking(problem: dict, verdict: str, code: str, timeout: int) -> dict:
    raw = json.dumps({"verdict": verdict, "code": code}, ensure_ascii=False)
    return verify_answer(problem, raw, JudgeConfig(lean_timeout_seconds=timeout))


def _log_line(**kw) -> None:
    log.info(json.dumps({"ts": time.time(), **kw}, ensure_ascii=False))


@app.post("/verify")
async def verify(req: VerifyReq) -> dict:
    global _busy

    if "id" not in req.problem or not isinstance(req.problem["id"], str) or not req.problem["id"].strip():
        raise HTTPException(400, "problem.id required (non-empty string)")
    problem_id = req.problem["id"]
    if req.verdict not in {"true", "false"}:
        raise HTTPException(400, "verdict must be 'true' or 'false'")
    if not isinstance(req.code, str) or not req.code:
        raise HTTPException(400, "code must be a non-empty string")

    timeout = max(1, min(req.timeout_seconds or DEFAULT_TIMEOUT, TIMEOUT_HARD_CAP))
    req_id = uuid.uuid4().hex[:8]
    key = _cache_key(problem_id, req.verdict, req.code)
    started = time.time()

    cached = _cache_get(key)
    if cached is not None:
        elapsed_ms = int((time.time() - started) * 1000)
        _log_line(req_id=req_id, problem_id=problem_id, sha=key[:12],
                  status=cached.get("status"), error_code=cached.get("error_code"),
                  elapsed_ms=elapsed_ms, cached=True)
        return {**cached, "cached": True, "elapsed_ms": elapsed_ms, "service_rev": SERVICE_REV}

    with _busy_lock:
        if _busy >= WORKERS:
            raise HTTPException(
                503, detail={"error": "pool saturated", "retry_after_ms": 2000}
            )
        _busy += 1

    try:
        loop = asyncio.get_running_loop()
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    _pool, _verify_blocking, req.problem, req.verdict, req.code, timeout
                ),
                timeout=timeout + 30,
            )
        except asyncio.TimeoutError:
            elapsed_ms = int((time.time() - started) * 1000)
            _log_line(req_id=req_id, problem_id=problem_id, sha=key[:12],
                      status="incorrect", error_code="LEAN_TIMEOUT_HARD",
                      elapsed_ms=elapsed_ms, cached=False)
            return {
                "status": "incorrect", "error_code": "LEAN_TIMEOUT_HARD",
                "message": f"verification exceeded hard cap {timeout + 30}s",
                "verdict": req.verdict, "direct_declarations": [], "axioms": [],
                "stdout": "", "stderr": "",
                "cached": False, "elapsed_ms": elapsed_ms, "service_rev": SERVICE_REV,
            }
        except JudgeConfigurationError as exc:
            raise HTTPException(400, f"problem config error: {exc}")
        except JudgeInfrastructureError as exc:
            _log_line(req_id=req_id, problem_id=problem_id, sha=key[:12],
                      status="infra_error", error_code="INFRA",
                      elapsed_ms=int((time.time() - started) * 1000), cached=False,
                      message=str(exc))
            raise HTTPException(500, f"infrastructure error: {exc}")
    finally:
        with _busy_lock:
            _busy -= 1

    # artifact_path leaks server fs paths; drop before returning
    result["artifact_path"] = None
    result["stdout"] = _cap(result.get("stdout"), STDOUT_CAP)
    result["stderr"] = _cap(result.get("stderr"), STDERR_CAP)
    elapsed_ms = int((time.time() - started) * 1000)

    if result.get("error_code") in CACHEABLE_ERROR_CODES:
        _cache_put(key, result)

    _log_line(req_id=req_id, problem_id=problem_id, sha=key[:12],
              status=result.get("status"), error_code=result.get("error_code"),
              elapsed_ms=elapsed_ms, cached=False)

    return {**result, "cached": False, "elapsed_ms": elapsed_ms, "service_rev": SERVICE_REV}


@app.get("/health")
def health() -> dict:
    with _cache_lock:
        row = _cache_conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(LENGTH(response_json)), 0) FROM verify_cache"
        ).fetchone()
    return {
        "status": "ok",
        "lean_version": _lean_version(),
        "mathlib_rev": _mathlib_rev(),
        "judge_rev": _judge_code_rev(),
        "service_rev": SERVICE_REV,
        "workers_busy": _busy,
        "workers_total": WORKERS,
        "cache_entries": row[0],
        "cache_bytes": row[1],
    }


@app.get("/stats")
def stats() -> dict:
    with _cache_lock:
        row = _cache_conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(hits), 0), COALESCE(AVG(hits), 0) "
            "FROM verify_cache"
        ).fetchone()
    return {
        "cache_entries": row[0],
        "cache_total_hits": row[1],
        "cache_avg_hits_per_entry": float(row[2]),
        "workers_busy": _busy,
        "workers_total": WORKERS,
    }


@app.on_event("shutdown")
def _shutdown() -> None:
    _pool.shutdown(wait=True)
    with _cache_lock:
        _cache_conn.close()
