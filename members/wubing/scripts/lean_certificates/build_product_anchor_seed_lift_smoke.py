#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl  # noqa: E402
from math_distill_stage2.order5_product_anchor_seed_lift import (  # noqa: E402
    render_product_anchor_seed_lift_certificate,
)


DEFAULT_EQUATIONS_FILE = Path(
    "external/equational-theories-lean-stage2/examples/problems/eq_size5.txt"
)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build remote-smoke rows for product-anchor proofbank seed-lift candidates."
    )
    parser.add_argument("--candidate-jsonl", type=Path, required=True)
    parser.add_argument("--output-jsonl", type=Path, required=True)
    parser.add_argument("--summary-json", type=Path, required=True)
    parser.add_argument("--equations-file", type=Path, default=DEFAULT_EQUATIONS_FILE)
    parser.add_argument("--target-id", type=int, action="append", required=True)
    parser.add_argument("--source-id", type=int, action="append")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    equation_texts = _load_equation_texts(args.equations_file)
    requested_sources = set(args.source_id or [])
    target_ids = list(dict.fromkeys(args.target_id))
    candidate_rows = read_jsonl(args.candidate_jsonl)
    smoke_rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for candidate in candidate_rows:
        for seed_proof in candidate.get("source_seed_proofs", []):
            source_id = int(seed_proof["source_id"])
            if requested_sources and source_id not in requested_sources:
                continue
            for target_id in target_ids:
                try:
                    smoke_rows.append(
                        _smoke_row(
                            candidate=candidate,
                            seed_proof=seed_proof,
                            target_id=target_id,
                            target_equation=equation_texts[target_id],
                        )
                    )
                except Exception as exc:  # noqa: BLE001
                    errors.append(
                        {
                            "source_id": source_id,
                            "target_id": target_id,
                            "error_kind": type(exc).__name__,
                            "error_summary": str(exc),
                        }
                    )

    write_jsonl(args.output_jsonl, smoke_rows)
    summary = {
        "schema_version": 1,
        "candidate_jsonl": str(args.candidate_jsonl),
        "output_jsonl": str(args.output_jsonl),
        "equations_file": str(args.equations_file),
        "source_ids": sorted({int(row["source_id"]) for row in smoke_rows}),
        "target_ids": target_ids,
        "row_count": len(smoke_rows),
        "error_count": len(errors),
        "errors": errors[:20],
    }
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


def _load_equation_texts(path: Path) -> dict[int, str]:
    return {
        index: line.strip()
        for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if line.strip()
    }


def _smoke_row(
    *,
    candidate: dict[str, Any],
    seed_proof: dict[str, Any],
    target_id: int,
    target_equation: str,
) -> dict[str, Any]:
    source_id = int(seed_proof["source_id"])
    proof_body = Path(seed_proof["proof_body_path"]).read_text(encoding="utf-8")
    code = render_product_anchor_seed_lift_certificate(
        seed_equation=str(seed_proof["seed_product_anchor_equation"]),
        target_equation=target_equation,
        source_to_seed_proof_body=proof_body,
    )
    problem = {
        "id": f"product_anchor_seed_lift_{source_id}_{target_id}",
        "eq1_id": source_id,
        "eq2_id": target_id,
        "equation1": seed_proof["source_equation"],
        "equation2": target_equation,
        "answer": True,
    }
    return {
        "schema_version": 1,
        "id": problem["id"],
        "candidate_key": candidate["candidate_key"],
        "verdict": True,
        "source_id": source_id,
        "target_id": target_id,
        "source_seed_proof": seed_proof,
        "problem": problem,
        "answer": {
            "call": "judge",
            "verdict": "true",
            "code": code,
        },
    }


if __name__ == "__main__":
    raise SystemExit(main())
