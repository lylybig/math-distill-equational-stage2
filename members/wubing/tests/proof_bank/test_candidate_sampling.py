import gzip
import json
from pathlib import Path

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.proof_bank.candidate_sampling import sample_candidate_pool
from math_distill_stage2.proof_bank.keying import problem_key_from_equations


def write_gzip_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def right_nested(depth: int) -> str:
    term = "x"
    for name in ["y", "z", "w", "u", "v", "a", "b", "c", "d", "e"][:depth]:
        term = f"({term} ◇ {name})"
    return term


def left_nested(depth: int) -> str:
    term = "x"
    for name in ["y", "z", "w", "u", "v", "a", "b", "c", "d", "e"][:depth]:
        term = f"({name} ◇ {term})"
    return term


def process_row(index: int, *, score: int, stratum: str = "high") -> dict:
    return {
        "source_problem_id": f"true_{index}_{index + 100}",
        "source_dataset": "order4_splits/dev_main",
        "eq1_id": index,
        "eq2_id": index + 100,
        "equation1": f"x = {right_nested(index % 7 + 1)}",
        "equation2": f"x = {left_nested(index % 11 + 1)}",
        "expected_verdict": True,
        "priority_score": score,
        "external_trace_available": True,
        "external_trace_family": f"fixture_{stratum}",
    }


def test_sample_candidate_pool_prioritizes_train_process_data_and_keeps_direct_order4_share(
    tmp_path: Path,
):
    bank = tmp_path / "bank"
    bank.mkdir()
    write_jsonl(bank / "accepted.jsonl", [])
    write_jsonl(bank / "attempts.jsonl", [])
    high_signal_pool = tmp_path / "high.jsonl"
    unsolved_pool = tmp_path / "unsolved.jsonl"
    order4_dir = tmp_path / "order4"
    write_jsonl(high_signal_pool, [process_row(i, score=100 - i) for i in range(1, 9)])
    write_jsonl(
        unsolved_pool,
        [process_row(i, score=50 - i, stratum="unsolved") for i in range(20, 24)],
    )
    write_gzip_jsonl(
        order4_dir / "part-00000.jsonl.gz",
        [
            {
                "id": f"true_{i}_{i + 200}",
                "eq1_id": i,
                "eq2_id": i + 200,
                "equation1": f"x = {right_nested(i % 7 + 1)}",
                "equation2": f"x = {left_nested(i % 11 + 1)}",
                "answer": True,
            }
            for i in range(30, 36)
        ],
    )
    (order4_dir / "manifest.json").write_text(
        json.dumps({"rows": 6, "shards": [{"path": "part-00000.jsonl.gz", "rows": 6, "true": 6}]}),
        encoding="utf-8",
    )

    summary = sample_candidate_pool(
        bank=bank,
        output_pool=tmp_path / "sampled.jsonl",
        output_manifest=tmp_path / "sampled.manifest.json",
        pool_id="fixture-sampled",
        seed=123,
        limit=10,
        high_signal_pools=[high_signal_pool],
        unsolved_pools=[unsolved_pool],
        order4_source=order4_dir,
    )

    rows = read_jsonl(tmp_path / "sampled.jsonl")
    by_stratum = summary["selected_by_stratum"]
    assert len(rows) == 10
    assert by_stratum == {
        "direct_order4_true_exploration": 2,
        "high_signal_failed_attempts": 6,
        "unsolved_trace_or_timeout": 2,
    }
    assert [row["source_candidate_stratum"] for row in rows[:3]] == [
        "high_signal_failed_attempts",
        "unsolved_trace_or_timeout",
        "direct_order4_true_exploration",
    ]
    assert {row["source_candidate_stratum"] for row in rows} == set(by_stratum)


def test_sample_candidate_pool_excludes_accepted_and_attempt_ceiling(tmp_path: Path):
    bank = tmp_path / "bank"
    bank.mkdir()
    accepted = process_row(1, score=100)
    saturated = process_row(2, score=99)
    accepted_key = problem_key_from_equations(accepted["equation1"], accepted["equation2"])
    saturated_key = problem_key_from_equations(saturated["equation1"], saturated["equation2"])
    write_jsonl(
        bank / "accepted.jsonl",
        [{"problem_key": accepted_key, "certificate_kind": "true_proof"}],
    )
    write_jsonl(
        bank / "attempts.jsonl",
        [{"problem_key": saturated_key}, {"problem_key": saturated_key}, {"problem_key": saturated_key}],
    )
    high_signal_pool = tmp_path / "high.jsonl"
    write_jsonl(
        high_signal_pool,
        [accepted, saturated, process_row(3, score=98), process_row(4, score=97)],
    )

    summary = sample_candidate_pool(
        bank=bank,
        output_pool=tmp_path / "sampled.jsonl",
        output_manifest=tmp_path / "sampled.manifest.json",
        pool_id="fixture-exclusions",
        seed=1,
        limit=2,
        high_signal_pools=[high_signal_pool],
        unsolved_pools=[],
        order4_source=None,
        max_attempts_per_problem=3,
    )

    rows = read_jsonl(tmp_path / "sampled.jsonl")
    keys = {problem_key_from_equations(row["equation1"], row["equation2"]) for row in rows}
    assert accepted_key not in keys
    assert saturated_key not in keys
    assert summary["excluded_accepted_count"] == 1
    assert summary["excluded_attempt_ceiling_count"] == 1


