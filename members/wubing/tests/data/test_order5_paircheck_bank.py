import json
import subprocess
import sys
from pathlib import Path

from math_distill_stage2.equations import parse_equation
from math_distill_stage2.order5_pair_space import ids_to_pair_index
from math_distill_stage2.order5_paircheck_bank import (
    PaircheckModel,
    analyze_existing_false_coverage,
    build_paircheck_bank_artifacts,
    build_remote_smoke_records,
    enumerate_paircheck_models,
    find_paircheck_countermodels,
    load_paircheck_models_from_strategy_manifest,
    merge_paircheck_increment_rows,
    pair_stratum,
    sample_unresolved_pairs,
    write_paircheck_bank,
)
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
        "order4_source_to_order4_target",
        "order4_source_to_order5_target",
        "order5_source_to_order4_target",
        "order5_source_to_order5_target",
    }


def test_pair_stratum_includes_order4_to_order4_pairs():
    assert pair_stratum(1, 2, order4_max_id=3) == "order4_source_to_order4_target"
    assert pair_stratum(1, 4, order4_max_id=3) == "order4_source_to_order5_target"
    assert pair_stratum(4, 1, order4_max_id=3) == "order5_source_to_order4_target"
    assert pair_stratum(4, 5, order4_max_id=3) == "order5_source_to_order5_target"


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


