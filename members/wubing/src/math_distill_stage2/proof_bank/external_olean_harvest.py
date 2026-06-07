from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import textwrap
from typing import Any

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.proof_bank.import_responses import preflight_raw_responses
from math_distill_stage2.proof_bank.keying import problem_key_from_equations
from math_distill_stage2.proof_bank.storage import write_json


DEFAULT_STAGE2_ARTIFACTS = Path("external/equational-theories-lean-stage2/.artifacts")
DEFAULT_EQUATIONS_PATH = Path(
    "external/equational_theories/equational_theories/Generated/All4x4Tables/src/equations.txt"
)

EQUATION_DECL_RE = re.compile(
    r"^def Equation(?P<id>\d+) \(G: Type\*\) \[Magma G\] := ∀ (?P<body>.*)$"
)
ARTIFACT_DIR_RE = re.compile(r"^true_(?P<eq1>\d+)_(?P<eq2>\d+)\.")

FORBIDDEN_PROOF_TOKENS = (
    "sorry",
    "admit",
    "axiom",
    "unsafe",
    "import",
    "def submission",
    "theorem",
    "congr_arg",
    "*",
)


@dataclass(frozen=True)
class ExternalOleanCandidate:
    row: dict[str, Any]
    proof: str


def parse_equations_file(path: Path) -> dict[int, str]:
    equations: dict[int, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = EQUATION_DECL_RE.match(line.strip())
        if match is None:
            continue
        equation_id = int(match.group("id"))
        equations[equation_id] = _strip_equation_binder(match.group("body").strip())
    return equations


def extract_submission_proof_body(source: str) -> str | None:
    lines = source.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == "intro G _ h":
            proof = "\n".join(lines[index + 1 :])
            proof = textwrap.dedent(proof).strip()
            return proof or None
    return None


def has_forbidden_proof_token(proof: str) -> str | None:
    for token in FORBIDDEN_PROOF_TOKENS:
        if token in proof:
            return token
    return None


def collect_external_olean_candidates(
    *,
    artifacts_root: Path,
    equations_path: Path,
    bank: Path,
    limit: int,
    candidate_pool: Path | None = None,
) -> list[ExternalOleanCandidate]:
    if limit <= 0:
        raise ValueError("limit must be positive")
    equations = parse_equations_file(equations_path)
    blocked_problem_keys = _blocked_problem_keys(bank)
    candidates: list[ExternalOleanCandidate] = []
    seen_pairs: set[tuple[int, int]] = set()

    artifact_dirs = (
        _artifact_dirs_from_candidate_pool(candidate_pool, artifacts_root)
        if candidate_pool is not None
        else _all_artifact_dirs(artifacts_root)
    )

    for artifact_dir, source_row in artifact_dirs:
        match = ARTIFACT_DIR_RE.match(artifact_dir.name)
        if match is None:
            continue
        eq1_id = int(match.group("eq1"))
        eq2_id = int(match.group("eq2"))
        pair = (eq1_id, eq2_id)
        if pair in seen_pairs:
            continue
        equation1 = equations.get(eq1_id)
        equation2 = equations.get(eq2_id)
        if equation1 is None or equation2 is None:
            continue
        problem_key = problem_key_from_equations(equation1, equation2)
        if problem_key in blocked_problem_keys:
            continue

        submission_path = artifact_dir / "Submission.lean"
        if not submission_path.exists():
            continue
        proof = extract_submission_proof_body(submission_path.read_text(encoding="utf-8"))
        if proof is None:
            continue
        if has_forbidden_proof_token(proof) is not None:
            continue

        item_id = f"{len(candidates) + 1:06d}"
        source_metadata = dict(source_row or {})
        source_metadata.pop("schema_version", None)
        source_metadata.pop("item_id", None)
        source_metadata.pop("problem_key", None)
        row = {
            **source_metadata,
            "schema_version": 1,
            "item_id": item_id,
            "source_problem_id": source_metadata.get("source_problem_id") or f"true_{eq1_id}_{eq2_id}",
            "source_dataset": source_metadata.get("source_dataset")
            or "external_equational_theories_stage2_artifacts",
            "source_candidate_stratum": (
                f"external_submission_olean_harvest:{source_metadata.get('source_candidate_stratum')}"
                if source_metadata.get("source_candidate_stratum")
                else "external_submission_olean_harvest"
            ),
            "source_artifact_dir": str(artifact_dir),
            "source_candidate_pool": str(candidate_pool) if candidate_pool else None,
            "eq1_id": eq1_id,
            "eq2_id": eq2_id,
            "equation1": equation1,
            "equation2": equation2,
            "expected_verdict": True,
            "problem_key": problem_key,
        }
        candidates.append(ExternalOleanCandidate(row=row, proof=proof))
        seen_pairs.add(pair)
        if len(candidates) >= limit:
            break

    return candidates


def build_external_olean_harvest_run(
    *,
    run_dir: Path,
    source_run_id: str,
    artifacts_root: Path = DEFAULT_STAGE2_ARTIFACTS,
    equations_path: Path = DEFAULT_EQUATIONS_PATH,
    bank: Path,
    limit: int,
    candidate_pool: Path | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    if run_dir.exists() and any(run_dir.iterdir()) and not overwrite:
        raise FileExistsError(f"refusing to overwrite non-empty run directory: {run_dir}")

    candidates = collect_external_olean_candidates(
        artifacts_root=artifacts_root,
        equations_path=equations_path,
        bank=bank,
        limit=limit,
        candidate_pool=candidate_pool,
    )
    if not candidates:
        raise ValueError("no external Submission.olean candidates found")

    raw_dir = run_dir / "raw_responses"
    raw_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(run_dir / "input_problems.jsonl", [candidate.row for candidate in candidates])
    for candidate in candidates:
        raw_payload = {"verdict": "true", "proof": candidate.proof}
        (raw_dir / f"{candidate.row['item_id']}.txt").write_text(
            json.dumps(raw_payload, ensure_ascii=False, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )

    manifest = {
        "schema_version": 1,
        "source_run_id": source_run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "generator": {
            "mode": "external_submission_olean_harvest",
            "model": None,
        },
        "problem_count": len(candidates),
        "run_dir": str(run_dir),
        "source_artifacts_root": str(artifacts_root),
        "source_equations_path": str(equations_path),
        "source_candidate_pool": str(candidate_pool) if candidate_pool else None,
        "bank": str(bank),
    }
    write_json(run_dir / "manifest.json", manifest)
    preflight = preflight_raw_responses(run_dir)
    return {
        "schema_version": 1,
        "source_run_id": source_run_id,
        "run_dir": str(run_dir),
        "candidate_count": len(candidates),
        "prompt_items": [candidate.row for candidate in candidates],
        "raw_response_paths": [
            str(raw_dir / f"{candidate.row['item_id']}.txt") for candidate in candidates
        ],
        "manifest_path": str(run_dir / "manifest.json"),
        "preflight": preflight,
    }


def _strip_equation_binder(body: str) -> str:
    return re.sub(r"^(?:[a-z] ?)+: G,\s*", "", body)


def _all_artifact_dirs(artifacts_root: Path) -> list[tuple[Path, dict[str, Any] | None]]:
    return [
        (compiled_submission.parent, None)
        for compiled_submission in sorted(artifacts_root.glob("true_*_*/Submission.olean"))
    ]


def _artifact_dirs_from_candidate_pool(
    candidate_pool: Path,
    artifacts_root: Path,
) -> list[tuple[Path, dict[str, Any] | None]]:
    rows = read_jsonl(candidate_pool)
    artifact_dirs: list[tuple[Path, dict[str, Any] | None]] = []
    for row in rows:
        eq1_id = row.get("eq1_id")
        eq2_id = row.get("eq2_id")
        if eq1_id is None or eq2_id is None:
            continue
        for artifact_dir in sorted(artifacts_root.glob(f"true_{int(eq1_id)}_{int(eq2_id)}.*")):
            if (artifact_dir / "Submission.olean").exists():
                artifact_dirs.append((artifact_dir, row))
                break
    return artifact_dirs


def _blocked_problem_keys(bank: Path) -> set[str]:
    attempts_path = bank / "attempts.jsonl"
    if not attempts_path.exists():
        return set()
    blocked: set[str] = set()
    for line in attempts_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        attempt = json.loads(line)
        problem_key = attempt.get("problem_key")
        if not problem_key:
            continue
        if attempt.get("judge_status") == "accepted":
            blocked.add(str(problem_key))
            continue
        source_run_id = str(attempt.get("source_run_id") or "")
        if "external-olean-harvest" in source_run_id:
            blocked.add(str(problem_key))
    return blocked
