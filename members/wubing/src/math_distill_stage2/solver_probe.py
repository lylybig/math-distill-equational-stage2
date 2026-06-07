from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import time
from typing import Any, Iterable, Sequence


DEFAULT_SOLVER_PATH = Path("solvers/solo_official/current/solver.py")


@dataclass(frozen=True)
class SolverFirstMessageProbe:
    status: str
    elapsed_seconds: float
    message: dict[str, Any] | None
    returncode: int | None
    stderr_tail: str
    error: str | None = None
    expected_verdict: str | None = None

    @property
    def call(self) -> str | None:
        if not isinstance(self.message, dict):
            return None
        value = self.message.get("call")
        return str(value) if value is not None else None

    @property
    def verdict(self) -> str | None:
        if not isinstance(self.message, dict):
            return None
        value = self.message.get("verdict")
        return str(value) if value is not None else None

    @property
    def matches_expected_verdict(self) -> bool | None:
        if self.expected_verdict is None:
            return None
        return self.call == "judge" and self.verdict == self.expected_verdict

    def to_json(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "elapsed_seconds": self.elapsed_seconds,
            "call": self.call,
            "verdict": self.verdict,
            "expected_verdict": self.expected_verdict,
            "matches_expected_verdict": self.matches_expected_verdict,
            "message": self.message,
            "returncode": self.returncode,
            "stderr_tail": self.stderr_tail,
            "error": self.error,
        }


def build_problem_from_row(
    row: dict[str, Any],
    *,
    equations: Sequence[str] | None = None,
    expected_verdict: str | None = None,
    representative_pair_key: str | None = None,
) -> dict[str, Any]:
    """Build a Stage 2 Solo problem object from a candidate/probe row."""
    if isinstance(row.get("problem"), dict):
        problem = dict(row["problem"])
    else:
        eq1_id, eq2_id, pair_key = _extract_pair_ids(
            row,
            representative_pair_key=representative_pair_key,
        )
        equation1 = row.get("equation1")
        equation2 = row.get("equation2")
        if equation1 is None or equation2 is None:
            if equations is None:
                raise ValueError("row needs equation1/equation2 or an equations list")
            equation1 = _equation_by_id(equations, eq1_id)
            equation2 = _equation_by_id(equations, eq2_id)

        problem = {
            "id": str(row.get("id") or _default_problem_id(row, eq1_id, eq2_id, pair_key)),
            "eq1_id": eq1_id,
            "eq2_id": eq2_id,
            "equation1": str(equation1),
            "equation2": str(equation2),
        }
        if "answer" in row:
            problem["answer"] = row["answer"]

    if "answer" not in problem and expected_verdict in {"true", "false"}:
        problem["answer"] = expected_verdict == "true"
    return problem


