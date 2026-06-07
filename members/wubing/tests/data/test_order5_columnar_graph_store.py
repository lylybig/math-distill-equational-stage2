import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from math_distill_stage2.order5_columnar_graph_store import (
    BitsetLayer,
    ColumnarImplicationStore,
    finite_model_equation_partition,
    iter_pair_indexes,
)


def test_bitset_layer_sets_counts_and_iterates_ranges(tmp_path: Path):
    bitset = BitsetLayer.create(tmp_path / "sample.bitset", 20)

    with bitset.open() as layer:
        assert layer.set(0) is True
        assert layer.set(7) is True
        assert layer.set(12) is True
        assert layer.set(12) is False
        assert layer.get(7) is True
        assert layer.get(8) is False
        assert layer.count() == 3
        assert list(layer.iter_set_bits(start=1, stop=13)) == [7, 12]


def test_columnar_store_tracks_status_conflicts_and_rows(tmp_path: Path):
    store = ColumnarImplicationStore.create(
        tmp_path / "store",
        law_count=4,
        layers=("true", "false", "approx_true", "conflict"),
    )

    assert store.pair_count == 12
    assert store.set_pair("true", eq1_id=2, eq2_id=4) is True
    assert store.set_pair("true", eq1_id=2, eq2_id=4) is False
    assert store.status(eq1_id=2, eq2_id=4)["verdict"] == "true"
    assert store.row_targets("true", 2) == [4]

    store.set_pair("false", eq1_id=2, eq2_id=4)
    status = store.status(eq1_id=2, eq2_id=4)

    assert status["layers"]["true"] is True
    assert status["layers"]["false"] is True
    assert status["layers"]["conflict"] is True
    assert status["verdict"] == "conflict"


def test_import_pair_indexes_from_text_and_jsonl(tmp_path: Path):
    store = ColumnarImplicationStore.create(
        tmp_path / "store",
        law_count=4,
        layers=("true", "false", "conflict"),
    )
    text_path = tmp_path / "pairs.txt"
    text_path.write_text("0\n3\n3\n", encoding="ascii")

    summary = store.import_pair_indexes(
        text_path,
        layer_name="true",
        source_id="unit-test.true",
    )

    assert summary.read_count == 3
    assert summary.newly_set_count == 2
    assert summary.already_set_count == 1
    assert store.status(pair_index=0)["verdict"] == "true"
    assert store.status(pair_index=3)["verdict"] == "true"

    jsonl_path = tmp_path / "pairs.jsonl"
    jsonl_path.write_text(
        json.dumps({"pair_index": 3}) + "\n" + json.dumps({"pair_index": 8}) + "\n",
        encoding="utf-8",
    )

    summary = store.import_pair_indexes(
        jsonl_path,
        layer_name="false",
        source_id="unit-test.false",
        source_kind="jsonl_cache",
    )

    assert summary.read_count == 2
    assert summary.conflict_count == 1
    assert store.status(pair_index=3)["verdict"] == "conflict"
    assert store.status(pair_index=8)["verdict"] == "false"

    batch_log = tmp_path / "store" / "evidence" / "evidence_batches.jsonl"
    batch_rows = [json.loads(line) for line in batch_log.read_text().splitlines()]
    assert [row["source_id"] for row in batch_rows] == [
        "unit-test.true",
        "unit-test.false",
    ]


def test_source_target_block_import_sets_rows_without_self_pairs(tmp_path: Path):
    store = ColumnarImplicationStore.create(
        tmp_path / "store",
        law_count=4,
        layers=("true", "false", "conflict"),
    )

    summary = store.set_source_target_block(
        "true",
        source_ids={1, 3},
        target_ids={2, 3, 4},
        source_id="unit-test.block",
    )

    assert summary["read_count"] == 5
    assert summary["newly_set_count"] == 5
    assert store.row_targets("true", 1) == [2, 3, 4]
    assert store.row_targets("true", 3) == [2, 4]
    assert store.status(eq1_id=3, eq2_id=2)["verdict"] == "true"


