from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from math_distill_stage2.counterexample.finite_magma import FiniteMagma, enumerate_magmas
from math_distill_stage2.equations import Equation, parse_equation
from math_distill_stage2.order5_pair_space import ids_to_pair_index
from math_distill_stage2.order5_strategy_registry import (
    Order5StrategyRegistry,
    find_true_strategy_ids_for_pair,
    finmodel_false_judge_code,
)
from math_distill_stage2.order5_spine_smoke import (
    DEFAULT_EQ_SIZE5_PATH,
    DEFAULT_ORDER4_MAX_ID,
)


ORDER4_TO_ORDER4 = "order4_source_to_order4_target"
ORDER4_TO_ORDER5 = "order4_source_to_order5_target"
ORDER5_TO_ORDER4 = "order5_source_to_order4_target"
ORDER5_TO_ORDER5 = "order5_source_to_order5_target"
PAIRCHECK_STRATEGY_KEY = "false.finmodel.paircheck.bank"


@dataclass(frozen=True)
class PaircheckModel:
    label: str
    table: tuple[tuple[int, ...], ...]
    source: str

    @property
    def order(self) -> int:
        return len(self.table)

    def to_json_table(self) -> list[list[int]]:
        return [list(row) for row in self.table]

    def to_json(self) -> dict:
        return {
            "label": self.label,
            "source": self.source,
            "order": self.order,
            "table": self.to_json_table(),
        }


def load_equation_texts(path: Path) -> dict[int, str]:
    return {
        index: line.strip()
        for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if line.strip()
    }


def load_parsed_equations(path: Path) -> dict[int, Equation]:
    return {
        equation_id: parse_equation(equation)
        for equation_id, equation in load_equation_texts(path).items()
    }


def load_paircheck_models_from_strategy_manifest(
    path: Path,
    *,
    limit: int | None = None,
) -> list[PaircheckModel]:
    if limit is not None and limit <= 0:
        return []
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("strategy manifest must be a JSON list")
    models: list[PaircheckModel] = []
    seen: set[tuple[tuple[int, ...], ...]] = set()
    for row in rows:
        if not isinstance(row, dict) or "model_table" not in row:
            continue
        table = _normalize_table(row["model_table"])
        if table in seen:
            continue
        seen.add(table)
        source = str(row.get("strategy_id") or row.get("strategy_key") or "")
        label = str(row.get("model_family") or source or f"model_{len(models) + 1}")
        models.append(PaircheckModel(label=label, table=table, source=source))
        if limit is not None and len(models) >= limit:
            break
    return models


def enumerate_paircheck_models(
    *,
    order: int,
    existing_models: Sequence[PaircheckModel] = (),
    limit: int | None = None,
) -> list[PaircheckModel]:
    seen = {model.table for model in existing_models}
    models: list[PaircheckModel] = []
    for index, magma in enumerate(enumerate_magmas(order), start=1):
        if magma.table in seen:
            continue
        seen.add(magma.table)
        models.append(
            PaircheckModel(
                label=f"enum_order{order}_{index}",
                table=magma.table,
                source=f"enumerate_magmas_order{order}",
            )
        )
        if limit is not None and len(models) >= limit:
            break
    return models


def pair_stratum(eq1_id: int, eq2_id: int, *, order4_max_id: int) -> str | None:
    source_order5 = eq1_id > order4_max_id
    target_order5 = eq2_id > order4_max_id
    if source_order5 and target_order5:
        return ORDER5_TO_ORDER5
    if source_order5:
        return ORDER5_TO_ORDER4
    if target_order5:
        return ORDER4_TO_ORDER5
    return ORDER4_TO_ORDER4


def sample_unresolved_pairs(
    *,
    registry: Order5StrategyRegistry,
    order4_max_id: int,
    size: int,
    seed: int,
    max_scan_attempts: int | None = None,
) -> list[dict]:
    if size <= 0:
        raise ValueError("size must be positive")

    rng = random.Random(seed)
    law_count = registry.law_count
    ceiling = max_scan_attempts or max(size * 200, 10_000)
    attempts = 0
    seen: set[tuple[int, int]] = set()
    rows: list[dict] = []

    while len(rows) < size and attempts < ceiling:
        attempts += 1
        eq1_id = rng.randint(1, law_count)
        eq2_id = rng.randint(1, law_count - 1)
        if eq2_id >= eq1_id:
            eq2_id += 1
        if (eq1_id, eq2_id) in seen:
            continue
        stratum = pair_stratum(eq1_id, eq2_id, order4_max_id=order4_max_id)
        if stratum is None:
            continue
        pair_index = ids_to_pair_index(eq1_id, eq2_id, law_count=law_count)
        if registry.find_covering_strategies(pair_index):
            continue
        seen.add((eq1_id, eq2_id))
        rows.append(
            {
                "pair_index": pair_index,
                "eq1_id": eq1_id,
                "eq2_id": eq2_id,
                "stratum": stratum,
            }
        )

    return rows


