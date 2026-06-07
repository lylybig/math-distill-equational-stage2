from math_distill_stage2.proof_bank.keying import (
    canonical_signature_for_bank,
    problem_key_from_equations,
    sha256_hex,
    short_hash,
)


def test_canonical_signature_accepts_diamond_operator():
    assert canonical_signature_for_bank("x = y ◇ x") == "v0=(v1*v0)"


def test_problem_key_is_signature_first_and_oriented():
    forward = problem_key_from_equations("x = y ◇ x", "x = x ◇ y")
    backward = problem_key_from_equations("x = x ◇ y", "x = y ◇ x")

    assert forward.startswith("implication:sig:")
    assert forward != backward
    assert len(forward.split(":")[-1]) == 16


def test_short_hash_uses_sha256_prefix():
    digest = sha256_hex("abc")
    assert digest == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert short_hash("abc") == "ba7816bf8f01cfea"
