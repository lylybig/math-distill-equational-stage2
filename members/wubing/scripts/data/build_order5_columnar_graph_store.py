#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))
    sys.path.insert(0, str(repo_root))

from math_distill_stage2.order5_columnar_graph_store import (  # noqa: E402
    DEFAULT_LAYERS,
    DEFAULT_STORE_DIR,
    ColumnarImplicationStore,
    finite_model_equation_partition,
)
from math_distill_stage2.order5_pair_space import DEFAULT_EQUATIONS_PATH  # noqa: E402


DEFAULT_STRATEGIES_JSON = Path("data/processed/order5_strategy_registry/strategies.json")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build and query the local mmap-backed order<=5 columnar implication store."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize an empty bitset store.")
    init_parser.add_argument("--store-dir", type=Path, default=DEFAULT_STORE_DIR)
    init_parser.add_argument("--equations-file", type=Path, default=DEFAULT_EQUATIONS_PATH)
    init_parser.add_argument("--law-count", type=int)
    init_parser.add_argument("--include-self", action="store_true")
    init_parser.add_argument(
        "--layers",
        default=",".join(DEFAULT_LAYERS),
        help="Comma-separated bitset layer names.",
    )
    init_parser.add_argument("--force", action="store_true")

    import_parser = subparsers.add_parser(
        "import-pair-indexes",
        help="Import a text or JSONL pair_index cache into one bitset layer.",
    )
    import_parser.add_argument("--store-dir", type=Path, default=DEFAULT_STORE_DIR)
    import_parser.add_argument("--input", type=Path, required=True)
    import_parser.add_argument("--layer", required=True)
    import_parser.add_argument("--source-id", required=True)
    import_parser.add_argument("--source-kind", default="pair_index_cache")
    import_parser.add_argument("--write-pair-evidence", action="store_true")
    import_parser.add_argument("--no-conflicts", action="store_true")

    finmodel_preview_parser = subparsers.add_parser(
        "preview-finmodel-strategy-row",
        help="Preview a false finite-model source-target strategy from strategies.json.",
    )
    finmodel_preview_parser.add_argument("--store-dir", type=Path, default=DEFAULT_STORE_DIR)
    finmodel_preview_parser.add_argument("--strategies-json", type=Path, default=DEFAULT_STRATEGIES_JSON)
    finmodel_preview_parser.add_argument("--strategy-id", required=True)
    finmodel_preview_parser.add_argument("--equations-file", type=Path, default=DEFAULT_EQUATIONS_PATH)
    finmodel_preview_parser.add_argument("--top-n", type=int, default=10)

    finmodel_import_parser = subparsers.add_parser(
        "import-finmodel-strategy-row",
        help="Import a false finite-model source-target strategy from strategies.json.",
    )
    finmodel_import_parser.add_argument("--store-dir", type=Path, default=DEFAULT_STORE_DIR)
    finmodel_import_parser.add_argument("--strategies-json", type=Path, default=DEFAULT_STRATEGIES_JSON)
    finmodel_import_parser.add_argument("--strategy-id", required=True)
    finmodel_import_parser.add_argument("--equations-file", type=Path, default=DEFAULT_EQUATIONS_PATH)
    finmodel_import_parser.add_argument("--no-conflicts", action="store_true")

    preview_pair_parser = subparsers.add_parser(
        "preview-pair-indexes",
        help="Preview novelty/conflicts for a pair_index cache before importing it.",
    )
    preview_pair_parser.add_argument("--store-dir", type=Path, default=DEFAULT_STORE_DIR)
    preview_pair_parser.add_argument("--input", type=Path, required=True)
    preview_pair_parser.add_argument("--layer", required=True)
    preview_pair_parser.add_argument("--top-n", type=int, default=10)

    pair_row_preview_parser = subparsers.add_parser(
        "preview-pair-index-strategy-row",
        help="Preview a pair-index-backed strategy row from strategies.json.",
    )
    pair_row_preview_parser.add_argument("--store-dir", type=Path, default=DEFAULT_STORE_DIR)
    pair_row_preview_parser.add_argument("--strategies-json", type=Path, default=DEFAULT_STRATEGIES_JSON)
    pair_row_preview_parser.add_argument("--strategy-id", required=True)
    pair_row_preview_parser.add_argument("--top-n", type=int, default=10)

    pair_row_import_parser = subparsers.add_parser(
        "import-pair-index-strategy-row",
        help="Import a pair-index-backed strategy row from strategies.json.",
    )
    pair_row_import_parser.add_argument("--store-dir", type=Path, default=DEFAULT_STORE_DIR)
    pair_row_import_parser.add_argument("--strategies-json", type=Path, default=DEFAULT_STRATEGIES_JSON)
    pair_row_import_parser.add_argument("--strategy-id", required=True)
    pair_row_import_parser.add_argument("--no-conflicts", action="store_true")
    pair_row_import_parser.add_argument("--write-pair-evidence", action="store_true")

    status_parser = subparsers.add_parser("status", help="Query one directed pair.")
    status_parser.add_argument("--store-dir", type=Path, default=DEFAULT_STORE_DIR)
    status_identity = status_parser.add_mutually_exclusive_group(required=True)
    status_identity.add_argument("--pair-index", type=int)
    status_identity.add_argument("--eq-pair", nargs=2, type=int, metavar=("EQ1_ID", "EQ2_ID"))
    status_parser.add_argument(
        "--layers",
        help="Optional comma-separated layer subset; defaults to all manifest layers.",
    )

    row_parser = subparsers.add_parser("row", help="List target ids set in one source row.")
    row_parser.add_argument("--store-dir", type=Path, default=DEFAULT_STORE_DIR)
    row_parser.add_argument("--layer", required=True)
    row_parser.add_argument("--source-id", type=int, required=True)
    row_parser.add_argument("--limit", type=int)

    row_summary_parser = subparsers.add_parser(
        "row-summary",
        help="Count true/false/approx/unknown facts for one source row.",
    )
    row_summary_parser.add_argument("--store-dir", type=Path, default=DEFAULT_STORE_DIR)
    row_summary_parser.add_argument("--source-id", type=int, required=True)
    row_summary_parser.add_argument("--layers")

    frontier_parser = subparsers.add_parser(
        "frontier",
        help="List unknown target candidates for one source row.",
    )
    frontier_parser.add_argument("--store-dir", type=Path, default=DEFAULT_STORE_DIR)
    frontier_parser.add_argument("--source-id", type=int, required=True)
    frontier_parser.add_argument("--known-layers", default="true,false")
    frontier_parser.add_argument("--limit", type=int, default=20)

    summary_parser = subparsers.add_parser("summary", help="Print manifest and optional counts.")
    summary_parser.add_argument("--store-dir", type=Path, default=DEFAULT_STORE_DIR)
    summary_parser.add_argument("--count-bits", action="store_true")

    rebuild_parser = subparsers.add_parser(
        "rebuild-conflicts",
        help="Recompute conflict.bitset as true.bitset AND false.bitset.",
    )
    rebuild_parser.add_argument("--store-dir", type=Path, default=DEFAULT_STORE_DIR)

    registry_parser = subparsers.add_parser(
        "import-default-registry",
        help="Build the default Order5StrategyRegistry and import selected strategies.",
    )
    registry_parser.add_argument("--store-dir", type=Path, default=DEFAULT_STORE_DIR)
    registry_parser.add_argument("--equations-file", type=Path)
    registry_parser.add_argument("--order4-max-id", type=int)
    registry_parser.add_argument(
        "--verdict",
        choices=("true", "false", "all"),
        default="all",
        help="Import only true strategies, false strategies, or both.",
    )
    registry_parser.add_argument(
        "--coverage-kind",
        action="append",
        choices=("source_target_sets", "compiler_pair_indexes", "explicit_pairs"),
        help="May be repeated; defaults to all coverage kinds.",
    )
    registry_parser.add_argument(
        "--strategy-id",
        action="append",
        help="May be repeated; defaults to all selected strategies.",
    )
    registry_parser.add_argument("--max-strategies", type=int)
    registry_parser.add_argument("--no-conflicts", action="store_true")
    registry_parser.add_argument(
        "--no-true-strategies",
        action="store_true",
        help="Build the registry with include_true_strategies=False.",
    )
    registry_parser.add_argument(
        "--no-paircheck-bank",
        action="store_true",
        help="Do not load the default explicit paircheck bank.",
    )
    registry_parser.add_argument(
        "--no-setcheck-bank",
        action="store_true",
        help="Do not load the discovered setcheck bank.",
    )
    registry_parser.add_argument(
        "--no-predicatecheck-bank",
        action="store_true",
        help="Do not load the discovered predicatecheck bank.",
    )

    preview_registry_parser = subparsers.add_parser(
        "preview-default-registry",
        help="Preview selected default registry strategies without writing bitsets.",
    )
    preview_registry_parser.add_argument("--store-dir", type=Path, default=DEFAULT_STORE_DIR)
    preview_registry_parser.add_argument("--equations-file", type=Path)
    preview_registry_parser.add_argument("--order4-max-id", type=int)
    preview_registry_parser.add_argument(
        "--verdict",
        choices=("true", "false", "all"),
        default="all",
    )
    preview_registry_parser.add_argument(
        "--coverage-kind",
        action="append",
        choices=("source_target_sets", "compiler_pair_indexes", "explicit_pairs"),
    )
    preview_registry_parser.add_argument("--strategy-id", action="append")
    preview_registry_parser.add_argument("--max-strategies", type=int)
    preview_registry_parser.add_argument("--top-n", type=int, default=10)
    preview_registry_parser.add_argument("--no-true-strategies", action="store_true")
    preview_registry_parser.add_argument("--no-paircheck-bank", action="store_true")
    preview_registry_parser.add_argument("--no-setcheck-bank", action="store_true")
    preview_registry_parser.add_argument("--no-predicatecheck-bank", action="store_true")

    args = parser.parse_args()

    if args.command == "init":
        store = ColumnarImplicationStore.create(
            args.store_dir,
            law_count=args.law_count,
            equations_path=args.equations_file,
            include_self=args.include_self,
            layers=_split_layers(args.layers),
            force=args.force,
        )
        _print_json(store.manifest)
        return

    if args.command == "import-pair-indexes":
        store = ColumnarImplicationStore.open(args.store_dir)
        summary = store.import_pair_indexes(
            args.input,
            layer_name=args.layer,
            source_id=args.source_id,
            source_kind=args.source_kind,
            write_pair_evidence=args.write_pair_evidence,
            update_conflicts=not args.no_conflicts,
        )
        _print_json(summary.to_json())
        return

    if args.command == "preview-finmodel-strategy-row":
        store = ColumnarImplicationStore.open(args.store_dir)
        row, partition = _load_finmodel_strategy_partition(args)
        preview = store.preview_source_target_block(
            "false",
            source_ids=partition["satisfied_ids"],
            target_ids=partition["refuted_ids"],
            source_id=row["strategy_id"],
            source_kind="strategy_manifest.finmodel_source_target_sets",
            top_n=args.top_n,
        )
        _print_json(_merge_finmodel_report(row, partition, preview))
        return

    if args.command == "import-finmodel-strategy-row":
        store = ColumnarImplicationStore.open(args.store_dir)
        row, partition = _load_finmodel_strategy_partition(args)
        summary = store.set_source_target_block(
            "false",
            source_ids=partition["satisfied_ids"],
            target_ids=partition["refuted_ids"],
            source_id=row["strategy_id"],
            source_kind="strategy_manifest.finmodel_source_target_sets",
            update_conflicts=not args.no_conflicts,
        )
        _print_json(_merge_finmodel_report(row, partition, summary))
        return

    if args.command == "preview-pair-indexes":
        store = ColumnarImplicationStore.open(args.store_dir)
        _print_json(
            store.preview_pair_indexes(
                args.input,
                layer_name=args.layer,
                top_n=args.top_n,
            )
        )
        return

    if args.command == "status":
        store = ColumnarImplicationStore.open(args.store_dir)
        eq1_id = eq2_id = None
        if args.eq_pair is not None:
            eq1_id, eq2_id = args.eq_pair
        _print_json(
            store.status(
                pair_index=args.pair_index,
                eq1_id=eq1_id,
                eq2_id=eq2_id,
                layers=_split_layers(args.layers) if args.layers else None,
            )
        )
        return

    if args.command == "preview-pair-index-strategy-row":
        store = ColumnarImplicationStore.open(args.store_dir)
        row = _find_strategy_row(args.strategies_json, args.strategy_id)
        input_path = _strategy_pair_index_path(row)
        _print_json(
            {
                **store.preview_pair_indexes(
                    input_path,
                    layer_name=_strategy_layer(row),
                    top_n=args.top_n,
                ),
                "strategy_id": row["strategy_id"],
                "coverage_kind": row.get("coverage_kind"),
                "strategy_pair_index_path": str(input_path),
                "manifest_coverage_count": row.get("coverage_count"),
            }
        )
        return

    if args.command == "import-pair-index-strategy-row":
        store = ColumnarImplicationStore.open(args.store_dir)
        row = _find_strategy_row(args.strategies_json, args.strategy_id)
        input_path = _strategy_pair_index_path(row)
        summary = store.import_pair_indexes(
            input_path,
            layer_name=_strategy_layer(row),
            source_id=row["strategy_id"],
            source_kind=f"strategy_manifest.{row.get('coverage_kind', 'pair_indexes')}",
            write_pair_evidence=args.write_pair_evidence,
            update_conflicts=not args.no_conflicts,
        )
        _print_json(
            {
                **summary.to_json(),
                "strategy_id": row["strategy_id"],
                "coverage_kind": row.get("coverage_kind"),
                "strategy_pair_index_path": str(input_path),
                "manifest_coverage_count": row.get("coverage_count"),
            }
        )
        return

    if args.command == "row":
        store = ColumnarImplicationStore.open(args.store_dir)
        _print_json(
            {
                "layer": args.layer,
                "source_id": args.source_id,
                "targets": store.row_targets(
                    args.layer,
                    args.source_id,
                    limit=args.limit,
                ),
            }
        )
        return

    if args.command == "row-summary":
        store = ColumnarImplicationStore.open(args.store_dir)
        _print_json(
            store.row_summary(
                args.source_id,
                layers=_split_layers(args.layers) if args.layers else None,
            )
        )
        return

    if args.command == "frontier":
        store = ColumnarImplicationStore.open(args.store_dir)
        _print_json(
            store.source_frontier(
                args.source_id,
                known_layers=_split_layers(args.known_layers),
                limit=args.limit,
            )
        )
        return

    if args.command == "summary":
        store = ColumnarImplicationStore.open(args.store_dir)
        result = dict(store.manifest)
        if args.count_bits:
            result["layer_counts"] = {
                layer: store.layer_count(layer) for layer in store.layers
            }
        _print_json(result)
        return

    if args.command == "rebuild-conflicts":
        store = ColumnarImplicationStore.open(args.store_dir)
        _print_json(store.rebuild_conflicts())
        return

    if args.command == "import-default-registry":
        store = ColumnarImplicationStore.open(args.store_dir)
        registry = _build_registry_from_args(args)
        _print_json(
            store.import_coverage_strategies(
                registry.strategies,
                verdict=_parse_verdict(args.verdict),
                coverage_kinds=set(args.coverage_kind) if args.coverage_kind else None,
                strategy_ids=set(args.strategy_id) if args.strategy_id else None,
                max_strategies=args.max_strategies,
                update_conflicts=not args.no_conflicts,
            )
        )
        return

    if args.command == "preview-default-registry":
        store = ColumnarImplicationStore.open(args.store_dir)
        registry = _build_registry_from_args(args)
        _print_json(
            store.preview_coverage_strategies(
                registry.strategies,
                verdict=_parse_verdict(args.verdict),
                coverage_kinds=set(args.coverage_kind) if args.coverage_kind else None,
                strategy_ids=set(args.strategy_id) if args.strategy_id else None,
                max_strategies=args.max_strategies,
                top_n=args.top_n,
            )
        )
        return

    raise AssertionError(f"unhandled command: {args.command}")


