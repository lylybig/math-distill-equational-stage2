from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class VerifyReq(BaseModel):
    problem: dict[str, Any]
    verdict: str
    code: str
    timeout_seconds: int | None = None


class WorkerHealth(BaseModel):
    status: str
    service: str
    service_rev: str
    judge_repo: str
    lean_version: str
    mathlib_rev: str
    judge_rev: str
    workers_busy: int
    workers_total: int
    cache_entries: int
    cache_bytes: int

