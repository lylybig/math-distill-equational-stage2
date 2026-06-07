from __future__ import annotations

import argparse
import json
import textwrap
from datetime import datetime, timezone
from pathlib import Path

from math_distill_stage2 import order5_strategy_registry as registry
from math_distill_stage2.proof_bank.keying import problem_key_from_signatures


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Create deterministic proof-bank raw responses for singleton-collapse "
            "sources, targeting Equation2 (x = y)."
        )
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=Path("artifacts/proof_bank_runs/2026-05-14"),
    )
    parser.add_argument(
        "--bank",
        type=Path,
        default=Path("data/processed/proof_banks/gpt_true_certificates"),
    )
    parser.add_argument(
        "--equations",
        type=Path,
        default=registry.DEFAULT_EQ_SIZE5_PATH,
    )
    parser.add_argument("--target-id", type=int, default=2)
    parser.add_argument(
        "--exclude-run-id",
        action="append",
        default=[],
        help=(
            "Also exclude eq1_ids present in this run's input_problems.jsonl. "
            "May be supplied more than once."
        ),
    )
    parser.add_argument(
        "--exclude-source-id",
        action="append",
        default=[],
        type=int,
        help="Also exclude this eq1_id. May be supplied more than once.",
    )
    args = parser.parse_args()

    if args.limit <= 0:
        raise ValueError("--limit must be positive")

    run_dir = args.runs_root / args.run_id
    if run_dir.exists():
        raise FileExistsError(f"run directory already exists: {run_dir}")
    raw_dir = run_dir / "raw_responses"
    raw_dir.mkdir(parents=True)

    selected, candidate_count = _select_candidates(
        equations_path=args.equations,
        bank_path=args.bank,
        runs_root=args.runs_root,
        exclude_run_ids=args.exclude_run_id,
        exclude_source_ids=set(args.exclude_source_id),
        limit=args.limit,
    )
    if not selected:
        raise RuntimeError("no singleton-collapse candidates selected")

    features = list(registry._cached_parsed_equation_features(args.equations))
    features_by_id = {
        feature.equation_id: (feature, equation) for feature, equation in features
    }
    target_feature, target_equation = features_by_id[args.target_id]
    target_signature = registry._canonical_signature_from_equation(target_equation)

    input_path = run_dir / "input_problems.jsonl"
    with input_path.open("w", encoding="utf-8") as out:
        for index, source_id in enumerate(selected, start=1):
            feature, equation = features_by_id[source_id]
            source_signature = registry._canonical_signature_from_equation(equation)
            problem = {
                "schema_version": 1,
                "item_id": f"{index:06d}",
                "problem_key": problem_key_from_signatures(
                    source_signature,
                    target_signature,
                ),
                "source_problem_id": f"singleton_collapse_seed_{source_id}_{args.target_id}",
                "source_dataset": (
                    "order5_strategy_registry.singleton_collapse_unseeded"
                ),
                "source_candidate_stratum": (
                    "singleton_collapse_order5_remaining_to_equation2_fixed_dedent"
                ),
                "eq1_id": source_id,
                "eq2_id": args.target_id,
                "eq1_signature": source_signature,
                "eq2_signature": target_signature,
                "equation1": feature.equation,
                "equation2": target_feature.equation,
                "expected_verdict": True,
            }
            out.write(json.dumps(problem, ensure_ascii=False, sort_keys=True) + "\n")

            proof = _source_level_proof_body(feature.equation, target_feature.equation)
            (raw_dir / f"{index:06d}.txt").write_text(
                json.dumps(
                    {"verdict": "true", "proof": proof},
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                + "\n",
                encoding="utf-8",
            )

    manifest = {
        "schema_version": 1,
        "source_run_id": args.run_id,
        "created_at_utc": datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        "run_dir": str(run_dir),
        "bank": str(args.bank),
        "problem_count": len(selected),
        "generator": {
            "mode": "deterministic_singleton_collapse_to_equation2_fixed_dedent",
            "model": None,
        },
        "candidate_selection": {
            "source": (
                "remaining order5 singleton_collapse sources outside current "
                "singleton_seedbank and accepted harvestable proofbank"
            ),
            "candidate_count_before_limit": candidate_count,
            "limit": args.limit,
            "selected_first": selected[:10],
            "selected_last": selected[-10:],
        },
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "run_id": args.run_id,
                "run_dir": str(run_dir),
                "problem_count": len(selected),
                "candidate_count_before_limit": candidate_count,
                "selected_first": selected[:10],
                "selected_last": selected[-10:],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _select_candidates(
    *,
    equations_path: Path,
    bank_path: Path,
    runs_root: Path,
    exclude_run_ids: list[str],
    exclude_source_ids: set[int],
    limit: int,
) -> tuple[list[int], int]:
    features = list(registry._cached_parsed_equation_features(equations_path))
    feature_ids = {feature.equation_id for feature, _equation in features}
    _signatures, singleton_sources, _targets, _counts = registry._singleton_collapse_sets(
        equations_path
    )
    _seed_signatures, seed_sources, _seed_targets, _mismatches = (
        registry._singleton_seedbank_sets(equations_path)
    )
    excluded = (
        set(seed_sources)
        | _accepted_harvestable_source_ids(bank_path)
        | _run_source_ids(runs_root, exclude_run_ids)
        | exclude_source_ids
    )
    candidates = sorted(
        source_id
        for source_id in singleton_sources
        if source_id > registry.DEFAULT_ORDER4_MAX_ID
        and source_id not in excluded
        and source_id in feature_ids
    )
    return candidates[:limit], len(candidates)


def _run_source_ids(runs_root: Path, run_ids: list[str]) -> set[int]:
    source_ids: set[int] = set()
    for run_id in run_ids:
        input_path = runs_root / run_id / "input_problems.jsonl"
        if not input_path.exists():
            raise FileNotFoundError(f"exclude run input not found: {input_path}")
        for row in _read_jsonl_records(input_path):
            source_id = row.get("eq1_id")
            if isinstance(source_id, int):
                source_ids.add(source_id)
    return source_ids


def _accepted_harvestable_source_ids(bank_path: Path) -> set[int]:
    attempts_path = bank_path / "attempts.jsonl"
    problems_path = bank_path / "problems.jsonl"
    accepted_path = bank_path / "accepted.jsonl"
    if (
        not attempts_path.exists()
        or not problems_path.exists()
        or not accepted_path.exists()
    ):
        return set()

    problems = {
        row["problem_key"]: row
        for row in _read_jsonl_records(problems_path)
        if "problem_key" in row
    }
    accepted_attempt_ids = {
        str(row["attempt_id"])
        for row in _read_jsonl_records(accepted_path)
        if "attempt_id" in row
    }

    source_ids: set[int] = set()
    for attempt in _read_jsonl_records(attempts_path):
        if str(attempt.get("attempt_id")) not in accepted_attempt_ids:
            continue
        if attempt.get("official_judge_status") != "accepted":
            continue
        problem = problems.get(str(attempt.get("problem_key")))
        if problem is None:
            continue
        proof_sha = attempt.get("proof_body_sha256")
        if not isinstance(proof_sha, str) or not proof_sha:
            continue
        proof_path = bank_path / "proof_bodies" / proof_sha[:2] / f"{proof_sha}.lean"
        if not proof_path.exists():
            continue
        try:
            registry._singleton_prefix_from_source_level_proof_body(
                proof_path.read_text(encoding="utf-8")
            )
        except ValueError:
            continue
        source_id = problem.get("eq1_id")
        if isinstance(source_id, int):
            source_ids.add(source_id)
    return source_ids


def _source_level_proof_body(source_equation: str, target_equation: str) -> str:
    code = registry.singleton_collapse_true_judge_code(source_equation, target_equation)
    prefix = "import JudgeProblem\n\ndef submission : Goal := by\n  intro G _ h\n"
    if not code.startswith(prefix):
        raise RuntimeError("unexpected singleton-collapse certificate prefix")
    return textwrap.dedent(code[len(prefix) :])


def _read_jsonl_records(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


if __name__ == "__main__":
    main()
