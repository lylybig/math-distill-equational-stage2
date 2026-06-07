from pathlib import Path
import subprocess
import sys

from math_distill_stage2.official_stage2_judge import (
    load_official_stage2_verify_module,
    verify_official_stage2_answer,
)


def test_official_stage2_judge_adapter_accepts_project_judge_call_shape():
    problem = {
        "id": "adapter_smoke",
        "eq1_id": 1,
        "eq2_id": 2,
        "equation1": "x = x",
        "equation2": "x = x",
    }

    result = verify_official_stage2_answer(
        problem,
        {"call": "judge", "verdict": "maybe", "code": "def submission : True := trivial"},
        judge_repo=Path("external/equational-theories-lean-stage2"),
    )

    assert result.status == "malformed"
    assert result.error_code == "INVALID_VERDICT"
    assert result.raw["status"] == "malformed"


def test_official_stage2_judge_lean_path_falls_back_after_lake_env_timeout(
    monkeypatch, tmp_path: Path
):
    module = load_official_stage2_verify_module(Path("external/equational-theories-lean-stage2"))
    module._LAKE_LEAN_PATH_CACHE.clear()
    monkeypatch.delenv("JUDGE_LEAN_PATH", raising=False)

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs.get("timeout"))

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(module, "_static_lake_lean_path", lambda: "static-lean-path")

    config = module.JudgeConfig(lake_bin=tmp_path / "lake")

    assert module._get_lake_lean_path(config) == "static-lean-path"


def test_official_stage2_certificate_cli_help_runs():
    root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [sys.executable, "scripts/lean_certificates/verify_official_stage2_certificate.py", "--help"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "--problem" in result.stdout
    assert "--answer" in result.stdout
    assert "--judge-repo" in result.stdout
