from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import textwrap

from math_distill_stage2.dataset_io import read_jsonl, write_jsonl
from math_distill_stage2.order5_strategy_registry import (
    DEFAULT_EQ_SIZE5_PATH,
    DEFAULT_ORDER4_MAX_ID,
    _product_anchor_sets,
    _singleton_collapse_sets,
    product_anchor_true_judge_code,
    singleton_collapse_true_judge_code,
)
from math_distill_stage2.proof_bank.import_responses import preflight_raw_responses
from math_distill_stage2.proof_bank.keying import problem_key_from_equations


SINGLETON_STRATEGY_ID = "true.proof.templatecheck.singleton_collapse.any_target.v1"
PRODUCT_STRATEGY_ID = (
    "true.proof.templatecheck.term_shape_anchor.product.any_product_target.v1"
)
DEFAULT_BANK = Path("data/processed/proof_banks/gpt_true_certificates")
DEFAULT_RUN_ROOT = Path("artifacts/proof_bank_runs/2026-05-14")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a registry-template true proofbank run."
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--bank", type=Path, default=DEFAULT_BANK)
    parser.add_argument("--singleton-quota", type=int, default=1200)
    parser.add_argument("--product-quota", type=int, default=800)
    args = parser.parse_args()

    run_dir = args.run_root / args.run_id
    quotas = {
        SINGLETON_STRATEGY_ID: args.singleton_quota,
        PRODUCT_STRATEGY_ID: args.product_quota,
    }
    if run_dir.exists():
        raise SystemExit(f"run dir already exists: {run_dir}")

    generator = RegistryTemplateRunGenerator(
        run_id=args.run_id,
        run_dir=run_dir,
        bank=args.bank,
        quotas=quotas,
    )
    result = generator.generate()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if result["manifest"]["generation_errors"] or not result["preflight"].get("ok"):
        return 1
    return 0


