import subprocess
import sys
from pathlib import Path

from math_distill_stage2.dataset_io import write_jsonl
from math_distill_stage2.proof_bank.bank import init_bank


SCRIPTS = [
    "scripts/lean_certificates/proof_bank_init.py",
    "scripts/lean_certificates/proof_bank_sample_candidates.py",
    "scripts/lean_certificates/proof_bank_build_prompt_pack.py",
    "scripts/lean_certificates/proof_bank_import_responses.py",
    "scripts/lean_certificates/proof_bank_merge_run.py",
    "scripts/lean_certificates/proof_bank_check.py",
    "scripts/lean_certificates/proof_bank_rebuild_indexes.py",
    "scripts/lean_certificates/proof_bank_quality_audit.py",
    "scripts/lean_certificates/proof_bank_nightly_loop.py",
    "scripts/lean_certificates/proof_bank_harvest_external_olean.py",
]


def test_proof_bank_cli_help_runs():
    root = Path(__file__).resolve().parents[2]
    for script in SCRIPTS:
        result = subprocess.run(
            [sys.executable, script, "--help"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, f"{script}: {result.stderr}"
        assert "proof" in result.stdout.lower()


def test_nightly_loop_cli_accepts_marathon_date_override(tmp_path: Path):
    root = Path(__file__).resolve().parents[2]
    bank = tmp_path / "bank"
    init_bank(bank)
    pool = tmp_path / "pool.jsonl"
    write_jsonl(
        pool,
        [
            {
                "source_problem_id": "fixture",
                "source_dataset": "fixture",
                "eq1_id": 1,
                "eq2_id": 2,
                "equation1": "x = x",
                "equation2": "x = x",
                "expected_verdict": True,
                "priority_score": 1,
            }
        ],
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/lean_certificates/proof_bank_nightly_loop.py",
            "--bank",
            str(bank),
            "--run-root",
            str(tmp_path / "runs"),
            "--marathon-id",
            "date-marathon",
            "--mode",
            "prepare",
            "--seed",
            "123",
            "--candidate-limit",
            "1",
            "--prompt-limit",
            "1",
            "--high-signal-pool",
            str(pool),
            "--no-order4-source",
            "--marathon-date",
            "2026-05-11",
        ],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "artifacts/proof_bank_runs" not in result.stdout
    assert f"{tmp_path}/runs/2026-05-11/date-marathon/marathon_state.json" in result.stdout


def test_nightly_loop_cli_help_mentions_remote_judge_backend():
    root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [sys.executable, "scripts/lean_certificates/proof_bank_nightly_loop.py", "--help"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "--judge-backend" in result.stdout
    assert "remote-ssh" in result.stdout
    assert "remote-http" in result.stdout
    assert "--remote-judge-base-url" in result.stdout
    assert "--remote-judge-base-urls" in result.stdout


def test_import_responses_cli_help_mentions_remote_http_backend():
    root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [sys.executable, "scripts/lean_certificates/proof_bank_import_responses.py", "--help"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "--judge-backend" in result.stdout
    assert "remote-http" in result.stdout
    assert "--remote-judge-base-url" in result.stdout
    assert "--remote-judge-base-urls" in result.stdout
