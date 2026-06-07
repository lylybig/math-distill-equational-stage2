from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import dataclass
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from math_distill_stage2.evaluator_cache import (
    ExactResultCache,
    build_exact_result_cache_context,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OFFICIAL_STAGE2_REPO = REPO_ROOT / "external" / "equational-theories-lean-stage2"
DEFAULT_SOLO_SUBMISSION = REPO_ROOT / "submissions" / "solo_official"
RUNS_ROOT = REPO_ROOT / "artifacts" / "runs"
DEFAULT_OUTPUT_ROOT = RUNS_ROOT / datetime.now().astimezone().strftime("%Y-%m-%d")

PROBLEM_SUITES = {
    "sample200": ("examples/problems/sample_200.json",),
    "public-examples": (
        "examples/problems/normal.jsonl",
        "examples/problems/hard1.jsonl",
        "examples/problems/hard2.jsonl",
        "examples/problems/hard3.jsonl",
    ),
}


@dataclass(frozen=True)
class OfficialRunnerSummaryInput:
    run_id: str
    solver_name: str
    problem_set: str
    result_path: Path
    created_at: str
    results: list[dict[str, Any]]
    status: str = "done"


def summarize_official_runner_results(item: OfficialRunnerSummaryInput) -> dict[str, Any]:
    accepted = 0
    rejected = 0
    errors = 0
    accepted_verdicts: dict[str, int] = {}
    llm_total_calls = 0
    judge_total_calls = 0
    elapsed_seconds = 0.0

    for row in item.results:
        llm_total_calls += int(row.get("llm_calls") or 0)
        judge_calls = int(row.get("judge_calls") or 0)
        judge_total_calls += judge_calls
        elapsed_seconds += float(row.get("elapsed_seconds") or 0.0)
        if row.get("solved"):
            accepted += 1
            verdict = str(row.get("verdict") or "unknown")
            accepted_verdicts[verdict] = accepted_verdicts.get(verdict, 0) + 1
        elif judge_calls > 0:
            rejected += 1
        else:
            errors += 1

    total = len(item.results)
    progress_done = accepted + rejected + errors
    metrics_text = f"{accepted}A / {rejected}R / {errors}E"
    if llm_total_calls > 0:
        metrics_text = f"{metrics_text} / {llm_total_calls} calls"

    return {
        "schemaVersion": 1,
        "id": item.run_id,
        "status": item.status,
        "solverName": item.solver_name,
        "problemSet": item.problem_set,
        "totalProblems": total,
        "accepted": accepted,
        "rejected": rejected,
        "errors": errors,
        "llmTotalCalls": llm_total_calls,
        "judgeTotalCalls": judge_total_calls,
        "elapsedSeconds": round(elapsed_seconds, 2),
        "acceptedVerdicts": accepted_verdicts,
        "createdAt": item.created_at,
        "resultPath": str(item.result_path),
        "progressText": f"{progress_done}/{total}",
        "metricsText": metrics_text,
    }


def combine_history_rows(run_id: str, rows: list[dict[str, Any]], created_at: str) -> dict[str, Any]:
    accepted = sum(int(row["accepted"]) for row in rows)
    rejected = sum(int(row["rejected"]) for row in rows)
    errors = sum(int(row["errors"]) for row in rows)
    total = sum(int(row["totalProblems"]) for row in rows)
    llm_total_calls = sum(int(row["llmTotalCalls"]) for row in rows)
    judge_total_calls = sum(int(row["judgeTotalCalls"]) for row in rows)
    elapsed_seconds = sum(float(row["elapsedSeconds"]) for row in rows)
    accepted_verdicts: dict[str, int] = {}
    for row in rows:
        for verdict, count in row.get("acceptedVerdicts", {}).items():
            accepted_verdicts[verdict] = accepted_verdicts.get(verdict, 0) + int(count)

    return {
        "schemaVersion": 1,
        "id": run_id,
        "status": "done" if all(row["status"] == "done" for row in rows) else "failed",
        "solverName": rows[0]["solverName"] if rows else "",
        "problemSet": " + ".join(row["problemSet"] for row in rows),
        "totalProblems": total,
        "accepted": accepted,
        "rejected": rejected,
        "errors": errors,
        "llmTotalCalls": llm_total_calls,
        "judgeTotalCalls": judge_total_calls,
        "elapsedSeconds": round(elapsed_seconds, 2),
        "acceptedVerdicts": accepted_verdicts,
        "createdAt": created_at,
        "sets": rows,
        "progressText": f"{accepted + rejected + errors}/{total}",
        "metricsText": _format_metrics_text(accepted, rejected, errors, llm_total_calls),
    }


def write_history_artifacts(run_dir: Path, rows: list[dict[str, Any]]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    if len(rows) == 1:
        summary = dict(rows[0])
    else:
        created_at = rows[0]["createdAt"] if rows else datetime.now().astimezone().isoformat(timespec="seconds")
        run_id = rows[0]["id"].rsplit("__", 1)[0] if rows else run_dir.name
        summary = combine_history_rows(run_id, rows, created_at)

    (run_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (run_dir / "history.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (run_dir / "history.md").write_text(render_history_markdown(rows), encoding="utf-8")


def render_history_markdown(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No runs.\n"
    lines = [
        "| Status | Solver | Run ID | Progress | Metrics | Problem Set | Created At |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {status} | {solver} | {run_id} | {progress} | {metrics} | {problem_set} | {created_at} |".format(
                status=row["status"],
                solver=row["solverName"],
                run_id=row["id"],
                progress=row["progressText"],
                metrics=row["metricsText"],
                problem_set=row["problemSet"],
                created_at=row["createdAt"],
            )
        )
    return "\n".join(lines) + "\n"


def run_official_solo_history(
    *,
    submission_dir: Path,
    problem_sets: list[Path],
    run_dir: Path,
    official_repo: Path = DEFAULT_OFFICIAL_STAGE2_REPO,
    config_path: Path | None = None,
) -> list[dict[str, Any]]:
    created_at = datetime.now().astimezone().isoformat(timespec="seconds")
    run_dir.mkdir(parents=True, exist_ok=True)
    results_dir = run_dir / "results"
    logs_dir = run_dir / "logs"
    results_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for problem_set in problem_sets:
        problem_set = problem_set.resolve()
        problem_name = problem_set.stem
        result_path = results_dir / f"{problem_name}.json"
        log_path = logs_dir / f"{problem_name}.log"
        command = _build_runner_command(
            submission_dir=submission_dir,
            problem_set=problem_set,
            result_path=result_path,
            config_path=config_path,
        )
        returncode = _run_and_tee(command, cwd=official_repo, log_path=log_path)
        results = _read_result_rows(result_path)
        row = summarize_official_runner_results(
            OfficialRunnerSummaryInput(
                run_id=f"{run_dir.name}__{problem_name}",
                solver_name=submission_dir.name,
                problem_set=problem_name,
                result_path=result_path,
                created_at=created_at,
                results=results,
                status="done" if returncode == 0 else "failed",
            )
        )
        row["command"] = command
        row["logPath"] = str(log_path)
        row["returncode"] = returncode
        rows.append(row)
        write_history_artifacts(run_dir, rows)
    return rows


@dataclass(frozen=True)
class _ParallelProblemTask:
    index: int
    problem_indices: list[int]
    problems: list[dict[str, Any]]
    shard_path: Path
    result_path: Path
    log_path: Path
    command: list[str]


@dataclass(frozen=True)
class _ParallelProblemOutcome:
    index: int
    problem_indices: list[int]
    results: list[dict[str, Any]]
    returncode: int
    log_path: Path
    command: list[str]


def run_official_solo_history_parallel(
    *,
    submission_dir: Path,
    problem_sets: list[Path],
    run_dir: Path,
    official_repo: Path = DEFAULT_OFFICIAL_STAGE2_REPO,
    config_path: Path | None = None,
    max_workers: int = 4,
    problems_per_shard: int = 1,
    cache_dir: Path | None = None,
) -> list[dict[str, Any]]:
    created_at = datetime.now().astimezone().isoformat(timespec="seconds")
    run_dir.mkdir(parents=True, exist_ok=True)
    results_dir = run_dir / "results"
    logs_dir = run_dir / "logs"
    shard_root = run_dir / "parallel_shards"
    problem_logs_root = run_dir / "parallel_logs"
    results_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    shard_root.mkdir(parents=True, exist_ok=True)
    problem_logs_root.mkdir(parents=True, exist_ok=True)

    worker_count = max(1, int(max_workers))
    shard_size = max(1, int(problems_per_shard))
    exact_cache = ExactResultCache(cache_dir / "exact_results.sqlite") if cache_dir is not None else None
    exact_cache_context = (
        build_exact_result_cache_context(
            submission_dir=submission_dir,
            official_repo=official_repo,
            config_path=config_path,
        )
        if exact_cache is not None
        else None
    )
    cache_env = _cache_environment(cache_dir)
    rows: list[dict[str, Any]] = []
    for problem_set in problem_sets:
        problem_set = problem_set.resolve()
        problem_name = problem_set.stem
        result_path = results_dir / f"{problem_name}.json"
        log_path = logs_dir / f"{problem_name}.log"
        problems = _load_problem_rows(problem_set)
        cached_results_by_index: dict[int, dict[str, Any]] = {}
        indexed_problem_misses: list[tuple[int, dict[str, Any]]] = []
        if exact_cache is not None and exact_cache_context is not None:
            for index, problem in enumerate(problems):
                cached = exact_cache.get(exact_cache_context, problem)
                if cached is None:
                    indexed_problem_misses.append((index, problem))
                else:
                    cached_results_by_index[index] = cached
        else:
            indexed_problem_misses = list(enumerate(problems))
        tasks = _build_parallel_problem_tasks(
            submission_dir=submission_dir,
            indexed_problems=indexed_problem_misses,
            problem_name=problem_name,
            shard_dir=shard_root / problem_name,
            problem_log_dir=problem_logs_root / problem_name,
            config_path=config_path,
            problems_per_shard=shard_size,
        )
        with _patched_environ(cache_env):
            outcomes = _run_parallel_problem_tasks(
                tasks=tasks,
                official_repo=official_repo,
                max_workers=worker_count,
            )
        result_by_index = dict(cached_results_by_index)
        exact_cache_writes = 0
        for outcome in outcomes:
            for problem_index, result in zip(outcome.problem_indices, outcome.results, strict=False):
                result_by_index[problem_index] = result
                if exact_cache is not None and exact_cache_context is not None and outcome.returncode == 0:
                    exact_cache.put(exact_cache_context, problems[problem_index], result)
                    exact_cache_writes += 1
        ordered_results = [
            result_by_index.get(
                index,
                _synthetic_error_result(
                    problem,
                    message="parallel runner produced no result row and no exact cache entry",
                ),
            )
            for index, problem in enumerate(problems)
        ]
        result_path.write_text(
            json.dumps(ordered_results, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        _write_parallel_problem_set_log(
            log_path=log_path,
            problem_set=problem_set,
            outcomes=outcomes,
            max_workers=worker_count,
            cached_results_by_index=cached_results_by_index,
        )
        row = summarize_official_runner_results(
            OfficialRunnerSummaryInput(
                run_id=f"{run_dir.name}__{problem_name}",
                solver_name=submission_dir.name,
                problem_set=problem_name,
                result_path=result_path,
                created_at=created_at,
                results=ordered_results,
                status="done" if all(outcome.returncode == 0 for outcome in outcomes) else "failed",
            )
        )
        row["parallel"] = True
        row["maxWorkers"] = worker_count
        row["problemsPerShard"] = shard_size
        row["problemLogsDir"] = str((problem_logs_root / problem_name).resolve())
        row["logPath"] = str(log_path)
        row["returncode"] = 0 if all(outcome.returncode == 0 for outcome in outcomes) else 1
        if cache_dir is not None:
            row["cache"] = {
                "enabled": True,
                "dir": str(cache_dir.resolve()),
                "exactResultPath": str((cache_dir / "exact_results.sqlite").resolve()),
                "exactResultHits": len(cached_results_by_index),
                "exactResultMisses": len(indexed_problem_misses),
                "exactResultWrites": exact_cache_writes,
                "judgeCallPath": str((cache_dir / "judge_calls.sqlite").resolve()),
            }
        rows.append(row)
        write_history_artifacts(run_dir, rows)
    return rows


def resolve_problem_sets(
    *,
    official_repo: Path,
    suite: str,
    explicit_problem_sets: Iterable[Path],
) -> list[Path]:
    selected = [Path(path) for path in explicit_problem_sets]
    if selected:
        return [_resolve_path(path, base=official_repo) for path in selected]
    if suite not in PROBLEM_SUITES:
        raise ValueError(f"unknown suite: {suite!r}; expected one of {sorted(PROBLEM_SUITES)}")
    return [(official_repo / relative).resolve() for relative in PROBLEM_SUITES[suite]]


def default_run_id(suite: str) -> str:
    stamp = datetime.now().astimezone().strftime("%H%M%S")
    return f"{stamp}-official-solo-{suite}"


def _load_problem_rows(problem_set: Path) -> list[dict[str, Any]]:
    text = problem_set.read_text(encoding="utf-8")
    stripped = text.lstrip()
    if not stripped:
        raise ValueError(f"{problem_set}: file is empty")
    if stripped[0] == "[":
        data = json.loads(text)
        if not isinstance(data, list):
            raise ValueError(f"{problem_set}: expected JSON array")
        for index, value in enumerate(data, 1):
            if not isinstance(value, dict) or "id" not in value:
                raise ValueError(f"{problem_set}:{index}: expected problem object")
        return data
    rows: list[dict[str, Any]] = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        if not raw.strip():
            continue
        value = json.loads(raw)
        if not isinstance(value, dict) or "id" not in value:
            raise ValueError(f"{problem_set}:{lineno}: expected problem object")
        rows.append(value)
    return rows


def _build_parallel_problem_tasks(
    *,
    submission_dir: Path,
    indexed_problems: list[tuple[int, dict[str, Any]]],
    problem_name: str,
    shard_dir: Path,
    problem_log_dir: Path,
    config_path: Path | None,
    problems_per_shard: int,
) -> list[_ParallelProblemTask]:
    shard_dir.mkdir(parents=True, exist_ok=True)
    problem_log_dir.mkdir(parents=True, exist_ok=True)
    tasks: list[_ParallelProblemTask] = []
    shard_size = max(1, int(problems_per_shard))
    for start in range(0, len(indexed_problems), shard_size):
        shard_items = indexed_problems[start : start + shard_size]
        problem_indices = [index for index, _ in shard_items]
        shard_problems = [problem for _, problem in shard_items]
        first_index = problem_indices[0]
        last_index = problem_indices[-1]
        first_problem = shard_problems[0]
        safe_id = _safe_filename_part(str(first_problem.get("id") or f"problem_{first_index + 1}"))
        if first_index == last_index:
            stem = f"{first_index + 1:06d}_{safe_id}"
        else:
            stem = f"{first_index + 1:06d}-{last_index + 1:06d}_{safe_id}"
        shard_path = shard_dir / f"{stem}.json"
        result_path = shard_dir / f"{stem}.result.json"
        log_path = problem_log_dir / f"{stem}.log"
        shard_path.write_text(
            json.dumps(shard_problems, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        command = _build_runner_command(
            submission_dir=submission_dir,
            problem_set=shard_path,
            result_path=result_path,
            config_path=config_path,
        )
        tasks.append(
            _ParallelProblemTask(
                index=first_index,
                problem_indices=problem_indices,
                problems=shard_problems,
                shard_path=shard_path,
                result_path=result_path,
                log_path=log_path,
                command=command,
            )
        )
    return tasks


def _run_parallel_problem_tasks(
    *,
    tasks: list[_ParallelProblemTask],
    official_repo: Path,
    max_workers: int,
) -> list[_ParallelProblemOutcome]:
    if not tasks:
        return []
    outcomes_by_index: dict[int, _ParallelProblemOutcome] = {}
    done_count = 0
    total_count = sum(len(task.problems) for task in tasks)
    with ThreadPoolExecutor(max_workers=max(1, int(max_workers))) as pool:
        future_to_task = {
            pool.submit(_run_parallel_problem_task, task, official_repo): task
            for task in tasks
        }
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            try:
                outcome = future.result()
            except Exception as exc:  # noqa: BLE001
                outcome = _ParallelProblemOutcome(
                    index=task.index,
                    problem_indices=task.problem_indices,
                    results=[
                        _synthetic_error_result(
                            problem,
                            message=f"parallel runner task failed: {type(exc).__name__}: {exc}",
                        )
                        for problem in task.problems
                    ],
                    returncode=1,
                    log_path=task.log_path,
                    command=task.command,
                )
                task.log_path.write_text(
                    f"parallel runner task failed: {type(exc).__name__}: {exc}\n",
                    encoding="utf-8",
                )
            outcomes_by_index[outcome.index] = outcome
            for result in outcome.results:
                done_count += 1
                status = "SOLVED" if result.get("solved") else "FAILED"
                print(
                    "[{done}/{total}] {problem_id}: {status} "
                    "[llm:{llm}, judge:{judge}]".format(
                        done=done_count,
                        total=total_count,
                        problem_id=result.get("id", "?"),
                        status=status,
                        llm=int(result.get("llm_calls") or 0),
                        judge=int(result.get("judge_calls") or 0),
                    ),
                    flush=True,
                )
    return [outcomes_by_index[index] for index in sorted(outcomes_by_index)]


def _run_parallel_problem_task(
    task: _ParallelProblemTask,
    official_repo: Path,
) -> _ParallelProblemOutcome:
    returncode = _run_and_log(task.command, cwd=official_repo, log_path=task.log_path)
    result_rows = _read_result_rows(task.result_path)
    if result_rows:
        results = [dict(row) for row in result_rows]
    else:
        results = [
            _synthetic_error_result(
                problem,
                message=f"official runner produced no result row; returncode={returncode}",
            )
            for problem in task.problems
        ]
    return _ParallelProblemOutcome(
        index=task.index,
        problem_indices=task.problem_indices,
        results=results,
        returncode=returncode,
        log_path=task.log_path,
        command=task.command,
    )


def _synthetic_error_result(problem: dict[str, Any], *, message: str) -> dict[str, Any]:
    return {
        "id": problem.get("id"),
        "eq1_id": problem.get("eq1_id"),
        "eq2_id": problem.get("eq2_id"),
        "elapsed_seconds": 0.0,
        "solved": False,
        "verdict": None,
        "code": None,
        "llm_calls": 0,
        "judge_calls": 0,
        "log": [{"type": "error", "message": message}],
    }


def _write_parallel_problem_set_log(
    *,
    log_path: Path,
    problem_set: Path,
    outcomes: list[_ParallelProblemOutcome],
    max_workers: int,
    cached_results_by_index: dict[int, dict[str, Any]] | None = None,
) -> None:
    lines = [
        "Parallel official Solo run",
        f"Problem set: {problem_set}",
        f"Max workers: {max_workers}",
        f"Exact result cache hits: {len(cached_results_by_index or {})}",
        "",
    ]
    log_rows: list[tuple[int, str]] = []
    for index, result in (cached_results_by_index or {}).items():
        log_rows.append(
            (
                index,
                "[{index:06d}] {problem_id} returncode=0 "
                "solved={solved} llm={llm} judge={judge} log=exact-result-cache".format(
                    index=index + 1,
                    problem_id=result.get("id"),
                    solved=bool(result.get("solved")),
                    llm=int(result.get("llm_calls") or 0),
                    judge=int(result.get("judge_calls") or 0),
                ),
            )
        )
    for outcome in outcomes:
        relative_log = outcome.log_path
        try:
            relative_log = outcome.log_path.relative_to(log_path.parents[1])
        except ValueError:
            pass
        for problem_index, result in zip(outcome.problem_indices, outcome.results, strict=False):
            log_rows.append(
                (
                    problem_index,
                    "[{index:06d}] {problem_id} returncode={returncode} "
                    "solved={solved} llm={llm} judge={judge} log={log}".format(
                        index=problem_index + 1,
                        problem_id=result.get("id"),
                        returncode=outcome.returncode,
                        solved=bool(result.get("solved")),
                        llm=int(result.get("llm_calls") or 0),
                        judge=int(result.get("judge_calls") or 0),
                        log=relative_log,
                    ),
                )
            )
    lines.extend(row for _, row in sorted(log_rows))
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _cache_environment(cache_dir: Path | None) -> dict[str, str]:
    if cache_dir is None:
        return {}
    cache_dir.mkdir(parents=True, exist_ok=True)
    return {
        "STAGE2_JUDGE_CACHE_PATH": str((cache_dir / "judge_calls.sqlite").resolve()),
    }


@contextmanager
def _patched_environ(updates: dict[str, str]):
    if not updates:
        yield
        return
    old_values = {key: os.environ.get(key) for key in updates}
    os.environ.update(updates)
    try:
        yield
    finally:
        for key, old_value in old_values.items():
            if old_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_value


def _safe_filename_part(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")
    return safe[:80] or "problem"


def _format_metrics_text(accepted: int, rejected: int, errors: int, llm_total_calls: int) -> str:
    metrics = f"{accepted}A / {rejected}R / {errors}E"
    if llm_total_calls > 0:
        metrics = f"{metrics} / {llm_total_calls} calls"
    return metrics


def _build_runner_command(
    *,
    submission_dir: Path,
    problem_set: Path,
    result_path: Path,
    config_path: Path | None,
) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "pipeline.runner",
        "--submission",
        str(submission_dir.resolve()),
        "--problems",
        str(problem_set.resolve()),
        "--output",
        str(result_path.resolve()),
    ]
    if config_path is not None:
        command.extend(["--config", str(config_path.resolve())])
    return command


def _run_and_tee(command: list[str], *, cwd: Path, log_path: Path) -> int:
    return _run_subprocess(command, cwd=cwd, log_path=log_path, tee=True)


def _run_and_log(command: list[str], *, cwd: Path, log_path: Path) -> int:
    return _run_subprocess(command, cwd=cwd, log_path=log_path, tee=False)


def _run_subprocess(command: list[str], *, cwd: Path, log_path: Path, tee: bool) -> int:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONUNBUFFERED"] = "1"
    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            if tee:
                print(line, end="")
            log.write(line)
            log.flush()
        return proc.wait()


def _read_result_rows(result_path: Path) -> list[dict[str, Any]]:
    if not result_path.exists():
        return []
    data = json.loads(result_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{result_path}: expected official runner JSON array")
    return data


def _resolve_path(path: Path, *, base: Path) -> Path:
    return path if path.is_absolute() else (base / path).resolve()
