# Order5 Paircheck Bank Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible `false.finmodel.paircheck.bank` pipeline for order5 unresolved pairs, with remote-only official judge smoke.

**Architecture:** Add a focused `order5_paircheck_bank` module for sampling unresolved pairs, scoring finite magma model pools, writing verified bank rows, and preparing remote judge smoke inputs. Keep registry integration separate through an `ExplicitPairsRule` so sparse pair coverage is not conflated with source-target setcheck coverage.

**Tech Stack:** Python standard library, existing `FiniteMagma`, `Order5StrategyRegistry`, `order5_pair_space`, `finmodel_false_judge_code`, JSONL artifacts, pytest, remote simple-api backend pool `http://10.220.69.153:8888,http://10.220.69.172:8888`.

---

## File Structure

- Create: `src/math_distill_stage2/order5_paircheck_bank.py`
  - Owns candidate sampling, model pool normalization, paircheck verification, bank summary, and smoke input generation.
- Create: `scripts/data/build_order5_paircheck_bank.py`
  - CLI entrypoint for local Python-only bank construction and smoke input generation.
- Create: `scripts/lean_certificates/verify_order5_paircheck_remote_smoke.py`
  - Remote-only smoke verifier using `make_remote_simple_api_batch_judge`.
- Create: `tests/data/test_order5_paircheck_bank.py`
  - Focused tests for sampler, model pool matching, schema, dedupe, and smoke input shape.
- Modify: `src/math_distill_stage2/order5_strategy_registry.py`
  - Add `ExplicitPairsRule` and mixed-rule union support.
- Modify: `tests/data/test_order5_strategy_registry.py`
  - Add focused coverage/union/conflict tests for `ExplicitPairsRule`.
- Generated outputs:
  - `data/processed/order5_paircheck_bank/candidate_pairs.jsonl`
  - `data/processed/order5_paircheck_bank/model_pool.jsonl`
  - `data/processed/order5_paircheck_bank/countermodels.jsonl`
  - `data/processed/order5_paircheck_bank/verified_bank.jsonl`
  - `data/processed/order5_paircheck_bank/candidate_increment_bank.jsonl`
  - `data/processed/order5_paircheck_bank/official_smoke_input.jsonl`
  - `data/processed/order5_paircheck_bank/bank_summary.json`

## Task 1: Unresolved Candidate Sampler

**Files:**
- Create: `src/math_distill_stage2/order5_paircheck_bank.py`
- Create: `tests/data/test_order5_paircheck_bank.py`

- [x] **Step 1: Write failing sampler tests**

Add this to `tests/data/test_order5_paircheck_bank.py`:

```python
from pathlib import Path

from math_distill_stage2.order5_pair_space import ids_to_pair_index
from math_distill_stage2.order5_paircheck_bank import sample_unresolved_pairs
from math_distill_stage2.order5_strategy_registry import (
    CoverageStrategy,
    Order5StrategyRegistry,
    SourceTargetSetsRule,
)


def test_sample_unresolved_pairs_excludes_existing_false_and_true_coverage():
    registry = Order5StrategyRegistry(
        law_count=6,
        strategies=[
            CoverageStrategy(
                strategy_key="false.covered",
                strategy_version=1,
                verdict=False,
                priority=10,
                coverage_rule=SourceTargetSetsRule(
                    source_ids=frozenset({1}),
                    target_ids=frozenset({4}),
                ),
                certificate_family="false_family",
            ),
            CoverageStrategy(
                strategy_key="true.covered",
                strategy_version=1,
                verdict=True,
                priority=20,
                coverage_rule=SourceTargetSetsRule(
                    source_ids=frozenset({2}),
                    target_ids=frozenset({5}),
                ),
                certificate_family="true_family",
            ),
        ],
    )

    rows = sample_unresolved_pairs(
        registry=registry,
        order4_max_id=3,
        size=10,
        seed=1,
    )
    pairs = {(row["eq1_id"], row["eq2_id"]) for row in rows}

    assert (1, 4) not in pairs
    assert (2, 5) not in pairs
    assert all(eq1 != eq2 for eq1, eq2 in pairs)
    assert {row["stratum"] for row in rows} <= {
        "order4_source_to_order5_target",
        "order5_source_to_order4_target",
        "order5_source_to_order5_target",
    }


def test_sample_unresolved_pairs_records_pair_index():
    registry = Order5StrategyRegistry(law_count=5, strategies=[])

    [row] = sample_unresolved_pairs(
        registry=registry,
        order4_max_id=2,
        size=1,
        seed=7,
    )

    assert row["pair_index"] == ids_to_pair_index(
        row["eq1_id"],
        row["eq2_id"],
        law_count=5,
    )
```

