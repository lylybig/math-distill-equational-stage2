import subprocess
import sys
from pathlib import Path

import pytest

from math_distill_stage2.lean_certificates import (
    finite_magma_counterexample_certificate,
    module_name_from_lean_filename,
    negative_finite_counterexample_certificate,
    positive_implication_certificate,
    positive_path_certificate,
    pure_finite_magma_counterexample_certificate,
)


def test_positive_implication_certificate_uses_etp_theorem():
    code = positive_implication_certificate(
        theorem_name="Subgraph.Equation2_implies_Equation3",
        lhs_id=2,
        rhs_id=3,
    )

    assert "import equational_theories.Subgraph" in code
    assert "theorem stage2_positive_cert" in code
    assert "(h : Equation2 G) : Equation3 G" in code
    assert "Subgraph.Equation2_implies_Equation3 G h" in code


def test_negative_finite_counterexample_certificate_emits_inline_fin_magma():
    code = negative_finite_counterexample_certificate(lhs_id=23, rhs_id=39)

    assert "import Mathlib.Tactic" in code
    assert "import equational_theories.Equations.Basic" in code
    assert "theorem stage2_negative_cert" in code
    assert "Equation23 G ∧ ¬ Equation39 G" in code
    assert "Fin 2" in code
    assert "by decide" in code


def test_finite_magma_counterexample_certificate_uses_table_operation():
    code = finite_magma_counterexample_certificate(
        lhs_id=649,
        rhs_id=2608,
        table=[[0, 0], [1, 1]],
        theorem_name="stage2_negative_cert_normal_0003",
    )

    assert "import Mathlib.Tactic" in code
    assert "import equational_theories.Equations.All" in code
    assert "theorem stage2_negative_cert_normal_0003" in code
    assert "Equation649 G ∧ ¬ Equation2608 G" in code
    assert "let op : Fin 2 → Fin 2 → Fin 2 := fun x y =>" in code
    assert "if x = 0 then" in code
    assert "if y = 0 then 0 else 0" in code
    assert "if y = 0 then 1 else 1" in code
    assert "⟨Fin 2, ⟨op⟩, by decide⟩" in code


def test_finite_magma_counterexample_certificate_rejects_invalid_tables():
    with pytest.raises(ValueError, match="square"):
        finite_magma_counterexample_certificate(1, 2, [[0, 1]])

    with pytest.raises(ValueError, match="entry"):
        finite_magma_counterexample_certificate(1, 2, [[0, 2], [1, 0]])


def test_pure_finite_magma_counterexample_certificate_inlines_everything():
    code = pure_finite_magma_counterexample_certificate(
        lhs_id=649,
        lhs_equation="x = x * (y * ((z * x) * x))",
        rhs_id=2608,
        rhs_equation="x = (y * ((z * z) * y)) * w",
        table=[[0, 0], [1, 1]],
        theorem_name="stage2_negative_cert_normal_0003",
    )

    assert "import " not in code
    assert "class Magma" in code
    assert 'infixl:70 " ◇ " => Magma.op' in code
    assert "abbrev Equation649" in code
    assert "∀ x y z : G, x = x ◇ (y ◇ ((z ◇ x) ◇ x))" in code
    assert "abbrev Equation2608" in code
    assert "∀ x y z w : G, x = (y ◇ ((z ◇ z) ◇ y)) ◇ w" in code
    assert "theorem stage2_negative_cert_normal_0003" in code
    assert "let op : Fin 2 -> Fin 2 -> Fin 2 := fun x y =>" in code
    assert "⟨Fin 2, ⟨op⟩, by decide⟩" in code


def test_module_name_from_lean_filename_converts_etp_path():
    assert (
        module_name_from_lean_filename(
            "././equational_theories/Generated/SimpleRewrites/theorems/Rewrite_uw.lean"
        )
        == "equational_theories.Generated.SimpleRewrites.theorems.Rewrite_uw"
    )


def test_positive_path_certificate_composes_theorem_edges():
    code = positive_path_certificate(
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
    )

    assert "import equational_theories.Subgraph" in code
    assert "(h : Equation2 G) : Equation8 G" in code
    assert "Subgraph.Equation3_implies_Equation8 G" in code
    assert "(Subgraph.Equation2_implies_Equation3 G h)" in code


def test_generate_countermodel_certificates_script_help_runs_when_invoked_by_path():
    root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [sys.executable, "scripts/counterexample/generate_countermodel_certificates.py", "--help"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
