from __future__ import annotations

from datetime import date, datetime, timezone
import json
from pathlib import Path
from typing import Any

from math_distill_stage2.dataset_io import read_jsonl
from math_distill_stage2.proof_bank.bank import (
    check_bank,
    merge_run,
    preview_merge_run,
)
from math_distill_stage2.proof_bank.candidate_sampling import sample_candidate_pool
from math_distill_stage2.proof_bank.etp_context import DEFAULT_ETP_IMPLICATIONS_PATH
from math_distill_stage2.proof_bank.import_responses import (
    BatchJudgeFunction,
    JudgeFunction,
    import_responses,
    preflight_raw_responses,
)
from math_distill_stage2.proof_bank.prompt_pack import build_prompt_pack
from math_distill_stage2.proof_bank.quality_audit import audit_proof_bank_quality
from math_distill_stage2.proof_bank.skill_guidance import (
    DEFAULT_GENERATION_SKILL_PATH,
    DEFAULT_LEAN_PROOF_SKILL_PATH,
)
from math_distill_stage2.proof_bank.storage import read_json, write_json


def advance_proofbank_marathon(
    *,
    bank: Path,
    run_root: Path,
    marathon_id: str,
    high_signal_pools: list[Path],
    unsolved_pools: list[Path],
    order4_source: Path | None,
    seed: int,
    candidate_limit: int,
    prompt_limit: int,
    repair_from_bank: bool = True,
    mode: str = "auto",
    prompt_policy: str = "trace-if-available",
    sampling_strategy: str = "default",
    max_attempts_per_problem: int = 3,
    allow_existing_accepted: bool = False,
    etp_implications_path: Path | None = DEFAULT_ETP_IMPLICATIONS_PATH,
    generation_skill_path: Path | None = DEFAULT_GENERATION_SKILL_PATH,
    lean_proof_skill_path: Path | None = DEFAULT_LEAN_PROOF_SKILL_PATH,
    pause_reason: str | None = None,
    judge: JudgeFunction | None = None,
    batch_judge: BatchJudgeFunction | None = None,
    today: date | None = None,
) -> dict[str, Any]:
    if mode not in {"auto", "prepare", "resume", "pause", "status"}:
        raise ValueError("mode must be one of: auto, prepare, resume, pause, status")
    if candidate_limit <= 0:
        raise ValueError("candidate_limit must be positive")
    if prompt_limit <= 0:
        raise ValueError("prompt_limit must be positive")

    today = today or date.today()
    state_dir = run_root / today.isoformat() / marathon_id
    state_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = state_dir / "marathon_manifest.json"
    state_path = state_dir / "marathon_state.json"
    summaries_path = state_dir / "cycle_summaries.jsonl"

    state = _load_state(state_path, marathon_id=marathon_id, bank=bank)
    if not manifest_path.exists():
        write_json(
            manifest_path,
            {
                "schema_version": 1,
                "marathon_id": marathon_id,
                "bank": str(bank),
                "run_root": str(run_root),
                "generator_mode": "codex_session",
                "proof_generation_boundary": (
                    "This runner does not synthesize proofs; it pauses for the Codex "
                    "session to write 1-3 raw responses."
                ),
                "candidate_limit": candidate_limit,
                "prompt_limit": prompt_limit,
                "prompt_policy": prompt_policy,
                "sampling_strategy": sampling_strategy,
                "etp_implications_path": str(etp_implications_path)
                if etp_implications_path
                else None,
                "generation_skill_path": str(generation_skill_path)
                if generation_skill_path
                else None,
                "lean_proof_skill_path": str(lean_proof_skill_path)
                if lean_proof_skill_path
                else None,
                "created_at_utc": utc_now(),
            },
        )

    if mode == "auto":
        mode = (
            "resume"
            if state.get("status") in {"awaiting_codex_generation", "awaiting_raw_response_fix"}
            else "status"
            if state.get("status") == "paused"
            else "prepare"
        )

    if mode == "status":
        result = _status_marathon(state)
    elif mode == "pause":
        result = _pause_marathon(state=state, state_path=state_path, reason=pause_reason)
    elif mode == "prepare":
        result = _prepare_cycle(
            bank=bank,
            run_root=run_root,
            marathon_id=marathon_id,
            state=state,
            state_dir=state_dir,
            state_path=state_path,
            summaries_path=summaries_path,
            high_signal_pools=high_signal_pools,
            unsolved_pools=unsolved_pools,
            order4_source=order4_source,
            seed=seed,
            candidate_limit=candidate_limit,
            prompt_limit=prompt_limit,
            repair_from_bank=repair_from_bank,
            prompt_policy=prompt_policy,
            sampling_strategy=sampling_strategy,
            max_attempts_per_problem=max_attempts_per_problem,
            allow_existing_accepted=allow_existing_accepted,
            etp_implications_path=etp_implications_path,
            generation_skill_path=generation_skill_path,
            lean_proof_skill_path=lean_proof_skill_path,
            today=today,
        )
    else:
        result = _resume_cycle(
            bank=bank,
            marathon_id=marathon_id,
            state=state,
            state_dir=state_dir,
            state_path=state_path,
            summaries_path=summaries_path,
            judge=judge,
            batch_judge=batch_judge,
        )

    result["manifest_path"] = str(manifest_path)
    result["state_path"] = str(state_path)
    result["cycle_summaries_path"] = str(summaries_path)
    return result