- [x] **Step 2: Run tests to verify failure**

Run:

```bash
PYTHONPATH=src pytest tests/data/test_order5_paircheck_bank.py -q
```

Expected: fail with `ModuleNotFoundError` or missing `sample_unresolved_pairs`.

- [x] **Step 3: Implement sampler**

Create `src/math_distill_stage2/order5_paircheck_bank.py` with:

```python
from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from math_distill_stage2.order5_pair_space import ids_to_pair_index
from math_distill_stage2.order5_strategy_registry import Order5StrategyRegistry


ORDER4_TO_ORDER5 = "order4_source_to_order5_target"
ORDER5_TO_ORDER4 = "order5_source_to_order4_target"
ORDER5_TO_ORDER5 = "order5_source_to_order5_target"
PAIRCHECK_STRATEGY_KEY = "false.finmodel.paircheck.bank"


def pair_stratum(eq1_id: int, eq2_id: int, *, order4_max_id: int) -> str | None:
    source_order5 = eq1_id > order4_max_id
    target_order5 = eq2_id > order4_max_id
    if source_order5 and target_order5:
        return ORDER5_TO_ORDER5
    if source_order5:
        return ORDER5_TO_ORDER4
    if target_order5:
        return ORDER4_TO_ORDER5
    return None


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
    attempts = 0
    ceiling = max_scan_attempts or max(size * 200, 10_000)
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
```

- [x] **Step 4: Run tests to verify pass**

Run:

```bash
PYTHONPATH=src pytest tests/data/test_order5_paircheck_bank.py -q
```

Expected: pass.

## Task 2: Model Pool Matching

**Files:**
- Modify: `src/math_distill_stage2/order5_paircheck_bank.py`
- Modify: `tests/data/test_order5_paircheck_bank.py`

- [x] **Step 1: Write failing model matching test**

Append:

```python
from math_distill_stage2.equations import parse_equation
from math_distill_stage2.order5_paircheck_bank import (
    PaircheckModel,
    find_paircheck_countermodels,
)


def test_find_paircheck_countermodels_uses_finite_magma_semantics():
    equations = {
        1: parse_equation("x * y = x"),
        2: parse_equation("x * y = y"),
        3: parse_equation("x = x"),
    }
    candidates = [
        {"pair_index": 0, "eq1_id": 1, "eq2_id": 2, "stratum": "order4_source_to_order5_target"},
        {"pair_index": 1, "eq1_id": 3, "eq2_id": 1, "stratum": "order5_source_to_order4_target"},
    ]
    model = PaircheckModel(
        label="fin2_left_projection",
        table=((0, 0), (1, 1)),
        source="test",
    )

    rows = find_paircheck_countermodels(
        candidate_pairs=candidates,
        equations=equations,
        models=[model],
    )

    assert rows == [
        {
            "pair_index": 0,
            "eq1_id": 1,
            "eq2_id": 2,
            "stratum": "order4_source_to_order5_target",
            "model_label": "fin2_left_projection",
            "model_source": "test",
            "order": 2,
            "table": [[0, 0], [1, 1]],
            "python_verified": True,
        }
    ]
```

- [x] **Step 2: Run the failing test**

Run:

```bash
PYTHONPATH=src pytest tests/data/test_order5_paircheck_bank.py::test_find_paircheck_countermodels_uses_finite_magma_semantics -q
```

