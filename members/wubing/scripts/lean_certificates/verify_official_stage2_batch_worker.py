from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

if __package__ in (None, ""):
    workspace = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(workspace / "src"))

from math_distill_stage2.dataset_io import read_jsonl
from math_distill_stage2.official_stage2_batch import verify_official_stage2_records
from math_distill_stage2.official_stage2_judge import (
    DEFAULT_STAGE2_JUDGE_REPO,
    build_official_stage2_judge_config,
    verify_official_stage2_answer,
)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Container worker for Dockerized official Stage 2 batch verification."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--summary", type=Path)
    parser.add_argument(
        "--judge-repo",
        type=Path,
        default=Path(os.environ.get("OFFICIAL_STAGE2_JUDGE_REPO", str(DEFAULT_STAGE2_JUDGE_REPO))),
    )
    parser.add_argument("--max-workers", type=int, default=1)
    parser.add_argument("--lean-timeout-seconds", type=int)
    parser.add_argument("--max-code-length", type=int)
    parser.add_argument("--max-false-cert-bytes", type=int)
    parser.add_argument("--resume", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    config = build_official_stage2_judge_config(
        judge_repo=args.judge_repo,
        artifact_dir=args.artifact_dir,
        lean_timeout_seconds=args.lean_timeout_seconds,
        max_code_length=args.max_code_length,
        max_false_cert_bytes=args.max_false_cert_bytes,
    )

    def verify(problem, answer):
        return verify_official_stage2_answer(
            problem,
            answer,
            judge_repo=args.judge_repo,
            config=config,
        ).raw

    summary = verify_official_stage2_records(
        read_jsonl(args.input),
        output_path=args.output,
        summary_path=args.summary,
        verify_fn=verify,
        resume=args.resume,
        max_workers=args.max_workers,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
