from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))
    sys.path.insert(0, str(repo_root))

from math_distill_stage2.counterexample.verifier import verify_counterexample_assets
from math_distill_stage2.lean_executor import DockerLeanExecutor
from math_distill_stage2.lean_executor.docker import DEFAULT_LEAN_DOCKER_IMAGE


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("data/assets/counterexamples"),
        help="Counterexample asset root.",
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--backend", choices=["docker"], default="docker")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout-seconds", type=int, default=60)
    parser.add_argument("--image", default=DEFAULT_LEAN_DOCKER_IMAGE)
    parser.add_argument("--lean-image-digest")
    parser.add_argument("--cpu-limit", default="1")
    parser.add_argument("--memory-limit", default="512m")
    args = parser.parse_args()

    executor = DockerLeanExecutor(
        image=args.image,
        cpu_limit=args.cpu_limit,
        memory_limit=args.memory_limit,
        lean_image_digest=args.lean_image_digest,
    )

    summary = verify_counterexample_assets(
        root=args.root,
        run_id=args.run_id,
        executor=executor,
        workers=args.workers,
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
