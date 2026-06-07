from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))

from math_distill_stage2.proof_bank.bank import rebuild_indexes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rebuild derived indexes for the proof bank.")
    parser.add_argument("--bank", type=Path, required=True)
    parser.add_argument("--write", action="store_true", help="Accepted for interface consistency; rebuild writes indexes.")
    args = parser.parse_args(argv)
    print(json.dumps(rebuild_indexes(args.bank), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
