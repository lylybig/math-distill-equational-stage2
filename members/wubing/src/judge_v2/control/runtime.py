from __future__ import annotations

import asyncio
import hashlib
import time
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException

from judge_v2.common.models import VerifyReq
from judge_v2.control.client import BackendClient, BackendError
from judge_v2.control.config import ControlSettings
from judge_v2.control.store import ControlStore


@dataclass
class BackendState:
    url: str
    healthy: bool = False
    workers_busy: int = 0
    workers_total: int = 1
    in_flight: int = 0
    service_rev: str = "unknown"
    last_error: str | None = None
    last_checked_at: float | None = None

    @property
    def score(self) -> float:
        total = max(1, self.workers_total)
        return (self.workers_busy + self.in_flight) / total


class ControlRuntime:
    def __init__(
        self,
        settings: ControlSettings,
        *,
        store: ControlStore | None = None,
        client: BackendClient | None = None,
    ) -> None:
        self.settings = settings
        self.store = store or ControlStore(settings.db_path)
        self.client = client or BackendClient()
        self.queue: asyncio.Queue[str] = asyncio.Queue()
        self.backends = {url: BackendState(url=url) for url in settings.backends}
        self._backend_lock = asyncio.Lock()
        self._tasks: list[asyncio.Task[None]] = []
        self._job_events: dict[str, asyncio.Event] = {}
        self._stopped = False

    async def start(self) -> None:
        await self.refresh_health()
        self._stopped = False
        self._tasks = [
            asyncio.create_task(self._dispatcher_loop(i), name=f"judge-v2-dispatcher-{i}")
            for i in range(self.settings.dispatchers)
        ]

    async def stop(self) -> None:
        self._stopped = True
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self.store.close()

    async def submit(self, req: VerifyReq) -> dict[str, Any]:
        _validate_verify_req(req)
        request = req.model_dump()
        request_key = _request_key(req)
        job_id, should_enqueue = self.store.create_or_get_job(request_key=request_key, request=request)
        job = self.store.get_job(job_id)
        if job is None:
            raise RuntimeError(f"job disappeared after create: {job_id}")
        if should_enqueue:
            await self.queue.put(job_id)
        return _job_public(job)

    async def verify_sync(self, req: VerifyReq, *, wait_timeout: float | None = None) -> dict[str, Any]:
        job = await self.submit(req)
        done = await self.wait_job(
            job["job_id"],
            timeout=wait_timeout or self.settings.job_wait_timeout_seconds,
        )
        if done is None:
            raise HTTPException(504, f"verification did not finish within {wait_timeout}s")
        if done["status"] == "done" and isinstance(done.get("result"), dict):
            result = dict(done["result"])
            result["control_job_id"] = done["job_id"]
            result["control_backend_url"] = done.get("backend_url")
            return result
        raise HTTPException(502, done.get("error") or "verification failed")

    async def wait_job(self, job_id: str, *, timeout: float) -> dict[str, Any] | None:
        job = self.store.get_job(job_id)
        if job is None:
            raise HTTPException(404, f"unknown job: {job_id}")
        if job["status"] in {"done", "failed", "cancelled"}:
            return _job_public(job)

        event = self._job_events.setdefault(job_id, asyncio.Event())
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            return None
        return _job_public(self.store.get_job(job_id) or job)

    async def get_job(self, job_id: str) -> dict[str, Any]:
        job = self.store.get_job(job_id)
        if job is None:
            raise HTTPException(404, f"unknown job: {job_id}")
        return _job_public(job)

    async def list_jobs(self, *, limit: int = 50) -> dict[str, Any]:
        return {"jobs": [_job_public(job) for job in self.store.list_recent_jobs(limit=limit)]}

    async def health(self) -> dict[str, Any]:
        await self.refresh_health()
        return {
            "status": "ok",
            "service": "judge-v2-control",
            "backends": [state.__dict__ | {"score": state.score} for state in self.backends.values()],
            "queue_size": self.queue.qsize(),
            **self.store.stats(),
        }

    async def refresh_health(self) -> None:
        results = await asyncio.gather(
            *(self._refresh_one(url) for url in self.backends),
            return_exceptions=True,
        )
        async with self._backend_lock:
            for url, result in zip(self.backends, results, strict=False):
                state = self.backends[url]
                state.last_checked_at = time.time()
                if isinstance(result, Exception):
                    state.healthy = False
                    state.last_error = str(result)
                    continue
                state.healthy = result.get("status") == "ok"
                state.workers_busy = int(result.get("workers_busy") or 0)
                state.workers_total = max(1, int(result.get("workers_total") or 1))
                state.service_rev = str(result.get("service_rev") or "unknown")
                state.last_error = None

    async def choose_backend(self) -> BackendState:
        await self.refresh_health()
        async with self._backend_lock:
            candidates = [state for state in self.backends.values() if state.healthy]
            if not candidates:
                raise BackendError("no healthy judge_v2 worker backends", retryable=True)
            chosen = min(candidates, key=lambda state: (state.score, state.url))
            chosen.in_flight += 1
            return chosen

    async def release_backend(self, state: BackendState) -> None:
        async with self._backend_lock:
            state.in_flight = max(0, state.in_flight - 1)

    async def _refresh_one(self, url: str) -> dict[str, Any]:
        return await asyncio.to_thread(
            self.client.health,
            url,
            timeout=self.settings.backend_health_timeout_seconds,
        )

    async def _dispatcher_loop(self, _: int) -> None:
        while not self._stopped:
            job_id = await self.queue.get()
            try:
                await self._run_job(job_id)
            finally:
                self.queue.task_done()

    async def _run_job(self, job_id: str) -> None:
        job = self.store.get_job(job_id)
        if job is None or job["status"] in {"done", "failed", "cancelled"}:
            self._notify_job(job_id)
            return

        req = VerifyReq.model_validate(job["request"])
        state: BackendState | None = None
        try:
            state = await self.choose_backend()
            self.store.mark_running(job_id, backend_url=state.url)
            timeout = req.timeout_seconds or self.settings.default_timeout_seconds
            result = await asyncio.to_thread(
                self.client.verify,
                state.url,
                req,
                timeout=timeout + self.settings.timeout_grace_seconds,
            )
            result["control_cached"] = False
            self.store.mark_done(job_id, result=result, cache=_is_cacheable(result))
            self._notify_job(job_id)
        except BackendError as exc:
            latest = self.store.get_job(job_id) or job
            if exc.retryable and int(latest.get("attempts") or 0) < self.settings.max_attempts:
                self.store.mark_queued(job_id, error=str(exc))
                await asyncio.sleep(self.settings.retry_delay_seconds)
                await self.queue.put(job_id)
            else:
                self.store.mark_failed(job_id, error=str(exc))
                self._notify_job(job_id)
        except Exception as exc:  # noqa: BLE001
            self.store.mark_failed(job_id, error=f"{type(exc).__name__}: {exc}")
            self._notify_job(job_id)
        finally:
            if state is not None:
                await self.release_backend(state)

    def _notify_job(self, job_id: str) -> None:
        event = self._job_events.get(job_id)
        if event is not None:
            event.set()


def _validate_verify_req(req: VerifyReq) -> None:
    problem_id = req.problem.get("id")
    if not isinstance(problem_id, str) or not problem_id.strip():
        raise HTTPException(400, "problem.id required (non-empty string)")
    if req.verdict not in {"true", "false"}:
        raise HTTPException(400, "verdict must be 'true' or 'false'")
    if not isinstance(req.code, str) or not req.code:
        raise HTTPException(400, "code must be a non-empty string")


def _request_key(req: VerifyReq) -> str:
    h = hashlib.sha256()
    for part in (str(req.problem.get("id")), req.verdict, req.code, "judge-v2-control-v1"):
        h.update(part.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()


def _is_cacheable(result: dict[str, Any]) -> bool:
    return result.get("error_code") in {
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


def _job_public(job: dict[str, Any]) -> dict[str, Any]:
    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "result": job.get("result"),
        "error": job.get("error"),
        "backend_url": job.get("backend_url"),
        "attempts": job.get("attempts"),
        "created_at": job.get("created_at"),
        "updated_at": job.get("updated_at"),
        "started_at": job.get("started_at"),
        "finished_at": job.get("finished_at"),
    }
