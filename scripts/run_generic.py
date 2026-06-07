"""Run baseline_solver_v3e against the remote judge_service for Lean verification
(no local Lean needed) and the official LLM endpoint (gemma-4-31b), with
parallel per-problem execution.

This is a near-twin of `scripts/run_opnorm.py` — same monkey-patch of
`pipeline.proxy._call_judge`, same parallel ThreadPoolExecutor — but
points the submission at `solvers/baseline_solver_v3e.py`.

Because pipeline.proxy requires the submission directory to contain
ONLY `solver.py` (no helper files, no symlinks), we stage baseline_solver_v3e.py
into a fresh tempdir on each invocation:

    /tmp/baseline_v3e_submission_<rand>/solver.py   ← copy of solvers/baseline_solver_v3e.py

Usage:
    OPENAI_API_KEY=sk-... python3 scripts/run_eval.py
    OPENAI_API_KEY=sk-... WORKERS=8 PROBLEMS=examples/problems/sample_200.json \\
        python3 scripts/run_eval.py

Env vars (same as run_opnorm.py except SUBMISSION is forced):
    OPENAI_API_KEY        required; LLM endpoint sk-... key
    JUDGE_SERVICE_URL     default http://10.220.69.153:9666
    LLM_BASE_URL          default http://60.171.65.125:30197/v1
    LLM_MODEL             default gemma-4-31b  (官方主推)
    LLM_HTTP_TIMEOUT      LLM per-request timeout in seconds; default 900
    WORKERS               number of problems to solve in parallel; default 4
    PROBLEMS              default examples/problems/sample_20.json
    OUTPUT                default results/baseline_solver_v3e.json (relative to repo root)
"""
from __future__ import annotations

import inspect
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SUBMODULE = REPO_ROOT / "third_party" / "equational-theories-lean-stage2"
SOLVER_SRC = Path(os.environ.get("SUBMISSION", REPO_ROOT / "solvers" / "baseline_solver_v3e.py"))
sys.path.insert(0, str(SUBMODULE))


# ---------------------------------------------------------------------------
# HTTP judge client (verbatim from scripts/run_opnorm.py)
# ---------------------------------------------------------------------------


