from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


_WUBING_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_JUDGE_REPO = _WUBING_ROOT / "external" / "equational-theories-lean-stage2"


@dataclass(frozen=True)
class WorkerSettings:
    judge_repo: Path
    workers: int
    default_timeout_seconds: int
    timeout_cap_seconds: int
    timeout_grace_seconds: int
    cache_path: Path
    stdout_cap: int
    stderr_cap: int
    lean_bin: str
    lake_bin: str
    artifact_dir: Path | None
    max_code_length: int | None
    max_false_cert_bytes: int | None


def settings_from_env() -> WorkerSettings:
    judge_repo = Path(
        os.environ.get(
            "JUDGE_REPO",
            os.environ.get(
                "OFFICIAL_STAGE2_JUDGE_REPO",
                os.environ.get("SIMPLE_API_OFFICIAL_REPO", str(_DEFAULT_JUDGE_REPO)),
            ),
        )
    ).expanduser().resolve()
    workers = _positive_int(
        os.environ.get("JUDGE_V2_WORKERS", os.environ.get("JUDGE_WORKERS")),
        default=max(1, (os.cpu_count() or 4) // 2),
        name="JUDGE_V2_WORKERS",
    )
    return WorkerSettings(
        judge_repo=judge_repo,
        workers=workers,
        default_timeout_seconds=_positive_int(
            os.environ.get(
                "JUDGE_V2_DEFAULT_TIMEOUT_SECONDS",
                os.environ.get("JUDGE_DEFAULT_TIMEOUT_SECONDS"),
            ),
            default=120,
            name="JUDGE_V2_DEFAULT_TIMEOUT_SECONDS",
        ),
        timeout_cap_seconds=_positive_int(
            os.environ.get(
                "JUDGE_V2_TIMEOUT_CAP_SECONDS",
                os.environ.get("JUDGE_TIMEOUT_CAP_SECONDS"),
            ),
            default=180,
            name="JUDGE_V2_TIMEOUT_CAP_SECONDS",
        ),
        timeout_grace_seconds=_positive_int(
            os.environ.get("JUDGE_V2_TIMEOUT_GRACE_SECONDS"),
            default=30,
            name="JUDGE_V2_TIMEOUT_GRACE_SECONDS",
        ),
        cache_path=Path(
            os.environ.get(
                "JUDGE_V2_CACHE_PATH",
                os.environ.get("JUDGE_CACHE_PATH", "judge_v2_worker_cache.sqlite"),
            )
        ).expanduser().resolve(),
        stdout_cap=_positive_int(
            os.environ.get("JUDGE_V2_STDOUT_CAP_BYTES"),
            default=16 * 1024,
            name="JUDGE_V2_STDOUT_CAP_BYTES",
        ),
        stderr_cap=_positive_int(
            os.environ.get("JUDGE_V2_STDERR_CAP_BYTES"),
            default=16 * 1024,
            name="JUDGE_V2_STDERR_CAP_BYTES",
        ),
        lean_bin=os.environ.get("LEAN_BIN", "lean"),
        lake_bin=os.environ.get("LAKE_BIN", "lake"),
        artifact_dir=_optional_path(os.environ.get("JUDGE_ARTIFACT_DIR")),
        max_code_length=_optional_int(os.environ.get("MAX_CODE_LENGTH"), "MAX_CODE_LENGTH"),
        max_false_cert_bytes=_optional_int(
            os.environ.get("MAX_FALSE_CERT_BYTES"),
            "MAX_FALSE_CERT_BYTES",
        ),
    )


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


def _optional_int(value: str | None, name: str) -> int | None:
    if value is None or value == "":
        return None
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if parsed <= 0:
        raise ValueError(f"{name} must be positive")
    return parsed


def _optional_path(value: str | None) -> Path | None:
    if not value:
        return None
    return Path(value).expanduser().resolve()