def find_paircheck_countermodels(
    *,
    candidate_pairs: Sequence[dict],
    equations: dict[int, Equation],
    models: Sequence[PaircheckModel],
) -> list[dict]:
    rows: list[dict] = []
    seen_pairs: set[int] = set()
    for pair in candidate_pairs:
        pair_index = int(pair["pair_index"])
        if pair_index in seen_pairs:
            continue
        eq1_id = int(pair["eq1_id"])
        eq2_id = int(pair["eq2_id"])
        for model in models:
            magma = FiniteMagma(order=model.order, table=model.table)
            if magma.satisfies(equations[eq1_id]) and not magma.satisfies(
                equations[eq2_id]
            ):
                seen_pairs.add(pair_index)
                rows.append(
                    {
                        "pair_index": pair_index,
                        "eq1_id": eq1_id,
                        "eq2_id": eq2_id,
                        "stratum": str(pair["stratum"]),
                        "model_label": model.label,
                        "model_source": model.source,
                        "order": model.order,
                        "table": model.to_json_table(),
                        "python_verified": True,
                    }
                )
                break
    return rows


def analyze_existing_false_coverage(
    *,
    bank_rows: Sequence[dict],
    equations: dict[int, Equation],
    existing_models: Sequence[PaircheckModel],
    order4_max_id: int,
) -> tuple[list[dict], dict]:
    annotated_rows: list[dict] = []
    existing_false_covered = 0
    for row in bank_rows:
        eq1_id = int(row["eq1_id"])
        eq2_id = int(row["eq2_id"])
        matches: list[dict] = []
        for model in existing_models:
            magma = FiniteMagma(order=model.order, table=model.table)
            if magma.satisfies(equations[eq1_id]) and not magma.satisfies(
                equations[eq2_id]
            ):
                matches.append(
                    {
                        "model_label": model.label,
                        "model_source": model.source,
                    }
                )
        covered = bool(matches)
        if covered:
            existing_false_covered += 1
        annotated_rows.append(
            {
                **row,
                "existing_false_covered": covered,
                "existing_false_matches": matches,
                "candidate_false_increment": not covered,
            }
        )
    summary = {
        "schema_version": 1,
        "total_count": len(annotated_rows),
        "existing_false_covered_count": existing_false_covered,
        "candidate_false_increment_count": len(annotated_rows) - existing_false_covered,
    }
    return annotated_rows, summary


