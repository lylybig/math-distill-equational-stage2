from __future__ import annotations

import gzip
import json
from contextlib import contextmanager
from dataclasses import dataclass
from itertools import permutations
from pathlib import Path
from typing import Iterator, Sequence, TextIO


DEFAULT_EQUATIONS_PATH = Path(
    "external/equational-theories-lean-stage2/examples/problems/eq_size5.txt"
)
DEFAULT_OUTPUT_DIR = Path("data/processed/order5_pair_problems")
VAR_NAMES = "xyzwuvrst"


@dataclass(frozen=True)
class ShardSummary:
    path: str
    rows: int
    unlabeled: int


def generate_equations_up_to_order(max_order: int) -> Iterator[str]:
    if max_order < 0:
        raise ValueError("max_order must be non-negative")
    for size in range(max_order + 1):
        yield from _generate_equations_of_order(size)


def read_equations(path: Path) -> list[str]:
    equations = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    if not equations:
        raise ValueError(f"no equations found in {path}")
    if any(not equation for equation in equations):
        raise ValueError(f"blank equation found in {path}")
    return equations


def iter_order_pair_rows(
    equations: Sequence[str],
    *,
    include_self: bool = False,
    max_rows: int | None = None,
) -> Iterator[dict]:
    emitted = 0
    for row_index, equation1 in enumerate(equations, start=1):
        for column_index, equation2 in enumerate(equations, start=1):
            if not include_self and row_index == column_index:
                continue
            yield {
                "id": f"{row_index}_{column_index}",
                "eq1_id": row_index,
                "eq2_id": column_index,
                "equation1": equation1,
                "equation2": equation2,
                "answer": None,
            }
            emitted += 1
            if max_rows is not None and emitted >= max_rows:
                return


def write_order5_pair_shards(
    *,
    output_dir: Path,
    rows_per_shard: int,
    equations_path: Path = DEFAULT_EQUATIONS_PATH,
    equations: Sequence[str] | None = None,
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

    laws = list(equations) if equations is not None else read_equations(equations_path)
    law_count = len(laws)
    expected_rows = law_count * law_count if include_self else law_count * (law_count - 1)
    if max_rows is not None:
        expected_rows = min(expected_rows, max_rows)

    suffix = ".jsonl.gz" if gzip_output else ".jsonl"
    total_rows = 0
    shard_index = -1
    shard_rows = 0
    shard_path: Path | None = None
    shard_handle: TextIO | None = None
    shard_context = None
    shard_summaries: list[ShardSummary] = []

    def close_current_shard() -> None:
        nonlocal shard_context, shard_handle, shard_rows, shard_path
        if shard_context is None:
            return
        assert shard_handle is not None
        assert shard_path is not None
        shard_context.__exit__(None, None, None)
        shard_summaries.append(
            ShardSummary(
                path=str(shard_path.relative_to(output_dir)),
                rows=shard_rows,
                unlabeled=shard_rows,
            )
        )
        shard_context = None
        shard_handle = None
        shard_rows = 0
        shard_path = None

    try:
        for row in iter_order_pair_rows(laws, include_self=include_self, max_rows=max_rows):
            if shard_handle is None or shard_rows >= rows_per_shard:
                close_current_shard()
                shard_index += 1
                shard_path = output_dir / f"part-{shard_index:05d}{suffix}"
                shard_context = _open_output_text(shard_path, gzip_output=gzip_output)
                shard_handle = shard_context.__enter__()
            shard_handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
            shard_handle.write("\n")
            shard_rows += 1
            total_rows += 1
    finally:
        close_current_shard()

    manifest = {
        "schema": ["id", "eq1_id", "eq2_id", "equation1", "equation2", "answer"],
        "format": "jsonl.gz" if gzip_output else "jsonl",
        "record_format": "sample_200 compatible unlabeled object per JSONL line",
        "answer_rule": "unlabeled order<=5 pair index; answer is null",
        "equations_path": str(equations_path) if equations is None else "<in-memory>",
        "law_count": law_count,
        "include_self": include_self,
        "expected_rows": expected_rows,
        "rows": total_rows,
        "unlabeled": total_rows,
        "rows_per_shard": rows_per_shard,
        "shard_count": len(shard_summaries),
        "shards": [summary.__dict__ for summary in shard_summaries],
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    return manifest


@contextmanager
def _open_output_text(path: Path, *, gzip_output: bool) -> Iterator[TextIO]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if gzip_output:
        with gzip.open(path, "wt", encoding="utf-8", newline="\n") as handle:
            yield handle
    else:
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            yield handle


def _generate_shapes(size: int):
    if size == 0:
        yield "."
    for left_size in range(size):
        for left in _generate_shapes(left_size):
            for right in _generate_shapes(size - 1 - left_size):
                yield (left, right)


def _exprs_with_shape(shape, used_vars: int):
    if shape == ".":
        for var in range(used_vars + 1):
            yield var, max(var + 1, used_vars)
    else:
        left, right = shape
        for left_expr, used_vars_after_left in _exprs_with_shape(left, used_vars):
            for right_expr, used_vars_after_right in _exprs_with_shape(
                right, used_vars_after_left
            ):
                yield (left_expr, right_expr), used_vars_after_right


def _rename_vars(expr, perm):
    if isinstance(expr, int):
        return perm[expr]
    left, right = expr
    return (_rename_vars(left, perm), _rename_vars(right, perm))


def _equation_symmetries_one_way(lhs, rhs, n_vars: int):
    for renaming in permutations(range(n_vars)):
        yield _rename_vars(lhs, renaming), _rename_vars(rhs, renaming)


def _equation_symmetries(lhs, rhs, n_vars: int):
    yield from _equation_symmetries_one_way(lhs, rhs, n_vars)
    yield from _equation_symmetries_one_way(rhs, lhs, n_vars)


def _generate_equations_of_order(size: int) -> Iterator[str]:
    seen = set()
    for lhs_size in range(size + 1):
        for lhs_shape in _generate_shapes(lhs_size):
            for rhs_shape in _generate_shapes(size - lhs_size):
                for lhs, used_vars in _exprs_with_shape(lhs_shape, 0):
                    for rhs, all_used_vars in _exprs_with_shape(rhs_shape, used_vars):
                        if any(
                            symmetry in seen
                            for symmetry in _equation_symmetries(lhs, rhs, all_used_vars)
                        ):
                            continue
                        if lhs == rhs and not isinstance(lhs, int):
                            continue
                        seen.add((lhs, rhs))
                        yield f"{_format_expr(lhs)} = {_format_expr(rhs)}"


def _format_expr(expr, *, outermost: bool = True) -> str:
    if isinstance(expr, int):
        return VAR_NAMES[expr]
    left, right = expr
    result = (
        f"{_format_expr(left, outermost=False)} ◇ "
        f"{_format_expr(right, outermost=False)}"
    )
    return result if outermost else f"({result})"
