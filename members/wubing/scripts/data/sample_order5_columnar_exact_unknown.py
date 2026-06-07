#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))
    sys.path.insert(0, str(repo_root))

from math_distill_stage2.dataset_io import write_jsonl  # noqa: E402
from math_distill_stage2.order5_columnar_graph_store import (  # noqa: E402
    DEFAULT_STORE_DIR,
    ColumnarImplicationStore,
)
from math_distill_stage2.order5_paircheck_bank import load_equation_texts  # noqa: E402
from math_distill_stage2.order5_residual_shape_sample import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
    _annotate_pair,
    _parse_needed_equations,
    summarize_shape_buckets,
    summarize_single_side_buckets,
)
from math_distill_stage2.order5_spine_smoke import (  # noqa: E402
    DEFAULT_EQ_SIZE5_PATH,
    DEFAULT_ORDER4_MAX_ID,
)


DEFAULT_OUTPUT_STEM = "current_residual_columnar_exact_unknown_1000_seed20260529"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Sample reproducible exact-unknown order5 pairs from the local "
            "columnar implication graph store."
        )
    )
    parser.add_argument("--store-dir", type=Path, default=DEFAULT_STORE_DIR)
    parser.add_argument("--equations-file", type=Path, default=DEFAULT_EQ_SIZE5_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--output-stem", default=DEFAULT_OUTPUT_STEM)
    parser.add_argument("--sample-size", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260529)
    parser.add_argument("--order4-max-id", type=int, default=DEFAULT_ORDER4_MAX_ID)
    parser.add_argument("--max-draws", type=int)
    parser.add_argument("--top-k", type=int, default=50)
    parser.add_argument(
        "--skip-layer-counts",
        action="store_true",
        help="Skip exact layer bit counts in the summary for a faster run.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite output files if they already exist.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if args.sample_size <= 0:
        raise SystemExit("--sample-size must be positive")
    if args.top_k <= 0:
        raise SystemExit("--top-k must be positive")

    output_paths = {
        "sample_jsonl": args.output_dir / f"{args.output_stem}_sample.jsonl",
        "buckets_json": args.output_dir / f"{args.output_stem}_buckets.json",
        "summary_json": args.output_dir / f"{args.output_stem}_summary.json",
    }
    if not args.force:
        existing = [str(path) for path in output_paths.values() if path.exists()]
        if existing:
            raise SystemExit(
                "refusing to overwrite existing output; pass --force or choose "
                f"a new --output-stem: {existing}"
            )

    started_at = time.perf_counter()
    store = ColumnarImplicationStore.open(args.store_dir)
    if "true" not in store.layers or "false" not in store.layers:
        raise SystemExit("store must contain exact true and false layers")

    layer_counts = None
    exact_unknown_count = None
    if not args.skip_layer_counts:
        layer_counts = {
            "true": store.layer_count("true"),
            "false": store.layer_count("false"),
        }
        if "conflict" in store.layers:
            layer_counts["conflict"] = store.layer_count("conflict")
        else:
            layer_counts["conflict"] = 0
        exact_unknown_count = (
            store.pair_count
            - layer_counts["true"]
            - layer_counts["false"]
            + layer_counts["conflict"]
        )

    raw_rows, sampling_counts = _sample_exact_unknown_rows(
        store,
        sample_size=args.sample_size,
        seed=args.seed,
        order4_max_id=args.order4_max_id,
        max_draws=args.max_draws,
    )
    equation_texts = load_equation_texts(args.equations_file)
    equations = _parse_needed_equations(raw_rows, equation_texts)
    annotated_rows = []
    stratum_counts: Counter[str] = Counter()
    for index, row in enumerate(raw_rows, start=1):
        eq1_id = int(row["eq1_id"])
        eq2_id = int(row["eq2_id"])
        annotated = {
            "sample_id": f"{args.output_stem}-{index:04d}",
            "problem_id": f"{eq1_id}_{eq2_id}",
            "equation1": equation_texts[eq1_id],
            "equation2": equation_texts[eq2_id],
            "answer": None,
            "sampling_scope": "columnar_exact_unknown_true_false_layers",
            **_annotate_pair(row, equations=equations),
        }
        annotated_rows.append(annotated)
        stratum_counts[str(annotated["stratum"])] += 1

    projection_base = exact_unknown_count or 0
    buckets = {
        "schema_version": 1,
        "kind": "order5_columnar_exact_unknown_shape_buckets",
        "sampling_scope": "columnar_exact_unknown_true_false_layers",
        "sample_count": len(annotated_rows),
        "seed": args.seed,
        "projection_base": exact_unknown_count,
        "notes": [
            "Rows are sampled uniformly from exact unknown directed non-self pair indexes by rejection sampling.",
            "residual_estimate_if_uniform is sampling guidance, not union increment or soundness evidence.",
        ],
        "top_pair_buckets": summarize_shape_buckets(
            annotated_rows,
            projection_base=projection_base,
            top_k=args.top_k,
        ),
        "top_source_buckets": summarize_single_side_buckets(
            annotated_rows,
            side="source_shape",
            projection_base=projection_base,
            top_k=args.top_k,
        ),
        "top_target_buckets": summarize_single_side_buckets(
            annotated_rows,
            side="target_shape",
            projection_base=projection_base,
            top_k=args.top_k,
        ),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_paths["sample_jsonl"], annotated_rows)
    _write_json(output_paths["buckets_json"], buckets)

    summary = {
        "schema_version": 1,
        "kind": "order5_columnar_exact_unknown_sample",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": args.seed,
        "sample_size": args.sample_size,
        "selected_count": len(annotated_rows),
        "sampling_scope": "columnar_exact_unknown_true_false_layers",
        "sampling_algorithm": [
            "Use random.Random(seed).randrange(pair_count) over directed non-self pair indexes.",
            "Reject duplicate draws.",
            "Reject pairs set in the exact true or exact false bitset layers.",
            "Materialize the first sample_size unique exact-unknown pairs.",
        ],
        "store_dir": str(args.store_dir),
        "store_manifest": _compact_store_manifest(store.manifest),
        "layer_counts": layer_counts,
        "exact_unknown_count": exact_unknown_count,
        "order4_max_id": args.order4_max_id,
        "counts": sampling_counts,
        "selected_by_stratum": dict(stratum_counts),
        "top_pair_buckets": buckets["top_pair_buckets"][:10],
        "paths": {key: str(path) for key, path in output_paths.items()},
        "sample_jsonl_sha256": _sha256_file(output_paths["sample_jsonl"]),
        "buckets_json_sha256": _sha256_file(output_paths["buckets_json"]),
        "elapsed_seconds": round(time.perf_counter() - started_at, 3),
    }
    _write_json(output_paths["summary_json"], summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _sample_exact_unknown_rows(
    store: ColumnarImplicationStore,
    *,
    sample_size: int,
    seed: int,
    order4_max_id: int,
    max_draws: int | None,
) -> tuple[list[dict[str, Any]], dict[str, int | float]]:
    rng = random.Random(seed)
    draw_limit = max_draws or max(sample_size * 1000, 100_000)
    rows: list[dict[str, Any]] = []
    selected_pair_indexes: set[int] = set()
    seen_drawn_pair_indexes: set[int] = set()
    counts: Counter[str] = Counter()

    with store.layer("true").open() as true_layer, store.layer("false").open() as false_layer:
        while len(rows) < sample_size and counts["random_candidate_draws"] < draw_limit:
            counts["random_candidate_draws"] += 1
            pair_index = rng.randrange(store.pair_count)
            if pair_index in seen_drawn_pair_indexes:
                counts["duplicate_random_pair_draws"] += 1
                continue
            seen_drawn_pair_indexes.add(pair_index)

            if true_layer.get(pair_index):
                counts["covered_by_exact_true"] += 1
                continue
            if false_layer.get(pair_index):
                counts["covered_by_exact_false"] += 1
                continue
            if pair_index in selected_pair_indexes:
                counts["duplicate_selected_pair_draws"] += 1
                continue

            eq1_id, eq2_id = store.pair_index_to_ids(pair_index)
            selected_pair_indexes.add(pair_index)
            rows.append(
                {
                    "pair_index": pair_index,
                    "eq1_id": eq1_id,
                    "eq2_id": eq2_id,
                    "stratum": _pair_stratum(eq1_id, eq2_id, order4_max_id=order4_max_id),
                }
            )

    if len(rows) != sample_size:
        raise SystemExit(
            f"only selected {len(rows)} rows after "
            f"{counts['random_candidate_draws']} random draws"
        )

    draws = int(counts["random_candidate_draws"])
    return rows, {
        **dict(counts),
        "selected_exact_unknown": len(rows),
        "unique_random_pair_draws": len(seen_drawn_pair_indexes),
        "draw_acceptance_rate": len(rows) / draws if draws else 0.0,
    }


def _pair_stratum(eq1_id: int, eq2_id: int, *, order4_max_id: int) -> str:
    source_order5 = eq1_id > order4_max_id
    target_order5 = eq2_id > order4_max_id
    if source_order5 and target_order5:
        return "order5_source_to_order5_target"
    if source_order5:
        return "order5_source_to_order4_target"
    if target_order5:
        return "order4_source_to_order5_target"
    return "order4_source_to_order4_target"


def _compact_store_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "kind",
        "schema_version",
        "equations_path",
        "equations_sha256",
        "law_count",
        "include_self",
        "pair_count",
        "pair_index_base",
        "eq_id_base",
    ]
    return {key: manifest[key] for key in keys if key in manifest}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
