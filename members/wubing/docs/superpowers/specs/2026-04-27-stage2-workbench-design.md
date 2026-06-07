# Stage 2 Workbench Design

## Purpose

Build a local, repeatable workbench for the SAIR Equational Theories Stage 2
competition. The workbench stores source material, public datasets, and the
first reusable code needed for a certificate-producing solver.

## Architecture

The workbench is split into three layers:

1. Source snapshots: raw public problem files, competition API payloads, and
   selected ETP metadata under `data/raw/` and `references/`.
2. Python tooling: parser and dataset index utilities under
   `src/math_distill_stage2/`.
3. Generated artifacts: processed problem indexes and future certificate
   outputs under `data/processed/` and `artifacts/`.

This keeps raw data immutable and makes all derived files rebuildable.

## Components

- `math_distill_stage2.equations`: parse and canonicalize equation strings.
- `math_distill_stage2.dataset_io`: load/write JSONL, validate counts, and
  summarize public subsets.
- `scripts/download_public_data.py`: download bounded public source snapshots.
- `scripts/build_problem_index.py`: create canonical indexed public problems.

## Data Flow

1. Download raw JSONL and source metadata.
2. Load each subset and validate row counts.
3. Parse `equation1` and `equation2`.
4. Add canonical signatures.
5. Write processed index and summary.

## Testing

Use TDD for parser and dataset utilities. Tests should cover whitespace,
parentheses, alpha-equivalent signatures, invalid syntax, JSONL round-trips,
and count validation.

## Deferred Work

- ETP implication graph compression.
- Finite magma hitting-set counterexample bank.
- Lean certificate generator.
- Official Stage 2 judge adapter once published.
