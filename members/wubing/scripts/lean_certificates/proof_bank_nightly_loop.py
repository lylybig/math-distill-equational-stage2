from __future__ import annotations

import argparse
from datetime import date
import json
import os
from pathlib import Path
import sys

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))

from math_distill_stage2.proof_bank.nightly_loop import advance_proofbank_marathon
from math_distill_stage2.official_stage2_batch import (
    DEFAULT_REMOTE_JUDGE_V2_BASE_URLS,
    resolve_remote_judge_v2_base_urls,
    select_remote_judge_v2_base_url,
)
from math_distill_stage2.proof_bank.etp_context import DEFAULT_ETP_IMPLICATIONS_PATH
from math_distill_stage2.proof_bank.skill_guidance import (
    DEFAULT_GENERATION_SKILL_PATH,
    DEFAULT_LEAN_PROOF_SKILL_PATH,
)


DEFAULT_BANK = Path("data/processed/proof_banks/gpt_true_certificates")
DEFAULT_HIGH_SIGNAL = DEFAULT_BANK / "candidate_pools/order4_true_high_signal_failed_attempts_v1.jsonl"
DEFAULT_UNSOLVED = DEFAULT_BANK / "candidate_pools/order4_true_unsolved_v1.jsonl"
DEFAULT_ORDER4_SOURCE = Path("data/processed/order4_implication_problems")


def optional_env_int(name: str) -> int | None:
    value = os.environ.get(name)
    if value is None or not value.strip():
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{name} must be an integer") from exc


def optional_env_float(name: str) -> float | None:
    value = os.environ.get(name)
    if value is None or not value.strip():
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{name} must be a number") from exc


def parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected date in YYYY-MM-DD format") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Advance a Codex-session-driven proof bank marathon. The runner prepares "
            "prompt packs, pauses for Codex proof generation, then resumes import/merge/audit."
        )
    )
    parser.add_argument("--bank", type=Path, default=DEFAULT_BANK)
    parser.add_argument("--run-root", type=Path, default=Path("artifacts/proof_bank_runs"))
    parser.add_argument("--marathon-id", required=True)
    parser.add_argument(
        "--mode",
        choices=("auto", "prepare", "resume", "pause", "status"),
        default="auto",
    )
    parser.add_argument("--seed", type=int, default=20260511)
    parser.add_argument("--candidate-limit", type=int, default=50)
    parser.add_argument("--prompt-limit", type=int, default=3)
    parser.add_argument(
        "--sampling-strategy",
        choices=("default", "recovery-after-zero-yield"),
        default="default",
        help="Candidate/prompt selection strategy. Use recovery-after-zero-yield after an all-skipped cycle.",
    )
    parser.add_argument("--high-signal-pool", type=Path, action="append")
    parser.add_argument("--unsolved-pool", type=Path, action="append")
    parser.add_argument("--order4-source", type=Path, default=DEFAULT_ORDER4_SOURCE)
    parser.add_argument(
        "--no-order4-source",
        action="store_true",
        help="Use only process-data candidate pools. Intended for smoke runs only.",
    )
    parser.add_argument(
        "--no-repair-from-bank",
        action="store_true",
        help="Disable the rejected-attempt repair lane when sampling candidates.",
    )
    parser.add_argument(
        "--etp-implications-path",
        type=Path,
        default=DEFAULT_ETP_IMPLICATIONS_PATH,
        help="Processed ETP implication JSONL used for blueprint/path hints.",
    )
    parser.add_argument(
        "--no-etp-context",
        action="store_true",
        help="Disable ETP/blueprint context injection.",
    )
    parser.add_argument(
        "--generation-skill-path",
        type=Path,
        default=DEFAULT_GENERATION_SKILL_PATH,
        help="Skill markdown used for general proof-generation guidance.",
    )
    parser.add_argument(
        "--lean-proof-skill-path",
        type=Path,
        default=DEFAULT_LEAN_PROOF_SKILL_PATH,
        help="Skill markdown used for repair-item Lean proof guidance.",
    )
    parser.add_argument("--max-attempts-per-problem", type=int, default=3)
    parser.add_argument("--allow-existing-accepted", action="store_true")
    parser.add_argument(
        "--pause-reason",
        help="Human-readable reason recorded when --mode pause is used.",
    )
    parser.add_argument(
        "--marathon-date",
        type=parse_iso_date,
        help=(
            "Date directory for durable marathon state, in YYYY-MM-DD format. "
            "Use this to resume a marathon across local date rollover."
        ),
    )
    parser.add_argument(
        "--judge-backend",
        choices=("local", "remote-ssh", "remote-http", "remote-judge-v2"),
        default=os.environ.get("STAGE2_PROOFBANK_JUDGE_BACKEND", "local"),
        help=(
            "Official judge backend used during --mode resume. remote-http is an "
            "alias for remote-judge-v2; remote-ssh runs the Dockerized batch judge "
            "on another host."
        ),
    )
    parser.add_argument(
        "--remote-judge-base-url",
        default=os.environ.get("STAGE2_REMOTE_JUDGE_BASE_URL"),
        help="Single base URL for --judge-backend remote-http; overrides --remote-judge-base-urls.",
    )
    parser.add_argument(
        "--remote-judge-base-urls",
        default=os.environ.get("STAGE2_REMOTE_JUDGE_BASE_URLS"),
        help=(
            "Comma-separated endpoint pool for --judge-backend remote-http. "
            f"Default: {','.join(DEFAULT_REMOTE_JUDGE_V2_BASE_URLS)}."
        ),
    )
    parser.add_argument(
        "--remote-judge-host",
        default=os.environ.get("STAGE2_REMOTE_JUDGE_HOST"),
        help="SSH target for --judge-backend remote-ssh, for example user@gpu-host.",
    )
    parser.add_argument(
        "--remote-judge-repo",
        default=os.environ.get("STAGE2_REMOTE_JUDGE_REPO"),
        help="Path to this repository on the remote host.",
    )
    parser.add_argument(
        "--remote-judge-workdir",
        default=os.environ.get("STAGE2_REMOTE_JUDGE_WORKDIR", "/tmp/math-distill-stage2-proofbank-judge"),
        help="Remote scratch directory for uploaded batch inputs and judge artifacts.",
    )
    parser.add_argument(
        "--remote-judge-python",
        default=os.environ.get("STAGE2_REMOTE_JUDGE_PYTHON", "python3"),
        help="Python executable used inside the remote repository.",
    )
    parser.add_argument(
        "--remote-judge-max-workers",
        type=int,
        default=int(os.environ.get("STAGE2_REMOTE_JUDGE_MAX_WORKERS", "16")),
        help="Worker count passed to the remote judge backend.",
    )
    parser.add_argument(
        "--remote-judge-cpus",
        default=os.environ.get("STAGE2_REMOTE_JUDGE_CPUS"),
        help="Docker CPU limit passed on the remote host, for example 2.",
    )
    parser.add_argument(
        "--remote-judge-memory",
        default=os.environ.get("STAGE2_REMOTE_JUDGE_MEMORY"),
        help="Docker memory limit passed on the remote host, for example 6g.",
    )
    parser.add_argument(
        "--remote-judge-timeout-seconds",
        type=int,
        default=optional_env_int("STAGE2_REMOTE_JUDGE_TIMEOUT_SECONDS"),
        help="Wall timeout for remote ssh/scp, remote Docker batch commands, or judge-v2 requests.",
    )
    parser.add_argument(
        "--remote-judge-run-timeout-seconds",
        type=int,
        default=optional_env_int("STAGE2_REMOTE_JUDGE_RUN_TIMEOUT_SECONDS") or 600,
        help="Maximum seconds to wait for each remote-http judge-v2 job.",
    )
    parser.add_argument(
        "--remote-judge-poll-interval-seconds",
        type=float,
        default=optional_env_float("STAGE2_REMOTE_JUDGE_POLL_INTERVAL_SECONDS") or 2.0,
        help="Polling interval after a remote-http judge-v2 wait call times out.",
    )
    parser.add_argument(
        "--remote-judge-lean-timeout-seconds",
        type=int,
        default=optional_env_int("STAGE2_REMOTE_JUDGE_LEAN_TIMEOUT_SECONDS"),
        help="Lean timeout passed through to the official judge on the remote host.",
    )
    args = parser.parse_args(argv)

    high_signal_pools = args.high_signal_pool or ([DEFAULT_HIGH_SIGNAL] if DEFAULT_HIGH_SIGNAL.exists() else [])
    unsolved_pools = args.unsolved_pool or ([DEFAULT_UNSOLVED] if DEFAULT_UNSOLVED.exists() else [])
    order4_source = None if args.no_order4_source else args.order4_source
    if order4_source is not None and not order4_source.exists():
        order4_source = None

    batch_judge = None
    if args.judge_backend == "remote-ssh":
        if not args.remote_judge_host:
            parser.error("--remote-judge-host is required when --judge-backend remote-ssh")
        if not args.remote_judge_repo:
            parser.error("--remote-judge-repo is required when --judge-backend remote-ssh")
        from math_distill_stage2.official_stage2_batch import (
            RemoteOfficialStage2BatchConfig,
            make_remote_official_stage2_batch_judge,
        )

        batch_judge = make_remote_official_stage2_batch_judge(
            RemoteOfficialStage2BatchConfig(
                host=args.remote_judge_host,
                repo=args.remote_judge_repo,
                workdir=args.remote_judge_workdir,
                python=args.remote_judge_python,
                max_workers=args.remote_judge_max_workers,
                cpu_limit=args.remote_judge_cpus,
                memory_limit=args.remote_judge_memory,
                timeout_seconds=args.remote_judge_timeout_seconds,
                lean_timeout_seconds=args.remote_judge_lean_timeout_seconds,
            )
        )
    elif args.judge_backend == "remote-http":
        args.judge_backend = "remote-judge-v2"

    if args.judge_backend == "remote-judge-v2":
        from math_distill_stage2.official_stage2_batch import (
            RemoteJudgeV2Config,
            make_remote_judge_v2_batch_judge,
        )
        remote_judge_base_urls = resolve_remote_judge_v2_base_urls(
            base_url=args.remote_judge_base_url,
            base_urls=args.remote_judge_base_urls,
        )
        remote_judge_base_url = select_remote_judge_v2_base_url(
            remote_judge_base_urls,
            request_timeout_seconds=args.remote_judge_timeout_seconds,
        )

        batch_judge = make_remote_judge_v2_batch_judge(
            RemoteJudgeV2Config(
                base_url=remote_judge_base_url,
                max_workers=args.remote_judge_max_workers,
                request_timeout_seconds=args.remote_judge_timeout_seconds,
                run_timeout_seconds=args.remote_judge_run_timeout_seconds,
                poll_interval_seconds=args.remote_judge_poll_interval_seconds,
                lean_timeout_seconds=args.remote_judge_lean_timeout_seconds,
            )
        )
    result = advance_proofbank_marathon(
        bank=args.bank,
        run_root=args.run_root,
        marathon_id=args.marathon_id,
        high_signal_pools=high_signal_pools,
        unsolved_pools=unsolved_pools,
        order4_source=order4_source,
        seed=args.seed,
        candidate_limit=args.candidate_limit,
        prompt_limit=args.prompt_limit,
        repair_from_bank=not args.no_repair_from_bank,
        mode=args.mode,
        sampling_strategy=args.sampling_strategy,
        max_attempts_per_problem=args.max_attempts_per_problem,
        allow_existing_accepted=args.allow_existing_accepted,
        etp_implications_path=None if args.no_etp_context else args.etp_implications_path,
        generation_skill_path=args.generation_skill_path,
        lean_proof_skill_path=args.lean_proof_skill_path,
        pause_reason=args.pause_reason,
        batch_judge=batch_judge,
        today=args.marathon_date,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if args.mode == "status":
        return 0
    return (
        0
        if result["status"] in {"awaiting_codex_generation", "cycle_complete", "paused"}
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
