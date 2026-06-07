from __future__ import annotations

import json
import random
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from math_distill_stage2.dataset_io import write_jsonl
from math_distill_stage2.equations import Equation, Expr, parse_equation


DEFAULT_EQ_SIZE5_PATH = Path(
    "external/equational-theories-lean-stage2/examples/problems/eq_size5.txt"
)
DEFAULT_OUTPUT_DIR = Path("data/processed/order5_smokes")
DEFAULT_ORDER4_MAX_ID = 4694
DEFAULT_SEED = 20260512


@dataclass(frozen=True)
class EquationSpineFeature:
    equation_id: int
    equation: str
    lhs_var: str | None
    rhs_leftmost_var: str
    rhs_rightmost_var: str
    left_spine_depth: int
    right_spine_depth: int

    @property
    def is_left_zero_source(self) -> bool:
        return (
            self.lhs_var is not None
            and self.left_spine_depth > 0
            and self.rhs_leftmost_var == self.lhs_var
        )

    @property
    def is_left_zero_target(self) -> bool:
        return self.lhs_var is not None and self.rhs_leftmost_var != self.lhs_var


def equation_spine_feature(equation_id: int, equation: str) -> EquationSpineFeature:
    parsed = parse_equation(equation)
    lhs_var = _bare_var(parsed.left)
    return EquationSpineFeature(
        equation_id=equation_id,
        equation=equation,
        lhs_var=lhs_var,
        rhs_leftmost_var=_leftmost_var(parsed.right),
        rhs_rightmost_var=_rightmost_var(parsed.right),
        left_spine_depth=_left_spine_depth(parsed.right),
        right_spine_depth=_right_spine_depth(parsed.right),
    )


def load_equation_spine_features(path: Path) -> list[EquationSpineFeature]:
    return [
        equation_spine_feature(index, line.strip())
        for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if line.strip()
    ]


def spine_pair_stratum(
    source: EquationSpineFeature,
    target: EquationSpineFeature,
    *,
    order4_max_id: int = DEFAULT_ORDER4_MAX_ID,
) -> str | None:
    if source.equation_id == target.equation_id:
        return None
    if not source.is_left_zero_source or not target.is_left_zero_target:
        return None

    source_order5 = source.equation_id > order4_max_id
    target_order5 = target.equation_id > order4_max_id
    if source_order5 and target_order5:
        return "order5_source_to_order5_target"
    if source_order5:
        return "order5_source_to_order4_target"
    if target_order5:
        return "order4_source_to_order5_target"
    return "order4_source_to_order4_target"


