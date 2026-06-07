from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


PROTECTED_EXACT_PATHS = {
    "data/processed/order5_strategy_registry/candidate_index.jsonl",
    "data/processed/order5_strategy_registry/candidate_index_summary.json",
    "data/processed/order5_strategy_registry/coverage_summary.json",
    "data/processed/order5_strategy_registry/merge_review_queue.json",
    "data/processed/order5_strategy_registry/mining_state.json",
    "data/processed/order5_strategy_registry/setcheck_increment_history.jsonl",
    "data/processed/order5_strategy_registry/strategies.json",
    "src/math_distill_stage2/order5_strategy_registry.py",
    "submissions/solo_official/solver.py",
}

PROTECTED_PREFIXES = (
    "tests/order5_strategy_registry/",
)

PROTECTED_REGEXES = (
    re.compile(
        r"^data/processed/order5_strategy_registry/"
        r"[^/]+_pair_indexes_[0-9]{8}\.txt$"
    ),
)

ALLOWED_CANDIDATE_PREFIX = "data/processed/order5_strategy_registry/candidates/"

KNOWN_REGISTRY_WRITER_COMMANDS = {
    "scripts/data/summarize_order5_strategy_coverage.py": [
        "data/processed/order5_strategy_registry/strategies.json",
        "data/processed/order5_strategy_registry/coverage_summary.json",
    ],
    "scripts/data/update_order5_strategy_mining_state.py": [
        "data/processed/order5_strategy_registry/mining_state.json",
        "data/processed/order5_strategy_registry/candidate_index.jsonl",
        "data/processed/order5_strategy_registry/candidate_index_summary.json",
    ],
    "scripts/data/build_order5_strategy_merge_review_queue.py": [
        "data/processed/order5_strategy_registry/merge_review_queue.json",
    ],
}

PATH_PREFIXES_TO_EXTRACT = (
    "data/processed/order5_strategy_registry/",
    "docs/experiments/",
    "scripts/data/",
    "src/math_distill_stage2/order5_strategy_registry.py",
    "submissions/solo_official/",
    "tests/order5_strategy_registry/",
)

