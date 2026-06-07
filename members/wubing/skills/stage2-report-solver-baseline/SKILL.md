---
name: stage2-report-solver-baseline
description: Use when creating or updating Stage 2 Solo solver baseline, progress, version-comparison, leadership brief, team report, or WeCom-ready summary materials.
---

# Stage2 Report Solver Baseline

Use this skill to turn solver versions and official run evidence into concise
Chinese-first reports for leaders and teammates.

## When To Use

- The user asks for a Stage 2 Solo solver baseline brief, progress report, or
  version comparison.
- The report should explain `current`, `drafts`, `versions`, accepted counts,
  accepted rate, false/true breakdown, LLM contribution, or solver changes.
- The user asks for a WeCom/企微-ready Markdown report or pasteable summary.

## Source Of Truth

Prefer existing artifacts; do not recompute unless requested.

- Solver lifecycle: `solvers/solo_official/current/manifest.json` and
  `solvers/solo_official/versions/YYYY-MM-DD/vN/manifest.json`.
- Run metrics: `artifacts/runs/YYYY-MM-DD/<run-id>/results/*.json`,
  `summary.json`, and `history.md`.
- Detailed experiment records stay in `docs/experiments/`.
- Leadership/team reports go in `docs/reports/`.

Use `stage2-train-version-solver` for version state and `stage2-train-analyze-run` when
metrics or failure categories must be derived from a run directory.

## Markdown Report Shape

Write short reports under:

```text
docs/reports/YYYY-MM-DD-short-title.md
```

Keep the report about one or two pages when rendered. Default sections:

1. 一句话结论
2. 当前最佳版本
3. 版本演进
4. 关键改动说明
5. 当前判断
6. 下一步

The version table should include:

- version id
- source, such as `v1 -> d1 -> v2`
- `solver.py` change summary
- `sample200` accepted count
- accepted rate
- `LLM calls / solved`
- note or newly solved ids

For code changes, do not use a table when the user needs implementation detail.
Use prose plus Python code snippets:

- State what changed relative to the previous version.
- Give the exact `solver.py` path or compact `vN/solver.py line N`.
- Show the relevant Python code snippets directly.
- Preserve indentation for snippets such as counterexample tables and early
  lookup branches.

## Output Rules

- Produce Markdown reports and pasteable summaries only.
- Do not generate PDF artifacts as part of this skill.
- If a separate explicit PDF task changes this scope, place the PDF in the same directory
  as the source Markdown and verify rendering/text extraction with
  tools such as `pdftoppm` and `pdftotext`.

## Report Index

For new report families, create or update:

- `docs/reports/README.md`
- `docs/README.md` if a new top-level documentation category is introduced

Do not link leadership summaries from `docs/experiments/README.md` unless the
file actually lives in `docs/experiments/`.

## Hard Constraints

- Do not edit official runner result JSON or logs.
- Do not edit `solver.py` while using this skill.
- Do not present LLM calls as accepted unless the official judge accepted the
  certificate.
- Do not generate report PDFs unless a separate task explicitly changes this
  scope.
- Do not paste long failed-id lists into leadership briefs unless explicitly
  requested.
- Keep new user-facing documentation Chinese-first, preserving code symbols and
  file paths in English.