def _split_layers(raw: str) -> tuple[str, ...]:
    return tuple(layer.strip() for layer in raw.split(",") if layer.strip())


def _print_json(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))


def _parse_verdict(raw: str) -> bool | None:
    if raw == "true":
        return True
    if raw == "false":
        return False
    return None


def _build_registry_from_args(args):
    from math_distill_stage2.order5_spine_smoke import (  # noqa: PLC0415
        DEFAULT_EQ_SIZE5_PATH,
        DEFAULT_ORDER4_MAX_ID,
    )
    from math_distill_stage2.order5_strategy_registry import (  # noqa: PLC0415
        DEFAULT_PAIRCHECK_BANK_PATH,
        DEFAULT_PREDICATECHECK_BANK_PATH,
        DEFAULT_SETCHECK_BANK_PATH,
        build_default_order5_strategy_registry,
    )

    return build_default_order5_strategy_registry(
        equations_path=args.equations_file or DEFAULT_EQ_SIZE5_PATH,
        order4_max_id=args.order4_max_id
        if args.order4_max_id is not None
        else DEFAULT_ORDER4_MAX_ID,
        include_true_strategies=not args.no_true_strategies,
        paircheck_bank_path=None if args.no_paircheck_bank else DEFAULT_PAIRCHECK_BANK_PATH,
        setcheck_bank_path=None if args.no_setcheck_bank else DEFAULT_SETCHECK_BANK_PATH,
        predicatecheck_bank_path=None
        if args.no_predicatecheck_bank
        else DEFAULT_PREDICATECHECK_BANK_PATH,
    )


