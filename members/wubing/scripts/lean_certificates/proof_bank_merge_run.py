from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))

from math_distill_stage2.proof_bank.bank import merge_run, preview_merge_run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Merge a proof bank run into the global bank.")
    parser.add_argument("--bank", type=Path, required=True)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--write", action="store_true", help="Required to perform the merge.")
    args = parser.parse_args(argv)
    if not args.write:
        print(
            json.dumps(
                preview_merge_run(args.bank, args.run),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    print(json.dumps(merge_run(args.bank, args.run), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