class RegistryTemplateRunGenerator:
    def __init__(
        self,
        *,
        run_id: str,
        run_dir: Path,
        bank: Path,
        quotas: dict[str, int],
    ) -> None:
        self.run_id = run_id
        self.run_dir = run_dir
        self.bank = bank
        self.quotas = quotas
        self.rows: list[dict] = []

    def generate(self) -> dict:
        blocked = self._blocked_problem_keys()
        features, singleton_sources, singleton_targets, singleton_counts = (
            _singleton_collapse_sets(DEFAULT_EQ_SIZE5_PATH)
        )
        _, product_sources, product_targets, product_counts = _product_anchor_sets(
            DEFAULT_EQ_SIZE5_PATH
        )
        features_by_id = {feature.equation_id: feature for feature in features}

        generation_errors: dict[str, str] = {}
        for strategy_id, sources, targets in [
            (SINGLETON_STRATEGY_ID, singleton_sources, singleton_targets),
            (PRODUCT_STRATEGY_ID, product_sources, product_targets),
        ]:
            quota = self.quotas[strategy_id]
            selected = self._select(
                strategy_id=strategy_id,
                sources=sources,
                targets=targets,
                quota=quota,
                blocked=blocked,
                features_by_id=features_by_id,
            )
            if len(selected) != quota:
                generation_errors[strategy_id] = (
                    f"selected {len(selected)} of requested {quota}"
                )
            self.rows.extend(selected)

        self._write_run()
        manifest = self._write_manifest(
            blocked_count=len(blocked) - len(self.rows),
            singleton_sources=len(singleton_sources),
            singleton_targets=len(singleton_targets),
            singleton_counts=singleton_counts,
            product_sources=len(product_sources),
            product_targets=len(product_targets),
            product_counts=product_counts,
            generation_errors=generation_errors,
        )
        preflight = preflight_raw_responses(self.run_dir)
        return {
            "run_dir": str(self.run_dir),
            "manifest": manifest,
            "preflight": preflight,
        }

    def _blocked_problem_keys(self) -> set[str]:
        blocked = {
            str(row["problem_key"])
            for row in read_jsonl(self.bank / "attempts.jsonl")
            if row.get("problem_key")
        }
        for pending_path in self.run_dir.parent.glob("proofbank-20260514-*/input_problems.jsonl"):
            if (pending_path.parent / "summary.json").exists():
                continue
            if pending_path.parent == self.run_dir:
                continue
            for row in read_jsonl(pending_path):
                if row.get("problem_key"):
                    blocked.add(str(row["problem_key"]))
        return blocked

    def _select(
        self,
        *,
        strategy_id: str,
        sources: set[int] | frozenset[int],
        targets: set[int] | frozenset[int],
        quota: int,
        blocked: set[str],
        features_by_id: dict[int, object],
    ) -> list[dict]:
        selected = []
        for source_id in sorted(sources):
            source_feature = features_by_id[source_id]
            for target_id in sorted(targets):
                cls = _order_class(source_id, target_id)
                if cls is None:
                    continue
                target_feature = features_by_id[target_id]
                key = problem_key_from_equations(
                    source_feature.equation,
                    target_feature.equation,
                )
                if key in blocked:
                    continue
                blocked.add(key)
                selected.append(
                    {
                        "schema_version": 1,
                        "item_id": f"{len(self.rows) + len(selected) + 1:06d}",
                        "problem_key": key,
                        "source_problem_id": f"true_{source_id}_{target_id}",
                        "source_dataset": "order5_strategy_registry",
                        "source_candidate_stratum": f"registry_template_true:{strategy_id}",
                        "source_target_order_class": cls,
                        "strategy_id": strategy_id,
                        "verification_mode": "templatecheck",
                        "expected_verdict": True,
                        "eq1_id": source_id,
                        "eq2_id": target_id,
                        "equation1": source_feature.equation,
                        "equation2": target_feature.equation,
                        "certificate_family": (
                            "singleton_collapse"
                            if strategy_id == SINGLETON_STRATEGY_ID
                            else "product_anchor"
                        ),
                        "certificate_generator": (
                            "singleton_collapse"
                            if strategy_id == SINGLETON_STRATEGY_ID
                            else "product_anchor"
                        ),
                    }
                )
                if len(selected) >= quota:
                    return selected
        return selected

    def _write_run(self) -> None:
        self.run_dir.mkdir(parents=True)
        raw_dir = self.run_dir / "raw_responses"
        raw_dir.mkdir()
        write_jsonl(self.run_dir / "input_problems.jsonl", self.rows)
        for row in self.rows:
            proof = _raw_response_body(
                row["strategy_id"],
                row["equation1"],
                row["equation2"],
            )
            payload = {"verdict": "true", "proof": proof}
            (raw_dir / f"{row['item_id']}.txt").write_text(
                json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
            )

    def _write_manifest(
        self,
        *,
        blocked_count: int,
        singleton_sources: int,
        singleton_targets: int,
        singleton_counts: dict[str, int],
        product_sources: int,
        product_targets: int,
        product_counts: dict[str, int],
        generation_errors: dict[str, str],
    ) -> dict:
        selected_by_strategy = Counter(row["strategy_id"] for row in self.rows)
        selected_by_order_class = Counter(
            row["source_target_order_class"] for row in self.rows
        )
        manifest = {
            "schema_version": 1,
            "source_run_id": self.run_id,
            "run_dir": str(self.run_dir),
            "created_at_utc": datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "bank": str(self.bank),
            "generator": {
                "mode": "order5_strategy_registry_template_fast",
                "model": None,
            },
            "selector_version": "registry_template_true_proofbank_fast_v2_dedent",
            "source_strategy_registry": (
                "data/processed/order5_strategy_registry/strategies.json"
            ),
            "source_coverage_summary": (
                "data/processed/order5_strategy_registry/coverage_summary.json"
            ),
            "source_equations_path": str(DEFAULT_EQ_SIZE5_PATH),
            "quotas": self.quotas,
            "problem_count": len(self.rows),
            "blocked_attempted_problem_count": blocked_count,
            "selected_by_strategy": dict(sorted(selected_by_strategy.items())),
            "selected_by_order_class": dict(sorted(selected_by_order_class.items())),
            "source_counts": {
                SINGLETON_STRATEGY_ID: singleton_sources,
                PRODUCT_STRATEGY_ID: product_sources,
            },
            "target_counts": {
                SINGLETON_STRATEGY_ID: singleton_targets,
                PRODUCT_STRATEGY_ID: product_targets,
            },
            "shape_counts": {
                "singleton_collapse": dict(singleton_counts),
                "product_anchor": dict(product_counts),
            },
            "generation_errors": generation_errors,
        }
        (self.run_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return manifest


def _order_class(source_id: int, target_id: int) -> str | None:
    source_order5 = source_id > DEFAULT_ORDER4_MAX_ID
    target_order5 = target_id > DEFAULT_ORDER4_MAX_ID
    if source_order5 and target_order5:
        return "order5_source_to_order5_target"
    if source_order5:
        return "order5_source_to_order4_target"
    if target_order5:
        return "order4_source_to_order5_target"
    return "order4_source_to_order4_target"


def _raw_response_body(strategy_id: str, source_eq: str, target_eq: str) -> str:
    if strategy_id == SINGLETON_STRATEGY_ID:
        code = singleton_collapse_true_judge_code(source_eq, target_eq)
    elif strategy_id == PRODUCT_STRATEGY_ID:
        code = product_anchor_true_judge_code(source_eq, target_eq)
    else:
        raise ValueError(strategy_id)
    return _body_from_code(code)


def _body_from_code(code: str) -> str:
    lines = code.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == "intro G _ h":
            return textwrap.dedent("\n".join(lines[index + 1 :])).strip()
    raise ValueError("generated code did not contain expected intro")


if __name__ == "__main__":
    raise SystemExit(main())