def _load_finmodel_strategy_partition(args) -> tuple[dict, dict]:
    row = _find_strategy_row(args.strategies_json, args.strategy_id)
    if row.get("verdict") is not False:
        raise ValueError(f"{args.strategy_id} is not a false strategy")
    if "model_table" not in row:
        raise ValueError(f"{args.strategy_id} does not contain model_table")
    partition = finite_model_equation_partition(
        equations_path=args.equations_file,
        model_table=row["model_table"],
    )
    return row, partition


def _find_strategy_row(path: Path, strategy_id: str) -> dict:
    rows = json.loads(path.read_text(encoding="utf-8"))
    for row in rows:
        if row.get("strategy_id") == strategy_id:
            return row
    raise KeyError(strategy_id)


def _strategy_layer(row: dict) -> str:
    return "true" if row.get("verdict") is True else "false"


def _strategy_pair_index_path(row: dict) -> Path:
    for key in ("template_pair_index_cache_path", "pair_bank_path"):
        value = row.get(key)
        if value:
            return Path(value)
    raise ValueError(f"{row.get('strategy_id')} has no pair-index cache path")


def _merge_finmodel_report(row: dict, partition: dict, result: dict) -> dict:
    return {
        **result,
        "strategy_id": row["strategy_id"],
        "model_family": row.get("model_family"),
        "model_order": partition["model_order"],
        "computed_source_count": partition["satisfied_count"],
        "computed_target_count": partition["refuted_count"],
        "manifest_source_count": row.get("source_count"),
        "manifest_target_count": row.get("target_count"),
        "manifest_coverage_count": row.get("coverage_count"),
        "partition_elapsed_seconds": partition["elapsed_seconds"],
    }


if __name__ == "__main__":
    main()
