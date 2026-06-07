from pathlib import Path

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.proof_bank.bank import init_bank
from math_distill_stage2.proof_bank.prompt_pack import build_prompt_pack


def test_build_prompt_pack_writes_prompt_and_manifest(tmp_path: Path):
    bank = tmp_path / "bank"
    init_bank(bank)
    pool = tmp_path / "candidate_pool.jsonl"
    write_jsonl(
        pool,
        [
            {
                "source_problem_id": "true_5_2638",
                "source_dataset": "order4_splits/dev_fast",
                "eq1_id": 5,
                "eq2_id": 2638,
                "equation1": "x = y ◇ x",
                "equation2": "x = (y ◇ z) ◇ x",
                "expected_verdict": True,
                "priority_score": 10,
                "external_trace_available": False,
            }
        ],
    )
    run_root = tmp_path / "runs"

    summary = build_prompt_pack(
        bank=bank,
        candidate_pool=pool,
        run_root=run_root,
        source_run_id="gpt-true-cert-fixture-20260511-001",
        limit=1,
        prompt_policy="trace-if-available",
    )

    run_dir = Path(summary["run_dir"])
    prompt = (run_dir / "prompt_pack" / "000001.md").read_text(encoding="utf-8")
    assert summary["problem_count"] == 1
    assert (run_dir / "manifest.json").exists()
    assert read_jsonl(run_dir / "input_problems.jsonl")[0]["source_problem_id"] == "true_5_2638"
    assert "raw_response_path:" in prompt
    assert "x = y ◇ x" in prompt
    assert "def submission : Goal := by" in prompt
    assert '"verdict": "true"' in prompt


def test_build_prompt_pack_skips_existing_accepted_by_default(tmp_path: Path):
    bank = tmp_path / "bank"
    init_bank(bank)
    pool = tmp_path / "candidate_pool.jsonl"
    rows = [
        {
            "source_problem_id": "true_5_2638",
            "source_dataset": "order4_splits/dev_fast",
            "eq1_id": 5,
            "eq2_id": 2638,
            "equation1": "x = y ◇ x",
            "equation2": "x = (y ◇ z) ◇ x",
            "expected_verdict": True,
            "priority_score": 10,
            "external_trace_available": False,
        },
        {
            "source_problem_id": "true_6_2639",
            "source_dataset": "order4_splits/dev_fast",
            "eq1_id": 6,
            "eq2_id": 2639,
            "equation1": "x = y",
            "equation2": "x ◇ z = y ◇ z",
            "expected_verdict": True,
            "priority_score": 9,
            "external_trace_available": False,
        },
        {
            "source_problem_id": "true_7_2640",
            "source_dataset": "order4_splits/dev_fast",
            "eq1_id": 7,
            "eq2_id": 2640,
            "equation1": "x = y",
            "equation2": "z ◇ x = z ◇ y",
            "expected_verdict": True,
            "priority_score": 8,
            "external_trace_available": False,
        },
    ]
    write_jsonl(pool, rows)
    first_key_summary = build_prompt_pack(
        bank=bank,
        candidate_pool=pool,
        run_root=tmp_path / "runs",
        source_run_id="seed-first-key",
        limit=1,
        prompt_policy="trace-if-available",
    )
    first_problem = read_jsonl(Path(first_key_summary["run_dir"]) / "input_problems.jsonl")[0]
    write_jsonl(
        bank / "accepted.jsonl",
        [
            {
                "schema_version": 1,
                "problem_key": first_problem["problem_key"],
                "attempt_id": "attempt:accepted:000001",
                "certificate_sha256": "a" * 64,
                "certificate_kind": "true_proof",
            }
        ],
    )

    summary = build_prompt_pack(
        bank=bank,
        candidate_pool=pool,
        run_root=tmp_path / "runs",
        source_run_id="skip-existing",
        limit=2,
        prompt_policy="trace-if-available",
    )

    selected = read_jsonl(Path(summary["run_dir"]) / "input_problems.jsonl")
    assert summary["problem_count"] == 2
    assert summary["skipped_existing_accepted_count"] == 1
    assert [row["source_problem_id"] for row in selected] == ["true_6_2639", "true_7_2640"]