def _prepare_cycle(
    *,
    bank: Path,
    run_root: Path,
    marathon_id: str,
    state: dict[str, Any],
    state_dir: Path,
    state_path: Path,
    summaries_path: Path,
    high_signal_pools: list[Path],
    unsolved_pools: list[Path],
    order4_source: Path | None,
    seed: int,
    candidate_limit: int,
    prompt_limit: int,
    repair_from_bank: bool,
    prompt_policy: str,
    sampling_strategy: str,
    max_attempts_per_problem: int,
    allow_existing_accepted: bool,
    etp_implications_path: Path | None,
    generation_skill_path: Path | None,
    lean_proof_skill_path: Path | None,
    today: date,
) -> dict[str, Any]:
    if state.get("status") in {
        "awaiting_codex_generation",
        "awaiting_raw_response_fix",
        "paused",
    }:
        return {
            "status": state["status"],
            "cycle": state["cycles"][-1],
            "message": "current cycle is waiting for Codex raw responses, fixes, or manual resume",
        }

    bank_check = check_bank(bank)
    if not bank_check["ok"]:
        state["status"] = "pause_for_debug"
        state["updated_at_utc"] = utc_now()
        state["last_error"] = "bank integrity check failed"
        state["bank_check"] = bank_check
        write_json(state_path, state)
        return {"status": "pause_for_debug", "bank_check": bank_check}

    cycle_index = int(state.get("cycle_count") or 0) + 1
    source_run_id = f"{marathon_id}-cycle-{cycle_index:04d}"
    candidate_dir = state_dir / "candidate_pools"
    candidate_pool = candidate_dir / f"{source_run_id}.jsonl"
    sampled_manifest = candidate_dir / f"{source_run_id}.manifest.json"
    sample_summary = sample_candidate_pool(
        bank=bank,
        output_pool=candidate_pool,
        output_manifest=sampled_manifest,
        pool_id=source_run_id,
        seed=seed + cycle_index - 1,
        limit=candidate_limit,
        high_signal_pools=high_signal_pools,
        unsolved_pools=unsolved_pools,
        order4_source=order4_source,
        repair_from_bank=repair_from_bank,
        max_attempts_per_problem=max_attempts_per_problem,
        allow_existing_accepted=allow_existing_accepted,
        sampling_strategy=sampling_strategy,
    )
    max_high_signal_without_etp = (
        1 if sampling_strategy == "recovery-after-zero-yield" else None
    )
    prompt_summary = build_prompt_pack(
        bank=bank,
        candidate_pool=candidate_pool,
        run_root=run_root,
        source_run_id=source_run_id,
        limit=prompt_limit,
        prompt_policy=prompt_policy,
        allow_existing_accepted=allow_existing_accepted,
        etp_implications_path=etp_implications_path,
        generation_skill_path=generation_skill_path,
        lean_proof_skill_path=lean_proof_skill_path,
        max_high_signal_without_etp=max_high_signal_without_etp,
    )
    run_dir = Path(prompt_summary["run_dir"])
    prompt_paths = sorted(str(path) for path in (run_dir / "prompt_pack").glob("*.md"))
    raw_response_paths = [
        str(run_dir / "raw_responses" / f"{Path(prompt_path).stem}.txt")
        for prompt_path in prompt_paths
    ]
    prompt_items = _prompt_item_summaries(run_dir)
    now = utc_now()
    cycle_status = (
        "awaiting_codex_generation"
        if prompt_summary["problem_count"] > 0
        else "pause_for_debug"
    )
    cycle = {
        "cycle_index": cycle_index,
        "source_run_id": source_run_id,
        "status": cycle_status,
        "candidate_pool": str(candidate_pool),
        "sampled_manifest": str(sampled_manifest),
        "sample": {
            "selected_count": sample_summary["selected_count"],
            "selected_by_stratum": sample_summary["selected_by_stratum"],
            "sampling_strategy": sample_summary["sampling_strategy"],
            "excluded_accepted_count": sample_summary["excluded_accepted_count"],
            "excluded_attempt_ceiling_count": sample_summary["excluded_attempt_ceiling_count"],
        },
        "run_dir": str(run_dir),
        "prompt_problem_count": prompt_summary["problem_count"],
        "prompt_item_paths": prompt_paths,
        "prompt_items": prompt_items,
        "raw_response_paths": raw_response_paths,
        "started_at_utc": now,
        "updated_at_utc": now,
    }
    if prompt_summary["problem_count"] <= 0:
        cycle["last_error"] = "no prompt items available"
    state.setdefault("cycles", []).append(cycle)
    state["status"] = cycle_status
    if prompt_summary["problem_count"] <= 0:
        state["last_error"] = "no prompt items available"
    state["cycle_count"] = cycle_index
    state["current_cycle_index"] = cycle_index
    state["updated_at_utc"] = now
    write_json(state_path, state)
    _append_jsonl(summaries_path, _cycle_summary_row(cycle))
    return {"status": cycle_status, "cycle": cycle}


