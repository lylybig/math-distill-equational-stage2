from __future__ import annotations

import argparse
from pathlib import Path
import sys

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))

from math_distill_stage2.official_stage2_batch import (
    DEFAULT_OFFICIAL_STAGE2_JUDGE_IMAGE,
    run_docker_official_stage2_batch,
)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify Stage 2 certificates in batch using the Dockerized official judge."
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Input JSONL records with problem plus answer or judge_call objects.",
    )
    parser.add_argument("--output", type=Path, required=True, help="Output official verification JSONL.")
    parser.add_argument("--artifact-dir", type=Path, required=True, help="Host directory for official judge artifacts.")
    parser.add_argument("--summary", type=Path, help="Optional summary JSON path.")
    parser.add_argument("--image", default=DEFAULT_OFFICIAL_STAGE2_JUDGE_IMAGE)
    parser.add_argument("--max-workers", type=int, default=2)
    parser.add_argument("--cpus", default="2")
    parser.add_argument("--memory", default="4g")
    parser.add_argument("--timeout-seconds", type=int)
    parser.add_argument("--lean-timeout-seconds", type=int)
    parser.add_argument("--max-code-length", type=int)
    parser.add_argument("--max-false-cert-bytes", type=int)
    parser.add_argument("--resume", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    result = run_docker_official_stage2_batch(
        input_path=args.input,
        output_path=args.output,
        artifact_dir=args.artifact_dir,
        image=args.image,
        max_workers=args.max_workers,
        cpu_limit=args.cpus,
        memory_limit=args.memory,
        timeout_seconds=args.timeout_seconds,
        lean_timeout_seconds=args.lean_timeout_seconds,
        max_code_length=args.max_code_length,
        max_false_cert_bytes=args.max_false_cert_bytes,
        resume=args.resume,
        summary_path=args.summary,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