def probe_solver_first_message(
    problem: dict[str, Any],
    *,
    solver_path: Path = DEFAULT_SOLVER_PATH,
    expected_verdict: str | None = None,
    timeout_seconds: float = 5.0,
    budget_timeout_seconds: float = 60.0,
    python_executable: str | None = None,
    shutdown_timeout_seconds: float = 1.0,
) -> SolverFirstMessageProbe:
    solver_path = Path(solver_path)
    python_executable = python_executable or sys.executable
    started_at = time.perf_counter()
    proc: subprocess.Popen[str] | None = None
    try:
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        proc = subprocess.Popen(
            [python_executable, str(solver_path)],
            text=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
    except OSError as exc:
        return SolverFirstMessageProbe(
            status="start_error",
            elapsed_seconds=_elapsed(started_at),
            message=None,
            returncode=None,
            stderr_tail="",
            error=str(exc),
            expected_verdict=expected_verdict,
        )

    assert proc.stdin is not None
    assert proc.stdout is not None
    try:
        payload = {"problem": problem, "budget": {"timeout_seconds": budget_timeout_seconds}}
        proc.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
        proc.stdin.flush()
    except (BrokenPipeError, OSError) as exc:
        _, stderr_tail = _finish_process(proc, kill=True, timeout_seconds=shutdown_timeout_seconds)
        return SolverFirstMessageProbe(
            status="write_error",
            elapsed_seconds=_elapsed(started_at),
            message=None,
            returncode=proc.returncode,
            stderr_tail=stderr_tail,
            error=str(exc),
            expected_verdict=expected_verdict,
        )

    ready, _, _ = select.select([proc.stdout], [], [], timeout_seconds)
    if not ready:
        _, stderr_tail = _finish_process(proc, kill=True, timeout_seconds=shutdown_timeout_seconds)
        return SolverFirstMessageProbe(
            status="timeout",
            elapsed_seconds=_elapsed(started_at),
            message=None,
            returncode=proc.returncode,
            stderr_tail=stderr_tail,
            expected_verdict=expected_verdict,
        )

    line = proc.stdout.readline()
    if not line:
        _, stderr_tail = _finish_process(proc, kill=True, timeout_seconds=shutdown_timeout_seconds)
        return SolverFirstMessageProbe(
            status="no_output",
            elapsed_seconds=_elapsed(started_at),
            message=None,
            returncode=proc.returncode,
            stderr_tail=stderr_tail,
            expected_verdict=expected_verdict,
        )

    try:
        message = json.loads(line)
    except json.JSONDecodeError as exc:
        _, stderr_tail = _finish_process(proc, kill=True, timeout_seconds=shutdown_timeout_seconds)
        return SolverFirstMessageProbe(
            status="invalid_json",
            elapsed_seconds=_elapsed(started_at),
            message=None,
            returncode=proc.returncode,
            stderr_tail=stderr_tail,
            error=str(exc),
            expected_verdict=expected_verdict,
        )

    response = {"status": "accepted"} if isinstance(message, dict) and message.get("call") == "judge" else None
    _, stderr_tail = _finish_process(
        proc,
        response=response,
        kill=response is None,
        timeout_seconds=shutdown_timeout_seconds,
    )
    return SolverFirstMessageProbe(
        status="message",
        elapsed_seconds=_elapsed(started_at),
        message=message if isinstance(message, dict) else None,
        returncode=proc.returncode,
        stderr_tail=stderr_tail,
        expected_verdict=expected_verdict,
    )


def probe_candidate_rows(
    rows: Iterable[dict[str, Any]],
    *,
    solver_path: Path = DEFAULT_SOLVER_PATH,
    equations: Sequence[str] | None = None,
    expected_verdict: str | None = None,
    timeout_seconds: float = 5.0,
    limit: int | None = None,
    python_executable: str | None = None,
    representative_pair_key: str | None = None,
    max_workers: int = 1,
) -> list[dict[str, Any]]:
    indexed_rows: list[tuple[int, dict[str, Any]]] = []
    for input_index, row in enumerate(rows):
        if limit is not None and input_index >= limit:
            break
        indexed_rows.append((input_index, row))

    if max_workers <= 1:
        return [
            _probe_indexed_row(
                input_index,
                row,
                solver_path=solver_path,
                equations=equations,
                expected_verdict=expected_verdict,
                timeout_seconds=timeout_seconds,
                python_executable=python_executable,
                representative_pair_key=representative_pair_key,
            )
            for input_index, row in indexed_rows
        ]

    output_rows: list[dict[str, Any] | None] = [None] * len(indexed_rows)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                _probe_indexed_row,
                input_index,
                row,
                solver_path=solver_path,
                equations=equations,
                expected_verdict=expected_verdict,
                timeout_seconds=timeout_seconds,
                python_executable=python_executable,
                representative_pair_key=representative_pair_key,
            ): position
            for position, (input_index, row) in enumerate(indexed_rows)
        }
        for future in as_completed(futures):
            output_rows[futures[future]] = future.result()

    return [row for row in output_rows if row is not None]


def _probe_indexed_row(
    input_index: int,
    row: dict[str, Any],
    *,
    solver_path: Path,
    equations: Sequence[str] | None,
    expected_verdict: str | None,
    timeout_seconds: float,
    python_executable: str | None,
    representative_pair_key: str | None,
) -> dict[str, Any]:
    problem = build_problem_from_row(
        row,
        equations=equations,
        expected_verdict=expected_verdict,
        representative_pair_key=representative_pair_key,
    )
    probe = probe_solver_first_message(
        problem,
        solver_path=solver_path,
        expected_verdict=expected_verdict,
        timeout_seconds=timeout_seconds,
        python_executable=python_executable,
    )
    output_row = dict(row)
    output_row["input_index"] = input_index
    output_row["problem"] = problem
    output_row["solver_probe"] = probe.to_json()
    return output_row


