#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))
    sys.path.insert(0, str(repo_root))

from math_distill_stage2.order5_residual_cluster_report import (  # noqa: E402
    DEFAULT_COVERAGE_SUMMARY_PATH,
    DEFAULT_FALSE_SHAPE_BUCKETS_PATH,
    DEFAULT_FIN3_SELECTOR_PROBE_PATH,
    DEFAULT_PREDICATE_BUCKET_PROBE_PATH,
    DEFAULT_SETCHECK_RANKING_PATH,
    DEFAULT_TOP1_FIN3_SELECTOR_PROBE_PATH,
    DEFAULT_TOP2_3_FIN3_SELECTOR_PROBE_PATH,
    DEFAULT_TOP3_SYNTHESIS_SUMMARY_PATH,
    DEFAULT_TRUE_FILTERED_SHAPE_BUCKETS_PATH,
    build_residual_cluster_report,
    write_residual_cluster_report,
)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Aggregate existing order5 residual samples and probes into an ROI "
            "cluster report. This does not scan the full pair space."
        )
    )
    parser.add_argument("--coverage-summary", type=Path, default=DEFAULT_COVERAGE_SUMMARY_PATH)
    parser.add_argument(
        "--false-shape-buckets", type=Path, default=DEFAULT_FALSE_SHAPE_BUCKETS_PATH
    )
    parser.add_argument(
        "--true-filtered-shape-buckets",
        type=Path,
        default=DEFAULT_TRUE_FILTERED_SHAPE_BUCKETS_PATH,
    )
    parser.add_argument(
        "--top3-synthesis-summary",
        type=Path,
        default=DEFAULT_TOP3_SYNTHESIS_SUMMARY_PATH,
    )
    parser.add_argument("--fin3-selector-probe", type=Path, default=DEFAULT_FIN3_SELECTOR_PROBE_PATH)
    parser.add_argument(
        "--top1-fin3-selector-probe",
        type=Path,
        default=DEFAULT_TOP1_FIN3_SELECTOR_PROBE_PATH,
    )
    parser.add_argument(
        "--top2-3-fin3-selector-probe",
        type=Path,
        default=DEFAULT_TOP2_3_FIN3_SELECTOR_PROBE_PATH,
    )
    parser.add_argument(
        "--predicate-bucket-probe", type=Path, default=DEFAULT_PREDICATE_BUCKET_PROBE_PATH
    )
    parser.add_argument("--setcheck-ranking", type=Path, default=DEFAULT_SETCHECK_RANKING_PATH)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--output-json", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = build_residual_cluster_report(
        coverage_summary_path=args.coverage_summary,
        false_shape_buckets_path=args.false_shape_buckets,
        true_filtered_shape_buckets_path=args.true_filtered_shape_buckets,
        top3_synthesis_summary_path=args.top3_synthesis_summary,
        fin3_selector_probe_path=args.fin3_selector_probe,
        top1_fin3_selector_probe_path=args.top1_fin3_selector_probe,
        top2_3_fin3_selector_probe_path=args.top2_3_fin3_selector_probe,
        predicate_bucket_probe_path=args.predicate_bucket_probe,
        setcheck_ranking_path=args.setcheck_ranking,
        top_k=args.top_k,
    )
    write_residual_cluster_report(args.output_json, report)
    print(args.output_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
