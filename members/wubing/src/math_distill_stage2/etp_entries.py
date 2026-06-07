from __future__ import annotations

import json
import re
from pathlib import Path

from math_distill_stage2.dataset_io import write_jsonl


EQUATION_REF_RE = re.compile(r"^Equation(\d+)$")


def parse_equation_ref(value: str) -> int:
    match = EQUATION_REF_RE.match(value)
    if not match:
        raise ValueError(f"invalid equation reference: {value!r}")
    return int(match.group(1))


def build_etp_result_index(raw_entries_path: Path, output_dir: Path) -> dict:
    entries = json.loads(raw_entries_path.read_text(encoding="utf-8"))
    implications: list[dict] = []
    facts: list[dict] = []
    unconditionals: list[dict] = []

    for entry in entries:
        variant = entry["variant"]
        common = {
            "name": entry.get("name"),
            "filename": entry.get("filename"),
            "line": entry.get("line"),
            "proven": bool(entry.get("proven")),
        }
        if "implication" in variant:
            item = variant["implication"]
            implications.append(
                {
                    **common,
                    "lhs": item["lhs"],
                    "rhs": item["rhs"],
                    "lhs_id": parse_equation_ref(item["lhs"]),
                    "rhs_id": parse_equation_ref(item["rhs"]),
                    "finite": bool(item.get("finite")),
                }
            )
        elif "facts" in variant:
            item = variant["facts"]
            facts.append(
                {
                    **common,
                    "satisfied": item.get("satisfied", []),
                    "refuted": item.get("refuted", []),
                    "satisfied_ids": [parse_equation_ref(ref) for ref in item.get("satisfied", [])],
                    "refuted_ids": [parse_equation_ref(ref) for ref in item.get("refuted", [])],
                    "finite": bool(item.get("finite")),
                }
            )
        elif "unconditional" in variant:
            ref = variant["unconditional"]
            unconditionals.append(
                {
                    **common,
                    "equation": ref,
                    "equation_id": parse_equation_ref(ref),
                }
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_dir / "etp_implications.jsonl", implications)
    write_jsonl(output_dir / "etp_facts.jsonl", facts)
    write_jsonl(output_dir / "etp_unconditionals.jsonl", unconditionals)

    summary = {
        "source": str(raw_entries_path),
        "entries": len(entries),
        "implications": len(implications),
        "facts": len(facts),
        "unconditionals": len(unconditionals),
    }
    (output_dir / "etp_result_index.summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return summary
