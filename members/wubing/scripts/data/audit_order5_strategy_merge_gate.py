#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from math_distill_stage2.order5_strategy_merge_gate import (
    build_merge_gate_audit,
    default_controller_thread_id,
    default_sessions_root,
)
from math_distill_stage2.order5_strategy_mining_state import write_json


def _since_from_args(args: argparse.Namespace) -> datetime | None:
    if args.since:
        normalized = args.since.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    if args.since_hours is not None:
        return datetime.now(timezone.utc) - timedelta(hours=args.since_hours)
    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Audit the order5 strategy registry merge gate. The gate flags "
            "controller-only file changes or recent non-controller writes before "
            "a candidate is accepted into the formal registry."
        )
    )
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument(
        "--controller-thread-id",
        action="append",
        default=[],
        help="Allowed controller Codex thread id. Defaults to CODEX_THREAD_ID.",
    )
    parser.add_argument(
        "--sessions-root",
        type=Path,
        default=default_sessions_root(),
        help="Codex session log root. Use --no-session-log-scan to skip logs.",
    )
    parser.add_argument("--no-session-log-scan", action="store_true")
    parser.add_argument(
        "--since",
        help="UTC ISO timestamp. Only session log events at or after this time are scanned.",
    )
    parser.add_argument(
        "--since-hours",
        type=float,
        default=12.0,
        help="Default: 12. Ignored when --since is provided.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        help="Optional path for the full audit JSON.",
    )
    parser.add_argument(
        "--fail-on-violation",
        action="store_true",
        help="Exit non-zero when the gate is not clear.",
    )
    args = parser.parse_args()

    controller_thread_ids = list(args.controller_thread_id)
    if not controller_thread_ids:
        current_thread_id = default_controller_thread_id()
        if current_thread_id:
            controller_thread_ids.append(current_thread_id)

    audit = build_merge_gate_audit(
        cwd=args.cwd,
        controller_thread_ids=controller_thread_ids,
        sessions_root=None if args.no_session_log_scan else args.sessions_root,
        since=_since_from_args(args),
    )

    if args.output_json:
        write_json(args.output_json, audit)

    compact = {
        "merge_allowed": audit["merge_allowed"],
        "recommendation": audit["recommendation"],
        "violation_count": audit["violation_count"],
        "dirty_protected_path_count": audit["dirty_protected_path_count"],
        "protected_dirty_paths": audit["protected_dirty_paths"][:20],
        "non_controller_write_events": [
            {
                "timestamp": event["timestamp"],
                "session_id": event["session_id"],
                "tool_name": event["tool_name"],
                "protected_paths": event["protected_paths"],
            }
            for event in audit["non_controller_write_events"][:20]
        ],
    }
    print(json.dumps(compact, indent=2, sort_keys=True))

    if args.fail_on_violation and not audit["merge_allowed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()

