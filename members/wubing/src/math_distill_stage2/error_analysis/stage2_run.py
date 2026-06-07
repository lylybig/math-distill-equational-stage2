from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(repo_root / "src"))
    sys.path.insert(0, str(repo_root))

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl


FORBIDDEN_PATTERNS = {
    "import": "import ",
    "Mathlib": "Mathlib",
    "overloaded_star": " * ",
    "dummy": "def dummy",
    "placeholder_true": "theorem certificate : True",
    "starts_with_by": "by\n",
}


def analyze_stage2_run(run_dir: Path) -> dict[str, Any]:
    per_run_path = run_dir / "per_run.jsonl"
    if not per_run_path.exists():
        return analyze_official_runner_run(run_dir)

    return analyze_legacy_evaluator_run(run_dir)


def analyze_legacy_evaluator_run(run_dir: Path) -> dict[str, Any]:
    records = read_jsonl(run_dir / "per_run.jsonl")
    summary = _read_json(run_dir / "summary.json")
    errors: list[dict[str, Any]] = []
    category_counts: Counter[str] = Counter()
    subcategory_counts: Counter[str] = Counter()
    forbidden_counts: Counter[str] = Counter()
    representatives: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for record in records:
        classification = classify_record(record)
        if classification["category"] == "success":
            continue
        error = {
            "problem_id": record.get("problem_id"),
            "subset": record.get("subset"),
            "expected_verdict": record.get("expected_verdict"),
            "actual_verdict": record.get("actual_verdict"),
            "request_status": record.get("request_status"),
            "parsed_status": record.get("parsed_status"),
            "verdict_check_status": record.get("verdict_check_status"),
            "lean4_status": record.get("lean4_status"),
            "error_type": record.get("error_type"),
            "category": classification["category"],
            "subcategory": classification["subcategory"],
            "forbidden_patterns": classification["forbidden_patterns"],
            "lean_excerpt": classification["lean_excerpt"],
            "code_excerpt": classification["code_excerpt"],
        }
        errors.append(error)
        category_counts[str(error["category"])] += 1
        subcategory_counts[str(error["subcategory"])] += 1
        for pattern in error["forbidden_patterns"]:
            forbidden_counts[str(pattern)] += 1
        if len(representatives[str(error["subcategory"])]) < 3:
            representatives[str(error["subcategory"])].append(
                {
                    "problem_id": error["problem_id"],
                    "expected_verdict": error["expected_verdict"],
                    "actual_verdict": error["actual_verdict"],
                    "lean_excerpt": error["lean_excerpt"],
                    "code_excerpt": error["code_excerpt"],
                }
            )

    taxonomy = {
        "schema_version": 1,
        "input_format": "legacy_per_run",
        "run_dir": str(run_dir),
        "total_records": len(records),
        "success_count": sum(1 for row in records if row.get("reasoning_correct") is True),
        "failure_count": len(errors),
        "category_counts": dict(sorted(category_counts.items())),
        "subcategory_counts": dict(sorted(subcategory_counts.items())),
        "forbidden_pattern_counts": dict(sorted(forbidden_counts.items())),
        "leaderboard_metrics": summary.get("leaderboard_metrics", {}),
        "stage_metrics": summary.get("stage_metrics", {}),
        "representative_errors": dict(sorted(representatives.items())),
    }
    write_jsonl(run_dir / "errors.jsonl", errors)
    _write_json(run_dir / "failure_taxonomy.json", taxonomy)
    (run_dir / "analysis.md").write_text(_render_markdown(taxonomy), encoding="utf-8")
    return taxonomy


