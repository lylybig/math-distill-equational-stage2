from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))
    sys.path.insert(0, str(repo_root))

from math_distill_stage2.lean_certificates import (
    negative_finite_counterexample_certificate,
    positive_implication_certificate,
    positive_path_certificate,
)


def generate_smoke_certificates(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    positive = output_dir / "positive_equation2_implies_equation3.lean"
    positive_path = output_dir / "positive_path_equation2_implies_equation8.lean"
    negative = output_dir / "negative_equation23_not_implies_equation39.lean"

    positive.write_text(
        positive_implication_certificate(
            theorem_name="Subgraph.Equation2_implies_Equation3",
            lhs_id=2,
            rhs_id=3,
        ),
        encoding="utf-8",
    )
    negative.write_text(
        negative_finite_counterexample_certificate(lhs_id=23, rhs_id=39),
        encoding="utf-8",
    )
    positive_path.write_text(
        positive_path_certificate(
            [
                {
                    "lhs_id": 2,
                    "rhs_id": 3,
                    "name": "Subgraph.Equation2_implies_Equation3",
                    "filename": "./equational_theories/Subgraph.lean",
                },
                {
                    "lhs_id": 3,
                    "rhs_id": 8,
                    "name": "Subgraph.Equation3_implies_Equation8",
                    "filename": "./equational_theories/Subgraph.lean",
                },
            ]
        ),
        encoding="utf-8",
    )
    return [positive, positive_path, negative]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("certificates/smoke"),
    )
    args = parser.parse_args()

    for path in generate_smoke_certificates(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
