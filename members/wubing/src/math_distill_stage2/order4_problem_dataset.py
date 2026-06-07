from __future__ import annotations

import csv
import gzip
import json
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence, TextIO


DEFAULT_EQUATIONS_PATH = Path("external/equational_theories/data/equations.txt")
DEFAULT_IMPLICATIONS_CSV_PATH = Path(
    "external/equational_theories/scripts/predictor/raw_implications.csv"
)
DEFAULT_OUTPUT_DIR = Path("data/processed/order4_implication_problems")


@dataclass(frozen=True)
class ShardSummary:
    path: str
    rows: int
    true: int
    false: int


def read_equations(path: Path) -> list[str]:
    equations = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    if not equations:
        raise ValueError(f"no equations found in {path}")
    if any(not equation for equation in equations):
        raise ValueError(f"blank equation found in {path}")
    return equations


def implication_value_to_answer(value: int | str) -> bool:
    parsed = int(value)
    if parsed == 0:
        raise ValueError("raw implication matrix value must be nonzero")
    return parsed > 0


def make_problem_row(
    eq1_id: int,
    eq2_id: int,
    equation1: str,
    equation2: str,
    answer: bool,
) -> dict:
    label = "true" if answer else "false"
    return {
        "id": f"{label}_{eq1_id}_{eq2_id}",
        "eq1_id": eq1_id,
        "eq2_id": eq2_id,
        "equation1": equation1,
        "equation2": equation2,
        "answer": answer,
    }


def iter_order4_problem_rows(
    equations: Sequence[str],
    implication_rows: Iterable[Sequence[int | str]],
    *,
    include_self: bool = False,
    max_rows: int | None = None,
) -> Iterator[dict]:
    law_count = len(equations)
    emitted = 0
    row_count = 0

    for row_index, raw_values in enumerate(implication_rows, start=1):
        row_count = row_index
        if row_index > law_count:
            raise ValueError(
                f"implication matrix has more rows than equations: row {row_index} > {law_count}"
            )
        if len(raw_values) != law_count:
            raise ValueError(
                f"implication matrix row {row_index} has {len(raw_values)} columns; "
                f"expected {law_count}"
            )

        equation1 = equations[row_index - 1]
        for column_index, value in enumerate(raw_values, start=1):
            if not include_self and row_index == column_index:
                continue
            answer = implication_value_to_answer(value)
            yield make_problem_row(
                row_index,
                column_index,
                equation1,
                equations[column_index - 1],
                answer,
            )
            emitted += 1
            if max_rows is not None and emitted >= max_rows:
                return

    if row_count != law_count:
        raise ValueError(
            f"implication matrix has {row_count} rows; expected {law_count}"
        )


def iter_implication_csv_rows(path: Path) -> Iterator[list[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        yield from csv.reader(handle)


@contextmanager
def open_output_text(path: Path, *, gzip_output: bool) -> Iterator[TextIO]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if gzip_output:
        with gzip.open(path, "wt", encoding="utf-8", newline="\n") as handle:
            yield handle
    else:
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            yield handle


def write_order4_problem_shards(
    *,
    equations_path: Path,
    implications_csv_path: Path,
    output_dir: Path,
    rows_per_shard: int,
    gzip_output: bool = True,
    include_self: bool = False,
    max_rows: int | None = None,
    overwrite: bool = False,
) -> dict:
    if rows_per_shard <= 0:
        raise ValueError("rows_per_shard must be positive")
    if max_rows is not None and max_rows <= 0:
        raise ValueError("max_rows must be positive when provided")
    if output_dir.exists() and any(output_dir.iterdir()) and not overwrite:
        raise FileExistsError(
            f"{output_dir} already contains files; pass overwrite=True to replace shards"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    if overwrite:
        for path in output_dir.glob("part-*.jsonl*"):
            path.unlink()
        manifest_path = output_dir / "manifest.json"
        if manifest_path.exists():
            manifest_path.unlink()

    equations = read_equations(equations_path)
    law_count = len(equations)
    expected_rows = law_count * law_count if include_self else law_count * (law_count - 1)
    if max_rows is not None:
        expected_rows = min(expected_rows, max_rows)

    suffix = ".jsonl.gz" if gzip_output else ".jsonl"
    shard_summaries: list[ShardSummary] = []
    total_rows = 0
    total_true = 0
    total_false = 0
    shard_index = -1
    shard_handle: TextIO | None = None
    shard_context = None
    shard_rows = 0
    shard_true = 0
    shard_false = 0
    shard_path: Path | None = None

    def close_current_shard() -> None:
        nonlocal shard_context, shard_handle, shard_rows, shard_true, shard_false, shard_path
        if shard_context is None:
            return
        assert shard_handle is not None
        assert shard_path is not None
        shard_context.__exit__(None, None, None)
        shard_summaries.append(
            ShardSummary(
                path=str(shard_path.relative_to(output_dir)),
                rows=shard_rows,
                true=shard_true,
                false=shard_false,
            )
        )
        shard_context = None
        shard_handle = None
        shard_path = None
        shard_rows = 0
        shard_true = 0
        shard_false = 0

    try:
        rows = iter_order4_problem_rows(
            equations,
            iter_implication_csv_rows(implications_csv_path),
            include_self=include_self,
            max_rows=max_rows,
        )
        for row in rows:
            if shard_handle is None or shard_rows >= rows_per_shard:
                close_current_shard()
                shard_index += 1
                shard_path = output_dir / f"part-{shard_index:05d}{suffix}"
                shard_context = open_output_text(shard_path, gzip_output=gzip_output)
                shard_handle = shard_context.__enter__()

            shard_handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
            shard_handle.write("\n")
            shard_rows += 1
            total_rows += 1
            if row["answer"] is True:
                shard_true += 1
                total_true += 1
            else:
                shard_false += 1
                total_false += 1
    finally:
        close_current_shard()

    manifest = {
        "schema": ["id", "eq1_id", "eq2_id", "equation1", "equation2", "answer"],
        "format": "jsonl.gz" if gzip_output else "jsonl",
        "record_format": "sample_200 compatible object per JSONL line",
        "answer_rule": "raw_implications.csv value > 0 is true; value < 0 is false",
        "equations_path": str(equations_path),
        "implications_csv_path": str(implications_csv_path),
        "law_count": law_count,
        "include_self": include_self,
        "expected_rows": expected_rows,
        "rows": total_rows,
        "true": total_true,
        "false": total_false,
        "rows_per_shard": rows_per_shard,
        "shard_count": len(shard_summaries),
        "shards": [summary.__dict__ for summary in shard_summaries],
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    return manifest
