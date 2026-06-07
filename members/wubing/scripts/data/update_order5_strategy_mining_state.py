#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from math_distill_stage2.order5_strategy_mining_state import (
    build_candidate_index,
    build_mining_state,
    default_codex_state_sqlite,
    default_registry_dir,
    write_json,
    write_jsonl,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build a lightweight order5 strategy mining state snapshot and candidate summary index."
        )
    )
    parser.add_argument("--registry-dir", type=Path, default=default_registry_dir())
    parser.add_argument("--candidate-summary-glob", default="*summary.json")
    parser.add_argument("--limit-candidates", type=int)
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument(
        "--codex-state-sqlite",
        type=Path,
        default=default_codex_state_sqlite(),
        help="Optional Codex app state DB used to list active goal sessions for this cwd.",
    )
    parser.add_argument("--no-codex-sessions", action="store_true")
    parser.add_argument(
        "--output-state-json",
        type=Path,
        help="Default: <registry-dir>/mining_state.json",
    )
    parser.add_argument(
        "--output-candidate-index-jsonl",
        type=Path,
        help="Default: <registry-dir>/candidate_index.jsonl",
    )
    parser.add_argument(
        "--output-candidate-summary-json",
        type=Path,
        help="Default: <registry-dir>/candidate_index_summary.json",
    )
    args = parser.parse_args()

    registry_dir = args.registry_dir
    candidates_dir = registry_dir / "candidates"
    output_state_json = args.output_state_json or registry_dir / "mining_state.json"
    output_candidate_index_jsonl = (
        args.output_candidate_index_jsonl or registry_dir / "candidate_index.jsonl"
    )
    output_candidate_summary_json = (
        args.output_candidate_summary_json or registry_dir / "candidate_index_summary.json"
    )

    rows, candidate_summary = build_candidate_index(
        candidates_dir=candidates_dir,
        summary_glob=args.candidate_summary_glob,
        limit=args.limit_candidates,
    )
    state = build_mining_state(
        registry_dir=registry_dir,
        candidate_index_summary=candidate_summary,
        codex_state_sqlite=None if args.no_codex_sessions else args.codex_state_sqlite,
        cwd=args.cwd.resolve(),
    )

    write_jsonl(output_candidate_index_jsonl, rows)
    write_json(output_candidate_summary_json, candidate_summary)
    write_json(output_state_json, state)

    print(
        json.dumps(
            {
                "state": str(output_state_json),
                "candidate_index": str(output_candidate_index_jsonl),
                "candidate_summary": str(output_candidate_summary_json),
                "summary_file_count": candidate_summary["summary_file_count"],
                "status_counts": candidate_summary["status_counts"],
                "active_goal_count": len(state["active_goal_sessions"]),
                "unresolved_estimate": state["baseline"]["coverage"].get(
                    "unresolved_estimate"
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