def test_build_prompt_pack_includes_trace_and_repair_context(tmp_path: Path):
    bank = tmp_path / "bank"
    init_bank(bank)
    pool = tmp_path / "candidate_pool.jsonl"
    write_jsonl(
        pool,
        [
            {
                "source_problem_id": "true_2112_3405",
                "source_dataset": "order4_splits/dev_main",
                "eq1_id": 2112,
                "eq2_id": 3405,
                "equation1": "x = ((y ◇ x) ◇ z) ◇ (y ◇ y)",
                "equation2": "x ◇ y = z ◇ (y ◇ (z ◇ y))",
                "expected_verdict": True,
                "priority_score": 277,
                "external_trace_available": True,
                "external_trace_family": "failed_official_judge_attempts_high_signal",
                "source_candidate_stratum": "rejected_attempt_repair",
                "source_attempt_id": "attempt:old:000001",
                "previous_judge_error_kind": "lean_type_error",
                "previous_judge_error_summary": "application type mismatch",
                "previous_proof_body_excerpt": "have h1 := h y x z\nexact h1",
                "h_application_count": 32,
                "trans_count": 16,
                "symm_count": 16,
                "unknown_tactic_count": 2,
                "unsolved_goal_count": 6,
            }
        ],
    )

    summary = build_prompt_pack(
        bank=bank,
        candidate_pool=pool,
        run_root=tmp_path / "runs",
        source_run_id="trace-context",
        limit=1,
        prompt_policy="trace-if-available",
    )

    prompt = (
        Path(summary["run_dir"]) / "prompt_pack" / "000001.md"
    ).read_text(encoding="utf-8")
    assert "## Prior Solver Trace Summary" in prompt
    assert "h applications: 32" in prompt
    assert "previous judge error: lean_type_error" in prompt
    assert "Previous proof excerpt" in prompt
    assert "have h1 := h y x z" in prompt
    assert "Do not use Markdown fences" in prompt
    assert "If you cannot finish a proof" in prompt


def test_build_prompt_pack_uses_skill_guidance_for_repair_items(tmp_path: Path):
    bank = tmp_path / "bank"
    init_bank(bank)
    pool = tmp_path / "candidate_pool.jsonl"
    write_jsonl(
        pool,
        [
            {
                "source_problem_id": "true_10_30",
                "source_dataset": "order4_splits/dev_main",
                "eq1_id": 10,
                "eq2_id": 30,
                "equation1": "x = y",
                "equation2": "x ◇ z = y ◇ z",
                "expected_verdict": True,
                "priority_score": 500,
                "external_trace_available": True,
                "source_candidate_stratum": "rejected_attempt_repair",
                "previous_judge_error_kind": "lean_type_error",
                "previous_judge_error_summary": "application type mismatch",
                "previous_proof_body_excerpt": "exact h",
            }
        ],
    )

    summary = build_prompt_pack(
        bank=bank,
        candidate_pool=pool,
        run_root=tmp_path / "runs",
        source_run_id="repair-mode",
        limit=1,
        prompt_policy="trace-if-available",
        etp_implications_path=None,
    )

    run_dir = Path(summary["run_dir"])
    prompt = (run_dir / "prompt_pack" / "000001.md").read_text(encoding="utf-8")
    manifest = (run_dir / "manifest.json").read_text(encoding="utf-8")
    assert "## Skill-Guided Proof Instructions" in prompt
    assert "lean-proof" in prompt
    assert "source role: repair" in prompt
    assert "Syntax errors" in prompt
    assert "Type errors" in prompt
    assert "Unsolved goals" in prompt
    assert "one tactic" in prompt
    assert "Previous proof excerpt" in prompt
    assert '"name": "lean-proof"' in manifest
    assert '"source_role": "repair"' in manifest


