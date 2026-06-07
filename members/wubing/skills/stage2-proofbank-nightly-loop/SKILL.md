---
name: stage2-proofbank-nightly-loop
description: Use when explicitly authorized to run or prepare long-running Stage 2 proofbank expansion, overnight proof generation, 24-hour proof bank loops, marathon batches, or automatic true certificate mining.
---

# Stage2 Proofbank Nightly Loop

Coordinate a bounded 24-hour proofbank expansion loop. This skill orchestrates existing proofbank skills; it does not replace their per-step constraints and does not improve `solver.py`.

## Working Directory

All relative paths in this skill are relative to `members/wubing/`. If the shell
is at the team monorepo root, run `cd members/wubing` or set the command
`workdir` there before executing the commands below.

Current project reality: proof generation is Codex session driven. The runner records state and prepares work, but it does not daemonize proof generation and must not introduce an external proof generator worker.

Do not use this as the default answer to “should proof bank keep running?” If an active strategy candidate needs a finite set of source-level singleton certificates, run a bounded targeted proofbank gate through `stage2-proofbank-start` / `stage2-proofbank-sample-candidates` first. Broad nightly expansion is secondary and requires explicit user authorization.

## Preconditions

Require explicit user authorization before starting a long run. Record:

- timebox, default `24-hour`
- `marathon_id`
- generator mode: current Codex session
- maximum cycles, maximum prompt items per cycle, and judge concurrency
- compute/API budget and whether paid/cloud resources are allowed
- stop conditions and checkpoint cadence
- whether this is broad exploration or a targeted strategy-gate marathon; for targeted gates, record the strategy candidate key, seed pool, seed IDs, and target stop condition

Run only current-session Codex batches and keep `stage2-proofbank-generate-true-certificate` at 1-3 items per invocation.

## State

Create a durable marathon state area:

```text
artifacts/proof_bank_runs/YYYY-MM-DD/<marathon_id>/
  marathon_manifest.json
  marathon_state.json
  cycle_summaries.jsonl
```

Each cycle uses a normal proof bank run id such as `<marathon_id>-cycle-0001`, so existing verify/import/merge tooling still owns run artifacts.

Use `scripts/lean_certificates/proof_bank_nightly_loop.py` to advance the durable state:

```bash
python scripts/lean_certificates/proof_bank_nightly_loop.py \
  --marathon-id <marathon_id> \
  --mode auto \
  --seed <seed>
```

Use `--mode pause --pause-reason "<reason>"` to stop a marathon in the durable state before changing workflow or prompts. A paused marathon will not advance on `--mode auto`; use `--mode status` to inspect it, or `--mode resume` explicitly after the raw responses are ready and the user has approved continuing.

The nightly sampler enables the `rejected_attempt_repair` lane by default. Use `--no-repair-from-bank` only for smoke tests or when debugging sampler behavior.

Prompt packs are skill-driven. By default the builder embeds `skills/stage2-proofbank-generate-true-certificate/SKILL.md` for all items and the local `lean-proof` skill for repair items, with source paths and sha256 hashes recorded in the run manifest. Use `--generation-skill-path` or `--lean-proof-skill-path` to test a different strategy skill without changing code.

Prompt packs also add local ETP/blueprint context by default from `data/processed/etp/etp_implications.jsonl`, when a short proven path exists from `eq1_id` to `eq2_id`. Use `--no-etp-context` for ablations. ETP theorem names and file lines are planning hints only; generated certificates must remain self-contained under `JudgeProblem`.

When the script returns `awaiting_codex_generation`, inspect the returned `prompt_items` summary, open the listed prompt item paths, and use the current Codex session to write the listed raw response files. Then run the same command again, or use `--mode resume`, to preflight, import, judge, merge, check, and audit the completed batch.

Resume now runs a strict raw response preflight before judge/import/merge. The preflight requires each raw response to be exactly one JSON object with `"verdict":"true"` and a string proof field, and rejects raw text containing `sorry`, `admit`, `axiom`, `unsafe`, `import`, theorem headers, `def submission`, `congr_arg`, or `*`. If this fails, the marathon state becomes `awaiting_raw_response_fix`; fix the raw response files in place and rerun `--mode auto` or `--mode resume`. The failed batch must not be imported or merged until `raw_response_preflight.ok` is true.

