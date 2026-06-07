from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Sequence

from math_distill_stage2.equations import Equation, Expr, parse_equation
from math_distill_stage2.order5_pair_dataset import DEFAULT_EQUATIONS_PATH, read_equations


LiftingFamilyName = Literal[
    "list_append",
    "multiset_add",
    "finset_union",
    "left_projection",
    "right_projection",
]

ALL_LIFTING_FAMILIES: tuple[LiftingFamilyName, ...] = (
    "list_append",
    "multiset_add",
    "finset_union",
    "left_projection",
    "right_projection",
)

FAMILY_LABELS: dict[LiftingFamilyName, str] = {
    "list_append": "List Nat with append",
    "multiset_add": "Multiset Nat with addition",
    "finset_union": "Finset Nat with union",
    "left_projection": "Nat with left projection",
    "right_projection": "Nat with right projection",
}

FAMILY_NORMAL_FORM_KIND: dict[LiftingFamilyName, str] = {
    "list_append": "leaf_sequence",
    "multiset_add": "leaf_multiset",
    "finset_union": "leaf_set",
    "left_projection": "leftmost_leaf",
    "right_projection": "rightmost_leaf",
}

FAMILY_ETP_REFERENCES: dict[LiftingFamilyName, tuple[str, ...]] = {
    "list_append": (
        "third_party/equational_theories/equational_theories/LiftingMagmaFamilies.lean",
        "third_party/equational_theories/equational_theories/Generated/"
        "InvariantMetatheoremNonimplications/instLiftingMagmaFamilyList_counterexamples.lean",
    ),
    "multiset_add": (
        "third_party/equational_theories/equational_theories/LiftingMagmaFamilies.lean",
        "third_party/equational_theories/equational_theories/Generated/"
        "InvariantMetatheoremNonimplications/instLiftingMagmaFamilyMultiset_counterexamples.lean",
    ),
    "finset_union": (
        "third_party/equational_theories/equational_theories/LiftingMagmaFamilies.lean",
        "third_party/equational_theories/equational_theories/Generated/"
        "InvariantMetatheoremNonimplications/instLiftingMagmaFamilyFinset_counterexamples.lean",
    ),
    "left_projection": (
        "third_party/equational_theories/equational_theories/LiftingMagmaFamilies.lean",
        "third_party/equational_theories/equational_theories/Generated/"
        "InvariantMetatheoremNonimplications/instLiftingMagmaFamilyLeftProj_counterexamples.lean",
    ),
    "right_projection": (
        "third_party/equational_theories/equational_theories/LiftingMagmaFamilies.lean",
        "third_party/equational_theories/equational_theories/Generated/"
        "InvariantMetatheoremNonimplications/instLiftingMagmaFamilyRightProj_counterexamples.lean",
    ),
}


@dataclass(frozen=True)
class LiftingFamilyProfile:
    family: LiftingFamilyName
    law_count: int
    source_ids: frozenset[int]
    target_ids: frozenset[int]
    representative_pairs: dict[str, tuple[int, int] | None]

    @property
    def strategy_key(self) -> str:
        return f"false.infinite_model.lifting_family.{self.family}"

    @property
    def source_count(self) -> int:
        return len(self.source_ids)

    @property
    def target_count(self) -> int:
        return len(self.target_ids)

    @property
    def raw_coverage_count(self) -> int:
        return self.source_count * self.target_count - len(self.source_ids & self.target_ids)

    def to_json(self, *, include_ids: bool = True) -> dict:
        row = {
            "schema_version": 1,
            "candidate_key": self.strategy_key,
            "strategy_key": self.strategy_key,
            "verdict": "false",
            "certificate_family": "infinite_model_lifting_family",
            "certificate_generator": "order5_infinite_model_counterexamples",
            "family": self.family,
            "model": FAMILY_LABELS[self.family],
            "normal_form_kind": FAMILY_NORMAL_FORM_KIND[self.family],
            "source_count": self.source_count,
            "target_count": self.target_count,
            "raw_coverage": self.raw_coverage_count,
            "representative_pairs": {
                key: list(value) if value is not None else None
                for key, value in self.representative_pairs.items()
            },
            "etp_reference_files": list(FAMILY_ETP_REFERENCES[self.family]),
        }
        if include_ids:
            row["source_ids"] = sorted(self.source_ids)
            row["target_ids"] = sorted(self.target_ids)
        return row


def parse_law_text(source: str) -> Equation:
    """Parse a Stage 2 or ETP equation, accepting either `*` or `◇`."""

    return parse_equation(source.replace("◇", "*"))


def family_satisfies_equation(
    equation: Equation,
    family: LiftingFamilyName,
) -> bool:
    return _normal_form(equation.left, family) == _normal_form(equation.right, family)