Expected: fail with missing `PaircheckModel` or `find_paircheck_countermodels`.

- [x] **Step 3: Implement model matching**

Add to `src/math_distill_stage2/order5_paircheck_bank.py`:

```python
from math_distill_stage2.counterexample.finite_magma import FiniteMagma
from math_distill_stage2.equations import Equation


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


def find_paircheck_countermodels(
    *,
    candidate_pairs: Sequence[dict],
    equations: dict[int, Equation],
    models: Sequence[PaircheckModel],
) -> list[dict]:
    rows: list[dict] = []
    seen_pairs: set[int] = set()
    for pair in candidate_pairs:
        if int(pair["pair_index"]) in seen_pairs:
            continue
        eq1_id = int(pair["eq1_id"])
        eq2_id = int(pair["eq2_id"])
        for model in models:
            magma = FiniteMagma(order=model.order, table=model.table)
            if magma.satisfies(equations[eq1_id]) and not magma.satisfies(equations[eq2_id]):
                seen_pairs.add(int(pair["pair_index"]))
                rows.append(
                    {
                        "pair_index": int(pair["pair_index"]),
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
```

- [x] **Step 4: Run tests**

Run:

```bash
PYTHONPATH=src pytest tests/data/test_order5_paircheck_bank.py -q
```

Expected: pass.

## Task 3: Bank Writer And CLI

**Files:**
- Modify: `src/math_distill_stage2/order5_paircheck_bank.py`
- Create: `scripts/data/build_order5_paircheck_bank.py`
- Modify: `tests/data/test_order5_paircheck_bank.py`

- [x] **Step 1: Write failing bank output test**

Append:

```python
import json

from math_distill_stage2.order5_paircheck_bank import write_paircheck_bank


def test_write_paircheck_bank_writes_deduped_rows_and_summary(tmp_path: Path):
    rows = [
        {
            "pair_index": 5,
            "eq1_id": 1,
            "eq2_id": 2,
            "stratum": "order4_source_to_order5_target",
            "model_label": "m",
            "model_source": "test",
            "order": 2,
            "table": [[0, 0], [1, 1]],
            "python_verified": True,
        },
        {
            "pair_index": 5,
            "eq1_id": 1,
            "eq2_id": 2,
            "stratum": "order4_source_to_order5_target",
            "model_label": "m",
            "model_source": "test",
            "order": 2,
            "table": [[0, 0], [1, 1]],
            "python_verified": True,
        },
    ]

    summary = write_paircheck_bank(rows, output_dir=tmp_path)

    written = [
        json.loads(line)
        for line in (tmp_path / "verified_bank.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert summary["written"] == 1
    assert written[0]["strategy_key"] == "false.finmodel.paircheck.bank"
    assert written[0]["table_sha256"]
    assert (tmp_path / "bank_summary.json").exists()
```

- [x] **Step 2: Run failing test**

Run:

```bash
PYTHONPATH=src pytest tests/data/test_order5_paircheck_bank.py::test_write_paircheck_bank_writes_deduped_rows_and_summary -q
```

Expected: fail with missing `write_paircheck_bank`.

- [x] **Step 3: Implement bank writer**

Add to `src/math_distill_stage2/order5_paircheck_bank.py`:

```python
import hashlib
import json
from collections import Counter


def table_sha256(table: Sequence[Sequence[int]]) -> str:
    payload = json.dumps(table, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def write_jsonl(path: Path, rows: Sequence[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
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
    output_rows = list(deduped.values())
    output_rows.sort(key=lambda row: row["pair_index"])
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
```

- [x] **Step 4: Add CLI skeleton**

Create `scripts/data/build_order5_paircheck_bank.py`:

```python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))

from math_distill_stage2.order5_paircheck_bank import write_paircheck_bank


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--countermodels", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed/order5_paircheck_bank"),
    )
    args = parser.parse_args()
    rows = [
        json.loads(line)
        for line in args.countermodels.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    summary = write_paircheck_bank(rows, output_dir=args.output_dir)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
```

