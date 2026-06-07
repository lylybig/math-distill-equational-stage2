import json
from pathlib import Path

from math_distill_stage2.order5_opnorm_hconst_scan import (
    explicit_hits_delta_from_profile,
    scan_sample,
)
from math_distill_stage2.order5_opnorm_match_collapse import (
    iter_hconst_default_sandwich_match_collapse_proof_bodies,
    iter_hconst_match_collapse_proof_bodies,
    iter_hstep_default_sandwich_match_collapse_proof_bodies,
    matches_hconst_default_sandwich_match_collapse,
    matches_hconst_sandwich_match_collapse,
    matches_hconst_match_collapse,
    matches_hstep_default_sandwich_match_collapse,
    render_first_hconst_default_sandwich_match_collapse_certificate,
    render_first_hconst_match_collapse_certificate,
    render_first_hconst_sandwich_match_collapse_certificate,
    render_first_hstep_default_sandwich_match_collapse_certificate,
)
from math_distill_stage2.order5_pair_space import ids_to_pair_index
from math_distill_stage2.order5_strategy_registry import (
    OPNORM_HCONST_DEFAULT_SANDWICH_D13VC4_STRATEGY_KEY,
    OPNORM_HCONST_DEFAULT_SANDWICH_D14VC4_STRATEGY_KEY,
    OPNORM_HCONST_DEFAULT_SANDWICH_D14VC4_TARGETEXT_STRATEGY_KEY,
    OPNORM_HCONST_DEFAULT_SANDWICH_EDGE_EXTENSION_STRATEGY_KEY,
    OPNORM_HCONST_DEFAULT_SANDWICH_FRONTIER_EXTENSION_STRATEGY_KEY,
    OPNORM_HCONST_DEFAULT_SANDWICH_LOWVC_EXTENSION_STRATEGY_KEY,
    OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE2_TOP60_EXTENSION_STRATEGY_KEY,
    OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE3_TOP80_EXTENSION_STRATEGY_KEY,
    OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE4_TOP100_EXTENSION_STRATEGY_KEY,
    OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE5_TOP120_EXTENSION_STRATEGY_KEY,
    OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE6_SAMPLEHIT_TOP20_TAIL_STRATEGY_KEY,
    OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE7_SAMPLEHIT_TOP20_TAIL_STRATEGY_KEY,
    OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE8_D14VC5_FRONTIER_MULTITARGET20_STRATEGY_KEY,
    OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE8_EXACT_TOP10_COMBINED_TAIL_STRATEGY_KEY,
    OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE_TOP40_EXTENSION_STRATEGY_KEY,
    OPNORM_HCONST_DEFAULT_SANDWICH_ROUND30_CUMULATIVE_HCONST_FAMILY_STRATEGY_KEY,
    OPNORM_HCONST_DEFAULT_SANDWICH_TOP16_STRATEGY_KEY,
    OPNORM_HCONST_DEFAULT_SANDWICH_TOPBUCKET_EXTENSION_STRATEGY_KEY,
    OPNORM_HCONST_LMRM_MAINLINE_STRATEGY_KEY,
    OPNORM_HCONST_MATCH_COLLAPSE_STRATEGY_KEY,
    OPNORM_HCONST_PLUS_HSTEP_D14VC4_V17_TAIL_STRATEGY_KEY,
    OPNORM_HCONST_SANDWICH_STRATEGY_KEY,
    OPNORM_HCONST_VARMUL_TOP01_STRATEGY_KEY,
    find_true_strategy_ids_for_pair,
    opnorm_hconst_default_sandwich_true_judge_code,
    opnorm_hconst_match_collapse_true_judge_code,
    opnorm_hconst_plus_hstep_true_judge_code,
    opnorm_hconst_sandwich_true_judge_code,
)
import math_distill_stage2.order5_strategy_registry as strategy_registry_module
from math_distill_stage2.order5_strategy_registry import _encode_ids_bitset


SEED_PROOFS = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_opnorm_top16_true_seed_proofs_20260521.jsonl"
)


def _hconst_seed_rows():
    return [
        json.loads(line)
        for line in SEED_PROOFS.read_text(encoding="utf-8").splitlines()
        if line.strip() and json.loads(line)["proof_cluster"] == "hconst_match_collapse"
    ]


def _plain_nested_seed_rows():
    return [
        json.loads(line)
        for line in SEED_PROOFS.read_text(encoding="utf-8").splitlines()
        if line.strip()
        and json.loads(line)["proof_cluster"]
        in {"nested_congrArg_match_collapse", "plain_calc_match_collapse"}
    ]


def test_opnorm_hconst_compiler_finds_all_top16_hconst_seeds():
    hits = []
    for row in _hconst_seed_rows():
        proofs = list(
            iter_hconst_match_collapse_proof_bodies(
                row["equation1"],
                row["equation2"],
                max_candidates=5,
            )
        )
        if proofs:
            hits.append((row["eq1_id"], row["eq2_id"]))

    assert len(hits) == 5


def test_opnorm_hconst_compiler_emits_safe_certificate_shape():
    code = render_first_hconst_match_collapse_certificate(
        "x * y = z * (((x * w) * u) * w)",
        "x * x = y * ((z * (z * x)) * z)",
    )

    assert code is not None
    assert "def submission : Goal := by" in code
    assert "intro G _ h" in code
    assert "have hconst" in code
    assert "calc x ◇ x" in code
    assert "h x x y x x" in code
    assert "hconst y x x x" in code
    assert "*" not in code
    for token in ("sorry", "admit", "axiom", "unsafe"):
        assert token not in code


def test_opnorm_hconst_fast_matcher_agrees_with_render_for_seed():
    source_equation = "x * y = z * (((x * w) * u) * w)"
    target_equation = "x * x = y * ((z * (z * x)) * z)"

    assert matches_hconst_match_collapse(source_equation, target_equation)
    assert render_first_hconst_match_collapse_certificate(
        source_equation,
        target_equation,
    )


def test_opnorm_hconst_sandwich_compiler_finds_nested_and_plain_seed_subset():
    seed_pairs = [
        (
            "x * y = z * ((y * (w * w)) * u)",
            "x * y = ((z * (x * z)) * x) * x",
        ),
        (
            "x * y = z * (((y * w) * u) * u)",
            "x * x = (y * (z * (z * y))) * y",
        ),
        (
            "x * y = (z * ((w * u) * w)) * x",
            "x * y = y * (y * (z * (z * x)))",
        ),
    ]

    for source_equation, target_equation in seed_pairs:
        assert matches_hconst_sandwich_match_collapse(
            source_equation,
            target_equation,
            max_candidates=2,
        )
        code = render_first_hconst_sandwich_match_collapse_certificate(
            source_equation,
            target_equation,
            max_candidates=2,
        )
        assert code is not None
        assert "def submission : Goal := by" in code
        assert "have hconst" in code
        assert "calc" in code


def test_opnorm_default_sandwich_compilers_find_plain_nested_seeds():
    hits = []
    for row in _plain_nested_seed_rows():
        proofs = list(
            iter_hconst_default_sandwich_match_collapse_proof_bodies(
                row["equation1"],
                row["equation2"],
                max_candidates=2,
            )
        )
        if not proofs:
            proofs = list(
                iter_hstep_default_sandwich_match_collapse_proof_bodies(
                    row["equation1"],
                    row["equation2"],
                    max_candidates=2,
                )
            )
        if proofs:
            hits.append((row["eq1_id"], row["eq2_id"]))

    assert len(hits) == 6


def test_opnorm_hconst_default_sandwich_compiler_emits_safe_certificate_shape():
    row = _plain_nested_seed_rows()[0]

    assert matches_hconst_default_sandwich_match_collapse(
        row["equation1"],
        row["equation2"],
        max_candidates=1,
    )
    code = render_first_hconst_default_sandwich_match_collapse_certificate(
        row["equation1"],
        row["equation2"],
        max_candidates=1,
    )

    assert code is not None
    assert "def submission : Goal := by" in code
    assert "have hconst" in code
    assert "calc" in code
    assert "*" not in code
    for token in ("sorry", "admit", "axiom", "unsafe"):
        assert token not in code


def test_opnorm_hstep_default_sandwich_compiler_emits_safe_certificate_shape():
    rows = {
        (row["eq1_id"], row["eq2_id"]): row for row in _plain_nested_seed_rows()
    }
    row = rows[(50837, 45406)]

    assert matches_hstep_default_sandwich_match_collapse(
        row["equation1"],
        row["equation2"],
        max_candidates=1,
    )
    code = render_first_hstep_default_sandwich_match_collapse_certificate(
        row["equation1"],
        row["equation2"],
        max_candidates=1,
    )

    assert code is not None
    assert "def submission : Goal := by" in code
    assert "calc" in code
    assert "congrArg" in code
    assert "*" not in code
    for token in ("sorry", "admit", "axiom", "unsafe"):
        assert token not in code


def test_opnorm_hconst_plus_hstep_registry_wrapper_uses_hstep_renderer():
    rows = {
        (row["eq1_id"], row["eq2_id"]): row for row in _plain_nested_seed_rows()
    }
    row = rows[(50837, 45406)]

    code = opnorm_hconst_plus_hstep_true_judge_code(
        row["equation1"],
        row["equation2"],
    )

    assert "def submission : Goal := by" in code
    assert "calc" in code
    assert "congrArg" in code
    assert "*" not in code
    for token in ("sorry", "admit", "axiom", "unsafe"):
        assert token not in code


def test_opnorm_hconst_sandwich_compiler_finds_top03_yyleft_core_source():
    source_equation = "x * y = y * (y * (y * (z * w)))"
    target_equation = "x * y = z * (z * (y * (z * z)))"

    assert matches_hconst_sandwich_match_collapse(
        source_equation,
        target_equation,
        max_candidates=2,
    )
    code = render_first_hconst_sandwich_match_collapse_certificate(
        source_equation,
        target_equation,
        max_candidates=2,
    )

    assert code is not None
    assert "have hconst" in code
    assert "(h z (z ◇ (y ◇ (z ◇ z))) x x).symm" in code