def analyze_official_runner_run(run_dir: Path) -> dict[str, Any]:
    result_rows = _read_official_result_rows(run_dir)
    summary = _read_json(run_dir / "summary.json")
    errors: list[dict[str, Any]] = []
    category_counts: Counter[str] = Counter()
    subcategory_counts: Counter[str] = Counter()
    representatives: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in result_rows:
        classification = classify_official_runner_row(row)
        if classification["category"] == "success":
            continue
        error = {
            "problem_id": row.get("id"),
            "eq1_id": row.get("eq1_id"),
            "eq2_id": row.get("eq2_id"),
            "verdict": row.get("verdict"),
            "solved": row.get("solved"),
            "judge_calls": int(row.get("judge_calls") or 0),
            "llm_calls": int(row.get("llm_calls") or 0),
            "elapsed_seconds": float(row.get("elapsed_seconds") or 0.0),
            "category": classification["category"],
            "subcategory": classification["subcategory"],
            "log_excerpt": classification["log_excerpt"],
        }
        errors.append(error)
        category_counts[str(error["category"])] += 1
        subcategory_counts[str(error["subcategory"])] += 1
        if len(representatives[str(error["subcategory"])]) < 5:
            representatives[str(error["subcategory"])].append(
                {
                    "problem_id": error["problem_id"],
                    "verdict": error["verdict"],
                    "judge_calls": error["judge_calls"],
                    "llm_calls": error["llm_calls"],
                    "log_excerpt": error["log_excerpt"],
                }
            )

    taxonomy = {
        "schema_version": 1,
        "input_format": "official_runner_results",
        "run_dir": str(run_dir),
        "total_records": len(result_rows),
        "success_count": sum(1 for row in result_rows if row.get("solved") is True),
        "failure_count": len(errors),
        "category_counts": dict(sorted(category_counts.items())),
        "subcategory_counts": dict(sorted(subcategory_counts.items())),
        "official_runner_metrics": {
            key: summary.get(key)
            for key in (
                "accepted",
                "rejected",
                "errors",
                "acceptedVerdicts",
                "llmTotalCalls",
                "judgeTotalCalls",
                "metricsText",
            )
            if key in summary
        },
        "representative_errors": dict(sorted(representatives.items())),
    }
    write_jsonl(run_dir / "errors.jsonl", errors)
    _write_json(run_dir / "failure_taxonomy.json", taxonomy)
    (run_dir / "analysis.md").write_text(_render_markdown(taxonomy), encoding="utf-8")
    return taxonomy


def classify_record(record: dict[str, Any]) -> dict[str, Any]:
    code = str(((record.get("judge_call") or {}).get("code")) or "")
    lean_text = _lean_text(record)
    forbidden = _forbidden_patterns(code)

    if record.get("request_status") != "ok":
        category = "request_failure"
        subcategory = str(record.get("error_type") or "request_error")
    elif record.get("parsed_status") != "parsed":
        category = "parse_failure"
        subcategory = str(record.get("parsed_status") or "parse_failure")
    elif record.get("verdict_check_status") == "failed":
        category = "verdict_failure"
        subcategory = "wrong_verdict"
    elif record.get("lean4_status") in {"failed", "timeout"}:
        category = "lean4_failure"
        subcategory = _classify_lean_failure(code, lean_text, str(record.get("lean4_status")))
    elif record.get("reasoning_correct") is True:
        category = "success"
        subcategory = "success"
    else:
        category = "other_failure"
        subcategory = "unknown_failure"

    return {
        "category": category,
        "subcategory": subcategory,
        "forbidden_patterns": forbidden,
        "lean_excerpt": _excerpt(lean_text),
        "code_excerpt": _excerpt(code),
    }


def classify_official_runner_row(row: dict[str, Any]) -> dict[str, Any]:
    if row.get("solved") is True:
        category = "success"
        subcategory = "success"
    else:
        judge_calls = int(row.get("judge_calls") or 0)
        llm_calls = int(row.get("llm_calls") or 0)
        if judge_calls > 0:
            category = "judge_rejected"
            subcategory = "judge_rejected_candidate"
        elif llm_calls > 0:
            category = "llm_failure"
            subcategory = "llm_no_accepted_candidate"
        else:
            category = "no_candidate"
            subcategory = "deterministic_no_candidate"
    return {
        "category": category,
        "subcategory": subcategory,
        "log_excerpt": _excerpt(json.dumps(row.get("log") or [], ensure_ascii=False), limit=900),
    }


def _classify_lean_failure(code: str, lean_text: str, lean_status: str) -> str:
    text = f"{code}\n{lean_text}"
    if lean_status == "timeout":
        return "lean_timeout"
    if _forbidden_patterns(code) or "unknown module prefix 'Mathlib'" in text:
        return "lean_forbidden_pattern"
    if code.lstrip().startswith("by"):
        return "lean_proof_fragment"
    if "synthInstanceFailed" in text or "HMul" in text or "overloaded" in text:
        return "lean_typeclass_failure"
    if "|>" in code or ("has type\n  Prop" in text and "expected to have type\n  α" in text):
        return "lean_bad_translation_failure"
    if "maximum recursion depth has been reached" in text:
        return "lean_simp_loop_failure"
    if "Unknown identifier" in text or "already been declared" in text:
        return "lean_name_error"
    if "No goals to be solved" in text:
        return "lean_tactic_state_failure"
    if "Function expected at" in text:
        return "lean_arity_failure"
    if "unexpected token" in text or "expected command" in text or "Invalid pattern" in text:
        return "lean_syntax_failure"
    if "Type mismatch" in text:
        return "lean_type_mismatch"
    if "Tactic `rfl` failed" in text or "not definitionally equal" in text:
        return "lean_semantic_failure"
    return "lean_other_failure"


