from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))

from math_distill_stage2.proof_bank.prompt_pack import build_prompt_pack
from math_distill_stage2.proof_bank.etp_context import DEFAULT_ETP_IMPLICATIONS_PATH
from math_distill_stage2.proof_bank.skill_guidance import (
    DEFAULT_GENERATION_SKILL_PATH,
    DEFAULT_LEAN_PROOF_SKILL_PATH,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a Stage 2 proof bank prompt pack.")
    parser.add_argument("--bank", type=Path, required=True)
    parser.add_argument("--candidate-pool", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, default=Path("artifacts/proof_bank_runs"))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--prompt-policy", default="trace-if-available")
    parser.add_argument(
        "--etp-implications-path",
        type=Path,
        default=DEFAULT_ETP_IMPLICATIONS_PATH,
        help="Processed ETP implication JSONL used for blueprint/path hints.",
    )
    parser.add_argument(
        "--no-etp-context",
        action="store_true",
        help="Disable ETP/blueprint context injection.",
    )
    parser.add_argument(
        "--generation-skill-path",
        type=Path,
        default=DEFAULT_GENERATION_SKILL_PATH,
        help="Skill markdown used for general proof-generation guidance.",
    )
    parser.add_argument(
        "--lean-proof-skill-path",
        type=Path,
        default=DEFAULT_LEAN_PROOF_SKILL_PATH,
        help="Skill markdown used for repair-item Lean proof guidance.",
    )
    parser.add_argument(
        "--allow-existing-accepted",
        action="store_true",
        help="Allow prompt items for problems that already have accepted certificates.",
    )
    args = parser.parse_args(argv)
    summary = build_prompt_pack(
        bank=args.bank,
        candidate_pool=args.candidate_pool,
        run_root=args.run_root,
        source_run_id=args.run_id,
        limit=args.limit,
        prompt_policy=args.prompt_policy,
        allow_existing_accepted=args.allow_existing_accepted,
        etp_implications_path=None if args.no_etp_context else args.etp_implications_path,
        generation_skill_path=args.generation_skill_path,
        lean_proof_skill_path=args.lean_proof_skill_path,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
