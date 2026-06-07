import importlib
import json
import sys
from pathlib import Path


def test_proxy_reuses_judge_call_cache_for_identical_problem_and_certificate(
    tmp_path: Path,
    monkeypatch,
):
    repo_root = Path(__file__).resolve().parents[2]
    official_repo = repo_root / "external" / "equational-theories-lean-stage2"
    monkeypatch.syspath_prepend(str(official_repo))
    proxy = importlib.import_module("pipeline.proxy")
    cache_path = tmp_path / "judge_calls.sqlite"
    calls = 0

    def fake_verify_answer(problem, raw_answer, config=None):
        nonlocal calls
        calls += 1
        assert problem["id"] == "p1"
        assert json.loads(raw_answer)["code"] == "theorem submission : True := by trivial"
        return {
            "status": "accepted",
            "message": "ok",
            "stderr": "",
        }

    monkeypatch.setattr(proxy, "verify_answer", fake_verify_answer)
    monkeypatch.setenv("STAGE2_JUDGE_CACHE_PATH", str(cache_path))
    problem = {
        "id": "p1",
        "eq1_id": 1,
        "eq2_id": 1,
        "equation1": "x = x",
        "equation2": "x = x",
    }

    first = proxy._call_judge(problem, "true", "theorem submission : True := by trivial")
    second = proxy._call_judge(problem, "true", "theorem submission : True := by trivial")

    assert calls == 1
    assert first["status"] == "accepted"
    assert second["status"] == "accepted"
    assert second["_cache_hit"] is True


def test_proxy_does_not_cache_judge_infrastructure_errors(
    tmp_path: Path,
    monkeypatch,
):
    repo_root = Path(__file__).resolve().parents[2]
    official_repo = repo_root / "external" / "equational-theories-lean-stage2"
    monkeypatch.syspath_prepend(str(official_repo))
    proxy = importlib.import_module("pipeline.proxy")
    verify = importlib.import_module("judge.verify")
    cache_path = tmp_path / "judge_calls.sqlite"
    calls = 0

    def fake_verify_answer(problem, raw_answer, config=None):
        nonlocal calls
        calls += 1
        raise verify.JudgeInfrastructureError("lean missing")

    monkeypatch.setattr(proxy, "verify_answer", fake_verify_answer)
    monkeypatch.setenv("STAGE2_JUDGE_CACHE_PATH", str(cache_path))
    problem = {
        "id": "p1",
        "eq1_id": 1,
        "eq2_id": 1,
        "equation1": "x = x",
        "equation2": "x = x",
    }

    first = proxy._call_judge(problem, "true", "bad")
    second = proxy._call_judge(problem, "true", "bad")

    assert calls == 2
    assert "judge infrastructure error" in first["error"]
    assert "judge infrastructure error" in second["error"]
