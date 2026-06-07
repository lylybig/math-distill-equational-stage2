import hashlib
import json
import os
import select
import subprocess
import sys
from pathlib import Path


SUBMISSION_DIR = Path("submissions/solo_official")
SOLVER_PATH = SUBMISSION_DIR / "solver.py"
SOLVER_CURRENT_PATH = Path("solvers/solo_official/current/solver.py")
BASELINE_VERSION_PATH = Path(
    "solvers/solo_official/versions/2026-05-07/v1/solver.py"
)
FIN7_DRAFT_PATH = Path("solvers/solo_official/drafts/2026-05-07/d1/solver.py")
FALSE1682_DRAFT_PATH = Path("solvers/solo_official/drafts/2026-05-07/d2/solver.py")
TRUE_PLACEHOLDER_REPAIR_DRAFT_PATH = Path(
    "solvers/solo_official/drafts/2026-05-08/d3/solver.py"
)
GENERAL_TRUE_TEMPLATE_REPAIR_DRAFT_PATH = Path(
    "solvers/solo_official/drafts/2026-05-08/d4/solver.py"
)
LLM_TWO_ROUND_DRAFT_PATH = Path(
    "solvers/solo_official/drafts/2026-05-08/d5/solver.py"
)
GRIND_TRUE_FALLBACK_DRAFT_PATH = Path(
    "solvers/solo_official/drafts/2026-05-08/d6/solver.py"
)
VAMPIRE_SUPERPOSE_COMPILER_DRAFT_PATH = Path(
    "solvers/solo_official/drafts/2026-05-08/d7/solver.py"
)
VAMPIRE_COLLAPSE_COMPILER_DRAFT_PATH = Path(
    "solvers/solo_official/drafts/2026-05-08/d8/solver.py"
)
NO_LLM_DRAFT_PATH = Path("solvers/solo_official/drafts/2026-05-08/d9/solver.py")
IDEMPOTENT_EXPANSION_COMPILER_DRAFT_PATH = Path(
    "solvers/solo_official/drafts/2026-05-08/d10/solver.py"
)
MAGMAEGG_SINGLETON_COMPILER_DRAFT_PATH = Path(
    "solvers/solo_official/drafts/2026-05-08/d11/solver.py"
)
MAGMAEGG_SINGLETON_EXPANDED_DRAFT_PATH = Path(
    "solvers/solo_official/drafts/2026-05-09/d1/solver.py"
)
EQ41_PRODUCT_COMPILER_DRAFT_PATH = Path(
    "solvers/solo_official/drafts/2026-05-09/d2/solver.py"
)
EQ2118_SINGLETON_COMPILER_DRAFT_PATH = Path(
    "solvers/solo_official/drafts/2026-05-11/d1/solver.py"
)
EQ2921_SINGLETON_COMPILER_DRAFT_PATH = Path(
    "solvers/solo_official/drafts/2026-05-11/d2/solver.py"
)
HINSTANTIATED_GRIND_DRAFT_PATH = Path(
    "solvers/solo_official/drafts/2026-05-11/d3/solver.py"
)
EQ1087_SINGLETON_COMPILER_DRAFT_PATH = Path(
    "solvers/solo_official/drafts/2026-05-12/d4/solver.py"
)
COMPACT_ANCHOR_HINST_DRAFT_PATH = Path(
    "solvers/solo_official/drafts/2026-05-12/d5/solver.py"
)
ETP_EQ2_SINGLETON_DISTILLED_DRAFT_PATH = Path(
    "solvers/solo_official/drafts/2026-05-20/d1/solver.py"
)
FALSE_PREDICATE_TOP80_MIN25K_DRAFT_PATH = Path(
    "solvers/solo_official/drafts/2026-05-21/d1/solver.py"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_first_solver_message(
    problem: dict, solver_path: Path = SOLVER_PATH
) -> tuple[subprocess.Popen, dict]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.Popen(
        [sys.executable, str(solver_path)],
        text=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    assert proc.stdin is not None
    assert proc.stdout is not None
    proc.stdin.write(json.dumps({"problem": problem, "budget": {"timeout_seconds": 60}}) + "\n")
    proc.stdin.flush()
    line = proc.stdout.readline()
    assert line, (proc.stderr.read() if proc.stderr is not None else "")
    return proc, json.loads(line)


def _read_solver_message(proc: subprocess.Popen, *, timeout: float = 5.0) -> dict | None:
    assert proc.stdout is not None
    ready, _, _ = select.select([proc.stdout], [], [], timeout)
    if not ready:
        return None
    line = proc.stdout.readline()
    if not line:
        return None
    return json.loads(line)


def _write_solver_response(proc: subprocess.Popen, response: dict) -> None:
    assert proc.stdin is not None
    proc.stdin.write(json.dumps(response) + "\n")
    proc.stdin.flush()


def _accept_and_wait(proc: subprocess.Popen) -> None:
    _write_solver_response(proc, {"status": "accepted"})
    assert proc.wait(timeout=5) == 0


def test_official_solo_submission_is_single_solver_file_under_limit():
    files = sorted(path.relative_to(SUBMISSION_DIR) for path in SUBMISSION_DIR.iterdir())

    assert files == [Path("solver.py")]
    assert SOLVER_PATH.stat().st_size < 500_000


def test_current_solver_manifest_records_export_path_separately():
    assert SOLVER_CURRENT_PATH.is_file()
    current_manifest = json.loads(
        Path("solvers/solo_official/current/manifest.json").read_text(encoding="utf-8")
    )

    assert current_manifest["official_export_path"] == str(SOLVER_PATH)
    assert current_manifest["solver_path"] == str(SOLVER_CURRENT_PATH)
    assert current_manifest["solver_sha256"] == _sha256(SOLVER_CURRENT_PATH)
    source_version = current_manifest["source_version"]
    source_solver = Path("solvers/solo_official/versions") / source_version / "solver.py"
    assert source_solver.is_file()
    assert current_manifest["solver_sha256"] == _sha256(source_solver)


def test_solver_version_store_records_baseline_and_fin7_candidate():
    assert BASELINE_VERSION_PATH.is_file()
    assert FIN7_DRAFT_PATH.is_file()

    baseline_source = BASELINE_VERSION_PATH.read_text(encoding="utf-8")
    draft_source = FIN7_DRAFT_PATH.read_text(encoding="utf-8")

    assert "extended_counterexample(eq1_text, eq2_text, max_n=5" in baseline_source
    assert "set_option maxRecDepth" not in baseline_source
    assert "extended_counterexample(eq1_text, eq2_text, max_n=7" in draft_source
    assert "set_option maxRecDepth 1000000" in draft_source


def test_official_solver_is_opnorm_snapshot_with_llm_fallback():
    source = SOLVER_PATH.read_text(encoding="utf-8")

    assert "opnorm — flagship reference mining solver" in source
    assert "PROMPT = " in source
    assert "def call_llm" in source
    assert '{"call": "llm"' in source


def test_solver_emits_true_judge_call_for_identical_equations():
    problem = {
        "id": "identity_smoke",
        "eq1_id": 1,
        "eq2_id": 1,
        "equation1": "x = x",
        "equation2": "x = x",
    }

    proc, message = _read_first_solver_message(problem)
    try:
        assert message["call"] == "judge"
        assert message["verdict"] == "true"
        assert "import JudgeProblem" in message["code"]
        assert "def submission : Goal := by" in message["code"]
        assert "exact h" in message["code"]
        _accept_and_wait(proc)
    finally:
        if proc.poll() is None:
            proc.kill()


def test_solver_emits_singleton_true_judge_call_for_baseline_sample_problem():
    problem = {
        "id": "true_193_191",
        "eq1_id": 193,
        "eq2_id": 191,
        "equation1": "x = (y \u25c7 z) \u25c7 (y \u25c7 w)",
        "equation2": "x = (y \u25c7 z) \u25c7 (y \u25c7 y)",
        "answer": True,
    }

    proc, message = _read_first_solver_message(problem)
    try:
        assert message["call"] == "judge"
        assert message["verdict"] == "true"
        assert "have singleton" in message["code"]
        assert "exact singleton" in message["code"]
        _accept_and_wait(proc)
    finally:
        if proc.poll() is None:
            proc.kill()


def test_d11_solver_emits_magmaegg_singleton_compiler_for_order4_true_failure():
    problem = {
        "id": "true_1116_4141",
        "eq1_id": 1116,
        "eq2_id": 4141,
        "equation1": "x = y ◇ ((y ◇ (x ◇ z)) ◇ y)",
        "equation2": "x ◇ y = ((x ◇ z) ◇ y) ◇ x",
        "answer": True,
    }

    proc, message = _read_first_solver_message(
        problem, solver_path=MAGMAEGG_SINGLETON_COMPILER_DRAFT_PATH
    )
    try:
        assert message["call"] == "judge"
        assert message["verdict"] == "true"
        assert "let T := @Eq.trans" in message["code"]
        assert "have singleton : ∀ (x y : G), x = y := by" in message["code"]
        assert "exact singleton (x ◇ y) (((x ◇ z) ◇ y) ◇ x)" in message["code"]
        assert "equational_theories" not in message["code"]
        _accept_and_wait(proc)
    finally:
        if proc.poll() is None:
            proc.kill()


def test_d12_solver_emits_expanded_magmaegg_singleton_for_dev_main_seed():
    problem = {
        "id": "true_2572_853",
        "eq1_id": 2572,
        "eq2_id": 853,
        "equation1": "x = (y ◇ ((z ◇ x) ◇ y)) ◇ y",
        "equation2": "x = x ◇ ((y ◇ z) ◇ (x ◇ y))",
        "answer": True,
    }

    proc, message = _read_first_solver_message(
        problem, solver_path=MAGMAEGG_SINGLETON_EXPANDED_DRAFT_PATH
    )
    try:
        assert message["call"] == "judge"
        assert message["verdict"] == "true"
        assert "have singleton : ∀ (x y : G), x = y := by" in message["code"]
        assert "exact T" in message["code"]
        assert "exact singleton (x) (x ◇ ((y ◇ z) ◇ (x ◇ y)))" in message["code"]
        assert "equational_theories" not in message["code"]
        _accept_and_wait(proc)
    finally:
        if proc.poll() is None:
            proc.kill()


def test_d13_solver_emits_eq41_product_compiler_for_dev_main_tail_failure():
    problem = {
        "id": "true_4163_4310",
        "eq1_id": 4163,
        "eq2_id": 4310,
        "equation1": "x ◇ y = ((y ◇ x) ◇ z) ◇ w",
        "equation2": "x ◇ (x ◇ y) = z ◇ (w ◇ y)",
        "answer": True,
    }

    proc, first = _read_first_solver_message(
        problem, solver_path=EQ41_PRODUCT_COMPILER_DRAFT_PATH
    )
    try:
        message = first
        while message is not None:
            if message["call"] == "judge":
                assert message["verdict"] == "true"
                code = message["code"]
                if "have eq41 : ∀ (x y z : G), x ◇ x = y ◇ z := by" in code:
                    assert "have allprod : ∀ (a b c d : G), a ◇ b = c ◇ d := by" in code
                    assert "exact allprod (x) ((x ◇ y)) (z) ((w ◇ y))" in code
                    _accept_and_wait(proc)
                    return
                _write_solver_response(
                    proc,
                    {"status": "incorrect", "message": "forced test rejection"},
                )
            elif message["call"] == "llm":
                raise AssertionError("Eq41 product compiler was not emitted before LLM")
            else:
                raise AssertionError(message)
            message = _read_solver_message(proc, timeout=5.0)

        raise AssertionError("solver exited before emitting Eq41 product compiler")
    finally:
        if proc.poll() is None:
            proc.kill()


def test_d14_solver_emits_eq41_product_compiler_for_dev_fast_eq3992_failure():
    problem = {
        "id": "true_3992_4406",
        "eq1_id": 3992,
        "eq2_id": 4406,
        "equation1": "x ◇ y = (z ◇ (x ◇ y)) ◇ x",
        "equation2": "x ◇ (x ◇ y) = (y ◇ x) ◇ y",
        "answer": True,
    }

    proc, first = _read_first_solver_message(
        problem, solver_path=EQ41_PRODUCT_COMPILER_DRAFT_PATH
    )
    try:
        message = first
        while message is not None:
            if message["call"] == "judge":
                assert message["verdict"] == "true"
                code = message["code"]
                if "have eq41 : ∀ (x y z : G), x ◇ x = y ◇ z := by" in code:
                    assert "have allprod : ∀ (a b c d : G), a ◇ b = c ◇ d := by" in code
                    assert "exact allprod (x) ((x ◇ y)) ((y ◇ x)) (y)" in code
                    _accept_and_wait(proc)
                    return
                _write_solver_response(
                    proc,
                    {"status": "incorrect", "message": "forced test rejection"},
                )
            elif message["call"] == "llm":
                raise AssertionError("Eq41 product compiler was not emitted before LLM")
            else:
                raise AssertionError(message)
            message = _read_solver_message(proc, timeout=5.0)

        raise AssertionError("solver exited before emitting Eq41 product compiler")
    finally:
        if proc.poll() is None:
            proc.kill()


def test_d15_solver_emits_eq2118_singleton_compiler_for_dev_fast_family():
    problem = {
        "id": "true_2118_13",
        "eq1_id": 2118,
        "eq2_id": 13,
        "equation1": "x = ((y ◇ x) ◇ z) ◇ (z ◇ w)",
        "equation2": "x = y ◇ (x ◇ x)",
        "answer": True,
    }

    proc, first = _read_first_solver_message(
        problem, solver_path=EQ2118_SINGLETON_COMPILER_DRAFT_PATH
    )
    try:
        message = first
        while message is not None:
            if message["call"] == "judge":
                assert message["verdict"] == "true"
                code = message["code"]
                if "have singleton : ∀ (x y : G), x = y := by" in code:
                    assert (
                        "let h2117 : ∀ (x y z : G), x = ((y ◇ x) ◇ z) ◇ (z ◇ z) := "
                        "fun x y z => h x y z z"
                    ) in code
                    assert "exact singleton (x) (y ◇ (x ◇ x))" in code
                    assert "equational_theories" not in code
                    _accept_and_wait(proc)
                    return
                _write_solver_response(
                    proc,
                    {"status": "incorrect", "message": "forced test rejection"},
                )
            elif message["call"] == "llm":
                raise AssertionError(
                    "Eq2118 singleton compiler was not emitted before LLM"
                )
            else:
                raise AssertionError(message)
            message = _read_solver_message(proc, timeout=5.0)

        raise AssertionError("solver exited before emitting Eq2118 singleton compiler")
    finally:
        if proc.poll() is None:
            proc.kill()


def test_d16_solver_emits_eq2921_singleton_compiler_for_dev_fast_family():
    problem = {
        "id": "true_2921_512",
        "eq1_id": 2921,
        "eq2_id": 512,
        "equation1": "x = ((y ◇ (x ◇ z)) ◇ x) ◇ z",
        "equation2": "x = y ◇ (y ◇ (y ◇ (x ◇ z)))",
        "answer": True,
    }

    proc, first = _read_first_solver_message(
        problem, solver_path=EQ2921_SINGLETON_COMPILER_DRAFT_PATH
    )
    try:
        message = first
        while message is not None:
            if message["call"] == "judge":
                assert message["verdict"] == "true"
                code = message["code"]
                if "have singleton : ∀ (x y : G), x = y := by" in code:
                    assert "have eq12 (X1 X2 X3 : G)" in code
                    assert "have eq15 (X0 X2 : G)" in code
                    assert "congrArg" in code
                    assert "exact singleton (x) (y ◇ (y ◇ (y ◇ (x ◇ z))))" in code
                    assert "equational_theories" not in code
                    _accept_and_wait(proc)
                    return
                _write_solver_response(
                    proc,
                    {"status": "incorrect", "message": "forced test rejection"},
                )
            elif message["call"] == "llm":
                raise AssertionError(
                    "Eq2921 singleton compiler was not emitted before LLM"
                )
            else:
                raise AssertionError(message)
            message = _read_solver_message(proc, timeout=5.0)

        raise AssertionError("solver exited before emitting Eq2921 singleton compiler")
    finally:
        if proc.poll() is None:
            proc.kill()


def test_d17_solver_emits_hinstantiated_grind_for_proofbank_true_samples():
    cases = [
        (
            {
                "id": "true_1108_991",
                "eq1_id": 1108,
                "eq2_id": 991,
                "equation1": "x = y ◇ ((x ◇ (z ◇ w)) ◇ u)",
                "equation2": "x = y ◇ ((z ◇ z) ◇ (w ◇ z))",
                "answer": True,
            },
            "x = y ◇ ((x ◇ (z ◇ w)) ◇ z) := h x y z w z",
        ),
        (
            {
                "id": "true_1717_1879",
                "eq1_id": 1717,
                "eq2_id": 1879,
                "equation1": "x = (y ◇ x) ◇ ((z ◇ w) ◇ u)",
                "equation2": "x = (x ◇ (y ◇ z)) ◇ (w ◇ x)",
                "answer": True,
            },
            "x = (x ◇ x) ◇ ((y ◇ z) ◇ w) := h x x y z w",
        ),
        (
            {
                "id": "true_2123_4481",
                "eq1_id": 2123,
                "eq2_id": 4481,
                "equation1": "x = ((y ◇ x) ◇ z) ◇ (w ◇ u)",
                "equation2": "x ◇ (y ◇ y) = (y ◇ x) ◇ z",
                "answer": True,
            },
            "x = ((y ◇ x) ◇ z) ◇ (y ◇ y) := h x y z y y",
        ),
        (
            {
                "id": "true_2216_2785",
                "eq1_id": 2216,
                "eq2_id": 2785,
                "equation1": "x = ((y ◇ z) ◇ w) ◇ (x ◇ u)",
                "equation2": "x = ((y ◇ z) ◇ (x ◇ w)) ◇ w",
                "answer": True,
            },
            "x = ((y ◇ z) ◇ (x ◇ w)) ◇ (x ◇ w) := h x y z (x ◇ w) w",
        ),
        (
            {
                "id": "true_2419_1450",
                "eq1_id": 2419,
                "eq2_id": 1450,
                "equation1": "x = (y ◇ (z ◇ (w ◇ x))) ◇ u",
                "equation2": "x = (x ◇ y) ◇ (x ◇ (z ◇ w))",
                "answer": True,
            },
            "x = (x ◇ (x ◇ (x ◇ x))) ◇ (x ◇ (z ◇ w)) := h x x x x (x ◇ (z ◇ w))",
        ),
        (
            {
                "id": "true_2529_2783",
                "eq1_id": 2529,
                "eq2_id": 2783,
                "equation1": "x = (y ◇ ((x ◇ z) ◇ w)) ◇ u",
                "equation2": "x = ((y ◇ z) ◇ (x ◇ w)) ◇ y",
                "answer": True,
            },
            "x = (y ◇ ((x ◇ z) ◇ w)) ◇ y := h x y z w y",
        ),
    ]

    for problem, expected_hx in cases:
        proc, first = _read_first_solver_message(
            problem, solver_path=HINSTANTIATED_GRIND_DRAFT_PATH
        )
        try:
            message = first
            while message is not None:
                if message["call"] == "judge":
                    assert message["verdict"] == "true"
                    code = message["code"]
                    if expected_hx in code:
                        assert "\n  grind\n" in code
                        assert "equational_theories" not in code
                        _accept_and_wait(proc)
                        break
                    _write_solver_response(
                        proc,
                        {"status": "incorrect", "message": "forced test rejection"},
                    )
                elif message["call"] == "llm":
                    raise AssertionError(
                        f"h-instantiated grind was not emitted before LLM for {problem['id']}"
                    )
                else:
                    raise AssertionError(message)
                message = _read_solver_message(proc, timeout=5.0)
            else:
                raise AssertionError(
                    f"solver exited before emitting h-instantiated grind for {problem['id']}"
                )
        finally:
            if proc.poll() is None:
                proc.kill()


def test_d18_solver_emits_eq1087_singleton_compiler_for_proofbank_failures():
    cases = [
        {
            "id": "true_1087_996",
            "eq1_id": 1087,
            "eq2_id": 996,
            "equation1": "x = y ◇ ((x ◇ (y ◇ y)) ◇ z)",
            "equation2": "x = y ◇ ((z ◇ w) ◇ (x ◇ z))",
            "answer": True,
        },
        {
            "id": "true_1087_2170",
            "eq1_id": 1087,
            "eq2_id": 2170,
            "equation1": "x = y ◇ ((x ◇ (y ◇ y)) ◇ z)",
            "equation2": "x = ((y ◇ z) ◇ x) ◇ (z ◇ y)",
            "answer": True,
        },
        {
            "id": "true_1087_1010",
            "eq1_id": 1087,
            "eq2_id": 1010,
            "equation1": "x = y ◇ ((x ◇ (y ◇ y)) ◇ z)",
            "equation2": "x = y ◇ ((z ◇ w) ◇ (w ◇ y))",
            "answer": True,
        },
    ]

    for problem in cases:
        proc, first = _read_first_solver_message(
            problem, solver_path=EQ1087_SINGLETON_COMPILER_DRAFT_PATH
        )
        try:
            message = first
            while message is not None:
                if message["call"] == "judge":
                    assert message["verdict"] == "true"
                    code = message["code"]
                    if (
                        "have eq12 : ∀ (X0 X1 X2 : G), X1 ◇ X2 = X0" in code
                        and "have singleton : ∀ (a b : G), a = b" in code
                    ):
                        assert "exact singleton (" in code
                        assert "equational_theories" not in code
                        _accept_and_wait(proc)
                        break
                    _write_solver_response(
                        proc,
                        {"status": "incorrect", "message": "forced test rejection"},
                    )
                elif message["call"] == "llm":
                    raise AssertionError(
                        f"Eq1087 singleton compiler was not emitted before LLM for {problem['id']}"
                    )
                else:
                    raise AssertionError(message)
                message = _read_solver_message(proc, timeout=5.0)
            else:
                raise AssertionError(
                    f"solver exited before emitting Eq1087 singleton compiler for {problem['id']}"
                )
        finally:
            if proc.poll() is None:
                proc.kill()


def test_d19_solver_emits_compact_anchor_hinst_grind_for_eq1356_proofbank_failure():
    problem = {
        "id": "true_1356_762",
        "eq1_id": 1356,
        "eq2_id": 762,
        "equation1": "x = y ◇ (((z ◇ x) ◇ y) ◇ w)",
        "equation2": "x = y ◇ (z ◇ ((y ◇ y) ◇ y))",
        "answer": True,
    }

    proc, first = _read_first_solver_message(
        problem, solver_path=COMPACT_ANCHOR_HINST_DRAFT_PATH
    )
    try:
        message = first
        while message is not None:
            if message["call"] == "judge":
                assert message["verdict"] == "true"
                code = message["code"]
                if (
                    "have ha0_x : x = x ◇ (((x ◇ x) ◇ x) ◇ x) := h x x x x"
                    in code
                    and "have ha0_y : y = x ◇ (((x ◇ y) ◇ x) ◇ x) := h y x x x"
                    in code
                ):
                    assert "grind" in code
                    assert "equational_theories" not in code
                    _accept_and_wait(proc)
                    break
                _write_solver_response(
                    proc,
                    {"status": "incorrect", "message": "forced test rejection"},
                )
            elif message["call"] == "llm":
                raise AssertionError(
                    "compact anchor h-instantiated grind was not emitted before LLM"
                )
            else:
                raise AssertionError(message)
            message = _read_solver_message(proc, timeout=5.0)
        else:
            raise AssertionError("solver exited before compact anchor hinst grind")
    finally:
        if proc.poll() is None:
            proc.kill()


def test_d20_solver_emits_etp_eq2_singleton_distilled_compiler_for_order5_seed():
    problem = {
        "id": "true_19089_distilled_target",
        "eq1_id": 19089,
        "eq2_id": 900001,
        "equation1": "x = (y ◇ y) ◇ ((x ◇ x) ◇ (z ◇ z))",
        "equation2": "x ◇ z = y",
        "answer": True,
    }

    proc, first = _read_first_solver_message(
        problem, solver_path=ETP_EQ2_SINGLETON_DISTILLED_DRAFT_PATH
    )
    try:
        message = first
        while message is not None:
            if message["call"] == "judge":
                assert message["verdict"] == "true"
                code = message["code"]
                if "have etp_singleton : ∀ (x y : G), x = y := by" in code:
                    assert "have eq16 (X0 X3 : G) : X0 = X3 := by" in code
                    assert "exact etp_singleton (x ◇ z) (y)" in code
                    assert "equational_theories" not in code
                    _accept_and_wait(proc)
                    return
                _write_solver_response(
                    proc,
                    {"status": "incorrect", "message": "forced test rejection"},
                )
            elif message["call"] == "llm":
                raise AssertionError(
                    "ETP Eq2 singleton distilled compiler was not emitted before LLM"
                )
            else:
                raise AssertionError(message)
            message = _read_solver_message(proc, timeout=5.0)

        raise AssertionError("solver exited before emitting ETP Eq2 singleton compiler")
    finally:
        if proc.poll() is None:
            proc.kill()


def test_d21_solver_emits_false_predicate_bank_certificate_for_top80_min25k_pair():
    problem = {
        "id": "beam_batch01_new_order4_source_to_order5_target_9_45281",
        "eq1_id": 9,
        "eq2_id": 45281,
        "equation1": "x = x * (x * y)",
        "equation2": "x * y = x * (((y * x) * y) * y)",
        "answer": False,
    }

    proc, message = _read_first_solver_message(
        problem, solver_path=FALSE_PREDICATE_TOP80_MIN25K_DRAFT_PATH
    )
    try:
        assert message["call"] == "judge"
        assert message["verdict"] == "false"
        assert "finOpTable" in message["code"]
        assert "[[0, 0, 0, 1], [1, 1, 1, 0], [3, 3, 2, 2], [2, 2, 3, 3]]" in message[
            "code"
        ]
        assert "decideFin!" in message["code"]
        _accept_and_wait(proc)
    finally:
        if proc.poll() is None:
            proc.kill()


def test_solver_emits_false_judge_call_for_simple_nontrivial_counterexample():
    problem = {
        "id": "false_smoke",
        "eq1_id": 1,
        "eq2_id": 2,
        "equation1": "x = x",
        "equation2": "x = y",
    }

    proc, message = _read_first_solver_message(problem)
    try:
        assert message["call"] == "judge"
        assert message["verdict"] == "false"
        assert "import JudgeFinOp.MemoFinOp" in message["code"]
        assert "decideFin!" in message["code"]
        _accept_and_wait(proc)
    finally:
        if proc.poll() is None:
            proc.kill()


def test_solver_uses_lean4_congr_arg_name_for_iterated_single_var_goal():
    problem = {
        "id": "true_359_4065",
        "eq1_id": 359,
        "eq2_id": 4065,
        "equation1": "x ◇ x = (x ◇ x) ◇ x",
        "equation2": "x ◇ x = ((x ◇ x) ◇ x) ◇ x",
        "answer": True,
    }

    proc, message = _read_first_solver_message(problem)
    try:
        assert message["call"] == "judge"
        assert message["verdict"] == "true"
        assert "congrArg" in message["code"]
        assert "congr_arg" not in message["code"]
        _accept_and_wait(proc)
    finally:
        if proc.poll() is None:
            proc.kill()


def test_solver_uses_single_llm_round_when_model_repeats_duplicate_proof():
    problem = {
        "id": "true_359_4065",
        "eq1_id": 359,
        "eq2_id": 4065,
        "equation1": "x ◇ x = (x ◇ x) ◇ x",
        "equation2": "x ◇ x = ((x ◇ x) ◇ x) ◇ x",
        "answer": True,
    }
    repeated_llm_answer = {
        "response": json.dumps({
            "verdict": "true",
            "proof": "intro x\ncalc\n  x ◇ x = (x ◇ x) ◇ x := h x\n  _ = ((x ◇ x) ◇ x) ◇ x := h (x ◇ x)",
        })
    }

    proc, first = _read_first_solver_message(problem)
    llm_calls = 0
    try:
        message = first
        while message is not None:
            if message["call"] == "judge":
                _write_solver_response(proc, {"status": "incorrect", "message": "forced test rejection"})
            elif message["call"] == "llm":
                llm_calls += 1
                assert llm_calls <= 1
                _write_solver_response(proc, repeated_llm_answer)
            else:
                raise AssertionError(message)
            message = _read_solver_message(proc, timeout=5.0)

        assert proc.wait(timeout=5) == 0
        assert llm_calls == 1
    finally:
        if proc.poll() is None:
            proc.kill()


def test_d2_solver_emits_fin5_counterexample_for_false_1682_411():
    problem = {
        "id": "false_1682_411",
        "eq1_id": 1682,
        "eq2_id": 411,
        "equation1": "x = (y ◇ x) ◇ ((x ◇ x) ◇ y)",
        "equation2": "x = x ◇ (x ◇ (x ◇ (x ◇ x)))",
        "answer": False,
    }

    proc, message = _read_first_solver_message(problem, FALSE1682_DRAFT_PATH)
    try:
        assert message["call"] == "judge"
        assert message["verdict"] == "false"
        assert "Fin 5" in message["code"]
        assert "[1, 2, 4, 0, 3]" in message["code"]
        _accept_and_wait(proc)
    finally:
        if proc.poll() is None:
            proc.kill()


def test_d3_true_2942_candidates_do_not_emit_placeholder_lemma_types():
    problem = {
        "id": "true_2942_5",
        "eq1_id": 2942,
        "eq2_id": 5,
        "equation1": "x = ((y ◇ (y ◇ x)) ◇ z) ◇ x",
        "equation2": "x = y ◇ x",
        "answer": True,
    }

    proc, first = _read_first_solver_message(problem, TRUE_PLACEHOLDER_REPAIR_DRAFT_PATH)
    try:
        message = first
        while message is not None:
            if message["call"] == "judge":
                assert "), _ := by" not in message["code"]
                _write_solver_response(proc, {"status": "incorrect", "message": "forced test rejection"})
            elif message["call"] == "llm":
                _write_solver_response(proc, {"response": json.dumps({"verdict": "true", "proof": "intro x y\nexact h x y y"})})
            else:
                raise AssertionError(message)
            message = _read_solver_message(proc, timeout=5.0)
    finally:
        if proc.poll() is None:
            proc.kill()


def test_d4_true_130_restores_structural_congrarg_template_without_placeholder():
    problem = {
        "id": "true_130_1759",
        "eq1_id": 130,
        "eq2_id": 1759,
        "equation1": "x = y ◇ ((y ◇ z) ◇ x)",
        "equation2": "x = (y ◇ z) ◇ ((x ◇ y) ◇ x)",
        "answer": True,
    }
    expected_h_inst = "h x ((y ◇ z)) ((((y ◇ z) ◇ x) ◇ (x ◇ y)))"
    expected_lift = (
        "congrArg ((y ◇ z) ◇ ·) "
        "(congrArg (· ◇ x) ((h ((x ◇ y)) (y ◇ z) x).symm))"
    )

    proc, first = _read_first_solver_message(
        problem, GENERAL_TRUE_TEMPLATE_REPAIR_DRAFT_PATH
    )
    try:
        message = first
        while message is not None:
            if message["call"] == "judge":
                assert ": _ := by" not in message["code"]
                if expected_h_inst in message["code"] and expected_lift in message["code"]:
                    _accept_and_wait(proc)
                    return
                _write_solver_response(
                    proc,
                    {"status": "incorrect", "message": "forced test rejection"},
                )
            elif message["call"] == "llm":
                raise AssertionError("structural true proof template was not emitted before LLM")
            else:
                raise AssertionError(message)
            message = _read_solver_message(proc, timeout=5.0)

        raise AssertionError("solver exited before emitting structural true proof template")
    finally:
        if proc.poll() is None:
            proc.kill()


def test_d5_allows_second_llm_round_after_unparseable_first_response():
    problem = {
        "id": "true_193_191",
        "eq1_id": 193,
        "eq2_id": 191,
        "equation1": "x = (y ◇ z) ◇ (y ◇ w)",
        "equation2": "x = (y ◇ z) ◇ (y ◇ y)",
        "answer": True,
    }

    proc, first = _read_first_solver_message(problem, LLM_TWO_ROUND_DRAFT_PATH)
    llm_calls = 0
    try:
        message = first
        while message is not None:
            if message["call"] == "judge":
                assert ": _ := by" not in message["code"]
                _write_solver_response(
                    proc,
                    {"status": "incorrect", "message": "forced test rejection"},
                )
            elif message["call"] == "llm":
                llm_calls += 1
                assert llm_calls <= 2
                _write_solver_response(proc, {"response": "not json"})
            else:
                raise AssertionError(message)
            message = _read_solver_message(proc, timeout=20.0)

        assert proc.wait(timeout=5) == 0
        assert llm_calls == 2
    finally:
        if proc.poll() is None:
            proc.kill()


def test_d6_true_2074_uses_deterministic_grind_before_llm():
    problem = {
        "id": "true_2074_2082",
        "eq1_id": 2074,
        "eq2_id": 2082,
        "equation1": "x = ((x ◇ y) ◇ z) ◇ (y ◇ x)",
        "equation2": "x = ((x ◇ y) ◇ z) ◇ (w ◇ x)",
        "answer": True,
    }

    proc, first = _read_first_solver_message(problem, GRIND_TRUE_FALLBACK_DRAFT_PATH)
    try:
        message = first
        while message is not None:
            if message["call"] == "judge":
                assert message["verdict"] == "true"
                if "\n  grind\n" in message["code"]:
                    _accept_and_wait(proc)
                    return
                _write_solver_response(
                    proc,
                    {"status": "incorrect", "message": "forced test rejection"},
                )
            elif message["call"] == "llm":
                raise AssertionError("grind true proof was not emitted before LLM")
            else:
                raise AssertionError(message)
            message = _read_solver_message(proc, timeout=5.0)

        raise AssertionError("solver exited before emitting grind true proof")
    finally:
        if proc.poll() is None:
            proc.kill()


def test_d7_true_3108_compiles_superpose_projection_before_llm():
    problem = {
        "id": "true_3108_4642",
        "eq1_id": 3108,
        "eq2_id": 4642,
        "equation1": "x = (((y ◇ x) ◇ x) ◇ z) ◇ x",
        "equation2": "(x ◇ y) ◇ x = (z ◇ x) ◇ x",
        "answer": True,
    }

    proc, first = _read_first_solver_message(
        problem, VAMPIRE_SUPERPOSE_COMPILER_DRAFT_PATH
    )
    try:
        message = first
        while message is not None:
            if message["call"] == "judge":
                assert message["verdict"] == "true"
                code = message["code"]
                if "have e12" in code and "have e24" in code:
                    assert "congrArg" in code
                    assert "calc" in code
                    _accept_and_wait(proc)
                    return
                _write_solver_response(
                    proc,
                    {"status": "incorrect", "message": "forced test rejection"},
                )
            elif message["call"] == "llm":
                raise AssertionError(
                    "compiled superpose proof was not emitted before LLM"
                )
            else:
                raise AssertionError(message)
            message = _read_solver_message(proc, timeout=5.0)

        raise AssertionError("solver exited before emitting compiled superpose proof")
    finally:
        if proc.poll() is None:
            proc.kill()


def test_d7_true_674_compiles_left_absorption_before_llm():
    problem = {
        "id": "true_674_668",
        "eq1_id": 674,
        "eq2_id": 668,
        "equation1": "x = y ◇ (x ◇ ((x ◇ z) ◇ z))",
        "equation2": "x = y ◇ (x ◇ ((x ◇ x) ◇ z))",
        "answer": True,
    }

    proc, first = _read_first_solver_message(
        problem, VAMPIRE_SUPERPOSE_COMPILER_DRAFT_PATH
    )
    try:
        message = first
        while message is not None:
            if message["call"] == "judge":
                assert message["verdict"] == "true"
                code = message["code"]
                if "have e13" in code and "let t : G" in code:
                    assert "congrArg" in code
                    assert "calc" in code
                    _accept_and_wait(proc)
                    return
                _write_solver_response(
                    proc,
                    {"status": "incorrect", "message": "forced test rejection"},
                )
            elif message["call"] == "llm":
                raise AssertionError(
                    "compiled left absorption proof was not emitted before LLM"
                )
            else:
                raise AssertionError(message)
            message = _read_solver_message(proc, timeout=5.0)

        raise AssertionError("solver exited before emitting left absorption proof")
    finally:
        if proc.poll() is None:
            proc.kill()


def test_d8_true_689_compiles_collapse_before_llm():
    problem = {
        "id": "true_689_1350",
        "eq1_id": 689,
        "eq2_id": 1350,
        "equation1": "x = y ◇ (x ◇ ((z ◇ x) ◇ w))",
        "equation2": "x = y ◇ (((z ◇ x) ◇ x) ◇ y)",
        "answer": True,
    }

    proc, first = _read_first_solver_message(
        problem, VAMPIRE_COLLAPSE_COMPILER_DRAFT_PATH
    )
    try:
        message = first
        while message is not None:
            if message["call"] == "judge":
                assert message["verdict"] == "true"
                code = message["code"]
                if "have e12" in code and "have e15" in code and "have e20" in code:
                    assert "congrArg" in code
                    assert "exact e20" in code
                    _accept_and_wait(proc)
                    return
                _write_solver_response(
                    proc,
                    {"status": "incorrect", "message": "forced test rejection"},
                )
            elif message["call"] == "llm":
                raise AssertionError(
                    "compiled collapse proof was not emitted before LLM"
                )
            else:
                raise AssertionError(message)
            message = _read_solver_message(proc, timeout=5.0)

        raise AssertionError("solver exited before emitting collapse proof")
    finally:
        if proc.poll() is None:
            proc.kill()


def test_d9_no_llm_exits_without_llm_after_rejected_true_attempt():
    problem = {
        "id": "true_359_4065",
        "eq1_id": 359,
        "eq2_id": 4065,
        "equation1": "x ◇ x = (x ◇ x) ◇ x",
        "equation2": "x ◇ x = ((x ◇ x) ◇ x) ◇ x",
        "answer": True,
    }

    proc, first = _read_first_solver_message(problem, NO_LLM_DRAFT_PATH)
    judge_calls = 0
    try:
        message = first
        while message is not None:
            if message["call"] == "judge":
                judge_calls += 1
                _write_solver_response(
                    proc,
                    {"status": "incorrect", "message": "forced test rejection"},
                )
            elif message["call"] == "llm":
                raise AssertionError("no-LLM draft emitted an LLM request")
            else:
                raise AssertionError(message)
            message = _read_solver_message(proc, timeout=5.0)

        assert proc.wait(timeout=5) == 0
        assert judge_calls > 0
    finally:
        if proc.poll() is None:
            proc.kill()


def test_d10_true_428_compiles_idempotent_expansion_before_llm():
    problem = {
        "id": "true_428_3725",
        "eq1_id": 428,
        "eq2_id": 3725,
        "equation1": "x = x ◇ (y ◇ (x ◇ (x ◇ z)))",
        "equation2": "x ◇ y = (x ◇ y) ◇ (y ◇ y)",
        "answer": True,
    }

    proc, first = _read_first_solver_message(
        problem, IDEMPOTENT_EXPANSION_COMPILER_DRAFT_PATH
    )
    try:
        message = first
        while message is not None:
            if message["call"] == "judge":
                assert message["verdict"] == "true"
                code = message["code"]
                if "have eq12" in code and "have eq13" in code:
                    assert "congrArg" in code
                    assert "exact" not in code or "Equation428" not in code
                    _accept_and_wait(proc)
                    return
                _write_solver_response(
                    proc,
                    {"status": "incorrect", "message": "forced test rejection"},
                )
            elif message["call"] == "llm":
                raise AssertionError(
                    "compiled idempotent expansion proof was not emitted before LLM"
                )
            else:
                raise AssertionError(message)
            message = _read_solver_message(proc, timeout=5.0)

        raise AssertionError(
            "solver exited before emitting idempotent expansion proof"
        )
    finally:
        if proc.poll() is None:
            proc.kill()


def test_d10_true_4082_compiles_square_shuffle_before_grind():
    problem = {
        "id": "true_4082_4109",
        "eq1_id": 4082,
        "eq2_id": 4109,
        "equation1": "x ◇ x = ((y ◇ x) ◇ x) ◇ z",
        "equation2": "x ◇ x = ((y ◇ z) ◇ z) ◇ y",
        "answer": True,
    }

    proc, first = _read_first_solver_message(
        problem, IDEMPOTENT_EXPANSION_COMPILER_DRAFT_PATH
    )
    try:
        assert first["call"] == "judge"
        assert first["verdict"] == "true"
        code = first["code"]
        assert "calc x ◇ x" in code or "calc (x ◇ x)" in code
        assert "h z y y" in code
        assert "grind" not in code
        _accept_and_wait(proc)
    finally:
        if proc.poll() is None:
            proc.kill()