- [x] **Step 5: Run tests and CLI help**

Run:

```bash
PYTHONPATH=src pytest tests/data/test_order5_paircheck_bank.py -q
python scripts/data/build_order5_paircheck_bank.py --help
```

Expected: tests pass and help exits `0`.

## Task 4: Remote Smoke Input Generation

**Files:**
- Modify: `src/math_distill_stage2/order5_paircheck_bank.py`
- Modify: `tests/data/test_order5_paircheck_bank.py`

- [x] **Step 1: Write failing smoke input test**

Append:

```python
from math_distill_stage2.order5_paircheck_bank import build_remote_smoke_records


def test_build_remote_smoke_records_wraps_false_judge_answer():
    bank_rows = [
        {
            "pair_index": 5,
            "eq1_id": 1,
            "eq2_id": 2,
            "stratum": "order4_source_to_order5_target",
            "order": 2,
            "table": [[0, 0], [1, 1]],
            "table_sha256": "abc",
            "python_verified": True,
            "strategy_key": "false.finmodel.paircheck.bank",
        }
    ]
    equations = {1: "x * y = x", 2: "x * y = y"}

    [record] = build_remote_smoke_records(bank_rows=bank_rows, equations=equations, limit=1)

    assert record["id"] == "paircheck_1_2"
    assert record["problem"]["answer"] is False
    assert record["answer"]["call"] == "judge"
    assert record["answer"]["verdict"] == "false"
    assert "def submission" in record["answer"]["code"]
    assert "JudgeProblem" in record["answer"]["code"]
```

- [x] **Step 2: Run failing test**

Run:

```bash
PYTHONPATH=src pytest tests/data/test_order5_paircheck_bank.py::test_build_remote_smoke_records_wraps_false_judge_answer -q
```

Expected: fail with missing `build_remote_smoke_records`.

- [x] **Step 3: Implement smoke record builder**

Add to `src/math_distill_stage2/order5_paircheck_bank.py`:

```python
from math_distill_stage2.order5_strategy_registry import finmodel_false_judge_code


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
        table = tuple(tuple(int(value) for value in table_row) for table_row in row["table"])
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
```

- [x] **Step 4: Run tests**

Run:

```bash
PYTHONPATH=src pytest tests/data/test_order5_paircheck_bank.py -q
```

Expected: pass.

## Task 5: ExplicitPairsRule Registry Support

**Files:**
- Modify: `src/math_distill_stage2/order5_strategy_registry.py`
- Modify: `tests/data/test_order5_strategy_registry.py`

- [x] **Step 1: Write failing registry test**

Append to `tests/data/test_order5_strategy_registry.py`:

```python
def test_explicit_pairs_rule_counts_and_covers_sparse_pairs():
    rule = strategy_registry_module.ExplicitPairsRule(
        pair_indexes=frozenset({0, 3}),
        law_count=3,
    )

    assert rule.coverage_kind == "explicit_pairs"
    assert rule.coverage_count() == 2
    assert rule.covers(1, 2)
    assert rule.covers(2, 1)
    assert not rule.covers(1, 3)
```

- [x] **Step 2: Run failing test**

Run:

```bash
PYTHONPATH=src pytest tests/data/test_order5_strategy_registry.py::test_explicit_pairs_rule_counts_and_covers_sparse_pairs -q
```

Expected: fail with missing `ExplicitPairsRule`.

- [x] **Step 3: Implement `ExplicitPairsRule`**

Add near `SourceTargetSetsRule` in `src/math_distill_stage2/order5_strategy_registry.py`:

```python
@dataclass(frozen=True)
class ExplicitPairsRule:
    pair_indexes: frozenset[int]
    law_count: int

    @property
    def coverage_kind(self) -> str:
        return "explicit_pairs"

    def covers(self, eq1_id: int, eq2_id: int) -> bool:
        if eq1_id == eq2_id:
            return False
        pair_index = ids_to_pair_index(eq1_id, eq2_id, law_count=self.law_count)
        return pair_index in self.pair_indexes

    def coverage_count(self) -> int:
        return len(self.pair_indexes)

    def iter_covered_pairs(self) -> Iterable[tuple[int, int]]:
        for pair_index in sorted(self.pair_indexes):
            yield pair_index_to_ids(pair_index, law_count=self.law_count)

    def manifest_fragment(self) -> dict:
        return {
            "coverage_kind": self.coverage_kind,
            "pair_count": len(self.pair_indexes),
            "coverage_count": self.coverage_count(),
        }
```

