from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import sys
from typing import Any

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.official_stage2_batch import (
    DEFAULT_REMOTE_JUDGE_V2_BASE_URLS,
    RemoteJudgeV2Config,
    make_remote_judge_v2_batch_judge,
    resolve_remote_judge_v2_base_urls,
    select_remote_judge_v2_base_url,
)
from math_distill_stage2.official_stage2_judge import ensure_official_stage2_problem_defaults


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify order5 paircheck bank smoke records using remote judge-v2."
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Input JSONL records with problem and answer objects.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output JSONL with remote verification results.",
    )
    parser.add_argument("--summary", type=Path, help="Optional summary JSON path.")
    parser.add_argument(
        "--base-url",
        help=(
            "Single remote judge-v2 base URL. Overrides --base-urls and "
            "STAGE2_REMOTE_JUDGE_BASE_URLS."
        ),
    )
    parser.add_argument(
        "--base-urls",
        help=(
            "Comma-separated remote judge-v2 endpoint pool. Defaults to "
            + ",".join(DEFAULT_REMOTE_JUDGE_V2_BASE_URLS)
            + " unless STAGE2_REMOTE_JUDGE_BASE_URLS is set."
        ),
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=int(os.environ.get("STAGE2_REMOTE_JUDGE_MAX_WORKERS", "16")),
    )
    parser.add_argument("--request-timeout-seconds", type=int, default=20)
    parser.add_argument("--run-timeout-seconds", type=int, default=300)
    parser.add_argument("--poll-interval-seconds", type=float, default=2.0)
    return parser


def verify_order5_paircheck_remote_smoke(
    records: list[dict[str, Any]],
    *,
    input_path: Path | None = None,
    output_path: Path,
    summary_path: Path | None,
    config: RemoteJudgeV2Config,
    candidate_base_urls: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    requests = _requests_from_records(records)
    judge = make_remote_judge_v2_batch_judge(config)
    raw_results = judge(requests)
    if len(raw_results) != len(records):
        raise ValueError(
            f"remote judge-v2 returned {len(raw_results)} result(s) for {len(records)} input record(s)"
        )

    output_rows: list[dict[str, Any]] = []
    status_counts: Counter[str] = Counter()
    error_code_counts: Counter[str] = Counter()
    for record, raw_result in zip(records, raw_results, strict=True):
        status = str(raw_result.get("status") or "")
        error_code = str(raw_result.get("error_code") or "")
        status_counts[status] += 1
        error_code_counts[error_code] += 1
        output_rows.append(
            {
                **record,
                "status": status,
                "error_code": error_code,
                "remote_result": raw_result,
            }
        )

    write_jsonl(output_path, output_rows)
    summary = {
        "schema_version": 1,
        "input_path": str(input_path) if input_path is not None else None,
        "output_path": str(output_path),
        "total_count": len(output_rows),
        "accepted_count": status_counts.get("accepted", 0),
        "status_counts": dict(status_counts),
        "error_code_counts": dict(error_code_counts),
        "remote": {
            "backend": "judge-v2",
            "base_url": config.base_url,
            "candidate_base_urls": list(candidate_base_urls or (config.base_url,)),
            "max_workers": max(1, int(config.max_workers)),
            "request_timeout_seconds": config.request_timeout_seconds,
            "run_timeout_seconds": config.run_timeout_seconds,
            "poll_interval_seconds": config.poll_interval_seconds,
        },
    }
    if summary_path is not None:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    return summary


def _requests_from_records(
    records: list[dict[str, Any]],
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    requests: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for index, record in enumerate(records, start=1):
        problem = record.get("problem")
        answer = record.get("answer")
        if answer is None:
            answer = record.get("judge_call")
        if not isinstance(problem, dict):
            raise ValueError(f"record {index} is missing problem object")
        if not isinstance(answer, dict):
            raise ValueError(f"record {index} is missing answer/judge_call object")
        requests.append((ensure_official_stage2_problem_defaults(problem), answer))
    return requests


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    candidate_base_urls = resolve_remote_judge_v2_base_urls(
        base_url=args.base_url,
        base_urls=args.base_urls,
    )
    selected_base_url = select_remote_judge_v2_base_url(
        candidate_base_urls,
        request_timeout_seconds=args.request_timeout_seconds,
    )
    config = RemoteJudgeV2Config(
        base_url=selected_base_url,
        max_workers=args.max_workers,
        request_timeout_seconds=args.request_timeout_seconds,
        run_timeout_seconds=args.run_timeout_seconds,
        poll_interval_seconds=args.poll_interval_seconds,
    )
    summary = verify_order5_paircheck_remote_smoke(
        read_jsonl(args.input),
        input_path=args.input,
        output_path=args.output,
        summary_path=args.summary,
        config=config,
        candidate_base_urls=candidate_base_urls,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["accepted_count"] == summary["total_count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