def test_sample_candidate_pool_adds_rejected_attempt_repair_lane(tmp_path: Path):
    bank = tmp_path / "bank"
    bank.mkdir()
    rejected = process_row(11, score=0)
    rejected_key = problem_key_from_equations(rejected["equation1"], rejected["equation2"])
    write_jsonl(
        bank / "problems.jsonl",
        [
            {
                **rejected,
                "problem_key": rejected_key,
                "source_datasets": ["order4_splits/dev_main"],
            }
        ],
    )
    write_jsonl(bank / "accepted.jsonl", [])
    write_jsonl(
        bank / "attempts.jsonl",
        [
            {
                "attempt_id": "attempt:fixture:000001",
                "problem_key": rejected_key,
                "judge_status": "rejected",
                "official_judge_status": "incorrect",
                "judge_error_kind": "lean_type_error",
                "judge_error_summary": "application type mismatch",
                "proof_body_sha256": "a" * 64,
            }
        ],
    )
    high_signal_pool = tmp_path / "high.jsonl"
    write_jsonl(high_signal_pool, [process_row(i, score=20 - i) for i in range(1, 6)])

    summary = sample_candidate_pool(
        bank=bank,
        output_pool=tmp_path / "sampled.jsonl",
        output_manifest=tmp_path / "sampled.manifest.json",
        pool_id="fixture-repair",
        seed=7,
        limit=4,
        high_signal_pools=[high_signal_pool],
        unsolved_pools=[],
        order4_source=None,
        repair_from_bank=True,
    )

    rows = read_jsonl(tmp_path / "sampled.jsonl")
    repair_rows = [
        row for row in rows if row["source_candidate_stratum"] == "rejected_attempt_repair"
    ]
    assert summary["selected_by_stratum"]["rejected_attempt_repair"] == 1
    assert repair_rows[0]["source_attempt_id"] == "attempt:fixture:000001"
    assert repair_rows[0]["previous_judge_error_kind"] == "lean_type_error"
    assert rows[0]["source_candidate_stratum"] == "rejected_attempt_repair"


def test_sample_candidate_pool_recovery_strategy_rebalances_after_zero_yield(tmp_path: Path):
    bank = tmp_path / "bank"
    bank.mkdir()
    write_jsonl(bank / "accepted.jsonl", [])
    repair_problems = []
    repair_attempts = []
    for index in range(100, 108):
        row = process_row(index, score=0)
        problem_key = f"fixture-repair-{index}"
        repair_problems.append({**row, "problem_key": problem_key})
        repair_attempts.append(
            {
                "attempt_id": f"attempt:fixture:{index}",
                "problem_key": problem_key,
                "judge_status": "rejected",
                "official_judge_status": "incorrect",
                "judge_error_kind": "lean_type_error",
                "judge_error_summary": "application type mismatch",
            }
        )
    write_jsonl(bank / "problems.jsonl", repair_problems)
    write_jsonl(bank / "attempts.jsonl", repair_attempts)
    high_signal_pool = tmp_path / "high.jsonl"
    unsolved_pool = tmp_path / "unsolved.jsonl"
    order4_dir = tmp_path / "order4"
    write_jsonl(
        high_signal_pool,
        [
            {**process_row(i, score=100 - i), "problem_key": f"fixture-high-{i}"}
            for i in range(1, 20)
        ],
    )
    write_jsonl(
        unsolved_pool,
        [
            {
                **process_row(i, score=50 - i, stratum="unsolved"),
                "problem_key": f"fixture-unsolved-{i}",
            }
            for i in range(20, 30)
        ],
    )
    write_gzip_jsonl(
        order4_dir / "part-00000.jsonl.gz",
        [
            {
                "id": f"true_{i}_{i + 200}",
                "eq1_id": i,
                "eq2_id": i + 200,
                "equation1": f"x = {right_nested(i % 7 + 1)}",
                "equation2": f"x = {left_nested(i % 11 + 1)}",
                "answer": True,
            }
            for i in range(30, 45)
        ],
    )

    summary = sample_candidate_pool(
        bank=bank,
        output_pool=tmp_path / "sampled.jsonl",
        output_manifest=tmp_path / "sampled.manifest.json",
        pool_id="fixture-recovery",
        seed=123,
        limit=20,
        high_signal_pools=[high_signal_pool],
        unsolved_pools=[unsolved_pool],
        order4_source=order4_dir,
        repair_from_bank=True,
        sampling_strategy="recovery-after-zero-yield",
    )

    assert summary["sampling_strategy"] == "recovery-after-zero-yield"
    assert summary["selected_by_stratum"] == {
        "direct_order4_true_exploration": 5,
        "high_signal_failed_attempts": 7,
        "rejected_attempt_repair": 5,
        "unsolved_trace_or_timeout": 3,
    }
    assert summary["stratum_weights"] == {
        "direct_order4_true_exploration": 0.25,
        "high_signal_failed_attempts": 0.35,
        "rejected_attempt_repair": 0.25,
        "unsolved_trace_or_timeout": 0.15,
    }