def build_order5_spine_smoke(
    *,
    equations_path: Path = DEFAULT_EQ_SIZE5_PATH,
    output_path: Path,
    manifest_path: Path,
    size: int,
    seed: int = DEFAULT_SEED,
    order4_max_id: int = DEFAULT_ORDER4_MAX_ID,
) -> dict:
    if size <= 0:
        raise ValueError("size must be positive")

    features = load_equation_spine_features(equations_path)
    sources = [feature for feature in features if feature.is_left_zero_source]
    targets = [feature for feature in features if feature.is_left_zero_target]
    strata = _build_strata(sources, targets, order4_max_id=order4_max_id)
    if not strata:
        raise ValueError("no Spine Isolation left-zero candidate strata found")

    quotas = _allocate_equal_quotas(
        {name: len(srcs) * len(tgts) for name, (srcs, tgts) in strata.items()},
        size,
    )

    selected: list[tuple[str, EquationSpineFeature, EquationSpineFeature]] = []
    for stratum, quota in quotas.items():
        srcs, tgts = strata[stratum]
        selected.extend(_sample_stratum(stratum, srcs, tgts, quota, seed=seed))

    selected.sort(key=lambda item: (item[1].equation_id, item[2].equation_id))
    rows = [
        _problem_row(index, stratum, source, target)
        for index, (stratum, source, target) in enumerate(selected)
    ]
    write_jsonl(output_path, rows)

    manifest = {
        "schema_version": 1,
        "theorem_family": "spine_left_zero_nonleft",
        "theorem_statement": (
            "Pure left-spine source does not imply a bare-LHS target whose RHS "
            "leftmost variable differs from its LHS variable."
        ),
        "answer": False,
        "equations_path": str(equations_path),
        "output_path": str(output_path),
        "seed": seed,
        "order4_max_id": order4_max_id,
        "equation_count": len(features),
        "source_count": len(sources),
        "target_count": len(targets),
        "requested_rows": size,
        "rows": len(rows),
        "candidate_counts": {
            name: len(srcs) * len(tgts)
            for name, (srcs, tgts) in sorted(strata.items())
        },
        "selected_counts": dict(Counter(row["difficulty"] for row in rows)),
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return manifest


def _build_strata(
    sources: list[EquationSpineFeature],
    targets: list[EquationSpineFeature],
    *,
    order4_max_id: int,
) -> dict[str, tuple[list[EquationSpineFeature], list[EquationSpineFeature]]]:
    source_le4 = [source for source in sources if source.equation_id <= order4_max_id]
    source_order5 = [source for source in sources if source.equation_id > order4_max_id]
    target_le4 = [target for target in targets if target.equation_id <= order4_max_id]
    target_order5 = [target for target in targets if target.equation_id > order4_max_id]
    candidates = {
        "order4_source_to_order4_target": (source_le4, target_le4),
        "order4_source_to_order5_target": (source_le4, target_order5),
        "order5_source_to_order4_target": (source_order5, target_le4),
        "order5_source_to_order5_target": (source_order5, target_order5),
    }
    return {
        name: (srcs, tgts)
        for name, (srcs, tgts) in candidates.items()
        if srcs and tgts
    }


def _allocate_equal_quotas(candidate_counts: dict[str, int], size: int) -> dict[str, int]:
    available = {name: count for name, count in candidate_counts.items() if count > 0}
    quotas = {name: 0 for name in available}
    remaining = size
    while remaining > 0:
        open_names = [name for name, count in available.items() if quotas[name] < count]
        if not open_names:
            break
        base = max(1, remaining // len(open_names))
        for name in sorted(open_names):
            if remaining <= 0:
                break
            add = min(base, available[name] - quotas[name], remaining)
            quotas[name] += add
            remaining -= add
    return quotas


def _sample_stratum(
    stratum: str,
    sources: list[EquationSpineFeature],
    targets: list[EquationSpineFeature],
    quota: int,
    *,
    seed: int,
) -> list[tuple[str, EquationSpineFeature, EquationSpineFeature]]:
    if quota <= 0:
        return []
    candidate_count = len(sources) * len(targets)
    if quota >= candidate_count:
        return [(stratum, source, target) for source in sources for target in targets]

    rng = random.Random(f"{seed}:{stratum}")
    selected_keys: set[tuple[int, int]] = set()
    selected: list[tuple[str, EquationSpineFeature, EquationSpineFeature]] = []
    attempts = 0
    max_attempts = max(1000, quota * 50)
    while len(selected) < quota and attempts < max_attempts:
        attempts += 1
        source = rng.choice(sources)
        target = rng.choice(targets)
        key = (source.equation_id, target.equation_id)
        if key in selected_keys:
            continue
        selected_keys.add(key)
        selected.append((stratum, source, target))
    if len(selected) != quota:
        raise ValueError(f"{stratum}: selected {len(selected)} rows, expected {quota}")
    return selected


def _problem_row(
    index: int,
    stratum: str,
    source: EquationSpineFeature,
    target: EquationSpineFeature,
) -> dict:
    return {
        "id": f"false_{source.equation_id}_{target.equation_id}",
        "index": index,
        "difficulty": stratum,
        "eq1_id": source.equation_id,
        "eq2_id": target.equation_id,
        "equation1": source.equation,
        "equation2": target.equation,
        "answer": False,
    }


def _bare_var(expr: Expr) -> str | None:
    return expr.value if expr.kind == "var" else None


def _leftmost_var(expr: Expr) -> str:
    if expr.kind == "var":
        assert expr.value is not None
        return expr.value
    assert expr.left is not None
    return _leftmost_var(expr.left)


def _rightmost_var(expr: Expr) -> str:
    if expr.kind == "var":
        assert expr.value is not None
        return expr.value
    assert expr.right is not None
    return _rightmost_var(expr.right)


def _left_spine_depth(expr: Expr) -> int:
    if expr.kind == "var":
        return 0
    assert expr.left is not None
    return 1 + _left_spine_depth(expr.left)


def _right_spine_depth(expr: Expr) -> int:
    if expr.kind == "var":
        return 0
    assert expr.right is not None
    return 1 + _right_spine_depth(expr.right)
