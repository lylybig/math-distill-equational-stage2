import json
from pathlib import Path

from math_distill_stage2.proof_bank.singleton_seedgate import (
    binary_grind_singleton_proof_body,
    build_singleton_seedgate_run,
)
from math_distill_stage2.proof_bank.keying import problem_key_from_equations


def test_binary_grind_singleton_proof_body_scales_by_variable_count():
    proof = binary_grind_singleton_proof_body(3)

    assert proof.startswith("intro x y")
    assert proof.count("have h") == 8
    assert "have h7 := h (y) (y) (y)" in proof
    assert proof.endswith("grind")


def test_build_singleton_seedgate_run_excludes_attempted_problem_keys(tmp_path: Path):
    equations = tmp_path / "eq_size5.txt"
    equations.write_text(
        "\n".join(
            [
                "x = x",
                "x = y",
                "x = y * ((x * z) * (w * (w * z)))",
                "x = y * ((z * x) * ((y * y) * w))",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    candidates = tmp_path / "candidates.jsonl"
    candidates.write_text(
        json.dumps({"source_seed_ids": [3, 4]}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    previous = tmp_path / "previous"
    previous.mkdir()
    previous_input = {
        "item_id": "000001",
        "problem_key": problem_key_from_equations(
            "x = y * ((x * z) * (w * (w * z)))",
            "x = y",
        ),
    }
    (previous / "input_problems.jsonl").write_text(
        json.dumps(previous_input) + "\n",
        encoding="utf-8",
    )

    run_dir = tmp_path / "run"
    summary = build_singleton_seedgate_run(
        run_dir=run_dir,
        source_seed_candidates_path=candidates,
        equations_path=equations,
        limit=2,
        previous_run_dirs=[previous],
        source_run_id="test-run",
    )

    assert summary["problem_count"] == 1
    assert summary["selected_source_ids"] == [4]
    raw_response = json.loads((run_dir / "raw_responses" / "000001.txt").read_text())
    assert raw_response["verdict"] == "true"
    assert "have h15" in raw_response["proof"]


def test_build_singleton_seedgate_run_reads_top_priority_source_ids(tmp_path: Path):
    equations = tmp_path / "eq_size5.txt"
    equations.write_text(
        "\n".join(
            [
                "x = x",
                "x = y",
                "x = y * z",
                "x = y * (z * w)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    candidates = tmp_path / "recursive_anchor.jsonl"
    candidates.write_text(
        json.dumps({"source_ids_top_priority": [3, 4]}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    summary = build_singleton_seedgate_run(
        run_dir=tmp_path / "run",
        source_seed_candidates_path=candidates,
        equations_path=equations,
        limit=1,
        source_run_id="recursive-anchor-test",
    )

    assert summary["candidate_source_count"] == 2
    assert summary["selected_source_ids"] == [3]
