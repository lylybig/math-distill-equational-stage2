from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any


EXACT_RESULT_CACHE_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ExactResultCacheContext:
    solver_sha256: str
    config_sha256: str
    official_fingerprint_sha256: str


class ExactResultCache:
    """Persistent cache for complete official Solo per-problem results."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def get(self, context: ExactResultCacheContext, problem: dict[str, Any]) -> dict[str, Any] | None:
        key = self.key_for(context, problem)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT result_json FROM exact_results WHERE cache_key = ?",
                (key,),
            ).fetchone()
        if row is None:
            return None
        result = json.loads(row[0])
        if not isinstance(result, dict):
            return None
        result["cache_hit"] = True
        result["cache_kind"] = "exact_result"
        return result

    def put(
        self,
        context: ExactResultCacheContext,
        problem: dict[str, Any],
        result: dict[str, Any],
    ) -> None:
        key = self.key_for(context, problem)
        problem_sha = _canonical_json_sha256(problem)
        stored_result = {
            key: value
            for key, value in result.items()
            if key not in {"cache_hit", "cache_kind"}
        }
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO exact_results (
                    cache_key,
                    schema_version,
                    solver_sha256,
                    problem_sha256,
                    config_sha256,
                    official_fingerprint_sha256,
                    result_json,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    key,
                    EXACT_RESULT_CACHE_SCHEMA_VERSION,
                    context.solver_sha256,
                    problem_sha,
                    context.config_sha256,
                    context.official_fingerprint_sha256,
                    json.dumps(stored_result, ensure_ascii=False, sort_keys=True),
                    datetime.now().astimezone().isoformat(timespec="seconds"),
                ),
            )

    def key_for(self, context: ExactResultCacheContext, problem: dict[str, Any]) -> str:
        payload = {
            "schema_version": EXACT_RESULT_CACHE_SCHEMA_VERSION,
            "solver_sha256": context.solver_sha256,
            "problem_sha256": _canonical_json_sha256(problem),
            "config_sha256": context.config_sha256,
            "official_fingerprint_sha256": context.official_fingerprint_sha256,
        }
        return _canonical_json_sha256(payload)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS exact_results (
                    cache_key TEXT PRIMARY KEY,
                    schema_version INTEGER NOT NULL,
                    solver_sha256 TEXT NOT NULL,
                    problem_sha256 TEXT NOT NULL,
                    config_sha256 TEXT NOT NULL,
                    official_fingerprint_sha256 TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn


def build_exact_result_cache_context(
    *,
    submission_dir: Path,
    official_repo: Path,
    config_path: Path | None,
) -> ExactResultCacheContext:
    solver_path = submission_dir / "solver.py"
    resolved_config_path = config_path or official_repo / "pipeline" / "config.json"
    return ExactResultCacheContext(
        solver_sha256=_file_sha256(solver_path),
        config_sha256=_file_sha256_or_missing(resolved_config_path),
        official_fingerprint_sha256=_official_fingerprint_sha256(official_repo),
    )


def _official_fingerprint_sha256(official_repo: Path) -> str:
    files = [
        "lean-toolchain",
        "lakefile.lean",
        "lake-manifest.json",
        "pipeline/runner.py",
        "pipeline/proxy.py",
        "judge/verify.py",
    ]
    parts: list[dict[str, str]] = []
    for relative in files:
        path = official_repo / relative
        parts.append(
            {
                "path": relative,
                "sha256": _file_sha256_or_missing(path),
            }
        )
    return _canonical_json_sha256(parts)


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _file_sha256_or_missing(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return "missing"
    return _file_sha256(path)


def _canonical_json_sha256(value: Any) -> str:
    data = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(data).hexdigest()
