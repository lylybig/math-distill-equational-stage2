import json
from pathlib import Path

from math_distill_stage2.order5_strategy_merge_gate import (
    build_merge_gate_audit,
    extract_patch_target_paths,
    extract_project_paths,
    is_protected_path,
    session_id_from_path,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )


def test_protected_path_classifier_allows_candidate_layer():
    assert is_protected_path("data/processed/order5_strategy_registry/strategies.json")
    assert is_protected_path(
        "data/processed/order5_strategy_registry/"
        "opnorm_hconst_default_sandwich_postedge8_pair_indexes_20260522.txt"
    )
    assert is_protected_path("src/math_distill_stage2/order5_strategy_registry.py")
    assert is_protected_path("tests/order5_strategy_registry/test_demo.py")
    assert not is_protected_path(
        "data/processed/order5_strategy_registry/candidates/demo_summary.json"
    )


def test_extract_project_paths_from_absolute_and_relative_text(tmp_path: Path):
    cwd = tmp_path / "repo"
    cwd.mkdir()
    text = (
        f"{cwd}/src/math_distill_stage2/order5_strategy_registry.py "
        "data/processed/order5_strategy_registry/candidates/demo_summary.json"
    )

    paths = extract_project_paths(text, cwd=cwd)

    assert "src/math_distill_stage2/order5_strategy_registry.py" in paths
    assert (
        "data/processed/order5_strategy_registry/candidates/demo_summary.json" in paths
    )


def test_extract_patch_target_paths_ignores_patch_body_references(tmp_path: Path):
    cwd = tmp_path / "repo"
    cwd.mkdir()
    text = (
        "*** Begin Patch\n"
        "*** Add File: data/processed/order5_strategy_registry/candidates/demo.json\n"
        "+{\"source\": \"data/processed/order5_strategy_registry/strategies.json\"}\n"
        "*** End Patch\n"
    )

    paths = extract_patch_target_paths(text, cwd=cwd)

    assert paths == ["data/processed/order5_strategy_registry/candidates/demo.json"]


def test_audit_flags_non_controller_protected_patch(tmp_path: Path):
    cwd = tmp_path / "repo"
    sessions_root = tmp_path / "sessions"
    cwd.mkdir()
    log_path = (
        sessions_root
        / "2026"
        / "05"
        / "22"
        / "rollout-2026-05-22T12-00-00-019eaaaa-bbbb-cccc-dddd-eeeeeeeeeeee.jsonl"
    )
    _write_jsonl(
        log_path,
        [
            {
                "timestamp": "2026-05-22T04:00:00Z",
                "type": "session_meta",
                "payload": {
                    "id": "019eaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                    "originator": "codex-tui",
                    "source": "cli",
                },
            },
            {
                "timestamp": "2026-05-22T04:01:00Z",
                "type": "response_item",
                "payload": {
                    "type": "custom_tool_call",
                    "name": "apply_patch",
                    "input": (
                        "*** Begin Patch\n"
                        "*** Update File: "
                        f"{cwd}/src/math_distill_stage2/order5_strategy_registry.py\n"
                        "@@\n"
                        "+DEMO = True\n"
                        "*** End Patch\n"
                    ),
                },
            },
            {
                "timestamp": "2026-05-22T04:02:00Z",
                "type": "response_item",
                "payload": {
                    "type": "custom_tool_call",
                    "name": "apply_patch",
                    "input": (
                        "*** Begin Patch\n"
                        "*** Add File: "
                        "data/processed/order5_strategy_registry/candidates/demo.json\n"
                        "+{\"mentions\": "
                        "\"data/processed/order5_strategy_registry/strategies.json\"}\n"
                        "*** End Patch\n"
                    ),
                },
            },
        ],
    )

    audit = build_merge_gate_audit(
        cwd=cwd,
        controller_thread_ids=["019econtroller"],
        sessions_root=sessions_root,
        dirty_paths=[],
    )

    assert audit["merge_allowed"] is False
    assert audit["violation_count"] == 1
    event = audit["non_controller_write_events"][0]
    assert event["session_id"] == "019eaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    assert event["protected_paths"] == [
        "src/math_distill_stage2/order5_strategy_registry.py"
    ]


