import json
import subprocess
import sys
from pathlib import Path

from math_distill_stage2.counterexample.verifier import verify_counterexample_assets
from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.lean_executor import LeanExecutionResult, LeanTask
from math_distill_stage2.counterexample.verified_index import file_sha256


class FakePassingExecutor:
    backend = "fake"

    def __init__(self) -> None:
        self.tasks: list[LeanTask] = []

    def execute(self, task: LeanTask) -> LeanExecutionResult:
        self.tasks.append(task)
        return LeanExecutionResult(
            checked_at_utc="2026-04-29T00:00:00Z",
            executor_backend=self.backend,
            command=["fake-lean", str(task.certificate_path)],
            result="passed",
            returncode=0,
            stdout="",
            stderr="",
            timeout_seconds=task.timeout_seconds,
            elapsed_seconds=0.01,
            certificate_sha256=file_sha256(task.certificate_path),
        )


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def test_verify_counterexample_assets_updates_run_and_indexes(tmp_path: Path):
    root = tmp_path / "data" / "assets" / "counterexamples"
    run_id = "2026-04-29-000004-pure-lean-order2"
    problem_key = "eq1-1-eq2-2"
    run_dir = root / problem_key / "runs" / run_id
    certificate = run_dir / "certificate.lean"
    certificate.parent.mkdir(parents=True)
    certificate.write_text("#check Nat\n", encoding="utf-8")
    write_json(
        root / problem_key / "latest.json",
        {
            "run_id": run_id,
            "certificate_path": str(certificate),
            "verification_path": str(run_dir / "verification.json"),
            "verified": False,
        },
    )
    write_jsonl(
        root / "index.jsonl",
        [
            {
                "problem_key": problem_key,
                "eq1_id": 1,
                "eq2_id": 2,
                "latest_run_id": run_id,
                "certificate_path": str(certificate),
                "verified": False,
            }
        ],
    )
    write_json(
        root / "summary.json",
        {
            "schema_version": 1,
            "run_id": run_id,
            "exported": 1,
            "verified": 0,
            "output_root": str(root),
        },
    )
    executor = FakePassingExecutor()

    summary = verify_counterexample_assets(
        root=root,
        run_id=run_id,
        executor=executor,
        workers=2,
        timeout_seconds=17,
    )

    verification = json.loads((run_dir / "verification.json").read_text(encoding="utf-8"))
    latest = json.loads((root / problem_key / "latest.json").read_text(encoding="utf-8"))
    index_rows = read_jsonl(root / "index.jsonl")
    summary_file = json.loads((root / "summary.json").read_text(encoding="utf-8"))

    assert [task.certificate_path for task in executor.tasks] == [certificate]
    assert executor.tasks[0].timeout_seconds == 17
    assert verification["result"] == "passed"
    assert verification["executor_backend"] == "fake"
    assert latest["verified"] is True
    assert index_rows[0]["verified"] is True
    assert summary["checked"] == 1
    assert summary["passed"] == 1
    assert summary_file["verified"] == 1
    assert summary_file["verification_backend"] == "fake"
    assert summary_file["verification_workers"] == 2


def test_verify_counterexample_assets_script_help_runs_when_invoked_by_path():
    root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [sys.executable, "scripts/counterexample/verify_counterexample_assets.py", "--help"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