def families_refuting_implication(
    source_equation: Equation | str,
    target_equation: Equation | str,
    *,
    families: Sequence[LiftingFamilyName] = ALL_LIFTING_FAMILIES,
) -> tuple[LiftingFamilyName, ...]:
    source = parse_law_text(source_equation) if isinstance(source_equation, str) else source_equation
    target = parse_law_text(target_equation) if isinstance(target_equation, str) else target_equation
    return tuple(
        family
        for family in families
        if family_satisfies_equation(source, family)
        and not family_satisfies_equation(target, family)
    )


def build_lifting_family_profiles(
    equations: Sequence[str],
    *,
    families: Sequence[LiftingFamilyName] = ALL_LIFTING_FAMILIES,
    order4_max_id: int = 4694,
) -> list[LiftingFamilyProfile]:
    parsed_equations = [
        (eq_id, parse_law_text(equation))
        for eq_id, equation in enumerate(equations, start=1)
    ]
    law_count = len(parsed_equations)
    profiles: list[LiftingFamilyProfile] = []
    for family in families:
        source_ids = frozenset(
            eq_id
            for eq_id, equation in parsed_equations
            if family_satisfies_equation(equation, family)
        )
        target_ids = frozenset(
            eq_id
            for eq_id, _ in parsed_equations
            if eq_id not in source_ids
        )
        profiles.append(
            LiftingFamilyProfile(
                family=family,
                law_count=law_count,
                source_ids=source_ids,
                target_ids=target_ids,
                representative_pairs=_representative_pairs(
                    source_ids,
                    target_ids,
                    order4_max_id=order4_max_id,
                ),
            )
        )
    return profiles


def load_lifting_family_profiles(
    equations_path: Path = DEFAULT_EQUATIONS_PATH,
    *,
    families: Sequence[LiftingFamilyName] = ALL_LIFTING_FAMILIES,
    order4_max_id: int = 4694,
) -> list[LiftingFamilyProfile]:
    return build_lifting_family_profiles(
        read_equations(equations_path),
        families=families,
        order4_max_id=order4_max_id,
    )


def lifting_family_summary(
    profiles: Sequence[LiftingFamilyProfile],
    *,
    equations_path: Path | None = None,
) -> dict:
    return {
        "schema_version": 1,
        "equations_path": str(equations_path) if equations_path is not None else None,
        "law_count": profiles[0].law_count if profiles else 0,
        "families": [profile.to_json(include_ids=False) for profile in profiles],
    }


def _normal_form(expr: Expr, family: LiftingFamilyName) -> object:
    leaves = _leaf_sequence(expr)
    if family == "list_append":
        return leaves
    if family == "multiset_add":
        return tuple(sorted(Counter(leaves).items()))
    if family == "finset_union":
        return frozenset(leaves)
    if family == "left_projection":
        return leaves[0]
    if family == "right_projection":
        return leaves[-1]
    raise ValueError(f"unknown lifting family: {family}")


def _leaf_sequence(expr: Expr) -> tuple[str, ...]:
    if expr.kind == "var":
        assert expr.value is not None
        return (expr.value,)
    assert expr.left is not None
    assert expr.right is not None
    return (*_leaf_sequence(expr.left), *_leaf_sequence(expr.right))


def _representative_pairs(
    source_ids: frozenset[int],
    target_ids: frozenset[int],
    *,
    order4_max_id: int,
) -> dict[str, tuple[int, int] | None]:
    return {
        "order4_source_to_order4_target": _find_pair(
            source_ids,
            target_ids,
            source_order5=False,
            target_order5=False,
            order4_max_id=order4_max_id,
        ),
        "order4_source_to_order5_target": _find_pair(
            source_ids,
            target_ids,
            source_order5=False,
            target_order5=True,
            order4_max_id=order4_max_id,
        ),
        "order5_source_to_order4_target": _find_pair(
            source_ids,
            target_ids,
            source_order5=True,
            target_order5=False,
            order4_max_id=order4_max_id,
        ),
        "order5_source_to_order5_target": _find_pair(
            source_ids,
            target_ids,
            source_order5=True,
            target_order5=True,
            order4_max_id=order4_max_id,
        ),
    }


def _find_pair(
    source_ids: frozenset[int],
    target_ids: frozenset[int],
    *,
    source_order5: bool,
    target_order5: bool,
    order4_max_id: int,
) -> tuple[int, int] | None:
    sources = sorted(
        eq_id
        for eq_id in source_ids
        if (eq_id > order4_max_id) == source_order5
    )
    targets = sorted(
        eq_id
        for eq_id in target_ids
        if (eq_id > order4_max_id) == target_order5
    )
    for source_id in sources:
        for target_id in targets:
            if source_id != target_id:
                return (source_id, target_id)
    return None