def test_audit_does_not_treat_reader_mentions_as_known_writers(tmp_path: Path):
    cwd = tmp_path / "repo"
    sessions_root = tmp_path / "sessions"
    cwd.mkdir()
    log_path = (
        sessions_root
        / "2026"
        / "05"
        / "22"
        / "rollout-2026-05-22T12-00-00-019ereader-0000-0000-0000-000000000000.jsonl"
    )
    _write_jsonl(
        log_path,
        [
            {
                "timestamp": "2026-05-22T04:00:00Z",
                "type": "session_meta",
                "payload": {
                    "id": "019ereader-0000-0000-0000-000000000000",
                    "originator": "codex-tui",
                    "source": "cli",
                },
            },
            {
                "timestamp": "2026-05-22T04:01:00Z",
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "name": "exec_command",
                    "arguments": json.dumps(
                        {
                            "cmd": (
                                "rg summarize_order5_strategy_coverage.py "
                                "scripts/data/summarize_order5_strategy_coverage.py "
                                "data/processed/order5_strategy_registry/strategies.json"
                            )
                        }
                    ),
                },
            },
        ],
    )

    audit = build_merge_gate_audit(
        cwd=cwd,
        controller_thread_ids=["019econtroller"],
        sessions_root=sessions_root,
        dirty_paths=[],
    )

    assert audit["violation_count"] == 0
    assert audit["merge_allowed"] is True


def test_audit_treats_executed_summary_script_as_known_writer(tmp_path: Path):
    cwd = tmp_path / "repo"
    sessions_root = tmp_path / "sessions"
    cwd.mkdir()
    log_path = (
        sessions_root
        / "2026"
        / "05"
        / "22"
        / "rollout-2026-05-22T12-00-00-019ewriter-0000-0000-0000-000000000000.jsonl"
    )
    _write_jsonl(
        log_path,
        [
            {
                "timestamp": "2026-05-22T04:00:00Z",
                "type": "session_meta",
                "payload": {
                    "id": "019ewriter-0000-0000-0000-000000000000",
                    "originator": "codex-tui",
                    "source": "cli",
                },
            },
            {
                "timestamp": "2026-05-22T04:01:00Z",
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "name": "exec_command",
                    "arguments": json.dumps(
                        {
                            "cmd": (
                                "PYTHONPATH=src .venv/bin/python "
                                "scripts/data/summarize_order5_strategy_coverage.py "
                                "--reuse-true-from-output"
                            )
                        }
                    ),
                },
            },
        ],
    )

    audit = build_merge_gate_audit(
        cwd=cwd,
        controller_thread_ids=["019econtroller"],
        sessions_root=sessions_root,
        dirty_paths=[],
    )

    assert audit["violation_count"] == 1
    assert audit["non_controller_write_events"][0]["protected_paths"] == [
        "data/processed/order5_strategy_registry/coverage_summary.json",
        "data/processed/order5_strategy_registry/strategies.json",
    ]


def test_audit_ignores_shape_arrows_and_devnull_redirection(tmp_path: Path):
    cwd = tmp_path / "repo"
    sessions_root = tmp_path / "sessions"
    cwd.mkdir()
    log_path = (
        sessions_root
        / "2026"
        / "05"
        / "22"
        / "rollout-2026-05-22T12-00-00-019escan-0000-0000-0000-000000000000.jsonl"
    )
    _write_jsonl(
        log_path,
        [
            {
                "timestamp": "2026-05-22T04:00:00Z",
                "type": "session_meta",
                "payload": {
                    "id": "019escan-0000-0000-0000-000000000000",
                    "originator": "codex-tui",
                    "source": "cli",
                },
            },
            {
                "timestamp": "2026-05-22T04:01:00Z",
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "name": "exec_command",
                    "arguments": json.dumps(
                        {
                            "cmd": (
                                "source_shape='roots=mul>mul|d=1>4'; "
                                "ls data/processed/order5_strategy_registry/"
                                "coverage_summary.json 2>/dev/null"
                            )
                        }
                    ),
                },
            },
        ],
    )

    audit = build_merge_gate_audit(
        cwd=cwd,
        controller_thread_ids=["019econtroller"],
        sessions_root=sessions_root,
        dirty_paths=[],
    )

    assert audit["violation_count"] == 0