def _resume_cycle(
    *,
    bank: Path,
    marathon_id: str,
    state: dict[str, Any],
    state_dir: Path,
    state_path: Path,
    summaries_path: Path,
    judge: JudgeFunction | None,
    batch_judge: BatchJudgeFunction | None,
) -> dict[str, Any]:
    cycles = state.get("cycles") or []
    if not cycles:
        raise ValueError(f"no prepared cycle for marathon: {marathon_id}")
    cycle = cycles[-1]
    if cycle.get("status") == "cycle_complete":
        return {"status": "cycle_complete", "cycle": cycle}

    missing = [
        path
        for path in cycle.get("raw_response_paths", [])
        if not Path(path).exists() or not Path(path).read_text(encoding="utf-8").strip()
    ]
    if missing:
        cycle["status"] = "awaiting_codex_generation"
        cycle["missing_raw_response_paths"] = missing
        cycle.pop("raw_response_preflight", None)
        cycle.pop("pause_reason", None)
        cycle.pop("paused_at_utc", None)
        cycle["updated_at_utc"] = utc_now()
        state["status"] = "awaiting_codex_generation"
        state.pop("last_error", None)
        state.pop("pause_reason", None)
        state.pop("paused_at_utc", None)
        state["updated_at_utc"] = cycle["updated_at_utc"]
        write_json(state_path, state)
        return {
            "status": "awaiting_codex_generation",
            "cycle": cycle,
            "missing_raw_response_paths": missing,
        }

    run_dir = Path(cycle["run_dir"])
    raw_response_preflight = preflight_raw_responses(run_dir)
    if not raw_response_preflight["ok"]:
        cycle["status"] = "awaiting_raw_response_fix"
        cycle["raw_response_preflight"] = raw_response_preflight
        cycle.pop("missing_raw_response_paths", None)
        cycle["updated_at_utc"] = utc_now()
        state["status"] = "awaiting_raw_response_fix"
        state["last_error"] = "raw response preflight failed"
        state["updated_at_utc"] = cycle["updated_at_utc"]
        write_json(state_path, state)
        return {
            "status": "awaiting_raw_response_fix",
            "cycle": cycle,
            "raw_response_preflight": raw_response_preflight,
        }

    cycle["raw_response_preflight"] = raw_response_preflight
    cycle.pop("missing_raw_response_paths", None)
    cycle.pop("pause_reason", None)
    cycle.pop("paused_at_utc", None)
    state.pop("last_error", None)
    state.pop("pause_reason", None)
    state.pop("paused_at_utc", None)
    if batch_judge is not None:
        import_summary = import_responses(run_dir, batch_judge=batch_judge)
    else:
        active_judge = judge or _official_judge
        import_summary = import_responses(run_dir, judge=active_judge)
    dry_run_merge = preview_merge_run(bank, run_dir)
    merge_summary = merge_run(bank, run_dir)
    bank_check = check_bank(bank)
    audit_path = state_dir / "audits" / f"{cycle['source_run_id']}.json"
    audit = audit_proof_bank_quality(
        bank=bank,
        run_summary_path=run_dir / "summary.json",
        sampled_manifest_path=Path(cycle["sampled_manifest"]),
        marathon_state_path=state_path,
        output_path=audit_path,
    )

    accepted_count = int(import_summary.get("accepted_count") or 0)
    attempt_count = int(import_summary.get("attempt_count") or 0)
    previous_zero = int(state.get("consecutive_zero_accepted_cycles") or 0)
    consecutive_zero = previous_zero + 1 if attempt_count > 0 and accepted_count == 0 else 0
    state["accepted_count"] = int(state.get("accepted_count") or 0) + accepted_count
    state["attempt_count"] = int(state.get("attempt_count") or 0) + attempt_count
    state["consecutive_zero_accepted_cycles"] = consecutive_zero
    state["status"] = (
        "cycle_complete" if audit["decision"] != "pause_for_debug" else "pause_for_debug"
    )
    state["updated_at_utc"] = utc_now()

    cycle.update(
        {
            "status": "cycle_complete",
            "import_summary": import_summary,
            "dry_run_merge": dry_run_merge,
            "merge_summary": merge_summary,
            "bank_check": bank_check,
            "audit": audit,
            "audit_path": str(audit_path),
            "updated_at_utc": state["updated_at_utc"],
        }
    )
    write_json(state_path, state)
    _append_jsonl(summaries_path, _cycle_summary_row(cycle))
    return {"status": state["status"], "cycle": cycle, "audit": audit}


