from __future__ import annotations

import argparse
import fcntl
import json
import os
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


DEFAULT_LOCK_DIR = Path("artifacts/locks")
DEFAULT_HEAVY_TASK_LOCK_NAME = "order5_registry_heavy"


class HeavyTaskLockError(RuntimeError):
    pass


def add_heavy_task_lock_args(
    parser: argparse.ArgumentParser,
    *,
    default_name: str = DEFAULT_HEAVY_TASK_LOCK_NAME,
) -> None:
    parser.add_argument(
        "--heavy-task-lock-name",
        default=default_name,
        help="Name for the shared local heavy-task lock.",
    )
    parser.add_argument(
        "--heavy-task-lock-dir",
        type=Path,
        default=DEFAULT_LOCK_DIR,
        help="Directory used for local heavy-task lock files.",
    )
    parser.add_argument(
        "--wait-heavy-task-lock",
        action="store_true",
        help="Wait for the shared heavy-task lock instead of failing fast.",
    )
    parser.add_argument(
        "--no-heavy-task-lock",
        action="store_true",
        help="Disable the shared local heavy-task lock.",
    )


@contextmanager
def heavy_task_lock_from_args(args: argparse.Namespace) -> Iterator[Path | None]:
    if getattr(args, "no_heavy_task_lock", False):
        yield None
        return
    with acquire_heavy_task_lock(
        str(getattr(args, "heavy_task_lock_name", DEFAULT_HEAVY_TASK_LOCK_NAME)),
        lock_dir=Path(getattr(args, "heavy_task_lock_dir", DEFAULT_LOCK_DIR)),
        wait=bool(getattr(args, "wait_heavy_task_lock", False)),
    ) as lock_path:
        yield lock_path


@contextmanager
def acquire_heavy_task_lock(
    name: str = DEFAULT_HEAVY_TASK_LOCK_NAME,
    *,
    lock_dir: Path = DEFAULT_LOCK_DIR,
    wait: bool = False,
) -> Iterator[Path]:
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / f"{_safe_lock_name(name)}.lock"
    handle = lock_path.open("a+", encoding="utf-8")
    try:
        flags = fcntl.LOCK_EX
        if not wait:
            flags |= fcntl.LOCK_NB
        try:
            fcntl.flock(handle.fileno(), flags)
        except BlockingIOError as exc:
            holder = _read_lock_holder(handle)
            raise HeavyTaskLockError(
                f"heavy task lock is already held: {lock_path}; holder={holder}"
            ) from exc
        _write_lock_holder(handle)
        yield lock_path
    finally:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


def _safe_lock_name(name: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_", ".") else "_" for ch in name)
    return safe or DEFAULT_HEAVY_TASK_LOCK_NAME


def _read_lock_holder(handle) -> dict:
    handle.seek(0)
    text = handle.read().strip()
    if not text:
        return {}
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text[:200]}
    return payload if isinstance(payload, dict) else {"raw": text[:200]}


def _write_lock_holder(handle) -> None:
    payload = {
        "pid": os.getpid(),
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "cwd": os.getcwd(),
        "argv": sys.argv,
    }
    handle.seek(0)
    handle.truncate()
    handle.write(json.dumps(payload, sort_keys=True) + "\n")
    handle.flush()
