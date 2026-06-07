from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))

from math_distill_stage2.proof_bank.quality_audit import audit_proof_bank_quality


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit proof bank quality and loop readiness.")
    parser.add_argument("--bank", type=Path, required=True)
    parser.add_argument("--run-summary", type=Path)
    parser.add_argument("--sampled-manifest", type=Path)
    parser.add_argument("--marathon-state", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    audit = audit_proof_bank_quality(
        bank=args.bank,
        run_summary_path=args.run_summary,
        sampled_manifest_path=args.sampled_manifest,
        marathon_state_path=args.marathon_state,
        output_path=args.output,
    )
    print(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if audit["decision"] in {"continue", "continue_with_adjusted_sampling", "stop_complete"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
