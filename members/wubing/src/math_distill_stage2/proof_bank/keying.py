from __future__ import annotations

import hashlib

from math_distill_stage2.equations import canonical_equation_signature


def normalize_equation_operator(source: str) -> str:
    return source.replace("◇", "*")


def canonical_signature_for_bank(source: str) -> str:
    return canonical_equation_signature(normalize_equation_operator(source))


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def short_hash(text: str, length: int = 16) -> str:
    if length <= 0 or length > 64:
        raise ValueError("length must be between 1 and 64")
    return sha256_hex(text)[:length]


def problem_key_from_signatures(eq1_signature: str, eq2_signature: str) -> str:
    return f"implication:sig:{short_hash(eq1_signature)}:{short_hash(eq2_signature)}"


def problem_key_from_equations(equation1: str, equation2: str) -> str:
    return problem_key_from_signatures(
        canonical_signature_for_bank(equation1),
        canonical_signature_for_bank(equation2),
    )
