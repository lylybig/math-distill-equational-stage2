from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))

from math_distill_stage2.official_stage2_judge import (
    DEFAULT_STAGE2_JUDGE_REPO,
    build_official_stage2_judge_config,
    verify_official_stage2_answer,
)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify one Stage 2 problem/answer pair with the official judge/verify.py checker."
    )
    parser.add_argument("--problem", type=Path, required=True, help="Problem JSON file.")
    parser.add_argument(
        "--answer",
        type=Path,
        required=True,
        help="Answer JSON file. Accepts either {'verdict','code'} or {'call':'judge','verdict','code'}.",
    )
    parser.add_argument("--judge-repo", type=Path, default=DEFAULT_STAGE2_JUDGE_REPO)
    parser.add_argument("--artifact-dir", type=Path)
    parser.add_argument("--lean-bin", type=Path)
    parser.add_argument("--lake-bin", type=Path)
    parser.add_argument("--lean-timeout-seconds", type=int)
    parser.add_argument("--max-code-length", type=int)
    parser.add_argument("--max-false-cert-bytes", type=int)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    problem = json.loads(args.problem.read_text(encoding="utf-8"))
    answer = json.loads(args.answer.read_text(encoding="utf-8"))
    config = build_official_stage2_judge_config(
        judge_repo=args.judge_repo,
        lean_bin=args.lean_bin,
        lake_bin=args.lake_bin,
        artifact_dir=args.artifact_dir,
        lean_timeout_seconds=args.lean_timeout_seconds,
        max_code_length=args.max_code_length,
        max_false_cert_bytes=args.max_false_cert_bytes,
    )
    result = verify_official_stage2_answer(
        problem,
        answer,
        judge_repo=args.judge_repo,
        config=config,
    )
    print(json.dumps(result.raw, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.status == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