def _forbidden_patterns(code: str) -> list[str]:
    patterns: list[str] = []
    for name, needle in FORBIDDEN_PATTERNS.items():
        if name == "starts_with_by":
            if code.lstrip().startswith("by"):
                patterns.append(name)
        elif needle in code:
            patterns.append(name)
    return patterns


def _lean_text(record: dict[str, Any]) -> str:
    lean4_result = record.get("lean4_result") or {}
    if not isinstance(lean4_result, dict):
        return ""
    return "\n".join(str(lean4_result.get(key) or "") for key in ("stdout", "stderr"))


def _excerpt(text: str, limit: int = 700) -> str:
    cleaned = text.strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit] + "...[truncated]"


def _render_markdown(taxonomy: dict[str, Any]) -> str:
    if taxonomy.get("input_format") == "official_runner_results":
        return _render_official_markdown(taxonomy)

    lines = [
        "# Stage 2 Run Analysis",
        "",
        f"Run dir: `{taxonomy['run_dir']}`",
        "",
        "## Leaderboard Metrics",
        "",
        _json_block(taxonomy.get("leaderboard_metrics", {})),
        "",
        "## Stage Metrics",
        "",
        _json_block(taxonomy.get("stage_metrics", {})),
        "",
        "## Failure Taxonomy",
        "",
        "### Categories",
        "",
        _json_block(taxonomy.get("category_counts", {})),
        "",
        "### Subcategories",
        "",
        _json_block(taxonomy.get("subcategory_counts", {})),
        "",
        "### Forbidden Patterns",
        "",
        _json_block(taxonomy.get("forbidden_pattern_counts", {})),
        "",
        "## Representative Errors",
        "",
    ]
    for subcategory, examples in taxonomy.get("representative_errors", {}).items():
        lines.extend([f"### {subcategory}", ""])
        for example in examples:
            lines.extend(
                [
                    f"- `{example.get('problem_id')}` expected `{example.get('expected_verdict')}` actual `{example.get('actual_verdict')}`",
                    "",
                    "Lean excerpt:",
                    "",
                    "```text",
                    str(example.get("lean_excerpt") or ""),
                    "```",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def _render_official_markdown(taxonomy: dict[str, Any]) -> str:
    lines = [
        "# Stage 2 Official Runner Analysis",
        "",
        f"Run dir: `{taxonomy['run_dir']}`",
        "",
        "## Official Runner Metrics",
        "",
        _json_block(taxonomy.get("official_runner_metrics", {})),
        "",
        "## Failure Taxonomy",
        "",
        "### Categories",
        "",
        _json_block(taxonomy.get("category_counts", {})),
        "",
        "### Subcategories",
        "",
        _json_block(taxonomy.get("subcategory_counts", {})),
        "",
        "## Representative Errors",
        "",
    ]
    for subcategory, examples in taxonomy.get("representative_errors", {}).items():
        lines.extend([f"### {subcategory}", ""])
        for example in examples:
            lines.extend(
                [
                    f"- `{example.get('problem_id')}` verdict `{example.get('verdict')}` "
                    f"judge `{example.get('judge_calls')}` llm `{example.get('llm_calls')}`",
                    "",
                    "Log excerpt:",
                    "",
                    "```text",
                    str(example.get("log_excerpt") or ""),
                    "```",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def _read_official_result_rows(run_dir: Path) -> list[dict[str, Any]]:
    results_dir = run_dir / "results"
    if not results_dir.exists():
        raise FileNotFoundError(
            f"expected either {run_dir / 'per_run.jsonl'} or official runner results under {results_dir}"
        )
    rows: list[dict[str, Any]] = []
    for path in sorted(results_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            rows.extend(dict(row, result_file=path.name) for row in payload)
    if not rows:
        raise FileNotFoundError(f"no official runner result rows found under {results_dir}")
    return rows


def _json_block(payload: Any) -> str:
    return "```json\n" + json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n```"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze a Stage 2 evaluator run and write failure reports.")
    parser.add_argument("--run-dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    taxonomy = analyze_stage2_run(args.run_dir)
    print(json.dumps(taxonomy, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
