---
name: stage2-info-zulip-channel
description: Use when the user asks to update, sync, archive, fetch, crawl, summarize, digest, or review the SAIR Zulip Math Distillation Challenge equational theories channel, including daily message summaries or full original Zulip message archives.
---

# Stage2 Info Zulip Channel

Use this skill to sync the SAIR Zulip channel `Math Distillation Challenge - equational theories`, archive original messages, and generate daily Chinese-first digests.

## Working Directory

All relative paths in this skill are relative to `members/wubing/`. If the shell
is at the team monorepo root, run `cd members/wubing` or set the command
`workdir` there before executing the commands below.

## Workflow

1. Check credential availability without printing secrets:
   - Prefer `ZULIP_CONFIG_FILE`.
   - Otherwise use `~/.zuliprc`.
   - Expected config fields under `[api]`: `site`, `email`, `key`.
2. Run the reproducible sync command:
   ```bash
   python scripts/data/sync_zulip_channel.py
   ```
3. For a bounded first backfill, pass an ISO date:
   ```bash
   python scripts/data/sync_zulip_channel.py --since 2026-05-01
   ```
4. Confirm updated outputs:
   - `data/raw/references/zulip/math-distillation-challenge-equational-theories/state.json`
   - `data/raw/references/zulip/math-distillation-challenge-equational-theories/messages/YYYY-MM-DD.jsonl`
   - `docs/zulip-digests/YYYY-MM-DD.md`
5. Read the generated digest and preserve source boundaries:
   - Zulip is useful discussion context.
   - Official rules, official API snapshots, and the official judge repository remain authoritative.
   - Use `stage2-info-competition` when a Zulip message claims an official fact that should be checked against official sources.
   - If a Zulip message discusses Lean tactics, proof policy, allowed declarations, banned constructs, or certificate acceptance rules, cross-check `data/raw/references/stage2_judge/judge/verify.py` after running `stage2-info-competition`; summarize Zulip as discussion context and cite `judge/verify.py` as the authoritative local implementation snapshot.
6. Run focused validation:
   ```bash
   pytest tests/data/test_zulip_archive.py tests/skills/test_stage2_skills.py -q
   ```
7. Report message count, dates, archive paths, digest paths, state path, and validation result.

## Daily Automation

This skill may be used from cron or systemd timer by running:

```bash
cd members/wubing
python scripts/data/sync_zulip_channel.py
```

Recommended local cron entry for once per day at 09:00 local time:

```cron
0 9 * * * cd /path/to/math-distill-equational-stage2/members/wubing && /usr/bin/python3 scripts/data/sync_zulip_channel.py >> artifacts/zulip-sync.log 2>&1
```

Recommended systemd timer shape:

```ini
# ~/.config/systemd/user/stage2-zulip-sync.service
[Service]
WorkingDirectory=/path/to/math-distill-equational-stage2/members/wubing
ExecStart=/usr/bin/python3 scripts/data/sync_zulip_channel.py
```

```ini
# ~/.config/systemd/user/stage2-zulip-sync.timer
[Timer]
OnCalendar=*-*-* 09:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Do not modify the user's crontab or systemd user units unless explicitly requested with a time and delivery target.

## Delivery Targets

Local automation can always write to:

- `data/raw/references/zulip/math-distillation-challenge-equational-theories/messages/YYYY-MM-DD.jsonl`
- `docs/zulip-digests/YYYY-MM-DD.md`
- an optional local log such as `artifacts/zulip-sync.log`

It cannot reliably send to the current ChatGPT thread from cron or systemd timer, because the local scheduled process does not have a stable API handle for this conversation. 简短规则：不能可靠发送到当前 ChatGPT thread。If the user wants push delivery, ask for one explicit target and configure that separately, for example:

- email through a local mail command or SMTP wrapper
- Slack or Teams webhook
- GitHub issue/comment using the GitHub app or `gh`
- a daily local Markdown file only, then the user asks Codex to read it

Never send Zulip API keys, raw private content, or unreviewed digests to an external destination without explicit user approval.

## Report Language

Default report style is 中文为主:

- Use Chinese section titles and Chinese conclusions.
- Preserve important English terms such as `Lean`, `solver.py`, `judge`, `certificate`, `NumPy`, and `SymPy`.
- Keep short English original excerpts when they are needed for traceability.
- For user-facing summaries in chat, prefer Chinese bullets with source message IDs.

If the user asks for bilingual output, use 中英对照:

- Write one concise English bullet or paragraph.
- Follow immediately with the corresponding Chinese explanation.
- Do not machine-translate long raw Zulip messages wholesale; summarize the competition-relevant point and keep message IDs for lookup.

## Hard Constraints

- Do not print, commit, copy, or summarize Zulip API keys.
- Do not commit `data/raw/` unless the project policy changes; it is local generated snapshot storage.
- Do not rewrite `solver.py`, official run artifacts, official snapshots, or judge certificates while using this skill.
- Do not treat LLM-generated digest text as official fact.
- Keep new user-facing docs in Chinese by default.
- If Zulip credentials are missing or the channel is not accessible, stop after reporting the local credential path checked.
