import subprocess
from pathlib import Path

from math_distill_stage2.lean_executor import DockerLeanExecutor, LeanTask
from math_distill_stage2.official_stage2_batch import DEFAULT_OFFICIAL_STAGE2_JUDGE_IMAGE


def write_certificate(tmp_path: Path) -> Path:
    certificate = tmp_path / "certificate.lean"
    certificate.write_text("#check Nat\n", encoding="utf-8")
    return certificate


def test_docker_lean_executor_runs_certificate_in_readonly_workdir(
    monkeypatch, tmp_path: Path
):
    certificate = write_certificate(tmp_path)
    calls = []

    def fake_run(command, text, capture_output, check, timeout):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = DockerLeanExecutor(
        image="lean4-executor:test",
        cpu_limit="0.5",
        memory_limit="256m",
    ).execute(LeanTask(certificate_path=certificate, timeout_seconds=9))
    payload = result.to_json()
    command = calls[0]

    assert command[:4] == ["docker", "run", "--rm", "--network"]
    assert "none" in command
    assert "--cpus" in command
    assert "0.5" in command
    assert "--memory" in command
    assert "256m" in command
    assert "-v" in command
    assert f"{certificate.parent.resolve()}:/work:ro" in command
    assert command[-3:] == ["lean4-executor:test", "lean", "/work/certificate.lean"]
    assert payload["executor_backend"] == "docker"
    assert payload["lean_image"] == "lean4-executor:test"
    assert payload["cpu_limit"] == "0.5"
    assert payload["memory_limit"] == "256m"
    assert payload["result"] == "passed"


def test_docker_lean_executor_reports_timeout(monkeypatch, tmp_path: Path):
    certificate = write_certificate(tmp_path)

    def fake_run(command, text, capture_output, check, timeout):
        raise subprocess.TimeoutExpired(
            cmd=command,
            timeout=timeout,
            output="partial stdout",
            stderr="partial stderr",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = DockerLeanExecutor(image="lean4-executor:test").execute(
        LeanTask(certificate_path=certificate, timeout_seconds=3)
    )
    payload = result.to_json()

    assert payload["executor_backend"] == "docker"
    assert payload["result"] == "timeout"
    assert payload["returncode"] is None
    assert payload["timeout_seconds"] == 3
    assert "timed out" in payload["stderr"]


def test_docker_lean_executor_default_image_uses_official_stage2_judge_image(
    monkeypatch, tmp_path: Path
):
    certificate = write_certificate(tmp_path)
    calls = []

    def fake_run(command, text, capture_output, check, timeout):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = DockerLeanExecutor().execute(LeanTask(certificate_path=certificate))
    payload = result.to_json()

    assert DEFAULT_OFFICIAL_STAGE2_JUDGE_IMAGE in calls[0]
    assert payload["lean_image"] == DEFAULT_OFFICIAL_STAGE2_JUDGE_IMAGE


def test_legacy_lean4_executor_dockerfile_extends_official_stage2_judge_image():
    dockerfile = Path("docker/lean4-executor/Dockerfile").read_text(encoding="utf-8")

    assert "OFFICIAL_STAGE2_JUDGE_IMAGE=math-distill-stage2-official-judge:official-6805e23" in dockerfile
    assert "FROM ${OFFICIAL_STAGE2_JUDGE_IMAGE}" in dockerfile
    assert "LEAN_VERSION=v4.29.1" not in dockerfile