def _load_state(path: Path, *, marathon_id: str, bank: Path) -> dict[str, Any]:
    if path.exists():
        return read_json(path)
    now = utc_now()
    return {
        "schema_version": 1,
        "marathon_id": marathon_id,
        "bank": str(bank),
        "status": "initialized",
        "cycle_count": 0,
        "attempt_count": 0,
        "accepted_count": 0,
        "consecutive_zero_accepted_cycles": 0,
        "cycles": [],
        "created_at_utc": now,
        "updated_at_utc": now,
    }


def _status_marathon(state: dict[str, Any]) -> dict[str, Any]:
    cycles = state.get("cycles") or []
    result: dict[str, Any] = {
        "status": state.get("status"),
        "cycle_count": state.get("cycle_count", 0),
        "attempt_count": state.get("attempt_count", 0),
        "accepted_count": state.get("accepted_count", 0),
    }
    if cycles:
        result["cycle"] = cycles[-1]
    return result


def _pause_marathon(
    *,
    state: dict[str, Any],
    state_path: Path,
    reason: str | None,
) -> dict[str, Any]:
    now = utc_now()
    pause_reason = reason or "manual pause"
    previous_status = state.get("status")
    state["status"] = "paused"
    state["previous_status_before_pause"] = previous_status
    state["pause_reason"] = pause_reason
    state["paused_at_utc"] = now
    state["updated_at_utc"] = now
    cycles = state.get("cycles") or []
    if cycles:
        cycle = cycles[-1]
        cycle["previous_status_before_pause"] = cycle.get("status")
        cycle["status"] = "paused"
        cycle["pause_reason"] = pause_reason
        cycle["paused_at_utc"] = now
        cycle["updated_at_utc"] = now
    write_json(state_path, state)
    return _status_marathon(state)


def _cycle_summary_row(cycle: dict[str, Any]) -> dict[str, Any]:
    row = {
        "cycle_index": cycle.get("cycle_index"),
        "source_run_id": cycle.get("source_run_id"),
        "status": cycle.get("status"),
        "run_dir": cycle.get("run_dir"),
        "sampled_manifest": cycle.get("sampled_manifest"),
        "prompt_problem_count": cycle.get("prompt_problem_count"),
        "updated_at_utc": cycle.get("updated_at_utc"),
    }
    if "import_summary" in cycle:
        row["import_summary"] = cycle["import_summary"]
    if "audit" in cycle:
        row["audit_decision"] = cycle["audit"].get("decision")
    if "raw_response_preflight" in cycle:
        row["raw_response_preflight"] = {
            "ok": cycle["raw_response_preflight"].get("ok"),
            "issue_count": cycle["raw_response_preflight"].get("issue_count"),
        }
    return row


def _prompt_item_summaries(run_dir: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for problem in read_jsonl(run_dir / "input_problems.jsonl"):
        item_id = str(problem["item_id"])
        items.append(
            {
                "item_id": item_id,
                "source_problem_id": problem.get("source_problem_id"),
                "source_dataset": problem.get("source_dataset"),
                "eq1_id": problem.get("eq1_id"),
                "eq2_id": problem.get("eq2_id"),
                "source_candidate_stratum": problem.get("source_candidate_stratum"),
                "priority_score": problem.get("priority_score"),
                "previous_judge_error_kind": problem.get("previous_judge_error_kind"),
                "has_etp_context": bool(problem.get("etp_context")),
                "prompt_item_path": str(run_dir / "prompt_pack" / f"{item_id}.md"),
                "raw_response_path": str(run_dir / "raw_responses" / f"{item_id}.txt"),
                "equation1": problem.get("equation1"),
                "equation2": problem.get("equation2"),
            }
        )
    return items


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
        handle.write("\n")


def _official_judge(problem: dict[str, Any], answer: dict[str, Any]) -> dict[str, Any]:
    from math_distill_stage2.official_stage2_judge import verify_official_stage2_answer

    return verify_official_stage2_answer(problem, answer).raw


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