def test_import_coverage_strategies_accepts_pair_and_block_rules(tmp_path: Path):
    store = ColumnarImplicationStore.create(
        tmp_path / "store",
        law_count=4,
        layers=("true", "false", "conflict"),
    )
    pair_strategy = _FakeStrategy(
        strategy_key="true.fake.pairs",
        verdict=True,
        coverage_rule=_FakePairRule(pair_indexes=frozenset({0, 3})),
    )
    block_strategy = _FakeStrategy(
        strategy_key="false.fake.block",
        verdict=False,
        coverage_rule=_FakeSourceTargetRule(
            source_ids=frozenset({1, 2}),
            target_ids=frozenset({2, 4}),
        ),
    )

    summary = store.import_coverage_strategies([pair_strategy, block_strategy])

    assert summary["imported_count"] == 2
    assert summary["read_count"] == 5
    assert store.status(eq1_id=1, eq2_id=2)["verdict"] == "conflict"
    assert store.status(eq1_id=2, eq2_id=4)["verdict"] == "false"


def test_rebuild_conflicts_recomputes_from_true_and_false_layers(tmp_path: Path):
    store = ColumnarImplicationStore.create(
        tmp_path / "store",
        law_count=4,
        layers=("true", "false", "conflict"),
    )
    store.set_pair("true", eq1_id=1, eq2_id=2, update_conflict=False)
    store.set_pair("false", eq1_id=1, eq2_id=2, update_conflict=False)

    assert store.status(eq1_id=1, eq2_id=2)["layers"]["conflict"] is False

    summary = store.rebuild_conflicts()

    assert summary["conflict_count"] == 1
    assert store.status(eq1_id=1, eq2_id=2)["verdict"] == "conflict"


def test_preview_and_frontier_queries_support_mining(tmp_path: Path):
    store = ColumnarImplicationStore.create(
        tmp_path / "store",
        law_count=5,
        layers=("true", "false", "conflict"),
    )
    store.set_pair("true", eq1_id=1, eq2_id=2)
    store.set_pair("false", eq1_id=1, eq2_id=3)

    pair_cache = tmp_path / "pairs.txt"
    pair_cache.write_text(
        "\n".join(
            str(store.ids_to_pair_index(eq1_id, eq2_id))
            for eq1_id, eq2_id in [(1, 2), (1, 4), (2, 4)]
        )
        + "\n",
        encoding="ascii",
    )

    preview = store.preview_pair_indexes(pair_cache, layer_name="true", top_n=2)

    assert preview["read_count"] == 3
    assert preview["already_set_count"] == 1
    assert preview["newly_set_count"] == 2
    assert preview["top_sources"] == [{"id": 1, "count": 2}, {"id": 2, "count": 1}]
    assert store.status(eq1_id=1, eq2_id=4)["verdict"] == "unknown"

    block_preview = store.preview_source_target_block(
        "false",
        source_ids={1},
        target_ids={2, 3, 4},
        source_id="unit-test.preview-block",
    )

    assert block_preview["read_count"] == 3
    assert block_preview["already_set_count"] == 1
    assert block_preview["newly_set_count"] == 2
    assert block_preview["conflict_count"] == 1
    assert block_preview["top_new_sources"] == [{"id": 1, "count": 2}]

    row_summary = store.row_summary(1)
    assert row_summary["layer_counts"]["true"] == 1
    assert row_summary["layer_counts"]["false"] == 1
    assert row_summary["exact_known_count"] == 2
    assert row_summary["unknown_count"] == 2

    target_summary = store.target_summary(2)
    assert target_summary["layer_counts"]["true"] == 1
    assert target_summary["unknown_count"] == 3
    assert store.target_sources("true", 2) == [1]

    target_map = store.target_map(2)
    assert list(target_map["status_codes"]) == [1, 0, 0, 0]
    assert target_map["counts"]["true"] == 1
    assert target_map["counts"]["unknown"] == 3

    exact_counts = store.exact_pair_counts()
    assert exact_counts["exact_known_count"] == 2
    assert exact_counts["exact_unknown_count"] == 18

    frontier = store.source_frontier(1, limit=5)
    assert frontier["unknown_count"] == 2
    assert frontier["targets"] == [4, 5]