def merge_paircheck_increment_rows(
    rows: Sequence[dict],
    *,
    smoke_rows: Sequence[dict] = (),
    equations_path: Path = DEFAULT_EQ_SIZE5_PATH,
    order4_max_id: int = DEFAULT_ORDER4_MAX_ID,
    include_seedbank: bool = True,
) -> tuple[list[dict], dict]:
    smoke_status_by_pair: dict[int, str] = {}
    for row in smoke_rows:
        pair_index = int(row["pair_index"])
        status = row.get("status")
        if not isinstance(status, str):
            remote_result = row.get("remote_result")
            if isinstance(remote_result, dict):
                status = remote_result.get("status")
        smoke_status_by_pair[pair_index] = str(status or "unknown")

    deduped: dict[int, dict] = {}
    non_increment_count = 0
    for row in rows:
        if row.get("candidate_false_increment") is False:
            non_increment_count += 1
            continue
        pair_index = int(row["pair_index"])
        if pair_index in deduped:
            continue
        eq1_id = int(row["eq1_id"])
        eq2_id = int(row["eq2_id"])
        true_conflicts = find_true_strategy_ids_for_pair(
            eq1_id,
            eq2_id,
            equations_path=equations_path,
            order4_max_id=order4_max_id,
            include_seedbank=include_seedbank,
        )
        smoke_status = smoke_status_by_pair.get(pair_index, "unsmoked")
        deduped[pair_index] = {
            **row,
            "pair_index": pair_index,
            "eq1_id": eq1_id,
            "eq2_id": eq2_id,
            "remote_smoke_status": smoke_status,
            "remote_smoke_accepted": smoke_status == "accepted",
            "true_conflict_strategy_ids": true_conflicts,
            "true_conflict": bool(true_conflicts),
            "registry_ready": not bool(true_conflicts),
        }

    merged_rows = sorted(deduped.values(), key=lambda row: row["pair_index"])
    true_conflict_count = sum(1 for row in merged_rows if row["true_conflict"])
    registry_ready_count = sum(1 for row in merged_rows if row["registry_ready"])
    remote_smoke_accepted_count = sum(
        1 for row in merged_rows if row["remote_smoke_accepted"]
    )
    summary = {
        "schema_version": 1,
        "input_count": len(rows),
        "written_count": len(merged_rows),
        "duplicate_count": len(rows) - non_increment_count - len(merged_rows),
        "non_increment_count": non_increment_count,
        "remote_smoke_checked_count": sum(
            1 for row in merged_rows if row["remote_smoke_status"] != "unsmoked"
        ),
        "remote_smoke_accepted_count": remote_smoke_accepted_count,
        "true_conflict_count": true_conflict_count,
        "registry_ready_count": registry_ready_count,
        "stratum_counts": dict(Counter(row["stratum"] for row in merged_rows)),
        "order_counts": dict(
            Counter(str(row["order"]) for row in merged_rows if "order" in row)
        ),
    }
    return merged_rows, summary


