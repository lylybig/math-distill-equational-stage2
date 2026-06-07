from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Sequence

from math_distill_stage2.order5_pair_dataset import read_equations


DEFAULT_EQUATIONS_PATH = Path(
    "external/equational-theories-lean-stage2/examples/problems/eq_size5.txt"
)
DEFAULT_MANIFEST_PATH = Path("data/processed/order5_pair_space/manifest.json")


def pair_count(law_count: int, *, include_self: bool = False) -> int:
    _validate_law_count(law_count)
    if include_self:
        return law_count * law_count
    return law_count * (law_count - 1)


def pair_index_to_ids(
    pair_index: int,
    *,
    law_count: int,
    include_self: bool = False,
) -> tuple[int, int]:
    _validate_law_count(law_count)
    total = pair_count(law_count, include_self=include_self)
    if pair_index < 0 or pair_index >= total:
        raise ValueError(
            f"pair_index must be in [0, {total}); got {pair_index}"
        )

    if include_self:
        row, column = divmod(pair_index, law_count)
        return row + 1, column + 1

    row, column_slot = divmod(pair_index, law_count - 1)
    eq1_id = row + 1
    eq2_id = column_slot + 1
    if eq2_id >= eq1_id:
        eq2_id += 1
    return eq1_id, eq2_id


def ids_to_pair_index(
    eq1_id: int,
    eq2_id: int,
    *,
    law_count: int,
    include_self: bool = False,
) -> int:
    _validate_law_count(law_count)
    _validate_eq_id("eq1_id", eq1_id, law_count)
    _validate_eq_id("eq2_id", eq2_id, law_count)
    if not include_self and eq1_id == eq2_id:
        raise ValueError("self pairs are excluded from this pair space")

    if include_self:
        return (eq1_id - 1) * law_count + (eq2_id - 1)

    column_slot = eq2_id - 1
    if eq2_id > eq1_id:
        column_slot -= 1
    return (eq1_id - 1) * (law_count - 1) + column_slot


def materialize_problem(
    pair_index: int,
    equations: Sequence[str],
    *,
    answer: bool | None = None,
    include_self: bool = False,
) -> dict:
    eq1_id, eq2_id = pair_index_to_ids(
        pair_index,
        law_count=len(equations),
        include_self=include_self,
    )
    return {
        "id": f"{eq1_id}_{eq2_id}",
        "pair_index": pair_index,
        "eq1_id": eq1_id,
        "eq2_id": eq2_id,
        "equation1": equations[eq1_id - 1],
        "equation2": equations[eq2_id - 1],
        "answer": answer,
    }


def write_pair_space_manifest(
    *,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    equations_path: Path = DEFAULT_EQUATIONS_PATH,
    include_self: bool = False,
) -> dict:
    equations = read_equations(equations_path)
    law_count = len(equations)
    manifest = {
        "schema_version": 1,
        "kind": "order5_pair_space",
        "description": "Implicit directed equation-pair universe; no pair rows are materialized.",
        "equations_path": str(equations_path),
        "equations_sha256": _sha256_file(equations_path),
        "law_count": law_count,
        "include_self": include_self,
        "pair_count": pair_count(law_count, include_self=include_self),
        "pair_index_base": 0,
        "eq_id_base": 1,
        "pair_record_schema": ["pair_index"],
        "materialized_problem_schema": [
            "id",
            "pair_index",
            "eq1_id",
            "eq2_id",
            "equation1",
            "equation2",
            "answer",
        ],
        "mapping": {
            "pair_index_to_eq_ids": (
                "row = pair_index // (law_count - 1); "
                "slot = pair_index % (law_count - 1); "
                "eq1_id = row + 1; eq2_id = slot + 1; "
                "if eq2_id >= eq1_id then eq2_id += 1"
            )
            if not include_self
            else (
                "row = pair_index // law_count; column = pair_index % law_count; "
                "eq1_id = row + 1; eq2_id = column + 1"
            )
        },
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return manifest


def _validate_law_count(law_count: int) -> None:
    if law_count <= 0:
        raise ValueError(f"law_count must be positive; got {law_count}")


def _validate_eq_id(name: str, eq_id: int, law_count: int) -> None:
    if eq_id < 1 or eq_id > law_count:
        raise ValueError(f"{name} must be in [1, {law_count}]; got {eq_id}")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
