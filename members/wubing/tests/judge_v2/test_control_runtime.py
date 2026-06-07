from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from judge_v2.common.models import VerifyReq
from judge_v2.control.config import ControlSettings
from judge_v2.control.runtime import ControlRuntime


def test_control_verify_sync_dispatches_to_backend_and_caches(tmp_path):
    client = FakeBackendClient()
    runtime = ControlRuntime(_settings(tmp_path), client=client)

    async def run() -> None:
        await runtime.start()
        try:
            first = await runtime.verify_sync(_req())
            second = await runtime.verify_sync(_req())
        finally:
            await runtime.stop()

        assert first["status"] == "accepted"
        assert first["error_code"] == "ACCEPTED"
        assert first["control_cached"] is False
        assert first["control_backend_url"] == "http://worker-a"
        assert second["status"] == "accepted"
        assert second["control_cached"] is True
        assert client.verify_calls == ["http://worker-a"]

    asyncio.run(run())


def test_control_redacts_code_after_terminal_jobs(tmp_path):
    client = FakeBackendClient()
    runtime = ControlRuntime(_settings(tmp_path), client=client)

    async def run() -> None:
        await runtime.start()
        try:
            job = await runtime.submit(_req(code="exact secret_certificate"))
            done = await runtime.wait_job(job["job_id"], timeout=5)
            stored = runtime.store.get_job(job["job_id"])
        finally:
            await runtime.stop()

        assert done is not None
        assert done["status"] == "done"
        assert stored is not None
        assert stored["request"]["code"] == "<redacted after terminal job>"
        assert stored["request"]["code_redacted"] is True
        assert stored["request"]["code_bytes"] == len("exact secret_certificate")
        assert len(stored["request"]["code_sha256"]) == 64

    asyncio.run(run())


def test_control_jobs_api_returns_existing_inflight_job_for_duplicate(tmp_path):
    client = FakeBackendClient()
    runtime = ControlRuntime(_settings(tmp_path), client=client)

    async def run() -> None:
        await runtime.start()
        try:
            first = await runtime.submit(_req())
            second = await runtime.submit(_req())
            done = await runtime.wait_job(first["job_id"], timeout=5)
        finally:
            await runtime.stop()

        assert first["job_id"] == second["job_id"]
        assert done is not None
        assert done["status"] == "done"
        assert client.verify_calls == ["http://worker-a"]

    asyncio.run(run())


def test_control_chooses_least_busy_healthy_backend(tmp_path):
    client = FakeBackendClient(
        health_by_url={
            "http://worker-a": {"status": "ok", "workers_busy": 7, "workers_total": 8},
            "http://worker-b": {"status": "ok", "workers_busy": 1, "workers_total": 8},
        }
    )
    runtime = ControlRuntime(
        _settings(tmp_path, backends=("http://worker-a", "http://worker-b")),
        client=client,
    )

    async def run() -> None:
        await runtime.start()
        try:
            result = await runtime.verify_sync(_req(code="exact b"))
        finally:
            await runtime.stop()

        assert result["status"] == "accepted"
        assert client.verify_calls == ["http://worker-b"]

    asyncio.run(run())


class FakeBackendClient:
    def __init__(self, health_by_url: dict[str, dict[str, Any]] | None = None) -> None:
        self.health_by_url = health_by_url or {
            "http://worker-a": {"status": "ok", "workers_busy": 0, "workers_total": 8}
        }
        self.verify_calls: list[str] = []

    def health(self, base_url: str, *, timeout: float) -> dict[str, Any]:
        payload = dict(self.health_by_url[base_url])
        payload.setdefault("service", "judge-v2-worker")
        payload.setdefault("service_rev", "fake-rev")
        payload.setdefault("judge_repo", "/fake")
        payload.setdefault("lean_version", "fake")
        payload.setdefault("mathlib_rev", "fake")
        payload.setdefault("judge_rev", "fake")
        payload.setdefault("cache_entries", 0)
        payload.setdefault("cache_bytes", 0)
        return payload

    def verify(self, base_url: str, req: VerifyReq, *, timeout: float) -> dict[str, Any]:
        self.verify_calls.append(base_url)
        return {
            "status": "accepted",
            "error_code": "ACCEPTED",
            "message": "certificate accepted",
            "verdict": req.verdict,
            "artifact_path": None,
            "direct_declarations": [],
            "axioms": [],
            "stdout": "",
            "stderr": "",
            "cached": False,
            "elapsed_ms": 1,
            "service_rev": "fake-rev",
        }


def _req(code: str = "exact a") -> VerifyReq:
    return VerifyReq(
        problem={"id": "p_true_basic"},
        verdict="true",
        code=code,
        timeout_seconds=120,
    )


def _settings(
    tmp_path: Path,
    *,
    backends: tuple[str, ...] = ("http://worker-a",),
) -> ControlSettings:
    return ControlSettings(
        backends=backends,
        db_path=tmp_path / "control.sqlite",
        dispatchers=2,
        max_attempts=2,
        retry_delay_seconds=0.01,
        backend_health_timeout_seconds=0.1,
        default_timeout_seconds=120,
        timeout_grace_seconds=1,
        job_wait_timeout_seconds=5,
    )