def test_find_paircheck_countermodels_uses_finite_magma_semantics():
    equations = {
        1: parse_equation("x * y = x"),
        2: parse_equation("x * y = y"),
        3: parse_equation("x = x"),
    }
    candidates = [
        {
            "pair_index": 0,
            "eq1_id": 1,
            "eq2_id": 2,
            "stratum": "order4_source_to_order5_target",
        },
        {
            "pair_index": 1,
            "eq1_id": 3,
            "eq2_id": 1,
            "stratum": "order5_source_to_order4_target",
        },
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


def test_analyze_existing_false_coverage_marks_current_setcheck_hits():
    equations = {
        1: parse_equation("x * y = x"),
        2: parse_equation("x * y = y"),
    }
    existing_models = [
        PaircheckModel(
            label="left",
            table=((0, 0), (1, 1)),
            source="false.finmodel.setcheck.left.v1",
        )
    ]
    rows = [
        {
            "pair_index": 1,
            "eq1_id": 1,
            "eq2_id": 2,
            "stratum": "order4_source_to_order4_target",
            "table": [[0, 0], [1, 1]],
        },
        {
            "pair_index": 2,
            "eq1_id": 2,
            "eq2_id": 1,
            "stratum": "order4_source_to_order4_target",
            "table": [[0, 1], [0, 1]],
        },
    ]

    annotated, summary = analyze_existing_false_coverage(
        bank_rows=rows,
        equations=equations,
        existing_models=existing_models,
        order4_max_id=3,
    )

    assert summary["total_count"] == 2
    assert summary["existing_false_covered_count"] == 1
    assert summary["candidate_false_increment_count"] == 1
    assert annotated[0]["existing_false_covered"] is True
    assert annotated[0]["existing_false_matches"] == [
        {
            "model_label": "left",
            "model_source": "false.finmodel.setcheck.left.v1",
        }
    ]
    assert annotated[1]["existing_false_covered"] is False
    assert annotated[1]["existing_false_matches"] == []


def test_merge_paircheck_increment_rows_dedupes_and_marks_evidence(tmp_path: Path):
    equations_path = tmp_path / "eq_size5.txt"
    equations_path.write_text(
        "\n".join(["x = y * y", "x * x = y * y", "x * y = x"]) + "\n",
        encoding="utf-8",
    )
    rows = [
        {
            "pair_index": ids_to_pair_index(1, 2, law_count=3),
            "eq1_id": 1,
            "eq2_id": 2,
            "stratum": "order5_source_to_order5_target",
            "model_label": "m1",
            "candidate_false_increment": True,
        },
        {
            "pair_index": ids_to_pair_index(1, 2, law_count=3),
            "eq1_id": 1,
            "eq2_id": 2,
            "stratum": "order5_source_to_order5_target",
            "model_label": "duplicate",
            "candidate_false_increment": True,
        },
        {
            "pair_index": ids_to_pair_index(3, 2, law_count=3),
            "eq1_id": 3,
            "eq2_id": 2,
            "stratum": "order5_source_to_order5_target",
            "model_label": "m2",
            "candidate_false_increment": True,
        },
    ]
    smoke_rows = [
        {
            "pair_index": ids_to_pair_index(3, 2, law_count=3),
            "status": "accepted",
        }
    ]

    merged, summary = merge_paircheck_increment_rows(
        rows,
        smoke_rows=smoke_rows,
        equations_path=equations_path,
        order4_max_id=0,
        include_seedbank=False,
    )

    assert summary["input_count"] == 3
    assert summary["written_count"] == 2
    assert summary["duplicate_count"] == 1
    assert summary["remote_smoke_accepted_count"] == 1
    assert summary["true_conflict_count"] == 1
    assert summary["registry_ready_count"] == 1
    assert merged[0]["true_conflict"] is True
    assert (
        "true.proof.templatecheck.singleton_collapse.any_target.v1"
        in merged[0]["true_conflict_strategy_ids"]
    )
    assert merged[1]["remote_smoke_status"] == "accepted"
    assert merged[1]["registry_ready"] is True


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
        for line in (tmp_path / "verified_bank.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert summary["written"] == 1
    assert written[0]["strategy_key"] == "false.finmodel.paircheck.bank"
    assert written[0]["table_sha256"]
    assert (tmp_path / "bank_summary.json").exists()


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

    [record] = build_remote_smoke_records(
        bank_rows=bank_rows,
        equations=equations,
        limit=1,
    )

    assert record["id"] == "paircheck_1_2"
    assert record["problem"]["answer"] is False
    assert record["answer"]["call"] == "judge"
    assert record["answer"]["verdict"] == "false"
    assert "def submission" in record["answer"]["code"]
    assert "JudgeProblem" in record["answer"]["code"]


def test_load_paircheck_models_from_strategy_manifest_reads_model_tables(tmp_path: Path):
    manifest_path = tmp_path / "strategies.json"
    manifest_path.write_text(
        json.dumps(
            [
                {
                    "strategy_id": "false.finmodel.setcheck.left.v1",
                    "model_family": "left",
                    "model_table": [[0, 0], [1, 1]],
                },
                {
                    "strategy_id": "true.template.v1",
                    "coverage_kind": "source_target_sets",
                },
                {
                    "strategy_id": "false.finmodel.setcheck.left_duplicate.v1",
                    "model_table": [[0, 0], [1, 1]],
                },
            ]
        ),
        encoding="utf-8",
    )

    models = load_paircheck_models_from_strategy_manifest(manifest_path)

    assert models == [
        PaircheckModel(
            label="left",
            table=((0, 0), (1, 1)),
            source="false.finmodel.setcheck.left.v1",
        )
    ]
    assert load_paircheck_models_from_strategy_manifest(manifest_path, limit=0) == []


def test_enumerate_paircheck_models_dedupes_existing_tables():
    existing = [
        PaircheckModel(
            label="left",
            table=((0, 0), (1, 1)),
            source="manifest",
        )
    ]

    models = enumerate_paircheck_models(order=2, existing_models=existing)

    assert len(models) == 15
    assert all(model.source == "enumerate_magmas_order2" for model in models)
    assert ((0, 0), (1, 1)) not in {model.table for model in models}


def test_build_paircheck_bank_artifacts_writes_small_pipeline(tmp_path: Path):
    equations_path = tmp_path / "eq_size5.txt"
    equations_path.write_text(
        "\n".join(["x * y = x", "x * y = y", "x = x"]) + "\n",
        encoding="utf-8",
    )
    manifest_path = tmp_path / "strategies.json"
    manifest_path.write_text(
        json.dumps(
            [
                {
                    "strategy_id": "false.finmodel.setcheck.left.v1",
                    "model_family": "left",
                    "model_table": [[0, 0], [1, 1]],
                }
            ]
        ),
        encoding="utf-8",
    )
    registry = Order5StrategyRegistry(law_count=3, strategies=[])

    summary = build_paircheck_bank_artifacts(
        registry=registry,
        equations_path=equations_path,
        model_manifest_path=manifest_path,
        output_dir=tmp_path / "bank",
        sample_size=6,
        seed=1,
        order4_max_id=0,
        smoke_limit=2,
        enumerate_model_orders=[2],
        max_scan_attempts=100,
    )

    assert summary["candidate_count"] == 6
    assert summary["model_count"] == 16
    assert summary["countermodel_count"] >= 1
    assert summary["smoke_input_count"] == summary["candidate_false_increment_count"]
    assert summary["paths"]["candidate_increment_bank"].endswith(
        "candidate_increment_bank.jsonl"
    )
    increment_rows = [
        json.loads(line)
        for line in (tmp_path / "bank" / "candidate_increment_bank.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert len(increment_rows) == summary["candidate_false_increment_count"]
    assert all(row["candidate_false_increment"] for row in increment_rows)
    assert (tmp_path / "bank" / "candidate_pairs.jsonl").exists()
    assert (tmp_path / "bank" / "model_pool.jsonl").exists()
    assert (tmp_path / "bank" / "countermodels.jsonl").exists()
    assert (tmp_path / "bank" / "verified_bank.jsonl").exists()
    assert (tmp_path / "bank" / "candidate_increment_bank.jsonl").exists()
    assert (tmp_path / "bank" / "existing_false_filter.jsonl").exists()
    assert (tmp_path / "bank" / "existing_false_filter_summary.json").exists()
    assert (tmp_path / "bank" / "official_smoke_input.jsonl").exists()


def test_build_order5_paircheck_bank_cli_help_mentions_sampling_args():
    root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [
            sys.executable,
            "scripts/data/build_order5_paircheck_bank.py",
            "--help",
        ],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "--sample-size" in result.stdout
    assert "--model-manifest" in result.stdout
    assert "--enumerate-model-order" in result.stdout
    assert "--smoke-limit" in result.stdout
    assert "--false-only-registry" in result.stdout
    assert "--empty-registry" in result.stdout


def test_merge_order5_paircheck_increment_banks_cli_help_mentions_inputs():
    root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [
            sys.executable,
            "scripts/data/merge_order5_paircheck_increment_banks.py",
            "--help",
        ],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "--increment-bank" in result.stdout
    assert "--smoke-results" in result.stdout
    assert "--output-dir" in result.stdout
