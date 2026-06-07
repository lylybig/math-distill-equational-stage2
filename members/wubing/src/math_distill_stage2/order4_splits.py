from __future__ import annotations

import gzip
import hashlib
import heapq
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Sequence, TypeVar

from math_distill_stage2.dataset_io import summarize_problem_rows, write_jsonl


DEFAULT_INPUT_DIR = Path("data/processed/order4_implication_problems")
DEFAULT_OUTPUT_DIR = Path("data/processed/order4_splits")


@dataclass(frozen=True)
class SplitSpec:
    name: str
    size: int
    answer_mode: str


DEFAULT_ORDER4_SPLIT_SPECS = [
    SplitSpec(name="dev_fast", size=2_000, answer_mode="balanced"),
    SplitSpec(name="dev_main", size=10_000, answer_mode="balanced"),
    SplitSpec(name="test_locked", size=50_000, answer_mode="balanced"),
    SplitSpec(name="stress_true", size=5_000, answer_mode="true"),
    SplitSpec(name="stress_false", size=5_000, answer_mode="false"),
    SplitSpec(name="label_probe_100k", size=100_000, answer_mode="natural"),
]

ID_BUCKETS = (
    (1, 500, "0001-0500"),
    (501, 1500, "0501-1500"),
    (1501, 3000, "1501-3000"),
    (3001, 4694, "3001-4694"),
)
T = TypeVar("T")


def problem_stratum(row: dict[str, Any]) -> tuple[str, str, str, str]:
    answer = "true" if row["answer"] is True else "false"
    return (
        answer,
        equation_id_bucket(int(row["eq1_id"])),
        equation_id_bucket(int(row["eq2_id"])),
        complexity_bucket(row),
    )


def equation_id_bucket(equation_id: int) -> str:
    for start, end, label in ID_BUCKETS:
        if start <= equation_id <= end:
            return label
    return "out-of-range"


def complexity_bucket(row: dict[str, Any]) -> str:
    ops = str(row["equation1"]).count("◇") + str(row["equation2"]).count("◇")
    if ops <= 4:
        return "low"
    if ops <= 6:
        return "medium"
    return "high"


def iter_order4_split_source(input_dir: Path) -> Iterator[dict[str, Any]]:
    manifest_path = input_dir / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        shard_paths = [input_dir / shard["path"] for shard in manifest["shards"]]
    else:
        shard_paths = sorted(input_dir.glob("part-*.jsonl*"))

    for path in shard_paths:
        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rt", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    yield json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid JSON at {path}:{line_number}") from exc


def build_order4_splits(
    *,
    input_dir: Path = DEFAULT_INPUT_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    specs: Sequence[SplitSpec] = tuple(DEFAULT_ORDER4_SPLIT_SPECS),
    seed: int = 20260508,
    overwrite: bool = False,
) -> dict[str, Any]:
    return build_order4_splits_from_row_factory(
        row_factory=lambda: iter_order4_split_source(input_dir),
        output_dir=output_dir,
        specs=specs,
        seed=seed,
        source=str(input_dir),
        overwrite=overwrite,
    )


def build_order4_splits_from_rows(
    rows: Sequence[dict[str, Any]],
    *,
    output_dir: Path,
    specs: Sequence[SplitSpec],
    seed: int,
    overwrite: bool = True,
) -> dict[str, Any]:
    return build_order4_splits_from_row_factory(
        row_factory=lambda: iter(rows),
        output_dir=output_dir,
        specs=specs,
        seed=seed,
        source="<in-memory>",
        overwrite=overwrite,
    )