def table_sha256(table: Sequence[Sequence[int]]) -> str:
    payload = json.dumps(table, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def write_jsonl(path: Path, rows: Sequence[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
        ),
        encoding="utf-8",
    )


def write_paircheck_bank(rows: Sequence[dict], *, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    deduped: dict[int, dict] = {}
    for row in rows:
        pair_index = int(row["pair_index"])
        if pair_index in deduped:
            continue
        table = row["table"]
        deduped[pair_index] = {
            "schema_version": 1,
            "strategy_key": PAIRCHECK_STRATEGY_KEY,
            "pair_index": pair_index,
            "eq1_id": int(row["eq1_id"]),
            "eq2_id": int(row["eq2_id"]),
            "stratum": str(row["stratum"]),
            "model_label": str(row["model_label"]),
            "model_source": str(row["model_source"]),
            "order": int(row["order"]),
            "table": table,
            "table_sha256": table_sha256(table),
            "python_verified": bool(row["python_verified"]),
            "remote_official_smoke": None,
        }

    output_rows = sorted(deduped.values(), key=lambda row: row["pair_index"])
    write_jsonl(output_dir / "verified_bank.jsonl", output_rows)
    summary = {
        "schema_version": 1,
        "strategy_key": PAIRCHECK_STRATEGY_KEY,
        "input_rows": len(rows),
        "written": len(output_rows),
        "stratum_counts": dict(Counter(row["stratum"] for row in output_rows)),
        "order_counts": dict(Counter(str(row["order"]) for row in output_rows)),
    }
    (output_dir / "bank_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return summary


def build_remote_smoke_records(
    *,
    bank_rows: Sequence[dict],
    equations: dict[int, str],
    limit: int,
) -> list[dict]:
    records: list[dict] = []
    for row in bank_rows[:limit]:
        eq1_id = int(row["eq1_id"])
        eq2_id = int(row["eq2_id"])
        table = tuple(
            tuple(int(value) for value in table_row) for table_row in row["table"]
        )
        code = finmodel_false_judge_code(table)
        records.append(
            {
                "id": f"paircheck_{eq1_id}_{eq2_id}",
                "pair_index": int(row["pair_index"]),
                "problem": {
                    "id": f"paircheck_{eq1_id}_{eq2_id}",
                    "eq1_id": eq1_id,
                    "eq2_id": eq2_id,
                    "equation1": equations[eq1_id],
                    "equation2": equations[eq2_id],
                    "answer": False,
                },
                "answer": {
                    "call": "judge",
                    "verdict": "false",
                    "code": code,
                },
            }
        )
    return records


def build_paircheck_bank_artifacts(
    *,
    registry: Order5StrategyRegistry,
    equations_path: Path,
    model_manifest_path: Path,
    output_dir: Path,
    sample_size: int,
    seed: int,
    order4_max_id: int,
    smoke_limit: int,
    model_limit: int | None = None,
    enumerate_model_orders: Sequence[int] = (),
    enumerate_model_limit: int | None = None,
    max_scan_attempts: int | None = None,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    equation_texts = load_equation_texts(equations_path)
    equations = {
        equation_id: parse_equation(equation)
        for equation_id, equation in equation_texts.items()
    }
    models = load_paircheck_models_from_strategy_manifest(
        model_manifest_path,
        limit=model_limit,
    )
    for order in enumerate_model_orders:
        models.extend(
            enumerate_paircheck_models(
                order=order,
                existing_models=models,
                limit=enumerate_model_limit,
            )
        )
    candidates = sample_unresolved_pairs(
        registry=registry,
        order4_max_id=order4_max_id,
        size=sample_size,
        seed=seed,
        max_scan_attempts=max_scan_attempts,
    )
    countermodels = find_paircheck_countermodels(
        candidate_pairs=candidates,
        equations=equations,
        models=models,
    )
    bank_summary = write_paircheck_bank(countermodels, output_dir=output_dir)
    bank_rows = _read_jsonl(output_dir / "verified_bank.jsonl")
    existing_false_models = load_paircheck_models_from_strategy_manifest(
        model_manifest_path
    )
    existing_false_rows, existing_false_summary = analyze_existing_false_coverage(
        bank_rows=bank_rows,
        equations=equations,
        existing_models=existing_false_models,
        order4_max_id=order4_max_id,
    )
    write_jsonl(output_dir / "existing_false_filter.jsonl", existing_false_rows)
    (output_dir / "existing_false_filter_summary.json").write_text(
        json.dumps(
            existing_false_summary,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    increment_rows = [
        row for row in existing_false_rows if row["candidate_false_increment"]
    ]
    smoke_records = build_remote_smoke_records(
        bank_rows=increment_rows,
        equations=equation_texts,
        limit=smoke_limit,
    )

    write_jsonl(output_dir / "candidate_pairs.jsonl", candidates)
    write_jsonl(output_dir / "model_pool.jsonl", [model.to_json() for model in models])
    write_jsonl(output_dir / "countermodels.jsonl", countermodels)
    write_jsonl(output_dir / "candidate_increment_bank.jsonl", increment_rows)
    write_jsonl(output_dir / "official_smoke_input.jsonl", smoke_records)

    summary = {
        "schema_version": 1,
        "candidate_count": len(candidates),
        "model_count": len(models),
        "countermodel_count": len(countermodels),
        "bank_written": bank_summary["written"],
        "existing_false_covered_count": existing_false_summary[
            "existing_false_covered_count"
        ],
        "candidate_false_increment_count": existing_false_summary[
            "candidate_false_increment_count"
        ],
        "smoke_input_count": len(smoke_records),
        "seed": seed,
        "sample_size": sample_size,
        "order4_max_id": order4_max_id,
        "paths": {
            "candidate_pairs": str(output_dir / "candidate_pairs.jsonl"),
            "model_pool": str(output_dir / "model_pool.jsonl"),
            "countermodels": str(output_dir / "countermodels.jsonl"),
            "verified_bank": str(output_dir / "verified_bank.jsonl"),
            "candidate_increment_bank": str(
                output_dir / "candidate_increment_bank.jsonl"
            ),
            "official_smoke_input": str(output_dir / "official_smoke_input.jsonl"),
        },
    }
    (output_dir / "pipeline_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return summary


def _normalize_table(raw_table: object) -> tuple[tuple[int, ...], ...]:
    if not isinstance(raw_table, list) or not raw_table:
        raise ValueError("magma table must be a non-empty nested list")
    order = len(raw_table)
    table: list[tuple[int, ...]] = []
    for row in raw_table:
        if not isinstance(row, list) or len(row) != order:
            raise ValueError("magma table must be square")
        normalized_row: list[int] = []
        for value in row:
            if not isinstance(value, int) or value < 0 or value >= order:
                raise ValueError("magma table entries must be integers in [0, order)")
            normalized_row.append(value)
        table.append(tuple(normalized_row))
    return tuple(table)


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
