from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any


_MODULE_CACHE: dict[Path, ModuleType] = {}


def verify_answer_blocking(
    *,
    judge_repo: str,
    problem: dict[str, Any],
    verdict: str,
    code: str,
    timeout_seconds: int,
    lean_bin: str,
    lake_bin: str,
    artifact_dir: str | None,
    max_code_length: int | None,
    max_false_cert_bytes: int | None,
) -> dict[str, Any]:
    """Run the official judge in a worker process and return a serializable envelope."""
    repo = Path(judge_repo).expanduser().resolve()
    temp_artifacts: tempfile.TemporaryDirectory[str] | None = None
    try:
        module = load_official_verify_module(repo)
        raw_answer = json.dumps({"verdict": verdict, "code": code}, ensure_ascii=False)
        effective_artifact_dir = artifact_dir
        if effective_artifact_dir is None:
            temp_artifacts = tempfile.TemporaryDirectory(prefix="judge_v2_artifacts_")
            effective_artifact_dir = temp_artifacts.name
        config = build_judge_config(
            module=module,
            repo=repo,
            timeout_seconds=timeout_seconds,
            lean_bin=lean_bin,
            lake_bin=lake_bin,
            artifact_dir=effective_artifact_dir,
            max_code_length=max_code_length,
            max_false_cert_bytes=max_false_cert_bytes,
        )
        result = module.verify_answer(problem, raw_answer, config)
        if not isinstance(result, dict):
            raise TypeError(f"verify_answer returned {type(result).__name__}, expected dict")
        return result
    except Exception as exc:  # noqa: BLE001 - returned to parent for HTTP mapping
        return {
            "_judge_v2_exception": {
                "type": type(exc).__name__,
                "message": str(exc),
            }
        }
    finally:
        if temp_artifacts is not None:
            temp_artifacts.cleanup()


def load_official_verify_module(judge_repo: Path) -> ModuleType:
    verify_path = (judge_repo / "judge" / "verify.py").resolve()
    if verify_path in _MODULE_CACHE:
        return _MODULE_CACHE[verify_path]
    if not verify_path.exists():
        raise FileNotFoundError(f"official Stage 2 verify.py not found: {verify_path}")

    digest = hashlib.sha256(str(verify_path).encode("utf-8")).hexdigest()[:12]
    module_name = f"_judge_v2_official_verify_{digest}"
    spec = importlib.util.spec_from_file_location(module_name, verify_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load official Stage 2 verify module from {verify_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    inserted = False
    repo_text = str(judge_repo)
    if repo_text not in sys.path:
        sys.path.insert(0, repo_text)
        inserted = True
    try:
        spec.loader.exec_module(module)
    finally:
        if inserted:
            try:
                sys.path.remove(repo_text)
            except ValueError:
                pass
    _MODULE_CACHE[verify_path] = module
    return module


def build_judge_config(
    *,
    module: ModuleType,
    repo: Path,
    timeout_seconds: int,
    lean_bin: str,
    lake_bin: str,
    artifact_dir: str | None,
    max_code_length: int | None,
    max_false_cert_bytes: int | None,
) -> Any:
    defaults = module.JudgeConfig()
    kwargs: dict[str, Any] = {
        "lean_bin": Path(lean_bin),
        "lake_bin": Path(lake_bin),
        "lean_timeout_seconds": timeout_seconds,
        "max_code_length": (
            max_code_length if max_code_length is not None else defaults.max_code_length
        ),
        "max_false_cert_bytes": (
            max_false_cert_bytes
            if max_false_cert_bytes is not None
            else defaults.max_false_cert_bytes
        ),
    }
    if artifact_dir is not None:
        kwargs["artifact_dir"] = Path(artifact_dir)
    else:
        kwargs["artifact_dir"] = defaults.artifact_dir

    if lean_bin == "lean":
        elan_lean = _resolve_elan_binary(repo, "lean")
        if elan_lean is not None:
            kwargs["lean_bin"] = elan_lean
    if lake_bin == "lake":
        elan_lake = _resolve_elan_binary(repo, "lake")
        if elan_lake is not None:
            kwargs["lake_bin"] = elan_lake
    return module.JudgeConfig(**kwargs)


def judge_code_rev(judge_repo: Path) -> str:
    verify_path = judge_repo / "judge" / "verify.py"
    try:
        return hashlib.sha256(verify_path.read_bytes()).hexdigest()[:12]
    except OSError:
        return "unknown"


def lean_version(lean_bin: str, judge_repo: Path) -> str:
    try:
        proc = subprocess.run(
            [lean_bin, "--version"],
            cwd=judge_repo if judge_repo.exists() else None,
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except Exception:  # noqa: BLE001
        return "unknown"
    if proc.stdout.strip():
        return proc.stdout.strip()
    return "unknown"


def mathlib_rev(judge_repo: Path) -> str:
    manifest = judge_repo / ".lake" / "manifest.json"
    if not manifest.exists():
        manifest = judge_repo / "lake-manifest.json"
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        for package in data.get("packages", []):
            if package.get("name") == "mathlib":
                return str(package.get("rev", "unknown"))[:12]
    except Exception:  # noqa: BLE001
        pass
    return "unknown"


def service_rev(*, judge_repo: Path, lean_bin: str) -> str:
    version = lean_version(lean_bin, judge_repo)
    version_hash = hashlib.sha256(version.encode("utf-8")).hexdigest()[:8]
    return f"judge-{judge_code_rev(judge_repo)}-lean-{version_hash}-mathlib-{mathlib_rev(judge_repo)}"


def _resolve_elan_binary(judge_repo: Path, tool: str) -> Path | None:
    if shutil.which("elan") is None:
        return None
    try:
        proc = subprocess.run(
            ["elan", "which", tool],
            cwd=judge_repo if judge_repo.exists() else None,
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    path = proc.stdout.strip()
    if proc.returncode == 0 and path:
        return Path(path)
    return None
