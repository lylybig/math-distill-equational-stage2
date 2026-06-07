from __future__ import annotations

import argparse
from datetime import date
import json
import os
from pathlib import Path
import sys

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))

from math_distill_stage2.official_stage2_batch import (
    DEFAULT_REMOTE_JUDGE_V2_BASE_URLS,
    RemoteJudgeV2Config,
    make_remote_judge_v2_batch_judge,
    resolve_remote_judge_v2_base_urls,
    select_remote_judge_v2_base_url,
)
from math_distill_stage2.proof_bank.bank import check_bank, merge_run, preview_merge_run
from math_distill_stage2.proof_bank.external_olean_harvest import (
    DEFAULT_EQUATIONS_PATH,
    DEFAULT_STAGE2_ARTIFACTS,
    build_external_olean_harvest_run,
)
from math_distill_stage2.proof_bank.import_responses import import_responses


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a proofbank run from external compiled Submission.olean artifacts."
    )
    parser.add_argument("--bank", type=Path, default=Path("data/processed/proof_banks/gpt_true_certificates"))
    parser.add_argument("--run-root", type=Path, default=Path("artifacts/proof_bank_runs"))
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--artifacts-root", type=Path, default=DEFAULT_STAGE2_ARTIFACTS)
    parser.add_argument("--equations-path", type=Path, default=DEFAULT_EQUATIONS_PATH)
    parser.add_argument(
        "--candidate-pool",
        type=Path,
        default=None,
        help="Optional proofbank candidate pool used to prioritize external artifact lookup.",
    )
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--verify-remote-http", action="store_true")
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
    parser.add_argument("--merge", action="store_true", help="Merge the run into the bank after verification.")
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Omit per-item rows and raw response paths from stdout.",
    )
    args = parser.parse_args(argv)

    run_id = args.run_id or f"proofbank-{date.today():%Y%m%d}-external-olean-harvest"
    run_dir = args.run_root / f"{date.today():%Y-%m-%d}" / run_id
    result = build_external_olean_harvest_run(
        run_dir=run_dir,
        source_run_id=run_id,
        artifacts_root=args.artifacts_root,
        equations_path=args.equations_path,
        bank=args.bank,
        limit=args.limit,
        candidate_pool=args.candidate_pool,
        overwrite=args.overwrite,
    )

    if args.verify_remote_http:
        remote_judge_base_urls = resolve_remote_judge_v2_base_urls(
            base_url=args.remote_judge_base_url,
            base_urls=args.remote_judge_base_urls,
        )
        remote_judge_base_url = select_remote_judge_v2_base_url(
            remote_judge_base_urls,
            request_timeout_seconds=args.remote_judge_timeout_seconds,
        )
        result["import_summary"] = import_responses(
            run_dir,
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
        result["merge_preview"] = preview_merge_run(args.bank, run_dir)
        if args.merge:
            result["merge_summary"] = merge_run(args.bank, run_dir)
            result["bank_check"] = check_bank(args.bank)

    if args.summary_only:
        result = {
            key: value
            for key, value in result.items()
            if key not in {"prompt_items", "raw_response_paths"}
        }

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