def test_build_prompt_pack_includes_etp_blueprint_context(tmp_path: Path):
    bank = tmp_path / "bank"
    init_bank(bank)
    pool = tmp_path / "candidate_pool.jsonl"
    write_jsonl(
        pool,
        [
            {
                "source_problem_id": "true_10_30",
                "source_dataset": "order4_splits/dev_main",
                "eq1_id": 10,
                "eq2_id": 30,
                "equation1": "x = y",
                "equation2": "x = z",
                "expected_verdict": True,
                "priority_score": 12,
                "external_trace_available": False,
            }
        ],
    )
    etp_implications = tmp_path / "etp_implications.jsonl"
    write_jsonl(
        etp_implications,
        [
            {
                "lhs_id": 10,
                "rhs_id": 20,
                "name": "Subgraph.Equation10_implies_Equation20",
                "filename": "/snapshot/EquationalTheories/Generated/Subgraph.lean",
                "line": 100,
                "finite": False,
                "proven": True,
            },
            {
                "lhs_id": 20,
                "rhs_id": 30,
                "name": "Subgraph.Equation20_implies_Equation30",
                "filename": "/snapshot/EquationalTheories/Generated/Subgraph.lean",
                "line": 120,
                "finite": False,
                "proven": True,
            },
        ],
    )

    summary = build_prompt_pack(
        bank=bank,
        candidate_pool=pool,
        run_root=tmp_path / "runs",
        source_run_id="etp-context",
        limit=1,
        prompt_policy="trace-if-available",
        etp_implications_path=etp_implications,
    )

    prompt = (
        Path(summary["run_dir"]) / "prompt_pack" / "000001.md"
    ).read_text(encoding="utf-8")
    assert "## ETP Blueprint Context" in prompt
    assert "Equation10 -> Equation20 -> Equation30" in prompt
    assert "Subgraph.Equation10_implies_Equation20" in prompt
    assert "Subgraph.Equation20_implies_Equation30" in prompt
    assert "Subgraph.lean:100" in prompt
    assert "These hints are not available as theorem names" in prompt


def test_build_prompt_pack_can_limit_high_signal_items_without_etp_context(tmp_path: Path):
    bank = tmp_path / "bank"
    init_bank(bank)
    pool = tmp_path / "candidate_pool.jsonl"
    write_jsonl(
        pool,
        [
            {
                "source_problem_id": "true_100_200",
                "source_dataset": "order4_splits/dev_main",
                "eq1_id": 100,
                "eq2_id": 200,
                "equation1": "x = y ◇ x",
                "equation2": "x = (y ◇ z) ◇ x",
                "expected_verdict": True,
                "priority_score": 300,
                "external_trace_available": True,
                "source_candidate_stratum": "high_signal_failed_attempts",
            },
            {
                "source_problem_id": "true_101_201",
                "source_dataset": "order4_splits/dev_main",
                "eq1_id": 101,
                "eq2_id": 201,
                "equation1": "x = y ◇ (x ◇ y)",
                "equation2": "x = z ◇ (x ◇ z)",
                "expected_verdict": True,
                "priority_score": 299,
                "external_trace_available": True,
                "source_candidate_stratum": "high_signal_failed_attempts",
            },
            {
                "source_problem_id": "true_102_202",
                "source_dataset": "order4_implication_problems",
                "eq1_id": 102,
                "eq2_id": 202,
                "equation1": "x = x",
                "equation2": "x = x",
                "expected_verdict": True,
                "priority_score": 0,
                "external_trace_available": False,
                "source_candidate_stratum": "direct_order4_true_exploration",
            },
        ],
    )

    summary = build_prompt_pack(
        bank=bank,
        candidate_pool=pool,
        run_root=tmp_path / "runs",
        source_run_id="limit-high-no-etp",
        limit=3,
        prompt_policy="trace-if-available",
        etp_implications_path=None,
        max_high_signal_without_etp=1,
    )

    selected = read_jsonl(Path(summary["run_dir"]) / "input_problems.jsonl")
    assert summary["problem_count"] == 2
    assert summary["skipped_high_signal_without_etp_count"] == 1
    assert [row["source_problem_id"] for row in selected] == [
        "true_100_200",
        "true_102_202",
    ]
