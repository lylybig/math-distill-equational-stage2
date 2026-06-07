from pathlib import Path

from math_distill_stage2 import order5_strategy_registry as registry


def test_singleton_seedbank_specialization_uses_equal_skeleton_fast_path(
    monkeypatch,
    tmp_path: Path,
):
    equations = tmp_path / "eq_size5.txt"
    equations.write_text("x * y = z\n", encoding="utf-8")
    seed_equation = registry._parse_stage2_equation("a * a = b")

    monkeypatch.setattr(
        registry,
        "_singleton_seed_equations",
        lambda equations_path: ((1, seed_equation),),
    )

    def fail_scan(*_args, **_kwargs):
        raise AssertionError("same-size seed/source should use skeleton lookup")

    monkeypatch.setattr(
        registry,
        "_match_singleton_seedbank_specialization_from_seeds",
        fail_scan,
    )

    _features, sources, targets, match_counts = (
        registry._singleton_seedbank_specialization_sets(equations)
    )

    assert sources == frozenset({1})
    assert targets == frozenset({1})
    assert match_counts == {1: 1}
