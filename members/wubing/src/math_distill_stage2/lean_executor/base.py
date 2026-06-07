from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from math_distill_stage2.counterexample.verified_index import file_sha256


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class LeanTask:
    certificate_path: Path
    timeout_seconds: int = 60


@dataclass(frozen=True)
class LeanExecutionResult:
    checked_at_utc: str
    executor_backend: str
    command: list[str]
    result: str
    returncode: int | None
    stdout: str
    stderr: str
    timeout_seconds: int
    elapsed_seconds: float
    certificate_sha256: str
    lean_image: str | None = None
    lean_image_digest: str | None = None
    cpu_limit: str | None = None
    memory_limit: str | None = None

    def to_json(self) -> dict:
        return {
            "checked_at_utc": self.checked_at_utc,
            "executor_backend": self.executor_backend,
            "command": " ".join(self.command),
            "result": self.result,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "timeout_seconds": self.timeout_seconds,
            "elapsed_seconds": self.elapsed_seconds,
            "certificate_sha256": self.certificate_sha256,
            "lean_image": self.lean_image,
            "lean_image_digest": self.lean_image_digest,
            "cpu_limit": self.cpu_limit,
            "memory_limit": self.memory_limit,
        }


class LeanExecutor(Protocol):
    backend: str

    def execute(self, task: LeanTask) -> LeanExecutionResult:
        ...


def run_lean_command(
    command: list[str],
    task: LeanTask,
    backend: str,
    lean_image: str | None = None,
    lean_image_digest: str | None = None,
    cpu_limit: str | None = None,
    memory_limit: str | None = None,
) -> LeanExecutionResult:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
            timeout=task.timeout_seconds,
        )
        result = "passed" if completed.returncode == 0 else "failed"
        returncode = completed.returncode
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
    except subprocess.TimeoutExpired as exc:
        result = "timeout"
        returncode = None
        stdout = output_to_text(exc.stdout or exc.output)
        stderr = output_to_text(exc.stderr)
        timeout_message = f"command timed out after {task.timeout_seconds} seconds"
        stderr = f"{stderr}\n{timeout_message}".strip()
    elapsed = round(time.monotonic() - started, 6)
    return LeanExecutionResult(
        checked_at_utc=utc_timestamp(),
        executor_backend=backend,
        command=command,
        result=result,
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
        timeout_seconds=task.timeout_seconds,
        elapsed_seconds=elapsed,
        certificate_sha256=file_sha256(task.certificate_path),
        lean_image=lean_image,
        lean_image_digest=lean_image_digest,
        cpu_limit=cpu_limit,
        memory_limit=memory_limit,
    )


def output_to_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value
