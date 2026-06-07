#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))
    sys.path.insert(0, str(repo_root))

from math_distill_stage2.order5_setcheck_mining import (  # noqa: E402
    _load_parsed_equations,
    _normalize_table,
)
from math_distill_stage2.order5_spine_smoke import DEFAULT_EQ_SIZE5_PATH  # noqa: E402
from math_distill_stage2.order5_strategy_registry import (  # noqa: E402
    _affine_mod_equation_holds,
    finmodel_false_judge_code,
)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build representative remote-smoke rows for affine mod setcheck candidates."
    )
    parser.add_argument("--selection-jsonl", type=Path, required=True)
    parser.add_argument("--output-jsonl", type=Path, required=True)
    parser.add_argument("--summary-json", type=Path, required=True)
    parser.add_argument("--equations-file", type=Path, default=DEFAULT_EQ_SIZE5_PATH)
    parser.add_argument(
        "--candidate-limit",
        type=int,
        default=0,
        help="Optional max number of selected candidate rows to emit; 0 means all.",
    )
    parser.add_argument(
        "--certificate-style",
        choices=("table", "affine_formula"),
        default="table",
        help=(
            "False certificate encoding. 'table' uses the generic finite table; "
            "'affine_formula' writes the affine mod operation directly."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if args.candidate_limit < 0:
        raise SystemExit("--candidate-limit must be non-negative")

    equations = {
        equation_id: equation for equation_id, equation in _load_parsed_equations(args.equations_file)
    }
    equation_texts = {
        index: line.strip()
        for index, line in enumerate(args.equations_file.read_text(encoding="utf-8").splitlines(), start=1)
        if line.strip()
    }
    selected_rows = _read_jsonl(args.selection_jsonl)
    if args.candidate_limit:
        selected_rows = selected_rows[: args.candidate_limit]

    smoke_rows: list[dict] = []
    candidate_summaries: list[dict] = []
    for row in selected_rows:
        rows_for_candidate = _smoke_rows_for_candidate(
            row,
            equations=equations,
            equation_texts=equation_texts,
            certificate_style=args.certificate_style,
        )
        smoke_rows.extend(rows_for_candidate)
        candidate_summaries.append(
            {
                "candidate_key": row["candidate_key"],
                "smoke_row_count": len(rows_for_candidate),
                "exact_current_false_union_increment": row.get(
                    "exact_current_false_union_increment"
                ),
                "true_overlap_count": row.get("true_overlap_count"),
                "representative_pairs": row.get("representative_pairs"),
            }
        )

    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    args.output_jsonl.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in smoke_rows)
        + ("\n" if smoke_rows else ""),
        encoding="utf-8",
    )
    summary = {
        "schema_version": 1,
        "selection_path": str(args.selection_jsonl),
        "output_path": str(args.output_jsonl),
        "candidate_count": len(selected_rows),
        "smoke_row_count": len(smoke_rows),
        "certificate_style": args.certificate_style,
        "candidate_summaries": candidate_summaries,
    }
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _smoke_rows_for_candidate(
    row: dict,
    *,
    equations: dict[int, object],
    equation_texts: dict[int, str],
    certificate_style: str,
) -> list[dict]:
    table = _normalize_table(row["model_table"])
    modulus = int(row["modulus"])
    a = int(row["a"])
    b = int(row["b"])
    c = int(row["c"])
    if certificate_style == "table":
        code = finmodel_false_judge_code(table)
    elif certificate_style == "affine_formula":
        code = _affine_mod_false_judge_code(modulus=modulus, a=a, b=b, c=c)
    else:
        raise ValueError(f"unsupported certificate style: {certificate_style}")
    model_label = str(row.get("label") or _safe_id(row["candidate_key"]))
    rows: list[dict] = []
    for tier, pair in (row.get("representative_pairs") or {}).items():
        if pair is None:
            continue
        source_id, target_id = (int(pair[0]), int(pair[1]))
        source_holds = _affine_mod_equation_holds(
            equations[source_id],
            modulus=modulus,
            a=a,
            b=b,
            c=c,
        )
        target_holds = _affine_mod_equation_holds(
            equations[target_id],
            modulus=modulus,
            a=a,
            b=b,
            c=c,
        )
        if not source_holds or target_holds:
            raise ValueError(
                "representative pair is not refuted by affine candidate "
                f"{row['candidate_key']}: {source_id}->{target_id}"
            )
        pair_id = f"{_safe_id(model_label)}_{tier}_{source_id}_{target_id}"
        rows.append(
            {
                "schema_version": 1,
                "id": f"affine_mod_setcheck_smoke_{pair_id}",
                "candidate_key": row["candidate_key"],
                "model_label": model_label,
                "order": len(table),
                "table": [list(item) for item in table],
                "smoke_tier": tier,
                "expected_exact_increment": row.get("exact_current_false_union_increment"),
                "true_overlap_count": row.get("true_overlap_count"),
                "symbolic_pair_verified": True,
                "problem": {
                    "id": f"affine_mod_setcheck_smoke_{tier}_{source_id}_{target_id}",
                    "answer": False,
                    "eq1_id": source_id,
                    "eq2_id": target_id,
                    "equation1": equation_texts[source_id],
                    "equation2": equation_texts[target_id],
                },
                "answer": {
                    "call": "judge",
                    "verdict": "false",
                    "code": code,
                },
            }
        )
    return rows


def _affine_mod_false_judge_code(*, modulus: int, a: int, b: int, c: int) -> str:
    return (
        "import JudgeProblem\n"
        "import JudgeDecide.DecideBang\n"
        "set_option maxRecDepth 1000000\n"
        "set_option maxHeartbeats 0\n\n"
        "def submission : Goal := by\n"
        f"  let m : Magma (Fin {modulus}) := {{\n"
        "    op := fun i j =>\n"
        f"      Fin.ofNat (n := {modulus}) ({a} * i.val + {b} * j.val + {c})\n"
        "  }\n"
        f"  refine ⟨Fin {modulus}, m, ?_⟩\n"
        "  decideFin!\n"
    )


def _safe_id(raw: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", raw).strip("_")


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


if __name__ == "__main__":
    raise SystemExit(main())
