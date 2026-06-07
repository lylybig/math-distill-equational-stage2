#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any


TRUE_PROBLEM = {
    "id": "p_true_basic",
    "eq1_id": 38,
    "eq2_id": 42,
    "equation1": "x \u25c7 x = x \u25c7 y",
    "equation2": "x \u25c7 y = x \u25c7 z",
}
TRUE_CODE = (
    "import JudgeProblem\n\n"
    "def submission : Goal := by\n"
    "  intro G _ h\n"
    "  intro x y z\n"
    "  rw [\u2190 h, h]\n"
)

FALSE_PROBLEM = {
    "id": "p_false_witness",
    "eq1_id": 4,
    "eq2_id": 65,
    "equation1": "x = x \u25c7 y",
    "equation2": "x = y \u25c7 (x \u25c7 (y \u25c7 x))",
    "proof_policy": {
        "allowed_axioms": ["Classical.choice", "Quot.sound", "propext"],
        "allowed_declarations": ["Goal", "id", "letFun"],
        "allowed_declaration_prefixes": [
            "And.",
            "Bool.",
            "Classical.",
            "Decidable.",
            "Eq.",
            "Equation",
            "Exists.",
            "False.",
            "Fin.",
            "Fintype.",
            "Function.",
            "HEq.",
            "Iff.",
            "Init.",
            "Int.",
            "Lean.",
            "List.",
            "Magma.",
            "Mathlib.",
            "MemoFinOp.",
            "Nat.",
            "Nonempty.",
            "Not.",
            "OfNat.",
            "Option.",
            "Or.",
            "Prod.",
            "PUnit.",
            "Std.",
            "Subtype.",
            "Sum.",
            "True.",
            "Unit.",
            "inst",
            "of_decide_",
            "submission.",
        ],
    },
}
FALSE_CODE = (
    "import JudgeProblem\n"
    "import JudgeDecide.DecideBang\n"
    "import JudgeFinOp.MemoFinOp\n"
    "open MemoFinOp\n\n"
    "def submission : Goal := by\n"
    "  let candidateMagma : Magma (Fin 2) := {\n"
    "    op := finOpTable \"[[0,0],[1,1]]\"\n"
    "  }\n"
    "  refine \u27e8Fin 2, candidateMagma, ?_\u27e9\n"
    "  decideFin!\n"
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test a judge_v2 worker.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8889")
    parser.add_argument("--timeout-seconds", type=int, default=120)
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")

    health = _get_json(f"{base_url}/health", timeout=10)
    print("[health]", json.dumps(_pick(health, "status", "service", "workers_busy", "workers_total"), ensure_ascii=False))

    true_first = _verify(
        base_url,
        problem=TRUE_PROBLEM,
        verdict="true",
        code=TRUE_CODE,
        timeout_seconds=args.timeout_seconds,
    )
    _expect_accepted("true_first", true_first)
    print("[true_first]", _summary(true_first))

    true_cached = _verify(
        base_url,
        problem=TRUE_PROBLEM,
        verdict="true",
        code=TRUE_CODE,
        timeout_seconds=args.timeout_seconds,
    )
    _expect_accepted("true_cached", true_cached)
    if true_cached.get("cached") is not True:
        raise RuntimeError("true_cached did not report cached=true")
    print("[true_cached]", _summary(true_cached))

    false_first = _verify(
        base_url,
        problem=FALSE_PROBLEM,
        verdict="false",
        code=FALSE_CODE,
        timeout_seconds=args.timeout_seconds,
    )
    _expect_accepted("false_first", false_first)
    print("[false_first]", _summary(false_first))

    return 0


def _get_json(url: str, *, timeout: int) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _verify(
    base_url: str,
    *,
    problem: dict[str, Any],
    verdict: str,
    code: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    payload = {
        "problem": problem,
        "verdict": verdict,
        "code": code,
        "timeout_seconds": timeout_seconds,
    }
    request = urllib.request.Request(
        f"{base_url}/verify",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.time()
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds + 60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc
    data["_client_elapsed_ms"] = int((time.time() - started) * 1000)
    return data


def _expect_accepted(name: str, payload: dict[str, Any]) -> None:
    if payload.get("status") != "accepted" or payload.get("error_code") != "ACCEPTED":
        raise RuntimeError(f"{name} failed: {json.dumps(payload, ensure_ascii=False)}")


def _summary(payload: dict[str, Any]) -> str:
    picked = _pick(payload, "status", "error_code", "cached", "elapsed_ms", "_client_elapsed_ms")
    return json.dumps(picked, ensure_ascii=False)


def _pick(payload: dict[str, Any], *keys: str) -> dict[str, Any]:
    return {key: payload.get(key) for key in keys}


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)

