from __future__ import annotations

from pathlib import Path

from judge_v2.worker.verifier import verify_answer_blocking


def test_verify_answer_blocking_uses_deleted_temp_artifacts_by_default(tmp_path: Path):
    repo = _fake_judge_repo(tmp_path)

    result = verify_answer_blocking(
        judge_repo=str(repo),
        problem={"id": "p1"},
        verdict="true",
        code="exact trivial",
        timeout_seconds=1,
        lean_bin="lean",
        lake_bin="lake",
        artifact_dir=None,
        max_code_length=None,
        max_false_cert_bytes=None,
    )

    artifact_path = Path(result["artifact_path"])
    assert result["status"] == "accepted"
    assert artifact_path.name == "sentinel.txt"
    assert not artifact_path.exists()


def test_verify_answer_blocking_keeps_explicit_artifact_dir(tmp_path: Path):
    repo = _fake_judge_repo(tmp_path)
    artifact_dir = tmp_path / "artifacts"

    result = verify_answer_blocking(
        judge_repo=str(repo),
        problem={"id": "p1"},
        verdict="true",
        code="exact trivial",
        timeout_seconds=1,
        lean_bin="lean",
        lake_bin="lake",
        artifact_dir=str(artifact_dir),
        max_code_length=None,
        max_false_cert_bytes=None,
    )

    artifact_path = Path(result["artifact_path"])
    assert result["status"] == "accepted"
    assert artifact_path == artifact_dir / "sentinel.txt"
    assert artifact_path.read_text(encoding="utf-8") == "artifact"


def _fake_judge_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "official"
    judge_dir = repo / "judge"
    judge_dir.mkdir(parents=True)
    (judge_dir / "verify.py").write_text(
        """
from pathlib import Path


class JudgeConfig:
    def __init__(
        self,
        lean_bin=Path("lean"),
        lake_bin=Path("lake"),
        lean_timeout_seconds=120,
        artifact_dir=Path(".artifacts"),
        max_code_length=50000,
        max_false_cert_bytes=10000,
    ):
        self.lean_bin = Path(lean_bin)
        self.lake_bin = Path(lake_bin)
        self.lean_timeout_seconds = lean_timeout_seconds
        self.artifact_dir = Path(artifact_dir)
        self.max_code_length = max_code_length
        self.max_false_cert_bytes = max_false_cert_bytes


def verify_answer(problem, raw_answer, config):
    config.artifact_dir.mkdir(parents=True, exist_ok=True)
    path = config.artifact_dir / "sentinel.txt"
    path.write_text("artifact", encoding="utf-8")
    return {
        "status": "accepted",
        "error_code": "ACCEPTED",
        "message": "ok",
        "artifact_path": str(path),
    }
""".lstrip(),
        encoding="utf-8",
    )
    return repo
