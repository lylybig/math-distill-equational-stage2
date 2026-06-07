---
name: stage2-info-competition
description: Use when the user asks to update, refresh, crawl, fetch, sync, or verify the latest SAIR Mathematics Distillation Challenge Equational Theories Stage 2 competition information, official rules, official judge/evaluation repository metadata, API snapshots, or local competition docs.
---

# Stage2 Info Competition

Use this skill to refresh official Stage 2 competition information and keep local raw snapshots plus project docs aligned.

## Working Directory

All relative paths in this skill are relative to `members/wubing/`. If the shell
is at the team monorepo root, run `cd members/wubing` or set the command
`workdir` there before executing the commands below.

## Workflow

1. Read `docs/sources.md`, `docs/competition-analysis.md`, `docs/data-inventory.md`, and `docs/architecture.md` to understand the current recorded snapshot.
2. Run the reproducible downloader:
   ```bash
   python scripts/data/download_public_data.py
   ```
3. Maintain the official Stage 2 repository clone for analysis:
   - Expected path: `external/equational-theories-lean-stage2/`
   - If missing, clone it:
     ```bash
     git clone --depth 1 https://github.com/SAIRcompetition/equational-theories-lean-stage2 external/equational-theories-lean-stage2
     ```
   - If present, inspect it before updating:
     ```bash
     git -C external/equational-theories-lean-stage2 status --short
     git -C external/equational-theories-lean-stage2 rev-parse HEAD
     ```
   - Only refresh the clone when it is clean. If dirty, report the local changes and do not overwrite them.
   - For a clean clone, fetch latest `main` and move to it without using destructive reset:
     ```bash
     git -C external/equational-theories-lean-stage2 fetch --depth 1 origin main
     git -C external/equational-theories-lean-stage2 checkout --detach FETCH_HEAD
     ```
4. Confirm these local raw snapshots exist:
   - `data/raw/references/sair_api/competition_stage2_overview.html`
   - `data/raw/references/sair_api/competition_stage2_overview_bootstrap.json`
   - `data/raw/references/sair_api/competition_stage2.json`
   - `data/raw/references/sair_api/competitions.json`
   - `data/raw/references/stage2_judge/README.md`
   - `data/raw/references/stage2_judge/rules/overview.md`
   - `data/raw/references/stage2_judge/rules/evaluation.md`
   - `data/raw/references/stage2_judge/docs/solo_mode.md`
   - `data/raw/references/stage2_judge/docs/marathon_mode.md`
   - `data/raw/references/stage2_judge/judge/verify.py`
   - `data/raw/references/stage2_judge/pipeline/config.json`
   - `data/raw/references/stage2_judge/lean-toolchain`
   - `data/raw/references/stage2_judge/main_commit.json`
5. Compare key fields from the API snapshot, overview bootstrap JSON, official repo config, and external clone:
   - `updatedAt`, `participantCount`, `pythonMaxBytes`, legacy prompt-size max field, `allowDraftSubmissions`, `publicCodePrefix`
   - official repo commit SHA/date from `main_commit.json`
   - external clone HEAD from `git -C external/equational-theories-lean-stage2 rev-parse HEAD`
   - `pipeline/config.json` model/provider/token/budget/size fields
   - `judge/verify.py` proof-policy fields and `BANNED_PROOF_TOKENS`, especially when Zulip mentions Lean tactics, allowed declarations, or certificate policy
   - `lean-toolchain`
6. If official facts changed, update Chinese project docs:
   - `docs/competition-analysis.md` for rules, dates, budgets, risks, and open TBD items.
   - `docs/sources.md` for source URLs, local snapshot paths, and retrieval dates.
   - `docs/data-inventory.md` for raw snapshot inventory changes.
   - `docs/architecture.md` only when solver architecture constraints or priorities changed.
7. Preserve uncertainty explicitly. If official docs say TBD, write `TBD（待定）`; do not infer private evaluation set, final scoring, or final model details.
8. Run focused validation:
   ```bash
   pytest tests/data/test_download_public_data.py -q
   ```
9. Report the changed facts, raw snapshot paths, external clone HEAD, docs touched, and validation result.

## Source Priority

- Prefer official public sources: SAIR competition overview, SAIR public API, and `SAIRcompetition/equational-theories-lean-stage2`.
- Use the HTML bootstrap JSON for front-end pages when available.
- Use headless browser rendering only as a fallback when visible page text has changed but API/bootstrap/raw docs do not expose it.
- Do not use unofficial summaries as authoritative facts.

## Hard Constraints

- Do not edit prompt assets, evaluator runs, or solver logic while using this skill.
- Do not write new command scripts unless `scripts/data/download_public_data.py` cannot cover a stable official source.
- Keep raw downloads under `data/raw/references/`.
- Keep the official Stage 2 repository clone under `external/equational-theories-lean-stage2/`; `external/` is ignored by git and should not be committed.
- Keep new documentation in Chinese by default, preserving official English names, file paths, API fields, and Lean symbols as written.
- Treat root `/data/` as generated local snapshot storage; it is intentionally ignored by git.