def summarize_solver_probe_rows(
    rows: Sequence[dict[str, Any]],
    *,
    expected_verdict: str | None = None,
) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    verdict_counts: dict[str, int] = {}
    elapsed_values: list[float] = []
    expected_fast_count = 0
    judge_count = 0

    for row in rows:
        probe = row.get("solver_probe") or {}
        status = str(probe.get("status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        elapsed = probe.get("elapsed_seconds")
        if isinstance(elapsed, (int, float)):
            elapsed_values.append(float(elapsed))
        if probe.get("call") == "judge":
            judge_count += 1
        verdict = probe.get("verdict")
        if verdict is not None:
            verdict_text = str(verdict)
            verdict_counts[verdict_text] = verdict_counts.get(verdict_text, 0) + 1
        if probe.get("matches_expected_verdict") is True:
            expected_fast_count += 1

    total = len(rows)
    solver_uncovered_count = total - expected_fast_count if expected_verdict is not None else None
    return {
        "schema_version": 1,
        "total_count": total,
        "expected_verdict": expected_verdict,
        "status_counts": status_counts,
        "verdict_counts": verdict_counts,
        "judge_count": judge_count,
        "expected_fast_count": expected_fast_count,
        "solver_uncovered_count": solver_uncovered_count,
        "timeout_count": status_counts.get("timeout", 0),
        "avg_elapsed_seconds": (
            sum(elapsed_values) / len(elapsed_values) if elapsed_values else None
        ),
        "max_elapsed_seconds": max(elapsed_values) if elapsed_values else None,
    }


def _required_int(row: dict[str, Any], key: str) -> int:
    if key not in row:
        raise ValueError(f"row is missing {key}")
    return int(row[key])


def _extract_pair_ids(
    row: dict[str, Any],
    *,
    representative_pair_key: str | None,
) -> tuple[int, int, str | None]:
    if "eq1_id" in row and "eq2_id" in row:
        return int(row["eq1_id"]), int(row["eq2_id"]), None

    representative_pairs = row.get("representative_pairs")
    if not isinstance(representative_pairs, dict):
        raise ValueError("row is missing eq1_id/eq2_id")

    keys = []
    if representative_pair_key is not None:
        keys.append(representative_pair_key)
    keys.extend(
        [
            "new_order5_source_to_order5_target",
            "new_order4_source_to_order5_target",
            "new_order5_source_to_order4_target",
        ]
    )
    keys.extend(sorted(str(key) for key in representative_pairs if key != "overlap_existing"))
    keys.append("overlap_existing")

    seen: set[str] = set()
    for key in keys:
        if key in seen:
            continue
        seen.add(key)
        value = representative_pairs.get(key)
        if _is_pair(value):
            return int(value[0]), int(value[1]), key
    raise ValueError("row has no usable representative pair")


def _is_pair(value: Any) -> bool:
    return isinstance(value, list) and len(value) == 2


def _default_problem_id(row: dict[str, Any], eq1_id: int, eq2_id: int, pair_key: str | None) -> str:
    if pair_key is None:
        return f"{eq1_id}_{eq2_id}"
    label = row.get("label")
    prefix = str(label) if label else "representative"
    return f"{prefix}:{pair_key}:{eq1_id}_{eq2_id}"


def _equation_by_id(equations: Sequence[str], equation_id: int) -> str:
    index = equation_id - 1
    if index < 0 or index >= len(equations):
        raise ValueError(f"equation id out of range: {equation_id}")
    return equations[index]


def _finish_process(
    proc: subprocess.Popen[str],
    *,
    response: dict[str, Any] | None = None,
    kill: bool = False,
    timeout_seconds: float = 1.0,
) -> tuple[str, str]:
    if proc.poll() is None and response is not None and proc.stdin is not None:
        try:
            proc.stdin.write(json.dumps(response, ensure_ascii=False) + "\n")
            proc.stdin.flush()
        except (BrokenPipeError, OSError):
            pass
    if proc.stdin is not None:
        try:
            proc.stdin.close()
        except OSError:
            pass

    if proc.poll() is None and kill:
        proc.kill()
    try:
        proc.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=timeout_seconds)

    stdout_tail = ""
    stderr_tail = ""
    if proc.stdout is not None:
        try:
            stdout_tail = proc.stdout.read() or ""
        except OSError:
            stdout_tail = ""
    if proc.stderr is not None:
        try:
            stderr_tail = proc.stderr.read() or ""
        except OSError:
            stderr_tail = ""
    return _tail(stdout_tail), _tail(stderr_tail)


def _tail(text: str, *, max_chars: int = 4000) -> str:
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def _elapsed(started_at: float) -> float:
    return round(time.perf_counter() - started_at, 6)
