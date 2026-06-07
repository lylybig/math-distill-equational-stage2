#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from math_distill_stage2.order5_strategy_mining_state import (
    build_merge_review_queue,
    default_registry_dir,
    read_json,
    read_jsonl,
    render_merge_review_markdown,
    write_json,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build an order5 strategy candidate merge-review queue."
    )
    parser.add_argument("--registry-dir", type=Path, default=default_registry_dir())
    parser.add_argument(
        "--candidate-index-jsonl",
        type=Path,
        help="Default: <registry-dir>/candidate_index.jsonl",
    )
    parser.add_argument(
        "--mining-state-json",
        type=Path,
        help="Default: <registry-dir>/mining_state.json",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        help="Default: <registry-dir>/merge_review_queue.json",
    )
    parser.add_argument(
        "--output-markdown",
        type=Path,
        help="Default: docs/experiments/YYYY-MM-DD-order5-strategy-merge-review-queue.md",
    )
    parser.add_argument("--main-gate", type=int, default=1_000_000)
    parser.add_argument("--tail-gate", type=int, default=100_000)
    args = parser.parse_args()

    registry_dir = args.registry_dir
    candidate_index_jsonl = args.candidate_index_jsonl or registry_dir / "candidate_index.jsonl"
    mining_state_json = args.mining_state_json or registry_dir / "mining_state.json"
    output_json = args.output_json or registry_dir / "merge_review_queue.json"
    output_markdown = args.output_markdown or Path(
        "docs/experiments"
    ) / f"{datetime.now().date()}-order5-strategy-merge-review-queue.md"

    queue = build_merge_review_queue(
        rows=read_jsonl(candidate_index_jsonl),
        mining_state=read_json(mining_state_json),
        main_gate=args.main_gate,
        tail_gate=args.tail_gate,
    )
    write_json(output_json, queue)
    output_markdown.parent.mkdir(parents=True, exist_ok=True)
    output_markdown.write_text(render_merge_review_markdown(queue), encoding="utf-8")

    print(
        json.dumps(
            {
                "output_json": str(output_json),
                "output_markdown": str(output_markdown),
                "queue_counts": queue["queue_counts"],
                "unresolved_estimate": queue["baseline"].get("unresolved_estimate"),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