def _call_judge_http(
    problem: dict,
    verdict: str,
    code: str,
    *,
    lean_timeout_seconds: int | None = None,
    max_code_length: int | None = None,
    max_false_cert_bytes: int | None = None,
) -> dict:
    """Drop-in for ``pipeline.proxy._call_judge`` — POST to the judge service."""
    from pipeline.proxy import _to_judge_problem  # local import; proxy is patched at startup

    judge_url = os.environ["JUDGE_SERVICE_URL"].rstrip("/")
    body: dict[str, Any] = {
        "problem": _to_judge_problem(problem),
        "verdict": verdict,
        "code": code,
    }
    if lean_timeout_seconds is not None:
        body["timeout_seconds"] = max(1, int(lean_timeout_seconds))

    data = json.dumps(body).encode("utf-8")
    http_timeout = (lean_timeout_seconds or 120) + 60
    deadline = time.time() + http_timeout * 2
    backoff = 1.0

    while True:
        req = urllib.request.Request(
            judge_url + "/verify",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=http_timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            try:
                err_body = e.read().decode("utf-8", errors="replace")
                err_payload = json.loads(err_body) if err_body else {}
            except Exception:
                err_payload, err_body = {}, ""
            detail = err_payload.get("detail") if isinstance(err_payload, dict) else None
            if e.code == 503 and time.time() < deadline:
                retry_ms = 2000
                if isinstance(detail, dict):
                    retry_ms = int(detail.get("retry_after_ms", retry_ms))
                time.sleep(max(backoff, retry_ms / 1000.0))
                backoff = min(backoff * 1.5, 10.0)
                continue
            if e.code == 400:
                return {"error": f"judge configuration error: {detail or err_body}"}
            return {"error": f"judge infrastructure error: HTTP {e.code} {err_body[:200]}"}
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if time.time() < deadline:
                time.sleep(backoff)
                backoff = min(backoff * 1.5, 10.0)
                continue
            return {"error": f"judge infrastructure error: {e}"}

    response: dict[str, Any] = {"status": result.get("status", "infra_error")}
    if result.get("stderr"):
        response["stderr"] = result["stderr"]
    if result.get("message"):
        response["message"] = result["message"]
    return response


def _patch_proxy() -> None:
    """Replace ``pipeline.proxy._call_judge`` with the HTTP variant."""
    from pipeline import proxy

    expected_params = {
        "problem", "verdict", "code",
        "lean_timeout_seconds", "max_code_length", "max_false_cert_bytes",
    }
    actual = set(inspect.signature(proxy._call_judge).parameters)
    missing = expected_params - actual
    if missing:
        sys.exit(
            f"upstream proxy._call_judge signature drift: missing {sorted(missing)}; "
            f"got {sorted(actual)}. Update {__file__} to match."
        )
    proxy._call_judge = _call_judge_http


# ---------------------------------------------------------------------------
# Config + submission staging
# ---------------------------------------------------------------------------


def _build_config(submodule: Path, model: str, base_url: str, http_timeout: int) -> dict:
    """In-memory pipeline config with the LLM endpoint patched in."""
    src = submodule / "pipeline" / "config.json"
    cfg = json.loads(src.read_text())
    llm = {
        **cfg.get("llm", {}),
        "model": model,
        "base_url": base_url,
        "api_key_env": "OPENAI_API_KEY",
        "http_timeout_seconds": http_timeout,
    }
    llm.pop("provider", None)
    llm.pop("reasoning_effort", None)
    cfg["llm"] = llm
    # Allow SOLVER_TIMEOUT env override (default keeps config.json value).
    solver_t = os.environ.get("SOLVER_TIMEOUT")
    if solver_t:
        cfg.setdefault("solver", {})["timeout_seconds"] = int(solver_t)
    # Allow LLM_MAX_OUTPUT_TOKENS env override for models with small ctx.
    max_out = os.environ.get("LLM_MAX_OUTPUT_TOKENS")
    if max_out:
        cfg["llm"]["max_output_tokens"] = int(max_out)
    return cfg


def _stage_submission() -> str:
    """Copy solvers/baseline_solver_v3e.py into a fresh tmpdir as solver.py.

    Returns the path string suitable for `proxy.run_solver(submission_path, ...)`.
    The submission directory contract: exactly one regular file named solver.py.
    """
    if not SOLVER_SRC.exists():
        sys.exit(f"missing {SOLVER_SRC} — write it first")
    tmp = Path(tempfile.mkdtemp(prefix="baseline_v3e_submission_"))
    shutil.copy(SOLVER_SRC, tmp / "solver.py")
    return str(tmp.resolve())


def _load_existing(output_path: Path) -> tuple[list[dict], set[str]]:
    """Mirror pipeline.runner: keep solved entries, drop failed so they retry."""
    if not output_path.exists():
        return [], set()
    try:
        prior = json.loads(output_path.read_text())
    except json.JSONDecodeError:
        return [], set()
    kept = [e for e in prior if e.get("solved")]
    return kept, {e["id"] for e in kept}


def _solve_one(submission_path: str, problem: dict, cfg: dict) -> dict:
    """Run pipeline.proxy.run_solver for one problem and pack the result."""
    from pipeline.proxy import run_solver
    t0 = time.time()
    result = run_solver(submission_path, problem, cfg)
    elapsed = time.time() - t0
    return {
        "id": problem["id"],
        "eq1_id": problem["eq1_id"],
        "eq2_id": problem["eq2_id"],
        "elapsed_seconds": round(elapsed, 2),
        **result,
    }


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        sys.exit("OPENAI_API_KEY must be set (LLM endpoint sk-... key)")

    os.environ.setdefault("JUDGE_SERVICE_URL", "http://10.220.69.153:9666")
    llm_base_url = os.environ.get("LLM_BASE_URL", "http://60.171.65.125:30197/v1")
    llm_model = os.environ.get("LLM_MODEL", "gemma-4-31b")
    llm_http_timeout = int(os.environ.get("LLM_HTTP_TIMEOUT", "900"))
    workers = max(1, int(os.environ.get("WORKERS", "4")))
    problems_path = os.environ.get("PROBLEMS", "examples/problems/sample_20.json")
    output_env = os.environ.get("OUTPUT", "results/baseline_solver_v3e.json")
    output_path = Path(output_env)
    if not output_path.is_absolute():
        output_path = REPO_ROOT / output_path
    output_path = output_path.resolve()

    _patch_proxy()
    cfg = _build_config(SUBMODULE, llm_model, llm_base_url, llm_http_timeout)
    submission = _stage_submission()

    # cd into the submodule so pipeline.proxy's relative paths and load_problems
    # resolve correctly.  The staged submission is already an absolute path.
    os.chdir(SUBMODULE)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    from pipeline.proxy import load_problems
    problems = load_problems(problems_path)

    print("──────────────────────────────────────────────")
    print(f" Solver:       {SOLVER_SRC}")
    print(f" Submission:   {submission}  (staged)")
    print(f" Problems:     {problems_path}  ({len(problems)} total)")
    print(f" Judge:        {os.environ['JUDGE_SERVICE_URL']}")
    print(f" LLM:          {llm_model} @ {llm_base_url}  (http_timeout={llm_http_timeout}s)")
    print(f" Workers:      {workers}")
    print(f" Output:       {output_path}")
    print("──────────────────────────────────────────────", flush=True)

    results, existing_solved = _load_existing(output_path)
    pending = [p for p in problems if p["id"] not in existing_solved]
    print(f"[skip] {len(existing_solved)} already solved | [pending] {len(pending)}", flush=True)

    write_lock = threading.Lock()
    started = time.time()
    completed = 0
    solved = len(existing_solved)
    failed = 0

    def _persist() -> None:
        tmp = output_path.with_suffix(output_path.suffix + ".tmp")
        tmp.write_text(json.dumps(results, indent=2, ensure_ascii=False))
        tmp.replace(output_path)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        future_to_pid = {
            pool.submit(_solve_one, submission, p, cfg): p["id"]
            for p in pending
        }
        for fut in as_completed(future_to_pid):
            pid = future_to_pid[fut]
            try:
                entry = fut.result()
            except Exception as e:
                entry = {
                    "id": pid, "solved": False, "verdict": None, "code": None,
                    "llm_calls": 0, "judge_calls": 0,
                    "log": [{"type": "error", "message": f"_solve_one raised: {e!r}"}],
                    "elapsed_seconds": 0.0,
                }
            with write_lock:
                results.append(entry)
                _persist()
                completed += 1
                if entry.get("solved"):
                    solved += 1
                    outcome = f"SOLVED ({entry.get('verdict')})"
                else:
                    failed += 1
                    outcome = "FAILED"
                print(
                    f"[{completed}/{len(pending)}] {pid} -> {outcome} "
                    f"in {entry.get('elapsed_seconds', 0):.1f}s "
                    f"[llm:{entry.get('llm_calls', 0)}, judge:{entry.get('judge_calls', 0)}]",
                    flush=True,
                )

    total = len(problems)
    print("\n" + "=" * 60)
    print(f"Results: {solved}/{total} solved, {failed} failed")
    print(f"Total time: {time.time() - started:.1f}s")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
