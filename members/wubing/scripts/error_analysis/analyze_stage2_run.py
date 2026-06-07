from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))
    sys.path.insert(0, str(repo_root))

from math_distill_stage2.error_analysis.stage2_run import (  # noqa: E402
    analyze_stage2_run,
    build_arg_parser,
    classify_record,
    main,
)

__all__ = ["analyze_stage2_run", "build_arg_parser", "classify_record", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