Update the `CoverageStrategy.coverage_rule` type annotation to accept both rule types:

```python
coverage_rule: SourceTargetSetsRule | ExplicitPairsRule
```

- [x] **Step 4: Run focused registry test**

Run:

```bash
PYTHONPATH=src pytest tests/data/test_order5_strategy_registry.py::test_explicit_pairs_rule_counts_and_covers_sparse_pairs -q
```

Expected: pass.

## Task 6: Mixed Union Support

**Files:**
- Modify: `src/math_distill_stage2/order5_strategy_registry.py`
- Modify: `tests/data/test_order5_strategy_registry.py`

- [x] **Step 1: Write failing mixed union test**

Append:

```python
def test_registry_summary_counts_explicit_pairs_with_source_target_rules():
    false_block = CoverageStrategy(
        strategy_key="false.block",
        strategy_version=1,
        verdict=False,
        priority=10,
        coverage_rule=SourceTargetSetsRule(
            source_ids=frozenset({1}),
            target_ids=frozenset({2, 3}),
        ),
        certificate_family="block",
    )
    false_pair = CoverageStrategy(
        strategy_key="false.pair",
        strategy_version=1,
        verdict=False,
        priority=20,
        coverage_rule=strategy_registry_module.ExplicitPairsRule(
            pair_indexes=frozenset({0, 5}),
            law_count=3,
        ),
        certificate_family="paircheck",
    )
    registry = Order5StrategyRegistry(law_count=3, strategies=[false_block, false_pair])

    summary = registry.coverage_summary()

    assert summary["raw_false_union_covered"] == 3
    assert summary["strategy_counts"]["false.pair.v1"] == 2
    assert summary["same_verdict_overlap"] == 1
```

- [x] **Step 2: Run failing mixed union test**

Run:

```bash
PYTHONPATH=src pytest tests/data/test_order5_strategy_registry.py::test_registry_summary_counts_explicit_pairs_with_source_target_rules -q
```

Expected: fail if `_union_count_for_rules` assumes only source-target rules.

- [x] **Step 3: Implement mixed union fallback**

Update `_union_count_for_rules` in `src/math_distill_stage2/order5_strategy_registry.py`:

```python
def _union_count_for_rules(rules: Sequence[SourceTargetSetsRule | ExplicitPairsRule]) -> int:
    if any(rule.coverage_kind == "explicit_pairs" for rule in rules):
        return len(
            {
                pair
                for rule in rules
                for pair in rule.iter_covered_pairs()
            }
        )
    return _union_count_for_source_target_rules(rules)
```

Rename the current optimized implementation body to `_union_count_for_source_target_rules`. Keep `_union_count_for_rules_inclusion_exclusion` unchanged for existing tests.

- [x] **Step 4: Run registry tests**

Run:

```bash
PYTHONPATH=src pytest tests/data/test_order5_strategy_registry.py -q
```

Expected: pass.

## Task 7: Remote Smoke Execution Script

**Files:**
- Create: `scripts/lean_certificates/verify_order5_paircheck_remote_smoke.py`
- Modify: `docs/superpowers/specs/2026-05-14-order5-paircheck-bank-design.md`

- [x] **Step 1: Create remote-only smoke verifier**

Create `scripts/lean_certificates/verify_order5_paircheck_remote_smoke.py`:

