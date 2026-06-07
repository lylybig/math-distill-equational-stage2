from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.proof_bank.keying import (
    canonical_signature_for_bank,
    problem_key_from_equations,
)
from math_distill_stage2.proof_bank.etp_context import (
    DEFAULT_ETP_IMPLICATIONS_PATH,
    find_etp_implication_context,
)
from math_distill_stage2.proof_bank.skill_guidance import (
    DEFAULT_GENERATION_SKILL_PATH,
    DEFAULT_LEAN_PROOF_SKILL_PATH,
    SkillPromptFragment,
    load_skill_guidance_for_problem,
    render_skill_guidance,
)
from math_distill_stage2.proof_bank.storage import write_json


def run_dir_for(run_root: Path, source_run_id: str, day: date | None = None) -> Path:
    day = day or date.today()
    return run_root / day.isoformat() / source_run_id


def build_prompt_pack(
    *,
    bank: Path,
    candidate_pool: Path,
    run_root: Path,
    source_run_id: str,
    limit: int,
    prompt_policy: str,
    allow_existing_accepted: bool = False,
    etp_implications_path: Path | None = DEFAULT_ETP_IMPLICATIONS_PATH,
    generation_skill_path: Path | None = DEFAULT_GENERATION_SKILL_PATH,
    lean_proof_skill_path: Path | None = DEFAULT_LEAN_PROOF_SKILL_PATH,
    max_high_signal_without_etp: int | None = None,
) -> dict[str, Any]:
    rows = read_jsonl(candidate_pool)
    accepted_problem_keys = set()
    if not allow_existing_accepted and (bank / "accepted.jsonl").exists():
        accepted_problem_keys = {
            str(row["problem_key"])
            for row in read_jsonl(bank / "accepted.jsonl")
            if row.get("certificate_kind") == "true_proof" and row.get("problem_key")
        }

    selected: list[dict[str, Any]] = []
    selected_etp_contexts: list[dict[str, Any] | None] = []
    skipped_existing_accepted_count = 0
    skipped_high_signal_without_etp_count = 0
    high_signal_without_etp_count = 0
    for row in rows:
        eq1 = str(row["equation1"])
        eq2 = str(row["equation2"])
        problem_key = problem_key_from_equations(eq1, eq2)
        if problem_key in accepted_problem_keys:
            skipped_existing_accepted_count += 1
            continue
        candidate_problem = {
            **row,
            "problem_key": problem_key,
            "eq1_signature": canonical_signature_for_bank(eq1),
            "eq2_signature": canonical_signature_for_bank(eq2),
        }
        etp_context = find_etp_implication_context(
            candidate_problem,
            implications_path=etp_implications_path,
        )
        is_high_signal_without_etp = (
            row.get("source_candidate_stratum") == "high_signal_failed_attempts"
            and etp_context is None
        )
        if (
            max_high_signal_without_etp is not None
            and is_high_signal_without_etp
            and high_signal_without_etp_count >= max_high_signal_without_etp
        ):
            skipped_high_signal_without_etp_count += 1
            continue
        if is_high_signal_without_etp:
            high_signal_without_etp_count += 1
        selected.append(row)
        selected_etp_contexts.append(etp_context)
        if len(selected) >= limit:
            break

    run_dir = run_dir_for(run_root, source_run_id)
    prompt_dir = run_dir / "prompt_pack"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    input_rows: list[dict[str, Any]] = []
    skill_guidance_manifest: dict[tuple[str, str, str], dict[str, str]] = {}
    for index, (row, etp_context) in enumerate(zip(selected, selected_etp_contexts, strict=True), start=1):
        item_id = f"{index:06d}"
        eq1 = str(row["equation1"])
        eq2 = str(row["equation2"])
        problem_key = problem_key_from_equations(eq1, eq2)
        problem = {
            **row,
            "schema_version": 1,
            "item_id": item_id,
            "problem_key": problem_key,
            "eq1_signature": canonical_signature_for_bank(eq1),
            "eq2_signature": canonical_signature_for_bank(eq2),
        }
        if etp_context is not None:
            problem["etp_context"] = etp_context
        skill_guidance = load_skill_guidance_for_problem(
            problem,
            generation_skill_path=generation_skill_path,
            lean_proof_skill_path=lean_proof_skill_path,
        )
        if skill_guidance:
            skill_metadata = [fragment.metadata() for fragment in skill_guidance]
            problem["prompt_skill_guidance"] = skill_metadata
            for metadata in skill_metadata:
                key = (
                    metadata["name"],
                    metadata["source_role"],
                    metadata["path"],
                )
                skill_guidance_manifest[key] = metadata
        input_rows.append(problem)
        raw_response_path = run_dir / "raw_responses" / f"{item_id}.txt"
        prompt_text = render_prompt_item(
            problem,
            source_run_id,
            raw_response_path,
            etp_context=etp_context,
            skill_guidance=skill_guidance,
        )
        (prompt_dir / f"{item_id}.md").write_text(prompt_text, encoding="utf-8")

    write_jsonl(run_dir / "input_problems.jsonl", input_rows)
    manifest = {
        "schema_version": 1,
        "source_run_id": source_run_id,
        "bank_id": "gpt_true_certificates",
        "bank": str(bank),
        "candidate_pool": str(candidate_pool),
        "prompt_policy": prompt_policy,
        "problem_count": len(input_rows),
        "allow_existing_accepted": allow_existing_accepted,
        "skipped_existing_accepted_count": skipped_existing_accepted_count,
        "max_high_signal_without_etp": max_high_signal_without_etp,
        "skipped_high_signal_without_etp_count": skipped_high_signal_without_etp_count,
        "etp_context": {
            "enabled": etp_implications_path is not None,
            "implications_path": str(etp_implications_path) if etp_implications_path else None,
        },
        "skill_guidance": sorted(
            skill_guidance_manifest.values(),
            key=lambda item: (item["source_role"], item["name"], item["path"]),
        ),
    }
    write_json(run_dir / "manifest.json", manifest)
    return {
        "run_dir": str(run_dir),
        "problem_count": len(input_rows),
        "skipped_existing_accepted_count": skipped_existing_accepted_count,
        "max_high_signal_without_etp": max_high_signal_without_etp,
        "skipped_high_signal_without_etp_count": skipped_high_signal_without_etp_count,
    }


