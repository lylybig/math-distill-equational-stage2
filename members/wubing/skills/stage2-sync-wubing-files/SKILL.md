---
name: stage2-sync-wubing-files
description: Use when the user asks to sync, copy, share, export, or hand off selected Stage 2 project files or artifacts into the Wubing member workspace under members/wubing.
---

# Stage2 Sync Wubing Files

Use this skill when the user wants specific files or directories synchronized to
the Wubing member workspace:

`members/wubing/`

If running from the team monorepo root, keep the shell there for this skill so
source paths like `docs/...` can be copied into `members/wubing/docs/...`.

## Workflow

1. Identify the exact source files or directories the user wants to sync.
   If the request says "these files" or depends on earlier context, infer from
   the current conversation; ask only if the source set is genuinely ambiguous.
2. Verify each source path exists before copying. Do not create or modify source
   files as part of this skill.
3. Create the destination directory if it does not already exist.
4. Preserve repository-relative paths under the destination by default. For
   example, sync `docs/reports/a.md` to
   `members/wubing/docs/reports/a.md`. If a source is outside the repository, use
   the source basename unless the user specifies a destination subdirectory.
   If the source is already under `members/wubing/`, report that it is already
   in the Wubing workspace unless the user explicitly asks for a duplicate copy.
5. Use `rsync -a --itemize-changes` or an equivalent safe copy command. Do not
   use `--delete` unless the user explicitly asks for mirror semantics.
6. For requested source paths, overwriting the corresponding destination copy is
   allowed as normal sync behavior. Do not overwrite unrelated files.
7. After syncing, report the destination paths and any skipped or missing
   sources.

## Constraints

- Do not sync broad globs, large raw datasets, or bulky generated artifacts
  unless the user explicitly selected them.
- Do not delete anything from the Wubing handoff directory without explicit
  instruction.
- Do not modify solver code, registry files, proof banks, or reports unless the
  user separately asks for those edits.
- This skill is only for file synchronization; it is not a solver training,
  proof bank, strategy registry, or official submission workflow.
