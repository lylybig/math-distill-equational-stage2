from __future__ import annotations

import json
from itertools import product
from pathlib import Path
from typing import Any, Iterable

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.equations import parse_equation
from math_distill_stage2.proof_bank.keying import (
    canonical_signature_for_bank,
    problem_key_from_equations,
)
from math_distill_stage2.proof_bank.storage import write_json


DEFAULT_EQUATIONS_PATH = Path(
    "external/equational-theories-lean-stage2/examples/problems/eq_size5.txt"
)
DEFAULT_SOURCE_SEED_CANDIDATES_PATH = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_candidates_20260518_topshape_true_templates.jsonl"
)
DEFAULT_EQ2_ID = 2


def binary_grind_singleton_proof_body(variable_count: int) -> str:
    if variable_count <= 0:
        raise ValueError("variable_count must be positive")
    lines = ["intro x y"]
    for index, assignment in enumerate(product(("x", "y"), repeat=variable_count)):
        args = " ".join(f"({value})" for value in assignment)
        lines.append(f"have h{index} := h {args}")
    lines.append("grind")
    return "\n".join(lines)


def build_singleton_seedgate_run(
    *,
    run_dir: Path,
    source_seed_candidates_path: Path = DEFAULT_SOURCE_SEED_CANDIDATES_PATH,
    equations_path: Path = DEFAULT_EQUATIONS_PATH,
    eq2_id: int = DEFAULT_EQ2_ID,
    limit: int = 12,
    bank_attempts_path: Path | None = None,
    previous_run_dirs: Iterable[Path] = (),
    source_run_id: str | None = None,
) -> dict[str, Any]:
    if limit <= 0:
        raise ValueError("limit must be positive")

    equations = _load_equations(equations_path)
    if eq2_id not in equations:
        raise ValueError(f"eq2_id {eq2_id} not found in {equations_path}")
    target_equation = equations[eq2_id]

    attempted_problem_keys = _attempted_problem_keys(
        bank_attempts_path=bank_attempts_path,
        previous_run_dirs=previous_run_dirs,
    )
    source_ids = _load_source_seed_ids(source_seed_candidates_path)
    selected: list[dict[str, Any]] = []
    skipped_attempted = 0
    skipped_missing = 0
    for source_id in source_ids:
        source_equation = equations.get(source_id)
        if source_equation is None:
            skipped_missing += 1
            continue
        problem_key = problem_key_from_equations(source_equation, target_equation)
        if problem_key in attempted_problem_keys:
            skipped_attempted += 1
            continue
        parsed = parse_equation(source_equation)
        variables = parsed.variables()
        item_id = f"{len(selected) + 1:06d}"
        selected.append(
            {
                "eq1_id": source_id,
                "eq1_signature": canonical_signature_for_bank(source_equation),
                "eq2_id": eq2_id,
                "eq2_signature": canonical_signature_for_bank(target_equation),
                "equation1": source_equation.replace("*", "◇"),
                "equation2": target_equation.replace("*", "◇"),
                "expected_verdict": True,
                "item_id": item_id,
                "notes": (
                    "Deterministic binary-grind singleton seedgate candidate from "
                    "order5 residual true-template source_seed_ids."
                ),
                "problem_key": problem_key,
                "prompt_skill_guidance": [
                    {
                        "name": "stage2-proofbank-generate-true-certificate",
                        "path": "skills/stage2-proofbank-generate-true-certificate/SKILL.md",
                        "source_role": "generation",
                    }
                ],
                "schema_version": 1,
                "source_candidate_pool": str(source_seed_candidates_path),
                "source_candidate_stratum": "order5_topshape_seedgate_phase2_source_to_equation2",
                "source_dataset": "order5_strategy_registry_topshape_residual",
                "source_problem_id": f"topshape_seedgate_phase2_source_{source_id}_to_eq{eq2_id}",
                "variable_count": len(variables),
                "variables": variables,
            }
        )
        if len(selected) >= limit:
            break

    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "raw_responses").mkdir(parents=True, exist_ok=True)
    write_jsonl(run_dir / "input_problems.jsonl", selected)
    for row in selected:
        proof = binary_grind_singleton_proof_body(int(row["variable_count"]))
        raw_payload = {"verdict": "true", "proof": proof}
        (run_dir / "raw_responses" / f"{row['item_id']}.txt").write_text(
            json.dumps(raw_payload, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )

    run_id = source_run_id or run_dir.name
    manifest = {
        "bank": "data/processed/proof_banks/gpt_true_certificates",
        "candidate_pool": str(source_seed_candidates_path),
        "created_at_utc": "2026-05-18T00:00:00Z",
        "eq2_id": eq2_id,
        "generator": {
            "mode": "deterministic_binary_grind_singleton_seed_gate",
            "model": None,
        },
        "problem_count": len(selected),
        "schema_version": 1,
        "skill_guidance": [
            {
                "name": "stage2-proofbank-generate-true-certificate",
                "path": "skills/stage2-proofbank-generate-true-certificate/SKILL.md",
                "source_role": "generation",
            }
        ],
        "source_run_id": run_id,
    }
    write_json(run_dir / "manifest.json", manifest)

    summary = {
        "candidate_source_count": len(source_ids),
        "eq2_id": eq2_id,
        "limit": limit,
        "problem_count": len(selected),
        "run_dir": str(run_dir),
        "schema_version": 1,
        "selected_source_ids": [row["eq1_id"] for row in selected],
        "skipped_already_attempted": skipped_attempted,
        "skipped_missing_equation": skipped_missing,
        "source_run_id": run_id,
    }
    write_json(run_dir / "selection_summary.json", summary)
    return summary


def _load_equations(path: Path) -> dict[int, str]:
    return {
        index: line.strip()
        for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if line.strip()
    }


def _load_source_seed_ids(path: Path) -> list[int]:
    source_ids: list[int] = []
    seen: set[int] = set()
    for row in read_jsonl(path):
        raw_ids: Any
        if "source_seed_ids" in row:
            raw_ids = row["source_seed_ids"]
        elif "source_ids_top_priority" in row:
            raw_ids = row["source_ids_top_priority"]
        elif "source_ids" in row:
            raw_ids = row["source_ids"]
        elif "eq1_id" in row:
            raw_ids = [row["eq1_id"]]
        else:
            continue
        for raw_id in raw_ids:
            source_id = int(raw_id)
            if source_id not in seen:
                seen.add(source_id)
                source_ids.append(source_id)
    return source_ids


def _attempted_problem_keys(
    *,
    bank_attempts_path: Path | None,
    previous_run_dirs: Iterable[Path],
) -> set[str]:
    keys: set[str] = set()
    if bank_attempts_path is not None and bank_attempts_path.exists():
        for row in read_jsonl(bank_attempts_path):
            problem_key = row.get("problem_key")
            if problem_key:
                keys.add(str(problem_key))
    for run_dir in previous_run_dirs:
        input_path = run_dir / "input_problems.jsonl"
        if not input_path.exists():
            continue
        for row in read_jsonl(input_path):
            problem_key = row.get("problem_key")
            if problem_key:
                keys.add(str(problem_key))
    return keys