Batch judge/import must use a remote judge backend. Default `remote-http` is an
alias for `remote-judge-v2` and must target the judge-v2 control service at
`http://10.220.69.172:8890`. Use judge-v2 `/jobs` for Lean certificate remote
verification.

```bash
python scripts/lean_certificates/proof_bank_nightly_loop.py \
  --marathon-id <marathon_id> \
  --mode resume \
  --judge-backend remote-http \
  --remote-judge-base-url http://10.220.69.172:8890 \
  --remote-judge-max-workers 16
```

The remote HTTP backend submits each pending proof directly to judge-v2 `/jobs`
and imports only official judge outcomes. It keeps proof generation,
raw-response preflight, merge, and audit local, but does not run local
Lean/Docker judge.

Use the remote SSH backend when a direct SSH-accessible judge host/repo is configured:

```bash
python scripts/lean_certificates/proof_bank_nightly_loop.py \
  --marathon-id <marathon_id> \
  --mode resume \
  --judge-backend remote-ssh \
  --remote-judge-host <ssh-target> \
  --remote-judge-repo /path/to/math-distill-equational-stage2/members/wubing
```

The remote repository must have the official batch verifier script and Docker judge image available. Optional settings include `--remote-judge-workdir`, `--remote-judge-max-workers`, `--remote-judge-cpus`, `--remote-judge-memory`, and `--remote-judge-lean-timeout-seconds`; the same values can be supplied via `STAGE2_REMOTE_JUDGE_*` environment variables. Do not use local Lean/Docker judge for proofbank batch verification unless the user explicitly asks to debug the local environment.

## Loop

For each cycle:

1. Run `stage2-proofbank-maintain` check on the global bank.
2. Use `stage2-proofbank-sample-candidates`. For targeted strategy gates, sample only the declared seed pool and accepted-exclusion set. For broad nightly runs, include rejected-attempt repair when available and preserve `direct_order4_true_exploration` from the 22M order4 shards.
3. Build a bounded prompt pack.
4. Pause at `awaiting_codex_generation`; use `stage2-proofbank-generate-true-certificate` in the current Codex session for 1-3 prompt items.
5. Resume the runner after raw responses exist; it first runs raw response preflight, then uses `stage2-proofbank-verify-import` with the official judge.
6. Use `stage2-proofbank-maintain` dry-run merge, write merge, rebuild, and check.
7. Use `stage2-proofbank-quality-audit` before continuing.
8. Update `marathon_state.json` after every cycle.

If the user asks to stop, record a durable pause with `--mode pause` rather than leaving the state in `awaiting_codex_generation`.

## Quality Gates

Continue only while all hold:

- Global bank check passes after merge.
- Accepted certificates have official `accepted` evidence.
- For broad nightly runs, source balance includes direct 22M order4 sampling, not only `dev_main`. For targeted strategy gates, source balance is intentionally scoped to the declared seed pool and should not be “corrected” by adding unrelated order4 exploration.
- Attempt ceilings and accepted exclusions are respected.
- Accepted yield and rejection/error mix do not indicate a broken generator or judge.
- No individual `test_locked` failures are used.

Pause on repeated remote judge errors, malformed raw responses, hard merge errors, exhausted candidate strata, disk pressure, too many consecutive zero-accepted cycles, or when a targeted strategy gate has enough accepted seeds to hand back to total-control exact union/conflict review.

## Constraints

Do not edit `solver.py`, export submissions, add known-proof tables, delete bank ledgers, use `test_locked` individual failures, or convert accepted certificates into solver templates.

## Report

Report marathon id, elapsed time, cycles completed, sampled candidates, generated attempts, accepted/rejected/skipped/error/timeout counts, accepted yield, source balance or targeted seed coverage, latest `marathon_state.json`, and whether the run stopped normally or paused on a gate.
