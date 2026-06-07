---
name: stage2-train-proof-seed
description: Use when preparing bounded offline proof-seed data for remaining Stage 2 Solo true failures, including external proof trace clustering, Lean proof exploration, and reusable solver-template candidates.
---

# Stage2 Train Proof Seed

Use this skill to prepare evidence before changing `solver.py`. A proof seed is
a small, reproducible record that connects one or more failed true problems to:

- the external proof source or trace,
- a judge-accepted Lean certificate attempt or the blocking Lean error,
- the reusable proof pattern that could become a deterministic solver template.

This skill is a sub-workflow of `stage2-train-offline-explore-solver`.

## When To Use

- Remaining true failures need clustering before choosing the next dN target.
- A Vampire, EquationSearch, or other external proof trace may contain a
  reusable pattern.
- A single representative problem needs Lean proof exploration before deciding
  whether to edit `solver.py`.
- LLM assistance is being considered as an offline proof translator, not as a
  runtime scoring path.

## Workflow

1. Start from the latest validated order4 split run, usually `dev_fast`,
   `dev_main`, or `stress_true`, and its remaining true failures.
2. Build a small proof-seed subset; prefer 1-3 representative ids, not the
   whole suite.
3. For each id, record:
   - `problem_id`, `eq1_id`, `eq2_id`, equations, and current verdict.
   - external source file and theorem name, if available.
   - proof family: `Vampire`, `EquationSearch`, direct rewrite, tactic variant,
     or unknown.
   - proof shape: projection, absorption, collapse, idempotence, commutativity,
     constancy, theorem chain, or unknown.
   - trace size and key derived lemmas.
   - attempted Lean certificate, judge status, LLM calls if any, and errors.
   - candidate solver template and expected blast radius.
4. Use `lean-proof` methodology only for selected single-problem proof
   exploration: one step at a time, check Lean diagnostics, stop after the
   bounded probe limit.
5. Use LLMs only as offline translators when useful: provide the external trace,
   allowed certificate constructs, and Lean diagnostics; do not increase the
   runtime solver LLM loop based only on translation attempts.
6. Store findings in `docs/experiments/` or draft notes. Do not edit official
   runner results.
7. Hand off to `stage2-train-improve-solver` only when there is a narrow
   template candidate and a focused test target.

## Hard Constraints

- Do not edit `solver.py` while using this skill.
- Do not promote, export, or modify `submissions/solo_official/`.
- Do not add known-proof table entries.
- Do not run unbounded proof search, marathon jobs, cloud jobs, or bulk LLM
  calls.
- Do not treat an external theorem import as a valid Stage 2 certificate; every
  seed must be judged against the official Stage 2 judge contract.
- Do not start a runtime `MAX_LLM_ROUNDS` increase from this skill. That belongs
  to a separate targeted experiment with `stage2-train-evaluate`.

## Output

Record:

- subset inspected and selection reason,
- external proof sources and trace classifications,
- Lean proof probes and limits,
- accepted/rejected/error outcomes,
- reusable pattern candidates and non-generalizing dead ends,
- next focused test target, or a decision to keep exploring.
