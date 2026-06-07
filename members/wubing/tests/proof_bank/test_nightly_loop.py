import gzip
import json
from pathlib import Path

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.proof_bank.bank import init_bank
from math_distill_stage2.proof_bank.nightly_loop import advance_proofbank_marathon


def _problem(eq1_id: int, eq2_id: int, equation1: str, equation2: str) -> dict:
    return {
        "source_problem_id": f"p-{eq1_id}-{eq2_id}",
        "source_dataset": "fixture",
        "eq1_id": eq1_id,
        "eq2_id": eq2_id,
        "equation1": equation1,
        "equation2": equation2,
        "expected_verdict": True,
        "priority_score": 10,
    }


def test_nightly_loop_prepares_cycle_and_pauses_for_codex_generation(tmp_path: Path):
    bank = tmp_path / "bank"
    init_bank(bank)
    high_signal_pool = tmp_path / "high.jsonl"
    unsolved_pool = tmp_path / "unsolved.jsonl"
    write_jsonl(
        high_signal_pool,
        [
            _problem(1, 2, "x ◇ y = y ◇ x", "(x ◇ y) ◇ z = (y ◇ x) ◇ z"),
            _problem(3, 4, "(x ◇ y) ◇ z = x ◇ (y ◇ z)", "((x ◇ y) ◇ z) ◇ w = (x ◇ (y ◇ z)) ◇ w"),
            _problem(5, 6, "x ◇ (y ◇ z) = y ◇ (x ◇ z)", "(x ◇ (y ◇ z)) ◇ w = (y ◇ (x ◇ z)) ◇ w"),
        ],
    )
    write_jsonl(
        unsolved_pool,
        [
            _problem(7, 8, "x ◇ y = x", "(x ◇ y) ◇ z = x ◇ z"),
            _problem(9, 10, "x ◇ y = y", "z ◇ (x ◇ y) = z ◇ y"),
        ],
    )
    order4 = tmp_path / "order4.jsonl.gz"
    with gzip.open(order4, "wt", encoding="utf-8") as handle:
        for idx in range(20, 30):
            handle.write(
                json.dumps(
                    {
                        "id": f"o-{idx}",
                        "eq1_id": idx,
                        "eq2_id": idx + 100,
                        "equation1": f"x{idx} ◇ y = y ◇ x{idx}",
                        "equation2": f"(x{idx} ◇ y) ◇ z = (y ◇ x{idx}) ◇ z",
                        "answer": True,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    result = advance_proofbank_marathon(
        bank=bank,
        run_root=tmp_path / "runs",
        marathon_id="fixture-marathon",
        high_signal_pools=[high_signal_pool],
        unsolved_pools=[unsolved_pool],
        order4_source=order4,
        seed=123,
        candidate_limit=6,
        prompt_limit=2,
        mode="prepare",
    )

    state_path = Path(result["state_path"])
    state = json.loads(state_path.read_text(encoding="utf-8"))
    cycle = state["cycles"][-1]
    assert result["status"] == "awaiting_codex_generation"
    assert state["status"] == "awaiting_codex_generation"
    assert cycle["cycle_index"] == 1
    assert Path(cycle["run_dir"]).exists()
    assert len(cycle["prompt_item_paths"]) == 2
    assert len(cycle["prompt_items"]) == 2
    assert cycle["prompt_items"][0]["item_id"] == "000001"
    assert cycle["prompt_items"][0]["raw_response_path"].endswith("000001.txt")
    assert cycle["prompt_items"][0]["equation1"]
    assert read_jsonl(Path(cycle["run_dir"]) / "input_problems.jsonl")
    assert (state_path.parent / "cycle_summaries.jsonl").exists()


def test_nightly_loop_resume_imports_complete_codex_responses_and_audits(tmp_path: Path):
    bank = tmp_path / "bank"
    init_bank(bank)
    pool = tmp_path / "high.jsonl"
    write_jsonl(pool, [_problem(1, 2, "x = x", "x = x")])
    prepared = advance_proofbank_marathon(
        bank=bank,
        run_root=tmp_path / "runs",
        marathon_id="fixture-marathon",
        high_signal_pools=[pool],
        unsolved_pools=[],
        order4_source=None,
        seed=123,
        candidate_limit=1,
        prompt_limit=1,
        mode="prepare",
    )
    state = json.loads(Path(prepared["state_path"]).read_text(encoding="utf-8"))
    run_dir = Path(state["cycles"][-1]["run_dir"])
    raw_path = run_dir / "raw_responses" / "000001.txt"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text('{"verdict":"true","proof":"exact h"}\n', encoding="utf-8")

    def fake_judge(problem: dict, answer: dict) -> dict:
        return {
            "status": "accepted",
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
            "problem": problem,
            "answer": answer,
        }

    resumed = advance_proofbank_marathon(
        bank=bank,
        run_root=tmp_path / "runs",
        marathon_id="fixture-marathon",
        high_signal_pools=[pool],
        unsolved_pools=[],
        order4_source=None,
        seed=123,
        candidate_limit=1,
        prompt_limit=1,
        mode="resume",
        judge=fake_judge,
    )

    state = json.loads(Path(resumed["state_path"]).read_text(encoding="utf-8"))
    assert resumed["status"] == "cycle_complete"
    assert state["status"] == "cycle_complete"
    assert state["accepted_count"] == 1
    assert read_jsonl(bank / "accepted.jsonl")[0]["attempt_id"] == "attempt:fixture-marathon-cycle-0001:000001"
    assert state["cycles"][-1]["audit"]["decision"] in {"continue", "continue_with_adjusted_sampling"}


def test_nightly_loop_resume_can_use_batch_judge(tmp_path: Path):
    bank = tmp_path / "bank"
    init_bank(bank)
    pool = tmp_path / "high.jsonl"
    write_jsonl(pool, [_problem(1, 2, "x = x", "x = x")])
    prepared = advance_proofbank_marathon(
        bank=bank,
        run_root=tmp_path / "runs",
        marathon_id="fixture-marathon",
        high_signal_pools=[pool],
        unsolved_pools=[],
        order4_source=None,
        seed=123,
        candidate_limit=1,
        prompt_limit=1,
        mode="prepare",
    )
    state = json.loads(Path(prepared["state_path"]).read_text(encoding="utf-8"))
    run_dir = Path(state["cycles"][-1]["run_dir"])
    raw_path = run_dir / "raw_responses" / "000001.txt"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text('{"verdict":"true","proof":"exact h"}\n', encoding="utf-8")
    calls = []

    def fake_batch_judge(requests: list[tuple[dict, dict]]) -> list[dict]:
        calls.append(requests)
        return [{"status": "accepted", "exit_code": 0, "stdout": "", "stderr": ""}]

    resumed = advance_proofbank_marathon(
        bank=bank,
        run_root=tmp_path / "runs",
        marathon_id="fixture-marathon",
        high_signal_pools=[pool],
        unsolved_pools=[],
        order4_source=None,
        seed=123,
        candidate_limit=1,
        prompt_limit=1,
        mode="resume",
        batch_judge=fake_batch_judge,
    )

    assert resumed["status"] == "cycle_complete"
    assert len(calls) == 1
    assert calls[0][0][0]["id"] == "p-1-2"
    assert read_jsonl(bank / "accepted.jsonl")[0]["attempt_id"] == "attempt:fixture-marathon-cycle-0001:000001"


def test_nightly_loop_pauses_when_no_prompt_items_are_available(tmp_path: Path):
    bank = tmp_path / "bank"
    init_bank(bank)
    result = advance_proofbank_marathon(
        bank=bank,
        run_root=tmp_path / "runs",
        marathon_id="empty-marathon",
        high_signal_pools=[],
        unsolved_pools=[],
        order4_source=None,
        seed=123,
        candidate_limit=1,
        prompt_limit=1,
        mode="prepare",
    )

    state = json.loads(Path(result["state_path"]).read_text(encoding="utf-8"))
    assert result["status"] == "pause_for_debug"
    assert state["status"] == "pause_for_debug"
    assert state["last_error"] == "no prompt items available"


def test_nightly_loop_preflights_raw_responses_before_import_and_merge(tmp_path: Path):
    bank = tmp_path / "bank"
    init_bank(bank)
    pool = tmp_path / "high.jsonl"
    write_jsonl(pool, [_problem(1, 2, "x = x", "x = x")])
    prepared = advance_proofbank_marathon(
        bank=bank,
        run_root=tmp_path / "runs",
        marathon_id="fixture-marathon",
        high_signal_pools=[pool],
        unsolved_pools=[],
        order4_source=None,
        seed=123,
        candidate_limit=1,
        prompt_limit=1,
        mode="prepare",
    )
    state = json.loads(Path(prepared["state_path"]).read_text(encoding="utf-8"))
    run_dir = Path(state["cycles"][-1]["run_dir"])
    raw_path = run_dir / "raw_responses" / "000001.txt"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text('{"verdict":"true","proof":"sorry"}\n', encoding="utf-8")

    def should_not_call_judge(problem: dict, answer: dict) -> dict:
        raise AssertionError("judge should not run when raw response preflight fails")

    preflight_failed = advance_proofbank_marathon(
        bank=bank,
        run_root=tmp_path / "runs",
        marathon_id="fixture-marathon",
        high_signal_pools=[pool],
        unsolved_pools=[],
        order4_source=None,
        seed=123,
        candidate_limit=1,
        prompt_limit=1,
        mode="resume",
        judge=should_not_call_judge,
    )

    state = json.loads(Path(preflight_failed["state_path"]).read_text(encoding="utf-8"))
    assert preflight_failed["status"] == "awaiting_raw_response_fix"
    assert state["status"] == "awaiting_raw_response_fix"
    assert state["last_error"] == "raw response preflight failed"
    assert preflight_failed["raw_response_preflight"]["issues"][0]["error_subkind"] == "sorry"
    assert not (run_dir / "generated_attempts.jsonl").exists()

    raw_path.write_text('{"verdict":"true","proof":"exact h"}\n', encoding="utf-8")

    def fake_judge(problem: dict, answer: dict) -> dict:
        return {
            "status": "accepted",
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
            "problem": problem,
            "answer": answer,
        }

    resumed = advance_proofbank_marathon(
        bank=bank,
        run_root=tmp_path / "runs",
        marathon_id="fixture-marathon",
        high_signal_pools=[pool],
        unsolved_pools=[],
        order4_source=None,
        seed=123,
        candidate_limit=1,
        prompt_limit=1,
        mode="auto",
        judge=fake_judge,
    )

    assert resumed["status"] == "cycle_complete"
    state = json.loads(Path(resumed["state_path"]).read_text(encoding="utf-8"))
    assert state["status"] == "cycle_complete"
    assert state["cycles"][-1]["raw_response_preflight"]["ok"] is True


def test_nightly_loop_pause_blocks_auto_prepare_until_explicit_resume(tmp_path: Path):
    bank = tmp_path / "bank"
    init_bank(bank)
    pool = tmp_path / "high.jsonl"
    write_jsonl(pool, [_problem(1, 2, "x = x", "x = x")])
    advance_proofbank_marathon(
        bank=bank,
        run_root=tmp_path / "runs",
        marathon_id="fixture-marathon",
        high_signal_pools=[pool],
        unsolved_pools=[],
        order4_source=None,
        seed=123,
        candidate_limit=1,
        prompt_limit=1,
        mode="prepare",
    )

    paused = advance_proofbank_marathon(
        bank=bank,
        run_root=tmp_path / "runs",
        marathon_id="fixture-marathon",
        high_signal_pools=[pool],
        unsolved_pools=[],
        order4_source=None,
        seed=123,
        candidate_limit=1,
        prompt_limit=1,
        mode="pause",
        pause_reason="optimize proofbank flow",
    )

    assert paused["status"] == "paused"
    state = json.loads(Path(paused["state_path"]).read_text(encoding="utf-8"))
    assert state["cycle_count"] == 1
    assert state["pause_reason"] == "optimize proofbank flow"
    assert state["cycles"][-1]["status"] == "paused"

    auto = advance_proofbank_marathon(
        bank=bank,
        run_root=tmp_path / "runs",
        marathon_id="fixture-marathon",
        high_signal_pools=[pool],
        unsolved_pools=[],
        order4_source=None,
        seed=123,
        candidate_limit=1,
        prompt_limit=1,
        mode="auto",
    )

    assert auto["status"] == "paused"
    state = json.loads(Path(auto["state_path"]).read_text(encoding="utf-8"))
    assert state["cycle_count"] == 1

    run_dir = Path(state["cycles"][-1]["run_dir"])
    raw_path = run_dir / "raw_responses" / "000001.txt"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text('{"verdict":"true","proof":"exact h"}\n', encoding="utf-8")

    def fake_judge(problem: dict, answer: dict) -> dict:
        return {
            "status": "accepted",
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
            "problem": problem,
            "answer": answer,
        }

    resumed = advance_proofbank_marathon(
        bank=bank,
        run_root=tmp_path / "runs",
        marathon_id="fixture-marathon",
        high_signal_pools=[pool],
        unsolved_pools=[],
        order4_source=None,
        seed=123,
        candidate_limit=1,
        prompt_limit=1,
        mode="resume",
        judge=fake_judge,
    )

    assert resumed["status"] == "cycle_complete"
    state = json.loads(Path(resumed["state_path"]).read_text(encoding="utf-8"))
    assert "pause_reason" not in state
