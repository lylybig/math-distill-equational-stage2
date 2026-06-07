from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))

from math_distill_stage2.official_stage2_batch import DEFAULT_REMOTE_JUDGE_V2_BASE_URLS
from math_distill_stage2.official_stage2_judge import verify_official_stage2_answer
from math_distill_stage2.proof_bank.import_responses import import_responses


def official_judge(problem: dict, answer: dict) -> dict:
    result = verify_official_stage2_answer(problem, answer)
    return result.raw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import proof bank raw responses and verify with the official judge.")
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument(
        "--judge-backend",
        choices=("local", "remote-http", "remote-judge-v2"),
        default="local",
        help=(
            "Official judge backend. remote-http is an alias for remote-judge-v2 "
            "and uses the judge-v2 control service."
        ),
    )
    parser.add_argument(
        "--remote-judge-base-url",
        help="Single remote judge-v2 base URL; overrides --remote-judge-base-urls.",
    )
    parser.add_argument(
        "--remote-judge-base-urls",
        help=(
            "Comma-separated remote judge-v2 endpoint pool. Default: "
            f"{','.join(DEFAULT_REMOTE_JUDGE_V2_BASE_URLS)}."
        ),
    )
    parser.add_argument(
        "--remote-judge-max-workers",
        type=int,
        default=int(os.environ.get("STAGE2_REMOTE_JUDGE_MAX_WORKERS", "16")),
    )
    parser.add_argument("--remote-judge-timeout-seconds", type=int, default=20)
    parser.add_argument("--remote-judge-run-timeout-seconds", type=int, default=300)
    parser.add_argument("--remote-judge-poll-interval-seconds", type=float, default=2.0)
    args = parser.parse_args(argv)
    if args.judge_backend in {"remote-http", "remote-judge-v2"}:
        from math_distill_stage2.official_stage2_batch import (
            RemoteJudgeV2Config,
            make_remote_judge_v2_batch_judge,
            resolve_remote_judge_v2_base_urls,
            select_remote_judge_v2_base_url,
        )
        remote_judge_base_urls = resolve_remote_judge_v2_base_urls(
            base_url=args.remote_judge_base_url,
            base_urls=args.remote_judge_base_urls,
        )
        remote_judge_base_url = select_remote_judge_v2_base_url(
            remote_judge_base_urls,
            request_timeout_seconds=args.remote_judge_timeout_seconds,
        )

        summary = import_responses(
            args.run,
            batch_judge=make_remote_judge_v2_batch_judge(
                RemoteJudgeV2Config(
                    base_url=remote_judge_base_url,
                    max_workers=args.remote_judge_max_workers,
                    request_timeout_seconds=args.remote_judge_timeout_seconds,
                    run_timeout_seconds=args.remote_judge_run_timeout_seconds,
                    poll_interval_seconds=args.remote_judge_poll_interval_seconds,
                )
            ),
        )
    else:
        summary = import_responses(args.run, judge=official_judge)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
