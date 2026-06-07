import json
import subprocess
import sys
import time
from pathlib import Path

from math_distill_stage2.dataset_io import write_jsonl
from math_distill_stage2.official_stage2_batch import (
    DEFAULT_OFFICIAL_STAGE2_JUDGE_IMAGE,
    DEFAULT_REMOTE_JUDGE_V2_BASE_URLS,
    RemoteOfficialStage2BatchConfig,
    RemoteJudgeV2Config,
    make_remote_official_stage2_batch_judge,
    make_remote_judge_v2_batch_judge,
    resolve_remote_judge_v2_base_urls,
    select_remote_judge_v2_base_url,
    extract_official_verification_input,
    run_remote_official_stage2_batch,
    run_docker_official_stage2_batch,
    verify_official_stage2_records,
)


def test_extracts_evaluator_record_for_official_stage2_batch_verify():
    record = {
        "problem_id": "normal_0001",
        "input_index": 3,
        "repeat_index": 1,
        "eq1_id": 4,
        "eq2_id": 3,
        "equation1": "x = x * y",
        "equation2": "x = x * x",
        "judge_call": {
            "call": "judge",
            "verdict": "true",
            "code": "import JudgeProblem\n\ndef submission : Goal := by\n  intro G inst h\n  exact h",
        },
    }

    item = extract_official_verification_input(record)

    assert item.problem == {
        "id": "normal_0001",
        "eq1_id": 4,
        "eq2_id": 3,
        "equation1": "x = x * y",
        "equation2": "x = x * x",
        "proof_policy": {
            "allowed_axioms": ["propext", "Quot.sound", "Classical.choice"],
            "allowed_declarations": ["letFun"],
            "allowed_declaration_prefixes": [
                "And.",
                "Bool.",
                "Classical.",
                "Decidable.",
                "Eq.",
                "EquationLHS",
                "EquationRHS",
                "Goal",
                "Exists.",
                "False.",
                "Fin.",
                "Fintype.",
                "Function.",
                "HEq.",
                "Iff.",
                "Init.",
                "Int.",
                "Lean.",
                "List.",
                "Magma.",
                "Mathlib.",
                "MemoFinOp.",
                "Nat.",
                "Nonempty.",
                "Not.",
                "NthRewrites.",
                "OfNat.",
                "Option.",
                "Or.",
                "Prod.",
                "PUnit.",
                "RewriteCombinations.",
                "RewriteGoal.",
                "RewriteHypothesis.",
                "RewriteHypothesisAndGoal.",
                "SimpleRewrites.",
                "Std.",
                "Subgraph.",
                "Subtype.",
                "Sum.",
                "Trans.",
                "True.",
                "Unit.",
                "JudgeDecide.",
                "JudgeFinOp.",
                "JudgeMagma.",
                "inst",
                "of_decide_",
                "submission.",
                "congrArg",
                "congr_arg",
                "eq_self",
                "of_eq_true",
                "id",
                "eq_comm",
                "eq_mp",
                "eq_mpr",
                "rfl",
                "absurd",
            ],
        },
    }
    assert item.answer["call"] == "judge"
    assert item.answer["verdict"] == "true"
    assert item.problem_id == "normal_0001"
    assert item.repeat_index == 1
    assert len(item.code_sha256) == 64


def test_docker_official_stage2_batch_runs_one_container_with_mounted_paths(monkeypatch, tmp_path: Path):
    input_path = tmp_path / "input" / "per_run.jsonl"
    output_path = tmp_path / "output" / "official_verify.jsonl"
    artifact_dir = tmp_path / "artifacts"
    write_jsonl(input_path, [{"problem_id": "p1"}])
    calls = []

    def fake_run(command, text, capture_output, check, timeout):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = run_docker_official_stage2_batch(
        input_path=input_path,
        output_path=output_path,
        artifact_dir=artifact_dir,
        image="stage2-official-judge:test",
        max_workers=2,
        cpu_limit="2",
        memory_limit="4g",
        timeout_seconds=123,
        resume=True,
    )

    command = calls[0]
    assert result.returncode == 0
    assert command[:4] == ["docker", "run", "--rm", "--network"]
    assert "none" in command
    assert ["--cpus", "2"] == command[command.index("--cpus") : command.index("--cpus") + 2]
    assert ["--memory", "4g"] == command[command.index("--memory") : command.index("--memory") + 2]
    assert f"{input_path.parent.resolve()}:/input:ro" in command
    assert f"{output_path.parent.resolve()}:/output" in command
    assert f"{artifact_dir.resolve()}:/artifacts" in command
    assert "stage2-official-judge:test" in command
    assert "/workspace/scripts/lean_certificates/verify_official_stage2_batch_worker.py" in command
    assert "--judge-repo" in command
    assert "/opt/equational-theories-lean-stage2" in command
    assert "--resume" in command


