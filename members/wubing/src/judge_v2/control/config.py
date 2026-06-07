from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ControlSettings:
    backends: tuple[str, ...]
    db_path: Path
    dispatchers: int
    max_attempts: int
    retry_delay_seconds: float
    backend_health_timeout_seconds: float
    default_timeout_seconds: int
    timeout_grace_seconds: int
    job_wait_timeout_seconds: float


def settings_from_env() -> ControlSettings:
    return ControlSettings(
        backends=_parse_backends(
            os.environ.get(
                "JUDGE_V2_CONTROL_BACKENDS",
                os.environ.get("JUDGE_V2_BACKENDS", "http://127.0.0.1:8889"),
            )
        ),
        db_path=Path(
            os.environ.get("JUDGE_V2_CONTROL_DB", "judge_v2_control.sqlite")
        ).expanduser().resolve(),
        dispatchers=_positive_int(
            os.environ.get("JUDGE_V2_CONTROL_DISPATCHERS"),
            default=32,
            name="JUDGE_V2_CONTROL_DISPATCHERS",
        ),
        max_attempts=_positive_int(
            os.environ.get("JUDGE_V2_CONTROL_MAX_ATTEMPTS"),
            default=3,
            name="JUDGE_V2_CONTROL_MAX_ATTEMPTS",
        ),
        retry_delay_seconds=_positive_float(
            os.environ.get("JUDGE_V2_CONTROL_RETRY_DELAY_SECONDS"),
            default=1.0,
            name="JUDGE_V2_CONTROL_RETRY_DELAY_SECONDS",
        ),
        backend_health_timeout_seconds=_positive_float(
            os.environ.get("JUDGE_V2_CONTROL_HEALTH_TIMEOUT_SECONDS"),
            default=3.0,
            name="JUDGE_V2_CONTROL_HEALTH_TIMEOUT_SECONDS",
        ),
        default_timeout_seconds=_positive_int(
            os.environ.get("JUDGE_V2_CONTROL_DEFAULT_TIMEOUT_SECONDS"),
            default=120,
            name="JUDGE_V2_CONTROL_DEFAULT_TIMEOUT_SECONDS",
        ),
        timeout_grace_seconds=_positive_int(
            os.environ.get("JUDGE_V2_CONTROL_TIMEOUT_GRACE_SECONDS"),
            default=60,
            name="JUDGE_V2_CONTROL_TIMEOUT_GRACE_SECONDS",
        ),
        job_wait_timeout_seconds=_positive_float(
            os.environ.get("JUDGE_V2_CONTROL_JOB_WAIT_TIMEOUT_SECONDS"),
            default=300.0,
            name="JUDGE_V2_CONTROL_JOB_WAIT_TIMEOUT_SECONDS",
        ),
    )


def _parse_backends(raw: str | None) -> tuple[str, ...]:
    values = tuple(part.strip().rstrip("/") for part in (raw or "").split(",") if part.strip())
    if not values:
        raise ValueError("at least one judge_v2 backend URL is required")
    return values


def _positive_int(value: str | None, *, default: int, name: str) -> int:
    if value is None or value == "":
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if parsed <= 0:
        raise ValueError(f"{name} must be positive")
    return parsed


def _positive_float(value: str | None, *, default: float, name: str) -> float:
    if value is None or value == "":
        return default
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc
    if parsed <= 0:
        raise ValueError(f"{name} must be positive")
    return parsed