def test_preview_coverage_strategies_does_not_write_bits(tmp_path: Path):
    store = ColumnarImplicationStore.create(
        tmp_path / "store",
        law_count=4,
        layers=("true", "false", "conflict"),
    )
    store.set_pair("true", eq1_id=1, eq2_id=2)
    strategy = _FakeStrategy(
        strategy_key="false.fake.preview",
        verdict=False,
        coverage_rule=_FakeSourceTargetRule(
            source_ids=frozenset({1}),
            target_ids=frozenset({2, 3}),
        ),
    )

    summary = store.preview_coverage_strategies([strategy])

    assert summary["imported_count"] == 1
    assert summary["read_count"] == 2
    assert summary["newly_set_count"] == 2
    assert summary["conflict_count"] == 1
    assert store.status(eq1_id=1, eq2_id=3)["verdict"] == "unknown"


def test_finite_model_partition_supports_false_block_adapter(tmp_path: Path):
    equations_path = tmp_path / "eqs.txt"
    equations_path.write_text("x = x\nx * y = x\nx * y = y\n", encoding="utf-8")

    partition = finite_model_equation_partition(
        equations_path=equations_path,
        model_table=((0, 0), (1, 1)),
    )

    assert partition["satisfied_ids"] == [1, 2]
    assert partition["refuted_ids"] == [3]

    store = ColumnarImplicationStore.create(
        tmp_path / "store",
        law_count=3,
        layers=("false",),
    )
    preview = store.preview_source_target_block(
        "false",
        source_ids=partition["satisfied_ids"],
        target_ids=partition["refuted_ids"],
        source_id="unit-test.finmodel",
    )

    assert preview["read_count"] == 2
    assert preview["newly_set_count"] == 2


def test_iter_pair_indexes_rejects_invalid_rows(tmp_path: Path):
    path = tmp_path / "bad.txt"
    path.write_text("not-a-number\n", encoding="ascii")

    try:
        list(iter_pair_indexes(path))
    except ValueError as exc:
        assert "invalid pair_index" in str(exc)
    else:
        raise AssertionError("invalid pair index row was accepted")


def test_build_order5_columnar_graph_store_script_help_runs():
    root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [sys.executable, "scripts/data/build_order5_columnar_graph_store.py", "--help"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_build_order5_columnar_graph_store_registry_help_runs():
    root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [
            sys.executable,
            "scripts/data/build_order5_columnar_graph_store.py",
            "import-default-registry",
            "--help",
        ],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_build_order5_columnar_graph_store_mining_help_runs():
    root = Path(__file__).resolve().parents[2]
    commands = [
        "preview-pair-indexes",
        "preview-pair-index-strategy-row",
        "import-pair-index-strategy-row",
        "preview-default-registry",
        "preview-finmodel-strategy-row",
        "import-finmodel-strategy-row",
        "row-summary",
        "frontier",
    ]

    for command in commands:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/data/build_order5_columnar_graph_store.py",
                command,
                "--help",
            ],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr


@dataclass(frozen=True)
class _FakePairRule:
    pair_indexes: frozenset[int]

    @property
    def coverage_kind(self) -> str:
        return "explicit_pairs"


@dataclass(frozen=True)
class _FakeSourceTargetRule:
    source_ids: frozenset[int]
    target_ids: frozenset[int]

    @property
    def coverage_kind(self) -> str:
        return "source_target_sets"


@dataclass(frozen=True)
class _FakeStrategy:
    strategy_key: str
    verdict: bool
    coverage_rule: object
    deprecated: bool = False

    @property
    def strategy_id(self) -> str:
        return f"{self.strategy_key}.v1"
