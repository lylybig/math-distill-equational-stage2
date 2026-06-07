import json
import subprocess
import sys
from pathlib import Path

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.counterexample.verified_index import build_verified_counterexample_index


def test_build_verified_counterexample_index_joins_problem_countermodel_and_lean_certificate(
    tmp_path: Path,
):
    problem_index = tmp_path / "public_problem_index.jsonl"
    countermodels = tmp_path / "countermodels.jsonl"
    certificate_run = tmp_path / "certificate-run"
    output = tmp_path / "verified_counterexamples.jsonl"
    summary_output = tmp_path / "verified_counterexamples.summary.json"
    certificate_path = certificate_run / "certificates" / "normal_0003.lean"
    certificate_path.parent.mkdir(parents=True)
    certificate_path.write_text(
        "theorem stage2_negative_cert_normal_0003 : True := by decide\n",
        encoding="utf-8",
    )

    write_jsonl(
        problem_index,
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
            }
        ],
    )
    write_jsonl(
        countermodels,
        [
            {
                "id": "normal_0003",
                "subset": "normal",
                "eq1_id": 649,
                "eq2_id": 2608,
                "order": 2,
                "table": [[0, 0], [1, 1]],
            }
        ],
    )
    write_jsonl(
        certificate_run / "certificate_index.jsonl",
        [
            {
                "id": "normal_0003",
                "subset": "normal",
                "eq1_id": 649,
                "eq2_id": 2608,
                "order": 2,
                "path": "certificates/normal_0003.lean",
                "theorem_name": "stage2_negative_cert_normal_0003",
            }
        ],
    )
    (certificate_run / "verification.json").write_text(
        json.dumps({"result": "passed", "command": "lake env lean batch.lean"}),
        encoding="utf-8",
    )

    summary = build_verified_counterexample_index(
        problem_index_path=problem_index,
        countermodels_path=countermodels,
        certificate_run_dir=certificate_run,
        output_path=output,
        summary_output_path=summary_output,
    )

    rows = read_jsonl(output)
    summary_on_disk = json.loads(summary_output.read_text(encoding="utf-8"))

    assert summary == summary_on_disk
    assert summary["verified_counterexamples"] == 1
    assert rows == [
        {
            "answer": False,
            "countermodel": {
                "order": 2,
                "source_path": str(countermodels),
                "table": [[0, 0], [1, 1]],
            },
            "eq1_id": 649,
            "eq1_signature": "v0=(v0*(v1*((v2*v0)*v0)))",
            "eq2_id": 2608,
            "eq2_signature": "v0=((v1*((v2*v2)*v1))*v3)",
            "equation1": "x = x * (y * ((z * x) * x))",
            "equation2": "x = (y * ((z * z) * y)) * w",
            "id": "normal_0003",
            "lean": {
                "batch_verification_result": "passed",
                "certificate_path": str(certificate_path),
                "certificate_sha256": rows[0]["lean"]["certificate_sha256"],
                "theorem_name": "stage2_negative_cert_normal_0003",
                "verified": True,
            },
            "subset": "normal",
        }
    ]
    assert len(rows[0]["lean"]["certificate_sha256"]) == 64


def test_build_verified_counterexample_index_script_help_runs_when_invoked_by_path():
    root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [sys.executable, "scripts/counterexample/build_verified_counterexample_index.py", "--help"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
