#!/usr/bin/env python3
"""Reusable evaluation entry for ETP Stage 2 solvers.

Wraps `scripts/run_generic.py`: validates inputs, loads .env, optionally
trims to a smoke subset, then invokes run_generic with the right env vars.
After completion, prints a quick by-stage / by-failure-mode summary.

Designed to be called from `scripts/run_eval.sh` (which handles backgrounding +
log redirection) OR directly:

  python3 scripts/run_eval.py --solver solvers/baseline_solver_v3e.py \\
      --problems third_party/equational-theories-lean-stage2/examples/problems/contest_1669.jsonl \\
      --workers 32 --timeout 1800 \\
      --output results/baseline_solver_v3e_contest_1669.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


# ─── .env loader ────────────────────────────────────────────────────────────

def load_env_file(path: Path) -> dict:
    """Parse a KEY=VALUE .env file. Skip comments/blank. Don't override
    variables already set in the current environment."""
    loaded = {}
    if not path.is_file():
        return loaded
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([A-Z_][A-Z0-9_]*)=(.*)$", line)
        if not m:
            continue
        k, v = m.group(1), m.group(2)
        # strip surrounding quotes if any
        if len(v) >= 2 and v[0] == v[-1] and v[0] in ('"', "'"):
            v = v[1:-1]
        if k not in os.environ:
            os.environ[k] = v
            loaded[k] = v
    return loaded


# ─── Problem helpers ────────────────────────────────────────────────────────

def count_problems(path: Path) -> int:
    if path.suffix == ".jsonl":
        with open(path) as f:
            return sum(1 for line in f if line.strip())
    return len(json.loads(path.read_text()))


def first_n_problems(src: Path, n: int) -> list:
    if src.suffix == ".jsonl":
        out = []
        with open(src) as f:
            for line in f:
                if line.strip():
                    out.append(json.loads(line))
                    if len(out) >= n:
                        break
        return out
    data = json.loads(src.read_text())
    return data[:n]


def build_smoke_file(src: Path, n: int) -> Path:
    sample = first_n_problems(src, n)
    fd, tmp = tempfile.mkstemp(prefix="etp_smoke_", suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(sample, f, ensure_ascii=False, indent=2)
    print(f"[smoke] {len(sample)} problems → {tmp}", file=sys.stderr)
    return Path(tmp)


# ─── Judge ping (non-fatal) ─────────────────────────────────────────────────

def ping_judge(url: str, timeout: float = 3.0) -> bool:
    try:
        req = urllib.request.Request(url.rstrip("/") + "/")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return True
    except urllib.error.HTTPError as e:
        # 4xx is fine — service is up, just no root handler
        return e.code < 500
    except Exception:
        return False


# ─── Post-run summary ───────────────────────────────────────────────────────

def summarise(result_path: Path) -> str:
    """Print solver/judge stats lifted from the result JSON written by
    run_generic.py.  Returns a one-line headline for caller logging."""
    try:
        data = json.loads(result_path.read_text())
    except Exception as e:
        return f"(could not read {result_path}: {e})"

    total = len(data)
    solved = sum(1 for e in data if e.get("solved"))
    by_stage = Counter()
    by_verdict_solved = Counter()
    fail_mode = Counter()
    last_stage_unsolved = Counter()

    stage_re = re.compile(r"^--\s*stage:(\S+)", re.MULTILINE)
    for e in data:
        if e.get("solved"):
            m = stage_re.search(e.get("code") or "")
            by_stage[m.group(1) if m else "no_tag"] += 1
            by_verdict_solved[e.get("verdict") or "?"] += 1
        else:
            log = e.get("log") or []
            last = log[-1] if log else {}
            t = last.get("type")
            if t == "timeout":
                fail_mode["wall_timeout"] += 1
            elif t == "judge":
                status = last.get("response", {}).get("status", "?")
                fail_mode[f"judge_{status}"] += 1
            elif t == "llm":
                fail_mode["llm_ended_no_judge"] += 1
            else:
                fail_mode[f"other:{t}"] += 1
            # Track which stage was last attempted
            for entry in reversed(log):
                if entry.get("type") == "judge":
                    m = stage_re.search(entry.get("request", {}).get("code", ""))
                    if m:
                        last_stage_unsolved[m.group(1)] += 1
                        break

    print(f"\n{'═'*70}")
    print(f"  RESULTS SUMMARY — {result_path.name}")
    print(f"{'═'*70}")
    print(f"  Total:     {total}")
    print(f"  Solved:    {solved} ({100*solved/total:.1f}%)")
    print(f"  Unsolved:  {total - solved}")
    print(f"  Verdict (solved): {dict(by_verdict_solved)}")
    print(f"\n  By stage (solved):")
    for s, n in sorted(by_stage.items(), key=lambda x: -x[1]):
        print(f"    {s:<25} {n:>5}   ({100*n/max(solved,1):>5.1f}% of solved)")
    print(f"\n  Failure mode (unsolved):")
    unsolved = total - solved
    for m, n in sorted(fail_mode.items(), key=lambda x: -x[1]):
        print(f"    {m:<25} {n:>5}   ({100*n/max(unsolved,1):>5.1f}% of unsolved)")
    print(f"\n  Last stage tried (unsolved, top):")
    for s, n in sorted(last_stage_unsolved.items(), key=lambda x: -x[1])[:8]:
        print(f"    {s:<25} {n:>5}")
    print(f"{'═'*70}\n")

    return f"{solved}/{total} = {100*solved/total:.1f}%"


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
    )
    p.add_argument("--solver", default="solvers/baseline_solver_v3e.py",
                   help="Solver script path (default: solvers/baseline_solver_v3e.py)")
    p.add_argument("--problems",
                   default="third_party/equational-theories-lean-stage2/examples/problems/sample_200.json",
                   help="Problem manifest .json or .jsonl")
    p.add_argument("--output",
                   help="Output JSON path. Default: results/<solver>_<problems>_<ts>.json")
    p.add_argument("--workers", type=int, default=8,
                   help="Parallel worker count (default: 8)")
    p.add_argument("--timeout", type=int, default=300,
                   help="Per-problem wall-clock seconds (default: 300)")
    p.add_argument("--judge-url", default=os.environ.get("JUDGE_SERVICE_URL",
                    "http://10.220.69.153:9666"),
                   help="Judge service URL")
    p.add_argument("--model", help="Override OPENAI_MODEL (LLM_MODEL)")
    p.add_argument("--llm-timeout", type=int, default=300,
                   help="LLM per-request HTTP timeout in seconds (default: 300)")
    p.add_argument("--llm-max-tokens", type=int, default=8192,
                   help="LLM max output tokens (default: 8192)")
    p.add_argument("--smoke", action="store_true",
                   help="Run only first 5 problems, 1 worker, 60s/题")
    p.add_argument("--smoke-n", type=int, default=5,
                   help="Smoke problem count (default: 5)")
    p.add_argument("--env-file", default=str(REPO_ROOT / ".env"),
                   help="Path to .env (default: <repo>/.env)")
    p.add_argument("--dry-run", action="store_true",
                   help="Print plan but don't launch run_generic.py")
    p.add_argument("--summary-only", metavar="RESULT_JSON",
                   help="Skip run; just print summary for an existing result file")
    p.add_argument("--resume", metavar="RESULT_JSON",
                   help="Resume an interrupted run.  Implies --output RESULT_JSON. "
                        "run_generic.py keeps solved entries and re-runs the rest. "
                        "(Equivalent to just passing --output the same path.)")
    p.add_argument("--retry-failed", action="store_true",
                   help="(with --resume) Force-retry already-failed entries too "
                        "(default: only retry NOT-YET-attempted). "
                        "Currently equivalent — run_generic always re-tries failed.")

    args = p.parse_args()

    # Summary-only short-circuit
    if args.summary_only:
        summarise(Path(args.summary_only))
        return 0

    # --resume = use the existing result file as both --output and the
    # checkpoint to continue from.
    if args.resume:
        args.output = args.resume

    # Load .env (won't clobber existing env)
    env_path = Path(args.env_file)
    loaded = load_env_file(env_path)
    if loaded:
        print(f"[env] loaded {len(loaded)} vars from {env_path}: "
              f"{sorted(loaded.keys())}", file=sys.stderr)

    # CLI model override
    if args.model:
        os.environ["OPENAI_MODEL"] = args.model
        os.environ["LLM_MODEL"] = args.model

    # Bridge OPENAI_* → LLM_* (run_generic.py reads LLM_*)
    if "LLM_BASE_URL" not in os.environ and "OPENAI_BASE_URL" in os.environ:
        os.environ["LLM_BASE_URL"] = os.environ["OPENAI_BASE_URL"]
    if "LLM_MODEL" not in os.environ:
        os.environ["LLM_MODEL"] = os.environ.get("OPENAI_MODEL", "gemma-4-31b")

    solver_path = (REPO_ROOT / args.solver).resolve() if not Path(args.solver).is_absolute() \
                  else Path(args.solver)
    problems_path = (REPO_ROOT / args.problems).resolve() if not Path(args.problems).is_absolute() \
                    else Path(args.problems)

    # Validate
    errors = []
    if not solver_path.is_file():
        errors.append(f"solver not found: {solver_path}")
    if not problems_path.is_file():
        errors.append(f"problems not found: {problems_path}")
    if not os.environ.get("OPENAI_API_KEY"):
        print("[warn] OPENAI_API_KEY not set — LLM stages will be skipped",
              file=sys.stderr)
    if not args.judge_url:
        errors.append("JUDGE_SERVICE_URL missing")
    if errors:
        for e in errors:
            print(f"[error] {e}", file=sys.stderr)
        return 2

    # Set JUDGE_SERVICE_URL env var (run_generic.py requires it)
    os.environ["JUDGE_SERVICE_URL"] = args.judge_url

    # Judge ping (non-fatal)
    if ping_judge(args.judge_url):
        print(f"[judge] OK at {args.judge_url}", file=sys.stderr)
    else:
        print(f"[warn] judge {args.judge_url} unreachable in 3s — continuing",
              file=sys.stderr)

    # Smoke prep
    workers = args.workers
    timeout = args.timeout
    smoke_tmp = None
    if args.smoke:
        smoke_tmp = build_smoke_file(problems_path, args.smoke_n)
        problems_path = smoke_tmp
        workers = 1
        timeout = 60
        print(f"[smoke] using {workers} worker, {timeout}s/题", file=sys.stderr)

    # Output path
    if args.output:
        out_path = Path(args.output)
        if not out_path.is_absolute():
            out_path = REPO_ROOT / out_path
    else:
        solver_base = solver_path.stem
        prob_base = problems_path.stem
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = REPO_ROOT / "results" / f"{solver_base}_{prob_base}_{ts}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    n_problems = count_problems(problems_path)

    # Resume detection: peek at existing output to report skip count up front
    resume_solved = 0
    if out_path.is_file():
        try:
            prior = json.loads(out_path.read_text())
            resume_solved = sum(1 for e in prior if e.get("solved"))
        except Exception:
            resume_solved = 0

    # Banner
    resume_note = ""
    if resume_solved:
        resume_note = (f"\n  ► RESUME: {resume_solved} solved entries kept, "
                       f"{n_problems - resume_solved} to run")
    banner = (
        f"{'═'*70}\n"
        f"  EVAL — {datetime.now():%Y-%m-%d %H:%M:%S}\n"
        f"{'═'*70}\n"
        f"  Solver:      {solver_path.relative_to(REPO_ROOT)}  "
        f"({solver_path.stat().st_size:,} bytes)\n"
        f"  Problems:    {problems_path}  ({n_problems} problems)\n"
        f"  Output:      {out_path.relative_to(REPO_ROOT)}{resume_note}\n"
        f"  Workers:     {workers}\n"
        f"  Per-problem: {timeout}s ({timeout/60:.1f} min)\n"
        f"  Judge URL:   {args.judge_url}\n"
        f"  LLM model:   {os.environ.get('LLM_MODEL', '<unset>')}\n"
        f"  LLM base:    {os.environ.get('LLM_BASE_URL', '<unset>')}\n"
        f"  Smoke:       {args.smoke}  Dry-run: {args.dry_run}\n"
        f"{'═'*70}"
    )
    print(banner)

    # Env for run_generic.py
    os.environ["SUBMISSION"] = str(solver_path)
    os.environ["PROBLEMS"] = str(problems_path)
    os.environ["OUTPUT"] = str(out_path)
    os.environ["WORKERS"] = str(workers)
    os.environ["SOLVER_TIMEOUT"] = str(timeout)
    os.environ["LLM_HTTP_TIMEOUT"] = str(args.llm_timeout)
    os.environ["LLM_MAX_OUTPUT_TOKENS"] = str(args.llm_max_tokens)

    if args.dry_run:
        print("\n[dry-run] would launch:")
        print(f"  python3 scripts/run_generic.py")
        for k in ("SUBMISSION", "PROBLEMS", "OUTPUT", "WORKERS",
                  "SOLVER_TIMEOUT", "JUDGE_SERVICE_URL", "LLM_MODEL",
                  "LLM_BASE_URL", "LLM_HTTP_TIMEOUT", "LLM_MAX_OUTPUT_TOKENS"):
            print(f"    {k}={os.environ.get(k, '')}")
        return 0

    # ── Launch run_generic.py ───────────────────────────────────────────────
    t_start = time.time()
    rc = subprocess.call(
        [sys.executable, "-u", str(REPO_ROOT / "scripts" / "run_generic.py")],
        cwd=str(REPO_ROOT),
    )
    elapsed = time.time() - t_start
    print(f"\n[run_generic] exit={rc}  wall={elapsed:.1f}s ({elapsed/60:.1f} min)",
          file=sys.stderr)

    # Cleanup smoke tempfile
    if smoke_tmp and smoke_tmp.exists():
        try: smoke_tmp.unlink()
        except Exception: pass

    # Summary
    if rc == 0 and out_path.is_file():
        headline = summarise(out_path)
        print(f"[done] {out_path.name}: {headline}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