def render_prompt_item(
    problem: dict[str, Any],
    source_run_id: str,
    raw_response_path: Path,
    *,
    etp_context: dict[str, Any] | None = None,
    skill_guidance: list[SkillPromptFragment] | None = None,
) -> str:
    trace = "none"
    if problem.get("external_trace_available"):
        trace = str(problem.get("external_trace_family") or "available")
    trace_context = render_trace_context(problem)
    etp_text = render_etp_context(etp_context)
    skill_guidance_text = render_skill_guidance(skill_guidance or [])
    return f"""# Stage 2 True Certificate Prompt Item

## Artifact Routing

- source_run_id: {source_run_id}
- item_id: {problem["item_id"]}
- raw_response_path: {raw_response_path}

## Problem Identity

- problem_key: {problem["problem_key"]}
- source_problem_id: {problem.get("source_problem_id")}
- source_dataset: {problem.get("source_dataset")}
- eq1_id: {problem.get("eq1_id")}
- eq2_id: {problem.get("eq2_id")}

## Equations

Premise equation `h`:

```text
{problem["equation1"]}
```

Goal equation:

```text
{problem["equation2"]}
```

## Judge Wrapper

Your proof will be inserted here:

```lean
import JudgeProblem

def submission : Goal := by
  intro G _ h
  <YOUR PROOF BODY>
```

## Required Output

Write exactly one JSON object to `raw_response_path`. Do not use Markdown fences,
extra commentary, or multiple JSON objects.

```json
{{
  "verdict": "true",
  "proof": "intro x y z\\ncalc\\n  x = x := rfl"
}}
```

The `proof` field must be only the tactic body after `intro G _ h`.
If you cannot finish a proof, still write a JSON object with `"verdict": "true"`,
an empty `"proof": ""`, and a short `"notes"` field explaining the blocker.

## Allowed Lean Constructs

Prefer: `intro`, `let`, `have`, `calc`, `exact`, `fun`, `rfl`, `Eq.trans`, `Eq.symm`, `.trans`, `.symm`, `congrArg`.

## Forbidden

`sorry`, `admit`, `axiom`, `unsafe`, `import`, theorem headers, `def submission`, external theorem names, `congr_arg`, `*`.

Use `◇`, not `*`. Use `congrArg`, not `congr_arg`.
{skill_guidance_text}
{etp_text}

## Optional Trace Hint

trace: {trace}

These hints are not available as theorem names. They may only guide a self-contained proof from `h`.
{trace_context}
"""