def test_opnorm_hconst_registry_strategy_loads_compiler_pair_cache(tmp_path):
    equations_path = tmp_path / "eq_size5.txt"
    equations_path.write_text(
        "\n".join(
            [
                "x * y = z * (((x * w) * u) * w)",
                "x * x = y * ((z * (z * x)) * z)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    pair_index = ids_to_pair_index(1, 2, law_count=2)
    pair_index_cache = tmp_path / "pair_indexes.txt"
    pair_index_cache.write_text(f"{pair_index}\n", encoding="ascii")
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(
            {
                "coverage_profile": "unit-profile-v6.json",
                "controller_merge_review": "unit-controller-review.json",
                "delta_against_current_profile_v6": {
                    "union_increment": 1,
                    "conflict_increment": 0,
                },
                "remote_smoke_accepted_count": 2,
                "remote_smoke_summary_paths": [
                    "unit-smoke-a.json",
                    "unit-smoke-b.json",
                ],
                "remote_smoke_total_count": 2,
                "sample_pairs": [{"eq1_id": 1, "eq2_id": 2}],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    strategy = strategy_registry_module._build_opnorm_hconst_match_collapse_strategy(
        equations_path=equations_path,
        pair_index_cache_path=pair_index_cache,
        register_summary_path=summary,
    )

    assert strategy.strategy_key == OPNORM_HCONST_MATCH_COLLAPSE_STRATEGY_KEY
    assert strategy.coverage_rule.coverage_kind == "compiler_pair_indexes"
    assert strategy.coverage_rule.covers(1, 2)
    assert not strategy.coverage_rule.covers(2, 1)
    manifest = strategy.manifest_record()
    assert manifest["compiler_name"] == "opnorm_hconst_match_collapse"
    assert manifest["template_current_union_increment"] == 1
    assert manifest["template_current_conflict_increment"] == 0
    assert manifest["template_current_profile"] == "unit-profile-v6.json"
    assert manifest["template_controller_merge_review_path"] == (
        "unit-controller-review.json"
    )
    assert manifest["template_remote_smoke_status"] == "accepted_2_of_2"
    assert manifest["template_remote_smoke_summary_paths"] == [
        "unit-smoke-a.json",
        "unit-smoke-b.json",
    ]


def test_opnorm_hconst_sandwich_registry_strategy_loads_compiler_pair_cache(tmp_path):
    equations_path = tmp_path / "eq_size5.txt"
    equations_path.write_text(
        "\n".join(
            [
                "x * y = y * (y * z)",
                "x * x = y * (x * (x * z))",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    pair_index = ids_to_pair_index(1, 2, law_count=2)
    pair_index_cache = tmp_path / "pair_indexes.txt"
    pair_index_cache.write_text(f"{pair_index}\n", encoding="ascii")
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(
            {
                "after_merge_projection_against_current_summary": {
                    "conflict_count": 0,
                    "deterministic_true_covered": 1320757874,
                    "unresolved_estimate": 225585244,
                },
                "coverage_profile": "unit-profile-v6.json",
                "delta_against_current_profile_v6": {
                    "union_increment": 1,
                    "conflict_increment": 0,
                },
                "remote_smoke_accepted_count": 2,
                "remote_smoke_summary_paths": [
                    "unit-smoke-a.json",
                    "unit-smoke-b.json",
                ],
                "remote_smoke_total_count": 2,
                "source_ids": [1],
                "target_shape_counts": {"unit-shape": 1},
                "sample_pairs": [{"eq1_id": 1, "eq2_id": 2}],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    strategy = strategy_registry_module._build_opnorm_hconst_sandwich_strategy(
        equations_path=equations_path,
        pair_index_cache_path=pair_index_cache,
        register_summary_path=summary,
    )

    assert strategy.strategy_key == OPNORM_HCONST_SANDWICH_STRATEGY_KEY
    assert strategy.coverage_rule.coverage_kind == "compiler_pair_indexes"
    assert strategy.coverage_rule.covers(1, 2)
    assert not strategy.coverage_rule.covers(2, 1)
    manifest = strategy.manifest_record()
    assert manifest["compiler_name"] == "opnorm_hconst_sandwich_match_collapse"
    assert manifest["template_source_ids"] == [1]
    assert manifest["template_target_shape_counts"] == {"unit-shape": 1}
    assert manifest["template_current_union_increment"] == 1
    assert manifest["template_current_conflict_increment"] == 0
    assert manifest["template_current_profile"] == "unit-profile-v6.json"
    assert manifest["template_remote_smoke_status"] == "accepted_2_of_2"


def test_opnorm_hconst_lmrm_mainline_registry_strategy_loads_compiler_pair_cache(
    tmp_path,
):
    equations_path = tmp_path / "eq_size5.txt"
    equations_path.write_text(
        "\n".join(
            [
                "x * y = y * (y * ((y * z) * w))",
                "x * x = x * (x * (y * z))",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    pair_index = ids_to_pair_index(1, 2, law_count=2)
    pair_index_cache = tmp_path / "pair_indexes.txt"
    pair_index_cache.write_text(f"{pair_index}\n", encoding="ascii")
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(
            {
                "after_merge_projection_against_current_summary": {
                    "conflict_count": 0,
                    "deterministic_true_covered": 1321867317,
                    "unresolved_estimate": 224449610,
                },
                "coverage_profile": "unit-profile-v7.json",
                "delta_against_current_profile_v7": {
                    "union_increment": 1,
                    "conflict_increment": 0,
                },
                "remote_smoke_accepted_count": 3,
                "remote_smoke_summary_paths": [
                    "unit-smoke-a.json",
                    "unit-smoke-b.json",
                ],
                "remote_smoke_total_count": 3,
                "source_count": 1,
                "source_ids_sample": [1],
                "source_class_hit_counts": {"left": 1},
                "target_label_hit_counts": {"lm1_d13_left": 1},
                "target_shape_counts": {"unit-shape": 1},
                "sample_pairs": [{"eq1_id": 1, "eq2_id": 2}],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    strategy = strategy_registry_module._build_opnorm_hconst_lmrm_mainline_strategy(
        equations_path=equations_path,
        pair_index_cache_path=pair_index_cache,
        register_summary_path=summary,
    )

    assert strategy.strategy_key == OPNORM_HCONST_LMRM_MAINLINE_STRATEGY_KEY
    assert strategy.coverage_rule.coverage_kind == "compiler_pair_indexes"
    assert strategy.coverage_rule.covers(1, 2)
    assert not strategy.coverage_rule.covers(2, 1)
    manifest = strategy.manifest_record()
    assert manifest["compiler_name"] == "opnorm_hconst_match_collapse_lmrm_mainline"
    assert manifest["template_source_count"] == 1
    assert manifest["template_source_class_hit_counts"] == {"left": 1}
    assert manifest["template_target_label_hit_counts"] == {"lm1_d13_left": 1}
    assert manifest["template_current_union_increment"] == 1
    assert manifest["template_current_conflict_increment"] == 0
    assert manifest["template_current_profile"] == "unit-profile-v7.json"
    assert manifest["template_remote_smoke_status"] == "accepted_3_of_3"


def test_opnorm_hconst_varmul_top01_registry_strategy_loads_compiler_pair_cache(
    tmp_path,
):
    equations_path = tmp_path / "eq_size5.txt"
    equations_path.write_text(
        "\n".join(
            [
                "x = y * (y * (y * (z * w)))",
                "x = y * (x * (x * (z * w)))",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    pair_index = ids_to_pair_index(1, 2, law_count=2)
    pair_index_cache = tmp_path / "pair_indexes.txt"
    pair_index_cache.write_text(f"{pair_index}\n", encoding="ascii")
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(
            {
                "after_merge_projection_against_current_summary": {
                    "conflict_count": 0,
                    "deterministic_true_covered": 1321940717,
                    "unresolved_estimate": 224376210,
                },
                "coverage_profile": "unit-profile-v8.json",
                "delta_against_current_profile_v8": {
                    "union_increment": 1,
                    "conflict_increment": 0,
                },
                "hit_stratum_counts": {"order4_source_to_order4_target": 1},
                "remote_smoke_accepted_count": 4,
                "remote_smoke_summary_paths": ["unit-smoke.json"],
                "remote_smoke_total_count": 4,
                "source_count_with_hits": 1,
                "source_offset_range": [0, 1],
                "source_shape": "roots=var>mul|d=0>4|vc=4|lm=0|rm=0|vs=0",
                "target_count_with_hits": 1,
                "target_shape": "roots=var>mul|d=0>4|vc=4|lm=0|rm=0|vs=0",
                "sample_pairs": [{"eq1_id": 1, "eq2_id": 2}],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    strategy = strategy_registry_module._build_opnorm_hconst_varmul_top01_strategy(
        equations_path=equations_path,
        pair_index_cache_path=pair_index_cache,
        register_summary_path=summary,
    )

    assert strategy.strategy_key == OPNORM_HCONST_VARMUL_TOP01_STRATEGY_KEY
    assert strategy.coverage_rule.coverage_kind == "compiler_pair_indexes"
    assert strategy.coverage_rule.covers(1, 2)
    assert not strategy.coverage_rule.covers(2, 1)
    manifest = strategy.manifest_record()
    assert manifest["compiler_name"] == "opnorm_hconst_match_collapse_varmul_top01"
    assert manifest["template_current_union_increment"] == 1
    assert manifest["template_current_conflict_increment"] == 0
    assert manifest["template_current_profile"] == "unit-profile-v8.json"
    assert manifest["template_remote_smoke_status"] == "accepted_4_of_4"
    assert manifest["template_hit_stratum_counts"] == {
        "order4_source_to_order4_target": 1
    }


def test_opnorm_hconst_default_sandwich_top16_strategy_loads_compiler_pair_cache(
    tmp_path,
):
    equations_path = tmp_path / "eq_size5.txt"
    equations_path.write_text(
        "\n".join(
            [
                "x * y = z * ((y * (w * w)) * u)",
                "x * y = ((z * (x * z)) * x) * x",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    pair_index = ids_to_pair_index(1, 2, law_count=2)
    pair_index_cache = tmp_path / "pair_indexes.txt"
    pair_index_cache.write_text(f"{pair_index}\n", encoding="ascii")
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(
            {
                "after_merge_projection_against_current_summary": {
                    "conflict_count": 0,
                    "deterministic_true_covered": 1322210379,
                    "unresolved_estimate": 224106548,
                },
                "coverage_profile": "unit-profile-v8.json",
                "delta_against_current_profile_v8": {
                    "union_increment": 1,
                    "conflict_increment": 0,
                },
                "hit_stratum_counts": {"order5_source_to_order5_target": 1},
                "remote_smoke_accepted_count": 5,
                "remote_smoke_summary_paths": ["unit-smoke.json"],
                "remote_smoke_total_count": 5,
                "shape_bucket": "unit-shape",
                "source_count": 1,
                "source_shape": "source-shape",
                "target_count": 1,
                "target_shape": "target-shape",
                "sample_pairs": [{"eq1_id": 1, "eq2_id": 2}],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    strategy = (
        strategy_registry_module._build_opnorm_hconst_default_sandwich_top16_strategy(
            equations_path=equations_path,
            pair_index_cache_path=pair_index_cache,
            register_summary_path=summary,
        )
    )

    assert strategy.strategy_key == OPNORM_HCONST_DEFAULT_SANDWICH_TOP16_STRATEGY_KEY
    assert strategy.coverage_rule.coverage_kind == "compiler_pair_indexes"
    assert strategy.coverage_rule.covers(1, 2)
    assert not strategy.coverage_rule.covers(2, 1)
    manifest = strategy.manifest_record()
    assert (
        manifest["compiler_name"]
        == "opnorm_hconst_default_sandwich_match_collapse_top16"
    )
    assert manifest["template_current_union_increment"] == 1
    assert manifest["template_current_conflict_increment"] == 0
    assert manifest["template_current_profile"] == "unit-profile-v8.json"
    assert manifest["template_remote_smoke_status"] == "accepted_5_of_5"
    assert manifest["template_hit_stratum_counts"] == {
        "order5_source_to_order5_target": 1
    }


def test_opnorm_hconst_default_sandwich_d14vc4_strategy_loads_compiler_pair_cache(
    tmp_path,
):
    equations_path = tmp_path / "eq_size5.txt"
    equations_path.write_text(
        "\n".join(
            [
                "x * y = y * (z * (y * (y * w)))",
                "x * x = y * (x * (x * (z * w)))",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    pair_index = ids_to_pair_index(1, 2, law_count=2)
    pair_index_cache = tmp_path / "pair_indexes.txt"
    pair_index_cache.write_text(f"{pair_index}\n", encoding="ascii")
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(
            {
                "after_merge_projection_against_current_summary": {
                    "conflict_count": 0,
                    "deterministic_true_covered": 1325116789,
                    "unresolved_estimate": 221200138,
                },
                "coverage_profile": "unit-profile-v9.json",
                "delta_against_current_profile_v9": {
                    "union_increment": 1,
                    "conflict_increment": 0,
                },
                "hit_stratum_counts": {"order5_source_to_order5_target": 1},
                "remote_smoke_accepted_count": 6,
                "remote_smoke_summary_paths": ["unit-smoke.json"],
                "remote_smoke_total_count": 6,
                "shape_counts": {"unit-source -> unit-target": 1},
                "source_count": 1,
                "source_shape": "unit-source",
                "target_shape_count": 2,
                "target_shapes": ["unit-target-a", "unit-target-b"],
                "top_source_hit_counts": [{"eq1_id": 1, "hit_count": 1}],
                "sample_pairs": [{"eq1_id": 1, "eq2_id": 2}],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    strategy = (
        strategy_registry_module._build_opnorm_hconst_default_sandwich_d14vc4_strategy(
            equations_path=equations_path,
            pair_index_cache_path=pair_index_cache,
            register_summary_path=summary,
        )
    )

    assert strategy.strategy_key == OPNORM_HCONST_DEFAULT_SANDWICH_D14VC4_STRATEGY_KEY
    assert strategy.coverage_rule.coverage_kind == "compiler_pair_indexes"
    assert strategy.coverage_rule.covers(1, 2)
    assert not strategy.coverage_rule.covers(2, 1)
    manifest = strategy.manifest_record()
    assert (
        manifest["compiler_name"]
        == "opnorm_hconst_default_sandwich_match_collapse_d14vc4"
    )
    assert manifest["template_current_union_increment"] == 1
    assert manifest["template_current_conflict_increment"] == 0
    assert manifest["template_current_profile"] == "unit-profile-v9.json"
    assert manifest["template_remote_smoke_status"] == "accepted_6_of_6"
    assert manifest["template_source_shape"] == "unit-source"
    assert manifest["template_target_shapes"] == ["unit-target-a", "unit-target-b"]
    assert manifest["template_target_shape_count"] == 2
    assert manifest["template_shape_counts"] == {"unit-source -> unit-target": 1}
    assert manifest["template_hit_stratum_counts"] == {
        "order5_source_to_order5_target": 1
    }


def test_opnorm_hconst_default_sandwich_d13vc4_strategy_loads_compiler_pair_cache(
    tmp_path,
):
    equations_path = tmp_path / "eq_size5.txt"
    equations_path.write_text(
        "\n".join(
            [
                "x * y = z * (w * (x * x))",
                "x * (y * z) = w * (x * x)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    pair_index = ids_to_pair_index(1, 2, law_count=2)
    pair_index_cache = tmp_path / "pair_indexes.txt"
    pair_index_cache.write_text(f"{pair_index}\n", encoding="ascii")
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(
            {
                "after_merge_projection_against_current_summary": {
                    "conflict_count": 0,
                    "deterministic_true_covered": 1328758970,
                    "unresolved_estimate": 217557957,
                },
                "coverage_profile": "unit-profile-v10.json",
                "delta_against_current_profile_v10": {
                    "union_increment": 1,
                    "conflict_increment": 0,
                },
                "hit_stratum_counts": {"order5_source_to_order5_target": 1},
                "remote_smoke_accepted_count": 7,
                "remote_smoke_summary_paths": ["unit-smoke.json"],
                "remote_smoke_total_count": 7,
                "shape_counts": {"unit-source -> unit-target": 1},
                "source_count": 1,
                "source_shape": "unit-source",
                "target_shape_count": 3,
                "target_shapes": ["unit-target-a", "unit-target-b", "unit-target-c"],
                "top_source_hit_counts": [{"source_id": 1, "hit_count": 1}],
                "source_hits_paths": ["unit-hits.jsonl"],
                "sample_pairs": [{"eq1_id": 1, "eq2_id": 2}],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    strategy = (
        strategy_registry_module._build_opnorm_hconst_default_sandwich_d13vc4_strategy(
            equations_path=equations_path,
            pair_index_cache_path=pair_index_cache,
            register_summary_path=summary,
        )
    )

    assert strategy.strategy_key == OPNORM_HCONST_DEFAULT_SANDWICH_D13VC4_STRATEGY_KEY
    assert strategy.coverage_rule.coverage_kind == "compiler_pair_indexes"
    assert strategy.coverage_rule.covers(1, 2)
    assert not strategy.coverage_rule.covers(2, 1)
    manifest = strategy.manifest_record()
    assert (
        manifest["compiler_name"]
        == "opnorm_hconst_default_sandwich_match_collapse_d13vc4"
    )
    assert manifest["template_current_union_increment"] == 1
    assert manifest["template_current_conflict_increment"] == 0
    assert manifest["template_current_profile"] == "unit-profile-v10.json"
    assert manifest["template_remote_smoke_status"] == "accepted_7_of_7"
    assert manifest["template_source_shape"] == "unit-source"
    assert manifest["template_target_shapes"] == [
        "unit-target-a",
        "unit-target-b",
        "unit-target-c",
    ]
    assert manifest["template_target_shape_count"] == 3
    assert manifest["template_shape_counts"] == {"unit-source -> unit-target": 1}
    assert manifest["template_source_hits_paths"] == ["unit-hits.jsonl"]


def test_opnorm_hconst_default_sandwich_d14vc4_targetext_strategy_loads_compiler_pair_cache(
    tmp_path,
):
    equations_path = tmp_path / "eq_size5.txt"
    equations_path.write_text(
        "\n".join(
            [
                "x * y = y * (z * (y * (y * w)))",
                "x * y = y * (x * x)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    pair_index = ids_to_pair_index(1, 2, law_count=2)
    pair_index_cache = tmp_path / "pair_indexes.txt"
    pair_index_cache.write_text(f"{pair_index}\n", encoding="ascii")
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(
            {
                "after_merge_projection_against_current_summary": {
                    "conflict_count": 0,
                    "deterministic_true_covered": 1331863355,
                    "unresolved_estimate": 214453572,
                },
                "coverage_profile": "unit-profile-v11.json",
                "delta_against_current_profile_v11": {
                    "union_increment": 1,
                    "conflict_increment": 0,
                },
                "hit_stratum_counts": {"order5_source_to_order5_target": 1},
                "remote_smoke_accepted_count": 8,
                "remote_smoke_summary_paths": ["unit-smoke.json"],
                "remote_smoke_total_count": 8,
                "shape_counts": {"unit-source -> unit-target": 1},
                "source_count": 1,
                "source_shape": "unit-source",
                "target_shape_count": 4,
                "target_shapes": [
                    "unit-target-a",
                    "unit-target-b",
                    "unit-target-c",
                    "unit-target-d",
                ],
                "top_source_hit_counts": [{"source_id": 1, "hit_count": 1}],
                "source_hits_paths": ["unit-hits.jsonl"],
                "sample_pairs": [{"eq1_id": 1, "eq2_id": 2}],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    strategy = (
        strategy_registry_module._build_opnorm_hconst_default_sandwich_d14vc4_targetext_strategy(
            equations_path=equations_path,
            pair_index_cache_path=pair_index_cache,
            register_summary_path=summary,
        )
    )

    assert (
        strategy.strategy_key
        == OPNORM_HCONST_DEFAULT_SANDWICH_D14VC4_TARGETEXT_STRATEGY_KEY
    )
    assert strategy.coverage_rule.coverage_kind == "compiler_pair_indexes"
    assert strategy.coverage_rule.covers(1, 2)
    assert not strategy.coverage_rule.covers(2, 1)
    manifest = strategy.manifest_record()
    assert manifest["compiler_name"] == (
        "opnorm_hconst_default_sandwich_match_collapse_d14vc4_targetext"
    )
    assert manifest["template_current_union_increment"] == 1
    assert manifest["template_current_conflict_increment"] == 0
    assert manifest["template_current_profile"] == "unit-profile-v11.json"
    assert manifest["template_remote_smoke_status"] == "accepted_8_of_8"
    assert manifest["template_source_shape"] == "unit-source"
    assert manifest["template_target_shape_count"] == 4
    assert manifest["template_shape_counts"] == {"unit-source -> unit-target": 1}
    assert manifest["template_source_hits_paths"] == ["unit-hits.jsonl"]


def test_opnorm_hconst_default_sandwich_lowvc_extension_strategy_loads_compiler_pair_cache(
    tmp_path,
):
    equations_path = tmp_path / "eq_size5.txt"
    equations_path.write_text(
        "\n".join(
            [
                "x * y = y * (x * x)",
                "x * (y * z) = y * (x * x)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    pair_index = ids_to_pair_index(1, 2, law_count=2)
    pair_index_cache = tmp_path / "pair_indexes.txt"
    pair_index_cache.write_text(f"{pair_index}\n", encoding="ascii")
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(
            {
                "after_merge_projection_against_current_summary": {
                    "conflict_count": 0,
                    "deterministic_true_covered": 1333349806,
                    "unresolved_estimate": 212967121,
                },
                "coverage_profile": "unit-profile-v12.json",
                "delta_against_current_profile_v12": {
                    "union_increment": 1,
                    "conflict_increment": 0,
                },
                "hit_stratum_counts": {"order5_source_to_order5_target": 1},
                "remote_smoke_accepted_count": 9,
                "remote_smoke_summary_paths": ["unit-smoke.json"],
                "remote_smoke_total_count": 9,
                "shape_counts": {"unit-source -> unit-target": 1},
                "source_shape_count": 2,
                "source_shapes": ["unit-source-a", "unit-source-b"],
                "source_counts_by_shape": {"unit-source-a": 1, "unit-source-b": 1},
                "target_shape_count": 3,
                "target_shapes": ["unit-target-a", "unit-target-b", "unit-target-c"],
                "top_source_hit_counts": [{"source_id": 1, "hit_count": 1}],
                "source_hits_paths": ["unit-hits.jsonl"],
                "sample_pairs": [{"eq1_id": 1, "eq2_id": 2}],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    strategy = (
        strategy_registry_module._build_opnorm_hconst_default_sandwich_lowvc_extension_strategy(
            equations_path=equations_path,
            pair_index_cache_path=pair_index_cache,
            register_summary_path=summary,
        )
    )

    assert (
        strategy.strategy_key
        == OPNORM_HCONST_DEFAULT_SANDWICH_LOWVC_EXTENSION_STRATEGY_KEY
    )
    assert strategy.coverage_rule.coverage_kind == "compiler_pair_indexes"
    assert strategy.coverage_rule.covers(1, 2)
    assert not strategy.coverage_rule.covers(2, 1)
    manifest = strategy.manifest_record()
    assert manifest["compiler_name"] == (
        "opnorm_hconst_default_sandwich_match_collapse_lowvc_extension"
    )
    assert manifest["template_current_union_increment"] == 1
    assert manifest["template_current_conflict_increment"] == 0
    assert manifest["template_current_profile"] == "unit-profile-v12.json"
    assert manifest["template_remote_smoke_status"] == "accepted_9_of_9"
    assert manifest["template_source_shapes"] == ["unit-source-a", "unit-source-b"]
    assert manifest["template_source_shape_count"] == 2
    assert manifest["template_source_counts_by_shape"] == {
        "unit-source-a": 1,
        "unit-source-b": 1,
    }
    assert manifest["template_target_shape_count"] == 3
    assert manifest["template_shape_counts"] == {"unit-source -> unit-target": 1}


def test_opnorm_hconst_default_sandwich_topbucket_extension_strategy_loads_compiler_pair_cache(
    tmp_path,
):
    equations_path = tmp_path / "eq_size5.txt"
    equations_path.write_text(
        "\n".join(
            [
                "x * y = y * (x * x)",
                "x * (y * z) = y * (x * x)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    pair_index = ids_to_pair_index(1, 2, law_count=2)
    pair_index_cache = tmp_path / "pair_indexes.txt"
    pair_index_cache.write_text(f"{pair_index}\n", encoding="ascii")
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(
            {
                "after_merge_projection_against_current_summary": {
                    "conflict_count": 0,
                    "deterministic_true_covered": 1335125626,
                    "unresolved_estimate": 211191301,
                },
                "coverage_profile": "unit-profile-v13.json",
                "delta_against_current_profile_v13": {
                    "union_increment": 1,
                    "conflict_increment": 0,
                },
                "hit_stratum_counts": {"order5_source_to_order5_target": 1},
                "remote_smoke_accepted_count": 10,
                "remote_smoke_summary_paths": ["unit-smoke.json"],
                "remote_smoke_total_count": 10,
                "shape_counts": {"unit-source -> unit-target": 1},
                "source_shape_count": 2,
                "source_shapes": ["unit-source-a", "unit-source-b"],
                "source_counts_by_shape": {"unit-source-a": 1, "unit-source-b": 1},
                "target_shape_count": 3,
                "target_shapes": ["unit-target-a", "unit-target-b", "unit-target-c"],
                "top_source_hit_counts": [{"source_id": 1, "hit_count": 1}],
                "source_hits_paths": ["unit-hits.jsonl"],
                "sample_pairs": [{"eq1_id": 1, "eq2_id": 2}],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    strategy = (
        strategy_registry_module._build_opnorm_hconst_default_sandwich_topbucket_extension_strategy(
            equations_path=equations_path,
            pair_index_cache_path=pair_index_cache,
            register_summary_path=summary,
        )
    )

    assert (
        strategy.strategy_key
        == OPNORM_HCONST_DEFAULT_SANDWICH_TOPBUCKET_EXTENSION_STRATEGY_KEY
    )
    assert strategy.coverage_rule.coverage_kind == "compiler_pair_indexes"
    assert strategy.coverage_rule.covers(1, 2)
    assert not strategy.coverage_rule.covers(2, 1)
    manifest = strategy.manifest_record()
    assert manifest["compiler_name"] == (
        "opnorm_hconst_default_sandwich_match_collapse_topbucket_extension"
    )
    assert manifest["template_current_union_increment"] == 1
    assert manifest["template_current_conflict_increment"] == 0
    assert manifest["template_current_profile"] == "unit-profile-v13.json"
    assert manifest["template_remote_smoke_status"] == "accepted_10_of_10"
    assert manifest["template_source_shapes"] == ["unit-source-a", "unit-source-b"]
    assert manifest["template_source_shape_count"] == 2
    assert manifest["template_source_counts_by_shape"] == {
        "unit-source-a": 1,
        "unit-source-b": 1,
    }
    assert manifest["template_target_shape_count"] == 3
    assert manifest["template_shape_counts"] == {"unit-source -> unit-target": 1}


def test_opnorm_hconst_default_sandwich_frontier_extension_strategy_loads_compiler_pair_cache(
    tmp_path,
):
    equations_path = tmp_path / "eq_size5.txt"
    equations_path.write_text(
        "\n".join(
            [
                "x * y = y * (x * x)",
                "x * (y * z) = y * (x * x)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    pair_index = ids_to_pair_index(1, 2, law_count=2)
    pair_index_cache = tmp_path / "pair_indexes.txt"
    pair_index_cache.write_text(f"{pair_index}\n", encoding="ascii")
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(
            {
                "after_merge_projection_against_current_summary": {
                    "conflict_count": 0,
                    "deterministic_true_covered": 1338120456,
                    "unresolved_estimate": 208196471,
                },
                "coverage_profile": "unit-profile-v14.json",
                "delta_against_current_profile_v14": {
                    "union_increment": 1,
                    "conflict_increment": 0,
                },
                "hit_stratum_counts": {"order5_source_to_order5_target": 1},
                "remote_smoke_accepted_count": 11,
                "remote_smoke_summary_paths": ["unit-smoke.json"],
                "remote_smoke_total_count": 11,
                "shape_counts": {"unit-source -> unit-target": 1},
                "source_shape_count": 2,
                "source_shapes": ["unit-source-a", "unit-source-b"],
                "source_counts_by_shape": {"unit-source-a": 1, "unit-source-b": 1},
                "target_shape_count": 3,
                "target_shapes": ["unit-target-a", "unit-target-b", "unit-target-c"],
                "top_source_hit_counts": [{"source_id": 1, "hit_count": 1}],
                "source_hits_paths": ["unit-hits.jsonl"],
                "sample_pairs": [{"eq1_id": 1, "eq2_id": 2}],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    strategy = (
        strategy_registry_module._build_opnorm_hconst_default_sandwich_frontier_extension_strategy(
            equations_path=equations_path,
            pair_index_cache_path=pair_index_cache,
            register_summary_path=summary,
        )
    )

    assert (
        strategy.strategy_key
        == OPNORM_HCONST_DEFAULT_SANDWICH_FRONTIER_EXTENSION_STRATEGY_KEY
    )
    assert strategy.coverage_rule.coverage_kind == "compiler_pair_indexes"
    assert strategy.coverage_rule.covers(1, 2)
    assert not strategy.coverage_rule.covers(2, 1)
    manifest = strategy.manifest_record()
    assert manifest["compiler_name"] == (
        "opnorm_hconst_default_sandwich_match_collapse_frontier_extension"
    )
    assert manifest["template_current_union_increment"] == 1
    assert manifest["template_current_conflict_increment"] == 0
    assert manifest["template_current_profile"] == "unit-profile-v14.json"
    assert manifest["template_remote_smoke_status"] == "accepted_11_of_11"
    assert manifest["template_source_shapes"] == ["unit-source-a", "unit-source-b"]
    assert manifest["template_source_shape_count"] == 2
    assert manifest["template_source_counts_by_shape"] == {
        "unit-source-a": 1,
        "unit-source-b": 1,
    }
    assert manifest["template_target_shape_count"] == 3
    assert manifest["template_shape_counts"] == {"unit-source -> unit-target": 1}


def test_opnorm_hconst_default_sandwich_edge_extension_strategy_loads_compiler_pair_cache(
    tmp_path,
):
    equations_path = tmp_path / "eq_size5.txt"
    equations_path.write_text(
        "\n".join(
            [
                "x * y = y * (x * x)",
                "x * (y * z) = y * (x * x)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    pair_index = ids_to_pair_index(1, 2, law_count=2)
    pair_index_cache = tmp_path / "pair_indexes.txt"
    pair_index_cache.write_text(f"{pair_index}\n", encoding="ascii")
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(
            {
                "after_merge_projection_against_current_summary": {
                    "conflict_count": 0,
                    "deterministic_true_covered": 1339189864,
                    "unresolved_estimate": 207127063,
                },
                "coverage_profile": "unit-profile-v15.json",
                "delta_against_current_profile_v15": {
                    "union_increment": 1,
                    "conflict_increment": 0,
                },
                "hit_stratum_counts": {"order5_source_to_order5_target": 1},
                "remote_smoke_accepted_count": 12,
                "remote_smoke_summary_paths": ["unit-smoke.json"],
                "remote_smoke_total_count": 12,
                "shape_counts": {"unit-source -> unit-target": 1},
                "source_shape_count": 2,
                "source_shapes": ["unit-source-a", "unit-source-b"],
                "source_counts_by_shape": {"unit-source-a": 1, "unit-source-b": 1},
                "target_shape_count": 3,
                "target_shapes": ["unit-target-a", "unit-target-b", "unit-target-c"],
                "top_source_hit_counts": [{"source_id": 1, "hit_count": 1}],
                "source_hits_paths": ["unit-hits.jsonl"],
                "sample_pairs": [{"eq1_id": 1, "eq2_id": 2}],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    strategy = (
        strategy_registry_module._build_opnorm_hconst_default_sandwich_edge_extension_strategy(
            equations_path=equations_path,
            pair_index_cache_path=pair_index_cache,
            register_summary_path=summary,
        )
    )

    assert (
        strategy.strategy_key
        == OPNORM_HCONST_DEFAULT_SANDWICH_EDGE_EXTENSION_STRATEGY_KEY
    )
    assert strategy.coverage_rule.coverage_kind == "compiler_pair_indexes"
    assert strategy.coverage_rule.covers(1, 2)
    assert not strategy.coverage_rule.covers(2, 1)
    manifest = strategy.manifest_record()
    assert manifest["compiler_name"] == (
        "opnorm_hconst_default_sandwich_match_collapse_edge_extension"
    )
    assert manifest["template_current_union_increment"] == 1
    assert manifest["template_current_conflict_increment"] == 0
    assert manifest["template_current_profile"] == "unit-profile-v15.json"
    assert manifest["template_remote_smoke_status"] == "accepted_12_of_12"
    assert manifest["template_source_shapes"] == ["unit-source-a", "unit-source-b"]
    assert manifest["template_source_shape_count"] == 2
    assert manifest["template_source_counts_by_shape"] == {
        "unit-source-a": 1,
        "unit-source-b": 1,
    }
    assert manifest["template_target_shape_count"] == 3
    assert manifest["template_shape_counts"] == {"unit-source -> unit-target": 1}


def test_opnorm_hconst_default_sandwich_postedge_top40_extension_strategy_loads_compiler_pair_cache(
    tmp_path,
):
    equations_path = tmp_path / "eq_size5.txt"
    equations_path.write_text(
        "\n".join(
            [
                "x * y = y * (x * x)",
                "x * (y * z) = y * (x * x)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    pair_index = ids_to_pair_index(1, 2, law_count=2)
    pair_index_cache = tmp_path / "pair_indexes.txt"
    pair_index_cache.write_text(f"{pair_index}\n", encoding="ascii")
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(
            {
                "after_merge_projection_against_current_summary": {
                    "conflict_count": 0,
                    "deterministic_true_covered": 1344693702,
                    "unresolved_estimate": 201564187,
                },
                "coverage_profile": "unit-profile-v16.json",
                "delta_against_current_profile_v16": {
                    "union_increment": 1,
                    "conflict_increment": 0,
                },
                "hit_stratum_counts": {"order5_source_to_order5_target": 1},
                "remote_smoke_accepted_count": 13,
                "remote_smoke_summary_paths": ["unit-smoke.json"],
                "remote_smoke_total_count": 13,
                "shape_counts": {"unit-source -> unit-target": 1},
                "source_shape_count": 2,
                "source_shapes": ["unit-source-a", "unit-source-b"],
                "source_counts_by_shape": {"unit-source-a": 1, "unit-source-b": 1},
                "target_shape_count": 3,
                "target_shapes": ["unit-target-a", "unit-target-b", "unit-target-c"],
                "top_source_hit_counts": [{"source_id": 1, "hit_count": 1}],
                "source_hits_paths": ["unit-hits.jsonl"],
                "sample_pairs": [{"eq1_id": 1, "eq2_id": 2}],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    strategy = strategy_registry_module._build_opnorm_hconst_default_sandwich_postedge_top40_extension_strategy(
        equations_path=equations_path,
        pair_index_cache_path=pair_index_cache,
        register_summary_path=summary,
    )

    assert (
        strategy.strategy_key
        == OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE_TOP40_EXTENSION_STRATEGY_KEY
    )
    assert strategy.coverage_rule.coverage_kind == "compiler_pair_indexes"
    assert strategy.coverage_rule.covers(1, 2)
    assert not strategy.coverage_rule.covers(2, 1)
    manifest = strategy.manifest_record()
    assert manifest["compiler_name"] == (
        "opnorm_hconst_default_sandwich_match_collapse_postedge_top40_extension"
    )
    assert manifest["template_current_union_increment"] == 1
    assert manifest["template_current_conflict_increment"] == 0
    assert manifest["template_current_profile"] == "unit-profile-v16.json"
    assert manifest["template_remote_smoke_status"] == "accepted_13_of_13"
    assert manifest["template_source_shapes"] == ["unit-source-a", "unit-source-b"]
    assert manifest["template_source_shape_count"] == 2
    assert manifest["template_source_counts_by_shape"] == {
        "unit-source-a": 1,
        "unit-source-b": 1,
    }
    assert manifest["template_target_shape_count"] == 3
    assert manifest["template_shape_counts"] == {"unit-source -> unit-target": 1}


def test_opnorm_hconst_default_sandwich_postedge2_top60_extension_strategy_loads_compiler_pair_cache(
    tmp_path,
):
    equations_path = tmp_path / "eq_size5.txt"
    equations_path.write_text(
        "\n".join(
            [
                "x * y = y * (x * x)",
                "x * (y * z) = y * (x * x)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    pair_index = ids_to_pair_index(1, 2, law_count=2)
    pair_index_cache = tmp_path / "pair_indexes.txt"
    pair_index_cache.write_text(f"{pair_index}\n", encoding="ascii")
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(
            {
                "after_merge_projection_against_current_summary": {
                    "conflict_count": 0,
                    "deterministic_true_covered": 1350989631,
                    "unresolved_estimate": 195268258,
                },
                "coverage_profile": "unit-profile-v17.json",
                "delta_against_current_profile_v17": {
                    "union_increment": 1,
                    "conflict_increment": 0,
                },
                "hit_stratum_counts": {"order5_source_to_order5_target": 1},
                "remote_smoke_accepted_count": 14,
                "remote_smoke_summary_paths": ["unit-smoke.json"],
                "remote_smoke_total_count": 14,
                "shape_counts": {"unit-source -> unit-target": 1},
                "source_shape_count": 2,
                "source_shapes": ["unit-source-a", "unit-source-b"],
                "source_counts_by_shape": {"unit-source-a": 1, "unit-source-b": 1},
                "target_shape_count": 3,
                "target_shapes": ["unit-target-a", "unit-target-b", "unit-target-c"],
                "top_source_hit_counts": [{"source_id": 1, "hit_count": 1}],
                "source_hits_paths": ["unit-hits.jsonl"],
                "sample_pairs": [{"eq1_id": 1, "eq2_id": 2}],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    strategy = strategy_registry_module._build_opnorm_hconst_default_sandwich_postedge2_top60_extension_strategy(
        equations_path=equations_path,
        pair_index_cache_path=pair_index_cache,
        register_summary_path=summary,
    )

    assert (
        strategy.strategy_key
        == OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE2_TOP60_EXTENSION_STRATEGY_KEY
    )
    assert strategy.coverage_rule.coverage_kind == "compiler_pair_indexes"
    assert strategy.coverage_rule.covers(1, 2)
    assert not strategy.coverage_rule.covers(2, 1)
    manifest = strategy.manifest_record()
    assert manifest["compiler_name"] == (
        "opnorm_hconst_default_sandwich_match_collapse_postedge2_top60_extension"
    )
    assert manifest["template_current_union_increment"] == 1
    assert manifest["template_current_conflict_increment"] == 0
    assert manifest["template_current_profile"] == "unit-profile-v17.json"
    assert manifest["template_remote_smoke_status"] == "accepted_14_of_14"
    assert manifest["template_source_shapes"] == ["unit-source-a", "unit-source-b"]
    assert manifest["template_source_shape_count"] == 2
    assert manifest["template_source_counts_by_shape"] == {
        "unit-source-a": 1,
        "unit-source-b": 1,
    }
    assert manifest["template_target_shape_count"] == 3
    assert manifest["template_shape_counts"] == {"unit-source -> unit-target": 1}


def test_opnorm_hconst_default_sandwich_postedge3_top80_extension_strategy_loads_compiler_pair_cache(
    tmp_path,
):
    equations_path = tmp_path / "eq_size5.txt"
    equations_path.write_text(
        "\n".join(
            [
                "x * y = y * (x * x)",
                "x * (y * z) = y * (x * x)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    pair_index = ids_to_pair_index(1, 2, law_count=2)
    pair_index_cache = tmp_path / "pair_indexes.txt"
    pair_index_cache.write_text(f"{pair_index}\n", encoding="ascii")
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(
            {
                "after_merge_projection_against_current_summary": {
                    "conflict_count": 0,
                    "deterministic_true_covered": 1354729736,
                    "unresolved_estimate": 191528153,
                },
                "coverage_profile": "unit-profile-v18.json",
                "delta_against_current_profile_v18": {
                    "union_increment": 1,
                    "conflict_increment": 0,
                },
                "hit_stratum_counts": {"order5_source_to_order5_target": 1},
                "remote_smoke_accepted_count": 15,
                "remote_smoke_summary_paths": ["unit-smoke.json"],
                "remote_smoke_total_count": 15,
                "shape_counts": {"unit-source -> unit-target": 1},
                "source_shape_count": 2,
                "source_shapes": ["unit-source-a", "unit-source-b"],
                "source_counts_by_shape": {"unit-source-a": 1, "unit-source-b": 1},
                "target_shape_count": 3,
                "target_shapes": ["unit-target-a", "unit-target-b", "unit-target-c"],
                "top_source_hit_counts": [{"source_id": 1, "hit_count": 1}],
                "source_hits_paths": ["unit-hits.jsonl"],
                "sample_pairs": [{"eq1_id": 1, "eq2_id": 2}],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    strategy = strategy_registry_module._build_opnorm_hconst_default_sandwich_postedge3_top80_extension_strategy(
        equations_path=equations_path,
        pair_index_cache_path=pair_index_cache,
        register_summary_path=summary,
    )

    assert (
        strategy.strategy_key
        == OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE3_TOP80_EXTENSION_STRATEGY_KEY
    )
    assert strategy.coverage_rule.coverage_kind == "compiler_pair_indexes"
    assert strategy.coverage_rule.covers(1, 2)
    assert not strategy.coverage_rule.covers(2, 1)
    manifest = strategy.manifest_record()
    assert manifest["compiler_name"] == (
        "opnorm_hconst_default_sandwich_match_collapse_postedge3_top80_extension"
    )
    assert manifest["template_current_union_increment"] == 1
    assert manifest["template_current_conflict_increment"] == 0
    assert manifest["template_current_profile"] == "unit-profile-v18.json"
    assert manifest["template_remote_smoke_status"] == "accepted_15_of_15"
    assert manifest["template_source_shapes"] == ["unit-source-a", "unit-source-b"]
    assert manifest["template_source_shape_count"] == 2
    assert manifest["template_source_counts_by_shape"] == {
        "unit-source-a": 1,
        "unit-source-b": 1,
    }
    assert manifest["template_target_shape_count"] == 3
    assert manifest["template_shape_counts"] == {"unit-source -> unit-target": 1}


def test_opnorm_hconst_default_sandwich_postedge4_top100_extension_strategy_loads_compiler_pair_cache(
    tmp_path,
):
    equations_path = tmp_path / "eq_size5.txt"
    equations_path.write_text(
        "\n".join(
            [
                "x * y = y * (x * x)",
                "x * (y * z) = y * (x * x)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    pair_index = ids_to_pair_index(1, 2, law_count=2)
    pair_index_cache = tmp_path / "pair_indexes.txt"
    pair_index_cache.write_text(f"{pair_index}\n", encoding="ascii")
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(
            {
                "after_merge_projection_against_current_summary": {
                    "conflict_count": 0,
                    "deterministic_true_covered": 1357847031,
                    "unresolved_estimate": 188410858,
                },
                "coverage_profile": "unit-profile-v19.json",
                "delta_against_current_profile_v19": {
                    "union_increment": 1,
                    "conflict_increment": 0,
                },
                "hit_stratum_counts": {"order5_source_to_order5_target": 1},
                "remote_smoke_accepted_count": 16,
                "remote_smoke_summary_paths": ["unit-smoke.json"],
                "remote_smoke_total_count": 16,
                "shape_counts": {"unit-source -> unit-target": 1},
                "source_shape_count": 2,
                "source_shapes": ["unit-source-a", "unit-source-b"],
                "source_counts_by_shape": {"unit-source-a": 1, "unit-source-b": 1},
                "target_shape_count": 3,
                "target_shapes": ["unit-target-a", "unit-target-b", "unit-target-c"],
                "top_source_hit_counts": [{"source_id": 1, "hit_count": 1}],
                "source_hits_paths": ["unit-hits.jsonl"],
                "sample_pairs": [{"eq1_id": 1, "eq2_id": 2}],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    strategy = strategy_registry_module._build_opnorm_hconst_default_sandwich_postedge4_top100_extension_strategy(
        equations_path=equations_path,
        pair_index_cache_path=pair_index_cache,
        register_summary_path=summary,
    )

    assert (
        strategy.strategy_key
        == OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE4_TOP100_EXTENSION_STRATEGY_KEY
    )
    assert strategy.coverage_rule.coverage_kind == "compiler_pair_indexes"
    assert strategy.coverage_rule.covers(1, 2)
    assert not strategy.coverage_rule.covers(2, 1)
    manifest = strategy.manifest_record()
    assert manifest["compiler_name"] == (
        "opnorm_hconst_default_sandwich_match_collapse_postedge4_top100_extension"
    )
    assert manifest["template_current_union_increment"] == 1
    assert manifest["template_current_conflict_increment"] == 0
    assert manifest["template_current_profile"] == "unit-profile-v19.json"
    assert manifest["template_remote_smoke_status"] == "accepted_16_of_16"
    assert manifest["template_source_shapes"] == ["unit-source-a", "unit-source-b"]
    assert manifest["template_source_shape_count"] == 2
    assert manifest["template_source_counts_by_shape"] == {
        "unit-source-a": 1,
        "unit-source-b": 1,
    }
    assert manifest["template_target_shape_count"] == 3
    assert manifest["template_shape_counts"] == {"unit-source -> unit-target": 1}


def test_opnorm_hconst_default_sandwich_postedge5_top120_extension_strategy_loads_compiler_pair_cache(
    tmp_path,
):
    equations_path = tmp_path / "eq_size5.txt"
    equations_path.write_text(
        "\n".join(
            [
                "x * y = y * (x * x)",
                "x * (y * z) = y * (x * x)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    pair_index = ids_to_pair_index(1, 2, law_count=2)
    pair_index_cache = tmp_path / "pair_indexes.txt"
    pair_index_cache.write_text(f"{pair_index}\n", encoding="ascii")
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(
            {
                "after_merge_projection_against_current_summary": {
                    "conflict_count": 0,
                    "deterministic_true_covered": 1359760747,
                    "unresolved_estimate": 186310259,
                },
                "coverage_profile": "unit-profile-v20.json",
                "delta_against_current_profile_v20": {
                    "union_increment": 1,
                    "conflict_increment": 0,
                },
                "hit_stratum_counts": {"order5_source_to_order5_target": 1},
                "remote_smoke_accepted_count": 17,
                "remote_smoke_summary_paths": ["unit-smoke.json"],
                "remote_smoke_total_count": 17,
                "shape_counts": {"unit-source -> unit-target": 1},
                "source_shape_count": 2,
                "source_shapes": ["unit-source-a", "unit-source-b"],
                "source_counts_by_shape": {"unit-source-a": 1, "unit-source-b": 1},
                "target_shape_count": 3,
                "target_shapes": ["unit-target-a", "unit-target-b", "unit-target-c"],
                "top_source_hit_counts": [{"source_id": 1, "hit_count": 1}],
                "source_hits_paths": ["unit-hits.jsonl"],
                "sample_pairs": [{"eq1_id": 1, "eq2_id": 2}],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    strategy = strategy_registry_module._build_opnorm_hconst_default_sandwich_postedge5_top120_extension_strategy(
        equations_path=equations_path,
        pair_index_cache_path=pair_index_cache,
        register_summary_path=summary,
    )

    assert (
        strategy.strategy_key
        == OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE5_TOP120_EXTENSION_STRATEGY_KEY
    )
    assert strategy.coverage_rule.coverage_kind == "compiler_pair_indexes"
    assert strategy.coverage_rule.covers(1, 2)
    assert not strategy.coverage_rule.covers(2, 1)
    manifest = strategy.manifest_record()
    assert manifest["compiler_name"] == (
        "opnorm_hconst_default_sandwich_match_collapse_postedge5_top120_extension"
    )
    assert manifest["template_current_union_increment"] == 1
    assert manifest["template_current_conflict_increment"] == 0
    assert manifest["template_current_profile"] == "unit-profile-v20.json"
    assert manifest["template_remote_smoke_status"] == "accepted_17_of_17"
    assert manifest["template_source_shapes"] == ["unit-source-a", "unit-source-b"]
    assert manifest["template_source_shape_count"] == 2
    assert manifest["template_source_counts_by_shape"] == {
        "unit-source-a": 1,
        "unit-source-b": 1,
    }
    assert manifest["template_target_shape_count"] == 3
    assert manifest["template_shape_counts"] == {"unit-source -> unit-target": 1}


def test_opnorm_hconst_default_sandwich_postedge6_samplehit_top20_tail_strategy_loads_compiler_pair_cache(
    tmp_path,
):
    equations_path = tmp_path / "eq_size5.txt"
    equations_path.write_text(
        "\n".join(
            [
                "x * y = y * (x * x)",
                "x * (y * z) = y * (x * x)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    pair_index = ids_to_pair_index(1, 2, law_count=2)
    pair_index_cache = tmp_path / "pair_indexes.txt"
    pair_index_cache.write_text(f"{pair_index}\n", encoding="ascii")
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(
            {
                "after_merge_projection": {
                    "conflict_count": 0,
                    "deterministic_true_covered": 1361769423,
                    "unresolved_estimate": 184301583,
                },
                "coverage_profile": "unit-profile-v22.json",
                "delta_against_current_profile_v22": {
                    "union_increment": 1,
                    "conflict_increment": 0,
                },
                "hit_stratum_counts": {"order5_source_to_order5_target": 1},
                "remote_smoke_accepted_count": 18,
                "remote_smoke_summary_paths": ["unit-smoke.json"],
                "remote_smoke_total_count": 18,
                "shape_counts": {"unit-source -> unit-target": 1},
                "source_shape_count": 2,
                "source_shapes": ["unit-source-a", "unit-source-b"],
                "source_counts_by_shape": {"unit-source-a": 1, "unit-source-b": 1},
                "target_shape_count": 3,
                "target_shapes": ["unit-target-a", "unit-target-b", "unit-target-c"],
                "top_source_hit_counts": [{"source_id": 1, "hit_count": 1}],
                "source_hits_paths": ["unit-hits.jsonl"],
                "representative_pairs": [{"eq1_id": 1, "eq2_id": 2}],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    strategy = strategy_registry_module._build_opnorm_hconst_default_sandwich_postedge6_samplehit_top20_tail_strategy(
        equations_path=equations_path,
        pair_index_cache_path=pair_index_cache,
        register_summary_path=summary,
    )

    assert (
        strategy.strategy_key
        == OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE6_SAMPLEHIT_TOP20_TAIL_STRATEGY_KEY
    )
    assert strategy.coverage_rule.coverage_kind == "compiler_pair_indexes"
    assert strategy.coverage_rule.covers(1, 2)
    assert not strategy.coverage_rule.covers(2, 1)
    manifest = strategy.manifest_record()
    assert manifest["compiler_name"] == (
        "opnorm_hconst_default_sandwich_match_collapse_postedge6_samplehit_top20_tail"
    )
    assert manifest["template_current_union_increment"] == 1
    assert manifest["template_current_conflict_increment"] == 0
    assert manifest["template_current_profile"] == "unit-profile-v22.json"
    assert manifest["template_remote_smoke_status"] == "accepted_18_of_18"
    assert manifest["template_source_shapes"] == ["unit-source-a", "unit-source-b"]
    assert manifest["template_source_shape_count"] == 2
    assert manifest["template_source_counts_by_shape"] == {
        "unit-source-a": 1,
        "unit-source-b": 1,
    }
    assert manifest["template_target_shape_count"] == 3
    assert manifest["template_shape_counts"] == {"unit-source -> unit-target": 1}
    assert manifest["template_after_merge_projection_against_current_summary"] == {
        "conflict_count": 0,
        "deterministic_true_covered": 1361769423,
        "unresolved_estimate": 184301583,
    }


def test_opnorm_hconst_default_sandwich_postedge7_samplehit_top20_tail_strategy_loads_compiler_pair_cache(
    tmp_path,
):
    equations_path = tmp_path / "eq_size5.txt"
    equations_path.write_text(
        "\n".join(
            [
                "x * y = y * (x * x)",
                "x * (y * z) = y * (x * x)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    pair_index = ids_to_pair_index(1, 2, law_count=2)
    pair_index_cache = tmp_path / "pair_indexes.txt"
    pair_index_cache.write_text(f"{pair_index}\n", encoding="ascii")
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(
            {
                "after_merge_projection": {
                    "conflict_count": 0,
                    "deterministic_true_covered": 1364538580,
                    "unresolved_estimate": 181532426,
                },
                "coverage_profile": "unit-profile-v23.json",
                "delta_against_current_profile_v23": {
                    "union_increment": 1,
                    "conflict_increment": 0,
                },
                "hit_stratum_counts": {"order5_source_to_order5_target": 1},
                "remote_smoke_accepted_count": 19,
                "remote_smoke_summary_paths": ["unit-smoke.json"],
                "remote_smoke_total_count": 19,
                "shape_counts": {"unit-source -> unit-target": 1},
                "source_shape_count": 2,
                "source_shapes": ["unit-source-a", "unit-source-b"],
                "source_counts_by_shape": {"unit-source-a": 1, "unit-source-b": 1},
                "target_shape_count": 3,
                "target_shapes": ["unit-target-a", "unit-target-b", "unit-target-c"],
                "top_source_hit_counts": [{"source_id": 1, "hit_count": 1}],
                "source_hits_paths": ["unit-hits.jsonl"],
                "representative_pairs": [{"eq1_id": 1, "eq2_id": 2}],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    strategy = strategy_registry_module._build_opnorm_hconst_default_sandwich_postedge7_samplehit_top20_tail_strategy(
        equations_path=equations_path,
        pair_index_cache_path=pair_index_cache,
        register_summary_path=summary,
    )

    assert (
        strategy.strategy_key
        == OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE7_SAMPLEHIT_TOP20_TAIL_STRATEGY_KEY
    )
    assert strategy.coverage_rule.coverage_kind == "compiler_pair_indexes"
    assert strategy.coverage_rule.covers(1, 2)
    assert not strategy.coverage_rule.covers(2, 1)
    manifest = strategy.manifest_record()
    assert manifest["compiler_name"] == (
        "opnorm_hconst_default_sandwich_match_collapse_postedge7_samplehit_top20_tail"
    )
    assert manifest["template_current_union_increment"] == 1
    assert manifest["template_current_conflict_increment"] == 0
    assert manifest["template_current_profile"] == "unit-profile-v23.json"
    assert manifest["template_remote_smoke_status"] == "accepted_19_of_19"
    assert manifest["template_source_shapes"] == ["unit-source-a", "unit-source-b"]
    assert manifest["template_source_shape_count"] == 2
    assert manifest["template_source_counts_by_shape"] == {
        "unit-source-a": 1,
        "unit-source-b": 1,
    }
    assert manifest["template_target_shape_count"] == 3
    assert manifest["template_shape_counts"] == {"unit-source -> unit-target": 1}
    assert manifest["template_after_merge_projection_against_current_summary"] == {
        "conflict_count": 0,
        "deterministic_true_covered": 1364538580,
        "unresolved_estimate": 181532426,
    }


def test_opnorm_hconst_default_sandwich_postedge8_d14vc5_frontier_multitarget20_strategy_loads_compiler_pair_cache(
    tmp_path,
):
    equations_path = tmp_path / "eq_size5.txt"
    equations_path.write_text(
        "\n".join(
            [
                "x * y = y * (x * x)",
                "x * (y * z) = y * (x * x)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    pair_index = ids_to_pair_index(1, 2, law_count=2)
    pair_index_cache = tmp_path / "pair_indexes.txt"
    pair_index_cache.write_text(f"{pair_index}\n", encoding="ascii")
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(
            {
                "after_merge_projection": {
                    "conflict_count": 0,
                    "deterministic_true_covered": 1365748955,
                    "unresolved_estimate": 166492867,
                },
                "coverage_profile": "unit-profile-v24.json",
                "delta_against_current_profile_v24": {
                    "union_increment": 1,
                    "conflict_increment": 0,
                },
                "hit_stratum_counts": {"order5_source_to_order5_target": 1},
                "remote_smoke_accepted_count": 20,
                "remote_smoke_summary_paths": ["unit-smoke.json"],
                "remote_smoke_total_count": 20,
                "shape_counts": {"unit-source -> unit-target": 1},
                "source_shape_count": 1,
                "source_shapes": ["unit-source"],
                "source_counts_by_shape": {"unit-source": 1},
                "target_shape_count": 4,
                "target_shapes": [
                    "unit-target-a",
                    "unit-target-b",
                    "unit-target-c",
                    "unit-target-d",
                ],
                "top_source_hit_counts": [{"source_id": 1, "hit_count": 1}],
                "source_hits_paths": ["unit-hits.jsonl"],
                "representative_pairs": [{"eq1_id": 1, "eq2_id": 2}],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    strategy = strategy_registry_module._build_opnorm_hconst_default_sandwich_postedge8_d14vc5_frontier_multitarget20_strategy(
        equations_path=equations_path,
        pair_index_cache_path=pair_index_cache,
        register_summary_path=summary,
    )

    assert (
        strategy.strategy_key
        == OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE8_D14VC5_FRONTIER_MULTITARGET20_STRATEGY_KEY
    )
    assert strategy.coverage_rule.coverage_kind == "compiler_pair_indexes"
    assert strategy.coverage_rule.covers(1, 2)
    assert not strategy.coverage_rule.covers(2, 1)
    manifest = strategy.manifest_record()
    assert manifest["compiler_name"] == (
        "opnorm_hconst_default_sandwich_match_collapse_postedge8_d14vc5_frontier_multitarget20"
    )
    assert manifest["template_current_union_increment"] == 1
    assert manifest["template_current_conflict_increment"] == 0
    assert manifest["template_current_profile"] == "unit-profile-v24.json"
    assert manifest["template_remote_smoke_status"] == "accepted_20_of_20"
    assert manifest["template_source_shapes"] == ["unit-source"]
    assert manifest["template_source_shape_count"] == 1
    assert manifest["template_source_counts_by_shape"] == {"unit-source": 1}
    assert manifest["template_target_shape_count"] == 4
    assert manifest["template_shape_counts"] == {"unit-source -> unit-target": 1}
    assert manifest["template_after_merge_projection_against_current_summary"] == {
        "conflict_count": 0,
        "deterministic_true_covered": 1365748955,
        "unresolved_estimate": 166492867,
    }


def test_opnorm_hconst_default_sandwich_postedge8_exact_top10_combined_tail_strategy_loads_compiler_pair_cache(
    tmp_path,
):
    equations_path = tmp_path / "eq_size5.txt"
    equations_path.write_text(
        "\n".join(
            [
                "x * y = y * (x * x)",
                "x * (y * z) = y * (x * x)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    pair_index = ids_to_pair_index(1, 2, law_count=2)
    pair_index_cache = tmp_path / "pair_indexes.txt"
    pair_index_cache.write_text(f"{pair_index}\n", encoding="ascii")
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(
            {
                "after_merge_projection": {
                    "conflict_count": 0,
                    "deterministic_true_covered": 1366426483,
                    "unresolved_estimate": 165814339,
                },
                "coverage_profile": "unit-profile-v25.json",
                "delta_against_current_profile_v25": {
                    "union_increment": 1,
                    "conflict_increment": 0,
                },
                "hit_stratum_counts": {"order5_source_to_order5_target": 1},
                "remote_smoke_accepted_count": 10,
                "remote_smoke_summary_paths": ["unit-smoke.json"],
                "remote_smoke_total_count": 10,
                "shape_counts": {"unit-source -> unit-target": 1},
                "source_shape_count": 1,
                "source_shapes": ["unit-source"],
                "source_counts_by_shape": {"unit-source": 1},
                "target_shape_count": 1,
                "target_shapes": ["unit-target"],
                "top_source_hit_counts": [{"source_id": 1, "hit_count": 1}],
                "source_hits_paths": ["unit-hits.jsonl"],
                "representative_pairs": [{"eq1_id": 1, "eq2_id": 2}],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    strategy = strategy_registry_module._build_opnorm_hconst_default_sandwich_postedge8_exact_top10_combined_tail_strategy(
        equations_path=equations_path,
        pair_index_cache_path=pair_index_cache,
        register_summary_path=summary,
    )

    assert (
        strategy.strategy_key
        == OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE8_EXACT_TOP10_COMBINED_TAIL_STRATEGY_KEY
    )
    assert strategy.coverage_rule.coverage_kind == "compiler_pair_indexes"
    assert strategy.coverage_rule.covers(1, 2)
    assert not strategy.coverage_rule.covers(2, 1)
    manifest = strategy.manifest_record()
    assert manifest["compiler_name"] == (
        "opnorm_hconst_default_sandwich_match_collapse_postedge8_exact_top10_combined_tail"
    )
    assert manifest["template_current_union_increment"] == 1
    assert manifest["template_current_conflict_increment"] == 0
    assert manifest["template_current_profile"] == "unit-profile-v25.json"
    assert manifest["template_remote_smoke_status"] == "accepted_10_of_10"
    assert manifest["template_source_shapes"] == ["unit-source"]
    assert manifest["template_source_shape_count"] == 1
    assert manifest["template_source_counts_by_shape"] == {"unit-source": 1}
    assert manifest["template_target_shape_count"] == 1
    assert manifest["template_shape_counts"] == {"unit-source -> unit-target": 1}
    assert manifest["template_after_merge_projection_against_current_summary"] == {
        "conflict_count": 0,
        "deterministic_true_covered": 1366426483,
        "unresolved_estimate": 165814339,
    }


def test_opnorm_hconst_default_sandwich_round30_cumulative_hconst_family_strategy_loads_compiler_pair_cache(
    tmp_path,
):
    equations_path = tmp_path / "eq_size5.txt"
    equations_path.write_text(
        "\n".join(
            [
                "x * y = y * (x * x)",
                "x * (y * z) = y * (x * x)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    pair_index = ids_to_pair_index(1, 2, law_count=2)
    pair_index_cache = tmp_path / "pair_indexes.txt"
    pair_index_cache.write_text(f"{pair_index}\n", encoding="ascii")
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(
            {
                "after_merge_projection_if_controller_accepts_cumulative_batch": {
                    "conflict_count": 0,
                    "deterministic_false_covered": 2383452378,
                    "deterministic_true_covered": 1369895240,
                    "unresolved_estimate": 162345582,
                },
                "candidate_roots": ["unit-root-summary.json"],
                "coverage_profile": "unit-profile-v26.json",
                "current_v26_delta": {
                    "union_increment": 1,
                    "conflict_increment": 0,
                },
                "pair_index_stats": {
                    "candidate_file_count": 2,
                    "hit_path_count": 4,
                    "missing_pair_index_count": 0,
                    "summary_count": 3,
                    "unique_pair_index_count": 1,
                },
                "remote_smoke_evidence": {"unit_component": "accepted_1_of_1"},
                "remote_smoke": {
                    "accepted_count_total": 1,
                    "total_count": 1,
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    strategy = strategy_registry_module._build_opnorm_hconst_default_sandwich_round30_cumulative_hconst_family_strategy(
        equations_path=equations_path,
        pair_index_cache_path=pair_index_cache,
        register_summary_path=summary,
    )

    assert (
        strategy.strategy_key
        == OPNORM_HCONST_DEFAULT_SANDWICH_ROUND30_CUMULATIVE_HCONST_FAMILY_STRATEGY_KEY
    )
    assert strategy.coverage_rule.coverage_kind == "compiler_pair_indexes"
    assert strategy.coverage_rule.covers(1, 2)
    assert not strategy.coverage_rule.covers(2, 1)
    manifest = strategy.manifest_record()
    assert manifest["compiler_name"] == (
        "opnorm_hconst_default_sandwich_match_collapse_round30_cumulative_hconst_family"
    )
    assert manifest["template_current_union_increment"] == 1
    assert manifest["template_current_conflict_increment"] == 0
    assert manifest["template_current_profile"] == "unit-profile-v26.json"
    assert manifest["template_remote_smoke_status"] == "accepted_1_of_1"
    assert manifest["template_remote_smoke_evidence"] == {
        "unit_component": "accepted_1_of_1"
    }
    assert manifest["template_remote_smoke"] == {
        "accepted_count_total": 1,
        "total_count": 1,
    }
    assert manifest["template_candidate_roots"] == ["unit-root-summary.json"]
    assert manifest["template_pair_index_stats"] == {
        "candidate_file_count": 2,
        "hit_path_count": 4,
        "missing_pair_index_count": 0,
        "summary_count": 3,
        "unique_pair_index_count": 1,
    }
    assert manifest["template_after_merge_projection_against_current_summary"] == {
        "conflict_count": 0,
        "deterministic_false_covered": 2383452378,
        "deterministic_true_covered": 1369895240,
        "unresolved_estimate": 162345582,
    }


def test_opnorm_hconst_registry_judge_code_wraps_compiler():
    code = opnorm_hconst_match_collapse_true_judge_code(
        "x * y = z * (((x * w) * u) * w)",
        "x * x = y * ((z * (z * x)) * z)",
    )

    assert "def submission : Goal := by" in code
    assert "have hconst" in code


def test_opnorm_hconst_sandwich_registry_judge_code_wraps_compiler():
    code = opnorm_hconst_sandwich_true_judge_code(
        "x * y = y * (y * (y * (z * w)))",
        "x * y = z * (z * (y * (z * z)))",
    )

    assert "def submission : Goal := by" in code
    assert "have hconst" in code


def test_opnorm_hconst_default_sandwich_registry_judge_code_wraps_compiler():
    code = opnorm_hconst_default_sandwich_true_judge_code(
        "x * y = z * ((y * (w * w)) * u)",
        "x * y = ((z * (x * z)) * x) * x",
    )

    assert "def submission : Goal := by" in code
    assert "have hconst" in code


def test_opnorm_hconst_registered_pair_is_discoverable_from_default_cache():
    strategy_ids = find_true_strategy_ids_for_pair(3277, 41620)

    assert f"{OPNORM_HCONST_MATCH_COLLAPSE_STRATEGY_KEY}.v1" in strategy_ids


def test_opnorm_hconst_sandwich_registered_pair_is_discoverable_from_default_cache():
    strategy_ids = find_true_strategy_ids_for_pair(41938, 3270)

    assert f"{OPNORM_HCONST_SANDWICH_STRATEGY_KEY}.v1" in strategy_ids


def test_opnorm_hconst_lmrm_mainline_registered_pair_is_discoverable_from_default_cache():
    strategy_ids = find_true_strategy_ids_for_pair(42816, 3257)

    assert f"{OPNORM_HCONST_LMRM_MAINLINE_STRATEGY_KEY}.v1" in strategy_ids


def test_opnorm_hconst_varmul_top01_registered_pair_is_discoverable_from_default_cache():
    strategy_ids = find_true_strategy_ids_for_pair(519, 472)

    assert f"{OPNORM_HCONST_VARMUL_TOP01_STRATEGY_KEY}.v1" in strategy_ids


def test_opnorm_hconst_default_sandwich_top16_pair_is_discoverable_from_default_cache():
    strategy_ids = find_true_strategy_ids_for_pair(41990, 42460)

    assert f"{OPNORM_HCONST_DEFAULT_SANDWICH_TOP16_STRATEGY_KEY}.v1" in strategy_ids


def test_opnorm_hconst_default_sandwich_d14vc4_pair_is_discoverable_from_default_cache():
    strategy_ids = find_true_strategy_ids_for_pair(41981, 41590)

    assert f"{OPNORM_HCONST_DEFAULT_SANDWICH_D14VC4_STRATEGY_KEY}.v1" in strategy_ids


def test_opnorm_hconst_default_sandwich_d13vc4_pair_is_discoverable_from_default_cache():
    strategy_ids = find_true_strategy_ids_for_pair(3369, 53831)

    assert f"{OPNORM_HCONST_DEFAULT_SANDWICH_D13VC4_STRATEGY_KEY}.v1" in strategy_ids


def test_opnorm_hconst_default_sandwich_d14vc4_targetext_pair_is_discoverable_from_default_cache():
    strategy_ids = find_true_strategy_ids_for_pair(41981, 53824)

    assert (
        f"{OPNORM_HCONST_DEFAULT_SANDWICH_D14VC4_TARGETEXT_STRATEGY_KEY}.v1"
        in strategy_ids
    )


def test_opnorm_hconst_default_sandwich_lowvc_extension_pair_is_discoverable_from_default_cache():
    strategy_ids = find_true_strategy_ids_for_pair(41935, 53831)

    assert (
        f"{OPNORM_HCONST_DEFAULT_SANDWICH_LOWVC_EXTENSION_STRATEGY_KEY}.v1"
        in strategy_ids
    )


def test_opnorm_hconst_default_sandwich_topbucket_extension_pair_is_discoverable_from_default_cache():
    strategy_ids = find_true_strategy_ids_for_pair(41990, 41590)

    assert (
        f"{OPNORM_HCONST_DEFAULT_SANDWICH_TOPBUCKET_EXTENSION_STRATEGY_KEY}.v1"
        in strategy_ids
    )


def test_opnorm_hconst_default_sandwich_frontier_extension_pair_is_discoverable_from_default_cache():
    strategy_ids = find_true_strategy_ids_for_pair(3369, 53824)

    assert (
        f"{OPNORM_HCONST_DEFAULT_SANDWICH_FRONTIER_EXTENSION_STRATEGY_KEY}.v1"
        in strategy_ids
    )


def test_opnorm_hconst_default_sandwich_edge_extension_pair_is_discoverable_from_default_cache():
    strategy_ids = find_true_strategy_ids_for_pair(3378, 41590)

    assert (
        f"{OPNORM_HCONST_DEFAULT_SANDWICH_EDGE_EXTENSION_STRATEGY_KEY}.v1"
        in strategy_ids
    )


def test_opnorm_hconst_default_sandwich_postedge_top40_extension_pair_is_discoverable_from_default_cache():
    strategy_ids = find_true_strategy_ids_for_pair(3357, 41543)

    assert (
        f"{OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE_TOP40_EXTENSION_STRATEGY_KEY}.v1"
        in strategy_ids
    )


def test_opnorm_hconst_default_sandwich_postedge2_top60_extension_pair_is_discoverable_from_default_cache():
    strategy_ids = find_true_strategy_ids_for_pair(516, 49480)

    assert (
        f"{OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE2_TOP60_EXTENSION_STRATEGY_KEY}.v1"
        in strategy_ids
    )


def test_opnorm_hconst_default_sandwich_postedge3_top80_extension_pair_is_discoverable_from_default_cache():
    strategy_ids = find_true_strategy_ids_for_pair(41935, 41583)

    assert (
        f"{OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE3_TOP80_EXTENSION_STRATEGY_KEY}.v1"
        in strategy_ids
    )


def test_opnorm_hconst_default_sandwich_postedge4_top100_extension_pair_is_discoverable_from_default_cache():
    strategy_ids = find_true_strategy_ids_for_pair(3357, 41536)

    assert (
        f"{OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE4_TOP100_EXTENSION_STRATEGY_KEY}.v1"
        in strategy_ids
    )


def test_opnorm_hconst_default_sandwich_postedge5_top120_extension_pair_is_discoverable_from_default_cache():
    strategy_ids = find_true_strategy_ids_for_pair(516, 51260)

    assert (
        f"{OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE5_TOP120_EXTENSION_STRATEGY_KEY}.v1"
        in strategy_ids
    )


def test_opnorm_hconst_default_sandwich_postedge6_samplehit_top20_tail_pair_is_discoverable_from_default_cache():
    strategy_ids = find_true_strategy_ids_for_pair(3763, 59992)

    assert (
        f"{OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE6_SAMPLEHIT_TOP20_TAIL_STRATEGY_KEY}.v1"
        in strategy_ids
    )


def test_opnorm_hconst_default_sandwich_postedge7_samplehit_top20_tail_pair_is_discoverable_from_default_cache():
    strategy_ids = find_true_strategy_ids_for_pair(3368, 53824)

    assert (
        f"{OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE7_SAMPLEHIT_TOP20_TAIL_STRATEGY_KEY}.v1"
        in strategy_ids
    )


def test_opnorm_hconst_default_sandwich_postedge8_d14vc5_frontier_multitarget20_pair_is_discoverable_from_default_cache():
    strategy_ids = find_true_strategy_ids_for_pair(41990, 53824)

    assert (
        f"{OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE8_D14VC5_FRONTIER_MULTITARGET20_STRATEGY_KEY}.v1"
        in strategy_ids
    )


def test_opnorm_hconst_default_sandwich_postedge8_exact_top10_combined_tail_pair_is_discoverable_from_default_cache():
    strategy_ids = find_true_strategy_ids_for_pair(41935, 4281)

    assert (
        f"{OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE8_EXACT_TOP10_COMBINED_TAIL_STRATEGY_KEY}.v1"
        in strategy_ids
    )


def test_opnorm_hconst_default_sandwich_round30_cumulative_hconst_family_pair_is_discoverable_from_default_cache():
    strategy_ids = find_true_strategy_ids_for_pair(3357, 53854)

    assert (
        f"{OPNORM_HCONST_DEFAULT_SANDWICH_ROUND30_CUMULATIVE_HCONST_FAMILY_STRATEGY_KEY}.v1"
        in strategy_ids
    )


def test_opnorm_hconst_plus_hstep_tail_pair_is_discoverable_from_default_cache():
    strategy_ids = find_true_strategy_ids_for_pair(317, 55594)

    assert (
        f"{OPNORM_HCONST_PLUS_HSTEP_D14VC4_V17_TAIL_STRATEGY_KEY}.v1"
        in strategy_ids
    )


def test_opnorm_hconst_compiler_does_not_match_top16_false_countermodels():
    false_rows = [
        ("x * x = y * ((z * (w * u)) * u)", "x * x = y * (x * ((z * x) * y))"),
        ("x * x = (y * (z * (w * u))) * w", "x * x = (((y * x) * x) * z) * y"),
    ]

    for source_equation, target_equation in false_rows:
        assert not matches_hconst_match_collapse(
            source_equation,
            target_equation,
            max_candidates=10,
        )
        assert (
            render_first_hconst_match_collapse_certificate(
                source_equation,
                target_equation,
                max_candidates=10,
            )
            is None
        )


def test_opnorm_hconst_sandwich_compiler_does_not_match_top16_false_countermodels():
    false_rows = [
        ("x * x = y * ((z * (w * u)) * u)", "x * x = y * (x * ((z * x) * y))"),
        ("x * x = (y * (z * (w * u))) * w", "x * x = (((y * x) * x) * z) * y"),
    ]

    for source_equation, target_equation in false_rows:
        assert not matches_hconst_sandwich_match_collapse(
            source_equation,
            target_equation,
            max_candidates=5,
            max_h_instantiations=50_000,
        )
        assert not matches_hconst_default_sandwich_match_collapse(
            source_equation,
            target_equation,
            max_candidates=5,
        )
        assert not matches_hstep_default_sandwich_match_collapse(
            source_equation,
            target_equation,
            max_candidates=5,
        )


def test_opnorm_hconst_scan_sample_finds_embedded_candidate(tmp_path):
    sample = tmp_path / "sample.jsonl"
    sample.write_text(
        json.dumps(
            {
                "source_id": 1,
                "target_id": 2,
                "source_equation": "x * y = z * (((x * w) * u) * w)",
                "target_equation": "x * x = y * ((z * (z * x)) * z)",
                "shape_bucket": "roots=mul>mul",
                "stratum": "unit",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    hits, summary = scan_sample(
        sample,
        equations={},
        require_mul_roots=True,
        max_candidates_per_pair=10,
    )

    assert [(hit["eq1_id"], hit["eq2_id"]) for hit in hits] == [(1, 2)]
    assert summary["stats"]["compiler_hit_count"] == 1
    assert summary["hit_stratum_counts"] == {"unit": 1}


def test_opnorm_explicit_hits_delta_uses_profile_groups():
    law_count = 8
    profile = {
        "law_count": law_count,
        "verdict_profiles": {
            "true": {
                "source_target_groups": [
                    {
                        "source_count": 1,
                        "target_count": 1,
                        "source_bitset_base64": _encode_ids_bitset(
                            [1],
                            law_count=law_count,
                        ),
                        "target_bitset_base64": _encode_ids_bitset(
                            [2],
                            law_count=law_count,
                        ),
                    }
                ],
                "explicit_source_target_groups": [
                    {
                        "source_id": 3,
                        "target_count": 1,
                        "target_bitset_base64": _encode_ids_bitset(
                            [4],
                            law_count=law_count,
                        ),
                    }
                ],
            },
            "false": {
                "source_target_groups": [
                    {
                        "source_count": 1,
                        "target_count": 1,
                        "source_bitset_base64": _encode_ids_bitset(
                            [5],
                            law_count=law_count,
                        ),
                        "target_bitset_base64": _encode_ids_bitset(
                            [6],
                            law_count=law_count,
                        ),
                    }
                ],
                "explicit_source_target_groups": [],
            },
        },
    }
    hits = [
        {"eq1_id": 1, "eq2_id": 2},
        {"eq1_id": 3, "eq2_id": 4},
        {"eq1_id": 5, "eq2_id": 6},
        {"eq1_id": 7, "eq2_id": 8},
    ]

    delta = explicit_hits_delta_from_profile(profile, hits, verdict=True)

    assert delta["raw_coverage"] == 4
    assert delta["same_verdict_overlap"] == 2
    assert delta["opposite_verdict_overlap"] == 1
    assert delta["conflict_increment"] == 1
    assert delta["union_increment"] == 2
    assert delta["total_deterministic_increment"] == 0