def test_default_official_stage2_judge_image_uses_fixed_official_commit_tag():
    assert DEFAULT_OFFICIAL_STAGE2_JUDGE_IMAGE == "math-distill-stage2-official-judge:official-6805e23"


def test_official_stage2_records_writer_emits_jsonl_and_summary(tmp_path: Path):
    records = [
        {
            "problem_id": "p_ok",
            "eq1_id": 1,
            "eq2_id": 1,
            "equation1": "x = x",
            "equation2": "x = x",
            "judge_call": {"call": "judge", "verdict": "true", "code": "def submission : True := trivial"},
        },
        {
            "problem_id": "p_bad",
            "eq1_id": 1,
            "eq2_id": 2,
            "equation1": "x = x",
            "equation2": "x = x",
            "judge_call": {"call": "judge", "verdict": "maybe", "code": "bad"},
        },
    ]
    output_path = tmp_path / "official_verify.jsonl"
    summary_path = tmp_path / "summary.json"

    def fake_verify(problem, answer):
        if answer["verdict"] == "true":
            return {
                "status": "accepted",
                "error_code": "ACCEPTED",
                "message": "ok",
                "verdict": "true",
                "artifact_path": "/artifacts/p_ok",
                "direct_declarations": [],
                "axioms": [],
            }
        return {
            "status": "malformed",
            "error_code": "INVALID_VERDICT",
            "message": "bad verdict",
            "verdict": None,
            "artifact_path": None,
            "direct_declarations": [],
            "axioms": [],
        }

    summary = verify_official_stage2_records(
        records,
        output_path=output_path,
        summary_path=summary_path,
        verify_fn=fake_verify,
    )

    rows = [line for line in output_path.read_text(encoding="utf-8").splitlines() if line]
    assert len(rows) == 2
    assert summary["status_counts"] == {"accepted": 1, "malformed": 1}
    assert summary["error_code_counts"] == {"ACCEPTED": 1, "INVALID_VERDICT": 1}
    assert summary["accepted_count"] == 1
    assert summary["total_count"] == 2
    assert summary_path.exists()