def render_etp_context(etp_context: dict[str, Any] | None) -> str:
    if not etp_context:
        return ""
    id_path = " -> ".join(f"Equation{eq_id}" for eq_id in etp_context.get("path", ()))
    lines = [
        "## ETP Blueprint Context",
        "",
        f"- local implication source: {etp_context.get('source')}",
        f"- blueprint reference: {etp_context.get('blueprint_reference')}",
        f"- proof path hint: {id_path}",
        "",
        "These hints are not available as theorem names in the judge environment. Use them only to guide a self-contained proof from `h`.",
        "",
        "ETP path edges:",
    ]
    for edge in etp_context.get("edges", ()):
        filename = edge.get("filename")
        file_label = Path(str(filename)).name if filename else "unknown"
        line = edge.get("line")
        if line is not None:
            file_label = f"{file_label}:{line}"
        lines.append(
            "- "
            f"Equation{edge.get('lhs_id')} -> Equation{edge.get('rhs_id')}: "
            f"{edge.get('name') or 'unknown'} ({file_label})"
        )
    return "\n" + "\n".join(lines) + "\n"


def render_trace_context(problem: dict[str, Any]) -> str:
    lines: list[str] = []
    if problem.get("external_trace_available"):
        lines.append("## Prior Solver Trace Summary")
        lines.append("")
        lines.append(f"- candidate stratum: {problem.get('source_candidate_stratum') or 'unknown'}")
        if problem.get("priority_score") is not None:
            lines.append(f"- priority score: {problem.get('priority_score')}")
        counter_labels = (
            ("h_application_count", "h applications"),
            ("trans_count", "Eq.trans-like steps"),
            ("symm_count", "Eq.symm-like steps"),
            ("congrArg_count", "congrArg-like steps"),
            ("unknown_tactic_count", "unknown tactic errors"),
            ("unsolved_goal_count", "unsolved goals"),
            ("type_mismatch_count", "type mismatches"),
        )
        for key, label in counter_labels:
            if problem.get(key) is not None:
                lines.append(f"- {label}: {problem.get(key)}")
        if problem.get("previous_solver_elapsed_seconds") is not None:
            lines.append(
                f"- previous solver seconds: {problem.get('previous_solver_elapsed_seconds')}"
            )
        if problem.get("previous_solver_judge_calls") is not None:
            lines.append(
                f"- previous solver judge calls: {problem.get('previous_solver_judge_calls')}"
            )
        if problem.get("source_attempt_id"):
            lines.append(f"- repair source attempt: {problem.get('source_attempt_id')}")
        if problem.get("previous_judge_error_kind"):
            lines.append(f"- previous judge error: {problem.get('previous_judge_error_kind')}")
        if problem.get("previous_judge_error_summary"):
            lines.append(f"- previous error summary: {problem.get('previous_judge_error_summary')}")

    excerpt = str(problem.get("previous_proof_body_excerpt") or "").strip()
    if excerpt:
        if not lines:
            lines.extend(["## Prior Solver Trace Summary", ""])
        lines.append("")
        lines.append("Previous proof excerpt:")
        lines.append("")
        lines.append("```lean")
        lines.append(excerpt)
        lines.append("```")

    if not lines:
        return ""
    return "\n" + "\n".join(lines) + "\n"
