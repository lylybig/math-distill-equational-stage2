from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
from types import ModuleType
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STAGE2_JUDGE_REPO = REPO_ROOT / "external" / "equational-theories-lean-stage2"
PUBLIC_JUDGE_STATUSES = frozenset(
    {"accepted", "unparsed", "malformed", "incomplete_proof", "incorrect"}
)
DEFAULT_OFFICIAL_STAGE2_PROOF_POLICY: dict[str, list[str]] = {
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
}

_MODULE_CACHE: dict[Path, ModuleType] = {}


@dataclass(frozen=True)
class OfficialStage2JudgeResult:
    status: str
    error_code: str
    message: str
    verdict: str | None
    artifact_path: Path | None
    direct_declarations: tuple[str, ...]
    axioms: tuple[str, ...]
    stdout: str
    stderr: str
    raw: dict[str, Any]


def verify_official_stage2_answer(
    problem: dict[str, Any],
    answer: dict[str, Any] | str,
    *,
    judge_repo: Path = DEFAULT_STAGE2_JUDGE_REPO,
    config: Any | None = None,
) -> OfficialStage2JudgeResult:
    """Verify a Stage 2 answer with the official `judge/verify.py` implementation.

    `answer` may be either the official raw answer JSON string
    `{"verdict": "...", "code": "..."}` or this project's parsed judge-call
    shape `{"call": "judge", "verdict": "...", "code": "..."}`.
    """
    module = load_official_stage2_verify_module(judge_repo)
    problem = ensure_official_stage2_problem_defaults(problem)
    raw_answer = _to_official_raw_answer(answer)
    if config is None:
        config = build_official_stage2_judge_config(judge_repo=judge_repo)
    raw_result = module.verify_answer(problem, raw_answer, config=config)
    return _normalize_result(raw_result)


def ensure_official_stage2_problem_defaults(problem: dict[str, Any]) -> dict[str, Any]:
    """Mirror `pipeline.proxy._to_judge_problem` defaults for local adapters."""
    normalized = dict(problem)
    if not normalized.get("proof_policy"):
        normalized["proof_policy"] = {
            key: list(value) for key, value in DEFAULT_OFFICIAL_STAGE2_PROOF_POLICY.items()
        }
    return normalized


def load_official_stage2_verify_module(judge_repo: Path = DEFAULT_STAGE2_JUDGE_REPO) -> ModuleType:
    verify_path = (judge_repo / "judge" / "verify.py").resolve()
    if verify_path in _MODULE_CACHE:
        return _MODULE_CACHE[verify_path]
    if not verify_path.exists():
        raise FileNotFoundError(f"official Stage 2 verify.py not found: {verify_path}")

    digest = hashlib.sha256(str(verify_path).encode("utf-8")).hexdigest()[:12]
    module_name = f"_math_distill_stage2_official_verify_{digest}"
    spec = importlib.util.spec_from_file_location(module_name, verify_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load official Stage 2 verify module from {verify_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    _MODULE_CACHE[verify_path] = module
    return module


def build_official_stage2_judge_config(
    *,
    judge_repo: Path = DEFAULT_STAGE2_JUDGE_REPO,
    lean_bin: Path | None = None,
    lake_bin: Path | None = None,
    artifact_dir: Path | None = None,
    lean_timeout_seconds: int | None = None,
    max_code_length: int | None = None,
    max_false_cert_bytes: int | None = None,
) -> Any:
    module = load_official_stage2_verify_module(judge_repo)
    defaults = module.JudgeConfig()
    return module.JudgeConfig(
        lean_bin=lean_bin or _resolve_elan_binary(judge_repo, "lean") or defaults.lean_bin,
        lake_bin=lake_bin or _resolve_elan_binary(judge_repo, "lake") or defaults.lake_bin,
        artifact_dir=artifact_dir or defaults.artifact_dir,
        lean_timeout_seconds=(
            lean_timeout_seconds if lean_timeout_seconds is not None else defaults.lean_timeout_seconds
        ),
        max_code_length=max_code_length if max_code_length is not None else defaults.max_code_length,
        max_false_cert_bytes=(
            max_false_cert_bytes if max_false_cert_bytes is not None else defaults.max_false_cert_bytes
        ),
    )


def _resolve_elan_binary(judge_repo: Path, tool: str) -> Path | None:
    if shutil.which("elan") is None:
        return None
    try:
        proc = subprocess.run(
            ["elan", "which", tool],
            cwd=judge_repo,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    path = proc.stdout.strip()
    if proc.returncode == 0 and path:
        return Path(path)
    return None


def _to_official_raw_answer(answer: dict[str, Any] | str) -> str:
    if isinstance(answer, str):
        return answer
    if not isinstance(answer, dict):
        raise TypeError("answer must be a dict or raw JSON string")

    payload = dict(answer)
    call = payload.pop("call", None)
    if call is not None and call != "judge":
        raise ValueError("answer.call must be 'judge' when present")
    official_payload = {
        "verdict": payload.get("verdict"),
        "code": payload.get("code"),
    }
    return json.dumps(official_payload, ensure_ascii=False)


def _normalize_result(raw_result: dict[str, Any]) -> OfficialStage2JudgeResult:
    status = str(raw_result.get("status") or "")
    if status not in PUBLIC_JUDGE_STATUSES:
        raise ValueError(f"unexpected official Stage 2 judge status: {status!r}")
    artifact_raw = raw_result.get("artifact_path")
    return OfficialStage2JudgeResult(
        status=status,
        error_code=str(raw_result.get("error_code") or ""),
        message=str(raw_result.get("message") or ""),
        verdict=raw_result.get("verdict") if isinstance(raw_result.get("verdict"), str) else None,
        artifact_path=Path(artifact_raw) if isinstance(artifact_raw, str) and artifact_raw else None,
        direct_declarations=tuple(str(item) for item in raw_result.get("direct_declarations", [])),
        axioms=tuple(str(item) for item in raw_result.get("axioms", [])),
        stdout=str(raw_result.get("stdout") or ""),
        stderr=str(raw_result.get("stderr") or ""),
        raw=dict(raw_result),
    )
