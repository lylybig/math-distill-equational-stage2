from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from judge_v2.common.models import VerifyReq
from judge_v2.control.config import ControlSettings, settings_from_env
from judge_v2.control.runtime import ControlRuntime


def create_app(settings: ControlSettings | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        runtime = ControlRuntime(settings or settings_from_env())
        app.state.runtime = runtime
        await runtime.start()
        try:
            yield
        finally:
            await runtime.stop()

    app = FastAPI(title="judge-v2-control", lifespan=lifespan)

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return await _runtime(app).health()

    @app.post("/verify")
    async def verify(req: VerifyReq) -> dict[str, Any]:
        return await _runtime(app).verify_sync(req)

    @app.post("/jobs")
    async def submit_job(req: VerifyReq) -> dict[str, Any]:
        return await _runtime(app).submit(req)

    @app.get("/jobs")
    async def list_jobs(limit: int = 50) -> dict[str, Any]:
        return await _runtime(app).list_jobs(limit=limit)

    @app.get("/jobs/{job_id}")
    async def get_job(job_id: str) -> dict[str, Any]:
        return await _runtime(app).get_job(job_id)

    @app.get("/jobs/{job_id}/wait")
    async def wait_job(job_id: str, timeout_seconds: float = 30.0) -> dict[str, Any]:
        job = await _runtime(app).wait_job(job_id, timeout=timeout_seconds)
        if job is None:
            current = await _runtime(app).get_job(job_id)
            current["wait_timeout"] = True
            return current
        return job

    return app


def _runtime(app: FastAPI) -> ControlRuntime:
    runtime = getattr(app.state, "runtime", None)
    if not isinstance(runtime, ControlRuntime):
        raise RuntimeError("judge-v2-control runtime has not started")
    return runtime


app = create_app()
