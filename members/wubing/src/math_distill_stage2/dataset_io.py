from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


class CountMismatchError(ValueError):
    """Raised when a downloaded subset does not match the expected row count."""


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                rows.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON at {path}:{line_number}") from exc
    return rows


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def validate_expected_counts(rows_by_subset: dict[str, list[dict]], expected: dict[str, int]) -> None:
    for subset, expected_count in expected.items():
        actual = len(rows_by_subset.get(subset, []))
        if actual != expected_count:
            raise CountMismatchError(
                f"{subset}: expected {expected_count} rows, found {actual}"
            )


def summarize_problem_rows(rows: list[dict]) -> dict[str, int]:
    true_count = sum(1 for row in rows if row.get("answer") is True)
    false_count = sum(1 for row in rows if row.get("answer") is False)
    return {
        "rows": len(rows),
        "true": true_count,
        "false": false_count,
        "unique_eq1": len({row.get("eq1_id") for row in rows}),
        "unique_eq2": len({row.get("eq2_id") for row in rows}),
    }
