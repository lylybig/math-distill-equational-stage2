from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from math_distill_stage2.dataset_io import read_jsonl
from math_distill_stage2.order5_coverage_profile import (
    read_coverage_profile,
    source_target_delta_summary_from_profile,
)


DEFAULT_ETP_FACTS_PATH = Path("data/processed/etp/etp_facts.jsonl")
DEFAULT_CURRENT_COVERAGE_PROFILE_PATH = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "current_coverage_profile_v29_active_true_tail_rescore_20260528.json"
)


@dataclass(frozen=True)
class EtpCounterexampleFactCandidate:
    name: str
    filename: str
    line: int | None
    source_ids: frozenset[int]
    target_ids: frozenset[int]
    finite_flag: bool
    candidate_family: str

    @property
    def candidate_key(self) -> str:
        return f"false.etp.{self.candidate_family}.{_slugify(self.name)}"

    @property
    def raw_coverage_count(self) -> int:
        return len(self.source_ids) * len(self.target_ids) - len(
            self.source_ids & self.target_ids
        )

    def to_json(self, *, include_ids: bool = True) -> dict:
        row = {
            "schema_version": 1,
            "candidate_key": self.candidate_key,
            "strategy_key": self.candidate_key,
            "verdict": "false",
            "certificate_family": (
                "infinite_magma_countermodel"
                if self.candidate_family == "infmodel"
                else "etp_counterexample_fact"
            ),
            "certificate_generator": "order5_etp_infinite_facts",
            "etp_name": self.name,
            "etp_reference_file": self.filename,
            "etp_reference_line": self.line,
            "etp_finite_flag": self.finite_flag,
            "source_count": len(self.source_ids),
            "target_count": len(self.target_ids),
            "raw_coverage": self.raw_coverage_count,
            "coverage_kind": "source_target_sets",
        }
        if include_ids:
            row["source_ids"] = sorted(self.source_ids)
            row["target_ids"] = sorted(self.target_ids)
        return row


def load_etp_counterexample_fact_candidates(
    facts_path: Path = DEFAULT_ETP_FACTS_PATH,
    *,
    name_prefixes: Sequence[str] = ("InfModel.",),
    max_equation_id: int = 62576,
    candidate_family: str = "infmodel",
) -> list[EtpCounterexampleFactCandidate]:
    return build_etp_counterexample_fact_candidates(
        read_jsonl(facts_path),
        name_prefixes=name_prefixes,
        max_equation_id=max_equation_id,
        candidate_family=candidate_family,
    )


def build_etp_counterexample_fact_candidates(
    fact_rows: Iterable[dict],
    *,
    name_prefixes: Sequence[str] = ("InfModel.",),
    max_equation_id: int = 62576,
    candidate_family: str = "infmodel",
) -> list[EtpCounterexampleFactCandidate]:
    prefixes = tuple(name_prefixes)
    candidates: list[EtpCounterexampleFactCandidate] = []
    for row in fact_rows:
        name = str(row.get("name") or "")
        if prefixes and not name.startswith(prefixes):
            continue
        source_ids = frozenset(
            int(eq_id)
            for eq_id in row.get("satisfied_ids", [])
            if int(eq_id) <= max_equation_id
        )
        target_ids = frozenset(
            int(eq_id)
            for eq_id in row.get("refuted_ids", [])
            if int(eq_id) <= max_equation_id
        )
        if not source_ids or not target_ids:
            continue
        candidates.append(
            EtpCounterexampleFactCandidate(
                name=name,
                filename=str(row.get("filename") or ""),
                line=row.get("line"),
                source_ids=source_ids,
                target_ids=target_ids,
                finite_flag=bool(row.get("finite")),
                candidate_family=candidate_family,
            )
        )
    return candidates


def annotate_candidates_with_profile_delta(
    candidates: Sequence[EtpCounterexampleFactCandidate],
    *,
    coverage_profile_path: Path = DEFAULT_CURRENT_COVERAGE_PROFILE_PATH,
    include_ids: bool = True,
) -> list[dict]:
    coverage_profile = read_coverage_profile(coverage_profile_path)
    rows = []
    for candidate in candidates:
        row = candidate.to_json(include_ids=include_ids)
        row["coverage_profile_path"] = str(coverage_profile_path)
        row["current_delta"] = source_target_delta_summary_from_profile(
            coverage_profile,
            source_ids=candidate.source_ids,
            target_ids=candidate.target_ids,
            verdict=False,
        )
        rows.append(row)
    return rows


def summarize_etp_counterexample_candidates(rows: Sequence[dict]) -> dict:
    return {
        "schema_version": 1,
        "candidate_count": len(rows),
        "raw_coverage": sum(int(row.get("raw_coverage", 0)) for row in rows),
        "union_increment": sum(
            int((row.get("current_delta") or {}).get("union_increment", 0))
            for row in rows
        ),
        "conflict_increment": sum(
            int((row.get("current_delta") or {}).get("conflict_increment", 0))
            for row in rows
        ),
        "candidates": [
            {
                key: row[key]
                for key in (
                    "candidate_key",
                    "etp_name",
                    "source_ids",
                    "target_ids",
                    "raw_coverage",
                    "current_delta",
                )
                if key in row
            }
            for row in rows
        ],
    }


def _slugify(value: str) -> str:
    return (
        value.replace(".", "_")
        .replace("/", "_")
        .replace(" ", "_")
        .replace(":", "_")
    )
