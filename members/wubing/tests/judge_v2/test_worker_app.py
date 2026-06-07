from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from judge_v2.worker.app import WorkerRuntime
from judge_v2.worker.config import WorkerSettings


def test_worker_health_reports_capacity_and_cache(tmp_path):
    runtime = WorkerRuntime(_settings(tmp_path), verify_func=_accepted_verify, inline_verify=True)
    try:
        payload = runtime.health()
    finally:
        runtime.shutdown()

    assert payload["service"] == "judge-v2-worker"
    assert payload["status"] == "ok"
    assert payload["workers_busy"] == 0
    assert payload["workers_total"] == 2
    assert payload["cache_entries"] == 0


def test_worker_verify_caches_cacheable_results(tmp_path):
    calls: list[str] = []

    def fake_verify(**_: Any) -> dict[str, Any]:
        calls.append("called")
        return _accepted_verify(**_)

    runtime = WorkerRuntime(_settings(tmp_path), verify_func=fake_verify, inline_verify=True)
    request = {
        "problem": {"id": "true_5_2638"},
        "verdict": "true",
        "code": "exact fun G _ h => h",
    }

    try:
        first = asyncio.run(runtime.verify_request_dict(request))
        second = asyncio.run(runtime.verify_request_dict(request))
        stats = runtime.stats()
    finally:
        runtime.shutdown()

    assert first["cached"] is False
    assert second["cached"] is True
    assert calls == ["called"]
    assert stats["cache_entries"] == 1
    assert stats["cache_total_hits"] == 1


def test_worker_verify_rejects_bad_request(tmp_path):
    runtime = WorkerRuntime(_settings(tmp_path), verify_func=_accepted_verify, inline_verify=True)
    try:
        try:
            asyncio.run(
                runtime.verify_request_dict(
                    {"problem": {"id": "p1"}, "verdict": "maybe", "code": "x"}
                )
            )
        except HTTPException as exc:
            assert exc.status_code == 400
            assert exc.detail == "verdict must be 'true' or 'false'"
        else:
            raise AssertionError("expected HTTPException")
    finally:
        runtime.shutdown()


def _accepted_verify(**_: Any) -> dict[str, Any]:
    return {
        "status": "accepted",
        "error_code": "ACCEPTED",
        "message": "ok",
        "verdict": "true",
        "artifact_path": "/tmp/private/path",
        "direct_declarations": [],
        "axioms": [],
        "stdout": "",
        "stderr": "",
    }


def _settings(tmp_path: Path) -> WorkerSettings:
    return WorkerSettings(
        judge_repo=tmp_path / "official",
        workers=2,
        default_timeout_seconds=120,
        timeout_cap_seconds=180,
        timeout_grace_seconds=1,
        cache_path=tmp_path / "cache.sqlite",
        stdout_cap=16 * 1024,
        stderr_cap=16 * 1024,
        lean_bin="__missing_lean_for_test__",
        lake_bin="__missing_lake_for_test__",
        artifact_dir=None,
        max_code_length=None,
        max_false_cert_bytes=None,
    )