def test_audit_flags_shell_redirection_to_protected_path(tmp_path: Path):
    cwd = tmp_path / "repo"
    sessions_root = tmp_path / "sessions"
    cwd.mkdir()
    log_path = (
        sessions_root
        / "2026"
        / "05"
        / "22"
        / "rollout-2026-05-22T12-00-00-019eredir-0000-0000-0000-000000000000.jsonl"
    )
    _write_jsonl(
        log_path,
        [
            {
                "timestamp": "2026-05-22T04:00:00Z",
                "type": "session_meta",
                "payload": {
                    "id": "019eredir-0000-0000-0000-000000000000",
                    "originator": "codex-tui",
                    "source": "cli",
                },
            },
            {
                "timestamp": "2026-05-22T04:01:00Z",
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "name": "exec_command",
                    "arguments": json.dumps(
                        {
                            "cmd": (
                                "echo '{}' > "
                                "data/processed/order5_strategy_registry/"
                                "coverage_summary.json"
                            )
                        }
                    ),
                },
            },
        ],
    )

    audit = build_merge_gate_audit(
        cwd=cwd,
        controller_thread_ids=["019econtroller"],
        sessions_root=sessions_root,
        dirty_paths=[],
    )

    assert audit["violation_count"] == 1
    assert audit["non_controller_write_events"][0]["protected_paths"] == [
        "data/processed/order5_strategy_registry/coverage_summary.json"
    ]


def test_audit_allows_controller_session_but_flags_dirty_protected_path(
    tmp_path: Path,
):
    cwd = tmp_path / "repo"
    sessions_root = tmp_path / "sessions"
    cwd.mkdir()
    log_path = (
        sessions_root
        / "2026"
        / "05"
        / "22"
        / "rollout-2026-05-22T12-00-00-019econtroller-0000-0000-0000-000000000000.jsonl"
    )
    _write_jsonl(
        log_path,
        [
            {
                "timestamp": "2026-05-22T04:00:00Z",
                "type": "session_meta",
                "payload": {
                    "id": "019econtroller-0000-0000-0000-000000000000",
                    "originator": "Codex Desktop",
                    "source": "vscode",
                },
            },
            {
                "timestamp": "2026-05-22T04:01:00Z",
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "name": "exec_command",
                    "arguments": json.dumps(
                        {
                            "cmd": (
                                "PYTHONPATH=src .venv/bin/python "
                                "scripts/data/summarize_order5_strategy_coverage.py"
                            )
                        }
                    ),
                },
            },
        ],
    )

    audit = build_merge_gate_audit(
        cwd=cwd,
        controller_thread_ids=["019econtroller-0000-0000-0000-000000000000"],
        sessions_root=sessions_root,
        dirty_paths=["data/processed/order5_strategy_registry/strategies.json"],
    )

    assert audit["violation_count"] == 0
    assert audit["dirty_protected_path_count"] == 1
    assert audit["merge_allowed"] is False
    assert audit["recommendation"] == (
        "review_dirty_controller_only_paths_before_next_registry_merge"
    )


def test_session_id_from_rollout_filename():
    path = Path(
        "rollout-2026-05-22T10-54-54-"
        "019e4d9b-7625-7d23-a814-014029444da5.jsonl"
    )

    assert session_id_from_path(path) == "019e4d9b-7625-7d23-a814-014029444da5"