def test_docker_batch_cli_help_runs():
    root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [sys.executable, "scripts/lean_certificates/verify_official_stage2_batch.py", "--help"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "--input" in result.stdout
    assert "--output" in result.stdout
    assert "--artifact-dir" in result.stdout
    assert "--image" in result.stdout


def test_order5_paircheck_remote_smoke_cli_help_runs():
    root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [
            sys.executable,
            "scripts/lean_certificates/verify_order5_paircheck_remote_smoke.py",
            "--help",
        ],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "--input" in result.stdout
    assert "--output" in result.stdout
    assert "--base-url" in result.stdout
    assert "--base-urls" in result.stdout


def test_remote_judge_v2_defaults_to_control_service_8890():
    assert DEFAULT_REMOTE_JUDGE_V2_BASE_URLS == ("http://10.220.69.172:8890",)
    assert resolve_remote_judge_v2_base_urls(environ={}) == DEFAULT_REMOTE_JUDGE_V2_BASE_URLS


def test_remote_judge_v2_endpoint_precedence_and_health_selection():
    assert resolve_remote_judge_v2_base_urls(
        base_url="http://one:8890",
        base_urls="http://two:8890,http://three:8890",
        environ={
            "STAGE2_REMOTE_JUDGE_V2_BASE_URLS": "http://env-pool:8890",
            "STAGE2_REMOTE_JUDGE_V2_BASE_URL": "http://env-single:8890",
        },
    ) == ("http://one:8890",)
    assert resolve_remote_judge_v2_base_urls(
        base_urls="http://two:8890, http://three:8890/",
        environ={},
    ) == ("http://two:8890", "http://three:8890")
    assert resolve_remote_judge_v2_base_urls(
        environ={"STAGE2_REMOTE_JUDGE_V2_BASE_URLS": "http://env-a:8890,http://env-b:8890"},
    ) == ("http://env-a:8890", "http://env-b:8890")

    selected = select_remote_judge_v2_base_url(
        ("http://busy:8890", "http://healthy:8890"),
        request_timeout_seconds=3,
        health_check=lambda url, timeout: url == "http://healthy:8890" and timeout == 3,
    )

    assert selected == "http://healthy:8890"


def test_remote_official_stage2_batch_uses_ssh_and_fetches_raw_results(
    monkeypatch, tmp_path: Path
):
    input_path = tmp_path / "input.jsonl"
    output_path = tmp_path / "official_verify.jsonl"
    artifact_dir = tmp_path / "artifacts"
    write_jsonl(
        input_path,
        [
            {
                "problem_id": "p1",
                "problem": {
                    "id": "p1",
                    "eq1_id": 1,
                    "eq2_id": 2,
                    "equation1": "x = x",
                    "equation2": "x = x",
                },
                "answer": {"call": "judge", "verdict": "true", "code": "def submission : True := trivial"},
            }
        ],
    )
    calls = []

    def fake_run(command, text, capture_output, check, timeout):
        calls.append(command)
        if command[0] == "scp" and command[1].startswith("gpu1:"):
            Path(command[2]).write_text(
                '{"problem_id":"p1","status":"accepted","error_code":"",'
                '"message":"","raw_result":{"status":"accepted","stdout":"","stderr":"",'
                '"message":"","error_code":""}}\n',
                encoding="utf-8",
            )
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = run_remote_official_stage2_batch(
        input_path=input_path,
        output_path=output_path,
        artifact_dir=artifact_dir,
        config=RemoteOfficialStage2BatchConfig(
            host="gpu1",
            repo="/srv/Math-Distill-Stage2",
            workdir="/tmp/proofbank-judge",
            python="python3",
            max_workers=2,
            cpu_limit="2",
            memory_limit="6g",
            job_id="job-1",
        ),
    )

    assert result["status_counts"] == {"accepted": 1}
    assert result["raw_results"] == [{"status": "accepted", "stdout": "", "stderr": "", "message": "", "error_code": ""}]
    assert output_path.exists()
    assert any(command[:2] == ["ssh", "gpu1"] and "verify_official_stage2_batch.py" in command[-1] for command in calls)
    assert any(command[:1] == ["scp"] and command[-1].startswith("gpu1:") for command in calls)
    assert any(command[:1] == ["scp"] and command[1].startswith("gpu1:") for command in calls)


def test_remote_official_stage2_batch_judge_returns_raw_results(monkeypatch, tmp_path: Path):
    calls = []

    def fake_run_remote_official_stage2_batch(**kwargs):
        calls.append(kwargs)
        return {
            "raw_results": [
                {"status": "accepted", "stdout": "", "stderr": "", "message": "", "error_code": ""},
                {"status": "incorrect", "stdout": "", "stderr": "type mismatch", "message": "", "error_code": ""},
            ]
        }

    monkeypatch.setattr(
        "math_distill_stage2.official_stage2_batch.run_remote_official_stage2_batch",
        fake_run_remote_official_stage2_batch,
    )

    judge = make_remote_official_stage2_batch_judge(
        RemoteOfficialStage2BatchConfig(
            host="gpu1",
            repo="/srv/Math-Distill-Stage2",
            workdir="/tmp/proofbank-judge",
            job_id="job-2",
        ),
        local_staging_root=tmp_path,
    )

    raw_results = judge(
        [
            (
                {"id": "p1", "eq1_id": 1, "eq2_id": 2, "equation1": "x = x", "equation2": "x = x"},
                {"call": "judge", "verdict": "true", "code": "code 1"},
            ),
            (
                {"id": "p2", "eq1_id": 1, "eq2_id": 3, "equation1": "x = x", "equation2": "x = y"},
                {"call": "judge", "verdict": "true", "code": "code 2"},
            ),
        ]
    )

    records = [json.loads(line) for line in calls[0]["input_path"].read_text(encoding="utf-8").splitlines()]
    assert raw_results[0]["status"] == "accepted"
    assert raw_results[1]["status"] == "incorrect"
    assert [record["problem_id"] for record in records] == ["p1", "p2"]
    assert records[0]["repeat_index"] == 0
    assert calls[0]["config"].host == "gpu1"


def test_remote_judge_v2_batch_judge_submits_certificate_jobs(monkeypatch):
    calls = []

    def fake_judge_v2_request(method, url, *, payload=None, timeout=None):
        calls.append({"method": method, "url": url, "payload": payload, "timeout": timeout})
        if method == "POST":
            assert url == "http://10.220.69.172:8890/jobs"
            assert payload["problem"]["id"] in {"p1", "p2"}
            assert "def submission" in payload["code"]
            return {"job_id": f"job-{payload['problem']['id']}", "status": "queued"}
        assert "/jobs/job-" in url
        assert "/wait?" in url
        if "job-p1" in url:
            return {
                "job_id": "job-p1",
                "status": "done",
                "result": {
                    "status": "accepted",
                    "error_code": "ACCEPTED",
                    "message": "ok",
                    "stdout": "",
                    "stderr": "",
                    "verdict": "true",
                    "control_backend_url": "http://10.220.69.172:8889",
                },
            }
        return {
            "job_id": "job-p2",
            "status": "done",
            "result": {
                "status": "incorrect",
                "error_code": "LEAN_REJECTED",
                "message": "type mismatch",
                "stdout": "",
                "stderr": "type mismatch",
                "verdict": "true",
            },
        }

    monkeypatch.setattr(
        "math_distill_stage2.official_stage2_batch._remote_judge_v2_json_request",
        fake_judge_v2_request,
    )

    judge = make_remote_judge_v2_batch_judge(
        RemoteJudgeV2Config(
            base_url="http://10.220.69.172:8890",
            max_workers=1,
            request_timeout_seconds=3,
            poll_interval_seconds=0.1,
        )
    )

    raw_results = judge(
        [
            (
                {"id": "p1", "eq1_id": 1, "eq2_id": 2, "equation1": "x = x", "equation2": "x = x"},
                {"call": "judge", "verdict": "true", "code": "def submission : True := by trivial"},
            ),
            (
                {"id": "p2", "eq1_id": 1, "eq2_id": 3, "equation1": "x = x", "equation2": "x = y"},
                {"call": "judge", "verdict": "true", "code": "def submission : True := by trivial"},
            ),
        ]
    )

    assert raw_results[0]["status"] == "accepted"
    assert raw_results[1]["status"] == "incorrect"
    assert raw_results[0]["remote_judge_v2"]["url"] == "http://10.220.69.172:8890/jobs/job-p1"
    assert raw_results[0]["remote_judge_v2"]["backend_url"] == "http://10.220.69.172:8889"
    assert [call["method"] for call in calls] == ["POST", "GET", "POST", "GET"]
    assert calls[0]["timeout"] == 3


def test_remote_judge_v2_batch_judge_runs_requests_concurrently(monkeypatch):
    calls = []

    def fake_run_remote_judge_v2_one(problem, answer, *, config, index):
        time.sleep(0.05)
        calls.append((problem["id"], index, config.max_workers))
        return {
            "status": "accepted",
            "stdout": "",
            "stderr": "",
            "message": "",
            "error_code": "",
        }

    monkeypatch.setattr(
        "math_distill_stage2.official_stage2_batch._run_remote_judge_v2_one",
        fake_run_remote_judge_v2_one,
    )
    judge = make_remote_judge_v2_batch_judge(
        RemoteJudgeV2Config(max_workers=4)
    )
    requests = [
        (
            {
                "id": f"p{index}",
                "eq1_id": 1,
                "eq2_id": 2,
                "equation1": "x = x",
                "equation2": "x = y",
            },
            {
                "call": "judge",
                "verdict": "true",
                "code": "def submission : True := by trivial",
            },
        )
        for index in range(4)
    ]

    start = time.perf_counter()
    raw_results = judge(requests)
    elapsed = time.perf_counter() - start

    assert [result["status"] for result in raw_results] == ["accepted"] * 4
    assert [call[0] for call in sorted(calls, key=lambda item: item[1])] == [
        "p0",
        "p1",
        "p2",
        "p3",
    ]
    assert elapsed < 0.15


def test_official_stage2_judge_dockerfile_pins_official_repo_and_worker():
    dockerfile = Path("docker/official-stage2-judge/Dockerfile").read_text(encoding="utf-8")

    assert "OFFICIAL_STAGE2_COMMIT=6805e2323018fbd8a85f41ca09fc33d74d5a02a5" in dockerfile
    assert "leanprover/lean4:${LEAN_VERSION}" in dockerfile
    assert "lake build JudgeMagma.Magma JudgeDecide.DecideBang JudgeFinOp.MemoFinOp JudgeSupport.Inspect" in dockerfile
    assert "verify_official_stage2_batch_worker.py" in dockerfile