SESSION_ID_RE = re.compile(r"rollout-.*?-(?P<session>019e[0-9a-f-]+)\.jsonl$")
PATCH_TARGET_RE = re.compile(
    r"^\*\*\* (?:Add File|Update File|Delete File|Move to): (?P<path>.+)$"
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def default_sessions_root() -> Path:
    return Path(os.path.expanduser("~/.codex/sessions"))


def default_controller_thread_id() -> str | None:
    value = os.environ.get("CODEX_THREAD_ID")
    return value.strip() if value and value.strip() else None


def parse_iso_timestamp(value: str) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def normalize_project_path(path_text: str, *, cwd: Path) -> str | None:
    path_text = path_text.strip().strip("\"'`.,);:")
    if not path_text:
        return None

    path = Path(path_text)
    if path.is_absolute():
        try:
            return path.resolve().relative_to(cwd.resolve()).as_posix()
        except ValueError:
            return None
    return path.as_posix().lstrip("./")


def classify_protected_path(project_path: str) -> str | None:
    if project_path.startswith(ALLOWED_CANDIDATE_PREFIX):
        return None
    if project_path in PROTECTED_EXACT_PATHS:
        return "controller_only_exact"
    if any(project_path.startswith(prefix) for prefix in PROTECTED_PREFIXES):
        return "controller_only_prefix"
    if any(regex.match(project_path) for regex in PROTECTED_REGEXES):
        return "controller_only_registry_asset"
    return None


def is_protected_path(project_path: str) -> bool:
    return classify_protected_path(project_path) is not None


def extract_project_paths(text: str, *, cwd: Path) -> list[str]:
    if not text:
        return []

    paths: set[str] = set()
    cwd_text = cwd.resolve().as_posix()
    for prefix in PATH_PREFIXES_TO_EXTRACT:
        pattern = re.compile(rf"(?<![\w./-]){re.escape(prefix)}[A-Za-z0-9_./:@+-]*")
        paths.update(match.group(0).rstrip("\"'`,);:") for match in pattern.finditer(text))

        abs_prefix = f"{cwd_text}/{prefix}"
        abs_pattern = re.compile(
            rf"{re.escape(abs_prefix)}[A-Za-z0-9_./:@+-]*"
        )
        for match in abs_pattern.finditer(text):
            normalized = normalize_project_path(match.group(0), cwd=cwd)
            if normalized:
                paths.add(normalized)

    return sorted(paths)


def extract_patch_target_paths(text: str, *, cwd: Path) -> list[str]:
    paths: set[str] = set()
    for line in text.splitlines():
        match = PATCH_TARGET_RE.match(line.strip())
        if not match:
            continue
        normalized = normalize_project_path(match.group("path"), cwd=cwd)
        if normalized:
            paths.add(normalized)
    return sorted(paths)


def session_id_from_path(path: Path) -> str | None:
    match = SESSION_ID_RE.search(path.name)
    if match:
        return match.group("session")
    return None


def iter_session_logs(
    *,
    sessions_root: Path,
    since: datetime | None,
) -> Iterable[Path]:
    if not sessions_root.exists():
        return []
    logs = sorted(sessions_root.rglob("rollout-*.jsonl"))
    if since is None:
        return logs
    cutoff = since.timestamp()
    return [path for path in logs if path.stat().st_mtime >= cutoff]


def _payload_text(payload: dict[str, Any]) -> tuple[str, str]:
    payload_type = payload.get("type")
    if payload_type == "function_call":
        name = str(payload.get("name") or "")
        arguments = payload.get("arguments")
        if isinstance(arguments, str):
            return name, arguments
        return name, json.dumps(arguments, sort_keys=True, ensure_ascii=False)
    if payload_type == "custom_tool_call":
        name = str(payload.get("name") or "")
        call_input = payload.get("input")
        if isinstance(call_input, str):
            return name, call_input
        return name, json.dumps(call_input, sort_keys=True, ensure_ascii=False)
    return "", ""


def _command_text_from_tool_arguments(text: str) -> str:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return text
    if isinstance(data, dict) and isinstance(data.get("cmd"), str):
        return data["cmd"]
    return text


def _shell_tokens(command_text: str) -> list[str]:
    try:
        return shlex.split(command_text)
    except ValueError:
        return command_text.split()


def _command_executes_script(command_text: str, script_path: str) -> bool:
    tokens = _shell_tokens(command_text)
    while tokens and "=" in tokens[0] and not tokens[0].startswith("-"):
        tokens = tokens[1:]
    if not tokens:
        return False
    if "--help" in tokens or "-h" in tokens:
        return False

    first = tokens[0]
    if first == script_path:
        return True
    python_like = (
        first in {"python", "python3"}
        or first.endswith("/python")
        or first.endswith("/python3")
    )
    return python_like and len(tokens) > 1 and tokens[1] == script_path


def _redirection_target_from_token(
    token: str,
    next_token: str | None,
) -> str | None:
    if token in {">", ">>", "1>", "1>>", "2>", "2>>", "&>"}:
        return next_token
    match = re.match(r"^(?:[12]?>|[12]?>>|&>)(?P<target>.+)$", token)
    if match:
        return match.group("target")
    return None


def _protected_shell_write_targets(command_text: str, *, cwd: Path) -> list[str]:
    tokens = _shell_tokens(command_text)
    targets: set[str] = set()
    for index, token in enumerate(tokens):
        next_token = tokens[index + 1] if index + 1 < len(tokens) else None
        target = _redirection_target_from_token(token, next_token)
        if target and target != "/dev/null":
            normalized = normalize_project_path(target, cwd=cwd)
            if normalized and is_protected_path(normalized):
                targets.add(normalized)
        if token == "tee":
            for tee_target in tokens[index + 1 :]:
                if tee_target.startswith("-"):
                    continue
                normalized = normalize_project_path(tee_target, cwd=cwd)
                if normalized and is_protected_path(normalized):
                    targets.add(normalized)
    return sorted(targets)


def _known_writer_targets(text: str) -> list[str]:
    command_text = _command_text_from_tool_arguments(text)
    targets: set[str] = set()
    for command, command_targets in KNOWN_REGISTRY_WRITER_COMMANDS.items():
        if _command_executes_script(command_text, command):
            targets.update(command_targets)
    return sorted(targets)


def parse_session_log_for_gate_events(
    log_path: Path,
    *,
    cwd: Path,
    since: datetime | None = None,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    session_id = session_id_from_path(log_path)
    session_meta: dict[str, Any] = {}

    with log_path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            timestamp = parse_iso_timestamp(str(record.get("timestamp") or ""))
            if since is not None and timestamp is not None and timestamp < since:
                continue

            record_type = record.get("type")
            payload = record.get("payload") or {}
            if record_type == "session_meta":
                if isinstance(payload, dict):
                    session_meta = payload
                    session_id = str(payload.get("id") or session_id or "")
                continue

            if record_type != "response_item" or not isinstance(payload, dict):
                continue

            name, text = _payload_text(payload)
            if not text:
                continue

            if name == "apply_patch":
                touched_paths = extract_patch_target_paths(text, cwd=cwd)
            else:
                touched_paths = extract_project_paths(text, cwd=cwd)
            protected_paths = [
                path for path in touched_paths if is_protected_path(path)
            ]
            known_writer_targets = _known_writer_targets(text)
            protected_paths.extend(
                path for path in known_writer_targets if path not in protected_paths
            )

            allowed_candidate_paths = [
                path for path in touched_paths if path.startswith(ALLOWED_CANDIDATE_PREFIX)
            ]
            write_like = bool(known_writer_targets)
            if name == "apply_patch":
                write_like = bool(protected_paths)
            if name == "exec_command" and protected_paths:
                command_text = _command_text_from_tool_arguments(text)
                protected_write_targets = _protected_shell_write_targets(
                    command_text,
                    cwd=cwd,
                )
                protected_paths.extend(
                    path for path in protected_write_targets if path not in protected_paths
                )
                write_like = (
                    bool(protected_write_targets) or bool(known_writer_targets)
                )

            if not protected_paths and not allowed_candidate_paths:
                continue

            events.append(
                {
                    "timestamp": timestamp.isoformat() if timestamp else None,
                    "session_id": str(session_id or ""),
                    "originator": session_meta.get("originator"),
                    "source": session_meta.get("source"),
                    "rollout_path": str(log_path),
                    "tool_name": name,
                    "write_like": write_like,
                    "protected_paths": sorted(set(protected_paths)),
                    "allowed_candidate_paths": allowed_candidate_paths[:12],
                    "excerpt": text.replace("\n", "\\n")[:500],
                }
            )

    return events


def git_status_paths(*, cwd: Path) -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    paths: list[str] = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        path_text = line[3:]
        if " -> " in path_text:
            path_text = path_text.split(" -> ", 1)[1]
        normalized = normalize_project_path(path_text, cwd=cwd)
        if normalized:
            paths.append(normalized)
    return paths


def build_merge_gate_audit(
    *,
    cwd: Path,
    controller_thread_ids: Iterable[str] = (),
    sessions_root: Path | None = None,
    since: datetime | None = None,
    dirty_paths: Iterable[str] | None = None,
) -> dict[str, Any]:
    cwd = cwd.resolve()
    controller_ids = {item for item in controller_thread_ids if item}
    if not controller_ids:
        current = default_controller_thread_id()
        if current:
            controller_ids.add(current)

    if dirty_paths is None:
        dirty_paths = git_status_paths(cwd=cwd)

    protected_dirty_paths: list[str] = []
    for path in dirty_paths:
        normalized = normalize_project_path(path, cwd=cwd)
        if normalized and is_protected_path(normalized):
            protected_dirty_paths.append(normalized)
    protected_dirty_paths = sorted(set(protected_dirty_paths))

    session_events: list[dict[str, Any]] = []
    if sessions_root is not None:
        for log_path in iter_session_logs(sessions_root=sessions_root, since=since):
            session_events.extend(
                parse_session_log_for_gate_events(log_path, cwd=cwd, since=since)
            )

    protected_write_events = [
        event
        for event in session_events
        if event["write_like"] and event["protected_paths"]
    ]
    non_controller_write_events = [
        event
        for event in protected_write_events
        if event["session_id"] not in controller_ids
    ]

    return {
        "schema_version": 1,
        "generated_at": utc_now_iso(),
        "cwd": str(cwd),
        "controller_thread_ids": sorted(controller_ids),
        "since": since.isoformat() if since else None,
        "policy": {
            "controller_only": "formal registry/code/test paths may only be written by the controller session",
            "candidate_layer_allowed_prefix": ALLOWED_CANDIDATE_PREFIX,
            "protected_exact_paths": sorted(PROTECTED_EXACT_PATHS),
            "protected_prefixes": list(PROTECTED_PREFIXES),
        },
        "protected_dirty_paths": protected_dirty_paths,
        "protected_write_events": protected_write_events,
        "non_controller_write_events": non_controller_write_events,
        "violation_count": len(non_controller_write_events),
        "dirty_protected_path_count": len(protected_dirty_paths),
        "merge_allowed": not non_controller_write_events and not protected_dirty_paths,
        "recommendation": _recommendation(
            protected_dirty_paths=protected_dirty_paths,
            non_controller_write_events=non_controller_write_events,
        ),
    }


def _recommendation(
    *,
    protected_dirty_paths: list[str],
    non_controller_write_events: list[dict[str, Any]],
) -> str:
    if non_controller_write_events:
        return (
            "stop_and_audit_non_controller_registry_writes_before_accepting_current_baseline"
        )
    if protected_dirty_paths:
        return "review_dirty_controller_only_paths_before_next_registry_merge"
    return "merge_gate_clear_for_controller_review"