def build_order4_splits_from_row_factory(
    *,
    row_factory,
    output_dir: Path,
    specs: Sequence[SplitSpec],
    seed: int,
    source: str,
    overwrite: bool,
) -> dict[str, Any]:
    _validate_specs(specs)
    _prepare_output_dir(output_dir, overwrite=overwrite)

    stratum_counts = Counter(problem_stratum(row) for row in row_factory())
    split_quotas = _allocate_split_quotas(stratum_counts, specs)
    stratum_needs = {
        stratum: sum(by_split.values())
        for stratum, by_split in split_quotas.items()
        if sum(by_split.values()) > 0
    }

    heaps: dict[tuple[str, str, str, str], list[tuple[int, str, dict[str, Any]]]] = {
        stratum: [] for stratum in stratum_needs
    }
    for row in row_factory():
        stratum = problem_stratum(row)
        need = stratum_needs.get(stratum, 0)
        if need == 0:
            continue
        score = _stable_score(seed, str(row["id"]))
        heap = heaps[stratum]
        entry = (-score, str(row["id"]), row)
        if len(heap) < need:
            heapq.heappush(heap, entry)
        elif score < -heap[0][0]:
            heapq.heapreplace(heap, entry)

    split_rows: dict[str, list[dict[str, Any]]] = {spec.name: [] for spec in specs}
    for stratum in sorted(stratum_needs):
        selected = sorted(heaps[stratum], key=lambda entry: (-entry[0], entry[1]))
        rows_for_stratum = [entry[2] for entry in selected]
        if len(rows_for_stratum) != stratum_needs[stratum]:
            raise ValueError(
                f"stratum {stratum} needed {stratum_needs[stratum]} rows, "
                f"selected {len(rows_for_stratum)}"
            )
        cursor = 0
        for spec in specs:
            quota = split_quotas[stratum].get(spec.name, 0)
            if quota:
                split_rows[spec.name].extend(rows_for_stratum[cursor : cursor + quota])
                cursor += quota

    for spec in specs:
        rows = split_rows[spec.name]
        if len(rows) != spec.size:
            raise ValueError(f"{spec.name}: expected {spec.size} rows, got {len(rows)}")
        rows.sort(key=_problem_sort_key)
        write_jsonl(output_dir / f"{spec.name}.jsonl", rows)

    manifest = {
        "schema_version": 1,
        "source": source,
        "output_dir": str(output_dir),
        "seed": seed,
        "split_specs": [spec.__dict__ for spec in specs],
        "stratify_by": ["answer", "eq1_bucket", "eq2_bucket", "complexity_bucket"],
        "strata": {
            _stratum_key(stratum): {
                "rows": count,
                "splits": {
                    split_name: count
                    for split_name, count in split_quotas.get(stratum, {}).items()
                    if count
                },
            }
            for stratum, count in sorted(stratum_counts.items())
        },
        "splits": {
            spec.name: summarize_problem_rows(split_rows[spec.name])
            for spec in specs
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return manifest


def _allocate_split_quotas(
    stratum_counts: Counter[tuple[str, str, str, str]],
    specs: Sequence[SplitSpec],
) -> dict[tuple[str, str, str, str], dict[str, int]]:
    remaining = Counter(stratum_counts)
    quotas: dict[tuple[str, str, str, str], dict[str, int]] = defaultdict(dict)

    for spec in specs:
        answer_targets = _answer_targets(spec, remaining)
        for answer, target in answer_targets.items():
            if target == 0:
                continue
            capacities = {
                stratum: count
                for stratum, count in remaining.items()
                if count > 0 and stratum[0] == answer
            }
            allocated = _allocate_proportional_counts(target, capacities)
            for stratum, count in allocated.items():
                if count:
                    quotas[stratum][spec.name] = count
                    remaining[stratum] -= count

    return quotas


def _answer_targets(
    spec: SplitSpec,
    remaining: Counter[tuple[str, str, str, str]],
) -> dict[str, int]:
    available = {
        "true": sum(count for stratum, count in remaining.items() if stratum[0] == "true"),
        "false": sum(count for stratum, count in remaining.items() if stratum[0] == "false"),
    }
    if spec.answer_mode == "balanced":
        true_target = spec.size // 2
        false_target = spec.size - true_target
        targets = {"true": true_target, "false": false_target}
    elif spec.answer_mode == "true":
        targets = {"true": spec.size, "false": 0}
    elif spec.answer_mode == "false":
        targets = {"true": 0, "false": spec.size}
    elif spec.answer_mode == "natural":
        allocated = _allocate_proportional_counts(spec.size, available)
        targets = {"true": allocated.get("true", 0), "false": allocated.get("false", 0)}
    else:
        raise ValueError(f"{spec.name}: unsupported answer_mode {spec.answer_mode!r}")

    for answer, target in targets.items():
        if target > available[answer]:
            raise ValueError(
                f"{spec.name}: requested {target} {answer} rows, "
                f"only {available[answer]} remain"
            )
    return targets


def _allocate_proportional_counts(total: int, capacities: dict[T, int]) -> dict[T, int]:
    capacity_total = sum(capacities.values())
    if total > capacity_total:
        raise ValueError(f"requested {total} rows from capacity {capacity_total}")
    if total == 0:
        return {key: 0 for key in capacities}
    if capacity_total == 0:
        raise ValueError("cannot allocate from empty capacities")

    exact = {key: total * capacity / capacity_total for key, capacity in capacities.items()}
    counts = {key: min(int(value), capacities[key]) for key, value in exact.items()}
    remainder = total - sum(counts.values())
    order = sorted(
        capacities,
        key=lambda key: (exact[key] - int(exact[key]), capacities[key], str(key)),
        reverse=True,
    )
    for key in order:
        if remainder == 0:
            break
        room = capacities[key] - counts[key]
        if room <= 0:
            continue
        take = min(room, remainder)
        counts[key] += take
        remainder -= take
    if remainder:
        raise ValueError(f"could not allocate {remainder} rows")
    return counts


def _stable_score(seed: int, row_id: str) -> int:
    digest = hashlib.blake2b(
        f"{seed}:{row_id}".encode("utf-8"),
        digest_size=8,
    ).digest()
    return int.from_bytes(digest, "big")


def _validate_specs(specs: Sequence[SplitSpec]) -> None:
    seen: set[str] = set()
    for spec in specs:
        if spec.size <= 0:
            raise ValueError(f"{spec.name}: size must be positive")
        if spec.name in seen:
            raise ValueError(f"duplicate split name: {spec.name}")
        seen.add(spec.name)


def _prepare_output_dir(output_dir: Path, *, overwrite: bool) -> None:
    if output_dir.exists() and any(output_dir.iterdir()) and not overwrite:
        raise FileExistsError(
            f"{output_dir} already contains files; pass overwrite=True to replace"
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    if overwrite:
        for path in output_dir.glob("*.jsonl"):
            path.unlink()
        manifest_path = output_dir / "manifest.json"
        if manifest_path.exists():
            manifest_path.unlink()


def _problem_sort_key(row: dict[str, Any]) -> tuple[int, int, str]:
    return int(row["eq1_id"]), int(row["eq2_id"]), str(row["id"])


def _stratum_key(stratum: tuple[str, str, str, str]) -> str:
    return "|".join(stratum)
