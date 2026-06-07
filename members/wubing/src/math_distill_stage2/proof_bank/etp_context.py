from __future__ import annotations

from pathlib import Path
from typing import Any

from math_distill_stage2.dataset_io import read_jsonl
from math_distill_stage2.implication_graph import ImplicationGraph


DEFAULT_ETP_IMPLICATIONS_PATH = Path("data/processed/etp/etp_implications.jsonl")
DEFAULT_ETP_BLUEPRINT_REFERENCE = Path("data/raw/references/etp/blueprint.pdf")


def find_etp_implication_context(
    problem: dict[str, Any],
    *,
    implications_path: Path | None = DEFAULT_ETP_IMPLICATIONS_PATH,
    max_edges: int = 4,
) -> dict[str, Any] | None:
    if implications_path is None or not implications_path.exists():
        return None
    source = _int_or_none(problem.get("eq1_id"))
    target = _int_or_none(problem.get("eq2_id"))
    if source is None or target is None:
        return None

    rows = [
        row
        for row in read_jsonl(implications_path)
        if row.get("proven") is True and row.get("finite") is False
    ]
    edge_path = ImplicationGraph.from_rows(rows).find_edge_path(source, target)
    if not edge_path or len(edge_path) > max_edges:
        return None

    id_path = [source, *[int(edge["rhs_id"]) for edge in edge_path]]
    return {
        "kind": "direct" if len(edge_path) == 1 else "path",
        "source": str(implications_path),
        "blueprint_reference": str(DEFAULT_ETP_BLUEPRINT_REFERENCE),
        "path": id_path,
        "edges": [_summarize_edge(edge) for edge in edge_path],
    }


def _summarize_edge(edge: dict[str, Any]) -> dict[str, Any]:
    return {
        "lhs_id": int(edge["lhs_id"]),
        "rhs_id": int(edge["rhs_id"]),
        "name": edge.get("name"),
        "filename": edge.get("filename"),
        "line": edge.get("line"),
        "finite": edge.get("finite"),
    }


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