```python
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))

from math_distill_stage2.official_stage2_batch import (
    RemoteSimpleApiJudgeConfig,
    make_remote_simple_api_batch_judge,
)


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--base-url")
    parser.add_argument("--base-urls", default="http://10.220.69.153:8888,http://10.220.69.172:8888")
    parser.add_argument("--max-workers", type=int, default=1)
    parser.add_argument("--request-timeout-seconds", type=int, default=20)
    parser.add_argument("--run-timeout-seconds", type=int, default=300)
    parser.add_argument("--poll-interval-seconds", type=float, default=2.0)
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args()

    records = read_jsonl(args.input)
    judge = make_remote_simple_api_batch_judge(
        RemoteSimpleApiJudgeConfig(
            base_url=args.base_url,
            max_workers=args.max_workers,
            problems_per_shard=1,
            cache=not args.no_cache,
            request_timeout_seconds=args.request_timeout_seconds,
            run_timeout_seconds=args.run_timeout_seconds,
            poll_interval_seconds=args.poll_interval_seconds,
            run_id_prefix="stage2-paircheck-smoke",
        )
    )
    requests = [(record["problem"], record["answer"]) for record in records]
    results = judge(requests)
    output_rows = [
        {
            **record,
            "remote_result": result,
            "status": result.get("status"),
            "error_code": result.get("error_code"),
        }
        for record, result in zip(records, results, strict=True)
    ]
    write_jsonl(args.output, output_rows)
    counts = Counter(str(row["status"]) for row in output_rows)
    summary = {
        "schema_version": 1,
        "input": str(args.input),
        "output": str(args.output),
        "total_count": len(output_rows),
        "status_counts": dict(counts),
        "accepted_count": counts.get("accepted", 0),
        "base_url": args.base_url,
        "cache": not args.no_cache,
    }
    if args.summary is not None:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["accepted_count"] == summary["total_count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [x] **Step 2: Add concrete remote smoke command to the spec**

Add this command block:

```bash
PYTHONPATH=src python scripts/lean_certificates/verify_order5_paircheck_remote_smoke.py \
  --input data/processed/order5_paircheck_bank/official_smoke_input.jsonl \
  --output data/processed/order5_paircheck_bank/official_smoke_results.jsonl \
  --summary data/processed/order5_paircheck_bank/official_smoke_summary.json \
  --base-urls http://10.220.69.153:8888,http://10.220.69.172:8888 \
  --max-workers 1 \
  --no-cache
```

This command must use the remote simple-api backend. Do not replace it with `verify_official_stage2_batch.py`, because that script runs local Docker.

- [x] **Step 3: Check documentation references**

Run:

```bash
rg -n "order5_paircheck_bank|remote-http|10\\.220\\.69\\.172|ExplicitPairsRule" \
  docs/superpowers/specs/2026-05-14-order5-paircheck-bank-design.md \
  AGENTS.md \
  skills/stage2-strategy-explore/SKILL.md
