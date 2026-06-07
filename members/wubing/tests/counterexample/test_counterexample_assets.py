import json
import subprocess
import sys
from pathlib import Path

from math_distill_stage2.counterexample.assets import export_counterexample_assets
from math_distill_stage2.dataset_io import read_jsonl, write_jsonl


def test_export_counterexample_assets_writes_problem_run_and_global_index(tmp_path: Path):
    verified = tmp_path / "verified_counterexamples.jsonl"
    output_root = tmp_path / "assets" / "counterexamples"
    write_jsonl(
        verified,
        [
            {
                "id": "normal_0003",
                "subset": "normal",
                "eq1_id": 649,
                "eq2_id": 2608,
                "equation1": "x = x * (y * ((z * x) * x))",
                "equation2": "x = (y * ((z * z) * y)) * w",
                "eq1_signature": "v0=(v0*(v1*((v2*v0)*v0)))",
                "eq2_signature": "v0=((v1*((v2*v2)*v1))*v3)",
                "answer": False,
                "countermodel": {
                    "order": 2,
                    "table": [[0, 0], [1, 1]],
                    "source_path": "countermodels.jsonl",
                },
                "lean": {
                    "theorem_name": "stage2_negative_cert_normal_0003",
                    "verified": True,
                },
            }
        ],
    )

    summary = export_counterexample_assets(
        verified_counterexamples_path=verified,
        output_root=output_root,
        run_id="2026-04-29-000004-pure-lean-order2",
        created_at_utc="2026-04-29T00:00:04Z",
        verify=False,
    )

    problem_dir = output_root / "eq1-649-eq2-2608"
    run_dir = problem_dir / "runs" / "2026-04-29-000004-pure-lean-order2"
    problem = json.loads((problem_dir / "problem.json").read_text(encoding="utf-8"))
    latest = json.loads((problem_dir / "latest.json").read_text(encoding="utf-8"))
    countermodel = json.loads((run_dir / "countermodel.json").read_text(encoding="utf-8"))
    metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    verification = json.loads((run_dir / "verification.json").read_text(encoding="utf-8"))
    certificate = (run_dir / "certificate.lean").read_text(encoding="utf-8")
    index_rows = read_jsonl(output_root / "index.jsonl")

    assert summary["exported"] == 1
    assert problem["problem_key"] == "eq1-649-eq2-2608"
    assert problem["equation1"] == "x = x * (y * ((z * x) * x))"
    assert countermodel["table"] == [[0, 0], [1, 1]]
    assert metadata["imports"] == []
    assert metadata["pure_lean"] is True
    assert verification["result"] == "not_run"
    assert latest["run_id"] == "2026-04-29-000004-pure-lean-order2"
    assert latest["verified"] is False
    assert "import " not in certificate
    assert "abbrev Equation649" in certificate
    assert index_rows == [
        {
            "certificate_path": str(run_dir / "certificate.lean"),
            "eq1_id": 649,
            "eq2_id": 2608,
            "latest_run_id": "2026-04-29-000004-pure-lean-order2",
            "problem_key": "eq1-649-eq2-2608",
            "verified": False,
        }
    ]


def test_export_counterexample_assets_script_help_runs_when_invoked_by_path():
    root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [sys.executable, "scripts/counterexample/export_counterexample_assets.py", "--help"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
