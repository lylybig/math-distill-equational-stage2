from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
import uuid
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException

from judge_v2.common.cache_key import verify_cache_key
from judge_v2.common.models import VerifyReq
from judge_v2.worker.cache import VerifyCache
from judge_v2.worker.config import WorkerSettings, settings_from_env
from judge_v2.worker.verifier import (
    judge_code_rev,
    lean_version,
    mathlib_rev,
    service_rev,
    verify_answer_blocking,
)


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

VerifyCallable = Callable[..., dict[str, Any]]

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("judge_v2.worker")


class WorkerRuntime:
    def __init__(
        self,
        settings: WorkerSettings,
        *,
        verify_func: VerifyCallable = verify_answer_blocking,
        inline_verify: bool = False,
    ) -> None:
        self.settings = settings
        self.verify_func = verify_func
        self.inline_verify = inline_verify
        self.cache = VerifyCache(settings.cache_path)
        self.pool = None if inline_verify else ProcessPoolExecutor(max_workers=settings.workers)
        self.busy = 0
        self.busy_lock = threading.Lock()
        self.service_rev = service_rev(
            judge_repo=settings.judge_repo,
            lean_bin=settings.lean_bin,
        )

    async def verify(self, req: VerifyReq) -> dict[str, Any]:
        problem_id = _validate_verify_req(req)
        timeout = max(
            1,
            min(
                req.timeout_seconds or self.settings.default_timeout_seconds,
                self.settings.timeout_cap_seconds,
            ),
        )
        req_id = uuid.uuid4().hex[:8]
        key = verify_cache_key(
            problem_id=problem_id,
            verdict=req.verdict,
            code=req.code,
            service_rev=self.service_rev,
        )
        started = time.time()

        cached = self.cache.get(key)
        if cached is not None:
            elapsed_ms = int((time.time() - started) * 1000)
            _log_line(
                req_id=req_id,
                problem_id=problem_id,
                sha=key[:12],
                status=cached.get("status"),
                error_code=cached.get("error_code"),
                elapsed_ms=elapsed_ms,
                cached=True,
            )
            return {
                **cached,
                "cached": True,
                "elapsed_ms": elapsed_ms,
                "service_rev": self.service_rev,
            }

        with self.busy_lock:
            if self.busy >= self.settings.workers:
                raise HTTPException(
                    503,
                    detail={"error": "pool saturated", "retry_after_ms": 2000},
                )
            self.busy += 1

        try:
            result = await self._run_verify(req, timeout)
        finally:
            with self.busy_lock:
                self.busy -= 1

        envelope = result.get("_judge_v2_exception")
        if isinstance(envelope, dict):
            self._raise_verify_exception(envelope, problem_id=problem_id, key=key, started=started)

        result["artifact_path"] = None
        result["stdout"] = _cap(str(result.get("stdout") or ""), self.settings.stdout_cap)
        result["stderr"] = _cap(str(result.get("stderr") or ""), self.settings.stderr_cap)
        elapsed_ms = int((time.time() - started) * 1000)

        if result.get("error_code") in CACHEABLE_ERROR_CODES:
            self.cache.put(key, result)

        _log_line(
            req_id=req_id,
            problem_id=problem_id,
            sha=key[:12],
            status=result.get("status"),
            error_code=result.get("error_code"),
            elapsed_ms=elapsed_ms,
            cached=False,
        )
        return {
            **result,
            "cached": False,
            "elapsed_ms": elapsed_ms,
            "service_rev": self.service_rev,
        }

    async def verify_request_dict(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.verify(VerifyReq.model_validate(payload))

    async def _run_verify(self, req: VerifyReq, timeout: int) -> dict[str, Any]:
        kwargs = {
            "judge_repo": str(self.settings.judge_repo),
            "problem": req.problem,
            "verdict": req.verdict,
            "code": req.code,
            "timeout_seconds": timeout,
            "lean_bin": self.settings.lean_bin,
            "lake_bin": self.settings.lake_bin,
            "artifact_dir": str(self.settings.artifact_dir) if self.settings.artifact_dir else None,
            "max_code_length": self.settings.max_code_length,
            "max_false_cert_bytes": self.settings.max_false_cert_bytes,
        }
        hard_timeout = timeout + self.settings.timeout_grace_seconds
        try:
            if self.inline_verify:
                return await asyncio.wait_for(asyncio.to_thread(self.verify_func, **kwargs), hard_timeout)
            if self.pool is None:
                raise RuntimeError("process pool is not initialized")
            loop = asyncio.get_running_loop()
            return await asyncio.wait_for(
                loop.run_in_executor(self.pool, _call_verify_func, self.verify_func, kwargs),
                hard_timeout,
            )
        except asyncio.TimeoutError:
            return {
                "status": "incorrect",
                "error_code": "LEAN_TIMEOUT_HARD",
                "message": f"verification exceeded hard cap {hard_timeout}s",
                "verdict": req.verdict,
                "direct_declarations": [],
                "axioms": [],
                "stdout": "",
                "stderr": "",
            }

    def health(self) -> dict[str, Any]:
        summary = self.cache.summary()
        return {
            "status": "ok",
            "service": "judge-v2-worker",
            "service_rev": self.service_rev,
            "judge_repo": str(self.settings.judge_repo),
            "lean_version": lean_version(self.settings.lean_bin, self.settings.judge_repo),
            "mathlib_rev": mathlib_rev(self.settings.judge_repo),
            "judge_rev": judge_code_rev(self.settings.judge_repo),
            "workers_busy": self.busy,
            "workers_total": self.settings.workers,
            "cache_entries": summary["cache_entries"],
            "cache_bytes": summary["cache_bytes"],
        }

    def stats(self) -> dict[str, Any]:
        summary = self.cache.summary()
        return {
            **summary,
            "workers_busy": self.busy,
            "workers_total": self.settings.workers,
        }

    def shutdown(self) -> None:
        if self.pool is not None:
            self.pool.shutdown(wait=True)
        self.cache.close()

    def _raise_verify_exception(
        self,
        envelope: dict[str, Any],
        *,
        problem_id: str,
        key: str,
        started: float,
    ) -> None:
        exc_type = str(envelope.get("type") or "Exception")
        message = str(envelope.get("message") or "")
        elapsed_ms = int((time.time() - started) * 1000)
        _log_line(
            problem_id=problem_id,
            sha=key[:12],
            status="infra_error",
            error_code=exc_type,
            elapsed_ms=elapsed_ms,
            cached=False,
            message=message,
        )
        if exc_type == "JudgeConfigurationError":
            raise HTTPException(400, f"problem config error: {message}")
        raise HTTPException(500, f"infrastructure error ({exc_type}): {message}")


def create_app(
    settings: WorkerSettings | None = None,
    *,
    verify_func: VerifyCallable = verify_answer_blocking,
    inline_verify: bool = False,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        runtime = WorkerRuntime(
            settings or settings_from_env(),
            verify_func=verify_func,
            inline_verify=inline_verify,
        )
        app.state.runtime = runtime
        try:
            yield
        finally:
            runtime.shutdown()

    app = FastAPI(title="judge-v2-worker", lifespan=lifespan)

    @app.post("/verify")
    async def verify(req: VerifyReq) -> dict[str, Any]:
        return await _runtime(app).verify(req)

    @app.get("/health")
    def health() -> dict[str, Any]:
        return _runtime(app).health()

    @app.get("/stats")
    def stats() -> dict[str, Any]:
        return _runtime(app).stats()

    return app


def _runtime(app: FastAPI) -> WorkerRuntime:
    runtime = getattr(app.state, "runtime", None)
    if not isinstance(runtime, WorkerRuntime):
        raise RuntimeError("judge-v2-worker runtime has not started")
    return runtime


def _call_verify_func(func: VerifyCallable, kwargs: dict[str, Any]) -> dict[str, Any]:
    return func(**kwargs)


def _validate_verify_req(req: VerifyReq) -> str:
    problem_id = req.problem.get("id")
    if not isinstance(problem_id, str) or not problem_id.strip():
        raise HTTPException(400, "problem.id required (non-empty string)")
    if req.verdict not in {"true", "false"}:
        raise HTTPException(400, "verdict must be 'true' or 'false'")
    if not isinstance(req.code, str) or not req.code:
        raise HTTPException(400, "code must be a non-empty string")
    return problem_id


def _cap(s: str, n: int) -> str:
    if len(s) <= n:
        return s
    return s[: n - 32] + f"\n... (truncated, {len(s) - n + 32} more chars)"


def _log_line(**kw: Any) -> None:
    log.info(json.dumps({"ts": time.time(), **kw}, ensure_ascii=False))


app = create_app()
