import json
import subprocess
import sys
from pathlib import Path

from math_distill_stage2.counterexample.evidence import build_counterexample_evidence_bank
from math_distill_stage2.dataset_io import read_jsonl


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def write_counterexample_asset(
    asset_root: Path,
    *,
    problem_key: str,
    problem_id: str,
    verified: bool,
) -> None:
    problem_dir = asset_root / problem_key
    run_dir = problem_dir / "runs" / "2026-04-29-test-run"
    write_json(
        problem_dir / "problem.json",
        {
            "answer": False,
            "eq1_id": 13,
            "eq2_id": 2392,
            "equation1": "x = x * x",
            "equation2": "x = y * x",
            "id": problem_id,
            "problem_key": problem_key,
            "subset": "normal",
        },
    )
    write_json(
        run_dir / "countermodel.json",
        {
            "carrier": [0, 1],
            "order": 2,
            "source_path": "countermodels.jsonl",
            "table": [[0, 0], [1, 1]],
        },
    )
    certificate_path = run_dir / "certificate.lean"
    certificate_path.write_text(
        "theorem counterexample_certificate : True := by\n  trivial\n",
        encoding="utf-8",
    )
    write_json(
        run_dir / "verification.json",
        {
            "certificate_sha256": "test-sha",
            "executor_backend": "docker",
            "result": "passed" if verified else "failed",
        },
    )
    write_json(
        problem_dir / "latest.json",
        {
            "certificate_path": str(certificate_path),
            "countermodel_path": str(run_dir / "countermodel.json"),
            "run_id": "2026-04-29-test-run",
            "verification_path": str(run_dir / "verification.json"),
            "verified": verified,
        },
    )


def test_build_counterexample_evidence_bank_writes_compact_model_facing_jsonl(tmp_path: Path):
    asset_root = tmp_path / "assets" / "counterexamples"
    output = tmp_path / "evidence.jsonl"
    summary_output = tmp_path / "summary.json"
    write_counterexample_asset(
        asset_root,
        problem_key="eq1-13-eq2-2392",
        problem_id="normal_0001",
        verified=True,
    )

    summary = build_counterexample_evidence_bank(
        asset_root=asset_root,
        output_path=output,
        summary_output_path=summary_output,
    )

    rows = read_jsonl(output)
    written_summary = json.loads(summary_output.read_text(encoding="utf-8"))
    assert summary["written"] == 1
    assert written_summary["written"] == 1
    assert rows[0]["id"] == "normal_0001"
    assert rows[0]["problem_id"] == "normal_0001"
    assert rows[0]["problem_key"] == "eq1-13-eq2-2392"
    assert rows[0]["verdict"] == "false"
    assert rows[0]["evidence_type"] == "finite_magma_counterexample"
    assert rows[0]["countermodel"]["table"] == [[0, 0], [1, 1]]
    assert rows[0]["certificate_path"].endswith("certificate.lean")
    assert rows[0]["certificate_sha256"] == "test-sha"
    assert rows[0]["evidence"] == rows[0]["prompt_evidence"]
    assert "Required verdict: false" in rows[0]["evidence"]
    assert "row 0: [0, 0]" in rows[0]["evidence"]
    assert "satisfies Equation 13 and refutes Equation 2392" in rows[0]["evidence"]
    assert "theorem counterexample_certificate" not in rows[0]["evidence"]


def test_build_counterexample_evidence_bank_skips_unverified_assets_by_default(tmp_path: Path):
    asset_root = tmp_path / "assets" / "counterexamples"
    output = tmp_path / "evidence.jsonl"
    write_counterexample_asset(
        asset_root,
        problem_key="eq1-13-eq2-2392",
        problem_id="normal_0001",
        verified=True,
    )
    write_counterexample_asset(
        asset_root,
        problem_key="eq1-14-eq2-2393",
        problem_id="normal_0002",
        verified=False,
    )

    summary = build_counterexample_evidence_bank(asset_root=asset_root, output_path=output)

    rows = read_jsonl(output)
    assert summary["seen_assets"] == 2
    assert summary["skipped_unverified"] == 1
    assert [row["problem_id"] for row in rows] == ["normal_0001"]


def test_build_counterexample_evidence_bank_can_include_lean_excerpt(tmp_path: Path):
    asset_root = tmp_path / "assets" / "counterexamples"
    output = tmp_path / "evidence.jsonl"
    write_counterexample_asset(
        asset_root,
        problem_key="eq1-13-eq2-2392",
        problem_id="normal_0001",
        verified=True,
    )

    build_counterexample_evidence_bank(
        asset_root=asset_root,
        output_path=output,
        max_certificate_chars=32,
    )

    row = read_jsonl(output)[0]
    assert "Lean certificate excerpt" in row["evidence"]
    assert row["certificate_excerpt"].startswith("theorem counterexample")


def test_build_counterexample_evidence_bank_script_help_runs_when_invoked_by_path():
    root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [sys.executable, "scripts/counterexample/build_counterexample_evidence_bank.py", "--help"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