```

Expected: all key paths and remote judge constraints are present.

## Verification

Run after all tasks:

```bash
PYTHONPATH=src pytest tests/data/test_order5_paircheck_bank.py -q
PYTHONPATH=src pytest tests/data/test_order5_strategy_registry.py -q
pytest tests/skills/test_stage2_skills.py -q
python scripts/data/build_order5_paircheck_bank.py --help
```

Expected:

```text
tests pass
CLI help exits 0
```

Do not run local Docker/Lean judge as part of this verification.

## Verification Notes

- `PYTHONPATH=src pytest tests/data/test_order5_paircheck_bank.py tests/order5_strategy_registry/test_explicit_pairs_rule.py tests/lean_certificates/test_official_stage2_docker_batch.py::test_order5_paircheck_remote_smoke_cli_help_runs -q` passed.
- `pytest tests/skills/test_stage2_skills.py -q` passed.
- `python scripts/data/build_order5_paircheck_bank.py --help` and `python scripts/lean_certificates/verify_order5_paircheck_remote_smoke.py --help` both exited `0`.
- `PYTHONPATH=src pytest tests/data/test_order5_strategy_registry.py -q` was executed; 84 tests passed and 3 existing singleton seedbank expectation tests failed because the dirty working tree currently changes singleton seedbank counts. The focused `ExplicitPairsRule` regression tests passed separately.
- Remote simple-api backend pool was updated to `http://10.220.69.153:8888,http://10.220.69.172:8888`; `/health` was OK on both services, and the selector chose `http://10.220.69.153:8888`.
- One paircheck remote smoke was executed through the backend pool: `paircheck_4_2` accepted on `http://10.220.69.153:8888`, run id `stage2-paircheck-bank-paircheck_4_2-1778744558-11005d51-00`.
- Small pipeline smoke `data/processed/order5_paircheck_bank/small_batch_002` used `--empty-registry` with pure order2 enumerated model pool: 500 sampled pairs, 16 models, 253 Python-verified countermodels, and 20 smoke inputs.
- Remote smoke for `small_batch_002` accepted 19/20 on `http://10.220.69.153:8888`; the one timeout retry accepted on `http://10.220.69.172:8888`, so accepted-after-retry is 20/20. This smoke proves certificate shape and backend-pool flow, not unresolved union increment, because `--empty-registry` deliberately skipped current registry filtering.
- Small pipeline smoke `data/processed/order5_paircheck_bank/small_batch_003` used `--empty-registry`, `--enumerate-model-order 3`, `--enumerate-model-limit 1000`, `--sample-size 500`, and then filtered the resulting bank against the current false finite-model setcheck manifest: 231 Python-verified countermodels, 213 already covered by existing false setcheck, 18 candidate false increments written to `candidate_increment_bank.jsonl`.
- Remote smoke for `small_batch_003` accepted 18/18 on selected backend `http://10.220.69.153:8888`; backend pool candidates were `http://10.220.69.153:8888,http://10.220.69.172:8888`. Increment strata were 16 `order5_source_to_order5_target`, 1 `order4_source_to_order5_target`, and 1 `order5_source_to_order4_target`; all 18 used order3 finite magma certificates.
- Medium pipeline batch `data/processed/order5_paircheck_bank/medium_batch_001` used `--empty-registry`, `--enumerate-model-order 3`, `--enumerate-model-limit 2000`, `--sample-size 2000`, and current false finite-model setcheck filtering: 868 Python-verified countermodels, 808 already covered by existing false setcheck, 60 candidate false increments written to `candidate_increment_bank.jsonl`.
- Remote smoke for `medium_batch_001` accepted 50/50 smoke inputs on selected backend `http://10.220.69.153:8888`. Increment strata were 49 `order5_source_to_order5_target`, 9 `order5_source_to_order4_target`, and 2 `order4_source_to_order5_target`; all 60 used order3 finite magma certificates. The 60 medium-batch increments had zero overlap with the 18 `small_batch_003` increments, giving 78 distinct candidate increment pairs across these two batches.
- Performance note: `sample_size=2000` with `enumerate_model_limit=2000` is already near the upper bound for interactive local Python filtering. Continue with shard-sized batches or add early-stop/resume support before increasing both dimensions together.
- Merged artifact `data/processed/order5_paircheck_bank/merged_v1` combines `small_batch_003` and `medium_batch_001`: 78 input rows, 0 duplicates, 0 true-template conflicts, and 78 registry-ready paircheck rows. Initial merge had 68/78 remote smoke accepted; the remaining 10 unsmoked rows were verified through remote simple-api and accepted 10/10 on `http://10.220.69.153:8888`.
- Registry integration added `false.finmodel.paircheck.bank.v1` as an `explicit_pairs` false strategy with `coverage_count=78`, `remote_smoke_accepted_count=78`, and `true_conflict_count=0`. `data/processed/order5_strategy_registry/coverage_summary.json` was updated by the verified delta: `raw_false_union_covered` and `deterministic_false_covered` increased by 78; `unresolved_estimate` changed from `1077812754` to `1077812676`.
- Full `scripts/data/summarize_order5_strategy_coverage.py` was attempted after code-level registry integration but was stopped after more than 4 minutes without output. The JSON summary update above is therefore a targeted structured update backed by `merged_v1` evidence; optimizing full summary runtime is a separate follow-up.
