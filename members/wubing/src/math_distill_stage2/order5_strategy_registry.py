from __future__ import annotations

import ast
import base64
import hashlib
import json
import re
import time
from dataclasses import dataclass, field, replace
from functools import lru_cache
from itertools import combinations, product
from pathlib import Path
from typing import Iterable, Sequence, Union

from math_distill_stage2.counterexample.finite_magma import FiniteMagma
from math_distill_stage2.equations import Equation, Expr, parse_equation
from math_distill_stage2.lean_certificates import lean_expr
from math_distill_stage2.order5_opnorm_match_collapse import (
    render_first_hconst_default_sandwich_match_collapse_certificate,
    render_first_hconst_match_collapse_certificate,
    render_first_hconst_sandwich_match_collapse_certificate,
    render_first_hstep_default_sandwich_match_collapse_certificate,
)
from math_distill_stage2.order5_pair_space import (
    ids_to_pair_index,
    pair_count,
    pair_index_to_ids,
)
from math_distill_stage2.order5_spine_smoke import (
    DEFAULT_EQ_SIZE5_PATH,
    DEFAULT_ORDER4_MAX_ID,
    load_equation_spine_features,
)


DEFAULT_OUTPUT_DIR = Path("data/processed/order5_strategy_registry")
DEFAULT_SOURCE_TARGET_CACHE_PATH = Path(
    "data/processed/order5_strategy_registry/setcheck_source_target_cache.jsonl"
)
DEFAULT_PAIRCHECK_BANK_PATH = Path(
    "data/processed/order5_paircheck_bank/merged_v1/registry_ready_bank.jsonl"
)
DEFAULT_SETCHECK_BANK_PATH = Path(
    "data/processed/order5_strategy_registry/discovered_setcheck_bank.jsonl"
)
DEFAULT_PREDICATECHECK_BANK_PATH = Path(
    "data/processed/order5_strategy_registry/discovered_predicatecheck_bank.jsonl"
)
DEFAULT_PRODUCT_ANCHOR_SEED_LIFT_CANDIDATE_JSONL = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_candidates_20260520_product_anchor_seed_lift_tail.jsonl"
)
DEFAULT_OPNORM_HCONST_MATCH_COLLAPSE_PAIR_INDEX_CACHE = Path(
    "data/processed/order5_strategy_registry/"
    "opnorm_hconst_match_collapse_top16_top13_top12_top08_pair_indexes_20260521.txt"
)
DEFAULT_OPNORM_HCONST_MATCH_COLLAPSE_REGISTER_SUMMARY = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_opnorm_hconst_shape_top16_top13_top12_top08_"
    "register_pair_index_cache_20260521_summary.json"
)
DEFAULT_OPNORM_HCONST_SANDWICH_PAIR_INDEX_CACHE = Path(
    "data/processed/order5_strategy_registry/"
    "opnorm_hconst_sandwich_yyleft_repfilter_targetbatch_pair_indexes_20260521.txt"
)
DEFAULT_OPNORM_HCONST_SANDWICH_REGISTER_SUMMARY = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_opnorm_hconst_sandwich_yyleft_repfilter_targetbatch_"
    "register_pair_index_cache_20260521_summary.json"
)
DEFAULT_OPNORM_HCONST_LMRM_MAINLINE_PAIR_INDEX_CACHE = Path(
    "data/processed/order5_strategy_registry/"
    "opnorm_hconst_lmrm_mainline_pair_indexes_20260521.txt"
)
DEFAULT_OPNORM_HCONST_LMRM_MAINLINE_REGISTER_SUMMARY = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_opnorm_hconst_lmrm_mainline_register_pair_index_cache_"
    "20260521_summary.json"
)
DEFAULT_OPNORM_HCONST_VARMUL_TOP01_PAIR_INDEX_CACHE = Path(
    "data/processed/order5_strategy_registry/"
    "opnorm_hconst_varmul_top01_source0000_0500_pair_indexes_20260521.txt"
)
DEFAULT_OPNORM_HCONST_VARMUL_TOP01_REGISTER_SUMMARY = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_opnorm_hconst_varmul_top01_source0000_0500_"
    "register_pair_index_cache_20260521_summary.json"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_TOP16_PAIR_INDEX_CACHE = Path(
    "data/processed/order5_strategy_registry/"
    "opnorm_hconst_default_sandwich_top16_fullshape_pair_indexes_20260521.txt"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_TOP16_REGISTER_SUMMARY = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_opnorm_hconst_default_sandwich_top16_fullshape_"
    "register_pair_index_cache_20260521_summary.json"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_D14VC4_PAIR_INDEX_CACHE = Path(
    "data/processed/order5_strategy_registry/"
    "opnorm_hconst_default_sandwich_d14vc4_multitarget_pair_indexes_20260521.txt"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_D14VC4_REGISTER_SUMMARY = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_opnorm_hconst_default_sandwich_d14vc4_multitarget_"
    "register_pair_index_cache_20260521_summary.json"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_D13VC4_PAIR_INDEX_CACHE = Path(
    "data/processed/order5_strategy_registry/"
    "opnorm_hconst_default_sandwich_d13vc4_multitarget_pair_indexes_20260521.txt"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_D13VC4_REGISTER_SUMMARY = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_opnorm_hconst_default_sandwich_d13vc4_multitarget_"
    "register_pair_index_cache_20260521_summary.json"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_D14VC4_TARGETEXT_PAIR_INDEX_CACHE = Path(
    "data/processed/order5_strategy_registry/"
    "opnorm_hconst_default_sandwich_d14vc4_targetext_pair_indexes_20260521.txt"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_D14VC4_TARGETEXT_REGISTER_SUMMARY = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_opnorm_hconst_default_sandwich_d14vc4_targetext_"
    "register_pair_index_cache_20260521_summary.json"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_LOWVC_EXTENSION_PAIR_INDEX_CACHE = Path(
    "data/processed/order5_strategy_registry/"
    "opnorm_hconst_default_sandwich_lowvc_extension_pair_indexes_20260521.txt"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_LOWVC_EXTENSION_REGISTER_SUMMARY = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_opnorm_hconst_default_sandwich_lowvc_extension_"
    "register_pair_index_cache_20260521_summary.json"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_TOPBUCKET_EXTENSION_PAIR_INDEX_CACHE = Path(
    "data/processed/order5_strategy_registry/"
    "opnorm_hconst_default_sandwich_topbucket_extension_pair_indexes_20260522.txt"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_TOPBUCKET_EXTENSION_REGISTER_SUMMARY = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_opnorm_hconst_default_sandwich_topbucket_extension_"
    "register_pair_index_cache_20260522_summary.json"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_FRONTIER_EXTENSION_PAIR_INDEX_CACHE = Path(
    "data/processed/order5_strategy_registry/"
    "opnorm_hconst_default_sandwich_frontier_extension_pair_indexes_20260522.txt"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_FRONTIER_EXTENSION_REGISTER_SUMMARY = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_opnorm_hconst_default_sandwich_frontier_extension_"
    "register_pair_index_cache_20260522_summary.json"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_EDGE_EXTENSION_PAIR_INDEX_CACHE = Path(
    "data/processed/order5_strategy_registry/"
    "opnorm_hconst_default_sandwich_edge_extension_pair_indexes_20260522.txt"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_EDGE_EXTENSION_REGISTER_SUMMARY = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_opnorm_hconst_default_sandwich_edge_extension_"
    "register_pair_index_cache_20260522_summary.json"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE_TOP40_EXTENSION_PAIR_INDEX_CACHE = Path(
    "data/processed/order5_strategy_registry/"
    "opnorm_hconst_default_sandwich_postedge_top40_extension_pair_indexes_20260522.txt"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE_TOP40_EXTENSION_REGISTER_SUMMARY = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_opnorm_hconst_default_sandwich_postedge_top40_extension_"
    "register_pair_index_cache_20260522_summary.json"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE2_TOP60_EXTENSION_PAIR_INDEX_CACHE = Path(
    "data/processed/order5_strategy_registry/"
    "opnorm_hconst_default_sandwich_postedge2_top60_extension_pair_indexes_20260522.txt"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE2_TOP60_EXTENSION_REGISTER_SUMMARY = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_opnorm_hconst_default_sandwich_postedge2_top60_extension_"
    "register_pair_index_cache_20260522_summary.json"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE3_TOP80_EXTENSION_PAIR_INDEX_CACHE = Path(
    "data/processed/order5_strategy_registry/"
    "opnorm_hconst_default_sandwich_postedge3_top80_extension_pair_indexes_20260522.txt"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE3_TOP80_EXTENSION_REGISTER_SUMMARY = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_opnorm_hconst_default_sandwich_postedge3_top80_extension_"
    "register_pair_index_cache_20260522_summary.json"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE4_TOP100_EXTENSION_PAIR_INDEX_CACHE = Path(
    "data/processed/order5_strategy_registry/"
    "opnorm_hconst_default_sandwich_postedge4_top100_extension_pair_indexes_20260522.txt"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE4_TOP100_EXTENSION_REGISTER_SUMMARY = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_opnorm_hconst_default_sandwich_postedge4_top100_extension_"
    "register_pair_index_cache_20260522_summary.json"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE5_TOP120_EXTENSION_PAIR_INDEX_CACHE = Path(
    "data/processed/order5_strategy_registry/"
    "opnorm_hconst_default_sandwich_postedge5_top120_extension_pair_indexes_20260522.txt"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE5_TOP120_EXTENSION_REGISTER_SUMMARY = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_opnorm_hconst_default_sandwich_postedge5_top120_extension_"
    "register_pair_index_cache_20260522_summary.json"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE6_SAMPLEHIT_TOP20_TAIL_PAIR_INDEX_CACHE = Path(
    "data/processed/order5_strategy_registry/"
    "opnorm_hconst_default_sandwich_postedge6_samplehit_top20_tail_pair_indexes_20260522.txt"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE6_SAMPLEHIT_TOP20_TAIL_REGISTER_SUMMARY = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_opnorm_hconst_default_sandwich_postedge6_samplehit_top20_tail_"
    "full_v22_20260522_summary.json"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE7_SAMPLEHIT_TOP20_TAIL_PAIR_INDEX_CACHE = Path(
    "data/processed/order5_strategy_registry/"
    "opnorm_hconst_default_sandwich_postedge7_samplehit_top20_tail_pair_indexes_20260522.txt"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE7_SAMPLEHIT_TOP20_TAIL_REGISTER_SUMMARY = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_opnorm_hconst_default_sandwich_postedge7_samplehit_top20_tail_"
    "full_v23_20260522_summary.json"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE8_D14VC5_FRONTIER_MULTITARGET20_PAIR_INDEX_CACHE = Path(
    "data/processed/order5_strategy_registry/"
    "opnorm_hconst_default_sandwich_postedge8_d14vc5_frontier_multitarget20_"
    "pair_indexes_20260522.txt"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE8_D14VC5_FRONTIER_MULTITARGET20_REGISTER_SUMMARY = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_opnorm_hconst_default_sandwich_postedge8_d14vc5_"
    "frontier_multitarget20_full_v24_20260522_summary.json"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE8_EXACT_TOP10_COMBINED_TAIL_PAIR_INDEX_CACHE = Path(
    "data/processed/order5_strategy_registry/"
    "opnorm_hconst_default_sandwich_postedge8_exact_top10_combined_tail_"
    "pair_indexes_20260522.txt"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE8_EXACT_TOP10_COMBINED_TAIL_REGISTER_SUMMARY = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_opnorm_hconst_default_sandwich_postedge8_exact_top10_"
    "combined_tail_register_pair_index_cache_20260522_summary.json"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_ROUND30_CUMULATIVE_HCONST_FAMILY_PAIR_INDEX_CACHE = Path(
    "data/processed/order5_strategy_registry/"
    "opnorm_hconst_default_sandwich_round30_cumulative_hconst_family_"
    "pair_indexes_20260524.txt"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_ROUND30_CUMULATIVE_HCONST_FAMILY_REGISTER_SUMMARY = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "controller_round30_hconst_cumulative_v26_delta_audit_20260524_summary.json"
)
DEFAULT_OPNORM_HCONST_MATCH_GE25K_TAIL_BATCH_PAIR_INDEX_CACHE = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_opnorm_hconst_match_ge25k_tail_batch_pair_indexes_20260527.txt"
)
DEFAULT_OPNORM_HCONST_MATCH_GE25K_TAIL_BATCH_REGISTER_SUMMARY = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_candidates_20260527_opnorm_hconst_match_ge25k_tail_batch_summary.json"
)
DEFAULT_OPNORM_HCONST_MATCH_GE10_TAIL_EXTENSION_PAIR_INDEX_CACHE = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_opnorm_hconst_match_ge10_tail_extension_pair_indexes_20260527.txt"
)
DEFAULT_OPNORM_HCONST_MATCH_GE10_TAIL_EXTENSION_REGISTER_SUMMARY = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_candidates_20260527_opnorm_hconst_match_ge10_tail_extension_summary.json"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_GE25_LT100_TAIL_BATCH_PAIR_INDEX_CACHE = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_opnorm_hconst_default_sandwich_ge25_lt100_tail_batch_pair_indexes_20260527.txt"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_GE25_LT100_TAIL_BATCH_REGISTER_SUMMARY = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_candidates_20260527_opnorm_hconst_default_sandwich_ge25_lt100_tail_batch_summary.json"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_LT25_REMAINING_TAIL_BATCH_PAIR_INDEX_CACHE = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_opnorm_hconst_default_sandwich_lt25_remaining_tail_batch_pair_indexes_20260527.txt"
)
DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_LT25_REMAINING_TAIL_BATCH_REGISTER_SUMMARY = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_candidates_20260527_opnorm_hconst_default_sandwich_lt25_remaining_tail_batch_summary.json"
)
DEFAULT_HINST_GROUND_CC_ACCEPTED_FAMILY_ROLLUP_PAIR_INDEX_CACHE = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_hinst_ground_cc_accepted_family_rollup_pair_indexes_20260528.txt"
)
DEFAULT_HINST_GROUND_CC_ACCEPTED_FAMILY_ROLLUP_REGISTER_SUMMARY = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_candidates_20260528_hinst_ground_cc_accepted_family_rollup_summary.json"
)
DEFAULT_OPNORM_HCONST_PLUS_HSTEP_D14VC4_V17_TAIL_PAIR_INDEX_CACHE = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_opnorm_hconst_plus_hstep_d14vc4_v17_tail_combined_pair_indexes_20260527.txt"
)
DEFAULT_OPNORM_HCONST_PLUS_HSTEP_D14VC4_V17_TAIL_REGISTER_SUMMARY = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_candidates_20260528_hconst_plus_hstep_v29_main_gate_packet_summary.json"
)
DEFAULT_PROOFBENCH_ONE_SIDED_CONSTANCY_EXPLICIT_NF_ACCEPTED_CANDIDATE_JSONL = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_candidates_20260528_proofbench_syntactic_one_sided_constancy_"
    "explicit_nf_accepted.jsonl"
)
DEFAULT_PROOFBENCH_ONE_SIDED_CONSTANCY_EXPLICIT_NF_ACCEPTED_SUMMARY = Path(
    "data/processed/order5_strategy_registry/candidates/"
    "true_template_candidates_20260528_proofbench_syntactic_one_sided_constancy_"
    "explicit_nf_accepted_summary.json"
)
PAIRCHECK_BANK_STRATEGY_KEY = "false.finmodel.paircheck.bank"
SETCHECK_BANK_STRATEGY_KEY_PREFIX = "false.finmodel.setcheck.bank"
PREDICATECHECK_BANK_STRATEGY_KEY_PREFIX = "false.finmodel.predicatecheck.bank"
MODEL_FAMILY_PREDICATECHECK_STRATEGY_KEY_PREFIX = (
    "false.finmodel.predicatecheck.model_family.residual_20260519_top1"
)
STRUCTURED_AFFINE_MOD5_A3_B2_C0_STRATEGY_KEY = (
    "false.finmodel.setcheck.structured.affine_mod5_a3_b2_c0.all_equations"
)
STRUCTURED_AFFINE_MOD5_A2_B3_C0_STRATEGY_KEY = (
    "false.finmodel.setcheck.structured.affine_mod5_a2_b3_c0.all_equations"
)
STRUCTURED_AFFINE_MOD4_A0_B1_C1_STRATEGY_KEY = (
    "false.finmodel.setcheck.structured.affine_mod4_a0_b1_c1.all_equations"
)
STRUCTURED_AFFINE_MOD4_A1_B0_C3_STRATEGY_KEY = (
    "false.finmodel.setcheck.structured.affine_mod4_a1_b0_c3.all_equations"
)
STRUCTURED_AFFINE_MOD5_A0_B1_C4_STRATEGY_KEY = (
    "false.finmodel.setcheck.structured.affine_mod5_a0_b1_c4.all_equations"
)
STRUCTURED_AFFINE_MOD5_A1_B0_C4_STRATEGY_KEY = (
    "false.finmodel.setcheck.structured.affine_mod5_a1_b0_c4.all_equations"
)
STRUCTURED_AFFINE_MOD5_A1_B3_C4_STRATEGY_KEY = (
    "false.finmodel.setcheck.structured.affine_mod5_a1_b3_c4.all_equations"
)
STRUCTURED_AFFINE_MOD5_A3_B1_C4_STRATEGY_KEY = (
    "false.finmodel.setcheck.structured.affine_mod5_a3_b1_c4.all_equations"
)
STRUCTURED_AFFINE_MOD7_A1_B3_C6_STRATEGY_KEY = (
    "false.finmodel.setcheck.structured.affine_mod7_a1_b3_c6.all_equations"
)
STRUCTURED_AFFINE_MOD7_A3_B1_C6_STRATEGY_KEY = (
    "false.finmodel.setcheck.structured.affine_mod7_a3_b1_c6.all_equations"
)
STRUCTURED_AFFINE_MOD4_A3_B2_C3_STRATEGY_KEY = (
    "false.finmodel.setcheck.structured.affine_mod4_a3_b2_c3.all_equations"
)
STRUCTURED_AFFINE_MOD4_A2_B3_C3_STRATEGY_KEY = (
    "false.finmodel.setcheck.structured.affine_mod4_a2_b3_c3.all_equations"
)
STRUCTURED_AFFINE_MOD7_A2_B5_C6_STRATEGY_KEY = (
    "false.finmodel.setcheck.structured.affine_mod7_a2_b5_c6.all_equations"
)
STRUCTURED_AFFINE_MOD7_A5_B2_C6_STRATEGY_KEY = (
    "false.finmodel.setcheck.structured.affine_mod7_a5_b2_c6.all_equations"
)
STRUCTURED_AFFINE_MOD7_A6_B2_C0_STRATEGY_KEY = (
    "false.finmodel.setcheck.structured.affine_mod7_a6_b2_c0.all_equations"
)
STRUCTURED_ETP_ORDER4_REFUTATION516_STRATEGY_KEY = (
    "false.finmodel.setcheck.structured.etp_order4_refutation516.all_equations"
)
STRUCTURED_ETP_ORDER4_REFUTATION482_STRATEGY_KEY = (
    "false.finmodel.setcheck.structured.etp_order4_refutation482.all_equations"
)
STRUCTURED_ALL4X4_REFUTATION4_STRATEGY_KEY = (
    "false.finmodel.setcheck.structured.all4x4.refutation4.all_equations"
)
LEFT_PROJECTION_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin2_left_projection.all_equations"
)
CONSTANT_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin2_constant.all_equations"
)
RIGHT_PROJECTION_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin2_right_projection.all_equations"
)
COMPLEMENT_LEFT_PROJECTION_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin2_complement_left_projection.all_equations"
)
COMPLEMENT_RIGHT_PROJECTION_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin2_complement_right_projection.all_equations"
)
LEFT_AND_COMPLEMENT_RIGHT_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin2_left_and_complement_right.all_equations"
)
COMPLEMENT_LEFT_AND_RIGHT_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin2_complement_left_and_right.all_equations"
)
XOR_ALL_EQUATIONS_STRATEGY_KEY = "false.finmodel.setcheck.fin2_xor.all_equations"
AND_ALL_EQUATIONS_STRATEGY_KEY = "false.finmodel.setcheck.fin2_and.all_equations"
NOR_ALL_EQUATIONS_STRATEGY_KEY = "false.finmodel.setcheck.fin2_nor.all_equations"
STEINER_QUASIGROUP_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin3_steiner_quasigroup.all_equations"
)
RIGHT_MINUS_LEFT_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin3_right_minus_left.all_equations"
)
LEFT_MINUS_RIGHT_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin3_left_minus_right.all_equations"
)
FIN3_TABLE_020_110_122_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin3_table_020_110_122.all_equations"
)
LEFT_CYCLIC_SUCCESSOR_3_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin3_left_cyclic_successor.all_equations"
)
RIGHT_CYCLIC_SUCCESSOR_3_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin3_right_cyclic_successor.all_equations"
)
FIN3_TABLE_022_010_112_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin3_table_022_010_112.all_equations"
)
ADDITION_MOD3_3_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin3_addition_mod3.all_equations"
)
FIN4_TABLE_0231_3102_1320_2013_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin4_table_0231_3102_1320_2013.all_equations"
)
FIN3_TABLE_000_211_122_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin3_table_000_211_122.all_equations"
)
FIN3_TABLE_012_012_102_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin3_table_012_012_102.all_equations"
)
FIN3_TABLE_011_012_012_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin3_table_011_012_012.all_equations"
)
FIN3_TABLE_000_110_222_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin3_table_000_110_222.all_equations"
)
FIN3_TABLE_122_020_110_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin3_table_122_020_110.all_equations"
)
FIN3_TABLE_002_112_102_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin3_table_002_112_102.all_equations"
)
FIN3_TABLE_011_012_110_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin3_table_011_012_110.all_equations"
)
FIN4_TABLE_2013_3102_0231_1320_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin4_table_2013_3102_0231_1320.all_equations"
)
FIN4_TABLE_0011_2233_0011_2233_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin4_table_0011_2233_0011_2233.all_equations"
)
FIN5_TABLE_02413_41302_30241_24130_13024_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin5_table_02413_41302_30241_24130_13024.all_equations"
)
FIN5_TABLE_03142_31420_14203_42031_20314_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin5_table_03142_31420_14203_42031_20314.all_equations"
)
FIN5_TABLE_02143_41320_34201_10432_23014_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin5_table_02143_41320_34201_10432_23014.all_equations"
)
FIN7_TABLE_0214365_3150624_4625031_6543210_5361402_2406153_1032546_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin7_table_0214365_3150624_4625031_6543210_5361402_2406153_1032546.all_equations"
)
FIN5_TABLE_31420_02341_14032_40213_23104_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin5_table_31420_02341_14032_40213_23104.all_equations"
)
FIN5_TABLE_34120_20413_01234_13042_42301_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin5_table_34120_20413_01234_13042_42301.all_equations"
)
FIN4_TABLE_1032_3210_2301_0123_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin4_table_1032_3210_2301_0123.all_equations"
)
FIN3_TABLE_000_000_001_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin3_table_000_000_001.all_equations"
)
FIN3_TABLE_000_000_010_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin3_table_000_000_010.all_equations"
)
FIN3_TABLE_000_000_020_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin3_table_000_000_020.all_equations"
)
FIN3_TABLE_000_000_100_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin3_table_000_000_100.all_equations"
)
FIN3_TABLE_001_000_000_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin3_table_001_000_000.all_equations"
)
FIN3_TABLE_000_000_011_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin3_table_000_000_011.all_equations"
)
FIN3_TABLE_000_001_001_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin3_table_000_001_001.all_equations"
)
FIN3_TABLE_000_001_010_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin3_table_000_001_010.all_equations"
)
FIN3_TABLE_000_020_001_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin3_table_000_020_001.all_equations"
)
FIN3_TABLE_000_122_122_ALL_EQUATIONS_STRATEGY_KEY = (
    "false.finmodel.setcheck.fin3_table_000_122_122.all_equations"
)
SINGLETON_COLLAPSE_ANY_TARGET_STRATEGY_KEY = (
    "true.proof.templatecheck.singleton_collapse.any_target"
)
SINGLETON_SEEDBANK_ANY_TARGET_STRATEGY_KEY = (
    "true.proof.explicitbank.singleton_seedbank.any_target"
)
SINGLETON_SEEDBANK_SPECIALIZATION_ANY_TARGET_STRATEGY_KEY = (
    "true.proof.templatecheck.singleton_seedbank_specialization.any_target"
)
SINGLETON_SUPERPOSE_ANY_TARGET_STRATEGY_KEY = (
    "true.proof.templatecheck.singleton_superpose.any_target"
)
PRODUCT_ANCHOR_ANY_PRODUCT_TARGET_STRATEGY_KEY = (
    "true.proof.templatecheck.term_shape_anchor.product.any_product_target"
)
PRODUCT_ANCHOR_SEED_LIFT_ANY_PRODUCT_TARGET_STRATEGY_KEY = (
    "true.proof.templatecheck.product_anchor_seed_lift.proofbank_tail."
    "any_product_target"
)
PRODUCT_ANCHOR_SEED_LIFT_CANDIDATE_KEY = (
    "true.proof.templatecheck.product_anchor_seed_lift.proofbank_tail.v1"
)
PRODUCT_COLLAPSE_STRATEGY_KEY_PREFIX = (
    "true.proof.templatecheck.term_shape_anchor.product_collapse"
)
LEFT_PROJECTION_NORMALIZER_ANY_TARGET_STRATEGY_KEY = (
    "true.proof.templatecheck.projection_normalizer.left.any_left_normal_target"
)
RIGHT_PROJECTION_NORMALIZER_ANY_TARGET_STRATEGY_KEY = (
    "true.proof.templatecheck.projection_normalizer.right.any_right_normal_target"
)
LEFT_SELF_ABSORPTION_INSTANCE_STRATEGY_KEY = (
    "true.proof.templatecheck.law_instance.left_self_absorption.any_instance"
)
RIGHT_SELF_ABSORPTION_INSTANCE_STRATEGY_KEY = (
    "true.proof.templatecheck.law_instance.right_self_absorption.any_instance"
)
LEFT_SANDWICH_ABSORPTION_INSTANCE_STRATEGY_KEY = (
    "true.proof.templatecheck.law_instance.left_sandwich_absorption.any_instance"
)
RIGHT_SANDWICH_ABSORPTION_INSTANCE_STRATEGY_KEY = (
    "true.proof.templatecheck.law_instance.right_sandwich_absorption.any_instance"
)
TARGET_INSTANCE_OF_SOURCE_STRATEGY_KEY = (
    "true.proof.templatecheck.law_instance.target_instance_of_source"
)
OPNORM_HCONST_MATCH_COLLAPSE_STRATEGY_KEY = (
    "true.proof.templatecheck.opnorm.hconst_match_collapse."
    "top16_top13_top12_top08"
)
OPNORM_HCONST_SANDWICH_STRATEGY_KEY = (
    "true.proof.templatecheck.opnorm.hconst_sandwich_match_collapse."
    "yyleft_repfilter_targetbatch"
)
OPNORM_HCONST_LMRM_MAINLINE_STRATEGY_KEY = (
    "true.proof.templatecheck.opnorm.hconst_match_collapse.lmrm_mainline"
)
OPNORM_HCONST_VARMUL_TOP01_STRATEGY_KEY = (
    "true.proof.templatecheck.opnorm.hconst_match_collapse."
    "varmul_top01_source0000_0500"
)
OPNORM_HCONST_DEFAULT_SANDWICH_TOP16_STRATEGY_KEY = (
    "true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse."
    "top16_fullshape"
)
OPNORM_HCONST_DEFAULT_SANDWICH_D14VC4_STRATEGY_KEY = (
    "true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse."
    "d14vc4_multitarget"
)
OPNORM_HCONST_DEFAULT_SANDWICH_D13VC4_STRATEGY_KEY = (
    "true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse."
    "d13vc4_multitarget"
)
OPNORM_HCONST_DEFAULT_SANDWICH_D14VC4_TARGETEXT_STRATEGY_KEY = (
    "true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse."
    "d14vc4_targetext"
)
OPNORM_HCONST_DEFAULT_SANDWICH_LOWVC_EXTENSION_STRATEGY_KEY = (
    "true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse."
    "lowvc_extension"
)
OPNORM_HCONST_DEFAULT_SANDWICH_TOPBUCKET_EXTENSION_STRATEGY_KEY = (
    "true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse."
    "topbucket_extension"
)
OPNORM_HCONST_DEFAULT_SANDWICH_FRONTIER_EXTENSION_STRATEGY_KEY = (
    "true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse."
    "frontier_extension"
)
OPNORM_HCONST_DEFAULT_SANDWICH_EDGE_EXTENSION_STRATEGY_KEY = (
    "true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse."
    "edge_extension"
)
OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE_TOP40_EXTENSION_STRATEGY_KEY = (
    "true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse."
    "postedge_top40_extension"
)
OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE2_TOP60_EXTENSION_STRATEGY_KEY = (
    "true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse."
    "postedge2_top60_extension"
)
OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE3_TOP80_EXTENSION_STRATEGY_KEY = (
    "true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse."
    "postedge3_top80_extension"
)
OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE4_TOP100_EXTENSION_STRATEGY_KEY = (
    "true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse."
    "postedge4_top100_extension"
)
OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE5_TOP120_EXTENSION_STRATEGY_KEY = (
    "true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse."
    "postedge5_top120_extension"
)
OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE6_SAMPLEHIT_TOP20_TAIL_STRATEGY_KEY = (
    "true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse."
    "postedge6_samplehit_top20_tail"
)
OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE7_SAMPLEHIT_TOP20_TAIL_STRATEGY_KEY = (
    "true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse."
    "postedge7_samplehit_top20_tail"
)
OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE8_D14VC5_FRONTIER_MULTITARGET20_STRATEGY_KEY = (
    "true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse."
    "postedge8_d14vc5_frontier_multitarget20"
)
OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE8_EXACT_TOP10_COMBINED_TAIL_STRATEGY_KEY = (
    "true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse."
    "postedge8_exact_top10_combined_tail"
)
OPNORM_HCONST_DEFAULT_SANDWICH_ROUND30_CUMULATIVE_HCONST_FAMILY_STRATEGY_KEY = (
    "true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse."
    "round30_cumulative_hconst_family"
)
OPNORM_HCONST_MATCH_GE25K_TAIL_BATCH_STRATEGY_KEY = (
    "true.proof.templatecheck.opnorm.hconst_match_collapse.ge25k_tail_batch"
)
OPNORM_HCONST_MATCH_GE10_TAIL_EXTENSION_STRATEGY_KEY = (
    "true.proof.templatecheck.opnorm.hconst_match_collapse.ge10_tail_extension"
)
OPNORM_HCONST_DEFAULT_SANDWICH_GE25_LT100_TAIL_BATCH_STRATEGY_KEY = (
    "true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse."
    "ge25_lt100_tail_batch"
)
OPNORM_HCONST_DEFAULT_SANDWICH_LT25_REMAINING_TAIL_BATCH_STRATEGY_KEY = (
    "true.proof.templatecheck.opnorm.hconst_default_sandwich_match_collapse."
    "lt25_remaining_tail_batch"
)
HINST_GROUND_CC_ACCEPTED_FAMILY_ROLLUP_STRATEGY_KEY = (
    "true.proof.templatecheck.evidence_guided.hinst_grind.ground_cc."
    "accepted_family_rollup"
)
OPNORM_HCONST_PLUS_HSTEP_D14VC4_V17_TAIL_STRATEGY_KEY = (
    "true.proof.templatecheck.opnorm.hconst_combined."
    "plus_hstep_default_sandwich_d14vc4_v17_tail"
)
ONE_SIDED_CONSTANCY_ROW_RECURSIVE_NF_STRATEGY_KEY = (
    "true.proof.templatecheck.evidence_guided.local_lemma.one_sided_constancy."
    "rhs_omits_right_arg.row_constancy_recursive_nf"
)
ONE_SIDED_CONSTANCY_COLUMN_RECURSIVE_NF_STRATEGY_KEY = (
    "true.proof.templatecheck.evidence_guided.local_lemma.one_sided_constancy."
    "rhs_omits_left_arg.column_constancy_recursive_nf"
)
OPNORM_HCONST_MATCH_COLLAPSE_SHAPE_BUCKETS = (
    (
        "roots=mul>mul|d=1>4|vc=5|lm=0|rm=0|vs=0",
        "roots=mul>mul|d=1>4|vc=3|lm=0|rm=0|vs=0",
    ),
    (
        "roots=mul>mul|d=1>3|vc=5|lm=0|rm=0|vs=0",
        "roots=mul>mul|d=1>4|vc=3|lm=0|rm=0|vs=0",
    ),
    (
        "roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0",
        "roots=mul>mul|d=1>3|vc=3|lm=0|rm=0|vs=0",
    ),
    (
        "roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0",
        "roots=mul>mul|d=1>4|vc=3|lm=0|rm=0|vs=0",
    ),
)
PRODUCT_COLLAPSE_TEMPLATES = (
    {
        "name": "left_nested_3_distinct",
        "term_pattern": "((v0*v1)*v2)",
        "summary_shape": "left-nested three-slot product",
    },
    {
        "name": "right_nested_3_distinct",
        "term_pattern": "(v0*(v1*v2))",
        "summary_shape": "right-nested three-slot product",
    },
    {
        "name": "left_nested_repeat_outer_left",
        "term_pattern": "((v0*v1)*v0)",
        "summary_shape": "left-nested product repeating the outer-left slot",
    },
    {
        "name": "left_nested_repeat_outer_right",
        "term_pattern": "((v0*v1)*v1)",
        "summary_shape": "left-nested product repeating the outer-right slot",
    },
    {
        "name": "right_nested_repeat_outer_inner_left",
        "term_pattern": "(v0*(v0*v1))",
        "summary_shape": "right-nested product repeating the outer slot inside-left",
    },
    {
        "name": "right_nested_repeat_outer_inner_right",
        "term_pattern": "(v0*(v1*v0))",
        "summary_shape": "right-nested product repeating the outer slot inside-right",
    },
    {
        "name": "left_nested_repeat_inner_pair",
        "term_pattern": "((v0*v0)*v1)",
        "summary_shape": "left-nested product with repeated inner pair",
    },
    {
        "name": "right_nested_repeat_inner_pair",
        "term_pattern": "(v0*(v1*v1))",
        "summary_shape": "right-nested product with repeated inner pair",
    },
    {
        "name": "binary_square",
        "term_pattern": "(v0*v0)",
        "summary_shape": "binary square product",
    },
    {
        "name": "left_nested_triple_same",
        "term_pattern": "((v0*v0)*v0)",
        "summary_shape": "left-nested triple square product",
    },
    {
        "name": "right_nested_triple_same",
        "term_pattern": "(v0*(v0*v0))",
        "summary_shape": "right-nested triple square product",
    },
)
SPINE_LEFT_ZERO_STRATEGY_KEY = LEFT_PROJECTION_ALL_EQUATIONS_STRATEGY_KEY
LEGACY_SPINE_LEFT_ZERO_STRATEGY_KEY = "false.spine_left_zero_nonleft.base"
LEFT_PROJECTION_2_TABLE = ((0, 0), (1, 1))
CONSTANT_2_TABLE = ((0, 0), (0, 0))
RIGHT_PROJECTION_2_TABLE = ((0, 1), (0, 1))
COMPLEMENT_LEFT_PROJECTION_2_TABLE = ((1, 1), (0, 0))
COMPLEMENT_RIGHT_PROJECTION_2_TABLE = ((1, 0), (1, 0))
LEFT_AND_COMPLEMENT_RIGHT_2_TABLE = ((0, 0), (1, 0))
COMPLEMENT_LEFT_AND_RIGHT_2_TABLE = ((0, 1), (0, 0))
XOR_2_TABLE = ((0, 1), (1, 0))
AND_2_TABLE = ((0, 0), (0, 1))
NOR_2_TABLE = ((1, 0), (0, 0))
STEINER_QUASIGROUP_3_TABLE = ((0, 2, 1), (2, 1, 0), (1, 0, 2))
RIGHT_MINUS_LEFT_3_TABLE = ((0, 1, 2), (2, 0, 1), (1, 2, 0))
LEFT_MINUS_RIGHT_3_TABLE = ((0, 2, 1), (1, 0, 2), (2, 1, 0))
FIN3_TABLE_020_110_122_TABLE = ((0, 2, 0), (1, 1, 0), (1, 2, 2))
LEFT_CYCLIC_SUCCESSOR_3_TABLE = ((1, 1, 1), (2, 2, 2), (0, 0, 0))
RIGHT_CYCLIC_SUCCESSOR_3_TABLE = ((1, 2, 0), (1, 2, 0), (1, 2, 0))
FIN3_TABLE_022_010_112_TABLE = ((0, 2, 2), (0, 1, 0), (1, 1, 2))
ADDITION_MOD3_3_TABLE = ((0, 1, 2), (1, 2, 0), (2, 0, 1))
FIN4_TABLE_0231_3102_1320_2013_TABLE = (
    (0, 2, 3, 1),
    (3, 1, 0, 2),
    (1, 3, 2, 0),
    (2, 0, 1, 3),
)
FIN3_TABLE_000_211_122_TABLE = ((0, 0, 0), (2, 1, 1), (1, 2, 2))
FIN3_TABLE_012_012_102_TABLE = ((0, 1, 2), (0, 1, 2), (1, 0, 2))
FIN3_TABLE_011_012_012_TABLE = ((0, 1, 1), (0, 1, 2), (0, 1, 2))
FIN3_TABLE_000_110_222_TABLE = ((0, 0, 0), (1, 1, 0), (2, 2, 2))
FIN3_TABLE_122_020_110_TABLE = ((1, 2, 2), (0, 2, 0), (1, 1, 0))
FIN3_TABLE_002_112_102_TABLE = ((0, 0, 2), (1, 1, 2), (1, 0, 2))
FIN3_TABLE_011_012_110_TABLE = ((0, 1, 1), (0, 1, 2), (1, 1, 0))
FIN4_TABLE_2013_3102_0231_1320_TABLE = (
    (2, 0, 1, 3),
    (3, 1, 0, 2),
    (0, 2, 3, 1),
    (1, 3, 2, 0),
)
FIN4_TABLE_0011_2233_0011_2233_TABLE = (
    (0, 0, 1, 1),
    (2, 2, 3, 3),
    (0, 0, 1, 1),
    (2, 2, 3, 3),
)
FIN5_TABLE_02413_41302_30241_24130_13024_TABLE = (
    (0, 2, 4, 1, 3),
    (4, 1, 3, 0, 2),
    (3, 0, 2, 4, 1),
    (2, 4, 1, 3, 0),
    (1, 3, 0, 2, 4),
)
FIN5_TABLE_03142_31420_14203_42031_20314_TABLE = (
    (0, 3, 1, 4, 2),
    (3, 1, 4, 2, 0),
    (1, 4, 2, 0, 3),
    (4, 2, 0, 3, 1),
    (2, 0, 3, 1, 4),
)
FIN5_TABLE_02143_41320_34201_10432_23014_TABLE = (
    (0, 2, 1, 4, 3),
    (4, 1, 3, 2, 0),
    (3, 4, 2, 0, 1),
    (1, 0, 4, 3, 2),
    (2, 3, 0, 1, 4),
)
FIN7_TABLE_0214365_3150624_4625031_6543210_5361402_2406153_1032546_TABLE = (
    (0, 2, 1, 4, 3, 6, 5),
    (3, 1, 5, 0, 6, 2, 4),
    (4, 6, 2, 5, 0, 3, 1),
    (6, 5, 4, 3, 2, 1, 0),
    (5, 3, 6, 1, 4, 0, 2),
    (2, 4, 0, 6, 1, 5, 3),
    (1, 0, 3, 2, 5, 4, 6),
)
FIN5_TABLE_31420_02341_14032_40213_23104_TABLE = (
    (3, 1, 4, 2, 0),
    (0, 2, 3, 4, 1),
    (1, 4, 0, 3, 2),
    (4, 0, 2, 1, 3),
    (2, 3, 1, 0, 4),
)
FIN5_TABLE_34120_20413_01234_13042_42301_TABLE = (
    (3, 4, 1, 2, 0),
    (2, 0, 4, 1, 3),
    (0, 1, 2, 3, 4),
    (1, 3, 0, 4, 2),
    (4, 2, 3, 0, 1),
)
STRUCTURED_AFFINE_MOD5_A3_B2_C0_TABLE = (
    (0, 2, 4, 1, 3),
    (3, 0, 2, 4, 1),
    (1, 3, 0, 2, 4),
    (4, 1, 3, 0, 2),
    (2, 4, 1, 3, 0),
)
STRUCTURED_AFFINE_MOD5_A2_B3_C0_TABLE = (
    (0, 3, 1, 4, 2),
    (2, 0, 3, 1, 4),
    (4, 2, 0, 3, 1),
    (1, 4, 2, 0, 3),
    (3, 1, 4, 2, 0),
)
STRUCTURED_AFFINE_MOD4_A0_B1_C1_TABLE = (
    (1, 2, 3, 0),
    (1, 2, 3, 0),
    (1, 2, 3, 0),
    (1, 2, 3, 0),
)
STRUCTURED_AFFINE_MOD4_A1_B0_C3_TABLE = (
    (3, 3, 3, 3),
    (0, 0, 0, 0),
    (1, 1, 1, 1),
    (2, 2, 2, 2),
)
STRUCTURED_AFFINE_MOD5_A0_B1_C4_TABLE = (
    (4, 0, 1, 2, 3),
    (4, 0, 1, 2, 3),
    (4, 0, 1, 2, 3),
    (4, 0, 1, 2, 3),
    (4, 0, 1, 2, 3),
)
STRUCTURED_AFFINE_MOD5_A1_B0_C4_TABLE = (
    (4, 4, 4, 4, 4),
    (0, 0, 0, 0, 0),
    (1, 1, 1, 1, 1),
    (2, 2, 2, 2, 2),
    (3, 3, 3, 3, 3),
)
STRUCTURED_AFFINE_MOD5_A1_B3_C4_TABLE = (
    (4, 2, 0, 3, 1),
    (0, 3, 1, 4, 2),
    (1, 4, 2, 0, 3),
    (2, 0, 3, 1, 4),
    (3, 1, 4, 2, 0),
)
STRUCTURED_AFFINE_MOD5_A3_B1_C4_TABLE = (
    (4, 0, 1, 2, 3),
    (2, 3, 4, 0, 1),
    (0, 1, 2, 3, 4),
    (3, 4, 0, 1, 2),
    (1, 2, 3, 4, 0),
)
STRUCTURED_AFFINE_MOD7_A1_B3_C6_TABLE = (
    (6, 2, 5, 1, 4, 0, 3),
    (0, 3, 6, 2, 5, 1, 4),
    (1, 4, 0, 3, 6, 2, 5),
    (2, 5, 1, 4, 0, 3, 6),
    (3, 6, 2, 5, 1, 4, 0),
    (4, 0, 3, 6, 2, 5, 1),
    (5, 1, 4, 0, 3, 6, 2),
)
STRUCTURED_AFFINE_MOD7_A3_B1_C6_TABLE = (
    (6, 0, 1, 2, 3, 4, 5),
    (2, 3, 4, 5, 6, 0, 1),
    (5, 6, 0, 1, 2, 3, 4),
    (1, 2, 3, 4, 5, 6, 0),
    (4, 5, 6, 0, 1, 2, 3),
    (0, 1, 2, 3, 4, 5, 6),
    (3, 4, 5, 6, 0, 1, 2),
)
STRUCTURED_AFFINE_MOD4_A3_B2_C3_TABLE = (
    (3, 1, 3, 1),
    (2, 0, 2, 0),
    (1, 3, 1, 3),
    (0, 2, 0, 2),
)
STRUCTURED_AFFINE_MOD4_A2_B3_C3_TABLE = (
    (3, 2, 1, 0),
    (1, 0, 3, 2),
    (3, 2, 1, 0),
    (1, 0, 3, 2),
)


def _affine_mod_table(
    modulus: int,
    a: int,
    b: int,
    c: int,
) -> tuple[tuple[int, ...], ...]:
    return tuple(
        tuple((a * x + b * y + c) % modulus for y in range(modulus))
        for x in range(modulus)
    )


STRUCTURED_AFFINE_MOD11_TOP2_MATCHOP_NOHB_SPECS = (
    {
        "label": "affine_mod11_a7_b9_c9",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod11_a7_b9_c9.all_equations",
        "priority": 350,
        "modulus": 11,
        "a": 7,
        "b": 9,
        "c": 9,
        "table": (
            (9, 7, 5, 3, 1, 10, 8, 6, 4, 2, 0),
            (5, 3, 1, 10, 8, 6, 4, 2, 0, 9, 7),
            (1, 10, 8, 6, 4, 2, 0, 9, 7, 5, 3),
            (8, 6, 4, 2, 0, 9, 7, 5, 3, 1, 10),
            (4, 2, 0, 9, 7, 5, 3, 1, 10, 8, 6),
            (0, 9, 7, 5, 3, 1, 10, 8, 6, 4, 2),
            (7, 5, 3, 1, 10, 8, 6, 4, 2, 0, 9),
            (3, 1, 10, 8, 6, 4, 2, 0, 9, 7, 5),
            (10, 8, 6, 4, 2, 0, 9, 7, 5, 3, 1),
            (6, 4, 2, 0, 9, 7, 5, 3, 1, 10, 8),
            (2, 0, 9, 7, 5, 3, 1, 10, 8, 6, 4),
        ),
        "current_increment": 768_190,
        "raw_coverage": 4_500_288,
        "representative_pairs": {
            "new_order4_source_to_order5_target": (907, 54684),
            "new_order5_source_to_order4_target": (4701, 4065),
            "new_order5_source_to_order5_target": (4701, 54684),
            "overlap_existing": (1, 54684),
        },
    },
    {
        "label": "affine_mod11_a9_b7_c9",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod11_a9_b7_c9.all_equations",
        "priority": 351,
        "modulus": 11,
        "a": 9,
        "b": 7,
        "c": 9,
        "table": (
            (9, 5, 1, 8, 4, 0, 7, 3, 10, 6, 2),
            (7, 3, 10, 6, 2, 9, 5, 1, 8, 4, 0),
            (5, 1, 8, 4, 0, 7, 3, 10, 6, 2, 9),
            (3, 10, 6, 2, 9, 5, 1, 8, 4, 0, 7),
            (1, 8, 4, 0, 7, 3, 10, 6, 2, 9, 5),
            (10, 6, 2, 9, 5, 1, 8, 4, 0, 7, 3),
            (8, 4, 0, 7, 3, 10, 6, 2, 9, 5, 1),
            (6, 2, 9, 5, 1, 8, 4, 0, 7, 3, 10),
            (4, 0, 7, 3, 10, 6, 2, 9, 5, 1, 8),
            (2, 9, 5, 1, 8, 4, 0, 7, 3, 10, 6),
            (0, 7, 3, 10, 6, 2, 9, 5, 1, 8, 4),
        ),
        "current_increment": 767_737,
        "raw_coverage": 4_500_288,
        "representative_pairs": {
            "new_order4_source_to_order5_target": (1435, 25743),
            "new_order5_source_to_order4_target": (5578, 4065),
            "new_order5_source_to_order5_target": (5578, 54684),
            "overlap_existing": (1, 54684),
        },
    },
)
STRUCTURED_AFFINE_MOD11_COMBO9_MATCHOP_NOHB_SPECS = (
    {
        "label": "affine_mod11_a6_b6_c0",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod11_a6_b6_c0.all_equations",
        "priority": 352,
        "modulus": 11,
        "a": 6,
        "b": 6,
        "c": 0,
        "table": _affine_mod_table(11, 6, 6, 0),
        "current_increment": 433_728,
        "raw_coverage": 30_914_844,
        "representative_pairs": {
            "new_order4_source_to_order5_target": (474, 59161),
            "new_order5_source_to_order4_target": (4758, 3068),
            "new_order5_source_to_order5_target": (4758, 52297),
            "overlap_existing": (1, 54897),
        },
        "smoke_tiers": (
            "new_order4_source_to_order5_target",
            "new_order5_source_to_order4_target",
            "new_order5_source_to_order5_target",
            "overlap_existing",
        ),
    },
    {
        "label": "affine_mod11_a8_b5_c9",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod11_a8_b5_c9.all_equations",
        "priority": 353,
        "modulus": 11,
        "a": 8,
        "b": 5,
        "c": 9,
        "table": _affine_mod_table(11, 8, 5, 9),
        "current_increment": 127_520,
        "raw_coverage": 3_126_300,
        "representative_pairs": {
            "new_order4_source_to_order5_target": (642, 54684),
            "new_order5_source_to_order4_target": (4701, 2035),
            "new_order5_source_to_order5_target": (4701, 22235),
            "overlap_existing": (1, 54684),
        },
        "smoke_tiers": ("new_order5_source_to_order4_target",),
    },
    {
        "label": "affine_mod11_a5_b8_c9",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod11_a5_b8_c9.all_equations",
        "priority": 354,
        "modulus": 11,
        "a": 5,
        "b": 8,
        "c": 9,
        "table": _affine_mod_table(11, 5, 8, 9),
        "current_increment": 127_516,
        "raw_coverage": 3_126_300,
        "representative_pairs": {
            "new_order4_source_to_order5_target": (2875, 54684),
            "new_order5_source_to_order4_target": (13518, 817),
            "new_order5_source_to_order5_target": (13483, 52053),
            "overlap_existing": (1, 54684),
        },
        "smoke_tiers": ("new_order5_source_to_order4_target",),
    },
    {
        "label": "affine_mod11_a3_b6_c9",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod11_a3_b6_c9.all_equations",
        "priority": 355,
        "modulus": 11,
        "a": 3,
        "b": 6,
        "c": 9,
        "table": _affine_mod_table(11, 3, 6, 9),
        "current_increment": 2_275,
        "raw_coverage": 2_751_408,
        "representative_pairs": {
            "new_order4_source_to_order5_target": None,
            "new_order5_source_to_order4_target": (12594, 4065),
            "new_order5_source_to_order5_target": (12594, 54684),
            "overlap_existing": (1, 54684),
        },
        "smoke_tiers": ("new_order5_source_to_order4_target",),
    },
    {
        "label": "affine_mod11_a6_b3_c9",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod11_a6_b3_c9.all_equations",
        "priority": 356,
        "modulus": 11,
        "a": 6,
        "b": 3,
        "c": 9,
        "table": _affine_mod_table(11, 6, 3, 9),
        "current_increment": 2_243,
        "raw_coverage": 2_751_408,
        "representative_pairs": {
            "new_order4_source_to_order5_target": None,
            "new_order5_source_to_order4_target": (4704, 203),
            "new_order5_source_to_order5_target": (4704, 52053),
            "overlap_existing": (1, 54684),
        },
        "smoke_tiers": ("new_order5_source_to_order4_target",),
    },
    {
        "label": "affine_mod11_a5_b7_c0",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod11_a5_b7_c0.all_equations",
        "priority": 357,
        "modulus": 11,
        "a": 5,
        "b": 7,
        "c": 0,
        "table": _affine_mod_table(11, 5, 7, 0),
        "current_increment": 89_621,
        "raw_coverage": 28_018_375,
        "representative_pairs": {
            "new_order4_source_to_order5_target": (271, 37153),
            "new_order5_source_to_order4_target": (4758, 3068),
            "new_order5_source_to_order5_target": (4758, 52297),
            "overlap_existing": (1, 54897),
        },
        "smoke_tiers": ("new_order5_source_to_order4_target",),
    },
    {
        "label": "affine_mod11_a7_b5_c0",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod11_a7_b5_c0.all_equations",
        "priority": 358,
        "modulus": 11,
        "a": 7,
        "b": 5,
        "c": 0,
        "table": _affine_mod_table(11, 7, 5, 0),
        "current_increment": 89_394,
        "raw_coverage": 28_018_375,
        "representative_pairs": {
            "new_order4_source_to_order5_target": (63, 8594),
            "new_order5_source_to_order4_target": (4912, 3079),
            "new_order5_source_to_order5_target": (4711, 16125),
            "overlap_existing": (1, 54897),
        },
        "smoke_tiers": ("new_order5_source_to_order4_target",),
    },
    {
        "label": "affine_mod11_a8_b4_c0",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod11_a8_b4_c0.all_equations",
        "priority": 359,
        "modulus": 11,
        "a": 8,
        "b": 4,
        "c": 0,
        "table": _affine_mod_table(11, 8, 4, 0),
        "current_increment": 72_282,
        "raw_coverage": 31_345_855,
        "representative_pairs": {
            "new_order4_source_to_order5_target": (882, 8221),
            "new_order5_source_to_order4_target": (4748, 4131),
            "new_order5_source_to_order5_target": (4748, 51430),
            "overlap_existing": (1, 54897),
        },
        "smoke_tiers": ("new_order5_source_to_order4_target",),
    },
    {
        "label": "affine_mod11_a4_b8_c0",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod11_a4_b8_c0.all_equations",
        "priority": 360,
        "modulus": 11,
        "a": 4,
        "b": 8,
        "c": 0,
        "table": _affine_mod_table(11, 4, 8, 0),
        "current_increment": 72_166,
        "raw_coverage": 31_345_855,
        "representative_pairs": {
            "new_order4_source_to_order5_target": (474, 59161),
            "new_order5_source_to_order4_target": (4758, 3068),
            "new_order5_source_to_order5_target": (4758, 52297),
            "overlap_existing": (1, 54897),
        },
        "smoke_tiers": ("new_order5_source_to_order4_target",),
    },
)
STRUCTURED_AFFINE_LOW_ORDER_LE9_COMBO19_SPECS = (
    {
        "label": "affine_mod9_a6_b4_c0",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod9_a6_b4_c0.all_equations",
        "priority": 361,
        "modulus": 9,
        "a": 6,
        "b": 4,
        "c": 0,
        "table": _affine_mod_table(9, 6, 4, 0),
        "current_increment": 232_881,
        "raw_coverage": 125_948_508,
        "representative_pairs": {
            "new_order4_source_to_order5_target": (28, 54162),
            "new_order5_source_to_order4_target": (4787, 4131),
            "new_order5_source_to_order5_target": (4787, 54897),
            "overlap_existing": (1, 54897),
        },
        "smoke_tiers": (
            "new_order4_source_to_order5_target",
            "new_order5_source_to_order4_target",
            "new_order5_source_to_order5_target",
            "overlap_existing",
        ),
    },
    {
        "label": "affine_mod9_a7_b3_c0",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod9_a7_b3_c0.all_equations",
        "priority": 362,
        "modulus": 9,
        "a": 7,
        "b": 3,
        "c": 0,
        "table": _affine_mod_table(9, 7, 3, 0),
        "current_increment": 232_293,
        "raw_coverage": 125_948_508,
        "representative_pairs": {
            "new_order4_source_to_order5_target": (9, 51430),
            "new_order5_source_to_order4_target": (4696, 4131),
            "new_order5_source_to_order5_target": (4696, 51430),
            "overlap_existing": (1, 60828),
        },
        "smoke_tiers": ("new_order5_source_to_order4_target",),
    },
    {
        "label": "affine_mod9_a3_b7_c8",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod9_a3_b7_c8.all_equations",
        "priority": 363,
        "modulus": 9,
        "a": 3,
        "b": 7,
        "c": 8,
        "table": _affine_mod_table(9, 3, 7, 8),
        "current_increment": 20_334,
        "raw_coverage": 12_661_719,
        "representative_pairs": {
            "new_order4_source_to_order5_target": None,
            "new_order5_source_to_order4_target": (7331, 4065),
            "new_order5_source_to_order5_target": (7331, 54684),
            "overlap_existing": (1, 54684),
        },
        "smoke_tiers": ("new_order5_source_to_order4_target",),
    },
    {
        "label": "affine_mod9_a7_b3_c8",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod9_a7_b3_c8.all_equations",
        "priority": 364,
        "modulus": 9,
        "a": 7,
        "b": 3,
        "c": 8,
        "table": _affine_mod_table(9, 7, 3, 8),
        "current_increment": 19_826,
        "raw_coverage": 12_661_719,
        "representative_pairs": {
            "new_order4_source_to_order5_target": None,
            "new_order5_source_to_order4_target": (23990, 3253),
            "new_order5_source_to_order5_target": (23990, 43283),
            "overlap_existing": (1, 54684),
        },
        "smoke_tiers": ("new_order5_source_to_order4_target",),
    },
    {
        "label": "affine_mod9_a6_b7_c8",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod9_a6_b7_c8.all_equations",
        "priority": 365,
        "modulus": 9,
        "a": 6,
        "b": 7,
        "c": 8,
        "table": _affine_mod_table(9, 6, 7, 8),
        "current_increment": 8_698,
        "raw_coverage": 10_795_719,
        "representative_pairs": {
            "new_order4_source_to_order5_target": (619, 9957),
            "new_order5_source_to_order4_target": (8208, 3862),
            "new_order5_source_to_order5_target": (8208, 9957),
            "overlap_existing": (1, 54684),
        },
        "smoke_tiers": ("new_order5_source_to_order4_target",),
    },
    {
        "label": "affine_mod9_a7_b6_c8",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod9_a7_b6_c8.all_equations",
        "priority": 366,
        "modulus": 9,
        "a": 7,
        "b": 6,
        "c": 8,
        "table": _affine_mod_table(9, 7, 6, 8),
        "current_increment": 8_745,
        "raw_coverage": 10_795_719,
        "representative_pairs": {
            "new_order4_source_to_order5_target": (2036, 43283),
            "new_order5_source_to_order4_target": (23113, 3456),
            "new_order5_source_to_order5_target": (23113, 43283),
            "overlap_existing": (1, 54684),
        },
        "smoke_tiers": ("new_order5_source_to_order4_target",),
    },
    {
        "label": "affine_mod8_a7_b2_c0",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod8_a7_b2_c0.all_equations",
        "priority": 367,
        "modulus": 8,
        "a": 7,
        "b": 2,
        "c": 0,
        "table": _affine_mod_table(8, 7, 2, 0),
        "current_increment": 77_949,
        "raw_coverage": 58_362_663,
        "representative_pairs": {
            "new_order4_source_to_order5_target": (48, 54897),
            "new_order5_source_to_order4_target": (4696, 3255),
            "new_order5_source_to_order5_target": (4696, 54897),
            "overlap_existing": (1, 54897),
        },
        "smoke_tiers": ("new_order5_source_to_order4_target",),
    },
    {
        "label": "affine_mod8_a6_b3_c0",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod8_a6_b3_c0.all_equations",
        "priority": 368,
        "modulus": 8,
        "a": 6,
        "b": 3,
        "c": 0,
        "table": _affine_mod_table(8, 6, 3, 0),
        "current_increment": 76_388,
        "raw_coverage": 58_362_663,
        "representative_pairs": {
            "new_order4_source_to_order5_target": (270, 62068),
            "new_order5_source_to_order4_target": (8218, 619),
            "new_order5_source_to_order5_target": (8218, 8208),
            "overlap_existing": (1, 54897),
        },
        "smoke_tiers": ("new_order5_source_to_order4_target",),
    },
    {
        "label": "affine_mod9_a5_b5_c0",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod9_a5_b5_c0.all_equations",
        "priority": 369,
        "modulus": 9,
        "a": 5,
        "b": 5,
        "c": 0,
        "table": _affine_mod_table(9, 5, 5, 0),
        "current_increment": 61_205,
        "raw_coverage": 32_884_380,
        "representative_pairs": {
            "new_order4_source_to_order5_target": None,
            "new_order5_source_to_order4_target": (5219, 4131),
            "new_order5_source_to_order5_target": (5219, 51430),
            "overlap_existing": (1, 54897),
        },
        "smoke_tiers": ("new_order5_source_to_order4_target",),
    },
    {
        "label": "affine_mod8_a6_b4_c7",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod8_a6_b4_c7.all_equations",
        "priority": 370,
        "modulus": 8,
        "a": 6,
        "b": 4,
        "c": 7,
        "table": _affine_mod_table(8, 6, 4, 7),
        "current_increment": 49_826,
        "raw_coverage": 35_957_680,
        "representative_pairs": {
            "new_order4_source_to_order5_target": (4610, 61700),
            "new_order5_source_to_order4_target": (60918, 4590),
            "new_order5_source_to_order5_target": (60912, 61700),
            "overlap_existing": (1, 55561),
        },
        "smoke_tiers": ("new_order5_source_to_order4_target",),
    },
    {
        "label": "affine_mod8_a4_b6_c7",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod8_a4_b6_c7.all_equations",
        "priority": 371,
        "modulus": 8,
        "a": 4,
        "b": 6,
        "c": 7,
        "table": _affine_mod_table(8, 4, 6, 7),
        "current_increment": 47_244,
        "raw_coverage": 35_957_680,
        "representative_pairs": {
            "new_order4_source_to_order5_target": (4295, 55561),
            "new_order5_source_to_order4_target": (54779, 4268),
            "new_order5_source_to_order5_target": (54773, 53807),
            "overlap_existing": (1, 55561),
        },
        "smoke_tiers": ("new_order5_source_to_order4_target",),
    },
    {
        "label": "affine_mod9_a2_b8_c0",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod9_a2_b8_c0.all_equations",
        "priority": 372,
        "modulus": 9,
        "a": 2,
        "b": 8,
        "c": 0,
        "table": _affine_mod_table(9, 2, 8, 0),
        "current_increment": 39_421,
        "raw_coverage": 43_619_055,
        "representative_pairs": {
            "new_order4_source_to_order5_target": (2700, 31937),
            "new_order5_source_to_order4_target": (8269, 3724),
            "new_order5_source_to_order5_target": (8444, 61950),
            "overlap_existing": (1, 54897),
        },
        "smoke_tiers": ("new_order5_source_to_order4_target",),
    },
    {
        "label": "affine_mod9_a8_b2_c0",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod9_a8_b2_c0.all_equations",
        "priority": 373,
        "modulus": 9,
        "a": 8,
        "b": 2,
        "c": 0,
        "table": _affine_mod_table(9, 8, 2, 0),
        "current_increment": 39_407,
        "raw_coverage": 43_619_055,
        "representative_pairs": {
            "new_order4_source_to_order5_target": (907, 13520),
            "new_order5_source_to_order4_target": (4936, 4608),
            "new_order5_source_to_order5_target": (4795, 46164),
            "overlap_existing": (1, 54897),
        },
        "smoke_tiers": ("new_order5_source_to_order4_target",),
    },
    {
        "label": "affine_mod7_a3_b5_c6",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod7_a3_b5_c6.all_equations",
        "priority": 374,
        "modulus": 7,
        "a": 3,
        "b": 5,
        "c": 6,
        "table": _affine_mod_table(7, 3, 5, 6),
        "current_increment": 23_868,
        "raw_coverage": 9_986_560,
        "representative_pairs": {
            "new_order4_source_to_order5_target": (105, 45914),
            "new_order5_source_to_order4_target": (6468, 3253),
            "new_order5_source_to_order5_target": (6468, 43283),
            "overlap_existing": (1, 54684),
        },
        "smoke_tiers": ("new_order5_source_to_order4_target",),
    },
    {
        "label": "affine_mod7_a5_b3_c6",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod7_a5_b3_c6.all_equations",
        "priority": 375,
        "modulus": 7,
        "a": 5,
        "b": 3,
        "c": 6,
        "table": _affine_mod_table(7, 5, 3, 6),
        "current_increment": 23_784,
        "raw_coverage": 9_986_560,
        "representative_pairs": {
            "new_order4_source_to_order5_target": (219, 14342),
            "new_order5_source_to_order4_target": (5578, 1223),
            "new_order5_source_to_order5_target": (5578, 22235),
            "overlap_existing": (1, 54684),
        },
        "smoke_tiers": ("new_order5_source_to_order4_target",),
    },
    {
        "label": "affine_mod7_a3_b4_c6",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod7_a3_b4_c6.all_equations",
        "priority": 376,
        "modulus": 7,
        "a": 3,
        "b": 4,
        "c": 6,
        "table": _affine_mod_table(7, 3, 4, 6),
        "current_increment": 11_032,
        "raw_coverage": 7_494_720,
        "representative_pairs": {
            "new_order4_source_to_order5_target": (2910, 54684),
            "new_order5_source_to_order4_target": (6816, 4065),
            "new_order5_source_to_order5_target": (6816, 54684),
            "overlap_existing": (1, 54684),
        },
        "smoke_tiers": ("new_order5_source_to_order4_target",),
    },
    {
        "label": "affine_mod7_a4_b3_c6",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod7_a4_b3_c6.all_equations",
        "priority": 377,
        "modulus": 7,
        "a": 4,
        "b": 3,
        "c": 6,
        "table": _affine_mod_table(7, 4, 3, 6),
        "current_increment": 11_025,
        "raw_coverage": 7_494_720,
        "representative_pairs": {
            "new_order4_source_to_order5_target": (633, 52053),
            "new_order5_source_to_order4_target": (13471, 203),
            "new_order5_source_to_order5_target": (13471, 52053),
            "overlap_existing": (1, 54684),
        },
        "smoke_tiers": ("new_order5_source_to_order4_target",),
    },
    {
        "label": "affine_mod8_a5_b4_c7",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod8_a5_b4_c7.all_equations",
        "priority": 378,
        "modulus": 8,
        "a": 5,
        "b": 4,
        "c": 7,
        "table": _affine_mod_table(8, 5, 4, 7),
        "current_increment": 15_826,
        "raw_coverage": 20_045_788,
        "representative_pairs": {
            "new_order4_source_to_order5_target": None,
            "new_order5_source_to_order4_target": (28383, 3253),
            "new_order5_source_to_order5_target": (28383, 54684),
            "overlap_existing": (1, 54684),
        },
        "smoke_tiers": ("new_order5_source_to_order4_target",),
    },
    {
        "label": "affine_mod8_a4_b5_c7",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod8_a4_b5_c7.all_equations",
        "priority": 379,
        "modulus": 8,
        "a": 4,
        "b": 5,
        "c": 7,
        "table": _affine_mod_table(8, 4, 5, 7),
        "current_increment": 15_794,
        "raw_coverage": 20_045_788,
        "representative_pairs": {
            "new_order4_source_to_order5_target": None,
            "new_order5_source_to_order4_target": (5577, 4065),
            "new_order5_source_to_order5_target": (5577, 54684),
            "overlap_existing": (1, 54684),
        },
        "smoke_tiers": ("new_order5_source_to_order4_target",),
    },
)
STRUCTURED_AFFINE_LOW_ORDER_TAIL_COMBO2_SPECS = (
    {
        "label": "affine_mod4_a2_b1_c3",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod4_a2_b1_c3.all_equations",
        "priority": 339,
        "table": ((3, 0, 1, 2), (1, 2, 3, 0), (3, 0, 1, 2), (1, 2, 3, 0)),
        "current_increment": 163_368,
        "raw_coverage": 48_749_943,
        "representative_pairs": {
            "new_order4_source_to_order5_target": (104, 60823),
            "new_order5_source_to_order4_target": (12593, 4065),
            "new_order5_source_to_order5_target": (12588, 52053),
            "overlap_existing": (1, 54684),
        },
    },
    {
        "label": "affine_mod4_a1_b2_c3",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod4_a1_b2_c3.all_equations",
        "priority": 340,
        "table": ((3, 1, 3, 1), (0, 2, 0, 2), (1, 3, 1, 3), (2, 0, 2, 0)),
        "current_increment": 163_116,
        "raw_coverage": 48_749_943,
        "representative_pairs": {
            "new_order4_source_to_order5_target": (152, 28374),
            "new_order5_source_to_order4_target": (17062, 4065),
            "new_order5_source_to_order5_target": (16980, 28374),
            "overlap_existing": (1, 42406),
        },
    },
    {
        "label": "affine_mod5_a1_b1_c4",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod5_a1_b1_c4.all_equations",
        "priority": 341,
        "table": (
            (4, 0, 1, 2, 3),
            (0, 1, 2, 3, 4),
            (1, 2, 3, 4, 0),
            (2, 3, 4, 0, 1),
            (3, 4, 0, 1, 2),
        ),
        "current_increment": 129_896,
        "raw_coverage": 20_293_500,
        "representative_pairs": {
            "new_order4_source_to_order5_target": None,
            "new_order5_source_to_order4_target": (4798, 151),
            "new_order5_source_to_order5_target": (4798, 51176),
            "overlap_existing": (1, 51176),
        },
    },
    {
        "label": "affine_mod7_a1_b5_c6",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod7_a1_b5_c6.all_equations",
        "priority": 342,
        "table": (
            (6, 4, 2, 0, 5, 3, 1),
            (0, 5, 3, 1, 6, 4, 2),
            (1, 6, 4, 2, 0, 5, 3),
            (2, 0, 5, 3, 1, 6, 4),
            (3, 1, 6, 4, 2, 0, 5),
            (4, 2, 0, 5, 3, 1, 6),
            (5, 3, 1, 6, 4, 2, 0),
        ),
        "current_increment": 100_354,
        "raw_coverage": 6_247_600,
        "representative_pairs": {
            "new_order4_source_to_order5_target": None,
            "new_order5_source_to_order4_target": (9108, 4065),
            "new_order5_source_to_order5_target": (9080, 5572),
            "overlap_existing": (1, 22235),
        },
    },
    {
        "label": "affine_mod7_a5_b1_c6",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod7_a5_b1_c6.all_equations",
        "priority": 343,
        "table": (
            (6, 0, 1, 2, 3, 4, 5),
            (4, 5, 6, 0, 1, 2, 3),
            (2, 3, 4, 5, 6, 0, 1),
            (0, 1, 2, 3, 4, 5, 6),
            (5, 6, 0, 1, 2, 3, 4),
            (3, 4, 5, 6, 0, 1, 2),
            (1, 2, 3, 4, 5, 6, 0),
        ),
        "current_increment": 100_343,
        "raw_coverage": 6_247_600,
        "representative_pairs": {
            "new_order4_source_to_order5_target": None,
            "new_order5_source_to_order4_target": (29280, 203),
            "new_order5_source_to_order5_target": (29280, 52053),
            "overlap_existing": (1, 16096),
        },
    },
    {
        "label": "affine_mod7_a5_b3_c0",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod7_a5_b3_c0.all_equations",
        "priority": 344,
        "table": (
            (0, 3, 6, 2, 5, 1, 4),
            (5, 1, 4, 0, 3, 6, 2),
            (3, 6, 2, 5, 1, 4, 0),
            (1, 4, 0, 3, 6, 2, 5),
            (6, 2, 5, 1, 4, 0, 3),
            (4, 0, 3, 6, 2, 5, 1),
            (2, 5, 1, 4, 0, 3, 6),
        ),
        "current_increment": 78_543,
        "raw_coverage": 69_192_700,
        "representative_pairs": {
            "new_order4_source_to_order5_target": (713, 51578),
            "new_order5_source_to_order4_target": (5087, 3079),
            "new_order5_source_to_order5_target": (5087, 46006),
            "overlap_existing": (1, 29655),
        },
    },
    {
        "label": "affine_mod7_a3_b5_c0",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod7_a3_b5_c0.all_equations",
        "priority": 345,
        "table": (
            (0, 5, 3, 1, 6, 4, 2),
            (3, 1, 6, 4, 2, 0, 5),
            (6, 4, 2, 0, 5, 3, 1),
            (2, 0, 5, 3, 1, 6, 4),
            (5, 3, 1, 6, 4, 2, 0),
            (1, 6, 4, 2, 0, 5, 3),
            (4, 2, 0, 5, 3, 1, 6),
        ),
        "current_increment": 78_525,
        "raw_coverage": 69_192_700,
        "representative_pairs": {
            "new_order4_source_to_order5_target": (1119, 22599),
            "new_order5_source_to_order4_target": (5050, 3068),
            "new_order5_source_to_order5_target": (5050, 14592),
            "overlap_existing": (1, 42505),
        },
    },
    {
        "label": "affine_mod7_a3_b6_c6",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod7_a3_b6_c6.all_equations",
        "priority": 346,
        "table": (
            (6, 5, 4, 3, 2, 1, 0),
            (2, 1, 0, 6, 5, 4, 3),
            (5, 4, 3, 2, 1, 0, 6),
            (1, 0, 6, 5, 4, 3, 2),
            (4, 3, 2, 1, 0, 6, 5),
            (0, 6, 5, 4, 3, 2, 1),
            (3, 2, 1, 0, 6, 5, 4),
        ),
        "current_increment": 69_435,
        "raw_coverage": 4_750_000,
        "representative_pairs": {
            "new_order4_source_to_order5_target": (474, 36267),
            "new_order5_source_to_order4_target": (17952, 1426),
            "new_order5_source_to_order5_target": (17869, 28374),
            "overlap_existing": (1, 51176),
        },
    },
    {
        "label": "affine_mod7_a6_b3_c6",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod7_a6_b3_c6.all_equations",
        "priority": 347,
        "table": (
            (6, 2, 5, 1, 4, 0, 3),
            (5, 1, 4, 0, 3, 6, 2),
            (4, 0, 3, 6, 2, 5, 1),
            (3, 6, 2, 5, 1, 4, 0),
            (2, 5, 1, 4, 0, 3, 6),
            (1, 4, 0, 3, 6, 2, 5),
            (0, 3, 6, 2, 5, 1, 4),
        ),
        "current_increment": 69_279,
        "raw_coverage": 4_750_000,
        "representative_pairs": {
            "new_order4_source_to_order5_target": (2540, 29251),
            "new_order5_source_to_order4_target": (12607, 3862),
            "new_order5_source_to_order5_target": (12607, 32759),
            "overlap_existing": (1, 32759),
        },
    },
    {
        "label": "affine_mod7_a5_b5_c6",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod7_a5_b5_c6.all_equations",
        "priority": 348,
        "table": (
            (6, 4, 2, 0, 5, 3, 1),
            (4, 2, 0, 5, 3, 1, 6),
            (2, 0, 5, 3, 1, 6, 4),
            (0, 5, 3, 1, 6, 4, 2),
            (5, 3, 1, 6, 4, 2, 0),
            (3, 1, 6, 4, 2, 0, 5),
            (1, 6, 4, 2, 0, 5, 3),
        ),
        "current_increment": 39_929,
        "raw_coverage": 7_744_048,
        "representative_pairs": {
            "new_order4_source_to_order5_target": None,
            "new_order5_source_to_order4_target": (17002, 1832),
            "new_order5_source_to_order5_target": (17002, 32759),
            "overlap_existing": (1, 12588),
        },
    },
    {
        "label": "affine_mod7_a4_b4_c0",
        "strategy_key": "false.finmodel.setcheck.structured.affine_mod7_a4_b4_c0.all_equations",
        "priority": 349,
        "table": (
            (0, 4, 1, 5, 2, 6, 3),
            (4, 1, 5, 2, 6, 3, 0),
            (1, 5, 2, 6, 3, 0, 4),
            (5, 2, 6, 3, 0, 4, 1),
            (2, 6, 3, 0, 4, 1, 5),
            (6, 3, 0, 4, 1, 5, 2),
            (3, 0, 4, 1, 5, 2, 6),
        ),
        "current_increment": 37_647,
        "raw_coverage": 49_542_748,
        "representative_pairs": {
            "new_order4_source_to_order5_target": (633, 24088),
            "new_order5_source_to_order4_target": (4721, 826),
            "new_order5_source_to_order5_target": (4721, 13494),
            "overlap_existing": (1, 27713),
        },
    },
)
STRUCTURED_ETP_ORDER4_REFUTATION516_TABLE = (
    (3, 2, 3, 3),
    (3, 3, 0, 3),
    (3, 3, 3, 3),
    (3, 3, 3, 3),
)
STRUCTURED_ETP_ORDER4_REFUTATION482_TABLE = (
    (0, 2, 3, 1),
    (2, 0, 1, 3),
    (3, 1, 0, 2),
    (1, 3, 2, 0),
)
STRUCTURED_ALL4X4_REFUTATION4_TABLE = (
    (0, 2, 3, 4, 5, 6, 7, 1),
    (4, 1, 6, 0, 7, 3, 5, 2),
    (5, 3, 2, 7, 0, 1, 4, 6),
    (6, 7, 4, 3, 1, 0, 2, 5),
    (7, 6, 1, 5, 4, 2, 0, 3),
    (1, 4, 7, 2, 6, 5, 3, 0),
    (2, 0, 5, 1, 3, 7, 6, 4),
    (3, 5, 0, 6, 2, 4, 1, 7),
)
STRUCTURED_AFFINE_MOD7_A2_B5_C6_TABLE = (
    (6, 4, 2, 0, 5, 3, 1),
    (1, 6, 4, 2, 0, 5, 3),
    (3, 1, 6, 4, 2, 0, 5),
    (5, 3, 1, 6, 4, 2, 0),
    (0, 5, 3, 1, 6, 4, 2),
    (2, 0, 5, 3, 1, 6, 4),
    (4, 2, 0, 5, 3, 1, 6),
)
STRUCTURED_AFFINE_MOD7_A5_B2_C6_TABLE = (
    (6, 1, 3, 5, 0, 2, 4),
    (4, 6, 1, 3, 5, 0, 2),
    (2, 4, 6, 1, 3, 5, 0),
    (0, 2, 4, 6, 1, 3, 5),
    (5, 0, 2, 4, 6, 1, 3),
    (3, 5, 0, 2, 4, 6, 1),
    (1, 3, 5, 0, 2, 4, 6),
)
STRUCTURED_AFFINE_MOD7_A6_B2_C0_TABLE = (
    (0, 2, 4, 6, 1, 3, 5),
    (6, 1, 3, 5, 0, 2, 4),
    (5, 0, 2, 4, 6, 1, 3),
    (4, 6, 1, 3, 5, 0, 2),
    (3, 5, 0, 2, 4, 6, 1),
    (2, 4, 6, 1, 3, 5, 0),
    (1, 3, 5, 0, 2, 4, 6),
)
FIN4_TABLE_1032_3210_2301_0123_TABLE = (
    (1, 0, 3, 2),
    (3, 2, 1, 0),
    (2, 3, 0, 1),
    (0, 1, 2, 3),
)
FIN3_TABLE_000_000_001_TABLE = ((0, 0, 0), (0, 0, 0), (0, 0, 1))
FIN3_TABLE_000_000_010_TABLE = ((0, 0, 0), (0, 0, 0), (0, 1, 0))
FIN3_TABLE_000_000_020_TABLE = ((0, 0, 0), (0, 0, 0), (0, 2, 0))
FIN3_TABLE_000_000_100_TABLE = ((0, 0, 0), (0, 0, 0), (1, 0, 0))
FIN3_TABLE_001_000_000_TABLE = ((0, 0, 1), (0, 0, 0), (0, 0, 0))
FIN3_TABLE_000_000_011_TABLE = ((0, 0, 0), (0, 0, 0), (0, 1, 1))
FIN3_TABLE_000_001_001_TABLE = ((0, 0, 0), (0, 0, 1), (0, 0, 1))
FIN3_TABLE_000_001_010_TABLE = ((0, 0, 0), (0, 0, 1), (0, 1, 0))
FIN3_TABLE_000_020_001_TABLE = ((0, 0, 0), (0, 2, 0), (0, 0, 1))
FIN3_TABLE_000_122_122_TABLE = ((0, 0, 0), (1, 2, 2), (1, 2, 2))
MODEL_FAMILY_ENUM_ORDER3_345_TABLE = ((0, 0, 0), (1, 1, 0), (2, 0, 2))
MODEL_FAMILY_ENUM_ORDER3_1521_TABLE = ((0, 0, 2), (0, 0, 2), (0, 2, 2))
MODEL_FAMILY_ENUM_ORDER3_3651_TABLE = ((0, 1, 2), (0, 0, 0), (0, 1, 2))
MODEL_FAMILY_ENUM_ORDER3_425_TABLE = ((0, 0, 0), (1, 2, 0), (2, 0, 1))
MODEL_FAMILY_ENUM_ORDER3_553_TABLE = ((0, 0, 0), (2, 0, 2), (1, 1, 0))
MODEL_FAMILY_ENUM_ORDER3_659_TABLE = ((0, 0, 0), (2, 2, 0), (1, 0, 1))
MODEL_FAMILY_PREDICATECHECK_SHARDS = (
    {
        "name": "witness_shard_1_enum_order3_345",
        "model_label": "enum_order3_345",
        "table": MODEL_FAMILY_ENUM_ORDER3_345_TABLE,
    },
    {
        "name": "witness_shard_2_enum_order3_1521",
        "model_label": "enum_order3_1521",
        "table": MODEL_FAMILY_ENUM_ORDER3_1521_TABLE,
    },
    {
        "name": "witness_shard_3_enum_order3_3651",
        "model_label": "enum_order3_3651",
        "table": MODEL_FAMILY_ENUM_ORDER3_3651_TABLE,
    },
    {
        "name": "witness_shard_4_enum_order3_425",
        "model_label": "enum_order3_425",
        "table": MODEL_FAMILY_ENUM_ORDER3_425_TABLE,
    },
    {
        "name": "witness_shard_5_enum_order3_553",
        "model_label": "enum_order3_553",
        "table": MODEL_FAMILY_ENUM_ORDER3_553_TABLE,
    },
    {
        "name": "witness_shard_6_enum_order3_659",
        "model_label": "enum_order3_659",
        "table": MODEL_FAMILY_ENUM_ORDER3_659_TABLE,
    },
)
DEFAULT_SINGLETON_SEEDBANK_PROOF_SOURCE = Path(
    "solvers/solo_official/versions/2026-05-12/v12/solver.py"
)
DEFAULT_SINGLETON_SEEDBANK_PROOF_BANK = Path(
    "data/processed/proof_banks/gpt_true_certificates"
)
SINGLETON_SEEDBANK_HARVEST_SOURCE_RUN_IDS = (
    "proofbank-20260513-singleton-seed-harvest-full",
    "proofbank-20260513-external-olean-harvest-011",
    "proofbank-20260514-singleton-collapse-seed-harvest-001",
    "proofbank-20260514-singleton-collapse-seed-harvest-002",
    "proofbank-20260514-singleton-collapse-seed-harvest-003",
    "proofbank-20260514-singleton-collapse-seed-harvest-003-retry-errors",
    "proofbank-20260514-external-olean-harvest-012",
    "proofbank-20260514-external-olean-harvest-013",
    "proofbank-20260514-external-olean-harvest-probe",
    "proofbank-20260514-registry-template-true-003",
    "proofbank-20260514-registry-template-true-004",
    "proofbank-20260514-registry-template-true-005",
    "proofbank-20260514-registry-template-true-006",
    "proofbank-20260514-registry-template-true-007",
    "proofbank-20260514-registry-template-true-008",
    "proofbank-20260514-registry-template-true-009",
    "proofbank-20260514-registry-template-true-010",
    "proofbank-20260514-registry-template-true-011",
    "proofbank-20260514-registry-template-true-012",
    "proofbank-20260514-registry-template-true-013",
    "proofbank-20260514-registry-template-true-014",
    "proofbank-20260514-registry-template-true-015",
    "proofbank-20260514-singleton-collapse-seed-harvest-004-retry-fixed-small-001",
    "proofbank-20260514-singleton-collapse-seed-harvest-004-retry-fixed-small-002",
    "proofbank-20260514-singleton-collapse-seed-harvest-006",
    "proofbank-20260514-singleton-collapse-seed-harvest-008",
    "proofbank-20260514-singleton-collapse-seed-harvest-009",
    "proofbank-20260514-singleton-collapse-seed-harvest-011",
    "proofbank-20260514-singleton-collapse-seed-harvest-013",
    "proofbank-20260514-singleton-collapse-seed-harvest-014",
    "proofbank-20260514-singleton-collapse-seed-harvest-016",
    "proofbank-20260514-singleton-collapse-seed-harvest-017",
    "proofbank-20260514-singleton-collapse-seed-harvest-018",
    "proofbank-20260514-singleton-collapse-seed-harvest-019",
    "proofbank-20260514-singleton-collapse-seed-harvest-020",
    "proofbank-20260514-singleton-collapse-seed-harvest-021",
    "proofbank-20260514-singleton-collapse-seed-harvest-022",
    "proofbank-20260514-singleton-collapse-seed-harvest-023",
    "proofbank-20260514-singleton-collapse-seed-harvest-024",
    "proofbank-20260514-singleton-collapse-seed-harvest-025",
    "proofbank-20260514-singleton-collapse-seed-harvest-026",
    "proofbank-20260514-singleton-collapse-seed-harvest-027",
    "proofbank-20260514-singleton-collapse-seed-harvest-028",
    "proofbank-20260514-singleton-collapse-seed-harvest-029",
    "proofbank-20260514-singleton-collapse-seed-harvest-030",
    "proofbank-20260514-singleton-collapse-seed-harvest-033",
    "proofbank-20260514-singleton-collapse-seed-harvest-034",
    "proofbank-20260514-singleton-collapse-seed-harvest-036",
    "proofbank-20260514-singleton-collapse-seed-harvest-037",
    "proofbank-20260514-singleton-collapse-seed-harvest-038",
    "proofbank-20260514-singleton-collapse-seed-harvest-039",
    "proofbank-20260514-singleton-collapse-seed-harvest-040",
    "order5-top3-shape-singleton-like-20260521",
    "topshape-seedgate-phase1-20260518",
    "topshape-seedgate-phase2-20260518",
    "topshape-seedgate-phase3-20260518",
    "topshape-seedgate-phase4-20260518",
    "topshape-seedgate-phase5-20260518",
    "topshape-seedgate-phase6-20260518",
)
SINGLETON_SEEDBANK_BARE_PROOF_SOURCE_RUN_IDS = (
    "order5-top3-shape-singleton-like-20260521",
    "topshape-seedgate-phase1-20260518",
    "topshape-seedgate-phase2-20260518",
    "topshape-seedgate-phase3-20260518",
    "topshape-seedgate-phase4-20260518",
    "topshape-seedgate-phase5-20260518",
    "topshape-seedgate-phase6-20260518",
)
SINGLETON_SEEDBANK_HARVEST_SOURCE_RUN_ID_PREFIXES = (
    "full-eq1-to-equation2-seedgate-",
)
SINGLETON_SEEDBANK_BARE_PROOF_SOURCE_RUN_ID_PREFIXES = (
    "full-eq1-to-equation2-seedgate-",
)
MAGMAEGG_SINGLETON_SEED_SOURCE_SIGNATURES = {
    485: "v0=(v1*(v0*(v2*(v0*v2))))",
    502: "v0=(v1*(v1*(v0*(v0*v2))))",
    710: "v0=(v1*(v1*((v0*v2)*v1)))",
    891: "v0=(v1*((v0*v2)*(v0*v2)))",
    1079: "v0=(v1*((v0*(v0*v2))*v1))",
    1080: "v0=(v1*((v0*(v0*v2))*v2))",
    1097: "v0=(v1*((v0*(v2*v1))*v1))",
    1111: "v0=(v1*((v1*(v0*v0))*v2))",
    1116: "v0=(v1*((v1*(v0*v2))*v1))",
    1164: "v0=(v1*((v2*(v1*v0))*v1))",
    1277: "v0=(v1*(((v0*v0)*v0)*v2))",
    1300: "v0=(v1*(((v0*v2)*v1)*v1))",
    1305: "v0=(v1*(((v0*v2)*v2)*v2))",
    1493: "v0=((v1*v0)*(v1*(v1*v2)))",
    1503: "v0=((v1*v0)*(v2*(v1*v1)))",
    1517: "v0=((v1*v1)*(v0*(v0*v2)))",
    1527: "v0=((v1*v1)*(v1*(v0*v2)))",
    1588: "v0=((v1*v2)*(v2*(v0*v2)))",
    1686: "v0=((v1*v0)*((v0*v1)*v2))",
    1720: "v0=((v1*v1)*((v0*v0)*v2))",
    1730: "v0=((v1*v1)*((v1*v0)*v2))",
    1756: "v0=((v1*v2)*((v0*v0)*v1))",
    1757: "v0=((v1*v2)*((v0*v0)*v2))",
    1891: "v0=((v1*(v0*v0))*(v2*v1))",
    1914: "v0=((v1*(v0*v2))*(v2*v2))",
    1933: "v0=((v1*(v1*v1))*(v0*v2))",
    1960: "v0=((v1*(v2*v0))*(v0*v2))",
    2102: "v0=(((v1*v0)*v1)*(v1*v2))",
    2118: "v0=(((v1*v0)*v2)*(v2*v3))",
    2136: "v0=(((v1*v1)*v1)*(v0*v2))",
    2179: "v0=(((v1*v2)*v1)*(v0*v1))",
    2334: "v0=((v1*(v1*(v0*v2)))*v1)",
    2510: "v0=((v1*((v0*v1)*v2))*v1)",
    2514: "v0=((v1*((v0*v2)*v0))*v1)",
    2551: "v0=((v1*((v1*v2)*v0))*v1)",
    2568: "v0=((v1*((v2*v0)*v0))*v1)",
    2585: "v0=((v1*((v2*v1)*v0))*v1)",
    2708: "v0=(((v1*v0)*(v1*v0))*v2)",
    2726: "v0=(((v1*v0)*(v2*v2))*v2)",
    2754: "v0=(((v1*v1)*(v2*v0))*v1)",
    2921: "v0=(((v1*(v0*v2))*v0)*v2)",
    3107: "v0=((((v1*v0)*v0)*v1)*v2)",
    3124: "v0=((((v1*v0)*v2)*v0)*v2)",
    3178: "v0=((((v1*v2)*v0)*v0)*v2)",
    3212: "v0=((((v1*v2)*v2)*v0)*v2)",
}
LAW_INSTANCE_TEMPLATES = (
    {
        "name": "left_self_absorption",
        "strategy_key": LEFT_SELF_ABSORPTION_INSTANCE_STRATEGY_KEY,
        "priority": 320,
        "law_equation": "a * (a * b) = a",
        "law": parse_equation("a * (a * b) = a"),
        "summary_zh": (
            "left self absorption law-instance 证明模板：source 可实例化为 "
            "a ◇ (a ◇ b) = a，target 是该 law 的实例。"
        ),
        "summary_en": (
            "Left self-absorption law-instance proof template: the source "
            "specializes to a ◇ (a ◇ b) = a, and the target is an instance "
            "of that law."
        ),
    },
    {
        "name": "right_self_absorption",
        "strategy_key": RIGHT_SELF_ABSORPTION_INSTANCE_STRATEGY_KEY,
        "priority": 321,
        "law_equation": "(a * b) * b = b",
        "law": parse_equation("(a * b) * b = b"),
        "summary_zh": (
            "right self absorption law-instance 证明模板：source 可实例化为 "
            "(a ◇ b) ◇ b = b，target 是该 law 的实例。"
        ),
        "summary_en": (
            "Right self-absorption law-instance proof template: the source "
            "specializes to (a ◇ b) ◇ b = b, and the target is an instance "
            "of that law."
        ),
    },
    {
        "name": "left_sandwich_absorption",
        "strategy_key": LEFT_SANDWICH_ABSORPTION_INSTANCE_STRATEGY_KEY,
        "priority": 322,
        "law_equation": "a * (b * a) = a",
        "law": parse_equation("a * (b * a) = a"),
        "summary_zh": (
            "left sandwich absorption law-instance 证明模板：source 可实例化为 "
            "a ◇ (b ◇ a) = a，target 是该 law 的实例。"
        ),
        "summary_en": (
            "Left sandwich-absorption law-instance proof template: the source "
            "specializes to a ◇ (b ◇ a) = a, and the target is an instance "
            "of that law."
        ),
    },
    {
        "name": "right_sandwich_absorption",
        "strategy_key": RIGHT_SANDWICH_ABSORPTION_INSTANCE_STRATEGY_KEY,
        "priority": 323,
        "law_equation": "(a * b) * a = a",
        "law": parse_equation("(a * b) * a = a"),
        "summary_zh": (
            "right sandwich absorption law-instance 证明模板：source 可实例化为 "
            "(a ◇ b) ◇ a = a，target 是该 law 的实例。"
        ),
        "summary_en": (
            "Right sandwich-absorption law-instance proof template: the source "
            "specializes to (a ◇ b) ◇ a = a, and the target is an instance "
            "of that law."
        ),
    },
)


@dataclass(frozen=True)
class SourceTargetSetsRule:
    source_ids: frozenset[int]
    target_ids: frozenset[int]
    excluded_blocks: tuple[tuple[frozenset[int], frozenset[int]], ...] = field(
        default_factory=tuple
    )

    @property
    def coverage_kind(self) -> str:
        return "source_target_sets"

    def covers(self, eq1_id: int, eq2_id: int) -> bool:
        if eq1_id == eq2_id:
            return False
        if eq1_id not in self.source_ids or eq2_id not in self.target_ids:
            return False
        return not any(
            eq1_id in excluded_sources and eq2_id in excluded_targets
            for excluded_sources, excluded_targets in self.excluded_blocks
        )

    def coverage_count(self) -> int:
        count = _block_count(self.source_ids, self.target_ids)
        return count - _block_union_count(
            self.source_ids,
            self.target_ids,
            self.excluded_blocks,
        )

    def iter_covered_pairs(self) -> Iterable[tuple[int, int]]:
        for eq1_id in sorted(self.source_ids):
            for eq2_id in sorted(self.target_ids):
                if self.covers(eq1_id, eq2_id):
                    yield eq1_id, eq2_id

    def manifest_fragment(self) -> dict:
        return {
            "coverage_kind": self.coverage_kind,
            "source_count": len(self.source_ids),
            "target_count": len(self.target_ids),
            "excluded_block_count": len(self.excluded_blocks),
            "coverage_count": self.coverage_count(),
        }


@dataclass(frozen=True)
class ExplicitPairsRule:
    pair_indexes: frozenset[int]
    law_count: int

    @property
    def coverage_kind(self) -> str:
        return "explicit_pairs"

    def covers(self, eq1_id: int, eq2_id: int) -> bool:
        if eq1_id == eq2_id:
            return False
        pair_index = ids_to_pair_index(eq1_id, eq2_id, law_count=self.law_count)
        return pair_index in self.pair_indexes

    def coverage_count(self) -> int:
        return len(self.pair_indexes)

    def iter_covered_pairs(self) -> Iterable[tuple[int, int]]:
        for pair_index in sorted(self.pair_indexes):
            yield pair_index_to_ids(pair_index, law_count=self.law_count)

    def manifest_fragment(self) -> dict:
        return {
            "coverage_kind": self.coverage_kind,
            "pair_count": len(self.pair_indexes),
            "coverage_count": self.coverage_count(),
        }


@dataclass(frozen=True)
class CompilerPairIndexesRule:
    pair_indexes: frozenset[int]
    law_count: int
    compiler_name: str

    @property
    def coverage_kind(self) -> str:
        return "compiler_pair_indexes"

    def covers(self, eq1_id: int, eq2_id: int) -> bool:
        if eq1_id == eq2_id:
            return False
        pair_index = ids_to_pair_index(eq1_id, eq2_id, law_count=self.law_count)
        return pair_index in self.pair_indexes

    def coverage_count(self) -> int:
        return len(self.pair_indexes)

    def iter_covered_pairs(self) -> Iterable[tuple[int, int]]:
        for pair_index in sorted(self.pair_indexes):
            yield pair_index_to_ids(pair_index, law_count=self.law_count)

    def manifest_fragment(self) -> dict:
        return {
            "coverage_kind": self.coverage_kind,
            "compiler_name": self.compiler_name,
            "pair_count": len(self.pair_indexes),
            "coverage_count": self.coverage_count(),
        }


PairIndexRule = Union[ExplicitPairsRule, CompilerPairIndexesRule]
CoverageRule = Union[SourceTargetSetsRule, ExplicitPairsRule, CompilerPairIndexesRule]


@dataclass(frozen=True)
class CoverageStrategy:
    strategy_key: str
    strategy_version: int
    verdict: bool
    coverage_rule: CoverageRule
    certificate_family: str
    priority: int = 1000
    summary_zh: str = ""
    summary_en: str = ""
    description_zh: str = ""
    description_en: str = ""
    legacy_strategy_keys: tuple[str, ...] = ()
    supersedes_strategy_ids: tuple[str, ...] = ()
    certificate_mode: str = ""
    verification_mode: str = ""
    coverage_rule_kind: str = ""
    certificate_generator: str = ""
    deprecated: bool = False
    evidence: dict = field(default_factory=dict)

    @property
    def strategy_id(self) -> str:
        return f"{self.strategy_key}.v{self.strategy_version}"

    def covers(self, eq1_id: int, eq2_id: int) -> bool:
        return not self.deprecated and self.coverage_rule.covers(eq1_id, eq2_id)

    def coverage_count(self) -> int:
        if self.deprecated:
            return 0
        return self.coverage_rule.coverage_count()

    def match_record(self) -> dict:
        return {
            "strategy_id": self.strategy_id,
            "strategy_key": self.strategy_key,
            "strategy_version": self.strategy_version,
            "verdict": self.verdict,
            "priority": self.priority,
            "coverage_kind": self.coverage_rule.coverage_kind,
            "certificate_family": self.certificate_family,
        }

    def manifest_record(self) -> dict:
        return {
            **self.match_record(),
            "deprecated": self.deprecated,
            "summary_zh": self.summary_zh,
            "summary_en": self.summary_en,
            "description_zh": self.description_zh,
            "description_en": self.description_en,
            "legacy_strategy_keys": list(self.legacy_strategy_keys),
            "legacy_strategy_ids": [
                f"{strategy_key}.v{self.strategy_version}"
                for strategy_key in self.legacy_strategy_keys
            ],
            "supersedes_strategy_ids": list(self.supersedes_strategy_ids),
            "certificate_mode": self.certificate_mode,
            "verification_mode": self.verification_mode,
            "coverage_rule_kind": self.coverage_rule_kind
            or self.coverage_rule.coverage_kind,
            "certificate_generator": self.certificate_generator,
            **self.coverage_rule.manifest_fragment(),
            **self.evidence,
        }

    def without_source_target_exclusions(self) -> "CoverageStrategy":
        if not isinstance(self.coverage_rule, SourceTargetSetsRule):
            return self
        if not self.coverage_rule.excluded_blocks:
            return self
        return replace(
            self,
            coverage_rule=replace(self.coverage_rule, excluded_blocks=()),
        )


@dataclass(frozen=True)
class Order5StrategyRegistry:
    law_count: int
    strategies: Sequence[CoverageStrategy]

    def find_covering_strategies(self, pair_index: int) -> list[dict]:
        eq1_id, eq2_id = pair_index_to_ids(pair_index, law_count=self.law_count)
        matches = [
            strategy.match_record()
            for strategy in self.strategies
            if strategy.covers(eq1_id, eq2_id)
        ]
        return sorted(matches, key=lambda record: (record["priority"], record["strategy_id"]))

    def find_canonical_strategy(
        self,
        pair_index: int,
        *,
        verdict: bool | None = None,
    ) -> dict | None:
        matches = self.find_covering_strategies(pair_index)
        if verdict is not None:
            matches = [match for match in matches if match["verdict"] is verdict]
        if not matches:
            return None
        verdicts = {match["verdict"] for match in matches}
        if verdict is None and len(verdicts) > 1:
            return None
        return matches[0]

    def strategies_manifest(self) -> list[dict]:
        return [strategy.manifest_record() for strategy in self.strategies]

    def without_source_target_exclusions(self) -> "Order5StrategyRegistry":
        return Order5StrategyRegistry(
            law_count=self.law_count,
            strategies=[
                strategy.without_source_target_exclusions()
                for strategy in self.strategies
            ],
        )

    def coverage_summary(
        self,
        *,
        exact_pair_threshold: int = 1_000_000,
        include_timings: bool = False,
    ) -> dict:
        del exact_pair_threshold
        total_started_at = time.perf_counter()
        timings: dict[str, float] = {}

        def record_timing(name: str, started_at: float) -> None:
            if include_timings:
                timings[f"{name}_seconds"] = time.perf_counter() - started_at

        started_at = time.perf_counter()
        total_pairs = pair_count(self.law_count)
        active_strategies = [strategy for strategy in self.strategies if not strategy.deprecated]
        record_timing("active_strategy_filter", started_at)

        started_at = time.perf_counter()
        strategy_counts = {
            strategy.strategy_id: strategy.coverage_count()
            for strategy in active_strategies
        }
        record_timing("strategy_counts", started_at)

        started_at = time.perf_counter()
        false_strategies = [
            strategy for strategy in active_strategies if strategy.verdict is False
        ]
        true_strategies = [
            strategy for strategy in active_strategies if strategy.verdict is True
        ]
        record_timing("verdict_partition", started_at)

        started_at = time.perf_counter()
        false_union = _union_count_for_rules(
            [strategy.coverage_rule for strategy in false_strategies]
        )
        record_timing("false_union", started_at)

        started_at = time.perf_counter()
        true_union = _union_count_for_rules(
            [strategy.coverage_rule for strategy in true_strategies]
        )
        record_timing("true_union", started_at)

        started_at = time.perf_counter()
        conflict_count = _conflict_count(false_strategies, true_strategies)
        record_timing("conflict_count", started_at)

        started_at = time.perf_counter()
        deterministic_false = false_union - conflict_count
        deterministic_true = true_union - conflict_count
        false_duplicate_coverage = (
            sum(strategy.coverage_count() for strategy in false_strategies)
            - false_union
        )
        true_duplicate_coverage = (
            sum(strategy.coverage_count() for strategy in true_strategies)
            - true_union
        )
        record_timing("derived_counts", started_at)

        source_target_excluded_block_count = sum(
            len(strategy.coverage_rule.excluded_blocks)
            for strategy in active_strategies
            if isinstance(strategy.coverage_rule, SourceTargetSetsRule)
        )
        summary = {
            "schema_version": 1,
            "coverage_scope": (
                "all_order5_directed_nonself"
                if source_target_excluded_block_count == 0
                else "source_target_sets_with_excluded_blocks"
            ),
            "includes_order4_source_to_order4_target": (
                source_target_excluded_block_count == 0
            ),
            "source_target_excluded_block_count": source_target_excluded_block_count,
            "allow_overlap": True,
            "canonical_selection": "lowest_priority_then_strategy_id",
            "total_pairs": total_pairs,
            "strategy_counts": strategy_counts,
            "raw_false_union_covered": false_union,
            "raw_true_union_covered": true_union,
            "deterministic_true_covered": deterministic_true,
            "deterministic_false_covered": deterministic_false,
            "same_verdict_overlap": false_duplicate_coverage + true_duplicate_coverage,
            "conflict_count": conflict_count,
            "unresolved_estimate": (
                total_pairs
                - deterministic_true
                - deterministic_false
            ),
        }
        if include_timings:
            timings["total_seconds"] = time.perf_counter() - total_started_at
            summary["timings_seconds"] = timings
        return summary

    def coverage_delta_summary(
        self,
        candidate_rule: CoverageRule,
        *,
        verdict: bool,
        exact_pair_threshold: int = 1_000_000,
    ) -> dict:
        """Compute exact incremental coverage for one bounded candidate rule."""
        raw_coverage = candidate_rule.coverage_count()
        if raw_coverage > exact_pair_threshold:
            raise ValueError(
                "candidate coverage "
                f"{raw_coverage} exceeds exact_pair_threshold {exact_pair_threshold}"
            )

        active_strategies = [
            strategy for strategy in self.strategies if not strategy.deprecated
        ]
        same_verdict_strategies = [
            strategy for strategy in active_strategies if strategy.verdict is verdict
        ]
        opposite_verdict_strategies = [
            strategy for strategy in active_strategies if strategy.verdict is not verdict
        ]

        same_verdict_overlap = 0
        opposite_verdict_overlap = 0
        conflict_increment = 0
        for eq1_id, eq2_id in candidate_rule.iter_covered_pairs():
            same_covered = any(
                strategy.coverage_rule.covers(eq1_id, eq2_id)
                for strategy in same_verdict_strategies
            )
            opposite_covered = any(
                strategy.coverage_rule.covers(eq1_id, eq2_id)
                for strategy in opposite_verdict_strategies
            )
            if same_covered:
                same_verdict_overlap += 1
            if opposite_covered:
                opposite_verdict_overlap += 1
            if opposite_covered and not same_covered:
                conflict_increment += 1

        union_increment = raw_coverage - same_verdict_overlap
        candidate_verdict_deterministic_increment = union_increment - conflict_increment
        total_deterministic_increment = union_increment - (2 * conflict_increment)
        return {
            "schema_version": 1,
            "verdict": verdict,
            "coverage_kind": candidate_rule.coverage_kind,
            "raw_coverage": raw_coverage,
            "same_verdict_overlap": same_verdict_overlap,
            "opposite_verdict_overlap": opposite_verdict_overlap,
            "conflict_increment": conflict_increment,
            "union_increment": union_increment,
            "candidate_verdict_deterministic_increment": (
                candidate_verdict_deterministic_increment
            ),
            "total_deterministic_increment": total_deterministic_increment,
            "unresolved_delta": -total_deterministic_increment,
        }


def _build_finmodel_setcheck_strategy(
    *,
    equations_path: Path,
    order4_max_id: int,
    table: tuple[tuple[int, ...], ...],
    strategy_key: str,
    priority: int,
    discovery_label: str,
    evidence_extra: dict | None = None,
) -> CoverageStrategy:
    _, source_ids, target_ids = _finmodel_sets(equations_path, table)
    table_signature = _table_signature(table)
    table_json = json.dumps([list(row) for row in table], separators=(",", ":"))
    model_family = _model_family(table)
    return CoverageStrategy(
        strategy_key=strategy_key,
        strategy_version=1,
        verdict=False,
        priority=priority,
        coverage_rule=SourceTargetSetsRule(
            source_ids=source_ids,
            target_ids=target_ids,
        ),
        certificate_family=f"finmodel_{model_family}",
        summary_zh=(
            f"Fin {len(table)} 显式表 {table_signature} 模型反例："
            "全量方程 source 成立、target 不成立。"
        ),
        summary_en=(
            f"Fin {len(table)} explicit table {table_signature} countermodel "
            "over all equations: sources hold, targets fail."
        ),
        description_zh=(
            f"使用 {discovery_label} 挖掘出的 Fin {len(table)} 显式运算表 "
            f"{table_json}。全量扫描 order<=5 方程，source 为该模型满足的所有"
            "方程，target 为该模型反驳的所有方程。因此任意 source -> target "
            "蕴含为 false。该策略按 current registry union increment 落地，"
            "并与已有 finite-model setcheck 策略存在重叠但提供新的 union 覆盖。"
        ),
        description_en=(
            f"Uses the Fin {len(table)} explicit operation table mined from "
            f"{discovery_label}: {table_json}. The model is checked against all "
            "order<=5 equations; sources are all equations satisfied by the model, "
            "and targets are all equations refuted by the model. Therefore every "
            "source -> target implication is false. This strategy was selected "
            "by current registry union increment and overlaps with existing "
            "finite-model setcheck strategies while adding new union coverage."
        ),
        certificate_mode="finmodel",
        verification_mode="setcheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="fin_table_decide",
        evidence={
            **_finmodel_setcheck_evidence(table, source_ids, target_ids),
            **(evidence_extra or {}),
        },
    )


def _build_affine_mod_setcheck_strategy(
    *,
    equations_path: Path,
    order4_max_id: int,
    modulus: int,
    a: int,
    b: int,
    c: int,
    table: tuple[tuple[int, ...], ...],
    strategy_key: str,
    priority: int,
    discovery_label: str,
    evidence_extra: dict | None = None,
) -> CoverageStrategy:
    parsed_features = _cached_parsed_equation_features(equations_path)
    source_ids = _affine_mod_source_ids(
        parsed_features,
        modulus=modulus,
        a=a,
        b=b,
        c=c,
    )
    all_ids = frozenset(feature.equation_id for feature, _ in parsed_features)
    target_ids = all_ids - source_ids
    table_signature = _table_signature(table)
    table_json = json.dumps([list(row) for row in table], separators=(",", ":"))
    model_family = _model_family(table)
    return CoverageStrategy(
        strategy_key=strategy_key,
        strategy_version=1,
        verdict=False,
        priority=priority,
        coverage_rule=SourceTargetSetsRule(
            source_ids=source_ids,
            target_ids=target_ids,
        ),
        certificate_family=f"finmodel_{model_family}",
        summary_zh=(
            f"Fin {len(table)} affine 模型 {table_signature} 反例："
            "source 由线性同余符号求值确认，target 为其补集。"
        ),
        summary_en=(
            f"Fin {len(table)} affine countermodel {table_signature}: sources "
            "are computed by symbolic linear evaluation modulo n and targets are "
            "their complement."
        ),
        description_zh=(
            f"使用 {discovery_label} 挖掘出的 Fin {len(table)} affine 运算表 "
            f"{table_json}。该表满足 x*y = {a}*x + {b}*y + {c} mod {modulus}，"
            "因此每个项可符号化为变量线性组合；source 集合由同余系数相等"
            "判定，target 为其余方程。order>=10 的 judge 证书使用 direct match "
            "编码，避免 finOpTable 的单 digit parser 限制。"
        ),
        description_en=(
            f"Uses the Fin {len(table)} affine operation table mined from "
            f"{discovery_label}: {table_json}. Since x*y = {a}*x + {b}*y + {c} "
            f"mod {modulus}, every term is evaluated symbolically as a linear "
            "combination of variables. Sources are equations with matching "
            "coefficients and targets are the remaining equations. For order>=10, "
            "judge certificates use direct match encoding to avoid finOpTable's "
            "single-digit parser limitation."
        ),
        certificate_mode="finmodel",
        verification_mode="setcheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="fin_table_decide",
        evidence={
            **_finmodel_setcheck_evidence(table, source_ids, target_ids),
            "affine_modulus": modulus,
            "affine_a": a,
            "affine_b": b,
            "affine_c": c,
            "source_set_method": "symbolic_affine_mod_linear_coefficients",
            **(evidence_extra or {}),
        },
    )


def _affine_mod_source_ids(
    parsed_features: Sequence[tuple[object, Equation]],
    *,
    modulus: int,
    a: int,
    b: int,
    c: int,
) -> frozenset[int]:
    return frozenset(
        feature.equation_id
        for feature, equation in parsed_features
        if _affine_mod_equation_holds(equation, modulus=modulus, a=a, b=b, c=c)
    )


def _affine_mod_equation_holds(
    equation: Equation,
    *,
    modulus: int,
    a: int,
    b: int,
    c: int,
) -> bool:
    left_const, left_coeffs = _affine_mod_expr_coefficients(
        equation.left,
        modulus=modulus,
        a=a,
        b=b,
        c=c,
    )
    right_const, right_coeffs = _affine_mod_expr_coefficients(
        equation.right,
        modulus=modulus,
        a=a,
        b=b,
        c=c,
    )
    if (left_const - right_const) % modulus != 0:
        return False
    return all(
        (left_coeffs.get(name, 0) - right_coeffs.get(name, 0)) % modulus == 0
        for name in set(left_coeffs) | set(right_coeffs)
    )


def _affine_mod_expr_coefficients(
    expr: Expr,
    *,
    modulus: int,
    a: int,
    b: int,
    c: int,
) -> tuple[int, dict[str, int]]:
    if expr.kind == "var":
        assert expr.value is not None
        return 0, {expr.value: 1 % modulus}
    assert expr.left is not None
    assert expr.right is not None
    left_const, left_coeffs = _affine_mod_expr_coefficients(
        expr.left,
        modulus=modulus,
        a=a,
        b=b,
        c=c,
    )
    right_const, right_coeffs = _affine_mod_expr_coefficients(
        expr.right,
        modulus=modulus,
        a=a,
        b=b,
        c=c,
    )
    coeffs: dict[str, int] = {}
    for name, value in left_coeffs.items():
        coeffs[name] = (coeffs.get(name, 0) + a * value) % modulus
    for name, value in right_coeffs.items():
        coeffs[name] = (coeffs.get(name, 0) + b * value) % modulus
    return (
        (a * left_const + b * right_const + c) % modulus,
        {name: value for name, value in coeffs.items() if value % modulus != 0},
    )


def build_model_family_predicatecheck_strategies(
    *,
    equations_path: Path = DEFAULT_EQ_SIZE5_PATH,
    order4_max_id: int = DEFAULT_ORDER4_MAX_ID,
    priority_start: int = 316,
) -> list[CoverageStrategy]:
    model_sets: list[tuple[dict, frozenset[int], frozenset[int]]] = []
    for shard in MODEL_FAMILY_PREDICATECHECK_SHARDS:
        _, source_ids, target_ids = _finmodel_sets(
            equations_path,
            shard["table"],
        )
        model_sets.append((shard, source_ids, target_ids))

    target_ids = frozenset.intersection(*(targets for _, _, targets in model_sets))
    source_union = frozenset().union(*(sources for _, sources, _ in model_sets))
    family_labels = tuple(str(shard["model_label"]) for shard, _, _ in model_sets)
    assigned_sources: set[int] = set()
    strategies: list[CoverageStrategy] = []
    for offset, (shard, source_ids, _) in enumerate(model_sets):
        partition_sources = frozenset(source_ids - assigned_sources)
        assigned_sources.update(source_ids)
        table = shard["table"]
        model_label = str(shard["model_label"])
        strategy_key = f"{MODEL_FAMILY_PREDICATECHECK_STRATEGY_KEY_PREFIX}.{shard['name']}"
        strategies.append(
            CoverageStrategy(
                strategy_key=strategy_key,
                strategy_version=1,
                verdict=False,
                priority=priority_start + offset,
                coverage_rule=SourceTargetSetsRule(
                    source_ids=partition_sources,
                    target_ids=target_ids,
                ),
                certificate_family=f"finmodel_predicatecheck_{model_label}",
                summary_zh=(
                    f"model-family predicatecheck shard：source 首次由 {model_label} "
                    "满足，target 被 residual top1 模型族全部反驳。"
                ),
                summary_en=(
                    f"Model-family predicatecheck shard: sources are first "
                    f"satisfied by {model_label}; targets are refuted by every "
                    "model in the residual top1 family."
                ),
                description_zh=(
                    "该策略来自 2026-05-19 false predicatecheck 挖掘。"
                    "模型族按固定顺序分区 source：每个 source 只归入第一个"
                    "满足它的模型 shard。target 集合取 6 个模型共同反驳的"
                    "方程，因此每个 shard 都可用自己的 Fin 3 表作为 false "
                    "certificate witness。该分解避免把多模型族误登记为单一"
                    "普通 setcheck 表。"
                ),
                description_en=(
                    "This strategy comes from the 2026-05-19 false "
                    "predicatecheck mining pass. The model family partitions "
                    "sources in a fixed first-satisfying-model order. The target "
                    "set is the intersection of equations refuted by all six "
                    "models, so each shard has its own Fin 3 certificate witness. "
                    "The decomposition avoids registering the multi-model family "
                    "as a single ordinary setcheck table."
                ),
                certificate_mode="finmodel",
                verification_mode="predicatecheck",
                coverage_rule_kind="source_target_sets",
                certificate_generator="fin_table_decide",
                evidence={
                    **_finmodel_setcheck_evidence(
                        table,
                        partition_sources,
                        target_ids,
                    ),
                    "predicate_family": "residual_model_family_20260519_top1",
                    "predicate_family_model_labels": list(family_labels),
                    "predicate_witness_model_label": model_label,
                    "predicate_source_partition_policy": (
                        "first_satisfying_model_in_family_order"
                    ),
                    "predicate_family_source_union_count": len(source_union),
                    "predicate_shared_target_count": len(target_ids),
                    "predicate_source_partition_count": len(partition_sources),
                    "predicate_mining_artifact": (
                        "data/processed/order5_strategy_registry/candidates/"
                        "false_predicate_model_family_controller_review_20260519.json"
                    ),
                },
            )
        )
    return strategies


def _build_law_instance_strategy(
    *,
    equations_path: Path,
    order4_max_id: int,
    template: dict,
) -> CoverageStrategy:
    _, source_ids, target_ids, counts = _law_instance_sets(
        equations_path,
        template["law"],
    )
    name = str(template["name"])
    law_equation = template["law"]
    return CoverageStrategy(
        strategy_key=str(template["strategy_key"]),
        strategy_version=1,
        verdict=True,
        priority=int(template["priority"]),
        coverage_rule=SourceTargetSetsRule(
            source_ids=source_ids,
            target_ids=target_ids,
        ),
        certificate_family=f"law_instance_{name}",
        summary_zh=str(template["summary_zh"]),
        summary_en=str(template["summary_en"]),
        description_zh=(
            "当 source 的某个实例等于 law "
            f"{lean_expr(law_equation.left, top=True)} = "
            f"{lean_expr(law_equation.right, top=True)} 或其反向时，"
            "证书先由 source hypothesis 构造该通用 law；随后如果 target "
            "是该 law 的实例或反向实例，则直接应用该 law 证明 target。"
        ),
        description_en=(
            "When an instance of the source equation is the law "
            f"{lean_expr(law_equation.left, top=True)} = "
            f"{lean_expr(law_equation.right, top=True)} or its reverse, "
            "the certificate first constructs that universal law from the "
            "source hypothesis. If the target is an instance of the law or "
            "its reverse, the target follows by applying the law."
        ),
        certificate_mode="proof_template",
        verification_mode="templatecheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator=f"{name}_instance",
        evidence=_law_instance_evidence(name, source_ids, target_ids, counts),
    )


def _build_target_instance_of_source_strategy(
    *,
    equations_path: Path,
    order4_max_id: int,
) -> CoverageStrategy:
    pair_indexes, evidence = _target_instance_of_source_pair_indexes(
        equations_path,
        order4_max_id,
    )
    return CoverageStrategy(
        strategy_key=TARGET_INSTANCE_OF_SOURCE_STRATEGY_KEY,
        strategy_version=1,
        verdict=True,
        priority=319,
        coverage_rule=ExplicitPairsRule(
            pair_indexes=pair_indexes,
            law_count=evidence["law_count"],
        ),
        certificate_family="law_instance_target_instance_of_source",
        summary_zh=(
            "target-instance-of-source 证明模板：target 或其反向是 source 的"
            "一阶项实例时，直接实例化 source hypothesis。"
        ),
        summary_en=(
            "Target-instance-of-source proof template: when the target equation "
            "or its reverse is a first-order term instance of the source, the "
            "certificate directly instantiates the source hypothesis."
        ),
        description_zh=(
            "该策略枚举所有 `(source, target)` pair：若 target 可由 source "
            "通过把 source 变量替换为 target 里的项得到，或 target 反向后满足"
            "同一条件，则 Lean certificate 只需对 target 变量 intro，然后用"
            "匹配到的 substitution terms 调用 source hypothesis；反向匹配时"
            "再取 `.symm`。该覆盖是 pair predicate，不能表达为 source × target "
            "笛卡尔积。"
        ),
        description_en=(
            "This strategy enumerates every `(source, target)` pair where the "
            "target, or its reverse orientation, is obtained from the source by "
            "substituting source variables with target terms. The Lean "
            "certificate introduces target variables and calls the source "
            "hypothesis with the matched substitution terms, using `.symm` for "
            "reverse-orientation matches. This is a pair predicate, not a "
            "source-by-target Cartesian product."
        ),
        supersedes_strategy_ids=tuple(
            f"{template['strategy_key']}.v1" for template in LAW_INSTANCE_TEMPLATES
        ),
        certificate_mode="proof_template",
        verification_mode="templatecheck",
        coverage_rule_kind="explicit_pairs",
        certificate_generator="target_instance_of_source",
        evidence=evidence,
    )


def _build_opnorm_hconst_match_collapse_strategy(
    *,
    equations_path: Path,
    pair_index_cache_path: Path = DEFAULT_OPNORM_HCONST_MATCH_COLLAPSE_PAIR_INDEX_CACHE,
    register_summary_path: Path = DEFAULT_OPNORM_HCONST_MATCH_COLLAPSE_REGISTER_SUMMARY,
) -> CoverageStrategy:
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_indexes, evidence = _opnorm_hconst_match_collapse_pair_indexes(
        law_count=law_count,
        pair_index_cache_path=pair_index_cache_path,
        register_summary_path=register_summary_path,
    )
    return CoverageStrategy(
        strategy_key=OPNORM_HCONST_MATCH_COLLAPSE_STRATEGY_KEY,
        strategy_version=1,
        verdict=True,
        priority=317,
        coverage_rule=CompilerPairIndexesRule(
            pair_indexes=pair_indexes,
            law_count=int(evidence["law_count"]),
            compiler_name="opnorm_hconst_match_collapse",
        ),
        certificate_family="opnorm_hconst_match_collapse",
        summary_zh=(
            "opnorm hconst match-collapse 证明模板：source 先推出局部常量性，"
            "再用一次 source 实例和 congrArg 重写闭合 target。"
        ),
        summary_en=(
            "opnorm hconst match-collapse proof template: the source derives "
            "local constancy, then a source instance and congrArg rewrites close "
            "the target."
        ),
        description_zh=(
            "该策略注册 top16/top13/top12/top08 residual shape bucket 中已经"
            "由 deterministic hconst compiler 精确枚举、并经 current profile "
            "复核无 false 冲突的 pair-index 集合。每个 pair 的 Lean certificate "
            "由 `render_first_hconst_match_collapse_certificate` 现场生成；"
            "registry 只保存 pair-index cache 摘要和 digest，不保存 proof body 表。"
        ),
        description_en=(
            "This strategy registers the pair-index set exactly enumerated by "
            "the deterministic hconst compiler in the top16/top13/top12/top08 "
            "residual shape buckets and rechecked against the current profile "
            "with no false conflicts. Certificates are generated on demand by "
            "`render_first_hconst_match_collapse_certificate`; the registry "
            "stores only a pair-index cache digest, not proof bodies."
        ),
        certificate_mode="proof_template",
        verification_mode="templatecheck+remote_smoke",
        coverage_rule_kind="compiler_pair_indexes",
        certificate_generator="opnorm_hconst_match_collapse",
        evidence=evidence,
    )


def _build_opnorm_hconst_sandwich_strategy(
    *,
    equations_path: Path,
    pair_index_cache_path: Path = DEFAULT_OPNORM_HCONST_SANDWICH_PAIR_INDEX_CACHE,
    register_summary_path: Path = DEFAULT_OPNORM_HCONST_SANDWICH_REGISTER_SUMMARY,
) -> CoverageStrategy:
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_indexes, evidence = _opnorm_hconst_sandwich_pair_indexes(
        law_count=law_count,
        pair_index_cache_path=pair_index_cache_path,
        register_summary_path=register_summary_path,
    )
    return CoverageStrategy(
        strategy_key=OPNORM_HCONST_SANDWICH_STRATEGY_KEY,
        strategy_version=1,
        verdict=True,
        priority=318,
        coverage_rule=CompilerPairIndexesRule(
            pair_indexes=pair_indexes,
            law_count=int(evidence["law_count"]),
            compiler_name="opnorm_hconst_sandwich_match_collapse",
        ),
        certificate_family="opnorm_hconst_sandwich_match_collapse",
        summary_zh=(
            "opnorm hconst sandwich match-collapse 证明模板：source 先推出"
            "局部常量性，再用 source 的 sandwich 实例和 hconst 重写闭合 target。"
        ),
        summary_en=(
            "opnorm hconst sandwich match-collapse proof template: the source "
            "first derives local constancy, then a sandwich-shaped source "
            "instance and hconst rewrites close the target."
        ),
        description_zh=(
            "该策略注册 y-left source family 的 23 个 source id 与 10 个 target "
            "shape bucket 的 exact current-residual pair-index 集合。候选由"
            " deterministic hconst-sandwich compiler 精确枚举，current profile "
            "v6 复核 union increment 263371、false conflict 0；代表性远程 "
            "judge smoke 在一次 transient HTTP 502 重试后 80/80 accepted。"
            "每个 pair 的 Lean certificate 由 "
            "`render_first_hconst_sandwich_match_collapse_certificate` 现场生成；"
            "registry 只保存 pair-index cache 摘要和 digest。"
        ),
        description_en=(
            "This strategy registers the exact current-residual pair-index set "
            "for 23 y-left source ids across 10 target shape buckets. The "
            "candidate was exactly enumerated by the deterministic "
            "hconst-sandwich compiler, rechecked against current profile v6 "
            "with union increment 263371 and zero false conflicts, and remote "
            "judge smoke accepted 80/80 after retrying one transient HTTP 502. "
            "Certificates are generated on demand by "
            "`render_first_hconst_sandwich_match_collapse_certificate`; the "
            "registry stores only a pair-index cache digest."
        ),
        certificate_mode="proof_template",
        verification_mode="templatecheck+remote_smoke",
        coverage_rule_kind="compiler_pair_indexes",
        certificate_generator="opnorm_hconst_sandwich_match_collapse",
        evidence=evidence,
    )


def _build_opnorm_hconst_lmrm_mainline_strategy(
    *,
    equations_path: Path,
    pair_index_cache_path: Path = DEFAULT_OPNORM_HCONST_LMRM_MAINLINE_PAIR_INDEX_CACHE,
    register_summary_path: Path = DEFAULT_OPNORM_HCONST_LMRM_MAINLINE_REGISTER_SUMMARY,
) -> CoverageStrategy:
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_indexes, evidence = _opnorm_hconst_lmrm_mainline_pair_indexes(
        law_count=law_count,
        pair_index_cache_path=pair_index_cache_path,
        register_summary_path=register_summary_path,
    )
    return CoverageStrategy(
        strategy_key=OPNORM_HCONST_LMRM_MAINLINE_STRATEGY_KEY,
        strategy_version=1,
        verdict=True,
        priority=319,
        coverage_rule=CompilerPairIndexesRule(
            pair_indexes=pair_indexes,
            law_count=int(evidence["law_count"]),
            compiler_name="opnorm_hconst_match_collapse_lmrm_mainline",
        ),
        certificate_family="opnorm_hconst_match_collapse",
        summary_zh=(
            "opnorm hconst lm/rm mainline 证明模板：source 推出左/右局部"
            "常量性，target 在 lm/rm/d23 形状中由 hconst match-collapse 闭合。"
        ),
        summary_en=(
            "opnorm hconst lm/rm mainline proof template: the source derives "
            "left/right local constancy, and hconst match-collapse closes "
            "lm/rm/d23 target shapes."
        ),
        description_zh=(
            "该策略注册 hconst_match_collapse compiler 在 lm1/rm1/d23 target "
            "子族上的 exact hit set。候选最初在 v5 profile 下形成，随后用"
            "当前 v7 coverage profile 重新复核：raw pair 1112800、same-true "
            "overlap 2345、union increment 1110455、false conflict 0；代表性"
            "远程 judge smoke 覆盖 lm1/rm1/d23 组件，合计 30/30 accepted。"
            "证书仍由 `render_first_hconst_match_collapse_certificate` 按 pair "
            "现场生成，registry 只保存 pair-index cache 摘要和 digest。"
        ),
        description_en=(
            "This strategy registers the exact hit set produced by the "
            "hconst_match_collapse compiler on lm1/rm1/d23 target subfamilies. "
            "The candidate was first formed against profile v5 and re-audited "
            "against the current v7 coverage profile: 1112800 raw pairs, 2345 "
            "same-true overlaps, 1110455 union increment, and zero false "
            "conflicts. Representative remote judge smoke accepted 30/30 "
            "across the lm1/rm1/d23 components. Certificates are generated on "
            "demand by `render_first_hconst_match_collapse_certificate`; the "
            "registry stores only a pair-index cache digest."
        ),
        certificate_mode="proof_template",
        verification_mode="templatecheck+remote_smoke",
        coverage_rule_kind="compiler_pair_indexes",
        certificate_generator="opnorm_hconst_match_collapse",
        evidence=evidence,
    )


def _build_opnorm_hconst_varmul_top01_strategy(
    *,
    equations_path: Path,
    pair_index_cache_path: Path = DEFAULT_OPNORM_HCONST_VARMUL_TOP01_PAIR_INDEX_CACHE,
    register_summary_path: Path = DEFAULT_OPNORM_HCONST_VARMUL_TOP01_REGISTER_SUMMARY,
) -> CoverageStrategy:
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_indexes, evidence = _opnorm_hconst_varmul_top01_pair_indexes(
        law_count=law_count,
        pair_index_cache_path=pair_index_cache_path,
        register_summary_path=register_summary_path,
    )
    return CoverageStrategy(
        strategy_key=OPNORM_HCONST_VARMUL_TOP01_STRATEGY_KEY,
        strategy_version=1,
        verdict=True,
        priority=320,
        coverage_rule=CompilerPairIndexesRule(
            pair_indexes=pair_indexes,
            law_count=int(evidence["law_count"]),
            compiler_name="opnorm_hconst_match_collapse_varmul_top01",
        ),
        certificate_family="opnorm_hconst_match_collapse",
        summary_zh=(
            "opnorm hconst var/mul top01 证明模板：source 为 var=mul 形状，"
            "target 在同一 current residual top bucket 中由 hconst match-collapse 闭合。"
        ),
        summary_en=(
            "opnorm hconst var/mul top01 proof template: var=mul-shaped "
            "sources close same-bucket current residual targets via hconst "
            "match-collapse."
        ),
        description_zh=(
            "该策略注册 current profile v8 中 "
            "`roots=var>mul|d=0>4|vc=4|lm=0|rm=0|vs=0` 到同形 target "
            "的 source offset 0..500 exact hit set。候选为 73400 个 "
            "order4->order4 true pair，v8 复核 union increment 73400、"
            "false conflict 0；代表性远程 judge smoke 30/30 accepted。"
            "证书由 `render_first_hconst_match_collapse_certificate` 按 pair "
            "现场生成，registry 只保存 pair-index cache 摘要和 digest。"
        ),
        description_en=(
            "This strategy registers the exact current-profile-v8 hit set from "
            "`roots=var>mul|d=0>4|vc=4|lm=0|rm=0|vs=0` sources to same-shape "
            "targets for source offset 0..500. The candidate contains 73400 "
            "order4->order4 true pairs, rechecked with v8 union increment "
            "73400 and zero false conflicts; representative remote judge "
            "smoke accepted 30/30. Certificates are generated on demand by "
            "`render_first_hconst_match_collapse_certificate`; the registry "
            "stores only a pair-index cache digest."
        ),
        certificate_mode="proof_template",
        verification_mode="templatecheck+remote_smoke",
        coverage_rule_kind="compiler_pair_indexes",
        certificate_generator="opnorm_hconst_match_collapse",
        evidence=evidence,
    )


def _build_opnorm_hconst_default_sandwich_top16_strategy(
    *,
    equations_path: Path,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_TOP16_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_TOP16_REGISTER_SUMMARY
    ),
) -> CoverageStrategy:
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_indexes, evidence = _opnorm_hconst_default_sandwich_top16_pair_indexes(
        law_count=law_count,
        pair_index_cache_path=pair_index_cache_path,
        register_summary_path=register_summary_path,
    )
    return CoverageStrategy(
        strategy_key=OPNORM_HCONST_DEFAULT_SANDWICH_TOP16_STRATEGY_KEY,
        strategy_version=1,
        verdict=True,
        priority=321,
        coverage_rule=CompilerPairIndexesRule(
            pair_indexes=pair_indexes,
            law_count=int(evidence["law_count"]),
            compiler_name="opnorm_hconst_default_sandwich_match_collapse_top16",
        ),
        certificate_family="opnorm_hconst_default_sandwich_match_collapse",
        summary_zh=(
            "opnorm hconst default-sandwich 证明模板：top16 source shape 中"
            "所有 source 使用默认首变量填充的 hconst sandwich 快路径闭合 target。"
        ),
        summary_en=(
            "opnorm hconst default-sandwich proof template: top16 source-shape "
            "sources close targets through a first-variable-default hconst "
            "sandwich fast path."
        ),
        description_zh=(
            "该策略注册 top16 shape "
            "`roots=mul>mul|d=1>4|vc=5|lm=0|rm=0|vs=0 -> "
            "roots=mul>mul|d=1>4|vc=3|lm=0|rm=0|vs=0` 中，由"
            " hconst-default-sandwich compiler 在 current profile v8 上精确枚举"
            "的 hit set。候选 raw/union pair 269662、false conflict 0；代表性"
            "远程 judge smoke 71/71 accepted。证书由 "
            "`render_first_hconst_default_sandwich_match_collapse_certificate` "
            "按 pair 现场生成，registry 只保存 pair-index cache 摘要和 digest。"
        ),
        description_en=(
            "This strategy registers the exact hit set produced by the "
            "hconst-default-sandwich compiler on the top16 shape bucket "
            "`roots=mul>mul|d=1>4|vc=5|lm=0|rm=0|vs=0 -> "
            "roots=mul>mul|d=1>4|vc=3|lm=0|rm=0|vs=0` against current profile "
            "v8. The candidate has 269662 raw/union pairs, zero false "
            "conflicts, and representative remote judge smoke accepted 71/71. "
            "Certificates are generated on demand by "
            "`render_first_hconst_default_sandwich_match_collapse_certificate`; "
            "the registry stores only a pair-index cache digest."
        ),
        certificate_mode="proof_template",
        verification_mode="templatecheck+remote_smoke",
        coverage_rule_kind="compiler_pair_indexes",
        certificate_generator="opnorm_hconst_default_sandwich_match_collapse",
        evidence=evidence,
    )


def _build_opnorm_hconst_default_sandwich_d14vc4_strategy(
    *,
    equations_path: Path,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_D14VC4_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_D14VC4_REGISTER_SUMMARY
    ),
) -> CoverageStrategy:
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_indexes, evidence = _opnorm_hconst_default_sandwich_d14vc4_pair_indexes(
        law_count=law_count,
        pair_index_cache_path=pair_index_cache_path,
        register_summary_path=register_summary_path,
    )
    return CoverageStrategy(
        strategy_key=OPNORM_HCONST_DEFAULT_SANDWICH_D14VC4_STRATEGY_KEY,
        strategy_version=1,
        verdict=True,
        priority=322,
        coverage_rule=CompilerPairIndexesRule(
            pair_indexes=pair_indexes,
            law_count=int(evidence["law_count"]),
            compiler_name="opnorm_hconst_default_sandwich_match_collapse_d14vc4",
        ),
        certificate_family="opnorm_hconst_default_sandwich_match_collapse",
        summary_zh=(
            "opnorm hconst default-sandwich d14vc4 证明模板：d1>4/vc4 "
            "source shape 通过默认首变量填充的 hconst sandwich 快路径闭合"
            " d1>4/vc4 与 d2>3/vc4 target。"
        ),
        summary_en=(
            "opnorm hconst default-sandwich d14vc4 proof template: d1>4/vc4 "
            "sources close d1>4/vc4 and d2>3/vc4 targets through a "
            "first-variable-default hconst sandwich fast path."
        ),
        description_zh=(
            "该策略注册 current profile v9 上由 hconst-default-sandwich compiler "
            "精确枚举的 d14/vc4 source multi-target hit set。覆盖两个 target "
            "shape：`roots=mul>mul|d=2>3|vc=4|lm=0|rm=0|vs=0` 与 "
            "`roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0`。候选 raw/union "
            "pair 2906410、false conflict 0；代表性远程 judge smoke "
            "86/86 accepted。证书由 "
            "`render_first_hconst_default_sandwich_match_collapse_certificate` "
            "按 pair 现场生成，registry 只保存 pair-index cache 摘要和 digest。"
        ),
        description_en=(
            "This strategy registers the exact current-profile-v9 d14/vc4 "
            "source multi-target hit set produced by the "
            "hconst-default-sandwich compiler. It covers two target shapes: "
            "`roots=mul>mul|d=2>3|vc=4|lm=0|rm=0|vs=0` and "
            "`roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0`. The candidate has "
            "2906410 raw/union pairs, zero false conflicts, and "
            "representative remote judge smoke accepted 86/86. Certificates "
            "are generated on demand by "
            "`render_first_hconst_default_sandwich_match_collapse_certificate`; "
            "the registry stores only a pair-index cache digest."
        ),
        certificate_mode="proof_template",
        verification_mode="templatecheck+remote_smoke",
        coverage_rule_kind="compiler_pair_indexes",
        certificate_generator="opnorm_hconst_default_sandwich_match_collapse",
        evidence=evidence,
    )


def _build_opnorm_hconst_default_sandwich_d13vc4_strategy(
    *,
    equations_path: Path,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_D13VC4_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_D13VC4_REGISTER_SUMMARY
    ),
) -> CoverageStrategy:
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_indexes, evidence = _opnorm_hconst_default_sandwich_d13vc4_pair_indexes(
        law_count=law_count,
        pair_index_cache_path=pair_index_cache_path,
        register_summary_path=register_summary_path,
    )
    return CoverageStrategy(
        strategy_key=OPNORM_HCONST_DEFAULT_SANDWICH_D13VC4_STRATEGY_KEY,
        strategy_version=1,
        verdict=True,
        priority=323,
        coverage_rule=CompilerPairIndexesRule(
            pair_indexes=pair_indexes,
            law_count=int(evidence["law_count"]),
            compiler_name="opnorm_hconst_default_sandwich_match_collapse_d13vc4",
        ),
        certificate_family="opnorm_hconst_default_sandwich_match_collapse",
        summary_zh=(
            "opnorm hconst default-sandwich d13vc4 证明模板：d1>3/vc4 "
            "source shape 通过默认首变量填充的 hconst sandwich 快路径闭合"
            " d1>3/vc4、d1>4/vc4 与 d2>3/vc4 target。"
        ),
        summary_en=(
            "opnorm hconst default-sandwich d13vc4 proof template: d1>3/vc4 "
            "sources close d1>3/vc4, d1>4/vc4, and d2>3/vc4 targets through "
            "a first-variable-default hconst sandwich fast path."
        ),
        description_zh=(
            "该策略注册 current profile v10 上由 hconst-default-sandwich compiler "
            "精确枚举的 d13/vc4 source multi-target hit set。覆盖三个 target "
            "shape：`roots=mul>mul|d=2>3|vc=4|lm=0|rm=0|vs=0`、"
            "`roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0` 与 "
            "`roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0`。候选 raw/union "
            "pair 3642181、false conflict 0；代表性远程 judge smoke "
            "90/90 accepted。证书由 "
            "`render_first_hconst_default_sandwich_match_collapse_certificate` "
            "按 pair 现场生成，registry 只保存 pair-index cache 摘要和 digest。"
        ),
        description_en=(
            "This strategy registers the exact current-profile-v10 d13/vc4 "
            "source multi-target hit set produced by the "
            "hconst-default-sandwich compiler. It covers three target shapes: "
            "`roots=mul>mul|d=2>3|vc=4|lm=0|rm=0|vs=0`, "
            "`roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0`, and "
            "`roots=mul>mul|d=1>4|vc=4|lm=0|rm=0|vs=0`. The candidate has "
            "3642181 raw/union pairs, zero false conflicts, and representative "
            "remote judge smoke accepted 90/90. Certificates are generated on "
            "demand by "
            "`render_first_hconst_default_sandwich_match_collapse_certificate`; "
            "the registry stores only a pair-index cache digest."
        ),
        certificate_mode="proof_template",
        verification_mode="templatecheck+remote_smoke",
        coverage_rule_kind="compiler_pair_indexes",
        certificate_generator="opnorm_hconst_default_sandwich_match_collapse",
        evidence=evidence,
    )


def _build_opnorm_hconst_default_sandwich_d14vc4_targetext_strategy(
    *,
    equations_path: Path,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_D14VC4_TARGETEXT_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_D14VC4_TARGETEXT_REGISTER_SUMMARY
    ),
) -> CoverageStrategy:
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_indexes, evidence = (
        _opnorm_hconst_default_sandwich_d14vc4_targetext_pair_indexes(
            law_count=law_count,
            pair_index_cache_path=pair_index_cache_path,
            register_summary_path=register_summary_path,
        )
    )
    return CoverageStrategy(
        strategy_key=OPNORM_HCONST_DEFAULT_SANDWICH_D14VC4_TARGETEXT_STRATEGY_KEY,
        strategy_version=1,
        verdict=True,
        priority=324,
        coverage_rule=CompilerPairIndexesRule(
            pair_indexes=pair_indexes,
            law_count=int(evidence["law_count"]),
            compiler_name=(
                "opnorm_hconst_default_sandwich_match_collapse_d14vc4_targetext"
            ),
        ),
        certificate_family="opnorm_hconst_default_sandwich_match_collapse",
        summary_zh=(
            "opnorm hconst default-sandwich d14vc4 target-extension 证明模板："
            "d1>4/vc4 source shape 通过默认首变量填充的 hconst sandwich 快路径"
            "闭合 d1>3/vc4、d1>4/vc3、d2>3/vc3 与 d1>3/vc3-lm1 target。"
        ),
        summary_en=(
            "opnorm hconst default-sandwich d14vc4 target-extension proof "
            "template: d1>4/vc4 sources close d1>3/vc4, d1>4/vc3, "
            "d2>3/vc3, and d1>3/vc3-lm1 targets through a "
            "first-variable-default hconst sandwich fast path."
        ),
        description_zh=(
            "该策略注册 current profile v11 上由 hconst-default-sandwich compiler "
            "精确枚举的 d14/vc4 source target-extension hit set。覆盖四个 "
            "target shape：`roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0`、"
            "`roots=mul>mul|d=1>4|vc=3|lm=0|rm=0|vs=0`、"
            "`roots=mul>mul|d=2>3|vc=3|lm=0|rm=0|vs=0` 与 "
            "`roots=mul>mul|d=1>3|vc=3|lm=1|rm=0|vs=0`。候选 raw/union "
            "pair 3104385、false conflict 0；代表性远程 judge smoke "
            "100/100 accepted。证书由 "
            "`render_first_hconst_default_sandwich_match_collapse_certificate` "
            "按 pair 现场生成，registry 只保存 pair-index cache 摘要和 digest。"
        ),
        description_en=(
            "This strategy registers the exact current-profile-v11 d14/vc4 "
            "source target-extension hit set produced by the "
            "hconst-default-sandwich compiler. It covers four target shapes: "
            "`roots=mul>mul|d=1>3|vc=4|lm=0|rm=0|vs=0`, "
            "`roots=mul>mul|d=1>4|vc=3|lm=0|rm=0|vs=0`, "
            "`roots=mul>mul|d=2>3|vc=3|lm=0|rm=0|vs=0`, and "
            "`roots=mul>mul|d=1>3|vc=3|lm=1|rm=0|vs=0`. The candidate has "
            "3104385 raw/union pairs, zero false conflicts, and representative "
            "remote judge smoke accepted 100/100. Certificates are generated "
            "on demand by "
            "`render_first_hconst_default_sandwich_match_collapse_certificate`; "
            "the registry stores only a pair-index cache digest."
        ),
        certificate_mode="proof_template",
        verification_mode="templatecheck+remote_smoke",
        coverage_rule_kind="compiler_pair_indexes",
        certificate_generator="opnorm_hconst_default_sandwich_match_collapse",
        evidence=evidence,
    )


def _build_opnorm_hconst_default_sandwich_lowvc_extension_strategy(
    *,
    equations_path: Path,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_LOWVC_EXTENSION_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_LOWVC_EXTENSION_REGISTER_SUMMARY
    ),
) -> CoverageStrategy:
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_indexes, evidence = (
        _opnorm_hconst_default_sandwich_lowvc_extension_pair_indexes(
            law_count=law_count,
            pair_index_cache_path=pair_index_cache_path,
            register_summary_path=register_summary_path,
        )
    )
    return CoverageStrategy(
        strategy_key=OPNORM_HCONST_DEFAULT_SANDWICH_LOWVC_EXTENSION_STRATEGY_KEY,
        strategy_version=1,
        verdict=True,
        priority=325,
        coverage_rule=CompilerPairIndexesRule(
            pair_indexes=pair_indexes,
            law_count=int(evidence["law_count"]),
            compiler_name=(
                "opnorm_hconst_default_sandwich_match_collapse_lowvc_extension"
            ),
        ),
        certificate_family="opnorm_hconst_default_sandwich_match_collapse",
        summary_zh=(
            "opnorm hconst default-sandwich low-vc extension 证明模板：低变量数"
            "source shape 通过默认首变量填充的 hconst sandwich 快路径闭合相邻"
            "target shape。"
        ),
        summary_en=(
            "opnorm hconst default-sandwich low-vc extension proof template: "
            "low-variable-count sources close adjacent target shapes through a "
            "first-variable-default hconst sandwich fast path."
        ),
        description_zh=(
            "该策略注册 current profile v12 上由 hconst-default-sandwich compiler "
            "精确枚举的 low-vc extension hit set。覆盖四个 source/target "
            "shape pair：d14/vc3 到 d23/vc4、d14/vc3 到 d14/vc4、"
            "d13/vc3 到 d13/vc4、d13/vc5 到 d14/vc3。候选 raw/union "
            "pair 1486451、false conflict 0；代表性远程 judge smoke "
            "80/80 accepted。证书由 "
            "`render_first_hconst_default_sandwich_match_collapse_certificate` "
            "按 pair 现场生成，registry 只保存 pair-index cache 摘要和 digest。"
        ),
        description_en=(
            "This strategy registers the exact current-profile-v12 low-vc "
            "extension hit set produced by the hconst-default-sandwich compiler. "
            "It covers four source/target shape pairs: d14/vc3 to d23/vc4, "
            "d14/vc3 to d14/vc4, d13/vc3 to d13/vc4, and d13/vc5 to d14/vc3. "
            "The candidate has 1486451 raw/union pairs, zero false conflicts, "
            "and representative remote judge smoke accepted 80/80. Certificates "
            "are generated on demand by "
            "`render_first_hconst_default_sandwich_match_collapse_certificate`; "
            "the registry stores only a pair-index cache digest."
        ),
        certificate_mode="proof_template",
        verification_mode="templatecheck+remote_smoke",
        coverage_rule_kind="compiler_pair_indexes",
        certificate_generator="opnorm_hconst_default_sandwich_match_collapse",
        evidence=evidence,
    )


def _build_opnorm_hconst_default_sandwich_topbucket_extension_strategy(
    *,
    equations_path: Path,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_TOPBUCKET_EXTENSION_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_TOPBUCKET_EXTENSION_REGISTER_SUMMARY
    ),
) -> CoverageStrategy:
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_indexes, evidence = (
        _opnorm_hconst_default_sandwich_topbucket_extension_pair_indexes(
            law_count=law_count,
            pair_index_cache_path=pair_index_cache_path,
            register_summary_path=register_summary_path,
        )
    )
    return CoverageStrategy(
        strategy_key=OPNORM_HCONST_DEFAULT_SANDWICH_TOPBUCKET_EXTENSION_STRATEGY_KEY,
        strategy_version=1,
        verdict=True,
        priority=326,
        coverage_rule=CompilerPairIndexesRule(
            pair_indexes=pair_indexes,
            law_count=int(evidence["law_count"]),
            compiler_name=(
                "opnorm_hconst_default_sandwich_match_collapse_topbucket_extension"
            ),
        ),
        certificate_family="opnorm_hconst_default_sandwich_match_collapse",
        summary_zh=(
            "opnorm hconst default-sandwich topbucket extension 证明模板："
            "post-lowvc residual top bucket 中的 source shape 通过默认首变量"
            "填充的 hconst sandwich 快路径闭合相邻 target shape。"
        ),
        summary_en=(
            "opnorm hconst default-sandwich topbucket extension proof "
            "template: post-lowvc residual top-bucket sources close adjacent "
            "target shapes through a first-variable-default hconst sandwich "
            "fast path."
        ),
        description_zh=(
            "该策略注册 current profile v13 上由 hconst-default-sandwich compiler "
            "精确枚举的 topbucket extension hit set。覆盖三个 source/target "
            "shape pair：d13/vc4 到 d14/vc3、d13/vc3 到 d14/vc4、"
            "d14/vc5 到 d14/vc4。候选 raw/union pair 1775820、false "
            "conflict 0；代表性远程 judge smoke 80/80 accepted。证书由 "
            "`render_first_hconst_default_sandwich_match_collapse_certificate` "
            "按 pair 现场生成，registry 只保存 pair-index cache 摘要和 digest。"
        ),
        description_en=(
            "This strategy registers the exact current-profile-v13 topbucket "
            "extension hit set produced by the hconst-default-sandwich "
            "compiler. It covers three source/target shape pairs: d13/vc4 to "
            "d14/vc3, d13/vc3 to d14/vc4, and d14/vc5 to d14/vc4. The "
            "candidate has 1775820 raw/union pairs, zero false conflicts, and "
            "representative remote judge smoke accepted 80/80. Certificates "
            "are generated on demand by "
            "`render_first_hconst_default_sandwich_match_collapse_certificate`; "
            "the registry stores only a pair-index cache digest."
        ),
        certificate_mode="proof_template",
        verification_mode="templatecheck+remote_smoke",
        coverage_rule_kind="compiler_pair_indexes",
        certificate_generator="opnorm_hconst_default_sandwich_match_collapse",
        evidence=evidence,
    )


def _build_opnorm_hconst_default_sandwich_frontier_extension_strategy(
    *,
    equations_path: Path,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_FRONTIER_EXTENSION_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_FRONTIER_EXTENSION_REGISTER_SUMMARY
    ),
) -> CoverageStrategy:
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_indexes, evidence = (
        _opnorm_hconst_default_sandwich_frontier_extension_pair_indexes(
            law_count=law_count,
            pair_index_cache_path=pair_index_cache_path,
            register_summary_path=register_summary_path,
        )
    )
    return CoverageStrategy(
        strategy_key=OPNORM_HCONST_DEFAULT_SANDWICH_FRONTIER_EXTENSION_STRATEGY_KEY,
        strategy_version=1,
        verdict=True,
        priority=327,
        coverage_rule=CompilerPairIndexesRule(
            pair_indexes=pair_indexes,
            law_count=int(evidence["law_count"]),
            compiler_name=(
                "opnorm_hconst_default_sandwich_match_collapse_frontier_extension"
            ),
        ),
        certificate_family="opnorm_hconst_default_sandwich_match_collapse",
        summary_zh=(
            "opnorm hconst default-sandwich frontier extension 证明模板："
            "topbucket extension 后的 residual frontier 中，多个相邻 source/"
            "target shape 仍可由默认首变量填充的 hconst sandwich 快路径闭合。"
        ),
        summary_en=(
            "opnorm hconst default-sandwich frontier extension proof template: "
            "after topbucket extension, several adjacent residual frontier "
            "source/target shapes still close through a first-variable-default "
            "hconst sandwich fast path."
        ),
        description_zh=(
            "该策略注册 current profile v14 上由 hconst-default-sandwich compiler "
            "精确枚举的 frontier extension hit set。覆盖五个 source/target "
            "shape pair：d13/vc4 到 d23/vc3、d14/vc5 到 d13/vc4、"
            "d14/vc4 到 d13/vc3、d13/vc3 到 d14/vc3、d14/vc5 到 "
            "d14/vc5。候选 raw/union pair 2994830、false conflict 0；"
            "代表性远程 judge smoke 90/90 accepted。证书由 "
            "`render_first_hconst_default_sandwich_match_collapse_certificate` "
            "按 pair 现场生成，registry 只保存 pair-index cache 摘要和 digest。"
        ),
        description_en=(
            "This strategy registers the exact current-profile-v14 frontier "
            "extension hit set produced by the hconst-default-sandwich compiler. "
            "It covers five source/target shape pairs: d13/vc4 to d23/vc3, "
            "d14/vc5 to d13/vc4, d14/vc4 to d13/vc3, d13/vc3 to d14/vc3, "
            "and d14/vc5 to d14/vc5. The candidate has 2994830 raw/union "
            "pairs, zero false conflicts, and representative remote judge "
            "smoke accepted 90/90. Certificates are generated on demand by "
            "`render_first_hconst_default_sandwich_match_collapse_certificate`; "
            "the registry stores only a pair-index cache digest."
        ),
        certificate_mode="proof_template",
        verification_mode="templatecheck+remote_smoke",
        coverage_rule_kind="compiler_pair_indexes",
        certificate_generator="opnorm_hconst_default_sandwich_match_collapse",
        evidence=evidence,
    )


def _build_opnorm_hconst_default_sandwich_edge_extension_strategy(
    *,
    equations_path: Path,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_EDGE_EXTENSION_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_EDGE_EXTENSION_REGISTER_SUMMARY
    ),
) -> CoverageStrategy:
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_indexes, evidence = (
        _opnorm_hconst_default_sandwich_edge_extension_pair_indexes(
            law_count=law_count,
            pair_index_cache_path=pair_index_cache_path,
            register_summary_path=register_summary_path,
        )
    )
    return CoverageStrategy(
        strategy_key=OPNORM_HCONST_DEFAULT_SANDWICH_EDGE_EXTENSION_STRATEGY_KEY,
        strategy_version=1,
        verdict=True,
        priority=328,
        coverage_rule=CompilerPairIndexesRule(
            pair_indexes=pair_indexes,
            law_count=int(evidence["law_count"]),
            compiler_name=(
                "opnorm_hconst_default_sandwich_match_collapse_edge_extension"
            ),
        ),
        certificate_family="opnorm_hconst_default_sandwich_match_collapse",
        summary_zh=(
            "opnorm hconst default-sandwich edge extension 证明模板：frontier "
            "extension 后的 residual edge 中，两个相邻 source/target shape "
            "仍可由默认首变量填充的 hconst sandwich 快路径闭合。"
        ),
        summary_en=(
            "opnorm hconst default-sandwich edge extension proof template: "
            "after frontier extension, two adjacent residual edge source/"
            "target shapes still close through a first-variable-default "
            "hconst sandwich fast path."
        ),
        description_zh=(
            "该策略注册 current profile v15 上由 hconst-default-sandwich compiler "
            "精确枚举的 edge extension hit set。覆盖两个 source/target shape "
            "pair：d13/vc5 到 d14/vc4、d14/vc3 到 d13/vc4。候选 "
            "raw/union pair 1069408、false conflict 0；代表性远程 judge "
            "smoke 首轮 79/80 accepted 且 1 条 remote request failure，重试后 "
            "80/80 accepted。证书由 "
            "`render_first_hconst_default_sandwich_match_collapse_certificate` "
            "按 pair 现场生成，registry 只保存 pair-index cache 摘要和 digest。"
        ),
        description_en=(
            "This strategy registers the exact current-profile-v15 edge "
            "extension hit set produced by the hconst-default-sandwich compiler. "
            "It covers two source/target shape pairs: d13/vc5 to d14/vc4 and "
            "d14/vc3 to d13/vc4. The candidate has 1069408 raw/union pairs, "
            "zero false conflicts, and representative remote judge smoke "
            "accepted 80/80 after retrying one remote request failure from an "
            "initial 79/80 run. Certificates are generated on demand by "
            "`render_first_hconst_default_sandwich_match_collapse_certificate`; "
            "the registry stores only a pair-index cache digest."
        ),
        certificate_mode="proof_template",
        verification_mode="templatecheck+remote_smoke",
        coverage_rule_kind="compiler_pair_indexes",
        certificate_generator="opnorm_hconst_default_sandwich_match_collapse",
        evidence=evidence,
    )


def _build_opnorm_hconst_default_sandwich_postedge_top40_extension_strategy(
    *,
    equations_path: Path,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE_TOP40_EXTENSION_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE_TOP40_EXTENSION_REGISTER_SUMMARY
    ),
) -> CoverageStrategy:
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_indexes, evidence = (
        _opnorm_hconst_default_sandwich_postedge_top40_extension_pair_indexes(
            law_count=law_count,
            pair_index_cache_path=pair_index_cache_path,
            register_summary_path=register_summary_path,
        )
    )
    return CoverageStrategy(
        strategy_key=OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE_TOP40_EXTENSION_STRATEGY_KEY,
        strategy_version=1,
        verdict=True,
        priority=329,
        coverage_rule=CompilerPairIndexesRule(
            pair_indexes=pair_indexes,
            law_count=int(evidence["law_count"]),
            compiler_name=(
                "opnorm_hconst_default_sandwich_match_collapse_postedge_top40_extension"
            ),
        ),
        certificate_family="opnorm_hconst_default_sandwich_match_collapse",
        summary_zh=(
            "opnorm hconst default-sandwich post-edge top40 extension 证明模板："
            "edge extension 后的 residual top shape 中，多个相邻 source/target "
            "shape 仍可由默认首变量填充的 hconst sandwich 快路径闭合。"
        ),
        summary_en=(
            "opnorm hconst default-sandwich post-edge top40 extension proof "
            "template: after edge extension, multiple residual top source/"
            "target shapes still close through a first-variable-default "
            "hconst sandwich fast path."
        ),
        description_zh=(
            "该策略注册 current profile v16 上由 hconst-default-sandwich compiler "
            "精确枚举的 post-edge top40 hit set。覆盖 23 个 positive "
            "source/target shape pair，候选 raw/union pair 5503838、false "
            "conflict 0；代表性远程 judge smoke 120/120 accepted。证书由 "
            "`render_first_hconst_default_sandwich_match_collapse_certificate` "
            "按 pair 现场生成，registry 只保存 pair-index cache 摘要和 digest。"
        ),
        description_en=(
            "This strategy registers the exact current-profile-v16 post-edge "
            "top40 hit set produced by the hconst-default-sandwich compiler. "
            "It covers 23 positive source/target shape pairs. The candidate "
            "has 5503838 raw/union pairs, zero false conflicts, and "
            "representative remote judge smoke accepted 120/120. Certificates "
            "are generated on demand by "
            "`render_first_hconst_default_sandwich_match_collapse_certificate`; "
            "the registry stores only a pair-index cache digest."
        ),
        certificate_mode="proof_template",
        verification_mode="templatecheck+remote_smoke",
        coverage_rule_kind="compiler_pair_indexes",
        certificate_generator="opnorm_hconst_default_sandwich_match_collapse",
        evidence=evidence,
    )


def _build_opnorm_hconst_default_sandwich_postedge2_top60_extension_strategy(
    *,
    equations_path: Path,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE2_TOP60_EXTENSION_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE2_TOP60_EXTENSION_REGISTER_SUMMARY
    ),
) -> CoverageStrategy:
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_indexes, evidence = (
        _opnorm_hconst_default_sandwich_postedge2_top60_extension_pair_indexes(
            law_count=law_count,
            pair_index_cache_path=pair_index_cache_path,
            register_summary_path=register_summary_path,
        )
    )
    return CoverageStrategy(
        strategy_key=OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE2_TOP60_EXTENSION_STRATEGY_KEY,
        strategy_version=1,
        verdict=True,
        priority=330,
        coverage_rule=CompilerPairIndexesRule(
            pair_indexes=pair_indexes,
            law_count=int(evidence["law_count"]),
            compiler_name=(
                "opnorm_hconst_default_sandwich_match_collapse_postedge2_top60_extension"
            ),
        ),
        certificate_family="opnorm_hconst_default_sandwich_match_collapse",
        summary_zh=(
            "opnorm hconst default-sandwich post-edge2 top60 extension 证明模板："
            "post-edge top40 后的 residual top shape 中，多个新 source/target "
            "shape 仍可由默认首变量填充的 hconst sandwich 快路径闭合。"
        ),
        summary_en=(
            "opnorm hconst default-sandwich post-edge2 top60 extension proof "
            "template: after the post-edge top40 batch, multiple new residual "
            "top source/target shapes still close through a first-variable-"
            "default hconst sandwich fast path."
        ),
        description_zh=(
            "该策略注册 current profile v17 上由 hconst-default-sandwich compiler "
            "精确枚举的 post-edge2 top60 hit set。覆盖 23 个 positive "
            "source/target shape pair，候选 raw/union pair 6295929、false "
            "conflict 0；代表性远程 judge smoke 120/120 accepted。证书由 "
            "`render_first_hconst_default_sandwich_match_collapse_certificate` "
            "按 pair 现场生成，registry 只保存 pair-index cache 摘要和 digest。"
        ),
        description_en=(
            "This strategy registers the exact current-profile-v17 post-edge2 "
            "top60 hit set produced by the hconst-default-sandwich compiler. "
            "It covers 23 positive source/target shape pairs. The candidate "
            "has 6295929 raw/union pairs, zero false conflicts, and "
            "representative remote judge smoke accepted 120/120. Certificates "
            "are generated on demand by "
            "`render_first_hconst_default_sandwich_match_collapse_certificate`; "
            "the registry stores only a pair-index cache digest."
        ),
        certificate_mode="proof_template",
        verification_mode="templatecheck+remote_smoke",
        coverage_rule_kind="compiler_pair_indexes",
        certificate_generator="opnorm_hconst_default_sandwich_match_collapse",
        evidence=evidence,
    )


def _build_opnorm_hconst_default_sandwich_postedge3_top80_extension_strategy(
    *,
    equations_path: Path,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE3_TOP80_EXTENSION_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE3_TOP80_EXTENSION_REGISTER_SUMMARY
    ),
) -> CoverageStrategy:
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_indexes, evidence = (
        _opnorm_hconst_default_sandwich_postedge3_top80_extension_pair_indexes(
            law_count=law_count,
            pair_index_cache_path=pair_index_cache_path,
            register_summary_path=register_summary_path,
        )
    )
    return CoverageStrategy(
        strategy_key=OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE3_TOP80_EXTENSION_STRATEGY_KEY,
        strategy_version=1,
        verdict=True,
        priority=331,
        coverage_rule=CompilerPairIndexesRule(
            pair_indexes=pair_indexes,
            law_count=int(evidence["law_count"]),
            compiler_name=(
                "opnorm_hconst_default_sandwich_match_collapse_postedge3_top80_extension"
            ),
        ),
        certificate_family="opnorm_hconst_default_sandwich_match_collapse",
        summary_zh=(
            "opnorm hconst default-sandwich post-edge3 top80 extension 证明模板："
            "postedge2 top60 后的 residual top shape 中，19 个 mul/mul "
            "source/target shape pair 仍可由默认首变量填充的 hconst sandwich "
            "快路径闭合。"
        ),
        summary_en=(
            "opnorm hconst default-sandwich post-edge3 top80 extension proof "
            "template: after the postedge2 top60 batch, 19 residual mul/mul "
            "source/target shape pairs still close through a first-variable-"
            "default hconst sandwich fast path."
        ),
        description_zh=(
            "该策略注册 current profile v18 上由 hconst-default-sandwich compiler "
            "精确枚举的 post-edge3 top80 mul/mul hit set。覆盖 19 个 positive "
            "source/target shape pair，候选 raw/union pair 3740105、false "
            "conflict 0；代表性远程 judge smoke 120/120 accepted。证书由 "
            "`render_first_hconst_default_sandwich_match_collapse_certificate` "
            "按 pair 现场生成，registry 只保存 pair-index cache 摘要和 digest。"
        ),
        description_en=(
            "This strategy registers the exact current-profile-v18 post-edge3 "
            "top80 mul/mul hit set produced by the hconst-default-sandwich "
            "compiler. It covers 19 positive source/target shape pairs. The "
            "candidate has 3740105 raw/union pairs, zero false conflicts, and "
            "representative remote judge smoke accepted 120/120. Certificates "
            "are generated on demand by "
            "`render_first_hconst_default_sandwich_match_collapse_certificate`; "
            "the registry stores only a pair-index cache digest."
        ),
        certificate_mode="proof_template",
        verification_mode="templatecheck+remote_smoke",
        coverage_rule_kind="compiler_pair_indexes",
        certificate_generator="opnorm_hconst_default_sandwich_match_collapse",
        evidence=evidence,
    )


def _build_opnorm_hconst_default_sandwich_postedge4_top100_extension_strategy(
    *,
    equations_path: Path,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE4_TOP100_EXTENSION_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE4_TOP100_EXTENSION_REGISTER_SUMMARY
    ),
) -> CoverageStrategy:
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_indexes, evidence = (
        _opnorm_hconst_default_sandwich_postedge4_top100_extension_pair_indexes(
            law_count=law_count,
            pair_index_cache_path=pair_index_cache_path,
            register_summary_path=register_summary_path,
        )
    )
    return CoverageStrategy(
        strategy_key=OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE4_TOP100_EXTENSION_STRATEGY_KEY,
        strategy_version=1,
        verdict=True,
        priority=332,
        coverage_rule=CompilerPairIndexesRule(
            pair_indexes=pair_indexes,
            law_count=int(evidence["law_count"]),
            compiler_name=(
                "opnorm_hconst_default_sandwich_match_collapse_postedge4_top100_extension"
            ),
        ),
        certificate_family="opnorm_hconst_default_sandwich_match_collapse",
        summary_zh=(
            "opnorm hconst default-sandwich post-edge4 top100 extension 证明模板："
            "postedge3 top80 后的 residual top shape 中，18 个长尾 source/target "
            "shape pair 仍可由默认首变量填充的 hconst sandwich 快路径闭合。"
        ),
        summary_en=(
            "opnorm hconst default-sandwich post-edge4 top100 extension proof "
            "template: after the postedge3 top80 batch, 18 residual tail "
            "source/target shape pairs still close through a first-variable-"
            "default hconst sandwich fast path."
        ),
        description_zh=(
            "该策略注册 current profile v19 上由 hconst-default-sandwich compiler "
            "精确枚举的 post-edge4 top100 hit set。覆盖 18 个 positive "
            "source/target shape pair，候选 raw/union pair 3117295、false "
            "conflict 0；代表性远程 judge smoke 120/120 accepted。证书由 "
            "`render_first_hconst_default_sandwich_match_collapse_certificate` "
            "按 pair 现场生成，registry 只保存 pair-index cache 摘要和 digest。"
        ),
        description_en=(
            "This strategy registers the exact current-profile-v19 post-edge4 "
            "top100 hit set produced by the hconst-default-sandwich compiler. "
            "It covers 18 positive source/target shape pairs. The candidate "
            "has 3117295 raw/union pairs, zero false conflicts, and "
            "representative remote judge smoke accepted 120/120. Certificates "
            "are generated on demand by "
            "`render_first_hconst_default_sandwich_match_collapse_certificate`; "
            "the registry stores only a pair-index cache digest."
        ),
        certificate_mode="proof_template",
        verification_mode="templatecheck+remote_smoke",
        coverage_rule_kind="compiler_pair_indexes",
        certificate_generator="opnorm_hconst_default_sandwich_match_collapse",
        evidence=evidence,
    )


def _build_opnorm_hconst_default_sandwich_postedge5_top120_extension_strategy(
    *,
    equations_path: Path,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE5_TOP120_EXTENSION_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE5_TOP120_EXTENSION_REGISTER_SUMMARY
    ),
) -> CoverageStrategy:
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_indexes, evidence = (
        _opnorm_hconst_default_sandwich_postedge5_top120_extension_pair_indexes(
            law_count=law_count,
            pair_index_cache_path=pair_index_cache_path,
            register_summary_path=register_summary_path,
        )
    )
    return CoverageStrategy(
        strategy_key=OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE5_TOP120_EXTENSION_STRATEGY_KEY,
        strategy_version=1,
        verdict=True,
        priority=333,
        coverage_rule=CompilerPairIndexesRule(
            pair_indexes=pair_indexes,
            law_count=int(evidence["law_count"]),
            compiler_name=(
                "opnorm_hconst_default_sandwich_match_collapse_postedge5_top120_extension"
            ),
        ),
        certificate_family="opnorm_hconst_default_sandwich_match_collapse",
        summary_zh=(
            "opnorm hconst default-sandwich post-edge5 top120 extension 证明模板："
            "postedge4 top100 后的 residual top shape 中，19 个长尾 source/target "
            "shape pair 仍可由默认首变量填充的 hconst sandwich 快路径闭合。"
        ),
        summary_en=(
            "opnorm hconst default-sandwich post-edge5 top120 extension proof "
            "template: after the postedge4 top100 batch, 19 residual tail "
            "source/target shape pairs still close through a first-variable-"
            "default hconst sandwich fast path."
        ),
        description_zh=(
            "该策略注册 current profile v20 上由 hconst-default-sandwich compiler "
            "精确枚举的 post-edge5 top120 hit set。覆盖 19 个 positive "
            "source/target shape pair，候选 raw/union pair 1913716、false "
            "conflict 0；代表性远程 judge smoke 120/120 accepted，其中 1 条"
            "基础设施请求失败后重试 accepted。证书由 "
            "`render_first_hconst_default_sandwich_match_collapse_certificate` "
            "按 pair 现场生成，registry 只保存 pair-index cache 摘要和 digest。"
        ),
        description_en=(
            "This strategy registers the exact current-profile-v20 post-edge5 "
            "top120 hit set produced by the hconst-default-sandwich compiler. "
            "It covers 19 positive source/target shape pairs. The candidate "
            "has 1913716 raw/union pairs, zero false conflicts, and "
            "representative remote judge smoke accepted 120/120 with one "
            "infrastructure request retried successfully. Certificates are "
            "generated on demand by "
            "`render_first_hconst_default_sandwich_match_collapse_certificate`; "
            "the registry stores only a pair-index cache digest."
        ),
        certificate_mode="proof_template",
        verification_mode="templatecheck+remote_smoke",
        coverage_rule_kind="compiler_pair_indexes",
        certificate_generator="opnorm_hconst_default_sandwich_match_collapse",
        evidence=evidence,
    )


def _build_opnorm_hconst_default_sandwich_postedge6_samplehit_top20_tail_strategy(
    *,
    equations_path: Path,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE6_SAMPLEHIT_TOP20_TAIL_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE6_SAMPLEHIT_TOP20_TAIL_REGISTER_SUMMARY
    ),
) -> CoverageStrategy:
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_indexes, evidence = (
        _opnorm_hconst_default_sandwich_postedge6_samplehit_top20_tail_pair_indexes(
            law_count=law_count,
            pair_index_cache_path=pair_index_cache_path,
            register_summary_path=register_summary_path,
        )
    )
    return CoverageStrategy(
        strategy_key=OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE6_SAMPLEHIT_TOP20_TAIL_STRATEGY_KEY,
        strategy_version=1,
        verdict=True,
        priority=334,
        coverage_rule=CompilerPairIndexesRule(
            pair_indexes=pair_indexes,
            law_count=int(evidence["law_count"]),
            compiler_name=(
                "opnorm_hconst_default_sandwich_match_collapse_postedge6_samplehit_top20_tail"
            ),
        ),
        certificate_family="opnorm_hconst_default_sandwich_match_collapse",
        summary_zh=(
            "opnorm hconst default-sandwich post-edge6 sample-hit top20 tail "
            "证明模板：postedge5 后 residual 样本中仍被 hconst-default-sandwich "
            "命中的 20 个长尾 shape pair。"
        ),
        summary_en=(
            "opnorm hconst default-sandwich post-edge6 sample-hit top20 tail "
            "proof template: after postedge5, 20 residual tail shape pairs "
            "still matched by the hconst-default-sandwich compiler."
        ),
        description_zh=(
            "该策略注册 current profile v22 上由 hconst-default-sandwich compiler "
            "精确枚举的 post-edge6 sample-hit top20 tail hit set。覆盖 20 个 "
            "positive source/target shape pair，候选 raw/union pair 2008676、"
            "false conflict 0；代表性远程 judge smoke 120/120 accepted。证书由 "
            "`render_first_hconst_default_sandwich_match_collapse_certificate` "
            "按 pair 现场生成，registry 只保存 pair-index cache 摘要和 digest。"
        ),
        description_en=(
            "This strategy registers the exact current-profile-v22 post-edge6 "
            "sample-hit top20 tail hit set produced by the hconst-default-"
            "sandwich compiler. It covers 20 positive source/target shape "
            "pairs. The candidate has 2008676 raw/union pairs, zero false "
            "conflicts, and representative remote judge smoke accepted "
            "120/120. Certificates are generated on demand by "
            "`render_first_hconst_default_sandwich_match_collapse_certificate`; "
            "the registry stores only a pair-index cache digest."
        ),
        certificate_mode="proof_template",
        verification_mode="templatecheck+remote_smoke",
        coverage_rule_kind="compiler_pair_indexes",
        certificate_generator="opnorm_hconst_default_sandwich_match_collapse",
        evidence=evidence,
    )


def _build_opnorm_hconst_default_sandwich_postedge7_samplehit_top20_tail_strategy(
    *,
    equations_path: Path,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE7_SAMPLEHIT_TOP20_TAIL_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE7_SAMPLEHIT_TOP20_TAIL_REGISTER_SUMMARY
    ),
) -> CoverageStrategy:
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_indexes, evidence = (
        _opnorm_hconst_default_sandwich_postedge7_samplehit_top20_tail_pair_indexes(
            law_count=law_count,
            pair_index_cache_path=pair_index_cache_path,
            register_summary_path=register_summary_path,
        )
    )
    return CoverageStrategy(
        strategy_key=OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE7_SAMPLEHIT_TOP20_TAIL_STRATEGY_KEY,
        strategy_version=1,
        verdict=True,
        priority=335,
        coverage_rule=CompilerPairIndexesRule(
            pair_indexes=pair_indexes,
            law_count=int(evidence["law_count"]),
            compiler_name=(
                "opnorm_hconst_default_sandwich_match_collapse_postedge7_samplehit_top20_tail"
            ),
        ),
        certificate_family="opnorm_hconst_default_sandwich_match_collapse",
        summary_zh=(
            "opnorm hconst default-sandwich post-edge7 sample-hit top20 tail "
            "证明模板：postedge6 后 residual 样本中继续被 "
            "hconst-default-sandwich 命中的 20 个长尾 shape pair。"
        ),
        summary_en=(
            "opnorm hconst default-sandwich post-edge7 sample-hit top20 tail "
            "proof template: after postedge6, 20 residual tail shape pairs "
            "still matched by the hconst-default-sandwich compiler."
        ),
        description_zh=(
            "该策略注册 current profile v23 上由 hconst-default-sandwich compiler "
            "精确枚举的 post-edge7 sample-hit top20 tail hit set。覆盖 20 个 "
            "positive source/target shape pair，候选 raw/union pair 2769157、"
            "false conflict 0；代表性远程 judge smoke 120/120 accepted。证书由 "
            "`render_first_hconst_default_sandwich_match_collapse_certificate` "
            "按 pair 现场生成，registry 只保存 pair-index cache 摘要和 digest。"
        ),
        description_en=(
            "This strategy registers the exact current-profile-v23 post-edge7 "
            "sample-hit top20 tail hit set produced by the hconst-default-"
            "sandwich compiler. It covers 20 positive source/target shape "
            "pairs. The candidate has 2769157 raw/union pairs, zero false "
            "conflicts, and representative remote judge smoke accepted "
            "120/120. Certificates are generated on demand by "
            "`render_first_hconst_default_sandwich_match_collapse_certificate`; "
            "the registry stores only a pair-index cache digest."
        ),
        certificate_mode="proof_template",
        verification_mode="templatecheck+remote_smoke",
        coverage_rule_kind="compiler_pair_indexes",
        certificate_generator="opnorm_hconst_default_sandwich_match_collapse",
        evidence=evidence,
    )


def _build_opnorm_hconst_default_sandwich_postedge8_d14vc5_frontier_multitarget20_strategy(
    *,
    equations_path: Path,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE8_D14VC5_FRONTIER_MULTITARGET20_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE8_D14VC5_FRONTIER_MULTITARGET20_REGISTER_SUMMARY
    ),
) -> CoverageStrategy:
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_indexes, evidence = (
        _opnorm_hconst_default_sandwich_postedge8_d14vc5_frontier_multitarget20_pair_indexes(
            law_count=law_count,
            pair_index_cache_path=pair_index_cache_path,
            register_summary_path=register_summary_path,
        )
    )
    return CoverageStrategy(
        strategy_key=OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE8_D14VC5_FRONTIER_MULTITARGET20_STRATEGY_KEY,
        strategy_version=1,
        verdict=True,
        priority=336,
        coverage_rule=CompilerPairIndexesRule(
            pair_indexes=pair_indexes,
            law_count=int(evidence["law_count"]),
            compiler_name=(
                "opnorm_hconst_default_sandwich_match_collapse_postedge8_d14vc5_frontier_multitarget20"
            ),
        ),
        certificate_family="opnorm_hconst_default_sandwich_match_collapse",
        summary_zh=(
            "opnorm hconst default-sandwich post-edge8 d14/vc5 frontier "
            "multitarget20 证明模板：postedge7 后 residual 中，d14/vc5 "
            "source 到 20 个 frontier target shape 仍可由默认首变量填充的 "
            "hconst sandwich 快路径闭合。"
        ),
        summary_en=(
            "opnorm hconst default-sandwich post-edge8 d14/vc5 frontier "
            "multitarget20 proof template: after postedge7, d14/vc5 "
            "residual sources still close to 20 frontier target shapes through "
            "a first-variable-default hconst sandwich fast path."
        ),
        description_zh=(
            "该策略注册 current profile v24 上由 hconst-default-sandwich compiler "
            "精确枚举的 d14/vc5 frontier multitarget20 hit set。20-target "
            "候选包含 19-target 候选并额外覆盖 d22/vc5 target shape；against "
            "postedge7 current 的 exact union increment 为 1210375、false "
            "conflict 0。组件级远程 judge smoke 合计 1000/1000 accepted。"
            "证书由 `render_first_hconst_default_sandwich_match_collapse_certificate` "
            "按 pair 现场生成，registry 只保存 pair-index cache 摘要和 digest。"
        ),
        description_en=(
            "This strategy registers the exact current-profile-v24 d14/vc5 "
            "frontier multitarget20 hit set produced by the hconst-default-"
            "sandwich compiler. The 20-target candidate contains the 19-target "
            "candidate and additionally covers the d22/vc5 target shape; "
            "against the postedge7 current baseline its exact union increment "
            "is 1210375 with zero false conflicts. Component remote judge "
            "smoke accepted 1000/1000. Certificates are generated on demand "
            "by `render_first_hconst_default_sandwich_match_collapse_certificate`; "
            "the registry stores only a pair-index cache digest."
        ),
        certificate_mode="proof_template",
        verification_mode="templatecheck+remote_smoke",
        coverage_rule_kind="compiler_pair_indexes",
        certificate_generator="opnorm_hconst_default_sandwich_match_collapse",
        evidence=evidence,
    )


def _build_opnorm_hconst_default_sandwich_postedge8_exact_top10_combined_tail_strategy(
    *,
    equations_path: Path,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE8_EXACT_TOP10_COMBINED_TAIL_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE8_EXACT_TOP10_COMBINED_TAIL_REGISTER_SUMMARY
    ),
) -> CoverageStrategy:
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_indexes, evidence = (
        _opnorm_hconst_default_sandwich_postedge8_exact_top10_combined_tail_pair_indexes(
            law_count=law_count,
            pair_index_cache_path=pair_index_cache_path,
            register_summary_path=register_summary_path,
        )
    )
    return CoverageStrategy(
        strategy_key=OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE8_EXACT_TOP10_COMBINED_TAIL_STRATEGY_KEY,
        strategy_version=1,
        verdict=True,
        priority=337,
        coverage_rule=CompilerPairIndexesRule(
            pair_indexes=pair_indexes,
            law_count=int(evidence["law_count"]),
            compiler_name=(
                "opnorm_hconst_default_sandwich_match_collapse_postedge8_exact_top10_combined_tail"
            ),
        ),
        certificate_family="opnorm_hconst_default_sandwich_match_collapse",
        summary_zh=(
            "opnorm hconst default-sandwich post-edge8 exact top10 combined "
            "tail 证明模板：postedge8 后 residual 中，10 个 sample-hit shape "
            "pair 仍可由默认首变量填充的 hconst sandwich 快路径闭合。"
        ),
        summary_en=(
            "opnorm hconst default-sandwich post-edge8 exact top10 combined "
            "tail proof template: after postedge8, ten sample-hit residual "
            "shape pairs still close through a first-variable-default hconst "
            "sandwich fast path."
        ),
        description_zh=(
            "该策略注册 current profile v25 上由 hconst-default-sandwich compiler "
            "精确枚举的 post-edge8 residual top10 tail hit set。候选 raw/union "
            "pair 677528、false conflict 0；代表性远程 judge smoke 100/100 "
            "accepted。证书由 "
            "`render_first_hconst_default_sandwich_match_collapse_certificate` "
            "按 pair 现场生成，registry 只保存 pair-index cache 摘要和 digest。"
        ),
        description_en=(
            "This strategy registers the exact current-profile-v25 post-edge8 "
            "residual top10 tail hit set produced by the hconst-default-"
            "sandwich compiler. The candidate has 677528 raw/union pairs, "
            "zero false conflicts, and representative remote judge smoke "
            "accepted 100/100. Certificates are generated on demand by "
            "`render_first_hconst_default_sandwich_match_collapse_certificate`; "
            "the registry stores only a pair-index cache digest."
        ),
        certificate_mode="proof_template",
        verification_mode="templatecheck+remote_smoke",
        coverage_rule_kind="compiler_pair_indexes",
        certificate_generator="opnorm_hconst_default_sandwich_match_collapse",
        evidence=evidence,
    )


def _build_opnorm_hconst_default_sandwich_round30_cumulative_hconst_family_strategy(
    *,
    equations_path: Path,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_ROUND30_CUMULATIVE_HCONST_FAMILY_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_ROUND30_CUMULATIVE_HCONST_FAMILY_REGISTER_SUMMARY
    ),
) -> CoverageStrategy:
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_indexes, evidence = (
        _opnorm_hconst_default_sandwich_round30_cumulative_hconst_family_pair_indexes(
            law_count=law_count,
            pair_index_cache_path=pair_index_cache_path,
            register_summary_path=register_summary_path,
        )
    )
    return CoverageStrategy(
        strategy_key=OPNORM_HCONST_DEFAULT_SANDWICH_ROUND30_CUMULATIVE_HCONST_FAMILY_STRATEGY_KEY,
        strategy_version=1,
        verdict=True,
        priority=338,
        coverage_rule=CompilerPairIndexesRule(
            pair_indexes=pair_indexes,
            law_count=int(evidence["law_count"]),
            compiler_name=(
                "opnorm_hconst_default_sandwich_match_collapse_round30_cumulative_hconst_family"
            ),
        ),
        certificate_family="opnorm_hconst_default_sandwich_match_collapse",
        summary_zh=(
            "opnorm hconst default-sandwich round30 cumulative hconst-family "
            "证明模板：合并 geologist hconst tail、round29 hconst-match tail "
            "和 round30 default-sandwich tail 的 declared-chain hit set。"
        ),
        summary_en=(
            "opnorm hconst default-sandwich round30 cumulative hconst-family "
            "proof template: declared-chain cumulative hit set combining the "
            "geologist hconst tail, round29 hconst-match tail, and round30 "
            "default-sandwich tail batches."
        ),
        description_zh=(
            "该策略注册 current profile v26 上由总控 declared-chain 审计得到的 "
            "cumulative hconst-family hit set。严格只收集组件 summary 声明的 "
            "candidate/hits 路径，exact raw/union pair 3468757，false "
            "conflict 0；组件级远程 judge smoke 证据已在审计 summary 中记录。"
            "证书由 `render_first_hconst_default_sandwich_match_collapse_certificate` "
            "按 pair 现场生成，registry 只保存 pair-index cache 摘要和 digest。"
        ),
        description_en=(
            "This strategy registers the current-profile-v26 cumulative "
            "hconst-family hit set audited by the controller declared-chain "
            "policy. It only collects candidate/hits paths declared by component "
            "summaries. The candidate has 3468757 exact raw/union pairs, zero "
            "false conflicts, and component remote judge smoke evidence recorded "
            "in the audit summary. Certificates are generated on demand by "
            "`render_first_hconst_default_sandwich_match_collapse_certificate`; "
            "the registry stores only a pair-index cache digest."
        ),
        certificate_mode="proof_template",
        verification_mode="templatecheck+remote_smoke",
        coverage_rule_kind="compiler_pair_indexes",
        certificate_generator="opnorm_hconst_default_sandwich_match_collapse",
        evidence=evidence,
    )


def _remote_smoke_counts(remote_smoke: object) -> tuple[int | None, int | None]:
    if not isinstance(remote_smoke, dict):
        return None, None
    accepted_count = remote_smoke.get("accepted_count")
    total_count = remote_smoke.get("total_count")
    if accepted_count is not None and total_count is not None:
        return int(accepted_count), int(total_count)
    accepted_count = remote_smoke.get("accepted_count_total")
    if accepted_count is not None and total_count is not None:
        return int(accepted_count), int(total_count)
    component_smoke = remote_smoke.get("component_smoke")
    if isinstance(component_smoke, list) and component_smoke:
        component_accepted = 0
        component_total = 0
        for component in component_smoke:
            if not isinstance(component, dict):
                return None, None
            if (
                component.get("accepted_count") is None
                or component.get("total_count") is None
            ):
                return None, None
            component_accepted += int(component["accepted_count"])
            component_total += int(component["total_count"])
        return component_accepted, component_total
    return None, None


@lru_cache(maxsize=16)
def _compiler_pair_indexes_from_cache(
    *,
    law_count: int,
    pair_index_cache_path: Path,
    register_summary_path: Path,
    template_family: str,
    template_source_scope: str,
    template_target_scope: str,
) -> tuple[frozenset[int], dict[str, object]]:
    pair_index_cache_path = Path(pair_index_cache_path)
    if not pair_index_cache_path.exists():
        raise FileNotFoundError(pair_index_cache_path)

    pair_indexes: set[int] = set()
    duplicate_count = 0
    digest = hashlib.sha256()
    with pair_index_cache_path.open(encoding="ascii") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                pair_index = int(stripped)
            except ValueError as exc:
                raise ValueError(
                    f"invalid pair_index on line {line_number} of "
                    f"{pair_index_cache_path}: {stripped!r}"
                ) from exc
            pair_index_to_ids(pair_index, law_count=law_count)
            if pair_index in pair_indexes:
                duplicate_count += 1
                continue
            pair_indexes.add(pair_index)

    for pair_index in sorted(pair_indexes):
        digest.update(f"{pair_index}\n".encode("ascii"))

    register_summary = _load_optional_json(register_summary_path)
    delta = (
        register_summary.get("delta")
        or register_summary.get("current_v26_delta")
        or register_summary.get("coverage_gate")
        or {}
    )
    if not isinstance(delta, dict):
        delta = {}
    remote_smoke = (
        register_summary.get("remote_judge_smoke")
        or register_summary.get("remote_smoke")
        or {}
    )
    smoke_accepted_count, smoke_total_count = _remote_smoke_counts(remote_smoke)
    if smoke_accepted_count is not None and smoke_total_count is not None:
        smoke_status = f"accepted_{smoke_accepted_count}_of_{smoke_total_count}"
    elif isinstance(remote_smoke, dict) and remote_smoke.get("status"):
        smoke_status = str(remote_smoke["status"])
    elif remote_smoke:
        smoke_status = "evidence_recorded"
    else:
        smoke_status = None

    component_groups = register_summary.get("component_groups")
    component_candidate_keys = []
    component_summary_paths = []
    component_group_keys = []
    if isinstance(component_groups, list):
        for component_group in component_groups:
            if not isinstance(component_group, dict):
                continue
            candidate_key = component_group.get("candidate_key")
            if isinstance(candidate_key, str):
                component_candidate_keys.append(candidate_key)
            summary_path = component_group.get("summary_path")
            if isinstance(summary_path, str):
                component_summary_paths.append(summary_path)
            group_key = component_group.get("group_key")
            if isinstance(group_key, str):
                component_group_keys.append(group_key)
    pair_indexes_manifest = register_summary.get("pair_indexes")
    if not isinstance(pair_indexes_manifest, dict):
        pair_indexes_manifest = {}
    declared_pair_index_cache_count = register_summary.get("pair_index_cache_count")
    if declared_pair_index_cache_count is None:
        declared_pair_index_cache_count = pair_indexes_manifest.get("count")
    declared_pair_index_cache_sha256 = register_summary.get("pair_index_cache_sha256")
    if declared_pair_index_cache_sha256 is None:
        declared_pair_index_cache_sha256 = pair_indexes_manifest.get("sha256")
    evidence = {
        "template_family": template_family,
        "template_verified": True,
        "law_count": law_count,
        "template_pair_count": len(pair_indexes),
        "template_source_scope": template_source_scope,
        "template_target_scope": template_target_scope,
        "template_pair_index_cache_path": str(pair_index_cache_path),
        "template_pair_index_sha256_newline_sorted": digest.hexdigest(),
        "template_duplicate_pair_index_count": duplicate_count,
        "template_declared_pair_index_cache_count": declared_pair_index_cache_count,
        "template_declared_pair_index_sha256": declared_pair_index_cache_sha256,
        "template_declared_pair_index_path": pair_indexes_manifest.get("path"),
        "template_current_union_increment": register_summary.get(
            "exact_union_increment",
            delta.get("union_increment")
            or delta.get("candidate_verdict_deterministic_increment"),
        ),
        "template_current_conflict_increment": register_summary.get(
            "conflict_increment",
            delta.get("conflict_increment"),
        ),
        "template_current_opposite_verdict_overlap": register_summary.get(
            "opposite_verdict_overlap",
            delta.get("opposite_verdict_overlap"),
        ),
        "template_current_same_verdict_overlap": register_summary.get(
            "same_verdict_overlap",
            delta.get("same_verdict_overlap"),
        ),
        "template_after_merge_projection_against_current_summary": register_summary.get(
            "after_merge_projection"
        ),
        "template_register_summary_path": str(register_summary_path),
        "template_summary_candidate_key": register_summary.get("candidate_key"),
        "template_component_count": register_summary.get("component_count")
        or (len(component_groups) if isinstance(component_groups, list) else None),
        "template_component_candidate_keys": component_candidate_keys,
        "template_component_summary_paths": component_summary_paths,
        "template_component_group_keys": component_group_keys,
        "template_remote_smoke": remote_smoke,
        "template_remote_smoke_accepted_count": smoke_accepted_count,
        "template_remote_smoke_total_count": smoke_total_count,
        "template_remote_smoke_status": smoke_status,
        "template_soundness_status": register_summary.get("soundness_status"),
    }
    return frozenset(pair_indexes), evidence


def _build_compiler_pair_indexes_strategy(
    *,
    equations_path: Path,
    pair_index_cache_path: Path,
    register_summary_path: Path,
    strategy_key: str,
    priority: int,
    compiler_name: str,
    certificate_family: str,
    certificate_generator: str,
    template_family: str,
    template_source_scope: str,
    template_target_scope: str,
    summary_zh: str,
    summary_en: str,
    description_zh: str,
    description_en: str,
) -> CoverageStrategy:
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_indexes, evidence = _compiler_pair_indexes_from_cache(
        law_count=law_count,
        pair_index_cache_path=pair_index_cache_path,
        register_summary_path=register_summary_path,
        template_family=template_family,
        template_source_scope=template_source_scope,
        template_target_scope=template_target_scope,
    )
    return CoverageStrategy(
        strategy_key=strategy_key,
        strategy_version=1,
        verdict=True,
        priority=priority,
        coverage_rule=CompilerPairIndexesRule(
            pair_indexes=pair_indexes,
            law_count=int(evidence["law_count"]),
            compiler_name=compiler_name,
        ),
        certificate_family=certificate_family,
        summary_zh=summary_zh,
        summary_en=summary_en,
        description_zh=description_zh,
        description_en=description_en,
        certificate_mode="proof_template",
        verification_mode="templatecheck+remote_smoke",
        coverage_rule_kind="compiler_pair_indexes",
        certificate_generator=certificate_generator,
        evidence=evidence,
    )


def _build_opnorm_hconst_match_ge25k_tail_batch_strategy(
    *,
    equations_path: Path,
    pair_index_cache_path: Path = DEFAULT_OPNORM_HCONST_MATCH_GE25K_TAIL_BATCH_PAIR_INDEX_CACHE,
    register_summary_path: Path = DEFAULT_OPNORM_HCONST_MATCH_GE25K_TAIL_BATCH_REGISTER_SUMMARY,
) -> CoverageStrategy:
    return _build_compiler_pair_indexes_strategy(
        equations_path=equations_path,
        pair_index_cache_path=pair_index_cache_path,
        register_summary_path=register_summary_path,
        strategy_key=OPNORM_HCONST_MATCH_GE25K_TAIL_BATCH_STRATEGY_KEY,
        priority=339,
        compiler_name="opnorm_hconst_match_collapse_ge25k_tail_batch",
        certificate_family="opnorm_hconst_match_collapse",
        certificate_generator="opnorm_hconst_match_collapse",
        template_family="opnorm_hconst_match_collapse_ge25k_tail_batch",
        template_source_scope="ge25k_tail_batch_sources",
        template_target_scope="ge25k_tail_batch_targets",
        summary_zh="opnorm hconst match-collapse ge25k 长尾批次证明模板。",
        summary_en="opnorm hconst match-collapse ge25k tail-batch proof template.",
        description_zh=(
            "该策略注册 2026-05-27 ge25k 长尾批次中由 hconst match-collapse "
            "compiler 精确枚举的 pair-index hit set。候选 raw/union pair "
            "1359062、false conflict 0；代表性远程 judge smoke 64/64 accepted。"
        ),
        description_en=(
            "This strategy registers the exact 2026-05-27 ge25k tail-batch "
            "pair-index hit set produced by the hconst match-collapse compiler. "
            "The candidate has 1,359,062 raw/union pairs, zero false conflicts, "
            "and representative remote judge smoke accepted 64/64."
        ),
    )


def _build_opnorm_hconst_match_ge10_tail_extension_strategy(
    *,
    equations_path: Path,
    pair_index_cache_path: Path = DEFAULT_OPNORM_HCONST_MATCH_GE10_TAIL_EXTENSION_PAIR_INDEX_CACHE,
    register_summary_path: Path = DEFAULT_OPNORM_HCONST_MATCH_GE10_TAIL_EXTENSION_REGISTER_SUMMARY,
) -> CoverageStrategy:
    return _build_compiler_pair_indexes_strategy(
        equations_path=equations_path,
        pair_index_cache_path=pair_index_cache_path,
        register_summary_path=register_summary_path,
        strategy_key=OPNORM_HCONST_MATCH_GE10_TAIL_EXTENSION_STRATEGY_KEY,
        priority=340,
        compiler_name="opnorm_hconst_match_collapse_ge10_tail_extension",
        certificate_family="opnorm_hconst_match_collapse",
        certificate_generator="opnorm_hconst_match_collapse",
        template_family="opnorm_hconst_match_collapse_ge10_tail_extension",
        template_source_scope="ge10_tail_extension_sources",
        template_target_scope="ge10_tail_extension_targets",
        summary_zh="opnorm hconst match-collapse ge10 tail extension 证明模板。",
        summary_en="opnorm hconst match-collapse ge10 tail-extension proof template.",
        description_zh=(
            "该策略注册 2026-05-27 ge10 tail extension 中由 hconst "
            "match-collapse compiler 精确枚举的 pair-index hit set。候选 "
            "raw/union pair 1138629、false conflict 0；代表性远程 judge "
            "smoke 134/134 accepted。"
        ),
        description_en=(
            "This strategy registers the exact 2026-05-27 ge10 tail-extension "
            "pair-index hit set produced by the hconst match-collapse compiler. "
            "The candidate has 1,138,629 raw/union pairs, zero false conflicts, "
            "and representative remote judge smoke accepted 134/134."
        ),
    )


def _build_opnorm_hconst_default_sandwich_ge25_lt100_tail_batch_strategy(
    *,
    equations_path: Path,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_GE25_LT100_TAIL_BATCH_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_GE25_LT100_TAIL_BATCH_REGISTER_SUMMARY
    ),
) -> CoverageStrategy:
    return _build_compiler_pair_indexes_strategy(
        equations_path=equations_path,
        pair_index_cache_path=pair_index_cache_path,
        register_summary_path=register_summary_path,
        strategy_key=OPNORM_HCONST_DEFAULT_SANDWICH_GE25_LT100_TAIL_BATCH_STRATEGY_KEY,
        priority=341,
        compiler_name=(
            "opnorm_hconst_default_sandwich_match_collapse_ge25_lt100_tail_batch"
        ),
        certificate_family="opnorm_hconst_default_sandwich_match_collapse",
        certificate_generator="opnorm_hconst_default_sandwich_match_collapse",
        template_family=(
            "opnorm_hconst_default_sandwich_match_collapse_ge25_lt100_tail_batch"
        ),
        template_source_scope="ge25_lt100_tail_batch_sources",
        template_target_scope="ge25_lt100_tail_batch_targets",
        summary_zh=(
            "opnorm hconst default-sandwich ge25/lt100 长尾批次证明模板。"
        ),
        summary_en=(
            "opnorm hconst default-sandwich ge25/lt100 tail-batch proof template."
        ),
        description_zh=(
            "该策略注册 2026-05-27 ge25/lt100 tail batch 中由 hconst-default-"
            "sandwich compiler 精确枚举的 pair-index hit set。候选 raw/union "
            "pair 3920576、false conflict 0；代表性远程 judge smoke 324/324 "
            "accepted，含 run-id collision 后重试 accepted 的请求。"
        ),
        description_en=(
            "This strategy registers the exact 2026-05-27 ge25/lt100 tail-batch "
            "pair-index hit set produced by the hconst-default-sandwich compiler. "
            "The candidate has 3,920,576 raw/union pairs, zero false conflicts, "
            "and representative remote judge smoke accepted 324/324, including "
            "successful retries after run-id collisions."
        ),
    )


def _build_opnorm_hconst_default_sandwich_lt25_remaining_tail_batch_strategy(
    *,
    equations_path: Path,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_LT25_REMAINING_TAIL_BATCH_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_LT25_REMAINING_TAIL_BATCH_REGISTER_SUMMARY
    ),
) -> CoverageStrategy:
    return _build_compiler_pair_indexes_strategy(
        equations_path=equations_path,
        pair_index_cache_path=pair_index_cache_path,
        register_summary_path=register_summary_path,
        strategy_key=OPNORM_HCONST_DEFAULT_SANDWICH_LT25_REMAINING_TAIL_BATCH_STRATEGY_KEY,
        priority=342,
        compiler_name=(
            "opnorm_hconst_default_sandwich_match_collapse_lt25_remaining_tail_batch"
        ),
        certificate_family="opnorm_hconst_default_sandwich_match_collapse",
        certificate_generator="opnorm_hconst_default_sandwich_match_collapse",
        template_family=(
            "opnorm_hconst_default_sandwich_match_collapse_lt25_remaining_tail_batch"
        ),
        template_source_scope="lt25_remaining_tail_batch_sources",
        template_target_scope="lt25_remaining_tail_batch_targets",
        summary_zh="opnorm hconst default-sandwich lt25 remaining tail 证明模板。",
        summary_en=(
            "opnorm hconst default-sandwich lt25 remaining-tail proof template."
        ),
        description_zh=(
            "该策略注册 2026-05-27 lt25 remaining tail batch 中由 hconst-default-"
            "sandwich compiler 精确枚举的 pair-index hit set。候选 raw/union "
            "pair 1243111、false conflict 0；代表性远程 judge smoke "
            "288/288 accepted。"
        ),
        description_en=(
            "This strategy registers the exact 2026-05-27 lt25 remaining-tail "
            "pair-index hit set produced by the hconst-default-sandwich compiler. "
            "The candidate has 1,243,111 raw/union pairs, zero false conflicts, "
            "and representative remote judge smoke accepted 288/288."
        ),
    )


def _build_hinst_ground_cc_accepted_family_rollup_strategy(
    *,
    equations_path: Path,
    pair_index_cache_path: Path = DEFAULT_HINST_GROUND_CC_ACCEPTED_FAMILY_ROLLUP_PAIR_INDEX_CACHE,
    register_summary_path: Path = DEFAULT_HINST_GROUND_CC_ACCEPTED_FAMILY_ROLLUP_REGISTER_SUMMARY,
) -> CoverageStrategy:
    return _build_compiler_pair_indexes_strategy(
        equations_path=equations_path,
        pair_index_cache_path=pair_index_cache_path,
        register_summary_path=register_summary_path,
        strategy_key=HINST_GROUND_CC_ACCEPTED_FAMILY_ROLLUP_STRATEGY_KEY,
        priority=343,
        compiler_name="hinst_ground_cc_accepted_family_rollup",
        certificate_family="hinst_ground_cc",
        certificate_generator="hinst_ground_cc",
        template_family="hinst_ground_cc_accepted_family_rollup",
        template_source_scope="accepted_hinst_ground_cc_family_sources",
        template_target_scope="accepted_hinst_ground_cc_family_targets",
        summary_zh="h-instantiated ground congruence closure accepted-family rollup。",
        summary_en="h-instantiated ground congruence-closure accepted-family rollup.",
        description_zh=(
            "该策略注册 2026-05-28 hinst ground-cc accepted-family rollup 的 "
            "pair-index hit set。rollup 吸收 mulroot_vc4_plus_d14vc5_mainline "
            "组件，另包含 broad mul-family 与两个 var-root tail 组件；候选 "
            "raw pair 4622829、current union increment 3117655、false "
            "conflict 0。组件级远程 smoke 均为 accepted。"
        ),
        description_en=(
            "This strategy registers the 2026-05-28 hinst ground-cc accepted-"
            "family rollup pair-index hit set. The rollup absorbs the "
            "mulroot_vc4_plus_d14vc5_mainline component and includes the broad "
            "mul-family plus two var-root tail components; it has 4,622,829 "
            "raw pairs, current union increment 3,117,655, zero false "
            "conflicts, and accepted component-level remote smoke."
        ),
    )


def _build_opnorm_hconst_plus_hstep_d14vc4_v17_tail_strategy(
    *,
    equations_path: Path,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_PLUS_HSTEP_D14VC4_V17_TAIL_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_PLUS_HSTEP_D14VC4_V17_TAIL_REGISTER_SUMMARY
    ),
) -> CoverageStrategy:
    strategy = _build_compiler_pair_indexes_strategy(
        equations_path=equations_path,
        pair_index_cache_path=pair_index_cache_path,
        register_summary_path=register_summary_path,
        strategy_key=OPNORM_HCONST_PLUS_HSTEP_D14VC4_V17_TAIL_STRATEGY_KEY,
        priority=344,
        compiler_name="opnorm_hconst_combined_plus_hstep_default_sandwich_d14vc4_v17_tail",
        certificate_family="opnorm_hconst_plus_hstep_match_collapse",
        certificate_generator="opnorm_hconst_plus_hstep_match_collapse",
        template_family="opnorm_hconst_combined_plus_hstep_default_sandwich_d14vc4_v17_tail",
        template_source_scope="hconst_combined_plus_hstep_d14vc4_v17_tail_sources",
        template_target_scope="hconst_combined_plus_hstep_d14vc4_v17_tail_targets",
        summary_zh="opnorm hconst combined plus hstep default-sandwich d14vc4/v17 tail 证明模板。",
        summary_en=(
            "opnorm hconst combined plus hstep default-sandwich d14vc4/v17 tail "
            "proof template."
        ),
        description_zh=(
            "该策略注册 2026-05-28 main-gate packet 中 hconst combined 与 "
            "hstep default-sandwich d14vc4/v17 tail 的合并 pair-index hit set。"
            "候选 raw pair 8350534、current union increment 1317879、false "
            "conflict 0；组件级远程 smoke 1022/1022 accepted。"
        ),
        description_en=(
            "This strategy registers the merged pair-index hit set from the "
            "2026-05-28 main-gate packet combining hconst components with the "
            "hstep default-sandwich d14vc4/v17 tail. It has 8,350,534 raw "
            "pairs, current union increment 1,317,879, zero false conflicts, "
            "and component-level remote smoke accepted 1022/1022."
        ),
    )
    absorbed_candidate_keys = [
        key
        for key in [
            strategy.evidence.get("template_summary_candidate_key"),
            *strategy.evidence.get("template_component_candidate_keys", []),
        ]
        if isinstance(key, str) and key.strip()
    ]
    return replace(
        strategy,
        evidence={
            **strategy.evidence,
            "absorbed_candidate_keys": absorbed_candidate_keys,
        },
    )


@lru_cache(maxsize=4)
def _proofbench_one_sided_constancy_rows(
    candidate_jsonl_path: Path,
) -> tuple[dict[str, object], ...]:
    candidate_jsonl_path = Path(candidate_jsonl_path)
    if not candidate_jsonl_path.exists():
        raise FileNotFoundError(candidate_jsonl_path)
    rows: list[dict[str, object]] = []
    with candidate_jsonl_path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            row = json.loads(stripped)
            if not isinstance(row, dict):
                raise ValueError(
                    f"invalid row on line {line_number} of {candidate_jsonl_path}"
                )
            rows.append(row)
    return tuple(rows)


def _proofbench_one_sided_constancy_row(
    *,
    candidate_jsonl_path: Path,
    candidate_key_fragment: str,
) -> dict[str, object]:
    matches = [
        row
        for row in _proofbench_one_sided_constancy_rows(candidate_jsonl_path)
        if candidate_key_fragment in str(row.get("candidate_key", ""))
    ]
    if len(matches) != 1:
        raise ValueError(
            f"expected one proofbench one-sided constancy row containing "
            f"{candidate_key_fragment!r}, found {len(matches)}"
        )
    return matches[0]


def _candidate_id_set(row: dict[str, object], key: str) -> frozenset[int]:
    values = row.get(key)
    if not isinstance(values, list):
        raise ValueError(f"candidate row is missing list field {key!r}")
    return frozenset(int(value) for value in values)


def _build_one_sided_constancy_recursive_nf_strategy(
    *,
    candidate_jsonl_path: Path,
    register_summary_path: Path,
    candidate_key_fragment: str,
    strategy_key: str,
    priority: int,
    template_family: str,
    certificate_family: str,
    summary_zh: str,
    summary_en: str,
    description_zh: str,
    description_en: str,
) -> CoverageStrategy:
    row = _proofbench_one_sided_constancy_row(
        candidate_jsonl_path=candidate_jsonl_path,
        candidate_key_fragment=candidate_key_fragment,
    )
    if row.get("coverage_kind") != "source_target_sets":
        raise ValueError(
            f"proofbench one-sided constancy row has unsupported coverage_kind: "
            f"{row.get('coverage_kind')!r}"
        )
    source_ids = _candidate_id_set(row, "source_ids")
    target_ids = _candidate_id_set(row, "target_ids")
    delta = row.get("current_v29_delta")
    if not isinstance(delta, dict):
        delta = {}
    remote_smoke = row.get("remote_judge_smoke")
    smoke_accepted_count, smoke_total_count = _remote_smoke_counts(remote_smoke)
    if smoke_accepted_count is not None and smoke_total_count is not None:
        smoke_status = f"accepted_{smoke_accepted_count}_of_{smoke_total_count}"
    elif isinstance(remote_smoke, dict) and remote_smoke.get("status"):
        smoke_status = str(remote_smoke["status"])
    elif remote_smoke:
        smoke_status = "evidence_recorded"
    else:
        smoke_status = None
    evidence = {
        "template_family": template_family,
        "template_verified": True,
        "absorbed_candidate_keys": [
            key
            for key in (
                row.get("candidate_key"),
                row.get("parent_candidate_key"),
                Path(register_summary_path).stem,
            )
            if isinstance(key, str) and key.strip()
        ],
        "template_candidate_key": row.get("candidate_key"),
        "template_parent_candidate_key": row.get("parent_candidate_key"),
        "template_candidate_jsonl_path": str(candidate_jsonl_path),
        "template_register_summary_path": str(register_summary_path),
        "template_source_count": len(source_ids),
        "template_target_count": len(target_ids),
        "template_raw_coverage": row.get("raw_coverage")
        or delta.get("raw_coverage"),
        "template_current_union_increment": row.get(
            "exact_union_increment",
            delta.get("union_increment")
            or delta.get("candidate_verdict_deterministic_increment"),
        ),
        "template_current_conflict_increment": delta.get("conflict_increment"),
        "template_current_opposite_verdict_overlap": delta.get(
            "opposite_verdict_overlap"
        ),
        "template_current_same_verdict_overlap": delta.get("same_verdict_overlap"),
        "template_after_merge_projection_against_current_summary": row.get(
            "after_merge_projection"
        ),
        "template_columnar_graph_preview": row.get("columnar_graph_preview"),
        "template_local_precheck_status": row.get("local_precheck_status"),
        "template_promotion_status": row.get("promotion_status"),
        "template_proof_surface": row.get("proof_surface"),
        "template_lean_certificate_surface": row.get("lean_certificate_surface"),
        "template_proof_template": row.get("proof_template"),
        "template_generalization_rule": row.get("template_generalization_rule"),
        "template_source_predicate": row.get("source_predicate"),
        "template_target_condition": row.get("target_condition"),
        "template_target_condition_count": row.get("target_condition_count"),
        "template_representative_pairs": row.get("representative_pairs"),
        "template_remote_smoke": remote_smoke,
        "template_remote_smoke_accepted_count": smoke_accepted_count,
        "template_remote_smoke_total_count": smoke_total_count,
        "template_remote_smoke_status": smoke_status,
        "template_soundness_status": row.get("soundness_status"),
    }
    return CoverageStrategy(
        strategy_key=strategy_key,
        strategy_version=1,
        verdict=True,
        priority=priority,
        coverage_rule=SourceTargetSetsRule(
            source_ids=source_ids,
            target_ids=target_ids,
        ),
        certificate_family=certificate_family,
        summary_zh=summary_zh,
        summary_en=summary_en,
        description_zh=description_zh,
        description_en=description_en,
        certificate_mode="proof_template",
        verification_mode="templatecheck+remote_smoke",
        coverage_rule_kind="source_target_sets",
        certificate_generator="one_sided_constancy_recursive_nf_explicit",
        evidence=evidence,
    )


def _build_one_sided_constancy_row_recursive_nf_strategy(
    *,
    equations_path: Path,
    candidate_jsonl_path: Path = (
        DEFAULT_PROOFBENCH_ONE_SIDED_CONSTANCY_EXPLICIT_NF_ACCEPTED_CANDIDATE_JSONL
    ),
    register_summary_path: Path = (
        DEFAULT_PROOFBENCH_ONE_SIDED_CONSTANCY_EXPLICIT_NF_ACCEPTED_SUMMARY
    ),
) -> CoverageStrategy:
    del equations_path
    return _build_one_sided_constancy_recursive_nf_strategy(
        candidate_jsonl_path=candidate_jsonl_path,
        register_summary_path=register_summary_path,
        candidate_key_fragment="rhs_omits_right_arg.row_constancy_recursive_nf",
        strategy_key=ONE_SIDED_CONSTANCY_ROW_RECURSIVE_NF_STRATEGY_KEY,
        priority=345,
        template_family="one_sided_constancy_rhs_omits_right_arg_row_recursive_nf",
        certificate_family="one_sided_constancy_recursive_nf",
        summary_zh="one-sided row-constancy recursive normal-form 证明模板。",
        summary_en="One-sided row-constancy recursive normal-form proof template.",
        description_zh=(
            "该策略注册右侧省略右参数的 one-sided constancy local lemma：source "
            "可推出 forall a b c, a*b = a*c，target 两侧 row-constancy "
            "recursive normal form 相同即成立。候选 raw coverage 6287120、"
            "current union increment 3595249、false conflict 0；explicit NF "
            "远程 smoke 4/4 accepted。"
        ),
        description_en=(
            "This strategy registers the one-sided constancy local lemma where "
            "the source omits the right argument and derives forall a b c, "
            "a*b = a*c. Targets hold when their row-constancy recursive normal "
            "forms agree. The candidate has raw coverage 6,287,120, current "
            "union increment 3,595,249, zero false conflicts, and explicit-NF "
            "remote smoke accepted 4/4."
        ),
    )


def _build_one_sided_constancy_column_recursive_nf_strategy(
    *,
    equations_path: Path,
    candidate_jsonl_path: Path = (
        DEFAULT_PROOFBENCH_ONE_SIDED_CONSTANCY_EXPLICIT_NF_ACCEPTED_CANDIDATE_JSONL
    ),
    register_summary_path: Path = (
        DEFAULT_PROOFBENCH_ONE_SIDED_CONSTANCY_EXPLICIT_NF_ACCEPTED_SUMMARY
    ),
) -> CoverageStrategy:
    del equations_path
    return _build_one_sided_constancy_recursive_nf_strategy(
        candidate_jsonl_path=candidate_jsonl_path,
        register_summary_path=register_summary_path,
        candidate_key_fragment="rhs_omits_left_arg.column_constancy_recursive_nf",
        strategy_key=ONE_SIDED_CONSTANCY_COLUMN_RECURSIVE_NF_STRATEGY_KEY,
        priority=346,
        template_family="one_sided_constancy_rhs_omits_left_arg_column_recursive_nf",
        certificate_family="one_sided_constancy_recursive_nf",
        summary_zh="one-sided column-constancy recursive normal-form 证明模板。",
        summary_en=(
            "One-sided column-constancy recursive normal-form proof template."
        ),
        description_zh=(
            "该策略注册右侧省略左参数的 one-sided constancy local lemma：source "
            "可推出 forall a b c, a*b = c*b，target 两侧 column-constancy "
            "recursive normal form 相同即成立。候选 raw coverage 6287120、"
            "current union increment 3375571、false conflict 0；explicit NF "
            "远程 smoke 4/4 accepted。"
        ),
        description_en=(
            "This strategy registers the one-sided constancy local lemma where "
            "the source omits the left argument and derives forall a b c, "
            "a*b = c*b. Targets hold when their column-constancy recursive "
            "normal forms agree. The candidate has raw coverage 6,287,120, "
            "current union increment 3,375,571, zero false conflicts, and "
            "explicit-NF remote smoke accepted 4/4."
        ),
    )


def _build_product_anchor_seed_lift_strategy(
    *,
    equations_path: Path,
    order4_max_id: int,
    candidate_jsonl_path: Path = DEFAULT_PRODUCT_ANCHOR_SEED_LIFT_CANDIDATE_JSONL,
) -> CoverageStrategy:
    _, source_ids, target_ids, counts = _product_anchor_seed_lift_sets(
        equations_path,
        candidate_jsonl_path=candidate_jsonl_path,
    )
    return CoverageStrategy(
        strategy_key=PRODUCT_ANCHOR_SEED_LIFT_ANY_PRODUCT_TARGET_STRATEGY_KEY,
        strategy_version=1,
        verdict=True,
        priority=312,
        coverage_rule=SourceTargetSetsRule(
            source_ids=source_ids,
            target_ids=target_ids,
        ),
        certificate_family="product_anchor_seed_lift",
        summary_zh=(
            "product-anchor seed-lift 证明库：已验证 source 可推出 product anchor "
            "seed，任意乘积根 target 成立。"
        ),
        summary_en=(
            "Product-anchor seed-lift proof bank: each verified source derives a "
            "product-anchor seed, so any product-root target equation holds."
        ),
        description_zh=(
            "该 tail 候选来自 proof bank 中已被远程 judge accepted 的 source→"
            "product-anchor seed 证明。注册层先校验 source id 对应方程签名，再"
            "复用 seed 证明得到 ∀ p q r s, p ◇ q = r ◇ s；随后左右根节点均"
            "为 ◇ 的 target 方程直接成立。canonical registry 覆盖全 order5 "
            "directed non-self pair space，包含 order4 source -> order4 target。"
        ),
        description_en=(
            "This tail candidate uses remote-judge-accepted proof-bank bodies "
            "from each source to a product-anchor seed. The registry verifies "
            "the source equation signature, reuses the seed proof to derive "
            "∀ p q r s, p ◇ q = r ◇ s, and then proves every target whose two "
            "sides are product-root terms. The canonical registry covers the "
            "full order5 directed non-self pair space, including order4 source "
            "to order4 target."
        ),
        certificate_mode="proof_bank",
        verification_mode="templatecheck+explicitbank",
        coverage_rule_kind="source_target_sets",
        certificate_generator="product_anchor_seed_lift",
        evidence=_product_anchor_seed_lift_evidence(
            source_ids,
            target_ids,
            counts,
            candidate_jsonl_path,
        ),
    )


def _build_product_collapse_strategy(
    *,
    equations_path: Path,
    order4_max_id: int,
    template: dict,
) -> CoverageStrategy:
    term_pattern = str(template["term_pattern"])
    _, source_ids, target_ids, counts = _product_collapse_sets(
        equations_path,
        term_pattern=term_pattern,
    )
    strategy_key = f"{PRODUCT_COLLAPSE_STRATEGY_KEY_PREFIX}.{template['name']}"
    summary_shape = str(template["summary_shape"])
    return CoverageStrategy(
        strategy_key=strategy_key,
        strategy_version=1,
        verdict=True,
        priority=311,
        coverage_rule=SourceTargetSetsRule(
            source_ids=source_ids,
            target_ids=target_ids,
        ),
        certificate_family="term_shape_anchor_product_collapse",
        summary_zh=(
            f"product-collapse 证明模板：source 强迫 {term_pattern} 形状项塌缩到"
            "同一个 disjoint anchor，左右均匹配该形状的 target 成立。"
        ),
        summary_en=(
            "Product-collapse proof template for "
            f"{summary_shape}: the source collapses this term shape to a "
            "disjoint anchor, so targets whose two sides match the shape hold."
        ),
        description_zh=(
            "当 source 的一边匹配指定 term_pattern，且另一边 anchor term 的变量"
            "与 pattern 变量不相交时，可用同一个 anchor 替换实例化 source "
            "hypothesis 两次。target 左右两边分别匹配同一 term_pattern，因此"
            "二者都等于该 anchor，最后用 trans/symm 得到 target 方程。重复"
            "pattern 变量要求 target 同一侧匹配到完全相同的子项。"
        ),
        description_en=(
            "When one side of the source matches the selected term_pattern and "
            "the other anchor term has variables disjoint from the pattern "
            "variables, the certificate instantiates the source hypothesis "
            "twice with the same anchor substitution. The two target sides "
            "both match the term pattern, so each equals the anchor and the "
            "target equation follows by trans/symm. Repeated pattern variables "
            "must match identical subterms within each target side."
        ),
        certificate_mode="proof_template",
        verification_mode="templatecheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="product_collapse",
        evidence=_product_collapse_evidence(
            term_pattern,
            source_ids,
            target_ids,
            counts,
        ),
    )


def build_setcheck_bank_strategies(
    *,
    bank_path: Path = DEFAULT_SETCHECK_BANK_PATH,
    equations_path: Path = DEFAULT_EQ_SIZE5_PATH,
    order4_max_id: int = DEFAULT_ORDER4_MAX_ID,
    priority_start: int = 360,
) -> list[CoverageStrategy]:
    if not bank_path.exists():
        return []
    rows = _read_jsonl_records(bank_path)
    payload = bank_path.read_bytes()
    strategies: list[CoverageStrategy] = []
    seen_strategy_keys: set[str] = set()
    for row_index, row in enumerate(rows, start=1):
        if row.get("active") is False:
            continue
        table = _normalize_table(row["table"])
        strategy_key = str(
            row.get("strategy_key")
            or f"{SETCHECK_BANK_STRATEGY_KEY_PREFIX}.{_table_signature(table)}"
        )
        if strategy_key in seen_strategy_keys:
            raise ValueError(f"duplicate setcheck bank strategy_key: {strategy_key}")
        seen_strategy_keys.add(strategy_key)
        label = str(row.get("label") or row.get("model_label") or strategy_key)
        evidence_extra = {
            "setcheck_bank_path": str(bank_path),
            "setcheck_bank_sha256": hashlib.sha256(payload).hexdigest(),
            "setcheck_bank_row_index": row_index,
            "discovery_label": label,
        }
        for key in (
            "current_increment",
            "independent_current_increment",
            "current_true_overlap_count",
            "raw_coverage",
            "provenance",
            "source_artifact",
            "selection_threshold",
            "seed_candidate_key",
            "smoke_input",
            "smoke_results",
            "smoke_summary",
            "official_smoke",
        ):
            if key in row:
                evidence_extra[key] = row[key]
        affine_params = _setcheck_bank_affine_params(row)
        if affine_params is None:
            strategy = _build_finmodel_setcheck_strategy(
                equations_path=equations_path,
                order4_max_id=order4_max_id,
                table=table,
                strategy_key=strategy_key,
                priority=int(row.get("priority", priority_start + len(strategies))),
                discovery_label=label,
                evidence_extra=evidence_extra,
            )
        else:
            strategy = _build_affine_mod_setcheck_strategy(
                equations_path=equations_path,
                order4_max_id=order4_max_id,
                modulus=affine_params["modulus"],
                a=affine_params["a"],
                b=affine_params["b"],
                c=affine_params["c"],
                table=table,
                strategy_key=strategy_key,
                priority=int(row.get("priority", priority_start + len(strategies))),
                discovery_label=label,
                evidence_extra=evidence_extra,
            )
        strategies.append(strategy)
    return strategies


def _setcheck_bank_affine_params(row: dict) -> dict[str, int] | None:
    aliases = {
        "modulus": ("modulus", "affine_modulus"),
        "a": ("a", "affine_a"),
        "b": ("b", "affine_b"),
        "c": ("c", "affine_c"),
    }
    values: dict[str, int] = {}
    for canonical, keys in aliases.items():
        value = next((row[key] for key in keys if key in row), None)
        if value is None:
            return None
        values[canonical] = int(value)
    return values


def build_predicatecheck_bank_strategies(
    *,
    bank_path: Path = DEFAULT_PREDICATECHECK_BANK_PATH,
    equations_path: Path = DEFAULT_EQ_SIZE5_PATH,
    order4_max_id: int = DEFAULT_ORDER4_MAX_ID,
) -> list[CoverageStrategy]:
    if not bank_path.exists():
        return []
    rows = _read_jsonl_records(bank_path)
    payload = bank_path.read_bytes()
    strategies: list[CoverageStrategy] = []
    seen_strategy_keys: set[str] = set()
    for row_index, row in enumerate(rows, start=1):
        if row.get("active") is False:
            continue
        predicate_family = str(row.get("predicate_family", ""))
        if predicate_family != "source_any_target_all_refuted_model_family":
            raise ValueError(
                f"unsupported predicatecheck bank family at row {row_index}: "
                f"{predicate_family}"
            )
        strategy_key_prefix = str(
            row.get("strategy_key")
            or f"{PREDICATECHECK_BANK_STRATEGY_KEY_PREFIX}.{row_index}"
        )
        if strategy_key_prefix in seen_strategy_keys:
            raise ValueError(
                f"duplicate predicatecheck bank strategy_key: {strategy_key_prefix}"
            )
        seen_strategy_keys.add(strategy_key_prefix)
        model_tables = row["model_tables"]
        model_labels = tuple(str(label) for label in row["model_labels"])
        if not model_labels:
            raise ValueError(f"predicatecheck bank row {row_index} has no models")
        model_sets: list[
            tuple[str, tuple[tuple[int, ...], ...], frozenset[int], frozenset[int]]
        ] = []
        for model_label in model_labels:
            table = _normalize_table(model_tables[model_label])
            _, source_ids, target_ids = _finmodel_sets(equations_path, table)
            model_sets.append((model_label, table, source_ids, target_ids))
        target_ids = frozenset.intersection(*(targets for _, _, _, targets in model_sets))
        assigned_sources: set[int] = set()
        priority_start = int(row.get("priority_start", 396 + len(strategies)))
        for offset, (model_label, table, source_ids, _) in enumerate(model_sets):
            partition_sources = frozenset(source_ids - assigned_sources)
            assigned_sources.update(source_ids)
            if not partition_sources:
                continue
            shard_name = f"witness_shard_{offset + 1}_{model_label}"
            strategies.append(
                CoverageStrategy(
                    strategy_key=f"{strategy_key_prefix}.{shard_name}",
                    strategy_version=1,
                    verdict=False,
                    priority=priority_start + offset,
                    coverage_rule=SourceTargetSetsRule(
                        source_ids=partition_sources,
                        target_ids=target_ids,
                    ),
                    certificate_family=f"finmodel_predicatecheck_{model_label}",
                    summary_zh=(
                        f"predicatecheck bank shard：source 首次由 {model_label} "
                        "满足，target 被该模型族全部反驳。"
                    ),
                    summary_en=(
                        f"Predicatecheck bank shard: sources are first satisfied "
                        f"by {model_label}; targets are refuted by every model in "
                        "the family."
                    ),
                    description_zh=(
                        "该策略来自 predicatecheck bank。模型族按固定顺序"
                        "分区 source，每个 source 只归入第一个满足它的模型；"
                        "target 集合取所有模型共同反驳的方程，因此每个 shard "
                        "都可用自己的有限模型作为 false certificate witness。"
                    ),
                    description_en=(
                        "This strategy comes from the predicatecheck bank. The "
                        "model family partitions sources in a fixed first-"
                        "satisfying-model order. Targets are the equations "
                        "refuted by every model in the family, so each shard "
                        "has its own finite-model false certificate witness."
                    ),
                    certificate_mode="finmodel",
                    verification_mode="predicatecheck",
                    coverage_rule_kind="source_target_sets",
                    certificate_generator="fin_table_decide",
                    evidence={
                        **_finmodel_setcheck_evidence(
                            table,
                            partition_sources,
                            target_ids,
                        ),
                        "predicatecheck_bank_path": str(bank_path),
                        "predicatecheck_bank_sha256": hashlib.sha256(payload).hexdigest(),
                        "predicatecheck_bank_row_index": row_index,
                        "predicate_family": predicate_family,
                        "predicate_label": str(row.get("label") or strategy_key_prefix),
                        "model_label": model_label,
                        "model_family_size": len(model_labels),
                        "model_family_labels": list(model_labels),
                        "source_partition": "first_satisfying_model",
                        "target_partition": "refuted_by_all_family_models",
                        "expected_family_source_count": row.get("source_count"),
                        "expected_family_target_count": row.get("target_count"),
                        "expected_exact_union_increment": row.get(
                            "exact_union_increment"
                        ),
                        "expected_raw_coverage": row.get("raw_coverage"),
                        "source_artifact": row.get("source_artifact"),
                        "official_smoke": row.get("official_smoke"),
                    },
                )
            )
        expected_source_count = row.get("source_count")
        if expected_source_count is not None and len(assigned_sources) != int(
            expected_source_count
        ):
            raise ValueError(
                f"predicatecheck bank row {row_index} source count mismatch: "
                f"expected {expected_source_count}, got {len(assigned_sources)}"
            )
        expected_target_count = row.get("target_count")
        if expected_target_count is not None and len(target_ids) != int(
            expected_target_count
        ):
            raise ValueError(
                f"predicatecheck bank row {row_index} target count mismatch: "
                f"expected {expected_target_count}, got {len(target_ids)}"
            )
    return strategies


def build_paircheck_bank_strategy(
    *,
    bank_path: Path = DEFAULT_PAIRCHECK_BANK_PATH,
    law_count: int,
    priority: int = 400,
) -> CoverageStrategy:
    rows = _read_jsonl_records(bank_path)
    max_pair_index = pair_count(law_count)
    pair_indexes: set[int] = set()
    remote_smoke_accepted_count = 0
    true_conflict_count = 0
    for row in rows:
        if row.get("registry_ready") is False:
            continue
        if row.get("true_conflict") is True:
            true_conflict_count += 1
            continue
        pair_index = int(row["pair_index"])
        if pair_index < 0 or pair_index >= max_pair_index:
            raise ValueError(f"pair_index out of range for law_count={law_count}: {pair_index}")
        pair_indexes.add(pair_index)
        if row.get("remote_smoke_accepted") is True or (
            row.get("remote_smoke_status") == "accepted"
        ):
            remote_smoke_accepted_count += 1

    payload = bank_path.read_bytes()
    return CoverageStrategy(
        strategy_key=PAIRCHECK_BANK_STRATEGY_KEY,
        strategy_version=1,
        verdict=False,
        priority=priority,
        coverage_rule=ExplicitPairsRule(
            pair_indexes=frozenset(pair_indexes),
            law_count=law_count,
        ),
        certificate_family="finmodel_paircheck_bank",
        summary_zh="paircheck bank：逐 pair 有限模型反例，覆盖稀疏 false pair。",
        summary_en=(
            "Paircheck bank: per-pair finite-model counterexamples for sparse "
            "false pairs."
        ),
        description_zh=(
            "每一行记录一个具体 source -> target pair 及其有限 magma table；"
            "该 table 满足 source 且反驳 target。此策略只覆盖显式 pair，不"
            "提升为 source × target setcheck。"
        ),
        description_en=(
            "Each row records one concrete source -> target pair and a finite "
            "magma table satisfying the source while refuting the target. This "
            "strategy covers explicit pairs only and is not promoted to a "
            "source x target setcheck."
        ),
        certificate_mode="finite_model_paircheck",
        verification_mode="python_verified_remote_smoke",
        coverage_rule_kind="explicit_pairs",
        certificate_generator="finmodel_false_judge",
        evidence={
            "pair_bank_path": str(bank_path),
            "pair_bank_row_count": len(rows),
            "pair_bank_sha256": hashlib.sha256(payload).hexdigest(),
            "remote_smoke_accepted_count": remote_smoke_accepted_count,
            "true_conflict_count": true_conflict_count,
        },
    )


@dataclass
class _FinmodelSourceTargetCache:
    path: Path
    equations_sha256: str
    law_count: int
    rows: dict[tuple[tuple[int, ...], ...], frozenset[int]]
    pending_rows: list[tuple[tuple[tuple[int, ...], ...], frozenset[int]]]

    @classmethod
    def load(
        cls,
        path: Path,
        *,
        equations_path: Path,
        law_count: int,
    ) -> "_FinmodelSourceTargetCache":
        equations_sha256 = _sha256_file(equations_path)
        rows: dict[tuple[tuple[int, ...], ...], frozenset[int]] = {}
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                payload = json.loads(line)
                if payload.get("schema_version") != 1:
                    continue
                if payload.get("equations_sha256") != equations_sha256:
                    continue
                if payload.get("law_count") != law_count:
                    continue
                table = _normalize_table(payload["table"])
                rows[table] = _decode_ids_bitset(
                    str(payload["source_bitset_base64"]),
                    law_count=law_count,
                )
        return cls(
            path=path,
            equations_sha256=equations_sha256,
            law_count=law_count,
            rows=rows,
            pending_rows=[],
        )

    def get(
        self,
        table: tuple[tuple[int, ...], ...],
        parsed_features: Sequence[tuple[object, Equation]],
        *,
        update: bool,
    ) -> tuple[frozenset[int], frozenset[int]] | None:
        source_ids = self.rows.get(table)
        if source_ids is not None:
            return source_ids, _target_ids_from_sources(
                source_ids,
                law_count=self.law_count,
            )
        if not update:
            return None
        source_ids, target_ids = _scan_finmodel_source_target_sets(table, parsed_features)
        self.rows[table] = source_ids
        self.pending_rows.append((table, source_ids))
        self.flush()
        return source_ids, target_ids

    def flush(self) -> None:
        if not self.pending_rows:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            for table, source_ids in self.pending_rows:
                payload = {
                    "schema_version": 1,
                    "equations_sha256": self.equations_sha256,
                    "law_count": self.law_count,
                    "table": [list(row) for row in table],
                    "source_bitset_base64": _encode_ids_bitset(
                        source_ids,
                        law_count=self.law_count,
                    ),
                }
                handle.write(json.dumps(payload, sort_keys=True) + "\n")
        self.pending_rows.clear()


_ACTIVE_FINMODEL_SOURCE_TARGET_CACHE: _FinmodelSourceTargetCache | None = None
_ACTIVE_FINMODEL_SOURCE_TARGET_CACHE_UPDATE = False


def build_default_order5_strategy_registry(
    *,
    equations_path: Path = DEFAULT_EQ_SIZE5_PATH,
    order4_max_id: int = DEFAULT_ORDER4_MAX_ID,
    include_true_strategies: bool = True,
    paircheck_bank_path: Path | None = DEFAULT_PAIRCHECK_BANK_PATH,
    setcheck_bank_path: Path | None = DEFAULT_SETCHECK_BANK_PATH,
    predicatecheck_bank_path: Path | None = DEFAULT_PREDICATECHECK_BANK_PATH,
    source_target_cache_path: Path | None = None,
    update_source_target_cache: bool = False,
) -> Order5StrategyRegistry:
    global _ACTIVE_FINMODEL_SOURCE_TARGET_CACHE
    global _ACTIVE_FINMODEL_SOURCE_TARGET_CACHE_UPDATE
    previous_cache = _ACTIVE_FINMODEL_SOURCE_TARGET_CACHE
    previous_update = _ACTIVE_FINMODEL_SOURCE_TARGET_CACHE_UPDATE
    if source_target_cache_path is not None:
        features = _cached_parsed_equation_features(equations_path)
        _ACTIVE_FINMODEL_SOURCE_TARGET_CACHE = _FinmodelSourceTargetCache.load(
            source_target_cache_path,
            equations_path=equations_path,
            law_count=len(features),
        )
        _ACTIVE_FINMODEL_SOURCE_TARGET_CACHE_UPDATE = update_source_target_cache
    try:
        registry = _build_default_order5_strategy_registry_uncached(
            equations_path=equations_path,
            order4_max_id=order4_max_id,
            include_true_strategies=include_true_strategies,
            paircheck_bank_path=paircheck_bank_path,
            setcheck_bank_path=setcheck_bank_path,
            predicatecheck_bank_path=predicatecheck_bank_path,
        )
        return registry.without_source_target_exclusions()
    finally:
        if _ACTIVE_FINMODEL_SOURCE_TARGET_CACHE is not None:
            _ACTIVE_FINMODEL_SOURCE_TARGET_CACHE.flush()
        _ACTIVE_FINMODEL_SOURCE_TARGET_CACHE = previous_cache
        _ACTIVE_FINMODEL_SOURCE_TARGET_CACHE_UPDATE = previous_update


def _build_default_order5_strategy_registry_uncached(
    *,
    equations_path: Path,
    order4_max_id: int,
    include_true_strategies: bool,
    paircheck_bank_path: Path | None,
    setcheck_bank_path: Path | None,
    predicatecheck_bank_path: Path | None,
) -> Order5StrategyRegistry:
    left_projection_features, left_projection_sources, left_projection_targets = (
        _finmodel_sets(equations_path, LEFT_PROJECTION_2_TABLE)
    )
    left_projection_order4_sources = frozenset(
        eq_id for eq_id in left_projection_sources if eq_id <= order4_max_id
    )
    left_projection_order4_targets = frozenset(
        eq_id for eq_id in left_projection_targets if eq_id <= order4_max_id
    )
    left_projection_strategy = CoverageStrategy(
        strategy_key=LEFT_PROJECTION_ALL_EQUATIONS_STRATEGY_KEY,
        strategy_version=1,
        verdict=False,
        priority=100,
        coverage_rule=SourceTargetSetsRule(
            source_ids=left_projection_sources,
            target_ids=left_projection_targets,
            excluded_blocks=(
                (left_projection_order4_sources, left_projection_order4_targets),
            ),
        ),
        certificate_family="spine_isolation_left_zero",
        summary_zh="Fin 2 左投影模型反例：全量方程 source 成立、target 不成立。",
        summary_en=(
            "Fin 2 left-projection countermodel over all equations: sources hold, targets fail."
        ),
        description_zh=(
            "使用 Fin 2 左投影运算 a ◇ b = a。全量扫描 order<=5 方程，"
            "source 为该模型满足的所有方程，target 为该模型反驳的所有方程。"
            "因此任意 source -> target 蕴含为 false。该策略包含旧的 "
            "left_spine_nonleft 子集策略。"
        ),
        description_en=(
            "Uses the Fin 2 left-projection operation a ◇ b = a. The model "
            "is checked against all order<=5 equations; sources are all "
            "equations satisfied by the model, and targets are all equations "
            "refuted by the model. Therefore every source -> target implication "
            "is false. This strategy supersedes the old left_spine_nonleft "
            "subset strategy."
        ),
        legacy_strategy_keys=(LEGACY_SPINE_LEFT_ZERO_STRATEGY_KEY,),
        supersedes_strategy_ids=(f"{LEGACY_SPINE_LEFT_ZERO_STRATEGY_KEY}.v1",),
        certificate_mode="finmodel",
        verification_mode="setcheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="fin_table_decide",
        evidence=_finmodel_setcheck_evidence(
            LEFT_PROJECTION_2_TABLE,
            left_projection_sources,
            left_projection_targets,
        ),
    )
    _, constant_sources, constant_targets = _finmodel_sets(
        equations_path,
        CONSTANT_2_TABLE,
    )
    constant_order4_sources = frozenset(
        eq_id for eq_id in constant_sources if eq_id <= order4_max_id
    )
    constant_order4_targets = frozenset(
        eq_id for eq_id in constant_targets if eq_id <= order4_max_id
    )
    constant_strategy = CoverageStrategy(
        strategy_key=CONSTANT_ALL_EQUATIONS_STRATEGY_KEY,
        strategy_version=1,
        verdict=False,
        priority=110,
        coverage_rule=SourceTargetSetsRule(
            source_ids=constant_sources,
            target_ids=constant_targets,
            excluded_blocks=((constant_order4_sources, constant_order4_targets),),
        ),
        certificate_family="finmodel_constant",
        summary_zh="Fin 2 常值模型反例：全量方程 source 成立、target 不成立。",
        summary_en=(
            "Fin 2 constant countermodel over all equations: sources hold, targets fail."
        ),
        description_zh=(
            "使用 Fin 2 常值运算 a ◇ b = 0。全量扫描 order<=5 方程，"
            "source 为该模型满足的所有方程，target 为该模型反驳的所有方程。"
            "因此任意 source -> target 蕴含为 false。该策略与左投影策略存在重叠，"
            "但提供新的 union 覆盖。"
        ),
        description_en=(
            "Uses the Fin 2 constant operation a ◇ b = 0. The model is "
            "checked against all order<=5 equations; sources are all equations "
            "satisfied by the model, and targets are all equations refuted by "
            "the model. Therefore every source -> target implication is false. "
            "This strategy overlaps with the left-projection strategy but adds "
            "new union coverage."
        ),
        certificate_mode="finmodel",
        verification_mode="setcheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="fin_table_decide",
        evidence=_finmodel_setcheck_evidence(
            CONSTANT_2_TABLE,
            constant_sources,
            constant_targets,
        ),
    )
    _, right_projection_sources, right_projection_targets = _finmodel_sets(
        equations_path,
        RIGHT_PROJECTION_2_TABLE,
    )
    right_projection_order4_sources = frozenset(
        eq_id for eq_id in right_projection_sources if eq_id <= order4_max_id
    )
    right_projection_order4_targets = frozenset(
        eq_id for eq_id in right_projection_targets if eq_id <= order4_max_id
    )
    right_projection_strategy = CoverageStrategy(
        strategy_key=RIGHT_PROJECTION_ALL_EQUATIONS_STRATEGY_KEY,
        strategy_version=1,
        verdict=False,
        priority=120,
        coverage_rule=SourceTargetSetsRule(
            source_ids=right_projection_sources,
            target_ids=right_projection_targets,
            excluded_blocks=(
                (right_projection_order4_sources, right_projection_order4_targets),
            ),
        ),
        certificate_family="finmodel_right_projection",
        summary_zh="Fin 2 右投影模型反例：全量方程 source 成立、target 不成立。",
        summary_en=(
            "Fin 2 right-projection countermodel over all equations: sources hold, targets fail."
        ),
        description_zh=(
            "使用 Fin 2 右投影运算 a ◇ b = b。全量扫描 order<=5 方程，"
            "source 为该模型满足的所有方程，target 为该模型反驳的所有方程。"
            "因此任意 source -> target 蕴含为 false。该策略与左投影、常值策略"
            "存在重叠，但提供新的 union 覆盖。"
        ),
        description_en=(
            "Uses the Fin 2 right-projection operation a ◇ b = b. The model "
            "is checked against all order<=5 equations; sources are all equations "
            "satisfied by the model, and targets are all equations refuted by "
            "the model. Therefore every source -> target implication is false. "
            "This strategy overlaps with the left-projection and constant "
            "strategies but adds new union coverage."
        ),
        certificate_mode="finmodel",
        verification_mode="setcheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="fin_table_decide",
        evidence=_finmodel_setcheck_evidence(
            RIGHT_PROJECTION_2_TABLE,
            right_projection_sources,
            right_projection_targets,
        ),
    )
    _, complement_left_sources, complement_left_targets = _finmodel_sets(
        equations_path,
        COMPLEMENT_LEFT_PROJECTION_2_TABLE,
    )
    complement_left_order4_sources = frozenset(
        eq_id for eq_id in complement_left_sources if eq_id <= order4_max_id
    )
    complement_left_order4_targets = frozenset(
        eq_id for eq_id in complement_left_targets if eq_id <= order4_max_id
    )
    complement_left_strategy = CoverageStrategy(
        strategy_key=COMPLEMENT_LEFT_PROJECTION_ALL_EQUATIONS_STRATEGY_KEY,
        strategy_version=1,
        verdict=False,
        priority=130,
        coverage_rule=SourceTargetSetsRule(
            source_ids=complement_left_sources,
            target_ids=complement_left_targets,
            excluded_blocks=(
                (complement_left_order4_sources, complement_left_order4_targets),
            ),
        ),
        certificate_family="finmodel_complement_left_projection",
        summary_zh="Fin 2 左补投影模型反例：全量方程 source 成立、target 不成立。",
        summary_en=(
            "Fin 2 complement-left-projection countermodel over all equations: "
            "sources hold, targets fail."
        ),
        description_zh=(
            "使用 Fin 2 左补投影运算 a ◇ b = 1 - a。全量扫描 order<=5 方程，"
            "source 为该模型满足的所有方程，target 为该模型反驳的所有方程。"
            "因此任意 source -> target 蕴含为 false。该策略与已有 Fin 2 "
            "setcheck 策略存在重叠，但提供新的 union 覆盖。"
        ),
        description_en=(
            "Uses the Fin 2 complement-left-projection operation a ◇ b = 1 - a. "
            "The model is checked against all order<=5 equations; sources are all "
            "equations satisfied by the model, and targets are all equations "
            "refuted by the model. Therefore every source -> target implication "
            "is false. This strategy overlaps with existing Fin 2 setcheck "
            "strategies but adds new union coverage."
        ),
        certificate_mode="finmodel",
        verification_mode="setcheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="fin_table_decide",
        evidence=_finmodel_setcheck_evidence(
            COMPLEMENT_LEFT_PROJECTION_2_TABLE,
            complement_left_sources,
            complement_left_targets,
        ),
    )
    _, complement_right_sources, complement_right_targets = _finmodel_sets(
        equations_path,
        COMPLEMENT_RIGHT_PROJECTION_2_TABLE,
    )
    complement_right_order4_sources = frozenset(
        eq_id for eq_id in complement_right_sources if eq_id <= order4_max_id
    )
    complement_right_order4_targets = frozenset(
        eq_id for eq_id in complement_right_targets if eq_id <= order4_max_id
    )
    complement_right_strategy = CoverageStrategy(
        strategy_key=COMPLEMENT_RIGHT_PROJECTION_ALL_EQUATIONS_STRATEGY_KEY,
        strategy_version=1,
        verdict=False,
        priority=140,
        coverage_rule=SourceTargetSetsRule(
            source_ids=complement_right_sources,
            target_ids=complement_right_targets,
            excluded_blocks=(
                (complement_right_order4_sources, complement_right_order4_targets),
            ),
        ),
        certificate_family="finmodel_complement_right_projection",
        summary_zh="Fin 2 右补投影模型反例：全量方程 source 成立、target 不成立。",
        summary_en=(
            "Fin 2 complement-right-projection countermodel over all equations: "
            "sources hold, targets fail."
        ),
        description_zh=(
            "使用 Fin 2 右补投影运算 a ◇ b = 1 - b。全量扫描 order<=5 方程，"
            "source 为该模型满足的所有方程，target 为该模型反驳的所有方程。"
            "因此任意 source -> target 蕴含为 false。该策略与已有 Fin 2 "
            "setcheck 策略存在重叠，但提供新的 union 覆盖。"
        ),
        description_en=(
            "Uses the Fin 2 complement-right-projection operation a ◇ b = 1 - b. "
            "The model is checked against all order<=5 equations; sources are all "
            "equations satisfied by the model, and targets are all equations "
            "refuted by the model. Therefore every source -> target implication "
            "is false. This strategy overlaps with existing Fin 2 setcheck "
            "strategies but adds new union coverage."
        ),
        certificate_mode="finmodel",
        verification_mode="setcheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="fin_table_decide",
        evidence=_finmodel_setcheck_evidence(
            COMPLEMENT_RIGHT_PROJECTION_2_TABLE,
            complement_right_sources,
            complement_right_targets,
        ),
    )
    _, left_and_complement_right_sources, left_and_complement_right_targets = (
        _finmodel_sets(
            equations_path,
            LEFT_AND_COMPLEMENT_RIGHT_2_TABLE,
        )
    )
    left_and_complement_right_order4_sources = frozenset(
        eq_id for eq_id in left_and_complement_right_sources if eq_id <= order4_max_id
    )
    left_and_complement_right_order4_targets = frozenset(
        eq_id for eq_id in left_and_complement_right_targets if eq_id <= order4_max_id
    )
    left_and_complement_right_strategy = CoverageStrategy(
        strategy_key=LEFT_AND_COMPLEMENT_RIGHT_ALL_EQUATIONS_STRATEGY_KEY,
        strategy_version=1,
        verdict=False,
        priority=150,
        coverage_rule=SourceTargetSetsRule(
            source_ids=left_and_complement_right_sources,
            target_ids=left_and_complement_right_targets,
            excluded_blocks=(
                (
                    left_and_complement_right_order4_sources,
                    left_and_complement_right_order4_targets,
                ),
            ),
        ),
        certificate_family="finmodel_left_and_complement_right",
        summary_zh="Fin 2 左且右补模型反例：全量方程 source 成立、target 不成立。",
        summary_en=(
            "Fin 2 left-and-complement-right countermodel over all equations: "
            "sources hold, targets fail."
        ),
        description_zh=(
            "使用 Fin 2 左且右补运算 a ◇ b = a ∧ (1 - b)。全量扫描 "
            "order<=5 方程，source 为该模型满足的所有方程，target 为该模型"
            "反驳的所有方程。因此任意 source -> target 蕴含为 false。该策略与"
            "已有 Fin 2 setcheck 策略存在重叠，但提供新的 union 覆盖。"
        ),
        description_en=(
            "Uses the Fin 2 left-and-complement-right operation "
            "a ◇ b = a ∧ (1 - b). The model is checked against all order<=5 "
            "equations; sources are all equations satisfied by the model, and "
            "targets are all equations refuted by the model. Therefore every "
            "source -> target implication is false. This strategy overlaps with "
            "existing Fin 2 setcheck strategies but adds new union coverage."
        ),
        certificate_mode="finmodel",
        verification_mode="setcheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="fin_table_decide",
        evidence=_finmodel_setcheck_evidence(
            LEFT_AND_COMPLEMENT_RIGHT_2_TABLE,
            left_and_complement_right_sources,
            left_and_complement_right_targets,
        ),
    )
    _, complement_left_and_right_sources, complement_left_and_right_targets = (
        _finmodel_sets(
            equations_path,
            COMPLEMENT_LEFT_AND_RIGHT_2_TABLE,
        )
    )
    complement_left_and_right_order4_sources = frozenset(
        eq_id for eq_id in complement_left_and_right_sources if eq_id <= order4_max_id
    )
    complement_left_and_right_order4_targets = frozenset(
        eq_id for eq_id in complement_left_and_right_targets if eq_id <= order4_max_id
    )
    complement_left_and_right_strategy = CoverageStrategy(
        strategy_key=COMPLEMENT_LEFT_AND_RIGHT_ALL_EQUATIONS_STRATEGY_KEY,
        strategy_version=1,
        verdict=False,
        priority=160,
        coverage_rule=SourceTargetSetsRule(
            source_ids=complement_left_and_right_sources,
            target_ids=complement_left_and_right_targets,
            excluded_blocks=(
                (
                    complement_left_and_right_order4_sources,
                    complement_left_and_right_order4_targets,
                ),
            ),
        ),
        certificate_family="finmodel_complement_left_and_right",
        summary_zh="Fin 2 左补且右模型反例：全量方程 source 成立、target 不成立。",
        summary_en=(
            "Fin 2 complement-left-and-right countermodel over all equations: "
            "sources hold, targets fail."
        ),
        description_zh=(
            "使用 Fin 2 左补且右运算 a ◇ b = (1 - a) ∧ b。全量扫描 "
            "order<=5 方程，source 为该模型满足的所有方程，target 为该模型"
            "反驳的所有方程。因此任意 source -> target 蕴含为 false。该策略与"
            "已有 Fin 2 setcheck 策略存在重叠，但提供新的 union 覆盖。"
        ),
        description_en=(
            "Uses the Fin 2 complement-left-and-right operation "
            "a ◇ b = (1 - a) ∧ b. The model is checked against all order<=5 "
            "equations; sources are all equations satisfied by the model, and "
            "targets are all equations refuted by the model. Therefore every "
            "source -> target implication is false. This strategy overlaps with "
            "existing Fin 2 setcheck strategies but adds new union coverage."
        ),
        certificate_mode="finmodel",
        verification_mode="setcheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="fin_table_decide",
        evidence=_finmodel_setcheck_evidence(
            COMPLEMENT_LEFT_AND_RIGHT_2_TABLE,
            complement_left_and_right_sources,
            complement_left_and_right_targets,
        ),
    )
    _, xor_sources, xor_targets = _finmodel_sets(
        equations_path,
        XOR_2_TABLE,
    )
    xor_order4_sources = frozenset(
        eq_id for eq_id in xor_sources if eq_id <= order4_max_id
    )
    xor_order4_targets = frozenset(
        eq_id for eq_id in xor_targets if eq_id <= order4_max_id
    )
    xor_strategy = CoverageStrategy(
        strategy_key=XOR_ALL_EQUATIONS_STRATEGY_KEY,
        strategy_version=1,
        verdict=False,
        priority=170,
        coverage_rule=SourceTargetSetsRule(
            source_ids=xor_sources,
            target_ids=xor_targets,
            excluded_blocks=((xor_order4_sources, xor_order4_targets),),
        ),
        certificate_family="finmodel_xor",
        summary_zh="Fin 2 异或模型反例：全量方程 source 成立、target 不成立。",
        summary_en=(
            "Fin 2 xor countermodel over all equations: sources hold, targets fail."
        ),
        description_zh=(
            "使用 Fin 2 异或运算 a ◇ b = a xor b。全量扫描 order<=5 方程，"
            "source 为该模型满足的所有方程，target 为该模型反驳的所有方程。"
            "因此任意 source -> target 蕴含为 false。该策略与已有 Fin 2 "
            "setcheck 策略存在重叠，但提供新的 union 覆盖。"
        ),
        description_en=(
            "Uses the Fin 2 xor operation a ◇ b = a xor b. The model is checked "
            "against all order<=5 equations; sources are all equations satisfied "
            "by the model, and targets are all equations refuted by the model. "
            "Therefore every source -> target implication is false. This strategy "
            "overlaps with existing Fin 2 setcheck strategies but adds new union "
            "coverage."
        ),
        certificate_mode="finmodel",
        verification_mode="setcheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="fin_table_decide",
        evidence=_finmodel_setcheck_evidence(
            XOR_2_TABLE,
            xor_sources,
            xor_targets,
        ),
    )
    _, and_sources, and_targets = _finmodel_sets(
        equations_path,
        AND_2_TABLE,
    )
    and_order4_sources = frozenset(
        eq_id for eq_id in and_sources if eq_id <= order4_max_id
    )
    and_order4_targets = frozenset(
        eq_id for eq_id in and_targets if eq_id <= order4_max_id
    )
    and_strategy = CoverageStrategy(
        strategy_key=AND_ALL_EQUATIONS_STRATEGY_KEY,
        strategy_version=1,
        verdict=False,
        priority=180,
        coverage_rule=SourceTargetSetsRule(
            source_ids=and_sources,
            target_ids=and_targets,
            excluded_blocks=((and_order4_sources, and_order4_targets),),
        ),
        certificate_family="finmodel_and",
        summary_zh="Fin 2 与模型反例：全量方程 source 成立、target 不成立。",
        summary_en=(
            "Fin 2 and countermodel over all equations: sources hold, targets fail."
        ),
        description_zh=(
            "使用 Fin 2 与运算 a ◇ b = a ∧ b。全量扫描 order<=5 方程，"
            "source 为该模型满足的所有方程，target 为该模型反驳的所有方程。"
            "因此任意 source -> target 蕴含为 false。该策略与已有 Fin 2 "
            "setcheck 策略存在重叠，但提供新的 union 覆盖。"
        ),
        description_en=(
            "Uses the Fin 2 and operation a ◇ b = a ∧ b. The model is checked "
            "against all order<=5 equations; sources are all equations satisfied "
            "by the model, and targets are all equations refuted by the model. "
            "Therefore every source -> target implication is false. This strategy "
            "overlaps with existing Fin 2 setcheck strategies but adds new union "
            "coverage."
        ),
        certificate_mode="finmodel",
        verification_mode="setcheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="fin_table_decide",
        evidence=_finmodel_setcheck_evidence(
            AND_2_TABLE,
            and_sources,
            and_targets,
        ),
    )
    _, nor_sources, nor_targets = _finmodel_sets(
        equations_path,
        NOR_2_TABLE,
    )
    nor_order4_sources = frozenset(
        eq_id for eq_id in nor_sources if eq_id <= order4_max_id
    )
    nor_order4_targets = frozenset(
        eq_id for eq_id in nor_targets if eq_id <= order4_max_id
    )
    nor_strategy = CoverageStrategy(
        strategy_key=NOR_ALL_EQUATIONS_STRATEGY_KEY,
        strategy_version=1,
        verdict=False,
        priority=190,
        coverage_rule=SourceTargetSetsRule(
            source_ids=nor_sources,
            target_ids=nor_targets,
            excluded_blocks=((nor_order4_sources, nor_order4_targets),),
        ),
        certificate_family="finmodel_nor",
        summary_zh="Fin 2 或非模型反例：全量方程 source 成立、target 不成立。",
        summary_en=(
            "Fin 2 nor countermodel over all equations: sources hold, targets fail."
        ),
        description_zh=(
            "使用 Fin 2 或非运算 a ◇ b = not (a ∨ b)。全量扫描 order<=5 方程，"
            "source 为该模型满足的所有方程，target 为该模型反驳的所有方程。"
            "因此任意 source -> target 蕴含为 false。该策略与已有 Fin 2 "
            "setcheck 策略存在重叠，但提供新的 union 覆盖。"
        ),
        description_en=(
            "Uses the Fin 2 nor operation a ◇ b = not (a ∨ b). The model is "
            "checked against all order<=5 equations; sources are all equations "
            "satisfied by the model, and targets are all equations refuted by "
            "the model. Therefore every source -> target implication is false. "
            "This strategy overlaps with existing Fin 2 setcheck strategies but "
            "adds new union coverage."
        ),
        certificate_mode="finmodel",
        verification_mode="setcheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="fin_table_decide",
        evidence=_finmodel_setcheck_evidence(
            NOR_2_TABLE,
            nor_sources,
            nor_targets,
        ),
    )
    _, steiner_sources, steiner_targets = _finmodel_sets(
        equations_path,
        STEINER_QUASIGROUP_3_TABLE,
    )
    steiner_order4_sources = frozenset(
        eq_id for eq_id in steiner_sources if eq_id <= order4_max_id
    )
    steiner_order4_targets = frozenset(
        eq_id for eq_id in steiner_targets if eq_id <= order4_max_id
    )
    steiner_strategy = CoverageStrategy(
        strategy_key=STEINER_QUASIGROUP_ALL_EQUATIONS_STRATEGY_KEY,
        strategy_version=1,
        verdict=False,
        priority=200,
        coverage_rule=SourceTargetSetsRule(
            source_ids=steiner_sources,
            target_ids=steiner_targets,
            excluded_blocks=((steiner_order4_sources, steiner_order4_targets),),
        ),
        certificate_family="finmodel_steiner_quasigroup",
        summary_zh="Fin 3 Steiner 拟群模型反例：全量方程 source 成立、target 不成立。",
        summary_en=(
            "Fin 3 Steiner quasigroup countermodel over all equations: sources hold, "
            "targets fail."
        ),
        description_zh=(
            "使用 Fin 3 Steiner 拟群运算 a ◇ b = -(a + b) mod 3，也就是 "
            "a = b 时返回 a，否则返回第三个元素。全量扫描 order<=5 方程，"
            "source 为该模型满足的所有方程，target 为该模型反驳的所有方程。"
            "因此任意 source -> target 蕴含为 false。该策略与已有 Fin 2 "
            "setcheck 策略存在重叠，但提供新的 union 覆盖。"
        ),
        description_en=(
            "Uses the Fin 3 Steiner quasigroup operation a ◇ b = -(a + b) mod 3, "
            "equivalently returning a when a = b and otherwise returning the third "
            "element. The model is checked against all order<=5 equations; sources "
            "are all equations satisfied by the model, and targets are all equations "
            "refuted by the model. Therefore every source -> target implication is "
            "false. This strategy overlaps with existing Fin 2 setcheck strategies "
            "but adds new union coverage."
        ),
        certificate_mode="finmodel",
        verification_mode="setcheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="fin_table_decide",
        evidence=_finmodel_setcheck_evidence(
            STEINER_QUASIGROUP_3_TABLE,
            steiner_sources,
            steiner_targets,
        ),
    )
    _, right_minus_left_sources, right_minus_left_targets = _finmodel_sets(
        equations_path,
        RIGHT_MINUS_LEFT_3_TABLE,
    )
    right_minus_left_order4_sources = frozenset(
        eq_id for eq_id in right_minus_left_sources if eq_id <= order4_max_id
    )
    right_minus_left_order4_targets = frozenset(
        eq_id for eq_id in right_minus_left_targets if eq_id <= order4_max_id
    )
    right_minus_left_strategy = CoverageStrategy(
        strategy_key=RIGHT_MINUS_LEFT_ALL_EQUATIONS_STRATEGY_KEY,
        strategy_version=1,
        verdict=False,
        priority=210,
        coverage_rule=SourceTargetSetsRule(
            source_ids=right_minus_left_sources,
            target_ids=right_minus_left_targets,
            excluded_blocks=(
                (right_minus_left_order4_sources, right_minus_left_order4_targets),
            ),
        ),
        certificate_family="finmodel_right_minus_left",
        summary_zh="Fin 3 右减左模型反例：全量方程 source 成立、target 不成立。",
        summary_en=(
            "Fin 3 right-minus-left countermodel over all equations: sources hold, "
            "targets fail."
        ),
        description_zh=(
            "使用 Fin 3 右减左运算 a ◇ b = b - a mod 3。全量扫描 order<=5 "
            "方程，source 为该模型满足的所有方程，target 为该模型反驳的所有"
            "方程。因此任意 source -> target 蕴含为 false。该策略与已有 Fin 2 "
            "和 Fin 3 setcheck 策略存在重叠，但提供新的 union 覆盖。"
        ),
        description_en=(
            "Uses the Fin 3 right-minus-left operation a ◇ b = b - a mod 3. "
            "The model is checked against all order<=5 equations; sources are all "
            "equations satisfied by the model, and targets are all equations "
            "refuted by the model. Therefore every source -> target implication is "
            "false. This strategy overlaps with existing Fin 2 and Fin 3 setcheck "
            "strategies but adds new union coverage."
        ),
        certificate_mode="finmodel",
        verification_mode="setcheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="fin_table_decide",
        evidence=_finmodel_setcheck_evidence(
            RIGHT_MINUS_LEFT_3_TABLE,
            right_minus_left_sources,
            right_minus_left_targets,
        ),
    )
    _, left_minus_right_sources, left_minus_right_targets = _finmodel_sets(
        equations_path,
        LEFT_MINUS_RIGHT_3_TABLE,
    )
    left_minus_right_order4_sources = frozenset(
        eq_id for eq_id in left_minus_right_sources if eq_id <= order4_max_id
    )
    left_minus_right_order4_targets = frozenset(
        eq_id for eq_id in left_minus_right_targets if eq_id <= order4_max_id
    )
    left_minus_right_strategy = CoverageStrategy(
        strategy_key=LEFT_MINUS_RIGHT_ALL_EQUATIONS_STRATEGY_KEY,
        strategy_version=1,
        verdict=False,
        priority=220,
        coverage_rule=SourceTargetSetsRule(
            source_ids=left_minus_right_sources,
            target_ids=left_minus_right_targets,
            excluded_blocks=(
                (left_minus_right_order4_sources, left_minus_right_order4_targets),
            ),
        ),
        certificate_family="finmodel_left_minus_right",
        summary_zh="Fin 3 左减右模型反例：全量方程 source 成立、target 不成立。",
        summary_en=(
            "Fin 3 left-minus-right countermodel over all equations: sources hold, "
            "targets fail."
        ),
        description_zh=(
            "使用 Fin 3 左减右运算 a ◇ b = a - b mod 3。全量扫描 order<=5 "
            "方程，source 为该模型满足的所有方程，target 为该模型反驳的所有"
            "方程。因此任意 source -> target 蕴含为 false。该策略与已有 Fin 2 "
            "和 Fin 3 setcheck 策略存在重叠，但提供新的 union 覆盖。"
        ),
        description_en=(
            "Uses the Fin 3 left-minus-right operation a ◇ b = a - b mod 3. "
            "The model is checked against all order<=5 equations; sources are all "
            "equations satisfied by the model, and targets are all equations "
            "refuted by the model. Therefore every source -> target implication is "
            "false. This strategy overlaps with existing Fin 2 and Fin 3 setcheck "
            "strategies but adds new union coverage."
        ),
        certificate_mode="finmodel",
        verification_mode="setcheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="fin_table_decide",
        evidence=_finmodel_setcheck_evidence(
            LEFT_MINUS_RIGHT_3_TABLE,
            left_minus_right_sources,
            left_minus_right_targets,
        ),
    )
    _, fin3_table_020_110_122_sources, fin3_table_020_110_122_targets = (
        _finmodel_sets(
            equations_path,
            FIN3_TABLE_020_110_122_TABLE,
        )
    )
    fin3_table_020_110_122_order4_sources = frozenset(
        eq_id for eq_id in fin3_table_020_110_122_sources if eq_id <= order4_max_id
    )
    fin3_table_020_110_122_order4_targets = frozenset(
        eq_id for eq_id in fin3_table_020_110_122_targets if eq_id <= order4_max_id
    )
    fin3_table_020_110_122_strategy = CoverageStrategy(
        strategy_key=FIN3_TABLE_020_110_122_ALL_EQUATIONS_STRATEGY_KEY,
        strategy_version=1,
        verdict=False,
        priority=230,
        coverage_rule=SourceTargetSetsRule(
            source_ids=fin3_table_020_110_122_sources,
            target_ids=fin3_table_020_110_122_targets,
            excluded_blocks=(
                (
                    fin3_table_020_110_122_order4_sources,
                    fin3_table_020_110_122_order4_targets,
                ),
            ),
        ),
        certificate_family="finmodel_fin3_table_020_110_122",
        summary_zh="Fin 3 显式表 020/110/122 模型反例：全量方程 source 成立、target 不成立。",
        summary_en=(
            "Fin 3 explicit table 020/110/122 countermodel over all equations: "
            "sources hold, targets fail."
        ),
        description_zh=(
            "使用 Fin 3 显式运算表 [[0,2,0],[1,1,0],[1,2,2]]。全量扫描 "
            "order<=5 方程，source 为该模型满足的所有方程，target 为该模型"
            "反驳的所有方程。因此任意 source -> target 蕴含为 false。该策略与"
            "已有 Fin 2 和 Fin 3 setcheck 策略存在重叠，但提供新的 union 覆盖。"
        ),
        description_en=(
            "Uses the Fin 3 explicit operation table "
            "[[0,2,0],[1,1,0],[1,2,2]]. The model is checked against all "
            "order<=5 equations; sources are all equations satisfied by the "
            "model, and targets are all equations refuted by the model. "
            "Therefore every source -> target implication is false. This "
            "strategy overlaps with existing Fin 2 and Fin 3 setcheck "
            "strategies but adds new union coverage."
        ),
        certificate_mode="finmodel",
        verification_mode="setcheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="fin_table_decide",
        evidence=_finmodel_setcheck_evidence(
            FIN3_TABLE_020_110_122_TABLE,
            fin3_table_020_110_122_sources,
            fin3_table_020_110_122_targets,
        ),
    )
    _, left_cyclic_successor_sources, left_cyclic_successor_targets = _finmodel_sets(
        equations_path,
        LEFT_CYCLIC_SUCCESSOR_3_TABLE,
    )
    left_cyclic_successor_order4_sources = frozenset(
        eq_id for eq_id in left_cyclic_successor_sources if eq_id <= order4_max_id
    )
    left_cyclic_successor_order4_targets = frozenset(
        eq_id for eq_id in left_cyclic_successor_targets if eq_id <= order4_max_id
    )
    left_cyclic_successor_strategy = CoverageStrategy(
        strategy_key=LEFT_CYCLIC_SUCCESSOR_3_ALL_EQUATIONS_STRATEGY_KEY,
        strategy_version=1,
        verdict=False,
        priority=240,
        coverage_rule=SourceTargetSetsRule(
            source_ids=left_cyclic_successor_sources,
            target_ids=left_cyclic_successor_targets,
            excluded_blocks=(
                (
                    left_cyclic_successor_order4_sources,
                    left_cyclic_successor_order4_targets,
                ),
            ),
        ),
        certificate_family="finmodel_left_cyclic_successor_n3",
        summary_zh="Fin 3 左循环后继模型反例：全量方程 source 成立、target 不成立。",
        summary_en=(
            "Fin 3 left cyclic successor countermodel over all equations: "
            "sources hold, targets fail."
        ),
        description_zh=(
            "使用 Fin 3 左循环后继运算 a ◇ b = a + 1 mod 3。全量扫描 "
            "order<=5 方程，source 为该模型满足的所有方程，target 为该模型"
            "反驳的所有方程。因此任意 source -> target 蕴含为 false。该策略与"
            "已有 Fin 2 和 Fin 3 setcheck 策略存在重叠，但提供新的 union 覆盖。"
        ),
        description_en=(
            "Uses the Fin 3 left cyclic successor operation "
            "a ◇ b = a + 1 mod 3. The model is checked against all order<=5 "
            "equations; sources are all equations satisfied by the model, and "
            "targets are all equations refuted by the model. Therefore every "
            "source -> target implication is false. This strategy overlaps with "
            "existing Fin 2 and Fin 3 setcheck strategies but adds new union "
            "coverage."
        ),
        certificate_mode="finmodel",
        verification_mode="setcheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="fin_table_decide",
        evidence=_finmodel_setcheck_evidence(
            LEFT_CYCLIC_SUCCESSOR_3_TABLE,
            left_cyclic_successor_sources,
            left_cyclic_successor_targets,
        ),
    )
    _, right_cyclic_successor_sources, right_cyclic_successor_targets = _finmodel_sets(
        equations_path,
        RIGHT_CYCLIC_SUCCESSOR_3_TABLE,
    )
    right_cyclic_successor_order4_sources = frozenset(
        eq_id for eq_id in right_cyclic_successor_sources if eq_id <= order4_max_id
    )
    right_cyclic_successor_order4_targets = frozenset(
        eq_id for eq_id in right_cyclic_successor_targets if eq_id <= order4_max_id
    )
    right_cyclic_successor_strategy = CoverageStrategy(
        strategy_key=RIGHT_CYCLIC_SUCCESSOR_3_ALL_EQUATIONS_STRATEGY_KEY,
        strategy_version=1,
        verdict=False,
        priority=250,
        coverage_rule=SourceTargetSetsRule(
            source_ids=right_cyclic_successor_sources,
            target_ids=right_cyclic_successor_targets,
            excluded_blocks=(
                (
                    right_cyclic_successor_order4_sources,
                    right_cyclic_successor_order4_targets,
                ),
            ),
        ),
        certificate_family="finmodel_right_cyclic_successor_n3",
        summary_zh="Fin 3 右循环后继模型反例：全量方程 source 成立、target 不成立。",
        summary_en=(
            "Fin 3 right cyclic successor countermodel over all equations: "
            "sources hold, targets fail."
        ),
        description_zh=(
            "使用 Fin 3 右循环后继运算 a ◇ b = b + 1 mod 3。全量扫描 "
            "order<=5 方程，source 为该模型满足的所有方程，target 为该模型"
            "反驳的所有方程。因此任意 source -> target 蕴含为 false。该策略与"
            "已有 Fin 2 和 Fin 3 setcheck 策略存在重叠，但提供新的 union 覆盖。"
        ),
        description_en=(
            "Uses the Fin 3 right cyclic successor operation "
            "a ◇ b = b + 1 mod 3. The model is checked against all order<=5 "
            "equations; sources are all equations satisfied by the model, and "
            "targets are all equations refuted by the model. Therefore every "
            "source -> target implication is false. This strategy overlaps with "
            "existing Fin 2 and Fin 3 setcheck strategies but adds new union "
            "coverage."
        ),
        certificate_mode="finmodel",
        verification_mode="setcheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="fin_table_decide",
        evidence=_finmodel_setcheck_evidence(
            RIGHT_CYCLIC_SUCCESSOR_3_TABLE,
            right_cyclic_successor_sources,
            right_cyclic_successor_targets,
        ),
    )
    _, fin3_table_022_010_112_sources, fin3_table_022_010_112_targets = (
        _finmodel_sets(
            equations_path,
            FIN3_TABLE_022_010_112_TABLE,
        )
    )
    fin3_table_022_010_112_order4_sources = frozenset(
        eq_id for eq_id in fin3_table_022_010_112_sources if eq_id <= order4_max_id
    )
    fin3_table_022_010_112_order4_targets = frozenset(
        eq_id for eq_id in fin3_table_022_010_112_targets if eq_id <= order4_max_id
    )
    fin3_table_022_010_112_strategy = CoverageStrategy(
        strategy_key=FIN3_TABLE_022_010_112_ALL_EQUATIONS_STRATEGY_KEY,
        strategy_version=1,
        verdict=False,
        priority=260,
        coverage_rule=SourceTargetSetsRule(
            source_ids=fin3_table_022_010_112_sources,
            target_ids=fin3_table_022_010_112_targets,
            excluded_blocks=(
                (
                    fin3_table_022_010_112_order4_sources,
                    fin3_table_022_010_112_order4_targets,
                ),
            ),
        ),
        certificate_family="finmodel_fin3_table_022_010_112",
        summary_zh="Fin 3 显式表 022/010/112 模型反例：全量方程 source 成立、target 不成立。",
        summary_en=(
            "Fin 3 explicit table 022/010/112 countermodel over all equations: "
            "sources hold, targets fail."
        ),
        description_zh=(
            "使用 Fin 3 显式运算表 [[0,2,2],[0,1,0],[1,1,2]]。全量扫描 "
            "order<=5 方程，source 为该模型满足的所有方程，target 为该模型"
            "反驳的所有方程。因此任意 source -> target 蕴含为 false。该策略与"
            "已有 Fin 2 和 Fin 3 setcheck 策略存在重叠，但提供新的 union 覆盖。"
        ),
        description_en=(
            "Uses the Fin 3 explicit operation table "
            "[[0,2,2],[0,1,0],[1,1,2]]. The model is checked against all "
            "order<=5 equations; sources are all equations satisfied by the "
            "model, and targets are all equations refuted by the model. "
            "Therefore every source -> target implication is false. This "
            "strategy overlaps with existing Fin 2 and Fin 3 setcheck "
            "strategies but adds new union coverage."
        ),
        certificate_mode="finmodel",
        verification_mode="setcheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="fin_table_decide",
        evidence=_finmodel_setcheck_evidence(
            FIN3_TABLE_022_010_112_TABLE,
            fin3_table_022_010_112_sources,
            fin3_table_022_010_112_targets,
        ),
    )
    _, addition_mod3_sources, addition_mod3_targets = _finmodel_sets(
        equations_path,
        ADDITION_MOD3_3_TABLE,
    )
    addition_mod3_order4_sources = frozenset(
        eq_id for eq_id in addition_mod3_sources if eq_id <= order4_max_id
    )
    addition_mod3_order4_targets = frozenset(
        eq_id for eq_id in addition_mod3_targets if eq_id <= order4_max_id
    )
    addition_mod3_strategy = CoverageStrategy(
        strategy_key=ADDITION_MOD3_3_ALL_EQUATIONS_STRATEGY_KEY,
        strategy_version=1,
        verdict=False,
        priority=270,
        coverage_rule=SourceTargetSetsRule(
            source_ids=addition_mod3_sources,
            target_ids=addition_mod3_targets,
            excluded_blocks=(
                (
                    addition_mod3_order4_sources,
                    addition_mod3_order4_targets,
                ),
            ),
        ),
        certificate_family="finmodel_addition_mod3_n3",
        summary_zh="Fin 3 加法 mod 3 模型反例：全量方程 source 成立、target 不成立。",
        summary_en=(
            "Fin 3 addition mod 3 countermodel over all equations: sources hold, "
            "targets fail."
        ),
        description_zh=(
            "使用 Fin 3 加法 mod 3 运算 a ◇ b = a + b mod 3。全量扫描 "
            "order<=5 方程，source 为该模型满足的所有方程，target 为该模型"
            "反驳的所有方程。因此任意 source -> target 蕴含为 false。该策略与"
            "已有 Fin 2 和 Fin 3 setcheck 策略存在重叠，但提供新的 union 覆盖。"
        ),
        description_en=(
            "Uses the Fin 3 addition mod 3 operation a ◇ b = a + b mod 3. "
            "The model is checked against all order<=5 equations; sources are all "
            "equations satisfied by the model, and targets are all equations "
            "refuted by the model. Therefore every source -> target implication is "
            "false. This strategy overlaps with existing Fin 2 and Fin 3 setcheck "
            "strategies but adds new union coverage."
        ),
        certificate_mode="finmodel",
        verification_mode="setcheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="fin_table_decide",
        evidence=_finmodel_setcheck_evidence(
            ADDITION_MOD3_3_TABLE,
            addition_mod3_sources,
            addition_mod3_targets,
        ),
    )
    _, fin4_table_0231_3102_1320_2013_sources, fin4_table_0231_3102_1320_2013_targets = (
        _finmodel_sets(
            equations_path,
            FIN4_TABLE_0231_3102_1320_2013_TABLE,
        )
    )
    fin4_table_0231_3102_1320_2013_order4_sources = frozenset(
        eq_id
        for eq_id in fin4_table_0231_3102_1320_2013_sources
        if eq_id <= order4_max_id
    )
    fin4_table_0231_3102_1320_2013_order4_targets = frozenset(
        eq_id
        for eq_id in fin4_table_0231_3102_1320_2013_targets
        if eq_id <= order4_max_id
    )
    fin4_table_0231_3102_1320_2013_strategy = CoverageStrategy(
        strategy_key=FIN4_TABLE_0231_3102_1320_2013_ALL_EQUATIONS_STRATEGY_KEY,
        strategy_version=1,
        verdict=False,
        priority=280,
        coverage_rule=SourceTargetSetsRule(
            source_ids=fin4_table_0231_3102_1320_2013_sources,
            target_ids=fin4_table_0231_3102_1320_2013_targets,
            excluded_blocks=(
                (
                    fin4_table_0231_3102_1320_2013_order4_sources,
                    fin4_table_0231_3102_1320_2013_order4_targets,
                ),
            ),
        ),
        certificate_family="finmodel_fin4_table_0231_3102_1320_2013",
        summary_zh=(
            "Fin 4 显式表 0231/3102/1320/2013 模型反例：全量方程 source 成立、"
            "target 不成立。"
        ),
        summary_en=(
            "Fin 4 explicit table 0231/3102/1320/2013 countermodel over all "
            "equations: sources hold, targets fail."
        ),
        description_zh=(
            "使用 Generated/All4x4Tables/Refutation317 发现的 Fin 4 显式运算表 "
            "[[0,2,3,1],[3,1,0,2],[1,3,2,0],[2,0,1,3]]。全量扫描 "
            "order<=5 方程，source 为该模型满足的所有方程，target 为该模型"
            "反驳的所有方程。因此任意 source -> target 蕴含为 false。该策略与"
            "已有 finite-model setcheck 策略存在重叠，但提供新的 union 覆盖。"
        ),
        description_en=(
            "Uses the Fin 4 explicit operation table found from "
            "Generated/All4x4Tables/Refutation317: "
            "[[0,2,3,1],[3,1,0,2],[1,3,2,0],[2,0,1,3]]. The model is checked "
            "against all order<=5 equations; sources are all equations satisfied "
            "by the model, and targets are all equations refuted by the model. "
            "Therefore every source -> target implication is false. This strategy "
            "overlaps with existing finite-model setcheck strategies but adds new "
            "union coverage."
        ),
        certificate_mode="finmodel",
        verification_mode="setcheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="fin_table_decide",
        evidence=_finmodel_setcheck_evidence(
            FIN4_TABLE_0231_3102_1320_2013_TABLE,
            fin4_table_0231_3102_1320_2013_sources,
            fin4_table_0231_3102_1320_2013_targets,
        ),
    )
    _, fin3_table_000_211_122_sources, fin3_table_000_211_122_targets = (
        _finmodel_sets(
            equations_path,
            FIN3_TABLE_000_211_122_TABLE,
        )
    )
    fin3_table_000_211_122_order4_sources = frozenset(
        eq_id for eq_id in fin3_table_000_211_122_sources if eq_id <= order4_max_id
    )
    fin3_table_000_211_122_order4_targets = frozenset(
        eq_id for eq_id in fin3_table_000_211_122_targets if eq_id <= order4_max_id
    )
    fin3_table_000_211_122_strategy = CoverageStrategy(
        strategy_key=FIN3_TABLE_000_211_122_ALL_EQUATIONS_STRATEGY_KEY,
        strategy_version=1,
        verdict=False,
        priority=290,
        coverage_rule=SourceTargetSetsRule(
            source_ids=fin3_table_000_211_122_sources,
            target_ids=fin3_table_000_211_122_targets,
            excluded_blocks=(
                (
                    fin3_table_000_211_122_order4_sources,
                    fin3_table_000_211_122_order4_targets,
                ),
            ),
        ),
        certificate_family="finmodel_fin3_table_000_211_122",
        summary_zh=(
            "Fin 3 显式表 000/211/122 模型反例：全量方程 source 成立、target 不成立。"
        ),
        summary_en=(
            "Fin 3 explicit table 000/211/122 countermodel over all equations: "
            "sources hold, targets fail."
        ),
        description_zh=(
            "使用 Generated/All4x4Tables/Refutation272 发现的 Fin 3 显式运算表 "
            "[[0,0,0],[2,1,1],[1,2,2]]。全量扫描 order<=5 方程，source 为"
            "该模型满足的所有方程，target 为该模型反驳的所有方程。因此任意 "
            "source -> target 蕴含为 false。该策略与已有 finite-model "
            "setcheck 策略存在重叠，但提供新的 union 覆盖。"
        ),
        description_en=(
            "Uses the Fin 3 explicit operation table found from "
            "Generated/All4x4Tables/Refutation272: [[0,0,0],[2,1,1],[1,2,2]]. "
            "The model is checked against all order<=5 equations; sources are "
            "all equations satisfied by the model, and targets are all equations "
            "refuted by the model. Therefore every source -> target implication "
            "is false. This strategy overlaps with existing finite-model "
            "setcheck strategies but adds new union coverage."
        ),
        certificate_mode="finmodel",
        verification_mode="setcheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="fin_table_decide",
        evidence=_finmodel_setcheck_evidence(
            FIN3_TABLE_000_211_122_TABLE,
            fin3_table_000_211_122_sources,
            fin3_table_000_211_122_targets,
        ),
    )
    _, fin3_table_012_012_102_sources, fin3_table_012_012_102_targets = (
        _finmodel_sets(
            equations_path,
            FIN3_TABLE_012_012_102_TABLE,
        )
    )
    fin3_table_012_012_102_order4_sources = frozenset(
        eq_id for eq_id in fin3_table_012_012_102_sources if eq_id <= order4_max_id
    )
    fin3_table_012_012_102_order4_targets = frozenset(
        eq_id for eq_id in fin3_table_012_012_102_targets if eq_id <= order4_max_id
    )
    fin3_table_012_012_102_strategy = CoverageStrategy(
        strategy_key=FIN3_TABLE_012_012_102_ALL_EQUATIONS_STRATEGY_KEY,
        strategy_version=1,
        verdict=False,
        priority=291,
        coverage_rule=SourceTargetSetsRule(
            source_ids=fin3_table_012_012_102_sources,
            target_ids=fin3_table_012_012_102_targets,
            excluded_blocks=(
                (
                    fin3_table_012_012_102_order4_sources,
                    fin3_table_012_012_102_order4_targets,
                ),
            ),
        ),
        certificate_family="finmodel_fin3_table_012_012_102",
        summary_zh=(
            "Fin 3 显式表 012/012/102 模型反例：全量方程 source 成立、target 不成立。"
        ),
        summary_en=(
            "Fin 3 explicit table 012/012/102 countermodel over all equations: "
            "sources hold, targets fail."
        ),
        description_zh=(
            "使用 Generated/All4x4Tables/Refutation287 发现的 Fin 3 显式运算表 "
            "[[0,1,2],[0,1,2],[1,0,2]]。全量扫描 order<=5 方程，source 为"
            "该模型满足的所有方程，target 为该模型反驳的所有方程。因此任意 "
            "source -> target 蕴含为 false。该策略与已有 finite-model "
            "setcheck 策略存在重叠，但提供新的 union 覆盖。"
        ),
        description_en=(
            "Uses the Fin 3 explicit operation table found from "
            "Generated/All4x4Tables/Refutation287: [[0,1,2],[0,1,2],[1,0,2]]. "
            "The model is checked against all order<=5 equations; sources are "
            "all equations satisfied by the model, and targets are all equations "
            "refuted by the model. Therefore every source -> target implication "
            "is false. This strategy overlaps with existing finite-model "
            "setcheck strategies but adds new union coverage."
        ),
        certificate_mode="finmodel",
        verification_mode="setcheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="fin_table_decide",
        evidence=_finmodel_setcheck_evidence(
            FIN3_TABLE_012_012_102_TABLE,
            fin3_table_012_012_102_sources,
            fin3_table_012_012_102_targets,
        ),
    )
    _, fin4_table_2013_3102_0231_1320_sources, fin4_table_2013_3102_0231_1320_targets = (
        _finmodel_sets(
            equations_path,
            FIN4_TABLE_2013_3102_0231_1320_TABLE,
        )
    )
    fin4_table_2013_3102_0231_1320_order4_sources = frozenset(
        eq_id
        for eq_id in fin4_table_2013_3102_0231_1320_sources
        if eq_id <= order4_max_id
    )
    fin4_table_2013_3102_0231_1320_order4_targets = frozenset(
        eq_id
        for eq_id in fin4_table_2013_3102_0231_1320_targets
        if eq_id <= order4_max_id
    )
    fin4_table_2013_3102_0231_1320_strategy = CoverageStrategy(
        strategy_key=FIN4_TABLE_2013_3102_0231_1320_ALL_EQUATIONS_STRATEGY_KEY,
        strategy_version=1,
        verdict=False,
        priority=292,
        coverage_rule=SourceTargetSetsRule(
            source_ids=fin4_table_2013_3102_0231_1320_sources,
            target_ids=fin4_table_2013_3102_0231_1320_targets,
            excluded_blocks=(
                (
                    fin4_table_2013_3102_0231_1320_order4_sources,
                    fin4_table_2013_3102_0231_1320_order4_targets,
                ),
            ),
        ),
        certificate_family="finmodel_fin4_table_2013_3102_0231_1320",
        summary_zh=(
            "Fin 4 显式表 2013/3102/0231/1320 模型反例：全量方程 source 成立、"
            "target 不成立。"
        ),
        summary_en=(
            "Fin 4 explicit table 2013/3102/0231/1320 countermodel over all "
            "equations: sources hold, targets fail."
        ),
        description_zh=(
            "使用 Generated/All4x4Tables/Refutation351 发现的 Fin 4 显式运算表 "
            "[[2,0,1,3],[3,1,0,2],[0,2,3,1],[1,3,2,0]]。全量扫描 "
            "order<=5 方程，source 为该模型满足的所有方程，target 为该模型"
            "反驳的所有方程。因此任意 source -> target 蕴含为 false。该策略与"
            "已有 finite-model setcheck 策略存在重叠，但提供新的 union 覆盖。"
        ),
        description_en=(
            "Uses the Fin 4 explicit operation table found from "
            "Generated/All4x4Tables/Refutation351: "
            "[[2,0,1,3],[3,1,0,2],[0,2,3,1],[1,3,2,0]]. The model is checked "
            "against all order<=5 equations; sources are all equations satisfied "
            "by the model, and targets are all equations refuted by the model. "
            "Therefore every source -> target implication is false. This strategy "
            "overlaps with existing finite-model setcheck strategies but adds new "
            "union coverage."
        ),
        certificate_mode="finmodel",
        verification_mode="setcheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="fin_table_decide",
        evidence=_finmodel_setcheck_evidence(
            FIN4_TABLE_2013_3102_0231_1320_TABLE,
            fin4_table_2013_3102_0231_1320_sources,
            fin4_table_2013_3102_0231_1320_targets,
        ),
    )
    _, fin3_table_011_012_012_sources, fin3_table_011_012_012_targets = (
        _finmodel_sets(
            equations_path,
            FIN3_TABLE_011_012_012_TABLE,
        )
    )
    fin3_table_011_012_012_order4_sources = frozenset(
        eq_id for eq_id in fin3_table_011_012_012_sources if eq_id <= order4_max_id
    )
    fin3_table_011_012_012_order4_targets = frozenset(
        eq_id for eq_id in fin3_table_011_012_012_targets if eq_id <= order4_max_id
    )
    fin3_table_011_012_012_strategy = CoverageStrategy(
        strategy_key=FIN3_TABLE_011_012_012_ALL_EQUATIONS_STRATEGY_KEY,
        strategy_version=1,
        verdict=False,
        priority=293,
        coverage_rule=SourceTargetSetsRule(
            source_ids=fin3_table_011_012_012_sources,
            target_ids=fin3_table_011_012_012_targets,
            excluded_blocks=(
                (
                    fin3_table_011_012_012_order4_sources,
                    fin3_table_011_012_012_order4_targets,
                ),
            ),
        ),
        certificate_family="finmodel_fin3_table_011_012_012",
        summary_zh=(
            "Fin 3 显式表 011/012/012 模型反例：全量方程 source 成立、target 不成立。"
        ),
        summary_en=(
            "Fin 3 explicit table 011/012/012 countermodel over all equations: "
            "sources hold, targets fail."
        ),
        description_zh=(
            "使用 Generated/All4x4Tables/Refutation135 发现的 Fin 3 显式运算表 "
            "[[0,1,1],[0,1,2],[0,1,2]]。全量扫描 order<=5 方程，source 为"
            "该模型满足的所有方程，target 为该模型反驳的所有方程。因此任意 "
            "source -> target 蕴含为 false。该策略与已有 finite-model "
            "setcheck 策略存在重叠，但提供新的 union 覆盖。"
        ),
        description_en=(
            "Uses the Fin 3 explicit operation table found from "
            "Generated/All4x4Tables/Refutation135: [[0,1,1],[0,1,2],[0,1,2]]. "
            "The model is checked against all order<=5 equations; sources are "
            "all equations satisfied by the model, and targets are all equations "
            "refuted by the model. Therefore every source -> target implication "
            "is false. This strategy overlaps with existing finite-model "
            "setcheck strategies but adds new union coverage."
        ),
        certificate_mode="finmodel",
        verification_mode="setcheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="fin_table_decide",
        evidence=_finmodel_setcheck_evidence(
            FIN3_TABLE_011_012_012_TABLE,
            fin3_table_011_012_012_sources,
            fin3_table_011_012_012_targets,
        ),
    )
    _, fin3_table_000_110_222_sources, fin3_table_000_110_222_targets = (
        _finmodel_sets(
            equations_path,
            FIN3_TABLE_000_110_222_TABLE,
        )
    )
    fin3_table_000_110_222_order4_sources = frozenset(
        eq_id for eq_id in fin3_table_000_110_222_sources if eq_id <= order4_max_id
    )
    fin3_table_000_110_222_order4_targets = frozenset(
        eq_id for eq_id in fin3_table_000_110_222_targets if eq_id <= order4_max_id
    )
    fin3_table_000_110_222_strategy = CoverageStrategy(
        strategy_key=FIN3_TABLE_000_110_222_ALL_EQUATIONS_STRATEGY_KEY,
        strategy_version=1,
        verdict=False,
        priority=294,
        coverage_rule=SourceTargetSetsRule(
            source_ids=fin3_table_000_110_222_sources,
            target_ids=fin3_table_000_110_222_targets,
            excluded_blocks=(
                (
                    fin3_table_000_110_222_order4_sources,
                    fin3_table_000_110_222_order4_targets,
                ),
            ),
        ),
        certificate_family="finmodel_fin3_table_000_110_222",
        summary_zh=(
            "Fin 3 显式表 000/110/222 模型反例：全量方程 source 成立、target 不成立。"
        ),
        summary_en=(
            "Fin 3 explicit table 000/110/222 countermodel over all equations: "
            "sources hold, targets fail."
        ),
        description_zh=(
            "使用 Generated/All4x4Tables/Refutation84 发现的 Fin 3 显式运算表 "
            "[[0,0,0],[1,1,0],[2,2,2]]。全量扫描 order<=5 方程，source 为"
            "该模型满足的所有方程，target 为该模型反驳的所有方程。因此任意 "
            "source -> target 蕴含为 false。该策略与已有 finite-model "
            "setcheck 策略存在重叠，但提供新的 union 覆盖。"
        ),
        description_en=(
            "Uses the Fin 3 explicit operation table found from "
            "Generated/All4x4Tables/Refutation84: [[0,0,0],[1,1,0],[2,2,2]]. "
            "The model is checked against all order<=5 equations; sources are "
            "all equations satisfied by the model, and targets are all equations "
            "refuted by the model. Therefore every source -> target implication "
            "is false. This strategy overlaps with existing finite-model "
            "setcheck strategies but adds new union coverage."
        ),
        certificate_mode="finmodel",
        verification_mode="setcheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="fin_table_decide",
        evidence=_finmodel_setcheck_evidence(
            FIN3_TABLE_000_110_222_TABLE,
            fin3_table_000_110_222_sources,
            fin3_table_000_110_222_targets,
        ),
    )
    _, fin3_table_122_020_110_sources, fin3_table_122_020_110_targets = (
        _finmodel_sets(
            equations_path,
            FIN3_TABLE_122_020_110_TABLE,
        )
    )
    fin3_table_122_020_110_order4_sources = frozenset(
        eq_id for eq_id in fin3_table_122_020_110_sources if eq_id <= order4_max_id
    )
    fin3_table_122_020_110_order4_targets = frozenset(
        eq_id for eq_id in fin3_table_122_020_110_targets if eq_id <= order4_max_id
    )
    fin3_table_122_020_110_strategy = CoverageStrategy(
        strategy_key=FIN3_TABLE_122_020_110_ALL_EQUATIONS_STRATEGY_KEY,
        strategy_version=1,
        verdict=False,
        priority=295,
        coverage_rule=SourceTargetSetsRule(
            source_ids=fin3_table_122_020_110_sources,
            target_ids=fin3_table_122_020_110_targets,
            excluded_blocks=(
                (
                    fin3_table_122_020_110_order4_sources,
                    fin3_table_122_020_110_order4_targets,
                ),
            ),
        ),
        certificate_family="finmodel_fin3_table_122_020_110",
        summary_zh=(
            "Fin 3 显式表 122/020/110 模型反例：全量方程 source 成立、target 不成立。"
        ),
        summary_en=(
            "Fin 3 explicit table 122/020/110 countermodel over all equations: "
            "sources hold, targets fail."
        ),
        description_zh=(
            "使用 Generated/All4x4Tables/Refutation54 发现的 Fin 3 显式运算表 "
            "[[1,2,2],[0,2,0],[1,1,0]]。全量扫描 order<=5 方程，source 为"
            "该模型满足的所有方程，target 为该模型反驳的所有方程。因此任意 "
            "source -> target 蕴含为 false。该策略与已有 finite-model "
            "setcheck 策略存在重叠，但提供新的 union 覆盖。"
        ),
        description_en=(
            "Uses the Fin 3 explicit operation table found from "
            "Generated/All4x4Tables/Refutation54: [[1,2,2],[0,2,0],[1,1,0]]. "
            "The model is checked against all order<=5 equations; sources are "
            "all equations satisfied by the model, and targets are all equations "
            "refuted by the model. Therefore every source -> target implication "
            "is false. This strategy overlaps with existing finite-model "
            "setcheck strategies but adds new union coverage."
        ),
        certificate_mode="finmodel",
        verification_mode="setcheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="fin_table_decide",
        evidence=_finmodel_setcheck_evidence(
            FIN3_TABLE_122_020_110_TABLE,
            fin3_table_122_020_110_sources,
            fin3_table_122_020_110_targets,
        ),
    )
    _, fin3_table_002_112_102_sources, fin3_table_002_112_102_targets = (
        _finmodel_sets(
            equations_path,
            FIN3_TABLE_002_112_102_TABLE,
        )
    )
    fin3_table_002_112_102_order4_sources = frozenset(
        eq_id for eq_id in fin3_table_002_112_102_sources if eq_id <= order4_max_id
    )
    fin3_table_002_112_102_order4_targets = frozenset(
        eq_id for eq_id in fin3_table_002_112_102_targets if eq_id <= order4_max_id
    )
    fin3_table_002_112_102_strategy = CoverageStrategy(
        strategy_key=FIN3_TABLE_002_112_102_ALL_EQUATIONS_STRATEGY_KEY,
        strategy_version=1,
        verdict=False,
        priority=296,
        coverage_rule=SourceTargetSetsRule(
            source_ids=fin3_table_002_112_102_sources,
            target_ids=fin3_table_002_112_102_targets,
            excluded_blocks=(
                (
                    fin3_table_002_112_102_order4_sources,
                    fin3_table_002_112_102_order4_targets,
                ),
            ),
        ),
        certificate_family="finmodel_fin3_table_002_112_102",
        summary_zh=(
            "Fin 3 显式表 002/112/102 模型反例：全量方程 source 成立、target 不成立。"
        ),
        summary_en=(
            "Fin 3 explicit table 002/112/102 countermodel over all equations: "
            "sources hold, targets fail."
        ),
        description_zh=(
            "使用 Generated/All4x4Tables/Refutation147 发现的 Fin 3 显式运算表 "
            "[[0,0,2],[1,1,2],[1,0,2]]。全量扫描 order<=5 方程，source 为"
            "该模型满足的所有方程，target 为该模型反驳的所有方程。因此任意 "
            "source -> target 蕴含为 false。该策略与已有 finite-model "
            "setcheck 策略存在重叠，但提供新的 union 覆盖。"
        ),
        description_en=(
            "Uses the Fin 3 explicit operation table found from "
            "Generated/All4x4Tables/Refutation147: [[0,0,2],[1,1,2],[1,0,2]]. "
            "The model is checked against all order<=5 equations; sources are "
            "all equations satisfied by the model, and targets are all equations "
            "refuted by the model. Therefore every source -> target implication "
            "is false. This strategy overlaps with existing finite-model "
            "setcheck strategies but adds new union coverage."
        ),
        certificate_mode="finmodel",
        verification_mode="setcheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="fin_table_decide",
        evidence=_finmodel_setcheck_evidence(
            FIN3_TABLE_002_112_102_TABLE,
            fin3_table_002_112_102_sources,
            fin3_table_002_112_102_targets,
        ),
    )
    _, fin3_table_011_012_110_sources, fin3_table_011_012_110_targets = (
        _finmodel_sets(
            equations_path,
            FIN3_TABLE_011_012_110_TABLE,
        )
    )
    fin3_table_011_012_110_order4_sources = frozenset(
        eq_id for eq_id in fin3_table_011_012_110_sources if eq_id <= order4_max_id
    )
    fin3_table_011_012_110_order4_targets = frozenset(
        eq_id for eq_id in fin3_table_011_012_110_targets if eq_id <= order4_max_id
    )
    fin3_table_011_012_110_strategy = CoverageStrategy(
        strategy_key=FIN3_TABLE_011_012_110_ALL_EQUATIONS_STRATEGY_KEY,
        strategy_version=1,
        verdict=False,
        priority=297,
        coverage_rule=SourceTargetSetsRule(
            source_ids=fin3_table_011_012_110_sources,
            target_ids=fin3_table_011_012_110_targets,
            excluded_blocks=(
                (
                    fin3_table_011_012_110_order4_sources,
                    fin3_table_011_012_110_order4_targets,
                ),
            ),
        ),
        certificate_family="finmodel_fin3_table_011_012_110",
        summary_zh=(
            "Fin 3 显式表 011/012/110 模型反例：全量方程 source 成立、target 不成立。"
        ),
        summary_en=(
            "Fin 3 explicit table 011/012/110 countermodel over all equations: "
            "sources hold, targets fail."
        ),
        description_zh=(
            "使用 Generated/All4x4Tables/Refutation63 发现的 Fin 3 显式运算表 "
            "[[0,1,1],[0,1,2],[1,1,0]]。全量扫描 order<=5 方程，source 为"
            "该模型满足的所有方程，target 为该模型反驳的所有方程。因此任意 "
            "source -> target 蕴含为 false。该策略与已有 finite-model "
            "setcheck 策略存在重叠，但提供新的 union 覆盖。"
        ),
        description_en=(
            "Uses the Fin 3 explicit operation table found from "
            "Generated/All4x4Tables/Refutation63: [[0,1,1],[0,1,2],[1,1,0]]. "
            "The model is checked against all order<=5 equations; sources are "
            "all equations satisfied by the model, and targets are all equations "
            "refuted by the model. Therefore every source -> target implication "
            "is false. This strategy overlaps with existing finite-model "
            "setcheck strategies but adds new union coverage."
        ),
        certificate_mode="finmodel",
        verification_mode="setcheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="fin_table_decide",
        evidence=_finmodel_setcheck_evidence(
            FIN3_TABLE_011_012_110_TABLE,
            fin3_table_011_012_110_sources,
            fin3_table_011_012_110_targets,
        ),
    )
    fin5_table_02413_41302_30241_24130_13024_strategy = (
        _build_finmodel_setcheck_strategy(
            equations_path=equations_path,
            order4_max_id=order4_max_id,
            table=FIN5_TABLE_02413_41302_30241_24130_13024_TABLE,
            strategy_key=FIN5_TABLE_02413_41302_30241_24130_13024_ALL_EQUATIONS_STRATEGY_KEY,
            priority=298,
            discovery_label="smallest_magma_examples label 2294",
        )
    )
    fin5_table_03142_31420_14203_42031_20314_strategy = (
        _build_finmodel_setcheck_strategy(
            equations_path=equations_path,
            order4_max_id=order4_max_id,
            table=FIN5_TABLE_03142_31420_14203_42031_20314_TABLE,
            strategy_key=FIN5_TABLE_03142_31420_14203_42031_20314_ALL_EQUATIONS_STRATEGY_KEY,
            priority=299,
            discovery_label="smallest_magma_examples label 1516",
        )
    )
    fin5_table_02143_41320_34201_10432_23014_strategy = (
        _build_finmodel_setcheck_strategy(
            equations_path=equations_path,
            order4_max_id=order4_max_id,
            table=FIN5_TABLE_02143_41320_34201_10432_23014_TABLE,
            strategy_key=FIN5_TABLE_02143_41320_34201_10432_23014_ALL_EQUATIONS_STRATEGY_KEY,
            priority=300,
            discovery_label="smallest_magma_examples label 1313",
        )
    )
    fin4_table_0011_2233_0011_2233_strategy = _build_finmodel_setcheck_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        table=FIN4_TABLE_0011_2233_0011_2233_TABLE,
        strategy_key=FIN4_TABLE_0011_2233_0011_2233_ALL_EQUATIONS_STRATEGY_KEY,
        priority=301,
        discovery_label="smallest_magma_examples label 168",
    )
    fin7_table_0214365_3150624_4625031_6543210_5361402_2406153_1032546_strategy = (
        _build_finmodel_setcheck_strategy(
            equations_path=equations_path,
            order4_max_id=order4_max_id,
            table=FIN7_TABLE_0214365_3150624_4625031_6543210_5361402_2406153_1032546_TABLE,
            strategy_key=FIN7_TABLE_0214365_3150624_4625031_6543210_5361402_2406153_1032546_ALL_EQUATIONS_STRATEGY_KEY,
            priority=302,
            discovery_label="smallest_magma_examples label 1286",
        )
    )
    fin5_table_31420_02341_14032_40213_23104_strategy = (
        _build_finmodel_setcheck_strategy(
            equations_path=equations_path,
            order4_max_id=order4_max_id,
            table=FIN5_TABLE_31420_02341_14032_40213_23104_TABLE,
            strategy_key=FIN5_TABLE_31420_02341_14032_40213_23104_ALL_EQUATIONS_STRATEGY_KEY,
            priority=303,
            discovery_label="smallest_magma_examples label 2903",
        )
    )
    fin5_table_34120_20413_01234_13042_42301_strategy = (
        _build_finmodel_setcheck_strategy(
            equations_path=equations_path,
            order4_max_id=order4_max_id,
            table=FIN5_TABLE_34120_20413_01234_13042_42301_TABLE,
            strategy_key=FIN5_TABLE_34120_20413_01234_13042_42301_ALL_EQUATIONS_STRATEGY_KEY,
            priority=304,
            discovery_label="smallest_magma_examples label 704",
        )
    )
    fin4_table_1032_3210_2301_0123_strategy = (
        _build_finmodel_setcheck_strategy(
            equations_path=equations_path,
            order4_max_id=order4_max_id,
            table=FIN4_TABLE_1032_3210_2301_0123_TABLE,
            strategy_key=FIN4_TABLE_1032_3210_2301_0123_ALL_EQUATIONS_STRATEGY_KEY,
            priority=305,
            discovery_label="smallest_magma_examples label 1110",
        )
    )
    fin3_table_000_000_001_strategy = _build_finmodel_setcheck_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        table=FIN3_TABLE_000_000_001_TABLE,
        strategy_key=FIN3_TABLE_000_000_001_ALL_EQUATIONS_STRATEGY_KEY,
        priority=306,
        discovery_label="enumerate_magmas_order3 enum_order3_2",
    )
    fin3_table_000_000_010_strategy = _build_finmodel_setcheck_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        table=FIN3_TABLE_000_000_010_TABLE,
        strategy_key=FIN3_TABLE_000_000_010_ALL_EQUATIONS_STRATEGY_KEY,
        priority=307,
        discovery_label="enumerate_magmas_order3 enum_order3_4",
    )
    fin3_table_000_000_020_strategy = _build_finmodel_setcheck_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        table=FIN3_TABLE_000_000_020_TABLE,
        strategy_key=FIN3_TABLE_000_000_020_ALL_EQUATIONS_STRATEGY_KEY,
        priority=308,
        discovery_label="enumerate_magmas_order3 enum_order3_7",
    )
    fin3_table_000_000_100_strategy = _build_finmodel_setcheck_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        table=FIN3_TABLE_000_000_100_TABLE,
        strategy_key=FIN3_TABLE_000_000_100_ALL_EQUATIONS_STRATEGY_KEY,
        priority=309,
        discovery_label="enumerate_magmas_order3 enum_order3_10",
    )
    fin3_table_001_000_000_strategy = _build_finmodel_setcheck_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        table=FIN3_TABLE_001_000_000_TABLE,
        strategy_key=FIN3_TABLE_001_000_000_ALL_EQUATIONS_STRATEGY_KEY,
        priority=310,
        discovery_label="enumerate_magmas_order3 enum_order3_730",
    )
    fin3_table_000_000_011_strategy = _build_finmodel_setcheck_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        table=FIN3_TABLE_000_000_011_TABLE,
        strategy_key=FIN3_TABLE_000_000_011_ALL_EQUATIONS_STRATEGY_KEY,
        priority=311,
        discovery_label="enumerate_magmas_order3 enum_order3_5",
    )
    fin3_table_000_001_001_strategy = _build_finmodel_setcheck_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        table=FIN3_TABLE_000_001_001_TABLE,
        strategy_key=FIN3_TABLE_000_001_001_ALL_EQUATIONS_STRATEGY_KEY,
        priority=312,
        discovery_label="enumerate_magmas_order3 enum_order3_29",
    )
    fin3_table_000_001_010_strategy = _build_finmodel_setcheck_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        table=FIN3_TABLE_000_001_010_TABLE,
        strategy_key=FIN3_TABLE_000_001_010_ALL_EQUATIONS_STRATEGY_KEY,
        priority=313,
        discovery_label="enumerate_magmas_order3 enum_order3_31",
    )
    fin3_table_000_020_001_strategy = _build_finmodel_setcheck_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        table=FIN3_TABLE_000_020_001_TABLE,
        strategy_key=FIN3_TABLE_000_020_001_ALL_EQUATIONS_STRATEGY_KEY,
        priority=314,
        discovery_label="enumerate_magmas_order3 enum_order3_164",
    )
    fin3_table_000_122_122_strategy = _build_finmodel_setcheck_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        table=FIN3_TABLE_000_122_122_TABLE,
        strategy_key=FIN3_TABLE_000_122_122_ALL_EQUATIONS_STRATEGY_KEY,
        priority=315,
        discovery_label="enumerate_magmas_order3 enum_order3_477",
    )
    is_default_equations = Path(equations_path).resolve() == DEFAULT_EQ_SIZE5_PATH.resolve()
    model_family_predicatecheck_strategies = (
        build_model_family_predicatecheck_strategies(
            equations_path=equations_path,
            order4_max_id=order4_max_id,
        )
        if is_default_equations
        else []
    )
    structured_affine_mod5_a3_b2_c0_strategy = _build_finmodel_setcheck_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        table=STRUCTURED_AFFINE_MOD5_A3_B2_C0_TABLE,
        strategy_key=STRUCTURED_AFFINE_MOD5_A3_B2_C0_STRATEGY_KEY,
        priority=322,
        discovery_label=(
            "structured_finite_models_ranked_20260519 affine_mod5_a3_b2_c0"
        ),
        evidence_extra={
            "candidate_label": "affine_mod5_a3_b2_c0",
            "candidate_scoring_method": "closed_form_affine_linear_mod_n",
            "candidate_exact_increment": 2_445_837,
            "candidate_ranked_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_structured_finite_models_ranked_20260519.jsonl"
            ),
            "candidate_remote_smoke_input": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_structured_affine_mod5_a3_b2_c0_smoke_20260519_input.jsonl"
            ),
            "candidate_remote_smoke_results": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_structured_affine_mod5_a3_b2_c0_smoke_20260519_results.jsonl"
            ),
            "candidate_remote_smoke_summary": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_structured_affine_mod5_a3_b2_c0_smoke_20260519_summary.json"
            ),
            "remote_smoke_accepted_count": 4,
            "remote_smoke_total_count": 4,
        },
    )
    structured_affine_mod5_a2_b3_c0_strategy = _build_finmodel_setcheck_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        table=STRUCTURED_AFFINE_MOD5_A2_B3_C0_TABLE,
        strategy_key=STRUCTURED_AFFINE_MOD5_A2_B3_C0_STRATEGY_KEY,
        priority=323,
        discovery_label=(
            "structured_finite_models_ranked_20260519 affine_mod5_a2_b3_c0"
        ),
        evidence_extra={
            "candidate_label": "affine_mod5_a2_b3_c0",
            "candidate_scoring_method": "closed_form_affine_linear_mod_n",
            "candidate_exact_increment": 2_431_039,
            "candidate_ranked_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_structured_finite_models_ranked_20260519.jsonl"
            ),
            "candidate_increment_after_previous_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_structured_affine_mod5_a2_b3_c0_after_c0_increment_20260519.json"
            ),
            "candidate_remote_smoke_input": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_structured_affine_mod5_a2_b3_c0_smoke_20260519_input.jsonl"
            ),
            "candidate_remote_smoke_results": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_structured_affine_mod5_a2_b3_c0_smoke_20260519_results.jsonl"
            ),
            "candidate_remote_smoke_summary": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_structured_affine_mod5_a2_b3_c0_smoke_20260519_summary.json"
            ),
            "remote_smoke_accepted_count": 4,
            "remote_smoke_total_count": 4,
        },
    )
    structured_affine_mod4_a0_b1_c1_strategy = _build_finmodel_setcheck_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        table=STRUCTURED_AFFINE_MOD4_A0_B1_C1_TABLE,
        strategy_key=STRUCTURED_AFFINE_MOD4_A0_B1_C1_STRATEGY_KEY,
        priority=324,
        discovery_label=(
            "structured_finite_models_ranked_20260519 affine_mod4_a0_b1_c1"
        ),
        evidence_extra={
            "candidate_label": "affine_mod4_a0_b1_c1",
            "candidate_scoring_method": "closed_form_affine_linear_mod_n",
            "candidate_exact_increment": 2_050_881,
            "candidate_ranked_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_structured_finite_models_ranked_20260519.jsonl"
            ),
            "candidate_increment_after_previous_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_structured_affine_mod4_a0_b1_c1_after_two_affine_mod5_"
                "increment_20260519.json"
            ),
            "candidate_remote_smoke_input": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_structured_affine_mod4_a0_b1_c1_smoke_20260519_input.jsonl"
            ),
            "candidate_remote_smoke_results": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_structured_affine_mod4_a0_b1_c1_smoke_20260519_results.jsonl"
            ),
            "candidate_remote_smoke_summary": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_structured_affine_mod4_a0_b1_c1_smoke_20260519_summary.json"
            ),
            "remote_smoke_accepted_count": 4,
            "remote_smoke_total_count": 4,
        },
    )
    structured_affine_mod4_a1_b0_c3_strategy = _build_finmodel_setcheck_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        table=STRUCTURED_AFFINE_MOD4_A1_B0_C3_TABLE,
        strategy_key=STRUCTURED_AFFINE_MOD4_A1_B0_C3_STRATEGY_KEY,
        priority=325,
        discovery_label=(
            "structured_finite_models affine_mod4_a1_b0_c3 partial rerank"
        ),
        evidence_extra={
            "candidate_label": "affine_mod4_a1_b0_c3",
            "candidate_scoring_method": "closed_form_affine_linear_mod_n",
            "candidate_exact_increment": 2_044_868,
            "candidate_ranked_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_selected_after_current_sequential_"
                "20260519.jsonl"
            ),
            "candidate_partial_scan_summary": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_after_current_rank_20260519_"
                "partial_summary.json"
            ),
            "candidate_remote_smoke_input": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_top3_smoke_20260519_input.jsonl"
            ),
            "candidate_remote_smoke_results": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_top3_smoke_20260519_results.jsonl"
            ),
            "candidate_remote_smoke_summary": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_top3_smoke_20260519_summary.json"
            ),
            "remote_smoke_accepted_count": 4,
            "remote_smoke_total_count": 4,
        },
    )
    structured_affine_mod5_a0_b1_c4_strategy = _build_finmodel_setcheck_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        table=STRUCTURED_AFFINE_MOD5_A0_B1_C4_TABLE,
        strategy_key=STRUCTURED_AFFINE_MOD5_A0_B1_C4_STRATEGY_KEY,
        priority=326,
        discovery_label=(
            "structured_finite_models affine_mod5_a0_b1_c4 partial rerank"
        ),
        evidence_extra={
            "candidate_label": "affine_mod5_a0_b1_c4",
            "candidate_scoring_method": "closed_form_affine_linear_mod_n",
            "candidate_exact_increment": 1_639_526,
            "candidate_ranked_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_selected_after_current_sequential_"
                "20260519.jsonl"
            ),
            "candidate_partial_scan_summary": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_after_current_rank_20260519_"
                "partial_summary.json"
            ),
            "candidate_remote_smoke_input": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_top3_smoke_20260519_input.jsonl"
            ),
            "candidate_remote_smoke_results": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_top3_smoke_20260519_results.jsonl"
            ),
            "candidate_remote_smoke_summary": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_top3_smoke_20260519_summary.json"
            ),
            "remote_smoke_accepted_count": 3,
            "remote_smoke_total_count": 3,
        },
    )
    structured_affine_mod5_a1_b0_c4_strategy = _build_finmodel_setcheck_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        table=STRUCTURED_AFFINE_MOD5_A1_B0_C4_TABLE,
        strategy_key=STRUCTURED_AFFINE_MOD5_A1_B0_C4_STRATEGY_KEY,
        priority=327,
        discovery_label=(
            "structured_finite_models affine_mod5_a1_b0_c4 partial rerank"
        ),
        evidence_extra={
            "candidate_label": "affine_mod5_a1_b0_c4",
            "candidate_scoring_method": "closed_form_affine_linear_mod_n",
            "candidate_exact_increment": 1_639_189,
            "candidate_ranked_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_selected_after_current_sequential_"
                "20260519.jsonl"
            ),
            "candidate_partial_scan_summary": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_after_current_rank_20260519_"
                "partial_summary.json"
            ),
            "candidate_remote_smoke_input": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_top3_smoke_20260519_input.jsonl"
            ),
            "candidate_remote_smoke_results": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_top3_smoke_20260519_results.jsonl"
            ),
            "candidate_remote_smoke_summary": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_top3_smoke_20260519_summary.json"
            ),
            "remote_smoke_accepted_count": 3,
            "remote_smoke_total_count": 3,
        },
    )
    structured_etp_order4_refutation516_strategy = _build_finmodel_setcheck_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        table=STRUCTURED_ETP_ORDER4_REFUTATION516_TABLE,
        strategy_key=STRUCTURED_ETP_ORDER4_REFUTATION516_STRATEGY_KEY,
        priority=328,
        discovery_label=(
            "equational_theories Generated/All4x4Tables Refutation516"
        ),
        evidence_extra={
            "candidate_label": "etp_order4_refutation516",
            "candidate_source": (
                "equational_theories/Generated/All4x4Tables/Refutation516.lean"
            ),
            "candidate_scoring_method": "etp_order4_structured_setcheck_rerank",
            "candidate_exact_increment": 1_290_220,
            "candidate_ranked_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_non_affine_structured_order4_all_after_top3_rank_20260519.jsonl"
            ),
            "candidate_sequential_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_non_affine_structured_order4_selected_after_top3_"
                "sequential_20260519.jsonl"
            ),
            "candidate_remote_smoke_input": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_non_affine_structured_order4_top2_smoke_20260519_input.jsonl"
            ),
            "candidate_remote_smoke_results": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_non_affine_structured_order4_top2_smoke_20260519_results.jsonl"
            ),
            "candidate_remote_smoke_summary": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_non_affine_structured_order4_top2_smoke_20260519_summary.json"
            ),
            "remote_smoke_accepted_count": 4,
            "remote_smoke_total_count": 4,
        },
    )
    structured_etp_order4_refutation482_strategy = _build_finmodel_setcheck_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        table=STRUCTURED_ETP_ORDER4_REFUTATION482_TABLE,
        strategy_key=STRUCTURED_ETP_ORDER4_REFUTATION482_STRATEGY_KEY,
        priority=329,
        discovery_label=(
            "equational_theories Generated/All4x4Tables Refutation482"
        ),
        evidence_extra={
            "candidate_label": "etp_order4_refutation482",
            "candidate_source": (
                "equational_theories/Generated/All4x4Tables/Refutation482.lean"
            ),
            "candidate_scoring_method": "etp_order4_structured_setcheck_rerank",
            "candidate_exact_increment": 1_141_366,
            "candidate_independent_increment": 1_141_401,
            "candidate_ranked_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_non_affine_structured_order4_all_after_top3_rank_20260519.jsonl"
            ),
            "candidate_sequential_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_non_affine_structured_order4_selected_after_top3_"
                "sequential_20260519.jsonl"
            ),
            "candidate_remote_smoke_input": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_non_affine_structured_order4_top2_smoke_20260519_input.jsonl"
            ),
            "candidate_remote_smoke_results": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_non_affine_structured_order4_top2_smoke_20260519_results.jsonl"
            ),
            "candidate_remote_smoke_summary": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_non_affine_structured_order4_top2_smoke_20260519_summary.json"
            ),
            "remote_smoke_accepted_count": 4,
            "remote_smoke_total_count": 4,
        },
    )
    structured_all4x4_refutation4_strategy = _build_finmodel_setcheck_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        table=STRUCTURED_ALL4X4_REFUTATION4_TABLE,
        strategy_key=STRUCTURED_ALL4X4_REFUTATION4_STRATEGY_KEY,
        priority=339,
        discovery_label=(
            "equational_theories Generated/All4x4Tables Refutation4"
        ),
        evidence_extra={
            "candidate_label": "etp_refutation4",
            "candidate_source": (
                "external/equational_theories/equational_theories/"
                "Generated/All4x4Tables/Refutation4.lean"
            ),
            "candidate_scoring_method": "all4x4_full_rerank_after_current",
            "candidate_exact_increment": 2_394_698,
            "candidate_batch_cumulative_increment": 2_394_698,
            "candidate_ranked_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_non_affine_all4x4_after_current_exact_20260520.jsonl"
            ),
            "candidate_sequential_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_non_affine_all4x4_union_batch_after_current_20260520.jsonl"
            ),
            "candidate_register_checklist": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_non_affine_all4x4_prefix5_register_checklist_"
                "20260520_summary.json"
            ),
            "candidate_remote_smoke_input": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_non_affine_all4x4_prefix5_remote_smoke_"
                "20260520_input.jsonl"
            ),
            "candidate_remote_smoke_results": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_non_affine_all4x4_prefix5_remote_smoke_"
                "20260520_results.jsonl"
            ),
            "candidate_remote_smoke_summary": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_non_affine_all4x4_prefix5_remote_smoke_"
                "20260520_summary.json"
            ),
            "remote_smoke_accepted_count": 4,
            "remote_smoke_total_count": 4,
            "remote_smoke_prefix_accepted_count": 20,
            "remote_smoke_prefix_total_count": 20,
        },
    )
    structured_affine_mod7_a2_b5_c6_strategy = _build_finmodel_setcheck_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        table=STRUCTURED_AFFINE_MOD7_A2_B5_C6_TABLE,
        strategy_key=STRUCTURED_AFFINE_MOD7_A2_B5_C6_STRATEGY_KEY,
        priority=330,
        discovery_label=(
            "structured_finite_models affine_mod7_a2_b5_c6 current rerank"
        ),
        evidence_extra={
            "candidate_label": "affine_mod7_a2_b5_c6",
            "candidate_scoring_method": (
                "closed_form_affine_linear_mod_n_current_rerank"
            ),
            "candidate_exact_increment": 982_772,
            "candidate_ranked_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_top30_after_order4_top2_current_"
                "rerank_20260519.jsonl"
            ),
            "candidate_sequential_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_mod7_top2_after_order4_top2_"
                "sequential_20260519.json"
            ),
            "candidate_remote_smoke_input": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_mod7_top2_smoke_20260519_input.jsonl"
            ),
            "candidate_remote_smoke_results": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_mod7_top2_smoke_20260519_results.jsonl"
            ),
            "candidate_remote_smoke_summary": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_mod7_top2_smoke_20260519_summary.json"
            ),
            "remote_smoke_accepted_count": 4,
            "remote_smoke_total_count": 4,
        },
    )
    structured_affine_mod7_a5_b2_c6_strategy = _build_finmodel_setcheck_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        table=STRUCTURED_AFFINE_MOD7_A5_B2_C6_TABLE,
        strategy_key=STRUCTURED_AFFINE_MOD7_A5_B2_C6_STRATEGY_KEY,
        priority=331,
        discovery_label=(
            "structured_finite_models affine_mod7_a5_b2_c6 current rerank"
        ),
        evidence_extra={
            "candidate_label": "affine_mod7_a5_b2_c6",
            "candidate_scoring_method": (
                "closed_form_affine_linear_mod_n_current_rerank"
            ),
            "candidate_exact_increment": 978_963,
            "candidate_independent_increment": 979_890,
            "candidate_ranked_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_top30_after_order4_top2_current_"
                "rerank_20260519.jsonl"
            ),
            "candidate_sequential_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_mod7_top2_after_order4_top2_"
                "sequential_20260519.json"
            ),
            "candidate_remote_smoke_input": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_mod7_top2_smoke_20260519_input.jsonl"
            ),
            "candidate_remote_smoke_results": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_mod7_top2_smoke_20260519_results.jsonl"
            ),
            "candidate_remote_smoke_summary": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_mod7_top2_smoke_20260519_summary.json"
            ),
            "remote_smoke_accepted_count": 4,
            "remote_smoke_total_count": 4,
        },
    )
    structured_affine_mod7_a6_b2_c0_strategy = _build_finmodel_setcheck_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        table=STRUCTURED_AFFINE_MOD7_A6_B2_C0_TABLE,
        strategy_key=STRUCTURED_AFFINE_MOD7_A6_B2_C0_STRATEGY_KEY,
        priority=332,
        discovery_label=(
            "structured_finite_models affine_mod7_a6_b2_c0 current rerank"
        ),
        evidence_extra={
            "candidate_label": "affine_mod7_a6_b2_c0",
            "candidate_scoring_method": (
                "closed_form_affine_linear_mod_n_current_rerank"
            ),
            "candidate_exact_increment": 712_809,
            "candidate_ranked_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_top30_after_mod7_current_"
                "rerank_20260519.jsonl"
            ),
            "candidate_remote_smoke_input": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_mod7_next_smoke_20260519_input.jsonl"
            ),
            "candidate_remote_smoke_results": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_mod7_next_smoke_20260519_results.jsonl"
            ),
            "candidate_remote_smoke_summary": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_mod7_next_smoke_20260519_summary.json"
            ),
            "remote_smoke_accepted_count": 4,
            "remote_smoke_total_count": 4,
        },
    )
    structured_affine_mod5_a1_b3_c4_strategy = _build_finmodel_setcheck_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        table=STRUCTURED_AFFINE_MOD5_A1_B3_C4_TABLE,
        strategy_key=STRUCTURED_AFFINE_MOD5_A1_B3_C4_STRATEGY_KEY,
        priority=333,
        discovery_label=(
            "structured_finite_models affine_mod5_a1_b3_c4 current rerank"
        ),
        evidence_extra={
            "candidate_label": "affine_mod5_a1_b3_c4",
            "candidate_scoring_method": (
                "closed_form_affine_linear_mod_n_current_rerank"
            ),
            "candidate_exact_increment": 606_069,
            "candidate_ranked_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_top30_after_mod7_next_current_"
                "rerank_20260519.jsonl"
            ),
            "candidate_sequential_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_mod5_next_top2_sequential_20260519.json"
            ),
            "candidate_remote_smoke_input": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_mod5_next_top2_smoke_20260519_input.jsonl"
            ),
            "candidate_remote_smoke_results": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_mod5_next_top2_smoke_20260519_results.jsonl"
            ),
            "candidate_remote_smoke_summary": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_mod5_next_top2_smoke_20260519_summary.json"
            ),
            "remote_smoke_accepted_count": 4,
            "remote_smoke_total_count": 4,
        },
    )
    structured_affine_mod5_a3_b1_c4_strategy = _build_finmodel_setcheck_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        table=STRUCTURED_AFFINE_MOD5_A3_B1_C4_TABLE,
        strategy_key=STRUCTURED_AFFINE_MOD5_A3_B1_C4_STRATEGY_KEY,
        priority=334,
        discovery_label=(
            "structured_finite_models affine_mod5_a3_b1_c4 current rerank"
        ),
        evidence_extra={
            "candidate_label": "affine_mod5_a3_b1_c4",
            "candidate_scoring_method": (
                "closed_form_affine_linear_mod_n_current_rerank"
            ),
            "candidate_exact_increment": 602_979,
            "candidate_independent_increment": 603_109,
            "candidate_ranked_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_top30_after_mod7_next_current_"
                "rerank_20260519.jsonl"
            ),
            "candidate_sequential_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_mod5_next_top2_sequential_20260519.json"
            ),
            "candidate_remote_smoke_input": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_mod5_next_top2_smoke_20260519_input.jsonl"
            ),
            "candidate_remote_smoke_results": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_mod5_next_top2_smoke_20260519_results.jsonl"
            ),
            "candidate_remote_smoke_summary": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_mod5_next_top2_smoke_20260519_summary.json"
            ),
            "remote_smoke_accepted_count": 4,
            "remote_smoke_total_count": 4,
        },
    )
    structured_affine_mod7_a1_b3_c6_strategy = _build_finmodel_setcheck_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        table=STRUCTURED_AFFINE_MOD7_A1_B3_C6_TABLE,
        strategy_key=STRUCTURED_AFFINE_MOD7_A1_B3_C6_STRATEGY_KEY,
        priority=335,
        discovery_label=(
            "structured_finite_models affine_mod7_a1_b3_c6 low-order tail combo"
        ),
        evidence_extra={
            "candidate_label": "affine_mod7_a1_b3_c6",
            "candidate_scoring_method": (
                "closed_form_affine_low_order_tail_combo_current_rerank"
            ),
            "candidate_exact_increment": 376_264,
            "candidate_combo_increment": 1_113_744,
            "candidate_ranked_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_top200_after_mod5_next_current_"
                "rerank_20260519.jsonl"
            ),
            "candidate_sequential_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_low_order_tail_combo_after_mod5_next_"
                "sequential_20260519.jsonl"
            ),
            "candidate_remote_smoke_input": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_low_order_tail_combo_smoke_20260519_input.jsonl"
            ),
            "candidate_remote_smoke_results": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_low_order_tail_combo_smoke_20260519_results.jsonl"
            ),
            "candidate_remote_smoke_summary": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_low_order_tail_combo_smoke_20260519_summary.json"
            ),
            "remote_smoke_accepted_count": 4,
            "remote_smoke_total_count": 4,
        },
    )
    structured_affine_mod7_a3_b1_c6_strategy = _build_finmodel_setcheck_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        table=STRUCTURED_AFFINE_MOD7_A3_B1_C6_TABLE,
        strategy_key=STRUCTURED_AFFINE_MOD7_A3_B1_C6_STRATEGY_KEY,
        priority=336,
        discovery_label=(
            "structured_finite_models affine_mod7_a3_b1_c6 low-order tail combo"
        ),
        evidence_extra={
            "candidate_label": "affine_mod7_a3_b1_c6",
            "candidate_scoring_method": (
                "closed_form_affine_low_order_tail_combo_current_rerank"
            ),
            "candidate_exact_increment": 376_157,
            "candidate_combo_increment": 1_113_744,
            "candidate_ranked_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_top200_after_mod5_next_current_"
                "rerank_20260519.jsonl"
            ),
            "candidate_sequential_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_low_order_tail_combo_after_mod5_next_"
                "sequential_20260519.jsonl"
            ),
            "candidate_remote_smoke_input": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_low_order_tail_combo_smoke_20260519_input.jsonl"
            ),
            "candidate_remote_smoke_results": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_low_order_tail_combo_smoke_20260519_results.jsonl"
            ),
            "candidate_remote_smoke_summary": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_low_order_tail_combo_smoke_20260519_summary.json"
            ),
            "remote_smoke_accepted_count": 4,
            "remote_smoke_total_count": 4,
        },
    )
    structured_affine_mod4_a3_b2_c3_strategy = _build_finmodel_setcheck_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        table=STRUCTURED_AFFINE_MOD4_A3_B2_C3_TABLE,
        strategy_key=STRUCTURED_AFFINE_MOD4_A3_B2_C3_STRATEGY_KEY,
        priority=337,
        discovery_label=(
            "structured_finite_models affine_mod4_a3_b2_c3 low-order tail combo"
        ),
        evidence_extra={
            "candidate_label": "affine_mod4_a3_b2_c3",
            "candidate_scoring_method": (
                "closed_form_affine_low_order_tail_combo_current_rerank"
            ),
            "candidate_exact_increment": 181_916,
            "candidate_combo_increment": 1_113_744,
            "candidate_ranked_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_top200_after_mod5_next_current_"
                "rerank_20260519.jsonl"
            ),
            "candidate_sequential_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_low_order_tail_combo_after_mod5_next_"
                "sequential_20260519.jsonl"
            ),
            "candidate_remote_smoke_input": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_low_order_tail_combo_smoke_20260519_input.jsonl"
            ),
            "candidate_remote_smoke_results": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_low_order_tail_combo_smoke_20260519_results.jsonl"
            ),
            "candidate_remote_smoke_summary": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_low_order_tail_combo_smoke_20260519_summary.json"
            ),
            "remote_smoke_accepted_count": 4,
            "remote_smoke_total_count": 4,
        },
    )
    structured_affine_mod4_a2_b3_c3_strategy = _build_finmodel_setcheck_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
        table=STRUCTURED_AFFINE_MOD4_A2_B3_C3_TABLE,
        strategy_key=STRUCTURED_AFFINE_MOD4_A2_B3_C3_STRATEGY_KEY,
        priority=338,
        discovery_label=(
            "structured_finite_models affine_mod4_a2_b3_c3 low-order tail combo"
        ),
        evidence_extra={
            "candidate_label": "affine_mod4_a2_b3_c3",
            "candidate_scoring_method": (
                "closed_form_affine_low_order_tail_combo_current_rerank"
            ),
            "candidate_exact_increment": 179_407,
            "candidate_combo_increment": 1_113_744,
            "candidate_ranked_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_top200_after_mod5_next_current_"
                "rerank_20260519.jsonl"
            ),
            "candidate_sequential_artifact": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_low_order_tail_combo_after_mod5_next_"
                "sequential_20260519.jsonl"
            ),
            "candidate_remote_smoke_input": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_low_order_tail_combo_smoke_20260519_input.jsonl"
            ),
            "candidate_remote_smoke_results": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_low_order_tail_combo_smoke_20260519_results.jsonl"
            ),
            "candidate_remote_smoke_summary": (
                "data/processed/order5_strategy_registry/candidates/"
                "false_affine_structured_low_order_tail_combo_smoke_20260519_summary.json"
            ),
            "remote_smoke_accepted_count": 4,
            "remote_smoke_total_count": 4,
        },
    )
    structured_affine_low_order_tail_combo2_strategies = [
        _build_finmodel_setcheck_strategy(
            equations_path=equations_path,
            order4_max_id=order4_max_id,
            table=spec["table"],
            strategy_key=spec["strategy_key"],
            priority=spec["priority"],
            discovery_label=(
                "structured_finite_models "
                f"{spec['label']} low-order tail combo2"
            ),
            evidence_extra={
                "candidate_label": spec["label"],
                "candidate_scoring_method": (
                    "closed_form_affine_low_order_tail_combo2_current_rerank"
                ),
                "candidate_exact_increment": spec["current_increment"],
                "candidate_combo_increment": 1_030_435,
                "candidate_ranked_artifact": (
                    "data/processed/order5_strategy_registry/candidates/"
                    "false_affine_structured_top200_after_low_order_tail_current_"
                    "rerank_20260519.jsonl"
                ),
                "candidate_sequential_artifact": (
                    "data/processed/order5_strategy_registry/candidates/"
                    "false_affine_structured_low_order_tail_combo2_sequential_"
                    "20260519.jsonl"
                ),
                "candidate_remote_smoke_input": (
                    "data/processed/order5_strategy_registry/candidates/"
                    "false_affine_structured_low_order_tail_combo2_smoke_"
                    "20260519_input.jsonl"
                ),
                "candidate_remote_smoke_results": (
                    "data/processed/order5_strategy_registry/candidates/"
                    "false_affine_structured_low_order_tail_combo2_smoke_"
                    "20260519_results.jsonl"
                ),
                "candidate_remote_smoke_summary": (
                    "data/processed/order5_strategy_registry/candidates/"
                    "false_affine_structured_low_order_tail_combo2_smoke_"
                    "20260519_summary.json"
                ),
                "remote_smoke_accepted_count": len(
                    [
                        pair
                        for pair in spec["representative_pairs"].values()
                        if pair is not None
                    ]
                ),
                "remote_smoke_total_count": len(
                    [
                        pair
                        for pair in spec["representative_pairs"].values()
                        if pair is not None
                    ]
                ),
            },
        )
        for spec in STRUCTURED_AFFINE_LOW_ORDER_TAIL_COMBO2_SPECS
    ]
    structured_affine_mod11_top2_matchop_nohb_strategies = [
        _build_affine_mod_setcheck_strategy(
            equations_path=equations_path,
            order4_max_id=order4_max_id,
            modulus=spec["modulus"],
            a=spec["a"],
            b=spec["b"],
            c=spec["c"],
            table=spec["table"],
            strategy_key=spec["strategy_key"],
            priority=spec["priority"],
            discovery_label=(
                "structured_finite_models "
                f"{spec['label']} mod11 matchop no-heartbeat"
            ),
            evidence_extra={
                "candidate_label": spec["label"],
                "candidate_scoring_method": (
                    "closed_form_affine_mod11_top2_after_low_order_tail_combo2"
                ),
                "candidate_exact_increment": spec["current_increment"],
                "candidate_combo_increment": 1_535_927,
                "candidate_ranked_artifact": (
                    "data/processed/order5_strategy_registry/candidates/"
                    "false_affine_structured_top200_after_low_order_tail_combo2_"
                    "current_rerank_20260519.jsonl"
                ),
                "candidate_sequential_artifact": (
                    "data/processed/order5_strategy_registry/candidates/"
                    "false_affine_structured_mod11_top2_matchop_nohb_symbolic_"
                    "sequential_20260519.json"
                ),
                "candidate_remote_smoke_input": (
                    "data/processed/order5_strategy_registry/candidates/"
                    "false_affine_structured_mod11_top2_matchop_nohb_smoke_"
                    "20260519_input.jsonl"
                ),
                "candidate_remote_smoke_results": (
                    "data/processed/order5_strategy_registry/candidates/"
                    "false_affine_structured_mod11_top2_matchop_nohb_smoke_"
                    "20260519_results.jsonl"
                ),
                "candidate_remote_smoke_summary": (
                    "data/processed/order5_strategy_registry/candidates/"
                    "false_affine_structured_mod11_top2_matchop_nohb_smoke_"
                    "20260519_summary.json"
                ),
                "certificate_encoding": (
                    "direct_match_i_val_j_val_maxHeartbeats0_for_order_ge_10"
                ),
                "remote_smoke_accepted_count": len(
                    [
                        pair
                        for pair in spec["representative_pairs"].values()
                        if pair is not None
                    ]
                ),
                "remote_smoke_total_count": len(
                    [
                        pair
                        for pair in spec["representative_pairs"].values()
                        if pair is not None
                    ]
                ),
            },
        )
        for spec in STRUCTURED_AFFINE_MOD11_TOP2_MATCHOP_NOHB_SPECS
    ]
    structured_affine_mod11_combo9_matchop_nohb_strategies = [
        _build_affine_mod_setcheck_strategy(
            equations_path=equations_path,
            order4_max_id=order4_max_id,
            modulus=spec["modulus"],
            a=spec["a"],
            b=spec["b"],
            c=spec["c"],
            table=spec["table"],
            strategy_key=spec["strategy_key"],
            priority=spec["priority"],
            discovery_label=(
                "structured_finite_models "
                f"{spec['label']} mod11 combo9 matchop no-heartbeat"
            ),
            evidence_extra={
                "candidate_label": spec["label"],
                "candidate_scoring_method": (
                    "closed_form_affine_mod11_combo9_after_smoke"
                ),
                "candidate_exact_increment": spec["current_increment"],
                "candidate_combo_increment": 1_016_745,
                "candidate_ranked_artifact": (
                    "data/processed/order5_strategy_registry/candidates/"
                    "false_affine_structured_top200_after_mod11_top2_"
                    "current_rerank_20260519.jsonl"
                ),
                "candidate_sequential_artifact": (
                    "data/processed/order5_strategy_registry/candidates/"
                    "false_affine_structured_order11_combo9_after_smoke_exact_"
                    "20260519.json"
                ),
                "candidate_remote_smoke_input": (
                    "data/processed/order5_strategy_registry/candidates/"
                    "false_affine_structured_order11_combo10_matchop_nohb_smoke_"
                    "20260519_input.jsonl"
                ),
                "candidate_remote_smoke_results": (
                    "data/processed/order5_strategy_registry/candidates/"
                    "false_affine_structured_order11_combo10_matchop_nohb_smoke_"
                    "20260519_results.jsonl"
                ),
                "candidate_remote_smoke_summary": (
                    "data/processed/order5_strategy_registry/candidates/"
                    "false_affine_structured_order11_combo10_matchop_nohb_smoke_"
                    "20260519_summary.json"
                ),
                "candidate_rejected_review": (
                    "data/processed/order5_strategy_registry/candidates/"
                    "false_affine_structured_order11_combo10_matchop_nohb_"
                    "rejected_20260519_controller_review.json"
                ),
                "certificate_encoding": (
                    "direct_match_i_val_j_val_maxHeartbeats0_for_order_ge_10"
                ),
                "excluded_failed_labels": ("affine_mod11_a5_b5_c9",),
                "remote_smoke_accepted_count": len(spec["smoke_tiers"]),
                "remote_smoke_total_count": len(spec["smoke_tiers"]),
                "remote_smoke_tiers": spec["smoke_tiers"],
            },
        )
        for spec in STRUCTURED_AFFINE_MOD11_COMBO9_MATCHOP_NOHB_SPECS
    ]
    structured_affine_low_order_le9_combo19_strategies = [
        _build_affine_mod_setcheck_strategy(
            equations_path=equations_path,
            order4_max_id=order4_max_id,
            modulus=spec["modulus"],
            a=spec["a"],
            b=spec["b"],
            c=spec["c"],
            table=spec["table"],
            strategy_key=spec["strategy_key"],
            priority=spec["priority"],
            discovery_label=(
                "structured_finite_models "
                f"{spec['label']} low-order le9 combo19"
            ),
            evidence_extra={
                "candidate_label": spec["label"],
                "candidate_scoring_method": (
                    "closed_form_affine_low_order_le9_greedy_combo_after_mod11_combo9"
                ),
                "candidate_exact_increment": spec["current_increment"],
                "candidate_combo_increment": 1_015_546,
                "candidate_ranked_artifact": (
                    "data/processed/order5_strategy_registry/candidates/"
                    "false_affine_structured_top200_after_mod11_combo9_"
                    "current_rerank_20260519.jsonl"
                ),
                "candidate_sequential_artifact": (
                    "data/processed/order5_strategy_registry/candidates/"
                    "false_affine_structured_low_order_le9_greedy_combo_exact_"
                    "20260519.json"
                ),
                "candidate_remote_smoke_input": (
                    "data/processed/order5_strategy_registry/candidates/"
                    "false_affine_structured_low_order_le9_combo19_smoke_"
                    "20260519_input.jsonl"
                ),
                "candidate_remote_smoke_results": (
                    "data/processed/order5_strategy_registry/candidates/"
                    "false_affine_structured_low_order_le9_combo19_smoke_"
                    "20260519_results.jsonl"
                ),
                "candidate_remote_smoke_summary": (
                    "data/processed/order5_strategy_registry/candidates/"
                    "false_affine_structured_low_order_le9_combo19_smoke_"
                    "20260519_summary.json"
                ),
                "certificate_encoding": "finOpTable_for_order_lt_10",
                "remote_smoke_accepted_count": len(spec["smoke_tiers"]),
                "remote_smoke_total_count": len(spec["smoke_tiers"]),
                "remote_smoke_tiers": spec["smoke_tiers"],
            },
        )
        for spec in STRUCTURED_AFFINE_LOW_ORDER_LE9_COMBO19_SPECS
    ]
    false_strategies = [
        left_projection_strategy,
        constant_strategy,
        right_projection_strategy,
        complement_left_strategy,
        complement_right_strategy,
        left_and_complement_right_strategy,
        complement_left_and_right_strategy,
        xor_strategy,
        and_strategy,
        nor_strategy,
        steiner_strategy,
        right_minus_left_strategy,
        left_minus_right_strategy,
        fin3_table_020_110_122_strategy,
        left_cyclic_successor_strategy,
        right_cyclic_successor_strategy,
        fin3_table_022_010_112_strategy,
        addition_mod3_strategy,
        fin4_table_0231_3102_1320_2013_strategy,
        fin3_table_000_211_122_strategy,
        fin3_table_012_012_102_strategy,
        fin4_table_2013_3102_0231_1320_strategy,
        fin3_table_011_012_012_strategy,
        fin3_table_000_110_222_strategy,
        fin3_table_122_020_110_strategy,
        fin3_table_002_112_102_strategy,
        fin3_table_011_012_110_strategy,
        fin5_table_02413_41302_30241_24130_13024_strategy,
        fin5_table_03142_31420_14203_42031_20314_strategy,
        fin5_table_02143_41320_34201_10432_23014_strategy,
        fin4_table_0011_2233_0011_2233_strategy,
        fin7_table_0214365_3150624_4625031_6543210_5361402_2406153_1032546_strategy,
        fin5_table_31420_02341_14032_40213_23104_strategy,
        fin5_table_34120_20413_01234_13042_42301_strategy,
        fin4_table_1032_3210_2301_0123_strategy,
        fin3_table_000_000_001_strategy,
        fin3_table_000_000_010_strategy,
        fin3_table_000_000_020_strategy,
        fin3_table_000_000_100_strategy,
        fin3_table_001_000_000_strategy,
        fin3_table_000_000_011_strategy,
        fin3_table_000_001_001_strategy,
        fin3_table_000_001_010_strategy,
        fin3_table_000_020_001_strategy,
        fin3_table_000_122_122_strategy,
        *model_family_predicatecheck_strategies,
        structured_affine_mod5_a3_b2_c0_strategy,
        structured_affine_mod5_a2_b3_c0_strategy,
        structured_affine_mod4_a0_b1_c1_strategy,
        structured_affine_mod4_a1_b0_c3_strategy,
        structured_affine_mod5_a0_b1_c4_strategy,
        structured_affine_mod5_a1_b0_c4_strategy,
        structured_etp_order4_refutation516_strategy,
        structured_etp_order4_refutation482_strategy,
        structured_all4x4_refutation4_strategy,
        structured_affine_mod7_a2_b5_c6_strategy,
        structured_affine_mod7_a5_b2_c6_strategy,
        structured_affine_mod7_a6_b2_c0_strategy,
        structured_affine_mod5_a1_b3_c4_strategy,
        structured_affine_mod5_a3_b1_c4_strategy,
        structured_affine_mod7_a1_b3_c6_strategy,
        structured_affine_mod7_a3_b1_c6_strategy,
        structured_affine_mod4_a3_b2_c3_strategy,
        structured_affine_mod4_a2_b3_c3_strategy,
        *structured_affine_low_order_tail_combo2_strategies,
        *structured_affine_mod11_top2_matchop_nohb_strategies,
        *structured_affine_mod11_combo9_matchop_nohb_strategies,
        *structured_affine_low_order_le9_combo19_strategies,
    ]
    if setcheck_bank_path is not None:
        bank_path = Path(setcheck_bank_path)
        is_default_bank = bank_path == DEFAULT_SETCHECK_BANK_PATH
        if bank_path.exists() and (not is_default_bank or is_default_equations):
            false_strategies.extend(
                build_setcheck_bank_strategies(
                    bank_path=bank_path,
                    equations_path=equations_path,
                    order4_max_id=order4_max_id,
                )
            )
    if predicatecheck_bank_path is not None:
        bank_path = Path(predicatecheck_bank_path)
        is_default_bank = bank_path == DEFAULT_PREDICATECHECK_BANK_PATH
        if bank_path.exists() and (not is_default_bank or is_default_equations):
            false_strategies.extend(
                build_predicatecheck_bank_strategies(
                    bank_path=bank_path,
                    equations_path=equations_path,
                    order4_max_id=order4_max_id,
                )
            )
    if paircheck_bank_path is not None:
        bank_path = Path(paircheck_bank_path)
        is_default_bank = bank_path == DEFAULT_PAIRCHECK_BANK_PATH
        if bank_path.exists() and (not is_default_bank or is_default_equations):
            false_strategies.append(
                build_paircheck_bank_strategy(
                    bank_path=bank_path,
                    law_count=len(left_projection_features),
                )
            )
    if not include_true_strategies:
        return Order5StrategyRegistry(
            law_count=len(left_projection_features),
            strategies=false_strategies,
        )
    _, singleton_sources, singleton_targets, singleton_counts = _singleton_collapse_sets(
        equations_path
    )
    singleton_order4_sources = frozenset(
        eq_id for eq_id in singleton_sources if eq_id <= order4_max_id
    )
    singleton_order4_targets = frozenset(
        eq_id for eq_id in singleton_targets if eq_id <= order4_max_id
    )
    singleton_strategy = CoverageStrategy(
        strategy_key=SINGLETON_COLLAPSE_ANY_TARGET_STRATEGY_KEY,
        strategy_version=1,
        verdict=True,
        priority=300,
        coverage_rule=SourceTargetSetsRule(
            source_ids=singleton_sources,
            target_ids=singleton_targets,
            excluded_blocks=((singleton_order4_sources, singleton_order4_targets),),
        ),
        certificate_family="singleton_collapse",
        summary_zh="singleton collapse 证明模板：source 强迫单元素，任意 target 成立。",
        summary_en=(
            "Singleton-collapse proof template: the source forces all elements "
            "equal, so any target equation holds."
        ),
        description_zh=(
            "当 source 形如 x = t 且 x 不出现在 t 中，或 t = x 且 x 不出现在 "
            "t 中时，两个 source 实例可推出 ∀ a b, a = b。随后任意 target "
            "方程的左右两边由 singleton 定理相等。因此任意匹配 source -> "
            "任意 target 蕴含为 true。"
        ),
        description_en=(
            "When the source has the form x = t with x absent from t, or t = x "
            "with x absent from t, two instances of the source imply "
            "∀ a b, a = b. The target equation then follows by applying this "
            "singleton theorem to its left and right sides. Therefore every "
            "matching source -> any target implication is true."
        ),
        certificate_mode="proof_template",
        verification_mode="templatecheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="singleton_collapse",
        evidence=_singleton_collapse_evidence(
            singleton_sources,
            singleton_targets,
            singleton_counts,
        ),
    )
    _, singleton_seedbank_sources, singleton_seedbank_targets, singleton_seedbank_mismatches = (
        _singleton_seedbank_sets(equations_path)
    )
    singleton_seedbank_order4_sources = frozenset(
        eq_id for eq_id in singleton_seedbank_sources if eq_id <= order4_max_id
    )
    singleton_seedbank_order4_targets = frozenset(
        eq_id for eq_id in singleton_seedbank_targets if eq_id <= order4_max_id
    )
    singleton_seedbank_strategy = CoverageStrategy(
        strategy_key=SINGLETON_SEEDBANK_ANY_TARGET_STRATEGY_KEY,
        strategy_version=1,
        verdict=True,
        priority=305,
        coverage_rule=SourceTargetSetsRule(
            source_ids=singleton_seedbank_sources,
            target_ids=singleton_seedbank_targets,
            excluded_blocks=(
                (singleton_seedbank_order4_sources, singleton_seedbank_order4_targets),
            ),
        ),
        certificate_family="singleton_seedbank",
        summary_zh=(
            "singleton seedbank 显式证明库：已验证 source 推出单元素，任意 target 成立。"
        ),
        summary_en=(
            "singleton seedbank explicit proofs: each verified source derives "
            "all elements equal, so any target equation holds."
        ),
        description_zh=(
            "使用 v12 MagmaEgg singleton proof body 和远程 judge accepted 的 "
            "source-level singleton proof bank 作为 anchor。每个 seed source "
            "已有显式 Lean proof body 推出 ∀ a b, a = b，"
            "随后任意 target 方程左右两边相等。为避免 ID 误用，registry 会同时"
            "校验 source 方程的 canonical signature。"
        ),
        description_en=(
            "Uses v12 MagmaEgg singleton proof bodies and remote-judge-accepted "
            "source-level singleton proof-bank bodies as anchors. Each seed "
            "source has an explicit Lean proof deriving ∀ a b, a = b; then any "
            "target equation follows. The registry also checks the source "
            "equation canonical signature to avoid ID-only misuse."
        ),
        certificate_mode="proof_bank",
        verification_mode="explicitbank",
        coverage_rule_kind="source_target_sets",
        certificate_generator="singleton_seedbank",
        evidence=_singleton_seedbank_evidence(
            singleton_seedbank_sources,
            singleton_seedbank_targets,
            singleton_seedbank_mismatches,
        ),
    )
    (
        _,
        singleton_specialization_sources,
        singleton_specialization_targets,
        singleton_specialization_match_counts,
    ) = _singleton_seedbank_specialization_sets(equations_path)
    singleton_specialization_order4_sources = frozenset(
        eq_id
        for eq_id in singleton_specialization_sources
        if eq_id <= order4_max_id
    )
    singleton_specialization_order4_targets = frozenset(
        eq_id
        for eq_id in singleton_specialization_targets
        if eq_id <= order4_max_id
    )
    singleton_specialization_strategy = CoverageStrategy(
        strategy_key=SINGLETON_SEEDBANK_SPECIALIZATION_ANY_TARGET_STRATEGY_KEY,
        strategy_version=1,
        verdict=True,
        priority=306,
        coverage_rule=SourceTargetSetsRule(
            source_ids=singleton_specialization_sources,
            target_ids=singleton_specialization_targets,
            excluded_blocks=(
                (
                    singleton_specialization_order4_sources,
                    singleton_specialization_order4_targets,
                ),
            ),
        ),
        certificate_family="singleton_seedbank_specialization",
        summary_zh=(
            "singleton seedbank specialization 证明模板：source 可专门化到已验证 "
            "singleton seed，任意 target 成立。"
        ),
        summary_en=(
            "Singleton seedbank specialization proof template: the source "
            "specializes to a verified singleton seed, so any target equation holds."
        ),
        description_zh=(
            "当 source 的一个实例与已验证 singleton seedbank 中的某个 seed "
            "方程一致时，先用 source 假设构造该 seed 方程，再复用 seed 的"
            "显式 Lean proof body 推出 ∀ x y, x = y，随后任意 target 方程"
            "左右两边相等。匹配允许 source 变量替换为 seed 变量构成的项，"
            "并保留方向或反向等式。"
        ),
        description_en=(
            "When an instance of the source equation matches one of the verified "
            "singleton seedbank equations, the certificate first "
            "constructs that seed equation from the source hypothesis, then "
            "reuses the seed's explicit Lean proof body to derive ∀ x y, x = y. "
            "The target equation follows by singleton equality. Matching allows "
            "source variables to be substituted by seed terms and handles both "
            "orientations."
        ),
        certificate_mode="proof_template",
        verification_mode="templatecheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="singleton_seedbank_specialization",
        evidence=_singleton_seedbank_specialization_evidence(
            singleton_specialization_sources,
            singleton_specialization_targets,
            singleton_specialization_match_counts,
            _available_singleton_seed_source_count(),
        ),
    )
    _, product_anchor_sources, product_anchor_targets, product_anchor_counts = (
        _product_anchor_sets(equations_path)
    )
    product_anchor_order4_sources = frozenset(
        eq_id for eq_id in product_anchor_sources if eq_id <= order4_max_id
    )
    product_anchor_order4_targets = frozenset(
        eq_id for eq_id in product_anchor_targets if eq_id <= order4_max_id
    )
    product_anchor_strategy = CoverageStrategy(
        strategy_key=PRODUCT_ANCHOR_ANY_PRODUCT_TARGET_STRATEGY_KEY,
        strategy_version=1,
        verdict=True,
        priority=310,
        coverage_rule=SourceTargetSetsRule(
            source_ids=product_anchor_sources,
            target_ids=product_anchor_targets,
            excluded_blocks=(
                (product_anchor_order4_sources, product_anchor_order4_targets),
            ),
        ),
        certificate_family="term_shape_anchor_product",
        summary_zh=(
            "product anchor 证明模板：source 强迫所有二元乘积相等，任意乘积根 target 成立。"
        ),
        summary_en=(
            "Product-anchor proof template: the source forces all binary "
            "products equal, so any product-root target equation holds."
        ),
        description_zh=(
            "当 source 的一边形如 x ◇ y，x 和 y 是不同变量，且这两个变量"
            "不出现在另一边 anchor term 中时，两个 source 实例可推出 "
            "∀ a b c d, a ◇ b = c ◇ d。随后任意左右两边根节点都是 ◇ 的 "
            "target 方程都成立。"
        ),
        description_en=(
            "When one side of the source has the form x ◇ y with distinct "
            "variables x and y, and neither variable appears in the other "
            "anchor term, two source instances imply ∀ a b c d, a ◇ b = c ◇ d. "
            "Any target equation whose left and right sides are both product-root "
            "terms then follows."
        ),
        certificate_mode="proof_template",
        verification_mode="templatecheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="product_anchor",
        evidence=_product_anchor_evidence(
            product_anchor_sources,
            product_anchor_targets,
            product_anchor_counts,
        ),
    )
    product_anchor_seed_lift_strategy = _build_product_anchor_seed_lift_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
    )
    product_collapse_strategies = tuple(
        _build_product_collapse_strategy(
            equations_path=equations_path,
            order4_max_id=order4_max_id,
            template=template,
        )
        for template in PRODUCT_COLLAPSE_TEMPLATES
    )
    (
        _,
        left_projection_normalizer_sources,
        left_projection_normalizer_targets,
        left_projection_normalizer_counts,
    ) = _projection_normalizer_sets(equations_path, side="left")
    left_projection_normalizer_order4_sources = frozenset(
        eq_id
        for eq_id in left_projection_normalizer_sources
        if eq_id <= order4_max_id
    )
    left_projection_normalizer_order4_targets = frozenset(
        eq_id
        for eq_id in left_projection_normalizer_targets
        if eq_id <= order4_max_id
    )
    left_projection_normalizer_strategy = CoverageStrategy(
        strategy_key=LEFT_PROJECTION_NORMALIZER_ANY_TARGET_STRATEGY_KEY,
        strategy_version=1,
        verdict=True,
        priority=315,
        coverage_rule=SourceTargetSetsRule(
            source_ids=left_projection_normalizer_sources,
            target_ids=left_projection_normalizer_targets,
            excluded_blocks=(
                (
                    left_projection_normalizer_order4_sources,
                    left_projection_normalizer_order4_targets,
                ),
            ),
        ),
        certificate_family="projection_normalizer_left",
        summary_zh=(
            "left projection normalizer 证明模板：source 给出左投影律，"
            "左右最左变量相同的 target 成立。"
        ),
        summary_en=(
            "Left-projection normalizer proof template: the source gives "
            "a ◇ b = a, so targets with the same leftmost variable hold."
        ),
        description_zh=(
            "当 source 形如 x = x ◇ y 或 x ◇ y = x，且 x/y 为不同变量时，"
            "可推出 ∀ a b, a ◇ b = a。随后每个 target term 都归约到其"
            "最左变量；若 target 左右两边最左变量相同，则蕴含为 true。"
        ),
        description_en=(
            "When the source has the form x = x ◇ y or x ◇ y = x with "
            "distinct variables, it derives ∀ a b, a ◇ b = a. Each target "
            "term then normalizes to its leftmost variable; targets whose "
            "two sides share that leftmost variable are true."
        ),
        certificate_mode="proof_template",
        verification_mode="templatecheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="left_projection_normalizer",
        evidence=_projection_normalizer_evidence(
            "left",
            left_projection_normalizer_sources,
            left_projection_normalizer_targets,
            left_projection_normalizer_counts,
        ),
    )
    (
        _,
        right_projection_normalizer_sources,
        right_projection_normalizer_targets,
        right_projection_normalizer_counts,
    ) = _projection_normalizer_sets(equations_path, side="right")
    right_projection_normalizer_order4_sources = frozenset(
        eq_id
        for eq_id in right_projection_normalizer_sources
        if eq_id <= order4_max_id
    )
    right_projection_normalizer_order4_targets = frozenset(
        eq_id
        for eq_id in right_projection_normalizer_targets
        if eq_id <= order4_max_id
    )
    right_projection_normalizer_strategy = CoverageStrategy(
        strategy_key=RIGHT_PROJECTION_NORMALIZER_ANY_TARGET_STRATEGY_KEY,
        strategy_version=1,
        verdict=True,
        priority=316,
        coverage_rule=SourceTargetSetsRule(
            source_ids=right_projection_normalizer_sources,
            target_ids=right_projection_normalizer_targets,
            excluded_blocks=(
                (
                    right_projection_normalizer_order4_sources,
                    right_projection_normalizer_order4_targets,
                ),
            ),
        ),
        certificate_family="projection_normalizer_right",
        summary_zh=(
            "right projection normalizer 证明模板：source 给出右投影律，"
            "左右最右变量相同的 target 成立。"
        ),
        summary_en=(
            "Right-projection normalizer proof template: the source gives "
            "a ◇ b = b, so targets with the same rightmost variable hold."
        ),
        description_zh=(
            "当 source 形如 x = y ◇ x 或 y ◇ x = x，且 x/y 为不同变量时，"
            "可推出 ∀ a b, a ◇ b = b。随后每个 target term 都归约到其"
            "最右变量；若 target 左右两边最右变量相同，则蕴含为 true。"
        ),
        description_en=(
            "When the source has the form x = y ◇ x or y ◇ x = x with "
            "distinct variables, it derives ∀ a b, a ◇ b = b. Each target "
            "term then normalizes to its rightmost variable; targets whose "
            "two sides share that rightmost variable are true."
        ),
        certificate_mode="proof_template",
        verification_mode="templatecheck",
        coverage_rule_kind="source_target_sets",
        certificate_generator="right_projection_normalizer",
        evidence=_projection_normalizer_evidence(
            "right",
            right_projection_normalizer_sources,
            right_projection_normalizer_targets,
            right_projection_normalizer_counts,
        ),
    )
    law_instance_strategies = tuple(
        _build_law_instance_strategy(
            equations_path=equations_path,
            order4_max_id=order4_max_id,
            template=template,
        )
        for template in LAW_INSTANCE_TEMPLATES
    )
    opnorm_hconst_match_collapse_strategies = (
        [
            _build_opnorm_hconst_match_collapse_strategy(
                equations_path=equations_path,
            )
        ]
        if is_default_equations
        and DEFAULT_OPNORM_HCONST_MATCH_COLLAPSE_PAIR_INDEX_CACHE.exists()
        else []
    )
    opnorm_hconst_sandwich_strategies = (
        [
            _build_opnorm_hconst_sandwich_strategy(
                equations_path=equations_path,
            )
        ]
        if is_default_equations
        and DEFAULT_OPNORM_HCONST_SANDWICH_PAIR_INDEX_CACHE.exists()
        else []
    )
    opnorm_hconst_lmrm_mainline_strategies = (
        [
            _build_opnorm_hconst_lmrm_mainline_strategy(
                equations_path=equations_path,
            )
        ]
        if is_default_equations
        and DEFAULT_OPNORM_HCONST_LMRM_MAINLINE_PAIR_INDEX_CACHE.exists()
        else []
    )
    opnorm_hconst_varmul_top01_strategies = (
        [
            _build_opnorm_hconst_varmul_top01_strategy(
                equations_path=equations_path,
            )
        ]
        if is_default_equations
        and DEFAULT_OPNORM_HCONST_VARMUL_TOP01_PAIR_INDEX_CACHE.exists()
        else []
    )
    opnorm_hconst_default_sandwich_top16_strategies = (
        [
            _build_opnorm_hconst_default_sandwich_top16_strategy(
                equations_path=equations_path,
            )
        ]
        if is_default_equations
        and DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_TOP16_PAIR_INDEX_CACHE.exists()
        else []
    )
    opnorm_hconst_default_sandwich_d14vc4_strategies = (
        [
            _build_opnorm_hconst_default_sandwich_d14vc4_strategy(
                equations_path=equations_path,
            )
        ]
        if is_default_equations
        and DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_D14VC4_PAIR_INDEX_CACHE.exists()
        else []
    )
    opnorm_hconst_default_sandwich_d13vc4_strategies = (
        [
            _build_opnorm_hconst_default_sandwich_d13vc4_strategy(
                equations_path=equations_path,
            )
        ]
        if is_default_equations
        and DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_D13VC4_PAIR_INDEX_CACHE.exists()
        else []
    )
    opnorm_hconst_default_sandwich_d14vc4_targetext_strategies = (
        [
            _build_opnorm_hconst_default_sandwich_d14vc4_targetext_strategy(
                equations_path=equations_path,
            )
        ]
        if is_default_equations
        and DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_D14VC4_TARGETEXT_PAIR_INDEX_CACHE.exists()
        else []
    )
    opnorm_hconst_default_sandwich_lowvc_extension_strategies = (
        [
            _build_opnorm_hconst_default_sandwich_lowvc_extension_strategy(
                equations_path=equations_path,
            )
        ]
        if is_default_equations
        and DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_LOWVC_EXTENSION_PAIR_INDEX_CACHE.exists()
        else []
    )
    opnorm_hconst_default_sandwich_topbucket_extension_strategies = (
        [
            _build_opnorm_hconst_default_sandwich_topbucket_extension_strategy(
                equations_path=equations_path,
            )
        ]
        if is_default_equations
        and DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_TOPBUCKET_EXTENSION_PAIR_INDEX_CACHE.exists()
        else []
    )
    opnorm_hconst_default_sandwich_frontier_extension_strategies = (
        [
            _build_opnorm_hconst_default_sandwich_frontier_extension_strategy(
                equations_path=equations_path,
            )
        ]
        if is_default_equations
        and DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_FRONTIER_EXTENSION_PAIR_INDEX_CACHE.exists()
        else []
    )
    opnorm_hconst_default_sandwich_edge_extension_strategies = (
        [
            _build_opnorm_hconst_default_sandwich_edge_extension_strategy(
                equations_path=equations_path,
            )
        ]
        if is_default_equations
        and DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_EDGE_EXTENSION_PAIR_INDEX_CACHE.exists()
        else []
    )
    opnorm_hconst_default_sandwich_postedge_top40_extension_strategies = (
        [
            _build_opnorm_hconst_default_sandwich_postedge_top40_extension_strategy(
                equations_path=equations_path,
            )
        ]
        if is_default_equations
        and DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE_TOP40_EXTENSION_PAIR_INDEX_CACHE.exists()
        else []
    )
    opnorm_hconst_default_sandwich_postedge2_top60_extension_strategies = (
        [
            _build_opnorm_hconst_default_sandwich_postedge2_top60_extension_strategy(
                equations_path=equations_path,
            )
        ]
        if is_default_equations
        and DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE2_TOP60_EXTENSION_PAIR_INDEX_CACHE.exists()
        else []
    )
    opnorm_hconst_default_sandwich_postedge3_top80_extension_strategies = (
        [
            _build_opnorm_hconst_default_sandwich_postedge3_top80_extension_strategy(
                equations_path=equations_path,
            )
        ]
        if is_default_equations
        and DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE3_TOP80_EXTENSION_PAIR_INDEX_CACHE.exists()
        else []
    )
    opnorm_hconst_default_sandwich_postedge4_top100_extension_strategies = (
        [
            _build_opnorm_hconst_default_sandwich_postedge4_top100_extension_strategy(
                equations_path=equations_path,
            )
        ]
        if is_default_equations
        and DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE4_TOP100_EXTENSION_PAIR_INDEX_CACHE.exists()
        else []
    )
    opnorm_hconst_default_sandwich_postedge5_top120_extension_strategies = (
        [
            _build_opnorm_hconst_default_sandwich_postedge5_top120_extension_strategy(
                equations_path=equations_path,
            )
        ]
        if is_default_equations
        and DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE5_TOP120_EXTENSION_PAIR_INDEX_CACHE.exists()
        else []
    )
    opnorm_hconst_default_sandwich_postedge6_samplehit_top20_tail_strategies = (
        [
            _build_opnorm_hconst_default_sandwich_postedge6_samplehit_top20_tail_strategy(
                equations_path=equations_path,
            )
        ]
        if is_default_equations
        and DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE6_SAMPLEHIT_TOP20_TAIL_PAIR_INDEX_CACHE.exists()
        else []
    )
    opnorm_hconst_default_sandwich_postedge7_samplehit_top20_tail_strategies = (
        [
            _build_opnorm_hconst_default_sandwich_postedge7_samplehit_top20_tail_strategy(
                equations_path=equations_path,
            )
        ]
        if is_default_equations
        and DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE7_SAMPLEHIT_TOP20_TAIL_PAIR_INDEX_CACHE.exists()
        else []
    )
    opnorm_hconst_default_sandwich_postedge8_d14vc5_frontier_multitarget20_strategies = (
        [
            _build_opnorm_hconst_default_sandwich_postedge8_d14vc5_frontier_multitarget20_strategy(
                equations_path=equations_path,
            )
        ]
        if is_default_equations
        and DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE8_D14VC5_FRONTIER_MULTITARGET20_PAIR_INDEX_CACHE.exists()
        else []
    )
    opnorm_hconst_default_sandwich_postedge8_exact_top10_combined_tail_strategies = (
        [
            _build_opnorm_hconst_default_sandwich_postedge8_exact_top10_combined_tail_strategy(
                equations_path=equations_path,
            )
        ]
        if is_default_equations
        and DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE8_EXACT_TOP10_COMBINED_TAIL_PAIR_INDEX_CACHE.exists()
        else []
    )
    opnorm_hconst_default_sandwich_round30_cumulative_hconst_family_strategies = (
        [
            _build_opnorm_hconst_default_sandwich_round30_cumulative_hconst_family_strategy(
                equations_path=equations_path,
            )
        ]
        if is_default_equations
        and DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_ROUND30_CUMULATIVE_HCONST_FAMILY_PAIR_INDEX_CACHE.exists()
        else []
    )
    opnorm_hconst_match_ge25k_tail_batch_strategies = (
        [
            _build_opnorm_hconst_match_ge25k_tail_batch_strategy(
                equations_path=equations_path,
            )
        ]
        if is_default_equations
        and DEFAULT_OPNORM_HCONST_MATCH_GE25K_TAIL_BATCH_PAIR_INDEX_CACHE.exists()
        else []
    )
    opnorm_hconst_match_ge10_tail_extension_strategies = (
        [
            _build_opnorm_hconst_match_ge10_tail_extension_strategy(
                equations_path=equations_path,
            )
        ]
        if is_default_equations
        and DEFAULT_OPNORM_HCONST_MATCH_GE10_TAIL_EXTENSION_PAIR_INDEX_CACHE.exists()
        else []
    )
    opnorm_hconst_default_sandwich_ge25_lt100_tail_batch_strategies = (
        [
            _build_opnorm_hconst_default_sandwich_ge25_lt100_tail_batch_strategy(
                equations_path=equations_path,
            )
        ]
        if is_default_equations
        and DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_GE25_LT100_TAIL_BATCH_PAIR_INDEX_CACHE.exists()
        else []
    )
    opnorm_hconst_default_sandwich_lt25_remaining_tail_batch_strategies = (
        [
            _build_opnorm_hconst_default_sandwich_lt25_remaining_tail_batch_strategy(
                equations_path=equations_path,
            )
        ]
        if is_default_equations
        and DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_LT25_REMAINING_TAIL_BATCH_PAIR_INDEX_CACHE.exists()
        else []
    )
    hinst_ground_cc_accepted_family_rollup_strategies = (
        [
            _build_hinst_ground_cc_accepted_family_rollup_strategy(
                equations_path=equations_path,
            )
        ]
        if is_default_equations
        and DEFAULT_HINST_GROUND_CC_ACCEPTED_FAMILY_ROLLUP_PAIR_INDEX_CACHE.exists()
        else []
    )
    opnorm_hconst_plus_hstep_d14vc4_v17_tail_strategies = (
        [
            _build_opnorm_hconst_plus_hstep_d14vc4_v17_tail_strategy(
                equations_path=equations_path,
            )
        ]
        if is_default_equations
        and DEFAULT_OPNORM_HCONST_PLUS_HSTEP_D14VC4_V17_TAIL_PAIR_INDEX_CACHE.exists()
        else []
    )
    one_sided_constancy_recursive_nf_strategies = (
        [
            _build_one_sided_constancy_row_recursive_nf_strategy(
                equations_path=equations_path,
            ),
            _build_one_sided_constancy_column_recursive_nf_strategy(
                equations_path=equations_path,
            ),
        ]
        if is_default_equations
        and DEFAULT_PROOFBENCH_ONE_SIDED_CONSTANCY_EXPLICIT_NF_ACCEPTED_CANDIDATE_JSONL.exists()
        else []
    )
    target_instance_of_source_strategy = _build_target_instance_of_source_strategy(
        equations_path=equations_path,
        order4_max_id=order4_max_id,
    )
    return Order5StrategyRegistry(
        law_count=len(left_projection_features),
        strategies=[
            *false_strategies,
            singleton_strategy,
            singleton_seedbank_strategy,
            singleton_specialization_strategy,
            product_anchor_strategy,
            *product_collapse_strategies,
            product_anchor_seed_lift_strategy,
            left_projection_normalizer_strategy,
            right_projection_normalizer_strategy,
            *opnorm_hconst_match_collapse_strategies,
            *opnorm_hconst_sandwich_strategies,
            *opnorm_hconst_lmrm_mainline_strategies,
            *opnorm_hconst_varmul_top01_strategies,
            *opnorm_hconst_default_sandwich_top16_strategies,
            *opnorm_hconst_default_sandwich_d14vc4_strategies,
            *opnorm_hconst_default_sandwich_d13vc4_strategies,
            *opnorm_hconst_default_sandwich_d14vc4_targetext_strategies,
            *opnorm_hconst_default_sandwich_lowvc_extension_strategies,
            *opnorm_hconst_default_sandwich_topbucket_extension_strategies,
            *opnorm_hconst_default_sandwich_frontier_extension_strategies,
            *opnorm_hconst_default_sandwich_edge_extension_strategies,
            *opnorm_hconst_default_sandwich_postedge_top40_extension_strategies,
            *opnorm_hconst_default_sandwich_postedge2_top60_extension_strategies,
            *opnorm_hconst_default_sandwich_postedge3_top80_extension_strategies,
            *opnorm_hconst_default_sandwich_postedge4_top100_extension_strategies,
            *opnorm_hconst_default_sandwich_postedge5_top120_extension_strategies,
            *opnorm_hconst_default_sandwich_postedge6_samplehit_top20_tail_strategies,
            *opnorm_hconst_default_sandwich_postedge7_samplehit_top20_tail_strategies,
            *opnorm_hconst_default_sandwich_postedge8_d14vc5_frontier_multitarget20_strategies,
            *opnorm_hconst_default_sandwich_postedge8_exact_top10_combined_tail_strategies,
            *opnorm_hconst_default_sandwich_round30_cumulative_hconst_family_strategies,
            *opnorm_hconst_match_ge25k_tail_batch_strategies,
            *opnorm_hconst_match_ge10_tail_extension_strategies,
            *opnorm_hconst_default_sandwich_ge25_lt100_tail_batch_strategies,
            *opnorm_hconst_default_sandwich_lt25_remaining_tail_batch_strategies,
            *hinst_ground_cc_accepted_family_rollup_strategies,
            *opnorm_hconst_plus_hstep_d14vc4_v17_tail_strategies,
            *one_sided_constancy_recursive_nf_strategies,
            target_instance_of_source_strategy,
            *law_instance_strategies,
        ],
    )


def find_true_strategy_ids_for_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path = DEFAULT_EQ_SIZE5_PATH,
    order4_max_id: int = DEFAULT_ORDER4_MAX_ID,
    include_seedbank: bool = True,
) -> list[str]:
    if eq1_id == eq2_id:
        return []
    strategy_ids: list[str] = []

    def add(strategy_key: str) -> None:
        strategy_ids.append(f"{strategy_key}.v1")

    equations_by_id = {
        feature.equation_id: equation
        for feature, equation in _cached_parsed_equation_features(equations_path)
    }
    source = equations_by_id.get(eq1_id)
    target = equations_by_id.get(eq2_id)
    if source is None or target is None:
        raise ValueError(f"unknown equation pair: {eq1_id}->{eq2_id}")

    if _singleton_collapse_shape(source) is not None:
        add(SINGLETON_COLLAPSE_ANY_TARGET_STRATEGY_KEY)
    if include_seedbank:
        seed_signatures = _verified_singleton_seed_source_signatures(equations_path)
        if eq1_id in seed_signatures:
            add(SINGLETON_SEEDBANK_ANY_TARGET_STRATEGY_KEY)
        if _match_singleton_seedbank_specialization(source, equations_path) is not None:
            add(SINGLETON_SEEDBANK_SPECIALIZATION_ANY_TARGET_STRATEGY_KEY)
    if _product_anchor_shape(source) is not None and _is_product_root_target(target):
        add(PRODUCT_ANCHOR_ANY_PRODUCT_TARGET_STRATEGY_KEY)
    if (
        include_seedbank
        and eq1_id in _product_anchor_seed_lift_source_signatures(equations_path)
        and _is_product_root_target(target)
    ):
        add(PRODUCT_ANCHOR_SEED_LIFT_ANY_PRODUCT_TARGET_STRATEGY_KEY)
    for template in PRODUCT_COLLAPSE_TEMPLATES:
        term_pattern = str(template["term_pattern"])
        pattern = _parse_product_collapse_pattern(term_pattern)
        if _product_collapse_source_shape(source, pattern) is None:
            continue
        if not _product_collapse_target_matches(target, pattern):
            continue
        add(f"{PRODUCT_COLLAPSE_STRATEGY_KEY_PREFIX}.{template['name']}")
    if _projection_normalizer_source_shape(source, side="left") is not None and (
        _is_projection_normal_target(target, side="left")
    ):
        add(LEFT_PROJECTION_NORMALIZER_ANY_TARGET_STRATEGY_KEY)
    if _projection_normalizer_source_shape(source, side="right") is not None and (
        _is_projection_normal_target(target, side="right")
    ):
        add(RIGHT_PROJECTION_NORMALIZER_ANY_TARGET_STRATEGY_KEY)
    if _opnorm_hconst_match_collapse_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
    ):
        add(OPNORM_HCONST_MATCH_COLLAPSE_STRATEGY_KEY)
    if _opnorm_hconst_sandwich_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
    ):
        add(OPNORM_HCONST_SANDWICH_STRATEGY_KEY)
    if _opnorm_hconst_lmrm_mainline_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
    ):
        add(OPNORM_HCONST_LMRM_MAINLINE_STRATEGY_KEY)
    if _opnorm_hconst_varmul_top01_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
    ):
        add(OPNORM_HCONST_VARMUL_TOP01_STRATEGY_KEY)
    if _opnorm_hconst_default_sandwich_top16_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
    ):
        add(OPNORM_HCONST_DEFAULT_SANDWICH_TOP16_STRATEGY_KEY)
    if _opnorm_hconst_default_sandwich_d14vc4_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
    ):
        add(OPNORM_HCONST_DEFAULT_SANDWICH_D14VC4_STRATEGY_KEY)
    if _opnorm_hconst_default_sandwich_d13vc4_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
    ):
        add(OPNORM_HCONST_DEFAULT_SANDWICH_D13VC4_STRATEGY_KEY)
    if _opnorm_hconst_default_sandwich_d14vc4_targetext_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
    ):
        add(OPNORM_HCONST_DEFAULT_SANDWICH_D14VC4_TARGETEXT_STRATEGY_KEY)
    if _opnorm_hconst_default_sandwich_lowvc_extension_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
    ):
        add(OPNORM_HCONST_DEFAULT_SANDWICH_LOWVC_EXTENSION_STRATEGY_KEY)
    if _opnorm_hconst_default_sandwich_topbucket_extension_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
    ):
        add(OPNORM_HCONST_DEFAULT_SANDWICH_TOPBUCKET_EXTENSION_STRATEGY_KEY)
    if _opnorm_hconst_default_sandwich_frontier_extension_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
    ):
        add(OPNORM_HCONST_DEFAULT_SANDWICH_FRONTIER_EXTENSION_STRATEGY_KEY)
    if _opnorm_hconst_default_sandwich_edge_extension_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
    ):
        add(OPNORM_HCONST_DEFAULT_SANDWICH_EDGE_EXTENSION_STRATEGY_KEY)
    if _opnorm_hconst_default_sandwich_postedge_top40_extension_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
    ):
        add(OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE_TOP40_EXTENSION_STRATEGY_KEY)
    if _opnorm_hconst_default_sandwich_postedge2_top60_extension_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
    ):
        add(OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE2_TOP60_EXTENSION_STRATEGY_KEY)
    if _opnorm_hconst_default_sandwich_postedge3_top80_extension_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
    ):
        add(OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE3_TOP80_EXTENSION_STRATEGY_KEY)
    if _opnorm_hconst_default_sandwich_postedge4_top100_extension_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
    ):
        add(OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE4_TOP100_EXTENSION_STRATEGY_KEY)
    if _opnorm_hconst_default_sandwich_postedge5_top120_extension_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
    ):
        add(OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE5_TOP120_EXTENSION_STRATEGY_KEY)
    if _opnorm_hconst_default_sandwich_postedge6_samplehit_top20_tail_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
    ):
        add(OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE6_SAMPLEHIT_TOP20_TAIL_STRATEGY_KEY)
    if _opnorm_hconst_default_sandwich_postedge7_samplehit_top20_tail_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
    ):
        add(OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE7_SAMPLEHIT_TOP20_TAIL_STRATEGY_KEY)
    if _opnorm_hconst_default_sandwich_postedge8_d14vc5_frontier_multitarget20_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
    ):
        add(
            OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE8_D14VC5_FRONTIER_MULTITARGET20_STRATEGY_KEY
        )
    if _opnorm_hconst_default_sandwich_postedge8_exact_top10_combined_tail_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
    ):
        add(
            OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE8_EXACT_TOP10_COMBINED_TAIL_STRATEGY_KEY
        )
    if _opnorm_hconst_default_sandwich_round30_cumulative_hconst_family_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
    ):
        add(
            OPNORM_HCONST_DEFAULT_SANDWICH_ROUND30_CUMULATIVE_HCONST_FAMILY_STRATEGY_KEY
        )
    if _opnorm_hconst_match_ge25k_tail_batch_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
    ):
        add(OPNORM_HCONST_MATCH_GE25K_TAIL_BATCH_STRATEGY_KEY)
    if _opnorm_hconst_match_ge10_tail_extension_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
    ):
        add(OPNORM_HCONST_MATCH_GE10_TAIL_EXTENSION_STRATEGY_KEY)
    if _opnorm_hconst_default_sandwich_ge25_lt100_tail_batch_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
    ):
        add(OPNORM_HCONST_DEFAULT_SANDWICH_GE25_LT100_TAIL_BATCH_STRATEGY_KEY)
    if _opnorm_hconst_default_sandwich_lt25_remaining_tail_batch_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
    ):
        add(OPNORM_HCONST_DEFAULT_SANDWICH_LT25_REMAINING_TAIL_BATCH_STRATEGY_KEY)
    if _hinst_ground_cc_accepted_family_rollup_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
    ):
        add(HINST_GROUND_CC_ACCEPTED_FAMILY_ROLLUP_STRATEGY_KEY)
    if _opnorm_hconst_plus_hstep_d14vc4_v17_tail_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
    ):
        add(OPNORM_HCONST_PLUS_HSTEP_D14VC4_V17_TAIL_STRATEGY_KEY)
    if _one_sided_constancy_row_recursive_nf_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
    ):
        add(ONE_SIDED_CONSTANCY_ROW_RECURSIVE_NF_STRATEGY_KEY)
    if _one_sided_constancy_column_recursive_nf_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
    ):
        add(ONE_SIDED_CONSTANCY_COLUMN_RECURSIVE_NF_STRATEGY_KEY)
    if _match_target_instance_of_source(source, target) is not None:
        add(TARGET_INSTANCE_OF_SOURCE_STRATEGY_KEY)
    for template in LAW_INSTANCE_TEMPLATES:
        law = template["law"]
        if _match_law_instance_source(source, law) is None:
            continue
        if _match_law_instance_target(law, target) is None:
            continue
        add(str(template["strategy_key"]))

    return strategy_ids


def verify_finmodel_setcheck(
    equations_path: Path = DEFAULT_EQ_SIZE5_PATH,
    table: tuple[tuple[int, ...], ...] = LEFT_PROJECTION_2_TABLE,
) -> dict:
    _, source_ids, target_ids = _finmodel_sets(equations_path, table)
    return _finmodel_setcheck_evidence(table, source_ids, target_ids)


def singleton_collapse_true_judge_answer(
    source_equation: str,
    target_equation: str,
) -> dict:
    return {
        "verdict": "true",
        "code": singleton_collapse_true_judge_code(source_equation, target_equation),
    }


def singleton_collapse_true_judge_code(
    source_equation: str,
    target_equation: str,
) -> str:
    source = _parse_stage2_equation(source_equation)
    target = _parse_stage2_equation(target_equation)
    shape = _singleton_collapse_shape(source)
    if shape is None:
        raise ValueError("source equation is not a singleton-collapse template")

    side, variable = shape
    h_a = f"h {_singleton_h_args(source, variable, 'a', 'a')}"
    h_b = f"h {_singleton_h_args(source, variable, 'b', 'a')}"
    if side == "left":
        singleton_proof = f"({h_a}).trans ({h_b}).symm"
    else:
        singleton_proof = f"({h_a}).symm.trans ({h_b})"
    target_variables = target.variables()
    target_intro = f"  intro {' '.join(target_variables)}\n" if target_variables else ""
    return (
        "import JudgeProblem\n\n"
        "def submission : Goal := by\n"
        "  intro G _ h\n"
        "  have singleton : ∀ (a b : G), a = b := by\n"
        "    intro a b\n"
        f"    exact {singleton_proof}\n"
        f"{target_intro}"
        f"  exact singleton ({lean_expr(target.left, top=True)}) "
        f"({lean_expr(target.right, top=True)})\n"
    )


def singleton_seedbank_true_judge_answer(
    source_equation_id: int,
    target_equation: str,
    *,
    proof_source_path: Path = DEFAULT_SINGLETON_SEEDBANK_PROOF_SOURCE,
    proof_bank_path: Path = DEFAULT_SINGLETON_SEEDBANK_PROOF_BANK,
) -> dict:
    return {
        "verdict": "true",
        "code": singleton_seedbank_true_judge_code(
            source_equation_id,
            target_equation,
            proof_source_path=proof_source_path,
            proof_bank_path=proof_bank_path,
        ),
    }


def singleton_seedbank_true_judge_code(
    source_equation_id: int,
    target_equation: str,
    *,
    proof_source_path: Path = DEFAULT_SINGLETON_SEEDBANK_PROOF_SOURCE,
    proof_bank_path: Path = DEFAULT_SINGLETON_SEEDBANK_PROOF_BANK,
) -> str:
    proof_bodies = _load_magmaegg_singleton_proof_bodies(proof_source_path)
    proof_body = proof_bodies.get(source_equation_id)
    harvested_proofs = _load_harvested_singleton_seed_proofs(proof_bank_path)
    harvested_proof = harvested_proofs.get(source_equation_id)
    if proof_body is None:
        if harvested_proof is not None:
            return _source_level_singleton_proof_judge_code(
                harvested_proof[1],
                target_equation,
            )
        raise ValueError(
            f"unknown singleton seedbank source equation id: {source_equation_id}"
        )

    target = _parse_stage2_equation(target_equation)
    target_variables = target.variables()
    target_intro = f"  intro {' '.join(target_variables)}\n" if target_variables else ""
    proof_body = re.sub(r"\bR\b", "Eq.refl", proof_body)
    indented_body = "\n".join(
        "    " + line if line.strip() else ""
        for line in proof_body.strip().splitlines()
    )
    return (
        "import JudgeProblem\n\n"
        "def submission : Goal := by\n"
        "  intro G _ h\n"
        "  have C : ∀ {a b c d : G}, a = b → c = d → a ◇ c = b ◇ d := by\n"
        "    intro a b c d h1 h2\n"
        "    rw [h1, h2]\n"
        "  let T := @Eq.trans\n"
        "  let S := @Eq.symm\n"
        "  let M := @Magma.op\n"
        "  have singleton : ∀ (x y : G), x = y := by\n"
        "    intro x y\n"
        f"{indented_body}\n"
        f"{target_intro}"
        f"  exact singleton ({lean_expr(target.left, top=True)}) "
        f"({lean_expr(target.right, top=True)})\n"
    )


def _source_level_singleton_proof_judge_code(
    source_level_proof_body: str,
    target_equation: str,
) -> str:
    target = _parse_stage2_equation(target_equation)
    singleton_prefix = _singleton_prefix_from_source_level_proof_body(
        source_level_proof_body,
        allow_bare=True,
    )
    target_variables = target.variables()
    target_intro = f"  intro {' '.join(target_variables)}\n" if target_variables else ""
    indented_prefix = "\n".join(
        "  " + line if line.strip() else ""
        for line in singleton_prefix.strip().splitlines()
    )
    return (
        "import JudgeProblem\n\n"
        "def submission : Goal := by\n"
        "  intro G _ h\n"
        f"{indented_prefix}\n"
        f"{target_intro}"
        f"  exact singleton ({lean_expr(target.left, top=True)}) "
        f"({lean_expr(target.right, top=True)})\n"
    )


def _singleton_prefix_from_source_level_proof_body(
    proof_body: str,
    *,
    allow_bare: bool = False,
) -> str:
    original_lines = proof_body.strip().splitlines()
    lines = list(original_lines)
    while lines and lines[0].strip().startswith("intro "):
        lines = lines[1:]
    singleton_index = None
    for index, line in enumerate(lines):
        if line.startswith("have singleton"):
            singleton_index = index
            break
    if singleton_index is None:
        if allow_bare and original_lines:
            indented_body = "\n".join(
                f"  {line}" if line.strip() else ""
                for line in original_lines
            )
            return (
                "have singleton : ∀ (x y : G), x = y := by\n"
                f"{indented_body}"
            )
        raise ValueError("source-level proof body does not define singleton")

    end_index = len(lines)
    for index in range(singleton_index + 1, len(lines)):
        stripped = lines[index].strip()
        if lines[index].startswith((" ", "\t")):
            continue
        if stripped.startswith("intro ") or stripped.startswith("exact singleton"):
            end_index = index
            break
    return "\n".join(lines[:end_index]).rstrip()


def singleton_seedbank_specialization_true_judge_answer(
    source_equation: str,
    target_equation: str,
    *,
    equations_path: Path = DEFAULT_EQ_SIZE5_PATH,
    proof_source_path: Path = DEFAULT_SINGLETON_SEEDBANK_PROOF_SOURCE,
    proof_bank_path: Path = DEFAULT_SINGLETON_SEEDBANK_PROOF_BANK,
) -> dict:
    return {
        "verdict": "true",
        "code": singleton_seedbank_specialization_true_judge_code(
            source_equation,
            target_equation,
            equations_path=equations_path,
            proof_source_path=proof_source_path,
            proof_bank_path=proof_bank_path,
        ),
    }


def singleton_seedbank_specialization_true_judge_code(
    source_equation: str,
    target_equation: str,
    *,
    equations_path: Path = DEFAULT_EQ_SIZE5_PATH,
    proof_source_path: Path = DEFAULT_SINGLETON_SEEDBANK_PROOF_SOURCE,
    proof_bank_path: Path = DEFAULT_SINGLETON_SEEDBANK_PROOF_BANK,
) -> str:
    source = _parse_stage2_equation(source_equation)
    target = _parse_stage2_equation(target_equation)
    match = _match_singleton_seedbank_specialization(source, equations_path)
    if match is None:
        raise ValueError(
            "source equation is not a singleton seedbank specialization template"
        )

    seed_id, seed_equation, orientation, substitutions = match
    proof_bodies = _load_magmaegg_singleton_proof_bodies(proof_source_path)
    proof_body = proof_bodies.get(seed_id)
    harvested_proof_body = None
    if proof_body is None:
        harvested_proof = _load_harvested_singleton_seed_proofs(proof_bank_path).get(
            seed_id
        )
        if harvested_proof is None:
            raise ValueError(f"missing singleton seedbank proof body: {seed_id}")
        harvested_proof_body = harvested_proof[1]

    seed_variables = seed_equation.variables()
    seed_intro = f"    intro {' '.join(seed_variables)}\n" if seed_variables else ""
    source_args = " ".join(
        lean_expr(substitutions[variable], top=False)
        for variable in source.variables()
    )
    seed_exact = f"h0 {source_args}" if source_args else "h0"
    if orientation == "symm":
        seed_exact = f"({seed_exact}).symm"

    target_variables = target.variables()
    target_intro = f"  intro {' '.join(target_variables)}\n" if target_variables else ""
    if harvested_proof_body is not None:
        singleton_prefix = _singleton_prefix_from_source_level_proof_body(
            harvested_proof_body,
            allow_bare=True,
        )
        indented_prefix = "\n".join(
            "  " + line if line.strip() else ""
            for line in singleton_prefix.strip().splitlines()
        )
        return (
            "import JudgeProblem\n\n"
            "def submission : Goal := by\n"
            "  intro G _ h0\n"
            "  have h : "
            f"∀ ({' '.join(seed_variables)} : G), "
            f"{lean_expr(seed_equation.left, top=True)} = "
            f"{lean_expr(seed_equation.right, top=True)} := by\n"
            f"{seed_intro}"
            f"    exact {seed_exact}\n"
            f"{indented_prefix}\n"
            f"{target_intro}"
            f"  exact singleton ({lean_expr(target.left, top=True)}) "
            f"({lean_expr(target.right, top=True)})\n"
        )
    proof_body = re.sub(r"\bR\b", "Eq.refl", proof_body)
    indented_body = "\n".join(
        "    " + line if line.strip() else ""
        for line in proof_body.strip().splitlines()
    )
    return (
        "import JudgeProblem\n\n"
        "def submission : Goal := by\n"
        "  intro G _ h0\n"
        "  have h : "
        f"∀ ({' '.join(seed_variables)} : G), "
        f"{lean_expr(seed_equation.left, top=True)} = "
        f"{lean_expr(seed_equation.right, top=True)} := by\n"
        f"{seed_intro}"
        f"    exact {seed_exact}\n"
        "  have C : ∀ {a b c d : G}, a = b → c = d → a ◇ c = b ◇ d := by\n"
        "    intro a b c d h1 h2\n"
        "    rw [h1, h2]\n"
        "  let T := @Eq.trans\n"
        "  let S := @Eq.symm\n"
        "  let M := @Magma.op\n"
        "  have singleton : ∀ (x y : G), x = y := by\n"
        "    intro x y\n"
        f"{indented_body}\n"
        f"{target_intro}"
        f"  exact singleton ({lean_expr(target.left, top=True)}) "
        f"({lean_expr(target.right, top=True)})\n"
    )


def singleton_superpose_true_judge_answer(
    source_equation: str,
    target_equation: str,
) -> dict:
    return {
        "verdict": "true",
        "code": singleton_superpose_true_judge_code(source_equation, target_equation),
    }


def singleton_superpose_true_judge_code(
    source_equation: str,
    target_equation: str,
) -> str:
    source = _parse_stage2_equation(source_equation)
    target = _parse_stage2_equation(target_equation)
    eq1087_match = _match_eq1087_singleton_shape(source)
    if eq1087_match is not None:
        return _eq1087_singleton_judge_code(source, target, eq1087_match)
    collapse_match = _match_superpose_collapse_shape(source)
    if collapse_match is not None:
        return _superpose_collapse_singleton_judge_code(source, target, collapse_match)
    raise ValueError("source equation is not a singleton-superpose template")


def _eq1087_singleton_judge_code(
    source: Equation,
    target: Equation,
    match: dict[str, str],
) -> str:
    def h_call(base: str, left: str, tail: str) -> str:
        role_values = {
            "base": base,
            "left": left,
            "tail": tail,
        }
        return "h " + " ".join(role_values[match[variable]] for variable in source.variables())

    target_variables = target.variables()
    target_intro = f"  intro {' '.join(target_variables)}\n" if target_variables else ""
    h_expand = h_call("X2", "(X0 ◇ (X1 ◇ X1))", "X2")
    h_collapse = h_call(
        "X0",
        "X1",
        "((X2 ◇ ((X0 ◇ (X1 ◇ X1)) ◇ (X0 ◇ (X1 ◇ X1)))) ◇ X2)",
    )
    return (
        "import JudgeProblem\n\n"
        "def submission : Goal := by\n"
        "  intro G _ h\n"
        "  have eq12 : ∀ (X0 X1 X2 : G), X1 ◇ X2 = X0 := by\n"
        "    intro X0 X1 X2\n"
        "    calc\n"
        "      X1 ◇ X2 = X1 ◇ ((X0 ◇ (X1 ◇ X1)) ◇ "
        "((X2 ◇ ((X0 ◇ (X1 ◇ X1)) ◇ (X0 ◇ (X1 ◇ X1)))) ◇ X2)) := "
        f"congrArg (fun t => X1 ◇ t) ({h_expand})\n"
        f"      _ = X0 := ({h_collapse}).symm\n"
        "  have singleton : ∀ (a b : G), a = b := by\n"
        "    intro a b\n"
        "    exact (eq12 a b b).symm.trans (eq12 b b b)\n"
        f"{target_intro}"
        f"  exact singleton ({lean_expr(target.left, top=True)}) "
        f"({lean_expr(target.right, top=True)})\n"
    )


def _superpose_collapse_singleton_judge_code(
    source: Equation,
    target: Equation,
    match: dict[str, object],
) -> str:
    role_by_variable = match["role_by_variable"]
    uses_symm = bool(match["uses_symm"])

    def h_inst(base: str, prefix: str, left: str, tail: str) -> str:
        role_values = {
            "base": base,
            "prefix": prefix,
            "left": left,
            "tail": tail,
        }
        args = " ".join(
            role_values[role_by_variable[variable]]
            for variable in source.variables()
        )
        call = f"h {args}"
        return f"({call}).symm" if uses_symm else call

    target_variables = target.variables()
    target_intro = f"  intro {' '.join(target_variables)}\n" if target_variables else ""
    return (
        "import JudgeProblem\n\n"
        "def submission : Goal := by\n"
        "  intro G _ h\n"
        f"{target_intro}"
        "  have e9 (a b c d : G) : b ◇ (a ◇ ((c ◇ a) ◇ d)) = a := by\n"
        f"    exact {h_inst('a', 'b', 'c', 'd')}\n"
        "  have e12 (a b c : G) : c ◇ (a ◇ b) = a := by\n"
        "    let d : G := b ◇ ((b ◇ b) ◇ b)\n"
        "    have q : (b ◇ a) ◇ d = b := e9 b (b ◇ a) b b\n"
        "    have p : c ◇ (a ◇ ((b ◇ a) ◇ d)) = a := e9 a c b d\n"
        "    exact (congrArg (fun u => c ◇ (a ◇ u)) q).symm.trans p\n"
        "  have e15 (a b c : G) : a ◇ (b ◇ c) = c := by\n"
        "    let d : G := c\n"
        "    have q : c ◇ ((b ◇ c) ◇ d) = b ◇ c := e12 (b ◇ c) d c\n"
        "    have p : a ◇ (c ◇ ((b ◇ c) ◇ d)) = c := e9 c a b d\n"
        "    exact (congrArg (fun u => a ◇ u) q).symm.trans p\n"
        "  have e20 (a b : G) : a = b := by\n"
        "    have p : a ◇ (a ◇ b) = b := e15 a a b\n"
        "    have q : a ◇ (a ◇ b) = a := e12 a b a\n"
        "    exact q.symm.trans p\n"
        f"  exact e20 ({lean_expr(target.left, top=True)}) "
        f"({lean_expr(target.right, top=True)})\n"
    )


def product_anchor_true_judge_answer(
    source_equation: str,
    target_equation: str,
) -> dict:
    return {
        "verdict": "true",
        "code": product_anchor_true_judge_code(source_equation, target_equation),
    }


def product_anchor_true_judge_code(
    source_equation: str,
    target_equation: str,
) -> str:
    source = _parse_stage2_equation(source_equation)
    target = _parse_stage2_equation(target_equation)
    shape = _product_anchor_shape(source)
    if shape is None:
        raise ValueError("source equation is not a product-anchor template")
    if not _is_product_root_target(target):
        raise ValueError("target equation is not a product-root equation")

    side, first_variable, second_variable = shape
    h_pq = f"h {_product_anchor_h_args(source, first_variable, second_variable, 'p', 'q')}"
    h_rs = f"h {_product_anchor_h_args(source, first_variable, second_variable, 'r', 's')}"
    if side == "left":
        allprod_proof = f"({h_pq}).trans ({h_rs}).symm"
    else:
        allprod_proof = f"({h_pq}).symm.trans ({h_rs})"
    target_variables = target.variables()
    target_intro = f"  intro {' '.join(target_variables)}\n" if target_variables else ""
    assert target.left.left is not None
    assert target.left.right is not None
    assert target.right.left is not None
    assert target.right.right is not None
    return (
        "import JudgeProblem\n\n"
        "def submission : Goal := by\n"
        "  intro G _ h\n"
        "  have allprod : ∀ (p q r s : G), p ◇ q = r ◇ s := by\n"
        "    intro p q r s\n"
        f"    exact {allprod_proof}\n"
        f"{target_intro}"
        f"  exact allprod ({lean_expr(target.left.left, top=True)}) "
        f"({lean_expr(target.left.right, top=True)}) "
        f"({lean_expr(target.right.left, top=True)}) "
        f"({lean_expr(target.right.right, top=True)})\n"
    )


def product_anchor_seed_lift_true_judge_answer(
    source_equation_id: int,
    target_equation: str,
    *,
    candidate_jsonl_path: Path = DEFAULT_PRODUCT_ANCHOR_SEED_LIFT_CANDIDATE_JSONL,
) -> dict:
    return {
        "verdict": "true",
        "code": product_anchor_seed_lift_true_judge_code(
            source_equation_id,
            target_equation,
            candidate_jsonl_path=candidate_jsonl_path,
        ),
    }


def product_anchor_seed_lift_true_judge_code(
    source_equation_id: int,
    target_equation: str,
    *,
    candidate_jsonl_path: Path = DEFAULT_PRODUCT_ANCHOR_SEED_LIFT_CANDIDATE_JSONL,
) -> str:
    proof = _load_product_anchor_seed_lift_proofs(candidate_jsonl_path).get(
        source_equation_id
    )
    if proof is None:
        raise ValueError(
            "unknown product-anchor seed-lift source equation id: "
            f"{source_equation_id}"
        )
    proof_body_path = Path(str(proof["proof_body_path"]))
    proof_body = proof_body_path.read_text(encoding="utf-8")
    from math_distill_stage2.order5_product_anchor_seed_lift import (
        render_product_anchor_seed_lift_certificate,
    )

    return render_product_anchor_seed_lift_certificate(
        seed_equation=str(proof["seed_product_anchor_equation"]),
        target_equation=target_equation,
        source_to_seed_proof_body=proof_body,
    )


def product_collapse_true_judge_answer(
    source_equation: str,
    target_equation: str,
    *,
    term_pattern: str | None = None,
) -> dict:
    return {
        "verdict": "true",
        "code": product_collapse_true_judge_code(
            source_equation,
            target_equation,
            term_pattern=term_pattern,
        ),
    }


def product_collapse_true_judge_code(
    source_equation: str,
    target_equation: str,
    *,
    term_pattern: str | None = None,
) -> str:
    source = _parse_stage2_equation(source_equation)
    target = _parse_stage2_equation(target_equation)
    matched = _product_collapse_template_match(
        source,
        target,
        term_pattern=term_pattern,
    )
    if matched is None:
        raise ValueError("source/target is not a product-collapse template match")
    pattern, source_shape, left_env, right_env = matched
    target_variables = target.variables()
    if not target_variables:
        raise ValueError("target equation has no variable for product-collapse anchor")
    anchor_seed = Expr.var(target_variables[0])
    left_h = _product_collapse_h_call(source, source_shape, left_env, anchor_seed)
    right_h = _product_collapse_h_call(source, source_shape, right_env, anchor_seed)
    if source_shape["side"] == "left":
        proof = f"({left_h}).trans ({right_h}).symm"
    elif source_shape["side"] == "right":
        proof = f"({left_h}).symm.trans ({right_h})"
    else:
        raise ValueError(f"unknown product-collapse source side: {source_shape['side']}")
    target_intro = f"  intro {' '.join(target_variables)}\n" if target_variables else ""
    return (
        "import JudgeProblem\n\n"
        "def submission : Goal := by\n"
        "  intro G _ h\n"
        f"{target_intro}"
        f"  exact {proof}\n"
    )


def opnorm_hconst_match_collapse_true_judge_answer(
    source_equation: str,
    target_equation: str,
) -> dict:
    return {
        "verdict": "true",
        "code": opnorm_hconst_match_collapse_true_judge_code(
            source_equation,
            target_equation,
        ),
    }


def opnorm_hconst_match_collapse_true_judge_code(
    source_equation: str,
    target_equation: str,
) -> str:
    code = render_first_hconst_match_collapse_certificate(
        source_equation,
        target_equation,
    )
    if code is None:
        raise ValueError("source/target is not an opnorm hconst match-collapse match")
    return code


def opnorm_hconst_sandwich_true_judge_answer(
    source_equation: str,
    target_equation: str,
) -> dict:
    return {
        "verdict": "true",
        "code": opnorm_hconst_sandwich_true_judge_code(
            source_equation,
            target_equation,
        ),
    }


def opnorm_hconst_sandwich_true_judge_code(
    source_equation: str,
    target_equation: str,
) -> str:
    code = render_first_hconst_sandwich_match_collapse_certificate(
        source_equation,
        target_equation,
    )
    if code is None:
        raise ValueError(
            "source/target is not an opnorm hconst sandwich match-collapse match"
        )
    return code


def opnorm_hconst_default_sandwich_true_judge_answer(
    source_equation: str,
    target_equation: str,
) -> dict:
    return {
        "verdict": "true",
        "code": opnorm_hconst_default_sandwich_true_judge_code(
            source_equation,
            target_equation,
        ),
    }


def opnorm_hconst_default_sandwich_true_judge_code(
    source_equation: str,
    target_equation: str,
) -> str:
    code = render_first_hconst_default_sandwich_match_collapse_certificate(
        source_equation,
        target_equation,
    )
    if code is None:
        raise ValueError(
            "source/target is not an opnorm hconst default-sandwich match-collapse match"
        )
    return code


def opnorm_hconst_plus_hstep_true_judge_answer(
    source_equation: str,
    target_equation: str,
) -> dict:
    return {
        "verdict": "true",
        "code": opnorm_hconst_plus_hstep_true_judge_code(
            source_equation,
            target_equation,
        ),
    }


def opnorm_hconst_plus_hstep_true_judge_code(
    source_equation: str,
    target_equation: str,
) -> str:
    renderers = (
        render_first_hconst_match_collapse_certificate,
        render_first_hconst_default_sandwich_match_collapse_certificate,
        render_first_hstep_default_sandwich_match_collapse_certificate,
    )
    for renderer in renderers:
        code = renderer(source_equation, target_equation)
        if code is not None:
            return code
    raise ValueError(
        "source/target is not an opnorm hconst-plus-hstep match-collapse match"
    )


def left_projection_normalizer_true_judge_answer(
    source_equation: str,
    target_equation: str,
) -> dict:
    return {
        "verdict": "true",
        "code": left_projection_normalizer_true_judge_code(
            source_equation,
            target_equation,
        ),
    }


def left_projection_normalizer_true_judge_code(
    source_equation: str,
    target_equation: str,
) -> str:
    return _projection_normalizer_true_judge_code(
        source_equation,
        target_equation,
        side="left",
    )


def right_projection_normalizer_true_judge_answer(
    source_equation: str,
    target_equation: str,
) -> dict:
    return {
        "verdict": "true",
        "code": right_projection_normalizer_true_judge_code(
            source_equation,
            target_equation,
        ),
    }


def right_projection_normalizer_true_judge_code(
    source_equation: str,
    target_equation: str,
) -> str:
    return _projection_normalizer_true_judge_code(
        source_equation,
        target_equation,
        side="right",
    )


def left_self_absorption_instance_true_judge_answer(
    source_equation: str,
    target_equation: str,
) -> dict:
    return {
        "verdict": "true",
        "code": left_self_absorption_instance_true_judge_code(
            source_equation,
            target_equation,
        ),
    }


def left_self_absorption_instance_true_judge_code(
    source_equation: str,
    target_equation: str,
) -> str:
    return _law_instance_true_judge_code(
        source_equation,
        target_equation,
        law_equation="a * (a * b) = a",
    )


def right_self_absorption_instance_true_judge_answer(
    source_equation: str,
    target_equation: str,
) -> dict:
    return {
        "verdict": "true",
        "code": right_self_absorption_instance_true_judge_code(
            source_equation,
            target_equation,
        ),
    }


def right_self_absorption_instance_true_judge_code(
    source_equation: str,
    target_equation: str,
) -> str:
    return _law_instance_true_judge_code(
        source_equation,
        target_equation,
        law_equation="(a * b) * b = b",
    )


def left_sandwich_absorption_instance_true_judge_answer(
    source_equation: str,
    target_equation: str,
) -> dict:
    return {
        "verdict": "true",
        "code": left_sandwich_absorption_instance_true_judge_code(
            source_equation,
            target_equation,
        ),
    }


def left_sandwich_absorption_instance_true_judge_code(
    source_equation: str,
    target_equation: str,
) -> str:
    return _law_instance_true_judge_code(
        source_equation,
        target_equation,
        law_equation="a * (b * a) = a",
    )


def right_sandwich_absorption_instance_true_judge_answer(
    source_equation: str,
    target_equation: str,
) -> dict:
    return {
        "verdict": "true",
        "code": right_sandwich_absorption_instance_true_judge_code(
            source_equation,
            target_equation,
        ),
    }


def right_sandwich_absorption_instance_true_judge_code(
    source_equation: str,
    target_equation: str,
) -> str:
    return _law_instance_true_judge_code(
        source_equation,
        target_equation,
        law_equation="(a * b) * a = a",
    )


def target_instance_of_source_true_judge_answer(
    source_equation: str,
    target_equation: str,
) -> dict:
    return {
        "verdict": "true",
        "code": target_instance_of_source_true_judge_code(
            source_equation,
            target_equation,
        ),
    }


def target_instance_of_source_true_judge_code(
    source_equation: str,
    target_equation: str,
) -> str:
    source = _parse_stage2_equation(source_equation)
    target = _parse_stage2_equation(target_equation)
    match = _match_target_instance_of_source(source, target)
    if match is None:
        raise ValueError("target equation is not an instance of source")

    orientation, substitutions = match
    source_args = " ".join(
        lean_expr(substitutions[variable], top=False)
        for variable in source.variables()
    )
    exact = f"h {source_args}" if source_args else "h"
    if orientation == "symm":
        exact = f"({exact}).symm"
    target_variables = target.variables()
    target_intro = f"  intro {' '.join(target_variables)}\n" if target_variables else ""
    return (
        "import JudgeProblem\n\n"
        "def submission : Goal := by\n"
        "  intro G _ h\n"
        f"{target_intro}"
        f"  exact {exact}\n"
    )


def _law_instance_true_judge_code(
    source_equation: str,
    target_equation: str,
    *,
    law_equation: str,
) -> str:
    source = _parse_stage2_equation(source_equation)
    target = _parse_stage2_equation(target_equation)
    law = _parse_stage2_equation(law_equation)
    source_match = _match_law_instance_source(source, law)
    if source_match is None:
        raise ValueError("source equation is not a law-instance source")
    target_match = _match_law_instance_target(law, target)
    if target_match is None:
        raise ValueError("target equation is not a law-instance target")

    source_orientation, source_substitutions = source_match
    target_orientation, target_substitutions = target_match
    source_args = " ".join(
        lean_expr(source_substitutions[variable], top=False)
        for variable in source.variables()
    )
    source_exact = f"h {source_args}" if source_args else "h"
    if source_orientation == "symm":
        source_exact = f"({source_exact}).symm"

    law_variables = law.variables()
    target_args = " ".join(
        lean_expr(target_substitutions[variable], top=False)
        for variable in law_variables
    )
    target_exact = f"law {target_args}" if target_args else "law"
    if target_orientation == "symm":
        target_exact = f"({target_exact}).symm"
    target_variables = target.variables()
    target_intro = f"  intro {' '.join(target_variables)}\n" if target_variables else ""
    law_intro = f"    intro {' '.join(law_variables)}\n" if law_variables else ""
    law_binders = f"({' '.join(law_variables)} : G)"
    return (
        "import JudgeProblem\n\n"
        "def submission : Goal := by\n"
        "  intro G _ h\n"
        f"  have law : ∀ {law_binders}, "
        f"{lean_expr(law.left, top=True)} = "
        f"{lean_expr(law.right, top=True)} := by\n"
        f"{law_intro}"
        f"    exact {source_exact}\n"
        f"{target_intro}"
        f"  exact {target_exact}\n"
    )


def _projection_normalizer_true_judge_code(
    source_equation: str,
    target_equation: str,
    *,
    side: str,
) -> str:
    source = _parse_stage2_equation(source_equation)
    target = _parse_stage2_equation(target_equation)
    shape = _projection_normalizer_source_shape(source, side=side)
    if shape is None:
        raise ValueError(f"source equation is not a {side}-projection normalizer")
    if not _is_projection_normal_target(target, side=side):
        raise ValueError(f"target equation is not a {side}-projection normal target")

    role_values = {"a": "a", "b": "b"}
    h_args = " ".join(
        role_values[shape["role_by_variable"][variable]]
        for variable in source.variables()
    )
    h_call = f"h {h_args}" if h_args else "h"
    projection_proof = f"({h_call}).symm" if shape["var_eq_product"] else h_call
    theorem_name = "leftproj" if side == "left" else "rightproj"
    theorem_rhs = "a" if side == "left" else "b"
    target_variables = target.variables()
    target_intro = f"  intro {' '.join(target_variables)}\n" if target_variables else ""
    target_normal = _projection_edge_variable(target.left, side=side)
    assert target_normal == _projection_edge_variable(target.right, side=side)
    left_proof = _projection_normalization_proof(
        target.left,
        theorem_name=theorem_name,
        side=side,
    )
    right_proof = _projection_normalization_proof(
        target.right,
        theorem_name=theorem_name,
        side=side,
    )
    return (
        "import JudgeProblem\n\n"
        "def submission : Goal := by\n"
        "  intro G _ h\n"
        f"  have {theorem_name} : ∀ (a b : G), a ◇ b = {theorem_rhs} := by\n"
        "    intro a b\n"
        f"    exact {projection_proof}\n"
        f"{target_intro}"
        "  calc\n"
        f"    {lean_expr(target.left, top=True)} = {target_normal} := {left_proof}\n"
        f"    _ = {lean_expr(target.right, top=True)} := ({right_proof}).symm\n"
    )


def _projection_normalization_proof(expr, *, theorem_name: str, side: str) -> str:
    if expr.kind == "var":
        return f"Eq.refl {lean_expr(expr, top=True)}"
    assert expr.left is not None
    assert expr.right is not None
    left = lean_expr(expr.left, top=False)
    right = lean_expr(expr.right, top=False)
    next_expr = expr.left if side == "left" else expr.right
    return (
        f"({theorem_name} {left} {right}).trans "
        f"({_projection_normalization_proof(next_expr, theorem_name=theorem_name, side=side)})"
    )


def _finmodel_setcheck_evidence(
    table: tuple[tuple[int, ...], ...],
    source_ids: frozenset[int],
    target_ids: frozenset[int],
) -> dict:
    return {
        "model_family": _model_family(table),
        "model_table": [list(row) for row in table],
        "model_verified": True,
        "model_source_count": len(source_ids),
        "model_source_satisfied": len(source_ids),
        "model_source_failures": 0,
        "model_target_count": len(target_ids),
        "model_target_refuted": len(target_ids),
        "model_target_failures": 0,
    }


def _singleton_collapse_evidence(
    source_ids: frozenset[int],
    target_ids: frozenset[int],
    direction_counts: dict[str, int],
) -> dict:
    return {
        "template_family": "singleton_collapse",
        "template_verified": True,
        "template_source_count": len(source_ids),
        "template_source_matched": len(source_ids),
        "template_source_failures": 0,
        "template_target_count": len(target_ids),
        "template_target_scope": "all_equations",
        "template_source_shape": "bare_variable_absent_from_other_side",
        "template_left_bare_source_count": direction_counts.get("left", 0),
        "template_right_bare_source_count": direction_counts.get("right", 0),
    }


def _singleton_seedbank_evidence(
    source_ids: frozenset[int],
    target_ids: frozenset[int],
    mismatched_source_ids: Sequence[int],
) -> dict:
    return {
        "proof_bank_family": "singleton_seedbank",
        "proof_bank_verified": True,
        "proof_bank_source_count": len(source_ids),
        "proof_bank_available_source_count": _available_singleton_seed_source_count(),
        "proof_bank_source_ids": sorted(source_ids),
        "proof_bank_signature_mismatch_count": len(mismatched_source_ids),
        "proof_bank_signature_mismatch_ids": sorted(mismatched_source_ids),
        "proof_bank_target_count": len(target_ids),
        "proof_bank_target_scope": "all_equations",
        "template_family": "singleton_seedbank",
        "template_verified": True,
    }


def _singleton_seedbank_specialization_evidence(
    source_ids: frozenset[int],
    target_ids: frozenset[int],
    match_counts: dict[int, int],
    seed_source_count: int,
) -> dict:
    return {
        "template_family": "singleton_seedbank_specialization",
        "template_verified": True,
        "template_source_count": len(source_ids),
        "template_source_matched": len(source_ids),
        "template_source_failures": 0,
        "template_target_count": len(target_ids),
        "template_target_scope": "all_equations",
        "template_seed_source_count": seed_source_count,
        "template_matched_seed_ids": sorted(match_counts),
        "template_match_counts_by_seed_id": {
            str(seed_id): count for seed_id, count in sorted(match_counts.items())
        },
    }


def _singleton_superpose_evidence(
    source_ids: frozenset[int],
    target_ids: frozenset[int],
    source_counts: dict[str, int],
) -> dict:
    return {
        "template_family": "singleton_superpose",
        "template_verified": True,
        "template_source_count": len(source_ids),
        "template_source_matched": len(source_ids),
        "template_source_failures": 0,
        "template_target_count": len(target_ids),
        "template_target_scope": "all_equations",
        "template_source_shape": "eq1087_or_superpose_collapse_singleton",
        "template_eq1087_source_count": source_counts.get("eq1087", 0),
        "template_superpose_collapse_source_count": source_counts.get(
            "superpose_collapse",
            0,
        ),
    }


def _product_anchor_evidence(
    source_ids: frozenset[int],
    target_ids: frozenset[int],
    direction_counts: dict[str, int],
) -> dict:
    return {
        "template_family": "term_shape_anchor_product",
        "template_verified": True,
        "template_source_count": len(source_ids),
        "template_source_matched": len(source_ids),
        "template_source_failures": 0,
        "template_target_count": len(target_ids),
        "template_target_scope": "product_root_equations",
        "template_source_shape": "distinct_bare_product_absent_from_anchor_side",
        "template_left_product_source_count": direction_counts.get("left", 0),
        "template_right_product_source_count": direction_counts.get("right", 0),
    }


def _product_anchor_seed_lift_evidence(
    source_ids: frozenset[int],
    target_ids: frozenset[int],
    counts: dict[str, object],
    candidate_jsonl_path: Path,
) -> dict:
    return {
        "template_family": "product_anchor_seed_lift",
        "template_verified": True,
        "template_source_count": len(source_ids),
        "template_source_matched": len(source_ids),
        "template_source_failures": counts.get("source_signature_mismatch_count", 0),
        "template_target_count": len(target_ids),
        "template_target_scope": "product_root_equations",
        "candidate_key": PRODUCT_ANCHOR_SEED_LIFT_CANDIDATE_KEY,
        "candidate_jsonl_path": str(candidate_jsonl_path),
        "candidate_source_count": counts.get("candidate_source_count", len(source_ids)),
        "candidate_source_ids": sorted(source_ids),
        "candidate_seed_product_anchor_source_ids": counts.get(
            "seed_product_anchor_source_ids",
            [],
        ),
        "candidate_proof_body_sha256_by_source_id": counts.get(
            "proof_body_sha256_by_source_id",
            {},
        ),
        "candidate_source_signature_mismatch_ids": counts.get(
            "source_signature_mismatch_ids",
            [],
        ),
        "candidate_delta_preview_path": (
            "data/processed/order5_strategy_registry/candidates/"
            "true_template_product_anchor_seed_lift_tail_profile_v3_delta_preview_"
            "20260521.json"
        ),
        "candidate_exact_raw_coverage": 135612,
        "candidate_exact_union_increment": 124237,
        "candidate_same_verdict_overlap": 11375,
        "candidate_conflict_increment": 0,
        "remote_smoke_summary_path": (
            "data/processed/order5_strategy_registry/candidates/"
            "true_template_product_anchor_seed_lift_tail_maintained_broad18_smoke_"
            "20260521_summary.json"
        ),
        "remote_smoke_input_path": (
            "data/processed/order5_strategy_registry/candidates/"
            "true_template_product_anchor_seed_lift_tail_maintained_broad18_smoke_"
            "20260521_input.jsonl"
        ),
        "remote_smoke_results_path": (
            "data/processed/order5_strategy_registry/candidates/"
            "true_template_product_anchor_seed_lift_tail_maintained_broad18_smoke_"
            "20260521_results.jsonl"
        ),
        "remote_smoke_accepted_count": 18,
        "remote_smoke_total_count": 18,
        "remote_smoke_backend": "remote-judge-v2:10.220.69.172:8890",
    }


def _product_collapse_evidence(
    term_pattern: str,
    source_ids: frozenset[int],
    target_ids: frozenset[int],
    counts: dict[str, int],
) -> dict:
    return {
        "template_family": "term_shape_anchor_product_collapse",
        "template_verified": True,
        "template_term_pattern": term_pattern,
        "template_source_count": len(source_ids),
        "template_source_matched": len(source_ids),
        "template_source_failures": 0,
        "template_target_count": len(target_ids),
        "template_target_matched": len(target_ids),
        "template_target_scope": "both_sides_match_term_pattern",
        "template_source_shape": "term_pattern_absent_from_anchor_side",
        "template_left_pattern_source_occurrence_count": counts.get("left", 0),
        "template_right_pattern_source_occurrence_count": counts.get("right", 0),
        "template_repetition_handling": (
            "repeated pattern variables must match identical target subterms"
        ),
        "template_remote_smoke_summary_path": (
            "data/processed/order5_strategy_registry/candidates/"
            "true_template_product_collapse_residual_smoke_20260519_summary.json"
        ),
        "template_cumulative_merge_summary_path": (
            "data/processed/order5_strategy_registry/candidates/"
            "true_template_product_collapse_residual_cumulative_merge_exact_20260519.json"
        ),
    }


def _projection_normalizer_evidence(
    side: str,
    source_ids: frozenset[int],
    target_ids: frozenset[int],
    counts: dict[str, int],
) -> dict:
    return {
        "template_family": f"projection_normalizer_{side}",
        "template_verified": True,
        "template_source_count": len(source_ids),
        "template_source_matched": len(source_ids),
        "template_source_failures": 0,
        "template_target_count": len(target_ids),
        "template_target_matched": len(target_ids),
        "template_target_scope": f"{side}_projection_normal_equations",
        "template_source_shape": f"{side}_projection_law",
        "template_var_eq_product_source_count": counts.get("var_eq_product", 0),
        "template_product_eq_var_source_count": counts.get("product_eq_var", 0),
    }


def _law_instance_evidence(
    name: str,
    source_ids: frozenset[int],
    target_ids: frozenset[int],
    counts: dict[str, int],
) -> dict:
    return {
        "template_family": f"law_instance_{name}",
        "template_verified": True,
        "template_source_count": len(source_ids),
        "template_source_matched": len(source_ids),
        "template_source_failures": 0,
        "template_target_count": len(target_ids),
        "template_target_matched": len(target_ids),
        "template_target_scope": f"{name}_instances",
        "template_source_shape": f"{name}_source_specializes_to_law",
        "template_source_direct_match_count": counts.get("source_direct", 0),
        "template_source_symm_match_count": counts.get("source_symm", 0),
        "template_target_direct_match_count": counts.get("target_direct", 0),
        "template_target_symm_match_count": counts.get("target_symm", 0),
    }


@lru_cache(maxsize=8)
def _target_instance_of_source_pair_indexes(
    equations_path: Path = DEFAULT_EQ_SIZE5_PATH,
    order4_max_id: int = DEFAULT_ORDER4_MAX_ID,
) -> tuple[frozenset[int], dict[str, object]]:
    parsed_features = _cached_parsed_equation_features(equations_path)
    law_count = len(parsed_features)
    source_id_by_signature = {
        _canonical_signature_from_equation(equation): int(feature.equation_id)
        for feature, equation in parsed_features
    }
    pair_indexes: set[int] = set()
    source_ids: set[int] = set()
    target_ids: set[int] = set()
    orientation_counts = {
        "direct_only": 0,
        "symmetric_only": 0,
        "both_orientations": 0,
    }
    matched_sources_per_target: list[int] = []
    order4_excluded_pairs: set[tuple[int, int]] = set()

    def should_include(source_id: int, target_id: int) -> bool:
        if source_id == target_id:
            return False
        if source_id <= order4_max_id and target_id <= order4_max_id:
            order4_excluded_pairs.add((source_id, target_id))
            return False
        return True

    for feature, target in parsed_features:
        target_id = int(feature.equation_id)
        direct_sources = {
            source_id
            for source_id in _target_instance_source_ids(
                target,
                source_id_by_signature,
            )
            if should_include(source_id, target_id)
        }
        reversed_target = Equation(left=target.right, right=target.left)
        symm_sources = {
            source_id
            for source_id in _target_instance_source_ids(
                reversed_target,
                source_id_by_signature,
            )
            if should_include(source_id, target_id)
        }
        both = direct_sources & symm_sources
        direct_only = direct_sources - both
        symm_only = symm_sources - both
        orientation_counts["direct_only"] += len(direct_only)
        orientation_counts["symmetric_only"] += len(symm_only)
        orientation_counts["both_orientations"] += len(both)
        union_sources = direct_sources | symm_sources
        if not union_sources:
            continue
        target_ids.add(target_id)
        source_ids.update(union_sources)
        matched_sources_per_target.append(len(union_sources))
        for source_id in union_sources:
            pair_indexes.add(
                ids_to_pair_index(source_id, target_id, law_count=law_count)
            )

    sorted_pair_indexes = sorted(pair_indexes)
    digest = hashlib.sha256()
    for pair_index in sorted_pair_indexes:
        digest.update(f"{pair_index}\n".encode("ascii"))
    quantiles = _integer_quantiles(matched_sources_per_target)
    sample_pairs = [
        {
            "pair_index": pair_index,
            "source_id": pair_index_to_ids(pair_index, law_count=law_count)[0],
            "target_id": pair_index_to_ids(pair_index, law_count=law_count)[1],
        }
        for pair_index in sorted_pair_indexes[:20]
    ]
    evidence = {
        "template_family": "law_instance_target_instance_of_source",
        "template_verified": True,
        "law_count": law_count,
        "template_pair_count": len(pair_indexes),
        "template_source_count": len(source_ids),
        "template_target_count": len(target_ids),
        "template_target_scope": "target_or_reversed_target_instance_of_source",
        "template_source_shape": "any_source_equation",
        "template_pair_index_sha256_newline_sorted": digest.hexdigest(),
        "template_direct_only_pair_count": orientation_counts["direct_only"],
        "template_symmetric_only_pair_count": orientation_counts["symmetric_only"],
        "template_both_orientations_pair_count": orientation_counts[
            "both_orientations"
        ],
        "template_order4_to_order4_excluded_pair_count": len(order4_excluded_pairs),
        "template_matched_source_count_per_target_quantiles": quantiles,
        "template_sample_pairs": sample_pairs,
    }
    return frozenset(pair_indexes), evidence


@lru_cache(maxsize=4)
def _opnorm_hconst_match_collapse_pair_indexes(
    *,
    law_count: int,
    pair_index_cache_path: Path = DEFAULT_OPNORM_HCONST_MATCH_COLLAPSE_PAIR_INDEX_CACHE,
    register_summary_path: Path = DEFAULT_OPNORM_HCONST_MATCH_COLLAPSE_REGISTER_SUMMARY,
) -> tuple[frozenset[int], dict[str, object]]:
    pair_index_cache_path = Path(pair_index_cache_path)
    if not pair_index_cache_path.exists():
        raise FileNotFoundError(pair_index_cache_path)

    pair_indexes: set[int] = set()
    duplicate_count = 0
    digest = hashlib.sha256()
    with pair_index_cache_path.open(encoding="ascii") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                pair_index = int(stripped)
            except ValueError as exc:
                raise ValueError(
                    f"invalid pair_index on line {line_number} of "
                    f"{pair_index_cache_path}: {stripped!r}"
                ) from exc
            pair_index_to_ids(pair_index, law_count=law_count)
            if pair_index in pair_indexes:
                duplicate_count += 1
                continue
            pair_indexes.add(pair_index)

    for pair_index in sorted(pair_indexes):
        digest.update(f"{pair_index}\n".encode("ascii"))

    register_summary = _load_optional_json(register_summary_path)
    sample_pairs = register_summary.get("sample_pairs", []) if register_summary else []
    delta = register_summary.get(
        "delta_against_current_profile_v6",
        register_summary.get("delta_against_current_profile_v5", {}),
    )
    smoke_summary_paths = register_summary.get(
        "remote_smoke_summary_paths",
        [
            (
                "data/processed/order5_strategy_registry/candidates/"
                "true_template_opnorm_hconst_shape_top16_top13_top12_"
                "smoke_20260521_summary.json"
            ),
            (
                "data/processed/order5_strategy_registry/candidates/"
                "true_template_opnorm_hconst_shape_top08_exact_smoke_"
                "20260521_summary.json"
            ),
        ],
    )
    smoke_accepted_count = register_summary.get("remote_smoke_accepted_count", 23)
    smoke_total_count = register_summary.get("remote_smoke_total_count", 23)
    evidence = {
        "template_family": "opnorm_hconst_match_collapse",
        "template_verified": True,
        "law_count": law_count,
        "template_pair_count": len(pair_indexes),
        "template_source_shape": "top16_top13_top12_top08_residual_shape_buckets",
        "template_target_scope": "compiler_verified_pair_indexes",
        "template_shape_buckets": [
            f"{source_shape} -> {target_shape}"
            for source_shape, target_shape in OPNORM_HCONST_MATCH_COLLAPSE_SHAPE_BUCKETS
        ],
        "template_pair_index_cache_path": str(pair_index_cache_path),
        "template_pair_index_sha256_newline_sorted": digest.hexdigest(),
        "template_duplicate_pair_index_count": duplicate_count,
        "template_current_union_increment": delta.get("union_increment"),
        "template_current_conflict_increment": delta.get("conflict_increment"),
        "template_current_profile": register_summary.get("coverage_profile")
        if register_summary
        else None,
        "template_register_summary_path": str(register_summary_path),
        "template_controller_merge_review_path": register_summary.get(
            "controller_merge_review"
        ),
        "template_remote_smoke_summary_paths": smoke_summary_paths,
        "template_remote_smoke_accepted_count": smoke_accepted_count,
        "template_remote_smoke_total_count": smoke_total_count,
        "template_remote_smoke_status": (
            f"accepted_{smoke_accepted_count}_of_{smoke_total_count}"
        ),
        "template_sample_pairs": sample_pairs,
    }
    return frozenset(pair_indexes), evidence


@lru_cache(maxsize=4)
def _opnorm_hconst_sandwich_pair_indexes(
    *,
    law_count: int,
    pair_index_cache_path: Path = DEFAULT_OPNORM_HCONST_SANDWICH_PAIR_INDEX_CACHE,
    register_summary_path: Path = DEFAULT_OPNORM_HCONST_SANDWICH_REGISTER_SUMMARY,
) -> tuple[frozenset[int], dict[str, object]]:
    pair_index_cache_path = Path(pair_index_cache_path)
    if not pair_index_cache_path.exists():
        raise FileNotFoundError(pair_index_cache_path)

    pair_indexes: set[int] = set()
    duplicate_count = 0
    digest = hashlib.sha256()
    with pair_index_cache_path.open(encoding="ascii") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                pair_index = int(stripped)
            except ValueError as exc:
                raise ValueError(
                    f"invalid pair_index on line {line_number} of "
                    f"{pair_index_cache_path}: {stripped!r}"
                ) from exc
            pair_index_to_ids(pair_index, law_count=law_count)
            if pair_index in pair_indexes:
                duplicate_count += 1
                continue
            pair_indexes.add(pair_index)

    for pair_index in sorted(pair_indexes):
        digest.update(f"{pair_index}\n".encode("ascii"))

    register_summary = _load_optional_json(register_summary_path)
    delta = register_summary.get("delta_against_current_profile_v6", {})
    smoke_summary_paths = register_summary.get("remote_smoke_summary_paths", [])
    smoke_accepted_count = register_summary.get("remote_smoke_accepted_count", 80)
    smoke_total_count = register_summary.get("remote_smoke_total_count", 80)
    source_ids = register_summary.get("source_ids", [])
    target_shape_counts = register_summary.get("target_shape_counts", {})
    evidence = {
        "template_family": "opnorm_hconst_sandwich_match_collapse",
        "template_verified": True,
        "law_count": law_count,
        "template_pair_count": len(pair_indexes),
        "template_source_count": len(source_ids),
        "template_source_ids": source_ids,
        "template_source_shape": "yyleft_repfilter_source_family",
        "template_target_scope": "targetbatch_10_shapes",
        "template_target_shape_count": len(target_shape_counts),
        "template_target_shape_counts": target_shape_counts,
        "template_pair_index_cache_path": str(pair_index_cache_path),
        "template_pair_index_sha256_newline_sorted": digest.hexdigest(),
        "template_duplicate_pair_index_count": duplicate_count,
        "template_current_union_increment": delta.get("union_increment"),
        "template_current_conflict_increment": delta.get("conflict_increment"),
        "template_current_profile": register_summary.get("coverage_profile")
        if register_summary
        else None,
        "template_after_merge_projection_against_current_summary": register_summary.get(
            "after_merge_projection_against_current_summary"
        ),
        "template_register_summary_path": str(register_summary_path),
        "template_source_hits_path": register_summary.get("source_hits_path"),
        "template_remote_smoke_summary_paths": smoke_summary_paths,
        "template_remote_smoke_accepted_count": smoke_accepted_count,
        "template_remote_smoke_total_count": smoke_total_count,
        "template_remote_smoke_status": (
            f"accepted_{smoke_accepted_count}_of_{smoke_total_count}"
        ),
        "template_sample_pairs": register_summary.get("sample_pairs", []),
    }
    return frozenset(pair_indexes), evidence


@lru_cache(maxsize=4)
def _opnorm_hconst_lmrm_mainline_pair_indexes(
    *,
    law_count: int,
    pair_index_cache_path: Path = DEFAULT_OPNORM_HCONST_LMRM_MAINLINE_PAIR_INDEX_CACHE,
    register_summary_path: Path = DEFAULT_OPNORM_HCONST_LMRM_MAINLINE_REGISTER_SUMMARY,
) -> tuple[frozenset[int], dict[str, object]]:
    pair_index_cache_path = Path(pair_index_cache_path)
    if not pair_index_cache_path.exists():
        raise FileNotFoundError(pair_index_cache_path)

    pair_indexes: set[int] = set()
    duplicate_count = 0
    digest = hashlib.sha256()
    with pair_index_cache_path.open(encoding="ascii") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                pair_index = int(stripped)
            except ValueError as exc:
                raise ValueError(
                    f"invalid pair_index on line {line_number} of "
                    f"{pair_index_cache_path}: {stripped!r}"
                ) from exc
            pair_index_to_ids(pair_index, law_count=law_count)
            if pair_index in pair_indexes:
                duplicate_count += 1
                continue
            pair_indexes.add(pair_index)

    for pair_index in sorted(pair_indexes):
        digest.update(f"{pair_index}\n".encode("ascii"))

    register_summary = _load_optional_json(register_summary_path)
    delta = register_summary.get("delta_against_current_profile_v7", {})
    smoke_accepted_count = register_summary.get("remote_smoke_accepted_count", 30)
    smoke_total_count = register_summary.get("remote_smoke_total_count", 30)
    evidence = {
        "template_family": "opnorm_hconst_match_collapse_lmrm_mainline",
        "template_verified": True,
        "law_count": law_count,
        "template_pair_count": len(pair_indexes),
        "template_source_shape": "d14_vc4_left_right_hconst_source_classes",
        "template_source_count": register_summary.get("source_count"),
        "template_source_ids_sample": register_summary.get("source_ids_sample", []),
        "template_source_shape_counts": register_summary.get(
            "source_shape_counts",
            {},
        ),
        "template_source_class_hit_counts": register_summary.get(
            "source_class_hit_counts",
            {},
        ),
        "template_target_scope": "lm1_rm1_d23_target_subfamilies",
        "template_target_shape_counts": register_summary.get(
            "target_shape_counts",
            {},
        ),
        "template_target_label_hit_counts": register_summary.get(
            "target_label_hit_counts",
            {},
        ),
        "template_component_count": register_summary.get("component_count"),
        "template_component_hit_files": register_summary.get(
            "component_hit_files",
            [],
        ),
        "template_pair_index_cache_path": str(pair_index_cache_path),
        "template_pair_index_sha256_newline_sorted": digest.hexdigest(),
        "template_duplicate_pair_index_count": duplicate_count,
        "template_current_union_increment": delta.get("union_increment"),
        "template_current_conflict_increment": delta.get("conflict_increment"),
        "template_current_profile": register_summary.get("coverage_profile")
        if register_summary
        else None,
        "template_after_merge_projection_against_current_summary": register_summary.get(
            "after_merge_projection_against_current_summary"
        ),
        "template_register_summary_path": str(register_summary_path),
        "template_remote_smoke_summary_paths": register_summary.get(
            "remote_smoke_summary_paths",
            [],
        ),
        "template_remote_smoke_accepted_count": smoke_accepted_count,
        "template_remote_smoke_total_count": smoke_total_count,
        "template_remote_smoke_status": (
            f"accepted_{smoke_accepted_count}_of_{smoke_total_count}"
        ),
        "template_sample_pairs": register_summary.get("sample_pairs", []),
    }
    return frozenset(pair_indexes), evidence


@lru_cache(maxsize=4)
def _opnorm_hconst_varmul_top01_pair_indexes(
    *,
    law_count: int,
    pair_index_cache_path: Path = DEFAULT_OPNORM_HCONST_VARMUL_TOP01_PAIR_INDEX_CACHE,
    register_summary_path: Path = DEFAULT_OPNORM_HCONST_VARMUL_TOP01_REGISTER_SUMMARY,
) -> tuple[frozenset[int], dict[str, object]]:
    pair_index_cache_path = Path(pair_index_cache_path)
    if not pair_index_cache_path.exists():
        raise FileNotFoundError(pair_index_cache_path)

    pair_indexes: set[int] = set()
    duplicate_count = 0
    digest = hashlib.sha256()
    with pair_index_cache_path.open(encoding="ascii") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                pair_index = int(stripped)
            except ValueError as exc:
                raise ValueError(
                    f"invalid pair_index on line {line_number} of "
                    f"{pair_index_cache_path}: {stripped!r}"
                ) from exc
            pair_index_to_ids(pair_index, law_count=law_count)
            if pair_index in pair_indexes:
                duplicate_count += 1
                continue
            pair_indexes.add(pair_index)

    for pair_index in sorted(pair_indexes):
        digest.update(f"{pair_index}\n".encode("ascii"))

    register_summary = _load_optional_json(register_summary_path)
    delta = register_summary.get("delta_against_current_profile_v8", {})
    smoke_accepted_count = register_summary.get("remote_smoke_accepted_count", 30)
    smoke_total_count = register_summary.get("remote_smoke_total_count", 30)
    evidence = {
        "template_family": "opnorm_hconst_match_collapse_varmul_top01",
        "template_verified": True,
        "law_count": law_count,
        "template_pair_count": len(pair_indexes),
        "template_source_shape": register_summary.get(
            "source_shape",
            "roots=var>mul|d=0>4|vc=4|lm=0|rm=0|vs=0",
        ),
        "template_target_scope": register_summary.get(
            "target_shape",
            "roots=var>mul|d=0>4|vc=4|lm=0|rm=0|vs=0",
        ),
        "template_source_offset_range": register_summary.get(
            "source_offset_range",
            [0, 500],
        ),
        "template_source_count_with_hits": register_summary.get(
            "source_count_with_hits"
        ),
        "template_target_count_with_hits": register_summary.get(
            "target_count_with_hits"
        ),
        "template_hit_stratum_counts": register_summary.get(
            "hit_stratum_counts",
            {},
        ),
        "template_pair_index_cache_path": str(pair_index_cache_path),
        "template_pair_index_sha256_newline_sorted": digest.hexdigest(),
        "template_duplicate_pair_index_count": duplicate_count,
        "template_current_union_increment": delta.get("union_increment"),
        "template_current_conflict_increment": delta.get("conflict_increment"),
        "template_current_profile": register_summary.get("coverage_profile")
        if register_summary
        else None,
        "template_after_merge_projection_against_current_summary": register_summary.get(
            "after_merge_projection_against_current_summary"
        ),
        "template_register_summary_path": str(register_summary_path),
        "template_source_hits_path": register_summary.get("source_hits_path"),
        "template_remote_smoke_summary_paths": register_summary.get(
            "remote_smoke_summary_paths",
            [],
        ),
        "template_remote_smoke_accepted_count": smoke_accepted_count,
        "template_remote_smoke_total_count": smoke_total_count,
        "template_remote_smoke_status": (
            f"accepted_{smoke_accepted_count}_of_{smoke_total_count}"
        ),
        "template_sample_pairs": register_summary.get("sample_pairs", []),
    }
    return frozenset(pair_indexes), evidence


@lru_cache(maxsize=4)
def _opnorm_hconst_default_sandwich_top16_pair_indexes(
    *,
    law_count: int,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_TOP16_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_TOP16_REGISTER_SUMMARY
    ),
) -> tuple[frozenset[int], dict[str, object]]:
    pair_index_cache_path = Path(pair_index_cache_path)
    if not pair_index_cache_path.exists():
        raise FileNotFoundError(pair_index_cache_path)

    pair_indexes: set[int] = set()
    duplicate_count = 0
    digest = hashlib.sha256()
    with pair_index_cache_path.open(encoding="ascii") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                pair_index = int(stripped)
            except ValueError as exc:
                raise ValueError(
                    f"invalid pair_index on line {line_number} of "
                    f"{pair_index_cache_path}: {stripped!r}"
                ) from exc
            pair_index_to_ids(pair_index, law_count=law_count)
            if pair_index in pair_indexes:
                duplicate_count += 1
                continue
            pair_indexes.add(pair_index)

    for pair_index in sorted(pair_indexes):
        digest.update(f"{pair_index}\n".encode("ascii"))

    register_summary = _load_optional_json(register_summary_path)
    delta = register_summary.get("delta_against_current_profile_v8", {})
    smoke_accepted_count = register_summary.get("remote_smoke_accepted_count", 71)
    smoke_total_count = register_summary.get("remote_smoke_total_count", 71)
    evidence = {
        "template_family": "opnorm_hconst_default_sandwich_match_collapse_top16",
        "template_verified": True,
        "law_count": law_count,
        "template_pair_count": len(pair_indexes),
        "template_source_shape": register_summary.get("source_shape"),
        "template_target_scope": register_summary.get("target_shape"),
        "template_shape_bucket": register_summary.get("shape_bucket"),
        "template_source_count": register_summary.get("source_count"),
        "template_target_count": register_summary.get("target_count"),
        "template_hit_stratum_counts": register_summary.get(
            "hit_stratum_counts",
            {},
        ),
        "template_top_source_hit_counts": register_summary.get(
            "top_source_hit_counts",
            [],
        ),
        "template_pair_index_cache_path": str(pair_index_cache_path),
        "template_pair_index_sha256_newline_sorted": digest.hexdigest(),
        "template_duplicate_pair_index_count": duplicate_count,
        "template_current_union_increment": delta.get("union_increment"),
        "template_current_conflict_increment": delta.get("conflict_increment"),
        "template_current_profile": register_summary.get("coverage_profile")
        if register_summary
        else None,
        "template_after_merge_projection_against_current_summary": register_summary.get(
            "after_merge_projection_against_current_summary"
        ),
        "template_register_summary_path": str(register_summary_path),
        "template_source_hits_path": register_summary.get("source_hits_path"),
        "template_remote_smoke_summary_paths": register_summary.get(
            "remote_smoke_summary_paths",
            [],
        ),
        "template_remote_smoke_accepted_count": smoke_accepted_count,
        "template_remote_smoke_total_count": smoke_total_count,
        "template_remote_smoke_status": (
            f"accepted_{smoke_accepted_count}_of_{smoke_total_count}"
        ),
        "template_sample_pairs": register_summary.get("sample_pairs", []),
    }
    return frozenset(pair_indexes), evidence


@lru_cache(maxsize=4)
def _opnorm_hconst_default_sandwich_d14vc4_pair_indexes(
    *,
    law_count: int,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_D14VC4_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_D14VC4_REGISTER_SUMMARY
    ),
) -> tuple[frozenset[int], dict[str, object]]:
    pair_index_cache_path = Path(pair_index_cache_path)
    if not pair_index_cache_path.exists():
        raise FileNotFoundError(pair_index_cache_path)

    pair_indexes: set[int] = set()
    duplicate_count = 0
    digest = hashlib.sha256()
    with pair_index_cache_path.open(encoding="ascii") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                pair_index = int(stripped)
            except ValueError as exc:
                raise ValueError(
                    f"invalid pair_index on line {line_number} of "
                    f"{pair_index_cache_path}: {stripped!r}"
                ) from exc
            pair_index_to_ids(pair_index, law_count=law_count)
            if pair_index in pair_indexes:
                duplicate_count += 1
                continue
            pair_indexes.add(pair_index)

    for pair_index in sorted(pair_indexes):
        digest.update(f"{pair_index}\n".encode("ascii"))

    register_summary = _load_optional_json(register_summary_path)
    delta = register_summary.get("delta_against_current_profile_v9", {})
    smoke_accepted_count = register_summary.get("remote_smoke_accepted_count", 86)
    smoke_total_count = register_summary.get("remote_smoke_total_count", 86)
    evidence = {
        "template_family": "opnorm_hconst_default_sandwich_match_collapse_d14vc4",
        "template_verified": True,
        "law_count": law_count,
        "template_pair_count": len(pair_indexes),
        "template_source_shape": register_summary.get("source_shape"),
        "template_target_scope": "d14vc4_and_d23vc4_targets",
        "template_target_shapes": register_summary.get("target_shapes", []),
        "template_target_shape_count": register_summary.get("target_shape_count"),
        "template_source_count": register_summary.get("source_count"),
        "template_shape_counts": register_summary.get("shape_counts", {}),
        "template_hit_stratum_counts": register_summary.get(
            "hit_stratum_counts",
            {},
        ),
        "template_top_source_hit_counts": register_summary.get(
            "top_source_hit_counts",
            [],
        ),
        "template_pair_index_cache_path": str(pair_index_cache_path),
        "template_pair_index_sha256_newline_sorted": digest.hexdigest(),
        "template_duplicate_pair_index_count": duplicate_count,
        "template_current_union_increment": delta.get("union_increment"),
        "template_current_conflict_increment": delta.get("conflict_increment"),
        "template_current_profile": register_summary.get("coverage_profile")
        if register_summary
        else None,
        "template_after_merge_projection_against_current_summary": register_summary.get(
            "after_merge_projection_against_current_summary"
        ),
        "template_register_summary_path": str(register_summary_path),
        "template_source_hits_path": register_summary.get("source_hits_path"),
        "template_remote_smoke_summary_paths": register_summary.get(
            "remote_smoke_summary_paths",
            [],
        ),
        "template_remote_smoke_accepted_count": smoke_accepted_count,
        "template_remote_smoke_total_count": smoke_total_count,
        "template_remote_smoke_status": (
            f"accepted_{smoke_accepted_count}_of_{smoke_total_count}"
        ),
        "template_sample_pairs": register_summary.get("sample_pairs", []),
    }
    return frozenset(pair_indexes), evidence


@lru_cache(maxsize=4)
def _opnorm_hconst_default_sandwich_d13vc4_pair_indexes(
    *,
    law_count: int,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_D13VC4_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_D13VC4_REGISTER_SUMMARY
    ),
) -> tuple[frozenset[int], dict[str, object]]:
    pair_index_cache_path = Path(pair_index_cache_path)
    if not pair_index_cache_path.exists():
        raise FileNotFoundError(pair_index_cache_path)

    pair_indexes: set[int] = set()
    duplicate_count = 0
    digest = hashlib.sha256()
    with pair_index_cache_path.open(encoding="ascii") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                pair_index = int(stripped)
            except ValueError as exc:
                raise ValueError(
                    f"invalid pair_index on line {line_number} of "
                    f"{pair_index_cache_path}: {stripped!r}"
                ) from exc
            pair_index_to_ids(pair_index, law_count=law_count)
            if pair_index in pair_indexes:
                duplicate_count += 1
                continue
            pair_indexes.add(pair_index)

    for pair_index in sorted(pair_indexes):
        digest.update(f"{pair_index}\n".encode("ascii"))

    register_summary = _load_optional_json(register_summary_path)
    delta = register_summary.get("delta_against_current_profile_v10", {})
    smoke_accepted_count = register_summary.get("remote_smoke_accepted_count", 90)
    smoke_total_count = register_summary.get("remote_smoke_total_count", 90)
    evidence = {
        "template_family": "opnorm_hconst_default_sandwich_match_collapse_d13vc4",
        "template_verified": True,
        "law_count": law_count,
        "template_pair_count": len(pair_indexes),
        "template_source_shape": register_summary.get("source_shape"),
        "template_target_scope": "d13vc4_d14vc4_and_d23vc4_targets",
        "template_target_shapes": register_summary.get("target_shapes", []),
        "template_target_shape_count": register_summary.get("target_shape_count"),
        "template_source_count": register_summary.get("source_count"),
        "template_shape_counts": register_summary.get("shape_counts", {}),
        "template_hit_stratum_counts": register_summary.get(
            "hit_stratum_counts",
            {},
        ),
        "template_top_source_hit_counts": register_summary.get(
            "top_source_hit_counts",
            [],
        ),
        "template_pair_index_cache_path": str(pair_index_cache_path),
        "template_pair_index_sha256_newline_sorted": digest.hexdigest(),
        "template_duplicate_pair_index_count": duplicate_count,
        "template_current_union_increment": delta.get("union_increment"),
        "template_current_conflict_increment": delta.get("conflict_increment"),
        "template_current_profile": register_summary.get("coverage_profile")
        if register_summary
        else None,
        "template_after_merge_projection_against_current_summary": register_summary.get(
            "after_merge_projection_against_current_summary"
        ),
        "template_register_summary_path": str(register_summary_path),
        "template_source_hits_path": register_summary.get("hits_path"),
        "template_source_hits_paths": register_summary.get("source_hits_paths", []),
        "template_remote_smoke_summary_paths": register_summary.get(
            "remote_smoke_summary_paths",
            [],
        ),
        "template_remote_smoke_accepted_count": smoke_accepted_count,
        "template_remote_smoke_total_count": smoke_total_count,
        "template_remote_smoke_status": (
            f"accepted_{smoke_accepted_count}_of_{smoke_total_count}"
        ),
        "template_sample_pairs": register_summary.get("sample_pairs", []),
    }
    return frozenset(pair_indexes), evidence


@lru_cache(maxsize=4)
def _opnorm_hconst_default_sandwich_d14vc4_targetext_pair_indexes(
    *,
    law_count: int,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_D14VC4_TARGETEXT_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_D14VC4_TARGETEXT_REGISTER_SUMMARY
    ),
) -> tuple[frozenset[int], dict[str, object]]:
    pair_index_cache_path = Path(pair_index_cache_path)
    if not pair_index_cache_path.exists():
        raise FileNotFoundError(pair_index_cache_path)

    pair_indexes: set[int] = set()
    duplicate_count = 0
    digest = hashlib.sha256()
    with pair_index_cache_path.open(encoding="ascii") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                pair_index = int(stripped)
            except ValueError as exc:
                raise ValueError(
                    f"invalid pair_index on line {line_number} of "
                    f"{pair_index_cache_path}: {stripped!r}"
                ) from exc
            pair_index_to_ids(pair_index, law_count=law_count)
            if pair_index in pair_indexes:
                duplicate_count += 1
                continue
            pair_indexes.add(pair_index)

    for pair_index in sorted(pair_indexes):
        digest.update(f"{pair_index}\n".encode("ascii"))

    register_summary = _load_optional_json(register_summary_path)
    delta = register_summary.get("delta_against_current_profile_v11", {})
    smoke_accepted_count = register_summary.get("remote_smoke_accepted_count", 100)
    smoke_total_count = register_summary.get("remote_smoke_total_count", 100)
    evidence = {
        "template_family": (
            "opnorm_hconst_default_sandwich_match_collapse_d14vc4_targetext"
        ),
        "template_verified": True,
        "law_count": law_count,
        "template_pair_count": len(pair_indexes),
        "template_source_shape": register_summary.get("source_shape"),
        "template_target_scope": "d13vc4_d14vc3_d23vc3_and_d13vc3_lm1_targets",
        "template_target_shapes": register_summary.get("target_shapes", []),
        "template_target_shape_count": register_summary.get("target_shape_count"),
        "template_source_count": register_summary.get("source_count"),
        "template_shape_counts": register_summary.get("shape_counts", {}),
        "template_hit_stratum_counts": register_summary.get(
            "hit_stratum_counts",
            {},
        ),
        "template_top_source_hit_counts": register_summary.get(
            "top_source_hit_counts",
            [],
        ),
        "template_pair_index_cache_path": str(pair_index_cache_path),
        "template_pair_index_sha256_newline_sorted": digest.hexdigest(),
        "template_duplicate_pair_index_count": duplicate_count,
        "template_current_union_increment": delta.get("union_increment"),
        "template_current_conflict_increment": delta.get("conflict_increment"),
        "template_current_profile": register_summary.get("coverage_profile")
        if register_summary
        else None,
        "template_after_merge_projection_against_current_summary": register_summary.get(
            "after_merge_projection_against_current_summary"
        ),
        "template_register_summary_path": str(register_summary_path),
        "template_source_hits_path": register_summary.get("hits_path"),
        "template_source_hits_paths": register_summary.get("source_hits_paths", []),
        "template_remote_smoke_summary_paths": register_summary.get(
            "remote_smoke_summary_paths",
            [],
        ),
        "template_remote_smoke_accepted_count": smoke_accepted_count,
        "template_remote_smoke_total_count": smoke_total_count,
        "template_remote_smoke_status": (
            f"accepted_{smoke_accepted_count}_of_{smoke_total_count}"
        ),
        "template_sample_pairs": register_summary.get("sample_pairs", []),
    }
    return frozenset(pair_indexes), evidence


@lru_cache(maxsize=4)
def _opnorm_hconst_default_sandwich_lowvc_extension_pair_indexes(
    *,
    law_count: int,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_LOWVC_EXTENSION_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_LOWVC_EXTENSION_REGISTER_SUMMARY
    ),
) -> tuple[frozenset[int], dict[str, object]]:
    pair_index_cache_path = Path(pair_index_cache_path)
    if not pair_index_cache_path.exists():
        raise FileNotFoundError(pair_index_cache_path)

    pair_indexes: set[int] = set()
    duplicate_count = 0
    digest = hashlib.sha256()
    with pair_index_cache_path.open(encoding="ascii") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                pair_index = int(stripped)
            except ValueError as exc:
                raise ValueError(
                    f"invalid pair_index on line {line_number} of "
                    f"{pair_index_cache_path}: {stripped!r}"
                ) from exc
            pair_index_to_ids(pair_index, law_count=law_count)
            if pair_index in pair_indexes:
                duplicate_count += 1
                continue
            pair_indexes.add(pair_index)

    for pair_index in sorted(pair_indexes):
        digest.update(f"{pair_index}\n".encode("ascii"))

    register_summary = _load_optional_json(register_summary_path)
    delta = register_summary.get("delta_against_current_profile_v12", {})
    smoke_accepted_count = register_summary.get("remote_smoke_accepted_count", 80)
    smoke_total_count = register_summary.get("remote_smoke_total_count", 80)
    evidence = {
        "template_family": (
            "opnorm_hconst_default_sandwich_match_collapse_lowvc_extension"
        ),
        "template_verified": True,
        "law_count": law_count,
        "template_pair_count": len(pair_indexes),
        "template_source_scope": "lowvc_extension_sources",
        "template_source_shapes": register_summary.get("source_shapes", []),
        "template_source_shape_count": register_summary.get("source_shape_count"),
        "template_source_counts_by_shape": register_summary.get(
            "source_counts_by_shape",
            {},
        ),
        "template_target_scope": "lowvc_extension_targets",
        "template_target_shapes": register_summary.get("target_shapes", []),
        "template_target_shape_count": register_summary.get("target_shape_count"),
        "template_shape_counts": register_summary.get("shape_counts", {}),
        "template_hit_stratum_counts": register_summary.get(
            "hit_stratum_counts",
            {},
        ),
        "template_top_source_hit_counts": register_summary.get(
            "top_source_hit_counts",
            [],
        ),
        "template_pair_index_cache_path": str(pair_index_cache_path),
        "template_pair_index_sha256_newline_sorted": digest.hexdigest(),
        "template_duplicate_pair_index_count": duplicate_count,
        "template_current_union_increment": delta.get("union_increment"),
        "template_current_conflict_increment": delta.get("conflict_increment"),
        "template_current_profile": register_summary.get("coverage_profile")
        if register_summary
        else None,
        "template_after_merge_projection_against_current_summary": register_summary.get(
            "after_merge_projection_against_current_summary"
        ),
        "template_register_summary_path": str(register_summary_path),
        "template_source_hits_path": register_summary.get("hits_path"),
        "template_source_hits_paths": register_summary.get("source_hits_paths", []),
        "template_remote_smoke_summary_paths": register_summary.get(
            "remote_smoke_summary_paths",
            [],
        ),
        "template_remote_smoke_accepted_count": smoke_accepted_count,
        "template_remote_smoke_total_count": smoke_total_count,
        "template_remote_smoke_status": (
            f"accepted_{smoke_accepted_count}_of_{smoke_total_count}"
        ),
        "template_sample_pairs": register_summary.get("sample_pairs", []),
    }
    return frozenset(pair_indexes), evidence


@lru_cache(maxsize=4)
def _opnorm_hconst_default_sandwich_topbucket_extension_pair_indexes(
    *,
    law_count: int,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_TOPBUCKET_EXTENSION_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_TOPBUCKET_EXTENSION_REGISTER_SUMMARY
    ),
) -> tuple[frozenset[int], dict[str, object]]:
    pair_index_cache_path = Path(pair_index_cache_path)
    if not pair_index_cache_path.exists():
        raise FileNotFoundError(pair_index_cache_path)

    pair_indexes: set[int] = set()
    duplicate_count = 0
    digest = hashlib.sha256()
    with pair_index_cache_path.open(encoding="ascii") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                pair_index = int(stripped)
            except ValueError as exc:
                raise ValueError(
                    f"invalid pair_index on line {line_number} of "
                    f"{pair_index_cache_path}: {stripped!r}"
                ) from exc
            pair_index_to_ids(pair_index, law_count=law_count)
            if pair_index in pair_indexes:
                duplicate_count += 1
                continue
            pair_indexes.add(pair_index)

    for pair_index in sorted(pair_indexes):
        digest.update(f"{pair_index}\n".encode("ascii"))

    register_summary = _load_optional_json(register_summary_path)
    delta = register_summary.get("delta_against_current_profile_v13", {})
    smoke_accepted_count = register_summary.get("remote_smoke_accepted_count", 80)
    smoke_total_count = register_summary.get("remote_smoke_total_count", 80)
    evidence = {
        "template_family": (
            "opnorm_hconst_default_sandwich_match_collapse_topbucket_extension"
        ),
        "template_verified": True,
        "law_count": law_count,
        "template_pair_count": len(pair_indexes),
        "template_source_scope": "topbucket_extension_sources",
        "template_source_shapes": register_summary.get("source_shapes", []),
        "template_source_shape_count": register_summary.get("source_shape_count"),
        "template_source_counts_by_shape": register_summary.get(
            "source_counts_by_shape",
            {},
        ),
        "template_target_scope": "topbucket_extension_targets",
        "template_target_shapes": register_summary.get("target_shapes", []),
        "template_target_shape_count": register_summary.get("target_shape_count"),
        "template_shape_counts": register_summary.get("shape_counts", {}),
        "template_hit_stratum_counts": register_summary.get(
            "hit_stratum_counts",
            {},
        ),
        "template_top_source_hit_counts": register_summary.get(
            "top_source_hit_counts",
            [],
        ),
        "template_pair_index_cache_path": str(pair_index_cache_path),
        "template_pair_index_sha256_newline_sorted": digest.hexdigest(),
        "template_duplicate_pair_index_count": duplicate_count,
        "template_current_union_increment": delta.get("union_increment"),
        "template_current_conflict_increment": delta.get("conflict_increment"),
        "template_current_profile": register_summary.get("coverage_profile")
        if register_summary
        else None,
        "template_after_merge_projection_against_current_summary": register_summary.get(
            "after_merge_projection_against_current_summary"
        ),
        "template_register_summary_path": str(register_summary_path),
        "template_source_hits_path": register_summary.get("hits_path"),
        "template_source_hits_paths": register_summary.get("source_hits_paths", []),
        "template_remote_smoke_summary_paths": register_summary.get(
            "remote_smoke_summary_paths",
            [],
        ),
        "template_remote_smoke_accepted_count": smoke_accepted_count,
        "template_remote_smoke_total_count": smoke_total_count,
        "template_remote_smoke_status": (
            f"accepted_{smoke_accepted_count}_of_{smoke_total_count}"
        ),
        "template_sample_pairs": register_summary.get("sample_pairs", []),
    }
    return frozenset(pair_indexes), evidence


@lru_cache(maxsize=4)
def _opnorm_hconst_default_sandwich_frontier_extension_pair_indexes(
    *,
    law_count: int,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_FRONTIER_EXTENSION_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_FRONTIER_EXTENSION_REGISTER_SUMMARY
    ),
) -> tuple[frozenset[int], dict[str, object]]:
    pair_index_cache_path = Path(pair_index_cache_path)
    if not pair_index_cache_path.exists():
        raise FileNotFoundError(pair_index_cache_path)

    pair_indexes: set[int] = set()
    duplicate_count = 0
    digest = hashlib.sha256()
    with pair_index_cache_path.open(encoding="ascii") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                pair_index = int(stripped)
            except ValueError as exc:
                raise ValueError(
                    f"invalid pair_index on line {line_number} of "
                    f"{pair_index_cache_path}: {stripped!r}"
                ) from exc
            pair_index_to_ids(pair_index, law_count=law_count)
            if pair_index in pair_indexes:
                duplicate_count += 1
                continue
            pair_indexes.add(pair_index)

    for pair_index in sorted(pair_indexes):
        digest.update(f"{pair_index}\n".encode("ascii"))

    register_summary = _load_optional_json(register_summary_path)
    delta = register_summary.get("delta_against_current_profile_v14", {})
    smoke_accepted_count = register_summary.get("remote_smoke_accepted_count", 90)
    smoke_total_count = register_summary.get("remote_smoke_total_count", 90)
    evidence = {
        "template_family": (
            "opnorm_hconst_default_sandwich_match_collapse_frontier_extension"
        ),
        "template_verified": True,
        "law_count": law_count,
        "template_pair_count": len(pair_indexes),
        "template_source_scope": "frontier_extension_sources",
        "template_source_shapes": register_summary.get("source_shapes", []),
        "template_source_shape_count": register_summary.get("source_shape_count"),
        "template_source_counts_by_shape": register_summary.get(
            "source_counts_by_shape",
            {},
        ),
        "template_target_scope": "frontier_extension_targets",
        "template_target_shapes": register_summary.get("target_shapes", []),
        "template_target_shape_count": register_summary.get("target_shape_count"),
        "template_shape_counts": register_summary.get("shape_counts", {}),
        "template_hit_stratum_counts": register_summary.get(
            "hit_stratum_counts",
            {},
        ),
        "template_top_source_hit_counts": register_summary.get(
            "top_source_hit_counts",
            [],
        ),
        "template_pair_index_cache_path": str(pair_index_cache_path),
        "template_pair_index_sha256_newline_sorted": digest.hexdigest(),
        "template_duplicate_pair_index_count": duplicate_count,
        "template_current_union_increment": delta.get("union_increment"),
        "template_current_conflict_increment": delta.get("conflict_increment"),
        "template_current_profile": register_summary.get("coverage_profile")
        if register_summary
        else None,
        "template_after_merge_projection_against_current_summary": register_summary.get(
            "after_merge_projection_against_current_summary"
        ),
        "template_register_summary_path": str(register_summary_path),
        "template_source_hits_path": register_summary.get("hits_path"),
        "template_source_hits_paths": register_summary.get("source_hits_paths", []),
        "template_remote_smoke_summary_paths": register_summary.get(
            "remote_smoke_summary_paths",
            [],
        ),
        "template_remote_smoke_accepted_count": smoke_accepted_count,
        "template_remote_smoke_total_count": smoke_total_count,
        "template_remote_smoke_status": (
            f"accepted_{smoke_accepted_count}_of_{smoke_total_count}"
        ),
        "template_sample_pairs": register_summary.get("sample_pairs", []),
    }
    return frozenset(pair_indexes), evidence


@lru_cache(maxsize=4)
def _opnorm_hconst_default_sandwich_edge_extension_pair_indexes(
    *,
    law_count: int,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_EDGE_EXTENSION_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_EDGE_EXTENSION_REGISTER_SUMMARY
    ),
) -> tuple[frozenset[int], dict[str, object]]:
    pair_index_cache_path = Path(pair_index_cache_path)
    if not pair_index_cache_path.exists():
        raise FileNotFoundError(pair_index_cache_path)

    pair_indexes: set[int] = set()
    duplicate_count = 0
    digest = hashlib.sha256()
    with pair_index_cache_path.open(encoding="ascii") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                pair_index = int(stripped)
            except ValueError as exc:
                raise ValueError(
                    f"invalid pair_index on line {line_number} of "
                    f"{pair_index_cache_path}: {stripped!r}"
                ) from exc
            pair_index_to_ids(pair_index, law_count=law_count)
            if pair_index in pair_indexes:
                duplicate_count += 1
                continue
            pair_indexes.add(pair_index)

    for pair_index in sorted(pair_indexes):
        digest.update(f"{pair_index}\n".encode("ascii"))

    register_summary = _load_optional_json(register_summary_path)
    delta = register_summary.get("delta_against_current_profile_v15", {})
    smoke_accepted_count = register_summary.get("remote_smoke_accepted_count", 80)
    smoke_total_count = register_summary.get("remote_smoke_total_count", 80)
    evidence = {
        "template_family": (
            "opnorm_hconst_default_sandwich_match_collapse_edge_extension"
        ),
        "template_verified": True,
        "law_count": law_count,
        "template_pair_count": len(pair_indexes),
        "template_source_scope": "edge_extension_sources",
        "template_source_shapes": register_summary.get("source_shapes", []),
        "template_source_shape_count": register_summary.get("source_shape_count"),
        "template_source_counts_by_shape": register_summary.get(
            "source_counts_by_shape",
            {},
        ),
        "template_target_scope": "edge_extension_targets",
        "template_target_shapes": register_summary.get("target_shapes", []),
        "template_target_shape_count": register_summary.get("target_shape_count"),
        "template_shape_counts": register_summary.get("shape_counts", {}),
        "template_hit_stratum_counts": register_summary.get(
            "hit_stratum_counts",
            {},
        ),
        "template_top_source_hit_counts": register_summary.get(
            "top_source_hit_counts",
            [],
        ),
        "template_pair_index_cache_path": str(pair_index_cache_path),
        "template_pair_index_sha256_newline_sorted": digest.hexdigest(),
        "template_duplicate_pair_index_count": duplicate_count,
        "template_current_union_increment": delta.get("union_increment"),
        "template_current_conflict_increment": delta.get("conflict_increment"),
        "template_current_profile": register_summary.get("coverage_profile")
        if register_summary
        else None,
        "template_after_merge_projection_against_current_summary": register_summary.get(
            "after_merge_projection_against_current_summary"
        ),
        "template_register_summary_path": str(register_summary_path),
        "template_source_hits_path": register_summary.get("hits_path"),
        "template_source_hits_paths": register_summary.get("source_hits_paths", []),
        "template_remote_smoke_summary_paths": register_summary.get(
            "remote_smoke_summary_paths",
            [],
        ),
        "template_remote_smoke_accepted_count": smoke_accepted_count,
        "template_remote_smoke_total_count": smoke_total_count,
        "template_remote_smoke_status": (
            f"accepted_{smoke_accepted_count}_of_{smoke_total_count}"
        ),
        "template_sample_pairs": register_summary.get("sample_pairs", []),
    }
    return frozenset(pair_indexes), evidence


@lru_cache(maxsize=4)
def _opnorm_hconst_default_sandwich_postedge_top40_extension_pair_indexes(
    *,
    law_count: int,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE_TOP40_EXTENSION_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE_TOP40_EXTENSION_REGISTER_SUMMARY
    ),
) -> tuple[frozenset[int], dict[str, object]]:
    pair_index_cache_path = Path(pair_index_cache_path)
    if not pair_index_cache_path.exists():
        raise FileNotFoundError(pair_index_cache_path)

    pair_indexes: set[int] = set()
    duplicate_count = 0
    digest = hashlib.sha256()
    with pair_index_cache_path.open(encoding="ascii") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                pair_index = int(stripped)
            except ValueError as exc:
                raise ValueError(
                    f"invalid pair_index on line {line_number} of "
                    f"{pair_index_cache_path}: {stripped!r}"
                ) from exc
            pair_index_to_ids(pair_index, law_count=law_count)
            if pair_index in pair_indexes:
                duplicate_count += 1
                continue
            pair_indexes.add(pair_index)

    for pair_index in sorted(pair_indexes):
        digest.update(f"{pair_index}\n".encode("ascii"))

    register_summary = _load_optional_json(register_summary_path)
    delta = register_summary.get("delta_against_current_profile_v16", {})
    smoke_accepted_count = register_summary.get("remote_smoke_accepted_count", 120)
    smoke_total_count = register_summary.get("remote_smoke_total_count", 120)
    evidence = {
        "template_family": (
            "opnorm_hconst_default_sandwich_match_collapse_postedge_top40_extension"
        ),
        "template_verified": True,
        "law_count": law_count,
        "template_pair_count": len(pair_indexes),
        "template_source_scope": "postedge_top40_extension_sources",
        "template_source_shapes": register_summary.get("source_shapes", []),
        "template_source_shape_count": register_summary.get("source_shape_count"),
        "template_source_counts_by_shape": register_summary.get(
            "source_counts_by_shape",
            {},
        ),
        "template_target_scope": "postedge_top40_extension_targets",
        "template_target_shapes": register_summary.get("target_shapes", []),
        "template_target_shape_count": register_summary.get("target_shape_count"),
        "template_shape_counts": register_summary.get("shape_counts", {}),
        "template_hit_stratum_counts": register_summary.get(
            "hit_stratum_counts",
            {},
        ),
        "template_top_source_hit_counts": register_summary.get(
            "top_source_hit_counts",
            [],
        ),
        "template_pair_index_cache_path": str(pair_index_cache_path),
        "template_pair_index_sha256_newline_sorted": digest.hexdigest(),
        "template_duplicate_pair_index_count": duplicate_count,
        "template_current_union_increment": delta.get("union_increment"),
        "template_current_conflict_increment": delta.get("conflict_increment"),
        "template_current_profile": register_summary.get("coverage_profile")
        if register_summary
        else None,
        "template_after_merge_projection_against_current_summary": register_summary.get(
            "after_merge_projection_against_current_summary"
        ),
        "template_register_summary_path": str(register_summary_path),
        "template_source_hits_path": register_summary.get("hits_path"),
        "template_source_hits_paths": register_summary.get("source_hits_paths", []),
        "template_remote_smoke_summary_paths": register_summary.get(
            "remote_smoke_summary_paths",
            [],
        ),
        "template_remote_smoke_accepted_count": smoke_accepted_count,
        "template_remote_smoke_total_count": smoke_total_count,
        "template_remote_smoke_status": (
            f"accepted_{smoke_accepted_count}_of_{smoke_total_count}"
        ),
        "template_sample_pairs": register_summary.get("sample_pairs", []),
    }
    return frozenset(pair_indexes), evidence


@lru_cache(maxsize=4)
def _opnorm_hconst_default_sandwich_postedge2_top60_extension_pair_indexes(
    *,
    law_count: int,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE2_TOP60_EXTENSION_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE2_TOP60_EXTENSION_REGISTER_SUMMARY
    ),
) -> tuple[frozenset[int], dict[str, object]]:
    pair_index_cache_path = Path(pair_index_cache_path)
    if not pair_index_cache_path.exists():
        raise FileNotFoundError(pair_index_cache_path)

    pair_indexes: set[int] = set()
    duplicate_count = 0
    digest = hashlib.sha256()
    with pair_index_cache_path.open(encoding="ascii") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                pair_index = int(stripped)
            except ValueError as exc:
                raise ValueError(
                    f"invalid pair_index on line {line_number} of "
                    f"{pair_index_cache_path}: {stripped!r}"
                ) from exc
            pair_index_to_ids(pair_index, law_count=law_count)
            if pair_index in pair_indexes:
                duplicate_count += 1
                continue
            pair_indexes.add(pair_index)

    for pair_index in sorted(pair_indexes):
        digest.update(f"{pair_index}\n".encode("ascii"))

    register_summary = _load_optional_json(register_summary_path)
    delta = register_summary.get("delta_against_current_profile_v17", {})
    smoke_accepted_count = register_summary.get("remote_smoke_accepted_count", 120)
    smoke_total_count = register_summary.get("remote_smoke_total_count", 120)
    evidence = {
        "template_family": (
            "opnorm_hconst_default_sandwich_match_collapse_postedge2_top60_extension"
        ),
        "template_verified": True,
        "law_count": law_count,
        "template_pair_count": len(pair_indexes),
        "template_source_scope": "postedge2_top60_extension_sources",
        "template_source_shapes": register_summary.get("source_shapes", []),
        "template_source_shape_count": register_summary.get("source_shape_count"),
        "template_source_counts_by_shape": register_summary.get(
            "source_counts_by_shape",
            {},
        ),
        "template_target_scope": "postedge2_top60_extension_targets",
        "template_target_shapes": register_summary.get("target_shapes", []),
        "template_target_shape_count": register_summary.get("target_shape_count"),
        "template_shape_counts": register_summary.get("shape_counts", {}),
        "template_hit_stratum_counts": register_summary.get(
            "hit_stratum_counts",
            {},
        ),
        "template_top_source_hit_counts": register_summary.get(
            "top_source_hit_counts",
            [],
        ),
        "template_pair_index_cache_path": str(pair_index_cache_path),
        "template_pair_index_sha256_newline_sorted": digest.hexdigest(),
        "template_duplicate_pair_index_count": duplicate_count,
        "template_current_union_increment": delta.get("union_increment"),
        "template_current_conflict_increment": delta.get("conflict_increment"),
        "template_current_profile": register_summary.get("coverage_profile")
        if register_summary
        else None,
        "template_after_merge_projection_against_current_summary": register_summary.get(
            "after_merge_projection_against_current_summary"
        ),
        "template_register_summary_path": str(register_summary_path),
        "template_source_hits_path": register_summary.get("hits_path"),
        "template_source_hits_paths": register_summary.get("source_hits_paths", []),
        "template_remote_smoke_summary_paths": register_summary.get(
            "remote_smoke_summary_paths",
            [],
        ),
        "template_remote_smoke_accepted_count": smoke_accepted_count,
        "template_remote_smoke_total_count": smoke_total_count,
        "template_remote_smoke_status": (
            f"accepted_{smoke_accepted_count}_of_{smoke_total_count}"
        ),
        "template_sample_pairs": register_summary.get("sample_pairs", []),
    }
    return frozenset(pair_indexes), evidence


@lru_cache(maxsize=4)
def _opnorm_hconst_default_sandwich_postedge3_top80_extension_pair_indexes(
    *,
    law_count: int,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE3_TOP80_EXTENSION_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE3_TOP80_EXTENSION_REGISTER_SUMMARY
    ),
) -> tuple[frozenset[int], dict[str, object]]:
    pair_index_cache_path = Path(pair_index_cache_path)
    if not pair_index_cache_path.exists():
        raise FileNotFoundError(pair_index_cache_path)

    pair_indexes: set[int] = set()
    duplicate_count = 0
    digest = hashlib.sha256()
    with pair_index_cache_path.open(encoding="ascii") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                pair_index = int(stripped)
            except ValueError as exc:
                raise ValueError(
                    f"invalid pair_index on line {line_number} of "
                    f"{pair_index_cache_path}: {stripped!r}"
                ) from exc
            pair_index_to_ids(pair_index, law_count=law_count)
            if pair_index in pair_indexes:
                duplicate_count += 1
                continue
            pair_indexes.add(pair_index)

    for pair_index in sorted(pair_indexes):
        digest.update(f"{pair_index}\n".encode("ascii"))

    register_summary = _load_optional_json(register_summary_path)
    delta = register_summary.get("delta_against_current_profile_v18", {})
    smoke_accepted_count = register_summary.get("remote_smoke_accepted_count", 120)
    smoke_total_count = register_summary.get("remote_smoke_total_count", 120)
    evidence = {
        "template_family": (
            "opnorm_hconst_default_sandwich_match_collapse_postedge3_top80_extension"
        ),
        "template_verified": True,
        "law_count": law_count,
        "template_pair_count": len(pair_indexes),
        "template_source_scope": "postedge3_top80_extension_sources",
        "template_source_shapes": register_summary.get("source_shapes", []),
        "template_source_shape_count": register_summary.get("source_shape_count"),
        "template_source_counts_by_shape": register_summary.get(
            "source_counts_by_shape",
            {},
        ),
        "template_target_scope": "postedge3_top80_extension_targets",
        "template_target_shapes": register_summary.get("target_shapes", []),
        "template_target_shape_count": register_summary.get("target_shape_count"),
        "template_shape_counts": register_summary.get("shape_counts", {}),
        "template_hit_stratum_counts": register_summary.get(
            "hit_stratum_counts",
            {},
        ),
        "template_top_source_hit_counts": register_summary.get(
            "top_source_hit_counts",
            [],
        ),
        "template_pair_index_cache_path": str(pair_index_cache_path),
        "template_pair_index_sha256_newline_sorted": digest.hexdigest(),
        "template_duplicate_pair_index_count": duplicate_count,
        "template_current_union_increment": delta.get("union_increment"),
        "template_current_conflict_increment": delta.get("conflict_increment"),
        "template_current_profile": register_summary.get("coverage_profile")
        if register_summary
        else None,
        "template_after_merge_projection_against_current_summary": register_summary.get(
            "after_merge_projection_against_current_summary"
        ),
        "template_register_summary_path": str(register_summary_path),
        "template_source_hits_path": register_summary.get("hits_path"),
        "template_source_hits_paths": register_summary.get("source_hits_paths", []),
        "template_remote_smoke_summary_paths": register_summary.get(
            "remote_smoke_summary_paths",
            [],
        ),
        "template_remote_smoke_accepted_count": smoke_accepted_count,
        "template_remote_smoke_total_count": smoke_total_count,
        "template_remote_smoke_status": (
            f"accepted_{smoke_accepted_count}_of_{smoke_total_count}"
        ),
        "template_sample_pairs": register_summary.get("sample_pairs", []),
    }
    return frozenset(pair_indexes), evidence


@lru_cache(maxsize=4)
def _opnorm_hconst_default_sandwich_postedge4_top100_extension_pair_indexes(
    *,
    law_count: int,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE4_TOP100_EXTENSION_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE4_TOP100_EXTENSION_REGISTER_SUMMARY
    ),
) -> tuple[frozenset[int], dict[str, object]]:
    pair_index_cache_path = Path(pair_index_cache_path)
    if not pair_index_cache_path.exists():
        raise FileNotFoundError(pair_index_cache_path)

    pair_indexes: set[int] = set()
    duplicate_count = 0
    digest = hashlib.sha256()
    with pair_index_cache_path.open(encoding="ascii") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                pair_index = int(stripped)
            except ValueError as exc:
                raise ValueError(
                    f"invalid pair_index on line {line_number} of "
                    f"{pair_index_cache_path}: {stripped!r}"
                ) from exc
            pair_index_to_ids(pair_index, law_count=law_count)
            if pair_index in pair_indexes:
                duplicate_count += 1
                continue
            pair_indexes.add(pair_index)

    for pair_index in sorted(pair_indexes):
        digest.update(f"{pair_index}\n".encode("ascii"))

    register_summary = _load_optional_json(register_summary_path)
    delta = register_summary.get("delta_against_current_profile_v19", {})
    smoke_accepted_count = register_summary.get("remote_smoke_accepted_count", 120)
    smoke_total_count = register_summary.get("remote_smoke_total_count", 120)
    evidence = {
        "template_family": (
            "opnorm_hconst_default_sandwich_match_collapse_postedge4_top100_extension"
        ),
        "template_verified": True,
        "law_count": law_count,
        "template_pair_count": len(pair_indexes),
        "template_source_scope": "postedge4_top100_extension_sources",
        "template_source_shapes": register_summary.get("source_shapes", []),
        "template_source_shape_count": register_summary.get("source_shape_count"),
        "template_source_counts_by_shape": register_summary.get(
            "source_counts_by_shape",
            {},
        ),
        "template_target_scope": "postedge4_top100_extension_targets",
        "template_target_shapes": register_summary.get("target_shapes", []),
        "template_target_shape_count": register_summary.get("target_shape_count"),
        "template_shape_counts": register_summary.get("shape_counts", {}),
        "template_hit_stratum_counts": register_summary.get(
            "hit_stratum_counts",
            {},
        ),
        "template_top_source_hit_counts": register_summary.get(
            "top_source_hit_counts",
            [],
        ),
        "template_pair_index_cache_path": str(pair_index_cache_path),
        "template_pair_index_sha256_newline_sorted": digest.hexdigest(),
        "template_duplicate_pair_index_count": duplicate_count,
        "template_current_union_increment": delta.get("union_increment"),
        "template_current_conflict_increment": delta.get("conflict_increment"),
        "template_current_profile": register_summary.get("coverage_profile")
        if register_summary
        else None,
        "template_after_merge_projection_against_current_summary": register_summary.get(
            "after_merge_projection_against_current_summary"
        ),
        "template_register_summary_path": str(register_summary_path),
        "template_source_hits_path": register_summary.get("hits_path"),
        "template_source_hits_paths": register_summary.get("source_hits_paths", []),
        "template_remote_smoke_summary_paths": register_summary.get(
            "remote_smoke_summary_paths",
            [],
        ),
        "template_remote_smoke_accepted_count": smoke_accepted_count,
        "template_remote_smoke_total_count": smoke_total_count,
        "template_remote_smoke_status": (
            f"accepted_{smoke_accepted_count}_of_{smoke_total_count}"
        ),
        "template_sample_pairs": register_summary.get("sample_pairs", []),
    }
    return frozenset(pair_indexes), evidence


@lru_cache(maxsize=4)
def _opnorm_hconst_default_sandwich_postedge5_top120_extension_pair_indexes(
    *,
    law_count: int,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE5_TOP120_EXTENSION_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE5_TOP120_EXTENSION_REGISTER_SUMMARY
    ),
) -> tuple[frozenset[int], dict[str, object]]:
    pair_index_cache_path = Path(pair_index_cache_path)
    if not pair_index_cache_path.exists():
        raise FileNotFoundError(pair_index_cache_path)

    pair_indexes: set[int] = set()
    duplicate_count = 0
    digest = hashlib.sha256()
    with pair_index_cache_path.open(encoding="ascii") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                pair_index = int(stripped)
            except ValueError as exc:
                raise ValueError(
                    f"invalid pair_index on line {line_number} of "
                    f"{pair_index_cache_path}: {stripped!r}"
                ) from exc
            pair_index_to_ids(pair_index, law_count=law_count)
            if pair_index in pair_indexes:
                duplicate_count += 1
                continue
            pair_indexes.add(pair_index)

    for pair_index in sorted(pair_indexes):
        digest.update(f"{pair_index}\n".encode("ascii"))

    register_summary = _load_optional_json(register_summary_path)
    delta = register_summary.get("delta_against_current_profile_v20", {})
    smoke_accepted_count = register_summary.get("remote_smoke_accepted_count", 120)
    smoke_total_count = register_summary.get("remote_smoke_total_count", 120)
    evidence = {
        "template_family": (
            "opnorm_hconst_default_sandwich_match_collapse_postedge5_top120_extension"
        ),
        "template_verified": True,
        "law_count": law_count,
        "template_pair_count": len(pair_indexes),
        "template_source_scope": "postedge5_top120_extension_sources",
        "template_source_shapes": register_summary.get("source_shapes", []),
        "template_source_shape_count": register_summary.get("source_shape_count"),
        "template_source_counts_by_shape": register_summary.get(
            "source_counts_by_shape",
            {},
        ),
        "template_target_scope": "postedge5_top120_extension_targets",
        "template_target_shapes": register_summary.get("target_shapes", []),
        "template_target_shape_count": register_summary.get("target_shape_count"),
        "template_shape_counts": register_summary.get("shape_counts", {}),
        "template_hit_stratum_counts": register_summary.get(
            "hit_stratum_counts",
            {},
        ),
        "template_top_source_hit_counts": register_summary.get(
            "top_source_hit_counts",
            [],
        ),
        "template_pair_index_cache_path": str(pair_index_cache_path),
        "template_pair_index_sha256_newline_sorted": digest.hexdigest(),
        "template_duplicate_pair_index_count": duplicate_count,
        "template_current_union_increment": delta.get("union_increment"),
        "template_current_conflict_increment": delta.get("conflict_increment"),
        "template_current_profile": register_summary.get("coverage_profile")
        if register_summary
        else None,
        "template_after_merge_projection_against_current_summary": register_summary.get(
            "after_merge_projection_against_current_summary"
        ),
        "template_register_summary_path": str(register_summary_path),
        "template_source_hits_path": register_summary.get("hits_path"),
        "template_source_hits_paths": register_summary.get("source_hits_paths", []),
        "template_remote_smoke_summary_paths": register_summary.get(
            "remote_smoke_summary_paths",
            [],
        ),
        "template_remote_smoke_accepted_count": smoke_accepted_count,
        "template_remote_smoke_total_count": smoke_total_count,
        "template_remote_smoke_status": (
            f"accepted_{smoke_accepted_count}_of_{smoke_total_count}"
        ),
        "template_sample_pairs": register_summary.get("sample_pairs", []),
    }
    return frozenset(pair_indexes), evidence


@lru_cache(maxsize=4)
def _opnorm_hconst_default_sandwich_postedge6_samplehit_top20_tail_pair_indexes(
    *,
    law_count: int,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE6_SAMPLEHIT_TOP20_TAIL_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE6_SAMPLEHIT_TOP20_TAIL_REGISTER_SUMMARY
    ),
) -> tuple[frozenset[int], dict[str, object]]:
    pair_index_cache_path = Path(pair_index_cache_path)
    if not pair_index_cache_path.exists():
        raise FileNotFoundError(pair_index_cache_path)

    pair_indexes: set[int] = set()
    duplicate_count = 0
    digest = hashlib.sha256()
    with pair_index_cache_path.open(encoding="ascii") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                pair_index = int(stripped)
            except ValueError as exc:
                raise ValueError(
                    f"invalid pair_index on line {line_number} of "
                    f"{pair_index_cache_path}: {stripped!r}"
                ) from exc
            pair_index_to_ids(pair_index, law_count=law_count)
            if pair_index in pair_indexes:
                duplicate_count += 1
                continue
            pair_indexes.add(pair_index)

    for pair_index in sorted(pair_indexes):
        digest.update(f"{pair_index}\n".encode("ascii"))

    register_summary = _load_optional_json(register_summary_path)
    delta = register_summary.get("delta_against_current_profile_v22", {})
    smoke_accepted_count = register_summary.get("remote_smoke_accepted_count", 120)
    smoke_total_count = register_summary.get("remote_smoke_total_count", 120)
    evidence = {
        "template_family": (
            "opnorm_hconst_default_sandwich_match_collapse_postedge6_samplehit_top20_tail"
        ),
        "template_verified": True,
        "law_count": law_count,
        "template_pair_count": len(pair_indexes),
        "template_source_scope": "postedge6_samplehit_top20_tail_sources",
        "template_source_shapes": register_summary.get("source_shapes", []),
        "template_source_shape_count": register_summary.get("source_shape_count"),
        "template_source_counts_by_shape": register_summary.get(
            "source_counts_by_shape",
            {},
        ),
        "template_target_scope": "postedge6_samplehit_top20_tail_targets",
        "template_target_shapes": register_summary.get("target_shapes", []),
        "template_target_shape_count": register_summary.get("target_shape_count"),
        "template_shape_counts": register_summary.get("shape_counts", {}),
        "template_hit_stratum_counts": register_summary.get(
            "hit_stratum_counts",
            {},
        ),
        "template_top_source_hit_counts": register_summary.get(
            "top_source_hit_counts",
            [],
        ),
        "template_pair_index_cache_path": str(pair_index_cache_path),
        "template_pair_index_sha256_newline_sorted": digest.hexdigest(),
        "template_duplicate_pair_index_count": duplicate_count,
        "template_current_union_increment": delta.get("union_increment"),
        "template_current_conflict_increment": delta.get("conflict_increment"),
        "template_current_profile": register_summary.get("coverage_profile")
        if register_summary
        else None,
        "template_after_merge_projection_against_current_summary": register_summary.get(
            "after_merge_projection"
        ),
        "template_register_summary_path": str(register_summary_path),
        "template_source_hits_path": register_summary.get("hits_path"),
        "template_source_hits_paths": register_summary.get("source_hits_paths", []),
        "template_remote_smoke_summary_paths": register_summary.get(
            "remote_smoke_summary_paths",
            [],
        ),
        "template_remote_smoke_accepted_count": smoke_accepted_count,
        "template_remote_smoke_total_count": smoke_total_count,
        "template_remote_smoke_status": (
            f"accepted_{smoke_accepted_count}_of_{smoke_total_count}"
        ),
        "template_sample_pairs": register_summary.get("representative_pairs", []),
    }
    return frozenset(pair_indexes), evidence


@lru_cache(maxsize=4)
def _opnorm_hconst_default_sandwich_postedge7_samplehit_top20_tail_pair_indexes(
    *,
    law_count: int,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE7_SAMPLEHIT_TOP20_TAIL_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE7_SAMPLEHIT_TOP20_TAIL_REGISTER_SUMMARY
    ),
) -> tuple[frozenset[int], dict[str, object]]:
    pair_index_cache_path = Path(pair_index_cache_path)
    if not pair_index_cache_path.exists():
        raise FileNotFoundError(pair_index_cache_path)

    pair_indexes: set[int] = set()
    duplicate_count = 0
    digest = hashlib.sha256()
    with pair_index_cache_path.open(encoding="ascii") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                pair_index = int(stripped)
            except ValueError as exc:
                raise ValueError(
                    f"invalid pair_index on line {line_number} of "
                    f"{pair_index_cache_path}: {stripped!r}"
                ) from exc
            pair_index_to_ids(pair_index, law_count=law_count)
            if pair_index in pair_indexes:
                duplicate_count += 1
                continue
            pair_indexes.add(pair_index)

    for pair_index in sorted(pair_indexes):
        digest.update(f"{pair_index}\n".encode("ascii"))

    register_summary = _load_optional_json(register_summary_path)
    delta = register_summary.get("delta_against_current_profile_v23", {})
    smoke_accepted_count = register_summary.get("remote_smoke_accepted_count", 120)
    smoke_total_count = register_summary.get("remote_smoke_total_count", 120)
    evidence = {
        "template_family": (
            "opnorm_hconst_default_sandwich_match_collapse_postedge7_samplehit_top20_tail"
        ),
        "template_verified": True,
        "law_count": law_count,
        "template_pair_count": len(pair_indexes),
        "template_source_scope": "postedge7_samplehit_top20_tail_sources",
        "template_source_shapes": register_summary.get("source_shapes", []),
        "template_source_shape_count": register_summary.get("source_shape_count"),
        "template_source_counts_by_shape": register_summary.get(
            "source_counts_by_shape",
            {},
        ),
        "template_target_scope": "postedge7_samplehit_top20_tail_targets",
        "template_target_shapes": register_summary.get("target_shapes", []),
        "template_target_shape_count": register_summary.get("target_shape_count"),
        "template_shape_counts": register_summary.get("shape_counts", {}),
        "template_hit_stratum_counts": register_summary.get(
            "hit_stratum_counts",
            {},
        ),
        "template_top_source_hit_counts": register_summary.get(
            "top_source_hit_counts",
            [],
        ),
        "template_pair_index_cache_path": str(pair_index_cache_path),
        "template_pair_index_sha256_newline_sorted": digest.hexdigest(),
        "template_duplicate_pair_index_count": duplicate_count,
        "template_current_union_increment": delta.get("union_increment"),
        "template_current_conflict_increment": delta.get("conflict_increment"),
        "template_current_profile": register_summary.get("coverage_profile")
        if register_summary
        else None,
        "template_after_merge_projection_against_current_summary": register_summary.get(
            "after_merge_projection"
        ),
        "template_register_summary_path": str(register_summary_path),
        "template_source_hits_path": register_summary.get("hits_path"),
        "template_source_hits_paths": register_summary.get("source_hits_paths", []),
        "template_remote_smoke_summary_paths": register_summary.get(
            "remote_smoke_summary_paths",
            [],
        ),
        "template_remote_smoke_accepted_count": smoke_accepted_count,
        "template_remote_smoke_total_count": smoke_total_count,
        "template_remote_smoke_status": (
            f"accepted_{smoke_accepted_count}_of_{smoke_total_count}"
        ),
        "template_sample_pairs": register_summary.get("representative_pairs", []),
    }
    return frozenset(pair_indexes), evidence


@lru_cache(maxsize=4)
def _opnorm_hconst_default_sandwich_postedge8_d14vc5_frontier_multitarget20_pair_indexes(
    *,
    law_count: int,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE8_D14VC5_FRONTIER_MULTITARGET20_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE8_D14VC5_FRONTIER_MULTITARGET20_REGISTER_SUMMARY
    ),
) -> tuple[frozenset[int], dict[str, object]]:
    pair_index_cache_path = Path(pair_index_cache_path)
    if not pair_index_cache_path.exists():
        raise FileNotFoundError(pair_index_cache_path)

    pair_indexes: set[int] = set()
    duplicate_count = 0
    digest = hashlib.sha256()
    with pair_index_cache_path.open(encoding="ascii") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                pair_index = int(stripped)
            except ValueError as exc:
                raise ValueError(
                    f"invalid pair_index on line {line_number} of "
                    f"{pair_index_cache_path}: {stripped!r}"
                ) from exc
            pair_index_to_ids(pair_index, law_count=law_count)
            if pair_index in pair_indexes:
                duplicate_count += 1
                continue
            pair_indexes.add(pair_index)

    for pair_index in sorted(pair_indexes):
        digest.update(f"{pair_index}\n".encode("ascii"))

    register_summary = _load_optional_json(register_summary_path)
    delta = register_summary.get("delta_against_current_profile_v24", {})
    smoke_accepted_count = register_summary.get("remote_smoke_accepted_count", 1000)
    smoke_total_count = register_summary.get("remote_smoke_total_count", 1000)
    evidence = {
        "template_family": (
            "opnorm_hconst_default_sandwich_match_collapse_postedge8_d14vc5_frontier_multitarget20"
        ),
        "template_verified": True,
        "law_count": law_count,
        "template_pair_count": len(pair_indexes),
        "template_source_scope": "postedge8_d14vc5_frontier_multitarget20_sources",
        "template_source_shapes": register_summary.get("source_shapes", []),
        "template_source_shape_count": register_summary.get("source_shape_count"),
        "template_source_counts_by_shape": register_summary.get(
            "source_counts_by_shape",
            {},
        ),
        "template_target_scope": (
            "postedge8_d14vc5_frontier_multitarget20_targets"
        ),
        "template_target_shapes": register_summary.get("target_shapes", []),
        "template_target_shape_count": register_summary.get("target_shape_count"),
        "template_shape_counts": register_summary.get("shape_counts", {}),
        "template_hit_stratum_counts": register_summary.get(
            "hit_stratum_counts",
            {},
        ),
        "template_top_source_hit_counts": register_summary.get(
            "top_source_hit_counts",
            [],
        ),
        "template_pair_index_cache_path": str(pair_index_cache_path),
        "template_pair_index_sha256_newline_sorted": digest.hexdigest(),
        "template_duplicate_pair_index_count": duplicate_count,
        "template_current_union_increment": delta.get("union_increment"),
        "template_current_conflict_increment": delta.get("conflict_increment"),
        "template_current_profile": register_summary.get("coverage_profile")
        if register_summary
        else None,
        "template_after_merge_projection_against_current_summary": register_summary.get(
            "after_merge_projection"
        ),
        "template_register_summary_path": str(register_summary_path),
        "template_source_hits_path": register_summary.get("hits_path"),
        "template_source_hits_paths": register_summary.get("source_hits_paths", []),
        "template_remote_smoke_summary_paths": register_summary.get(
            "remote_smoke_summary_paths",
            [],
        ),
        "template_remote_smoke_accepted_count": smoke_accepted_count,
        "template_remote_smoke_total_count": smoke_total_count,
        "template_remote_smoke_status": (
            f"accepted_{smoke_accepted_count}_of_{smoke_total_count}"
        ),
        "template_sample_pairs": register_summary.get("representative_pairs", []),
    }
    return frozenset(pair_indexes), evidence


@lru_cache(maxsize=4)
def _opnorm_hconst_default_sandwich_postedge8_exact_top10_combined_tail_pair_indexes(
    *,
    law_count: int,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE8_EXACT_TOP10_COMBINED_TAIL_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE8_EXACT_TOP10_COMBINED_TAIL_REGISTER_SUMMARY
    ),
) -> tuple[frozenset[int], dict[str, object]]:
    pair_index_cache_path = Path(pair_index_cache_path)
    if not pair_index_cache_path.exists():
        raise FileNotFoundError(pair_index_cache_path)

    pair_indexes: set[int] = set()
    duplicate_count = 0
    digest = hashlib.sha256()
    with pair_index_cache_path.open(encoding="ascii") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                pair_index = int(stripped)
            except ValueError as exc:
                raise ValueError(
                    f"invalid pair_index on line {line_number} of "
                    f"{pair_index_cache_path}: {stripped!r}"
                ) from exc
            pair_index_to_ids(pair_index, law_count=law_count)
            if pair_index in pair_indexes:
                duplicate_count += 1
                continue
            pair_indexes.add(pair_index)

    for pair_index in sorted(pair_indexes):
        digest.update(f"{pair_index}\n".encode("ascii"))

    register_summary = _load_optional_json(register_summary_path)
    delta = register_summary.get("delta_against_current_profile_v25", {})
    smoke_accepted_count = register_summary.get("remote_smoke_accepted_count", 100)
    smoke_total_count = register_summary.get("remote_smoke_total_count", 100)
    evidence = {
        "template_family": (
            "opnorm_hconst_default_sandwich_match_collapse_postedge8_exact_top10_combined_tail"
        ),
        "template_verified": True,
        "law_count": law_count,
        "template_pair_count": len(pair_indexes),
        "template_source_scope": "postedge8_exact_top10_combined_tail_sources",
        "template_source_shapes": register_summary.get("source_shapes", []),
        "template_source_shape_count": register_summary.get("source_shape_count"),
        "template_source_counts_by_shape": register_summary.get(
            "source_counts_by_shape",
            {},
        ),
        "template_target_scope": "postedge8_exact_top10_combined_tail_targets",
        "template_target_shapes": register_summary.get("target_shapes", []),
        "template_target_shape_count": register_summary.get("target_shape_count"),
        "template_shape_counts": register_summary.get("shape_counts", {}),
        "template_hit_stratum_counts": register_summary.get(
            "hit_stratum_counts",
            {},
        ),
        "template_top_source_hit_counts": register_summary.get(
            "top_source_hit_counts",
            [],
        ),
        "template_pair_index_cache_path": str(pair_index_cache_path),
        "template_pair_index_sha256_newline_sorted": digest.hexdigest(),
        "template_duplicate_pair_index_count": duplicate_count,
        "template_current_union_increment": delta.get("union_increment"),
        "template_current_conflict_increment": delta.get("conflict_increment"),
        "template_current_profile": register_summary.get("coverage_profile")
        if register_summary
        else None,
        "template_after_merge_projection_against_current_summary": register_summary.get(
            "after_merge_projection"
        ),
        "template_register_summary_path": str(register_summary_path),
        "template_source_hits_path": register_summary.get("hits_path"),
        "template_source_hits_paths": register_summary.get("source_hits_paths", []),
        "template_remote_smoke_summary_paths": register_summary.get(
            "remote_smoke_summary_paths",
            [],
        ),
        "template_remote_smoke_accepted_count": smoke_accepted_count,
        "template_remote_smoke_total_count": smoke_total_count,
        "template_remote_smoke_status": (
            f"accepted_{smoke_accepted_count}_of_{smoke_total_count}"
        ),
        "template_sample_pairs": register_summary.get("representative_pairs", []),
    }
    return frozenset(pair_indexes), evidence


@lru_cache(maxsize=4)
def _opnorm_hconst_default_sandwich_round30_cumulative_hconst_family_pair_indexes(
    *,
    law_count: int,
    pair_index_cache_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_ROUND30_CUMULATIVE_HCONST_FAMILY_PAIR_INDEX_CACHE
    ),
    register_summary_path: Path = (
        DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_ROUND30_CUMULATIVE_HCONST_FAMILY_REGISTER_SUMMARY
    ),
) -> tuple[frozenset[int], dict[str, object]]:
    pair_index_cache_path = Path(pair_index_cache_path)
    if not pair_index_cache_path.exists():
        raise FileNotFoundError(pair_index_cache_path)

    pair_indexes: set[int] = set()
    duplicate_count = 0
    digest = hashlib.sha256()
    with pair_index_cache_path.open(encoding="ascii") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                pair_index = int(stripped)
            except ValueError as exc:
                raise ValueError(
                    f"invalid pair_index on line {line_number} of "
                    f"{pair_index_cache_path}: {stripped!r}"
                ) from exc
            pair_index_to_ids(pair_index, law_count=law_count)
            if pair_index in pair_indexes:
                duplicate_count += 1
                continue
            pair_indexes.add(pair_index)

    for pair_index in sorted(pair_indexes):
        digest.update(f"{pair_index}\n".encode("ascii"))

    register_summary = _load_optional_json(register_summary_path)
    delta = register_summary.get("current_v26_delta", {})
    pair_index_stats = register_summary.get("pair_index_stats", {})
    remote_smoke_evidence = register_summary.get("remote_smoke_evidence", {})
    remote_smoke = register_summary.get("remote_smoke", {})
    smoke_accepted_count = register_summary.get(
        "remote_smoke_accepted_count",
        remote_smoke.get("accepted_count_total")
        if isinstance(remote_smoke, dict)
        else None,
    )
    smoke_total_count = register_summary.get(
        "remote_smoke_total_count",
        remote_smoke.get("total_count") if isinstance(remote_smoke, dict) else None,
    )
    if smoke_accepted_count is not None and smoke_total_count is not None:
        smoke_status = f"accepted_{smoke_accepted_count}_of_{smoke_total_count}"
    elif remote_smoke_evidence:
        smoke_status = "evidence_recorded"
    else:
        smoke_status = None
    evidence = {
        "template_family": (
            "opnorm_hconst_default_sandwich_match_collapse_round30_cumulative_hconst_family"
        ),
        "template_verified": True,
        "law_count": law_count,
        "template_pair_count": len(pair_indexes),
        "template_source_scope": "round30_cumulative_hconst_family_sources",
        "template_target_scope": "round30_cumulative_hconst_family_targets",
        "template_pair_index_cache_path": str(pair_index_cache_path),
        "template_pair_index_sha256_newline_sorted": digest.hexdigest(),
        "template_duplicate_pair_index_count": duplicate_count,
        "template_current_union_increment": delta.get("union_increment"),
        "template_current_conflict_increment": delta.get("conflict_increment"),
        "template_current_profile": register_summary.get("coverage_profile")
        if register_summary
        else None,
        "template_after_merge_projection_against_current_summary": (
            register_summary.get(
                "after_merge_projection_if_controller_accepts_cumulative_batch"
            )
            or register_summary.get("after_merge_projection")
        ),
        "template_register_summary_path": str(register_summary_path),
        "template_candidate_roots": register_summary.get("candidate_roots", []),
        "template_pair_index_stats": pair_index_stats,
        "template_declared_summary_count": pair_index_stats.get("summary_count"),
        "template_declared_hit_path_count": pair_index_stats.get("hit_path_count"),
        "template_declared_candidate_file_count": pair_index_stats.get(
            "candidate_file_count"
        ),
        "template_missing_pair_index_count": pair_index_stats.get(
            "missing_pair_index_count"
        ),
        "template_remote_smoke_evidence": remote_smoke_evidence,
        "template_remote_smoke": remote_smoke,
        "template_remote_smoke_accepted_count": smoke_accepted_count,
        "template_remote_smoke_total_count": smoke_total_count,
        "template_remote_smoke_status": smoke_status,
    }
    return frozenset(pair_indexes), evidence


def _load_optional_json(path: Path) -> dict:
    path = Path(path)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _opnorm_hconst_match_collapse_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
) -> bool:
    if Path(equations_path).resolve() != DEFAULT_EQ_SIZE5_PATH.resolve():
        return False
    if not DEFAULT_OPNORM_HCONST_MATCH_COLLAPSE_PAIR_INDEX_CACHE.exists():
        return False
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_index = ids_to_pair_index(eq1_id, eq2_id, law_count=law_count)
    pair_indexes, _ = _opnorm_hconst_match_collapse_pair_indexes(
        law_count=law_count,
    )
    return pair_index in pair_indexes


def _opnorm_hconst_sandwich_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
) -> bool:
    if Path(equations_path).resolve() != DEFAULT_EQ_SIZE5_PATH.resolve():
        return False
    if not DEFAULT_OPNORM_HCONST_SANDWICH_PAIR_INDEX_CACHE.exists():
        return False
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_index = ids_to_pair_index(eq1_id, eq2_id, law_count=law_count)
    pair_indexes, _ = _opnorm_hconst_sandwich_pair_indexes(
        law_count=law_count,
    )
    return pair_index in pair_indexes


def _opnorm_hconst_lmrm_mainline_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
) -> bool:
    if Path(equations_path).resolve() != DEFAULT_EQ_SIZE5_PATH.resolve():
        return False
    if not DEFAULT_OPNORM_HCONST_LMRM_MAINLINE_PAIR_INDEX_CACHE.exists():
        return False
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_index = ids_to_pair_index(eq1_id, eq2_id, law_count=law_count)
    pair_indexes, _ = _opnorm_hconst_lmrm_mainline_pair_indexes(
        law_count=law_count,
    )
    return pair_index in pair_indexes


def _opnorm_hconst_varmul_top01_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
) -> bool:
    if Path(equations_path).resolve() != DEFAULT_EQ_SIZE5_PATH.resolve():
        return False
    if not DEFAULT_OPNORM_HCONST_VARMUL_TOP01_PAIR_INDEX_CACHE.exists():
        return False
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_index = ids_to_pair_index(eq1_id, eq2_id, law_count=law_count)
    pair_indexes, _ = _opnorm_hconst_varmul_top01_pair_indexes(
        law_count=law_count,
    )
    return pair_index in pair_indexes


def _opnorm_hconst_default_sandwich_top16_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
) -> bool:
    if Path(equations_path).resolve() != DEFAULT_EQ_SIZE5_PATH.resolve():
        return False
    if not DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_TOP16_PAIR_INDEX_CACHE.exists():
        return False
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_index = ids_to_pair_index(eq1_id, eq2_id, law_count=law_count)
    pair_indexes, _ = _opnorm_hconst_default_sandwich_top16_pair_indexes(
        law_count=law_count,
    )
    return pair_index in pair_indexes


def _opnorm_hconst_default_sandwich_d14vc4_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
) -> bool:
    if Path(equations_path).resolve() != DEFAULT_EQ_SIZE5_PATH.resolve():
        return False
    if not DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_D14VC4_PAIR_INDEX_CACHE.exists():
        return False
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_index = ids_to_pair_index(eq1_id, eq2_id, law_count=law_count)
    pair_indexes, _ = _opnorm_hconst_default_sandwich_d14vc4_pair_indexes(
        law_count=law_count,
    )
    return pair_index in pair_indexes


def _opnorm_hconst_default_sandwich_d13vc4_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
) -> bool:
    if Path(equations_path).resolve() != DEFAULT_EQ_SIZE5_PATH.resolve():
        return False
    if not DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_D13VC4_PAIR_INDEX_CACHE.exists():
        return False
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_index = ids_to_pair_index(eq1_id, eq2_id, law_count=law_count)
    pair_indexes, _ = _opnorm_hconst_default_sandwich_d13vc4_pair_indexes(
        law_count=law_count,
    )
    return pair_index in pair_indexes


def _opnorm_hconst_default_sandwich_d14vc4_targetext_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
) -> bool:
    if Path(equations_path).resolve() != DEFAULT_EQ_SIZE5_PATH.resolve():
        return False
    if not DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_D14VC4_TARGETEXT_PAIR_INDEX_CACHE.exists():
        return False
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_index = ids_to_pair_index(eq1_id, eq2_id, law_count=law_count)
    pair_indexes, _ = _opnorm_hconst_default_sandwich_d14vc4_targetext_pair_indexes(
        law_count=law_count,
    )
    return pair_index in pair_indexes


def _opnorm_hconst_default_sandwich_lowvc_extension_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
) -> bool:
    if Path(equations_path).resolve() != DEFAULT_EQ_SIZE5_PATH.resolve():
        return False
    if not DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_LOWVC_EXTENSION_PAIR_INDEX_CACHE.exists():
        return False
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_index = ids_to_pair_index(eq1_id, eq2_id, law_count=law_count)
    pair_indexes, _ = _opnorm_hconst_default_sandwich_lowvc_extension_pair_indexes(
        law_count=law_count,
    )
    return pair_index in pair_indexes


def _opnorm_hconst_default_sandwich_topbucket_extension_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
) -> bool:
    if Path(equations_path).resolve() != DEFAULT_EQ_SIZE5_PATH.resolve():
        return False
    if not DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_TOPBUCKET_EXTENSION_PAIR_INDEX_CACHE.exists():
        return False
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_index = ids_to_pair_index(eq1_id, eq2_id, law_count=law_count)
    pair_indexes, _ = _opnorm_hconst_default_sandwich_topbucket_extension_pair_indexes(
        law_count=law_count,
    )
    return pair_index in pair_indexes


def _opnorm_hconst_default_sandwich_frontier_extension_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
) -> bool:
    if Path(equations_path).resolve() != DEFAULT_EQ_SIZE5_PATH.resolve():
        return False
    if not DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_FRONTIER_EXTENSION_PAIR_INDEX_CACHE.exists():
        return False
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_index = ids_to_pair_index(eq1_id, eq2_id, law_count=law_count)
    pair_indexes, _ = _opnorm_hconst_default_sandwich_frontier_extension_pair_indexes(
        law_count=law_count,
    )
    return pair_index in pair_indexes


def _opnorm_hconst_default_sandwich_edge_extension_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
) -> bool:
    if Path(equations_path).resolve() != DEFAULT_EQ_SIZE5_PATH.resolve():
        return False
    if not DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_EDGE_EXTENSION_PAIR_INDEX_CACHE.exists():
        return False
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_index = ids_to_pair_index(eq1_id, eq2_id, law_count=law_count)
    pair_indexes, _ = _opnorm_hconst_default_sandwich_edge_extension_pair_indexes(
        law_count=law_count,
    )
    return pair_index in pair_indexes


def _opnorm_hconst_default_sandwich_postedge_top40_extension_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
) -> bool:
    if Path(equations_path).resolve() != DEFAULT_EQ_SIZE5_PATH.resolve():
        return False
    if (
        not DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE_TOP40_EXTENSION_PAIR_INDEX_CACHE.exists()
    ):
        return False
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_index = ids_to_pair_index(eq1_id, eq2_id, law_count=law_count)
    pair_indexes, _ = (
        _opnorm_hconst_default_sandwich_postedge_top40_extension_pair_indexes(
            law_count=law_count,
        )
    )
    return pair_index in pair_indexes


def _opnorm_hconst_default_sandwich_postedge2_top60_extension_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
) -> bool:
    if Path(equations_path).resolve() != DEFAULT_EQ_SIZE5_PATH.resolve():
        return False
    if (
        not DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE2_TOP60_EXTENSION_PAIR_INDEX_CACHE.exists()
    ):
        return False
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_index = ids_to_pair_index(eq1_id, eq2_id, law_count=law_count)
    pair_indexes, _ = (
        _opnorm_hconst_default_sandwich_postedge2_top60_extension_pair_indexes(
            law_count=law_count,
        )
    )
    return pair_index in pair_indexes


def _opnorm_hconst_default_sandwich_postedge3_top80_extension_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
) -> bool:
    if Path(equations_path).resolve() != DEFAULT_EQ_SIZE5_PATH.resolve():
        return False
    if (
        not DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE3_TOP80_EXTENSION_PAIR_INDEX_CACHE.exists()
    ):
        return False
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_index = ids_to_pair_index(eq1_id, eq2_id, law_count=law_count)
    pair_indexes, _ = (
        _opnorm_hconst_default_sandwich_postedge3_top80_extension_pair_indexes(
            law_count=law_count,
        )
    )
    return pair_index in pair_indexes


def _opnorm_hconst_default_sandwich_postedge4_top100_extension_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
) -> bool:
    if Path(equations_path).resolve() != DEFAULT_EQ_SIZE5_PATH.resolve():
        return False
    if (
        not DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE4_TOP100_EXTENSION_PAIR_INDEX_CACHE.exists()
    ):
        return False
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_index = ids_to_pair_index(eq1_id, eq2_id, law_count=law_count)
    pair_indexes, _ = (
        _opnorm_hconst_default_sandwich_postedge4_top100_extension_pair_indexes(
            law_count=law_count,
        )
    )
    return pair_index in pair_indexes


def _opnorm_hconst_default_sandwich_postedge5_top120_extension_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
) -> bool:
    if Path(equations_path).resolve() != DEFAULT_EQ_SIZE5_PATH.resolve():
        return False
    if (
        not DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE5_TOP120_EXTENSION_PAIR_INDEX_CACHE.exists()
    ):
        return False
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_index = ids_to_pair_index(eq1_id, eq2_id, law_count=law_count)
    pair_indexes, _ = (
        _opnorm_hconst_default_sandwich_postedge5_top120_extension_pair_indexes(
            law_count=law_count,
        )
    )
    return pair_index in pair_indexes


def _opnorm_hconst_default_sandwich_postedge6_samplehit_top20_tail_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
) -> bool:
    if Path(equations_path).resolve() != DEFAULT_EQ_SIZE5_PATH.resolve():
        return False
    if (
        not DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE6_SAMPLEHIT_TOP20_TAIL_PAIR_INDEX_CACHE.exists()
    ):
        return False
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_index = ids_to_pair_index(eq1_id, eq2_id, law_count=law_count)
    pair_indexes, _ = (
        _opnorm_hconst_default_sandwich_postedge6_samplehit_top20_tail_pair_indexes(
            law_count=law_count,
        )
    )
    return pair_index in pair_indexes


def _opnorm_hconst_default_sandwich_postedge7_samplehit_top20_tail_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
) -> bool:
    if Path(equations_path).resolve() != DEFAULT_EQ_SIZE5_PATH.resolve():
        return False
    if (
        not DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE7_SAMPLEHIT_TOP20_TAIL_PAIR_INDEX_CACHE.exists()
    ):
        return False
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_index = ids_to_pair_index(eq1_id, eq2_id, law_count=law_count)
    pair_indexes, _ = (
        _opnorm_hconst_default_sandwich_postedge7_samplehit_top20_tail_pair_indexes(
            law_count=law_count,
        )
    )
    return pair_index in pair_indexes


def _opnorm_hconst_default_sandwich_postedge8_d14vc5_frontier_multitarget20_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
) -> bool:
    if Path(equations_path).resolve() != DEFAULT_EQ_SIZE5_PATH.resolve():
        return False
    if (
        not DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE8_D14VC5_FRONTIER_MULTITARGET20_PAIR_INDEX_CACHE.exists()
    ):
        return False
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_index = ids_to_pair_index(eq1_id, eq2_id, law_count=law_count)
    pair_indexes, _ = (
        _opnorm_hconst_default_sandwich_postedge8_d14vc5_frontier_multitarget20_pair_indexes(
            law_count=law_count,
        )
    )
    return pair_index in pair_indexes


def _opnorm_hconst_default_sandwich_postedge8_exact_top10_combined_tail_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
) -> bool:
    if Path(equations_path).resolve() != DEFAULT_EQ_SIZE5_PATH.resolve():
        return False
    if (
        not DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_POSTEDGE8_EXACT_TOP10_COMBINED_TAIL_PAIR_INDEX_CACHE.exists()
    ):
        return False
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_index = ids_to_pair_index(eq1_id, eq2_id, law_count=law_count)
    pair_indexes, _ = (
        _opnorm_hconst_default_sandwich_postedge8_exact_top10_combined_tail_pair_indexes(
            law_count=law_count,
        )
    )
    return pair_index in pair_indexes


def _opnorm_hconst_default_sandwich_round30_cumulative_hconst_family_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
) -> bool:
    if Path(equations_path).resolve() != DEFAULT_EQ_SIZE5_PATH.resolve():
        return False
    if (
        not DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_ROUND30_CUMULATIVE_HCONST_FAMILY_PAIR_INDEX_CACHE.exists()
    ):
        return False
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_index = ids_to_pair_index(eq1_id, eq2_id, law_count=law_count)
    pair_indexes, _ = (
        _opnorm_hconst_default_sandwich_round30_cumulative_hconst_family_pair_indexes(
            law_count=law_count,
        )
    )
    return pair_index in pair_indexes


def _compiler_pair_index_cache_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
    pair_index_cache_path: Path,
    register_summary_path: Path,
    template_family: str,
    template_source_scope: str,
    template_target_scope: str,
) -> bool:
    if Path(equations_path).resolve() != DEFAULT_EQ_SIZE5_PATH.resolve():
        return False
    if not Path(pair_index_cache_path).exists():
        return False
    law_count = len(_cached_parsed_equation_features(equations_path))
    pair_index = ids_to_pair_index(eq1_id, eq2_id, law_count=law_count)
    pair_indexes, _ = _compiler_pair_indexes_from_cache(
        law_count=law_count,
        pair_index_cache_path=pair_index_cache_path,
        register_summary_path=register_summary_path,
        template_family=template_family,
        template_source_scope=template_source_scope,
        template_target_scope=template_target_scope,
    )
    return pair_index in pair_indexes


def _opnorm_hconst_match_ge25k_tail_batch_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
) -> bool:
    return _compiler_pair_index_cache_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
        pair_index_cache_path=DEFAULT_OPNORM_HCONST_MATCH_GE25K_TAIL_BATCH_PAIR_INDEX_CACHE,
        register_summary_path=DEFAULT_OPNORM_HCONST_MATCH_GE25K_TAIL_BATCH_REGISTER_SUMMARY,
        template_family="opnorm_hconst_match_collapse_ge25k_tail_batch",
        template_source_scope="ge25k_tail_batch_sources",
        template_target_scope="ge25k_tail_batch_targets",
    )


def _opnorm_hconst_match_ge10_tail_extension_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
) -> bool:
    return _compiler_pair_index_cache_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
        pair_index_cache_path=DEFAULT_OPNORM_HCONST_MATCH_GE10_TAIL_EXTENSION_PAIR_INDEX_CACHE,
        register_summary_path=DEFAULT_OPNORM_HCONST_MATCH_GE10_TAIL_EXTENSION_REGISTER_SUMMARY,
        template_family="opnorm_hconst_match_collapse_ge10_tail_extension",
        template_source_scope="ge10_tail_extension_sources",
        template_target_scope="ge10_tail_extension_targets",
    )


def _opnorm_hconst_default_sandwich_ge25_lt100_tail_batch_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
) -> bool:
    return _compiler_pair_index_cache_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
        pair_index_cache_path=(
            DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_GE25_LT100_TAIL_BATCH_PAIR_INDEX_CACHE
        ),
        register_summary_path=(
            DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_GE25_LT100_TAIL_BATCH_REGISTER_SUMMARY
        ),
        template_family=(
            "opnorm_hconst_default_sandwich_match_collapse_ge25_lt100_tail_batch"
        ),
        template_source_scope="ge25_lt100_tail_batch_sources",
        template_target_scope="ge25_lt100_tail_batch_targets",
    )


def _opnorm_hconst_default_sandwich_lt25_remaining_tail_batch_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
) -> bool:
    return _compiler_pair_index_cache_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
        pair_index_cache_path=(
            DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_LT25_REMAINING_TAIL_BATCH_PAIR_INDEX_CACHE
        ),
        register_summary_path=(
            DEFAULT_OPNORM_HCONST_DEFAULT_SANDWICH_LT25_REMAINING_TAIL_BATCH_REGISTER_SUMMARY
        ),
        template_family=(
            "opnorm_hconst_default_sandwich_match_collapse_lt25_remaining_tail_batch"
        ),
        template_source_scope="lt25_remaining_tail_batch_sources",
        template_target_scope="lt25_remaining_tail_batch_targets",
    )


def _hinst_ground_cc_accepted_family_rollup_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
) -> bool:
    return _compiler_pair_index_cache_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
        pair_index_cache_path=DEFAULT_HINST_GROUND_CC_ACCEPTED_FAMILY_ROLLUP_PAIR_INDEX_CACHE,
        register_summary_path=DEFAULT_HINST_GROUND_CC_ACCEPTED_FAMILY_ROLLUP_REGISTER_SUMMARY,
        template_family="hinst_ground_cc_accepted_family_rollup",
        template_source_scope="accepted_hinst_ground_cc_family_sources",
        template_target_scope="accepted_hinst_ground_cc_family_targets",
    )


def _opnorm_hconst_plus_hstep_d14vc4_v17_tail_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
) -> bool:
    return _compiler_pair_index_cache_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
        pair_index_cache_path=(
            DEFAULT_OPNORM_HCONST_PLUS_HSTEP_D14VC4_V17_TAIL_PAIR_INDEX_CACHE
        ),
        register_summary_path=(
            DEFAULT_OPNORM_HCONST_PLUS_HSTEP_D14VC4_V17_TAIL_REGISTER_SUMMARY
        ),
        template_family="opnorm_hconst_combined_plus_hstep_default_sandwich_d14vc4_v17_tail",
        template_source_scope="hconst_combined_plus_hstep_d14vc4_v17_tail_sources",
        template_target_scope="hconst_combined_plus_hstep_d14vc4_v17_tail_targets",
    )


def _one_sided_constancy_recursive_nf_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
    candidate_key_fragment: str,
) -> bool:
    if eq1_id == eq2_id:
        return False
    if Path(equations_path).resolve() != DEFAULT_EQ_SIZE5_PATH.resolve():
        return False
    if (
        not DEFAULT_PROOFBENCH_ONE_SIDED_CONSTANCY_EXPLICIT_NF_ACCEPTED_CANDIDATE_JSONL.exists()
    ):
        return False
    row = _proofbench_one_sided_constancy_row(
        candidate_jsonl_path=(
            DEFAULT_PROOFBENCH_ONE_SIDED_CONSTANCY_EXPLICIT_NF_ACCEPTED_CANDIDATE_JSONL
        ),
        candidate_key_fragment=candidate_key_fragment,
    )
    source_ids = _candidate_id_set(row, "source_ids")
    target_ids = _candidate_id_set(row, "target_ids")
    return eq1_id in source_ids and eq2_id in target_ids


def _one_sided_constancy_row_recursive_nf_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
) -> bool:
    return _one_sided_constancy_recursive_nf_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
        candidate_key_fragment="rhs_omits_right_arg.row_constancy_recursive_nf",
    )


def _one_sided_constancy_column_recursive_nf_registered_pair(
    eq1_id: int,
    eq2_id: int,
    *,
    equations_path: Path,
) -> bool:
    return _one_sided_constancy_recursive_nf_registered_pair(
        eq1_id,
        eq2_id,
        equations_path=equations_path,
        candidate_key_fragment="rhs_omits_left_arg.column_constancy_recursive_nf",
    )


def _target_instance_source_ids(
    target: Equation,
    source_id_by_signature: dict[str, int],
) -> frozenset[int]:
    signatures = _target_instance_generalization_signatures(
        target.left.to_tuple(),
        target.right.to_tuple(),
    )
    return frozenset(
        source_id_by_signature[signature]
        for signature in signatures
        if signature in source_id_by_signature
    )


@lru_cache(maxsize=None)
def _target_instance_generalization_signatures(
    left_tuple: tuple,
    right_tuple: tuple,
) -> frozenset[str]:
    signatures: set[str] = set()
    for left_form in _target_instance_generalization_forms(left_tuple):
        for right_form in _target_instance_generalization_forms(right_tuple):
            occurrence_keys: list[tuple] = []
            _collect_generalization_variable_occurrences(left_form, occurrence_keys)
            _collect_generalization_variable_occurrences(right_form, occurrence_keys)
            groups: dict[tuple, list[int]] = {}
            for index, key in enumerate(occurrence_keys):
                groups.setdefault(key, []).append(index)
            group_items = list(groups.items())
            partition_choices = [
                _canonical_partitions(len(positions))
                for _, positions in group_items
            ]
            for partition_combo in product(*partition_choices):
                occurrence_classes: list[tuple[int, int] | None] = [
                    None
                ] * len(occurrence_keys)
                for group_index, ((_, positions), partition) in enumerate(
                    zip(group_items, partition_combo)
                ):
                    for local_index, occurrence_index in enumerate(positions):
                        occurrence_classes[occurrence_index] = (
                            group_index,
                            partition[local_index],
                        )
                signatures.add(
                    _encode_generalization_signature(
                        left_form,
                        right_form,
                        tuple(occurrence_classes),
                    )
                )
    return frozenset(signatures)


@lru_cache(maxsize=None)
def _target_instance_generalization_forms(expr_tuple: tuple) -> tuple[tuple, ...]:
    if expr_tuple[0] == "var":
        return (("var_pattern", expr_tuple),)
    _, left, right = expr_tuple
    forms: list[tuple] = [("var_pattern", expr_tuple)]
    for left_form in _target_instance_generalization_forms(left):
        for right_form in _target_instance_generalization_forms(right):
            forms.append(("mul_pattern", left_form, right_form))
    return tuple(forms)


@lru_cache(maxsize=None)
def _canonical_partitions(size: int) -> tuple[tuple[int, ...], ...]:
    if size == 0:
        return ((),)
    partitions: list[tuple[int, ...]] = []

    def visit(index: int, labels: list[int], max_label: int) -> None:
        if index == size:
            partitions.append(tuple(labels))
            return
        for label in range(max_label + 2):
            labels.append(label)
            visit(index + 1, labels, max(max_label, label))
            labels.pop()

    visit(0, [], -1)
    return tuple(partitions)


def _collect_generalization_variable_occurrences(
    form: tuple,
    occurrence_keys: list[tuple],
) -> None:
    if form[0] == "var_pattern":
        occurrence_keys.append(form[1])
        return
    _collect_generalization_variable_occurrences(form[1], occurrence_keys)
    _collect_generalization_variable_occurrences(form[2], occurrence_keys)


def _encode_generalization_signature(
    left_form: tuple,
    right_form: tuple,
    occurrence_classes: tuple[tuple[int, int] | None, ...],
) -> str:
    occurrence_index = 0
    class_to_variable: dict[tuple[int, int], str] = {}

    def encode(form: tuple) -> str:
        nonlocal occurrence_index
        if form[0] == "var_pattern":
            variable_class = occurrence_classes[occurrence_index]
            occurrence_index += 1
            assert variable_class is not None
            if variable_class not in class_to_variable:
                class_to_variable[variable_class] = f"v{len(class_to_variable)}"
            return class_to_variable[variable_class]
        return f"({encode(form[1])}*{encode(form[2])})"

    return f"{encode(left_form)}={encode(right_form)}"


def _integer_quantiles(values: Sequence[int]) -> dict[str, int]:
    if not values:
        return {}
    sorted_values = sorted(values)
    return {
        "p50": sorted_values[int((len(sorted_values) - 1) * 0.50)],
        "p90": sorted_values[int((len(sorted_values) - 1) * 0.90)],
        "p99": sorted_values[int((len(sorted_values) - 1) * 0.99)],
        "max": sorted_values[-1],
    }


def spine_left_zero_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": spine_left_zero_false_judge_code(),
    }


def spine_left_zero_false_judge_code() -> str:
    return finmodel_false_judge_code(LEFT_PROJECTION_2_TABLE)


def constant_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": constant_false_judge_code(),
    }


def constant_false_judge_code() -> str:
    return finmodel_false_judge_code(CONSTANT_2_TABLE)


def right_projection_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": right_projection_false_judge_code(),
    }


def right_projection_false_judge_code() -> str:
    return finmodel_false_judge_code(RIGHT_PROJECTION_2_TABLE)


def complement_left_projection_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": complement_left_projection_false_judge_code(),
    }


def complement_left_projection_false_judge_code() -> str:
    return finmodel_false_judge_code(COMPLEMENT_LEFT_PROJECTION_2_TABLE)


def complement_right_projection_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": complement_right_projection_false_judge_code(),
    }


def complement_right_projection_false_judge_code() -> str:
    return finmodel_false_judge_code(COMPLEMENT_RIGHT_PROJECTION_2_TABLE)


def left_and_complement_right_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": left_and_complement_right_false_judge_code(),
    }


def left_and_complement_right_false_judge_code() -> str:
    return finmodel_false_judge_code(LEFT_AND_COMPLEMENT_RIGHT_2_TABLE)


def complement_left_and_right_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": complement_left_and_right_false_judge_code(),
    }


def complement_left_and_right_false_judge_code() -> str:
    return finmodel_false_judge_code(COMPLEMENT_LEFT_AND_RIGHT_2_TABLE)


def xor_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": xor_false_judge_code(),
    }


def xor_false_judge_code() -> str:
    return finmodel_false_judge_code(XOR_2_TABLE)


def and_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": and_false_judge_code(),
    }


def and_false_judge_code() -> str:
    return finmodel_false_judge_code(AND_2_TABLE)


def nor_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": nor_false_judge_code(),
    }


def nor_false_judge_code() -> str:
    return finmodel_false_judge_code(NOR_2_TABLE)


def steiner_quasigroup_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": steiner_quasigroup_false_judge_code(),
    }


def steiner_quasigroup_false_judge_code() -> str:
    return finmodel_false_judge_code(STEINER_QUASIGROUP_3_TABLE)


def right_minus_left_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": right_minus_left_false_judge_code(),
    }


def right_minus_left_false_judge_code() -> str:
    return finmodel_false_judge_code(RIGHT_MINUS_LEFT_3_TABLE)


def left_minus_right_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": left_minus_right_false_judge_code(),
    }


def left_minus_right_false_judge_code() -> str:
    return finmodel_false_judge_code(LEFT_MINUS_RIGHT_3_TABLE)


def fin3_table_020_110_122_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": fin3_table_020_110_122_false_judge_code(),
    }


def fin3_table_020_110_122_false_judge_code() -> str:
    return finmodel_false_judge_code(FIN3_TABLE_020_110_122_TABLE)


def left_cyclic_successor_n3_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": left_cyclic_successor_n3_false_judge_code(),
    }


def left_cyclic_successor_n3_false_judge_code() -> str:
    return finmodel_false_judge_code(LEFT_CYCLIC_SUCCESSOR_3_TABLE)


def right_cyclic_successor_n3_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": right_cyclic_successor_n3_false_judge_code(),
    }


def right_cyclic_successor_n3_false_judge_code() -> str:
    return finmodel_false_judge_code(RIGHT_CYCLIC_SUCCESSOR_3_TABLE)


def fin3_table_022_010_112_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": fin3_table_022_010_112_false_judge_code(),
    }


def fin3_table_022_010_112_false_judge_code() -> str:
    return finmodel_false_judge_code(FIN3_TABLE_022_010_112_TABLE)


def addition_mod3_n3_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": addition_mod3_n3_false_judge_code(),
    }


def addition_mod3_n3_false_judge_code() -> str:
    return finmodel_false_judge_code(ADDITION_MOD3_3_TABLE)


def fin4_table_0231_3102_1320_2013_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": fin4_table_0231_3102_1320_2013_false_judge_code(),
    }


def fin4_table_0231_3102_1320_2013_false_judge_code() -> str:
    return finmodel_false_judge_code(FIN4_TABLE_0231_3102_1320_2013_TABLE)


def fin3_table_000_211_122_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": fin3_table_000_211_122_false_judge_code(),
    }


def fin3_table_000_211_122_false_judge_code() -> str:
    return finmodel_false_judge_code(FIN3_TABLE_000_211_122_TABLE)


def fin3_table_012_012_102_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": fin3_table_012_012_102_false_judge_code(),
    }


def fin3_table_012_012_102_false_judge_code() -> str:
    return finmodel_false_judge_code(FIN3_TABLE_012_012_102_TABLE)


def fin3_table_011_012_012_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": fin3_table_011_012_012_false_judge_code(),
    }


def fin3_table_011_012_012_false_judge_code() -> str:
    return finmodel_false_judge_code(FIN3_TABLE_011_012_012_TABLE)


def fin3_table_000_110_222_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": fin3_table_000_110_222_false_judge_code(),
    }


def fin3_table_000_110_222_false_judge_code() -> str:
    return finmodel_false_judge_code(FIN3_TABLE_000_110_222_TABLE)


def fin3_table_122_020_110_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": fin3_table_122_020_110_false_judge_code(),
    }


def fin3_table_122_020_110_false_judge_code() -> str:
    return finmodel_false_judge_code(FIN3_TABLE_122_020_110_TABLE)


def fin3_table_002_112_102_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": fin3_table_002_112_102_false_judge_code(),
    }


def fin3_table_002_112_102_false_judge_code() -> str:
    return finmodel_false_judge_code(FIN3_TABLE_002_112_102_TABLE)


def fin3_table_011_012_110_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": fin3_table_011_012_110_false_judge_code(),
    }


def fin3_table_011_012_110_false_judge_code() -> str:
    return finmodel_false_judge_code(FIN3_TABLE_011_012_110_TABLE)


def fin4_table_2013_3102_0231_1320_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": fin4_table_2013_3102_0231_1320_false_judge_code(),
    }


def fin4_table_2013_3102_0231_1320_false_judge_code() -> str:
    return finmodel_false_judge_code(FIN4_TABLE_2013_3102_0231_1320_TABLE)


def fin4_table_0011_2233_0011_2233_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": fin4_table_0011_2233_0011_2233_false_judge_code(),
    }


def fin4_table_0011_2233_0011_2233_false_judge_code() -> str:
    return finmodel_false_judge_code(FIN4_TABLE_0011_2233_0011_2233_TABLE)


def fin5_table_02413_41302_30241_24130_13024_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": fin5_table_02413_41302_30241_24130_13024_false_judge_code(),
    }


def fin5_table_02413_41302_30241_24130_13024_false_judge_code() -> str:
    return finmodel_false_judge_code(FIN5_TABLE_02413_41302_30241_24130_13024_TABLE)


def fin5_table_03142_31420_14203_42031_20314_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": fin5_table_03142_31420_14203_42031_20314_false_judge_code(),
    }


def fin5_table_03142_31420_14203_42031_20314_false_judge_code() -> str:
    return finmodel_false_judge_code(FIN5_TABLE_03142_31420_14203_42031_20314_TABLE)


def fin5_table_02143_41320_34201_10432_23014_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": fin5_table_02143_41320_34201_10432_23014_false_judge_code(),
    }


def fin5_table_02143_41320_34201_10432_23014_false_judge_code() -> str:
    return finmodel_false_judge_code(FIN5_TABLE_02143_41320_34201_10432_23014_TABLE)


def fin7_table_0214365_3150624_4625031_6543210_5361402_2406153_1032546_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": fin7_table_0214365_3150624_4625031_6543210_5361402_2406153_1032546_false_judge_code(),
    }


def fin7_table_0214365_3150624_4625031_6543210_5361402_2406153_1032546_false_judge_code() -> str:
    return finmodel_false_judge_code(
        FIN7_TABLE_0214365_3150624_4625031_6543210_5361402_2406153_1032546_TABLE
    )


def fin5_table_31420_02341_14032_40213_23104_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": fin5_table_31420_02341_14032_40213_23104_false_judge_code(),
    }


def fin5_table_31420_02341_14032_40213_23104_false_judge_code() -> str:
    return finmodel_false_judge_code(FIN5_TABLE_31420_02341_14032_40213_23104_TABLE)


def fin5_table_34120_20413_01234_13042_42301_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": fin5_table_34120_20413_01234_13042_42301_false_judge_code(),
    }


def fin5_table_34120_20413_01234_13042_42301_false_judge_code() -> str:
    return finmodel_false_judge_code(FIN5_TABLE_34120_20413_01234_13042_42301_TABLE)


def fin4_table_1032_3210_2301_0123_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": fin4_table_1032_3210_2301_0123_false_judge_code(),
    }


def fin4_table_1032_3210_2301_0123_false_judge_code() -> str:
    return finmodel_false_judge_code(FIN4_TABLE_1032_3210_2301_0123_TABLE)


def fin3_table_000_000_001_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": fin3_table_000_000_001_false_judge_code(),
    }


def fin3_table_000_000_001_false_judge_code() -> str:
    return finmodel_false_judge_code(FIN3_TABLE_000_000_001_TABLE)


def fin3_table_000_000_010_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": fin3_table_000_000_010_false_judge_code(),
    }


def fin3_table_000_000_010_false_judge_code() -> str:
    return finmodel_false_judge_code(FIN3_TABLE_000_000_010_TABLE)


def fin3_table_000_000_020_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": fin3_table_000_000_020_false_judge_code(),
    }


def fin3_table_000_000_020_false_judge_code() -> str:
    return finmodel_false_judge_code(FIN3_TABLE_000_000_020_TABLE)


def fin3_table_000_000_100_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": fin3_table_000_000_100_false_judge_code(),
    }


def fin3_table_000_000_100_false_judge_code() -> str:
    return finmodel_false_judge_code(FIN3_TABLE_000_000_100_TABLE)


def fin3_table_001_000_000_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": fin3_table_001_000_000_false_judge_code(),
    }


def fin3_table_001_000_000_false_judge_code() -> str:
    return finmodel_false_judge_code(FIN3_TABLE_001_000_000_TABLE)


def fin3_table_000_000_011_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": fin3_table_000_000_011_false_judge_code(),
    }


def fin3_table_000_000_011_false_judge_code() -> str:
    return finmodel_false_judge_code(FIN3_TABLE_000_000_011_TABLE)


def fin3_table_000_001_001_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": fin3_table_000_001_001_false_judge_code(),
    }


def fin3_table_000_001_001_false_judge_code() -> str:
    return finmodel_false_judge_code(FIN3_TABLE_000_001_001_TABLE)


def fin3_table_000_001_010_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": fin3_table_000_001_010_false_judge_code(),
    }


def fin3_table_000_001_010_false_judge_code() -> str:
    return finmodel_false_judge_code(FIN3_TABLE_000_001_010_TABLE)


def fin3_table_000_020_001_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": fin3_table_000_020_001_false_judge_code(),
    }


def fin3_table_000_020_001_false_judge_code() -> str:
    return finmodel_false_judge_code(FIN3_TABLE_000_020_001_TABLE)


def fin3_table_000_122_122_false_judge_answer() -> dict:
    return {
        "verdict": "false",
        "code": fin3_table_000_122_122_false_judge_code(),
    }


def fin3_table_000_122_122_false_judge_code() -> str:
    return finmodel_false_judge_code(FIN3_TABLE_000_122_122_TABLE)


def finmodel_false_judge_code(table: tuple[tuple[int, ...], ...]) -> str:
    if len(table) >= 10:
        return _finmodel_false_judge_code_direct_match(table)
    table_json = json.dumps([list(row) for row in table])
    order = len(table)
    return (
        "import JudgeProblem\n"
        "import JudgeDecide.DecideBang\n"
        "import JudgeFinOp.MemoFinOp\n"
        "set_option maxRecDepth 1000000\n"
        "open MemoFinOp\n\n"
        "def submission : Goal := by\n"
        f"  let m : Magma (Fin {order}) := {{\n"
        f"    op := finOpTable \"{table_json}\"\n"
        "  }\n"
        f"  refine ⟨Fin {order}, m, ?_⟩\n"
        "  decideFin!\n"
    )


def _finmodel_false_judge_code_direct_match(table: tuple[tuple[int, ...], ...]) -> str:
    order = len(table)
    lines = [
        "import JudgeProblem",
        "import JudgeDecide.DecideBang",
        "set_option maxRecDepth 1000000",
        "set_option maxHeartbeats 0",
        "",
        "def submission : Goal := by",
        f"  let m : Magma (Fin {order}) := {{",
        "    op := fun i j =>",
        "      match i.val, j.val with",
    ]
    for row_index, row in enumerate(table):
        for column_index, value in enumerate(row):
            lines.append(f"      | {row_index}, {column_index} => ({value} : Fin {order})")
    lines.extend(
        [
            f"      | _, _ => (0 : Fin {order})",
            "  }",
            f"  refine ⟨Fin {order}, m, ?_⟩",
            "  decideFin!",
            "",
        ]
    )
    return "\n".join(lines)


def _finmodel_sets(
    equations_path: Path,
    table: tuple[tuple[int, ...], ...],
) -> tuple[list, frozenset[int], frozenset[int]]:
    parsed_features = _cached_parsed_equation_features(equations_path)
    features = [feature for feature, _ in parsed_features]
    if _ACTIVE_FINMODEL_SOURCE_TARGET_CACHE is not None:
        cached = _ACTIVE_FINMODEL_SOURCE_TARGET_CACHE.get(
            table,
            parsed_features,
            update=_ACTIVE_FINMODEL_SOURCE_TARGET_CACHE_UPDATE,
        )
        if cached is not None:
            source_ids, target_ids = cached
            return features, source_ids, target_ids
    source_ids, target_ids = _scan_finmodel_source_target_sets(table, parsed_features)
    return features, source_ids, target_ids


def _scan_finmodel_source_target_sets(
    table: tuple[tuple[int, ...], ...],
    parsed_features: Sequence[tuple[object, Equation]],
) -> tuple[frozenset[int], frozenset[int]]:
    magma = FiniteMagma(order=len(table), table=table)
    sources: set[int] = set()
    targets: set[int] = set()
    for feature, equation in parsed_features:
        if magma.satisfies(equation):
            sources.add(feature.equation_id)
        else:
            targets.add(feature.equation_id)
    return frozenset(sources), frozenset(targets)


def _target_ids_from_sources(
    source_ids: frozenset[int],
    *,
    law_count: int,
) -> frozenset[int]:
    return frozenset(eq_id for eq_id in range(1, law_count + 1) if eq_id not in source_ids)


def _encode_ids_bitset(ids: Iterable[int], *, law_count: int) -> str:
    raw = bytearray((law_count + 7) // 8)
    for eq_id in ids:
        if eq_id < 1 or eq_id > law_count:
            raise ValueError(f"eq_id must be in [1, {law_count}]; got {eq_id}")
        bit_index = eq_id - 1
        raw[bit_index // 8] |= 1 << (bit_index % 8)
    return base64.b64encode(bytes(raw)).decode("ascii")


def _decode_ids_bitset(payload: str, *, law_count: int) -> frozenset[int]:
    raw = base64.b64decode(payload.encode("ascii"))
    expected_length = (law_count + 7) // 8
    if len(raw) != expected_length:
        raise ValueError(
            f"source bitset must have {expected_length} bytes; got {len(raw)}"
        )
    return frozenset(
        eq_id
        for eq_id in range(1, law_count + 1)
        if raw[(eq_id - 1) // 8] & (1 << ((eq_id - 1) % 8))
    )


def _normalize_table(raw_table: object) -> tuple[tuple[int, ...], ...]:
    if not isinstance(raw_table, list) or not raw_table:
        raise ValueError("magma table must be a non-empty nested list")
    order = len(raw_table)
    table: list[tuple[int, ...]] = []
    for row in raw_table:
        if not isinstance(row, list) or len(row) != order:
            raise ValueError("magma table must be square")
        normalized_row: list[int] = []
        for value in row:
            if not isinstance(value, int) or value < 0 or value >= order:
                raise ValueError("magma table entries must be integers in [0, order)")
            normalized_row.append(value)
        table.append(tuple(normalized_row))
    return tuple(table)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _singleton_collapse_sets(
    equations_path: Path,
) -> tuple[list, frozenset[int], frozenset[int], dict[str, int]]:
    parsed_features = _cached_parsed_equation_features(equations_path)
    features = [feature for feature, _ in parsed_features]
    sources: set[int] = set()
    direction_counts = {"left": 0, "right": 0}
    for feature, equation in parsed_features:
        shape = _singleton_collapse_shape(equation)
        if shape is None:
            continue
        side, _ = shape
        sources.add(feature.equation_id)
        direction_counts[side] += 1
    targets = frozenset(feature.equation_id for feature in features)
    return features, frozenset(sources), targets, direction_counts


def _product_anchor_sets(
    equations_path: Path,
) -> tuple[list, frozenset[int], frozenset[int], dict[str, int]]:
    parsed_features = _cached_parsed_equation_features(equations_path)
    features = [feature for feature, _ in parsed_features]
    sources: set[int] = set()
    targets: set[int] = set()
    direction_counts = {"left": 0, "right": 0}
    for feature, equation in parsed_features:
        shape = _product_anchor_shape(equation)
        if shape is not None:
            side, _, _ = shape
            sources.add(feature.equation_id)
            direction_counts[side] += 1
        if _is_product_root_target(equation):
            targets.add(feature.equation_id)
    return features, frozenset(sources), frozenset(targets), direction_counts


def _product_anchor_seed_lift_sets(
    equations_path: Path,
    *,
    candidate_jsonl_path: Path = DEFAULT_PRODUCT_ANCHOR_SEED_LIFT_CANDIDATE_JSONL,
) -> tuple[list, frozenset[int], frozenset[int], dict[str, object]]:
    parsed_features = _cached_parsed_equation_features(equations_path)
    features = [feature for feature, _ in parsed_features]
    records = _load_product_anchor_seed_lift_proofs(candidate_jsonl_path)
    source_signatures = _product_anchor_seed_lift_source_signatures(
        equations_path,
        candidate_jsonl_path,
    )
    sources = frozenset(source_signatures)
    mismatches = tuple(sorted(set(records) - set(sources)))
    _, _, target_ids, _ = _product_anchor_sets(equations_path)
    counts: dict[str, object] = {
        "candidate_source_count": len(records),
        "source_signature_mismatch_count": len(mismatches),
        "source_signature_mismatch_ids": list(mismatches),
        "seed_product_anchor_source_ids": [
            int(records[source_id]["seed_product_anchor_source_id"])
            for source_id in sorted(sources)
            if records[source_id].get("seed_product_anchor_source_id") is not None
        ],
        "proof_body_sha256_by_source_id": {
            str(source_id): str(records[source_id]["proof_body_sha256"])
            for source_id in sorted(sources)
            if records[source_id].get("proof_body_sha256")
        },
    }
    return features, sources, target_ids, counts


def _product_collapse_sets(
    equations_path: Path,
    *,
    term_pattern: str,
) -> tuple[list, frozenset[int], frozenset[int], dict[str, int]]:
    parsed_features = _cached_parsed_equation_features(equations_path)
    features = [feature for feature, _ in parsed_features]
    pattern = _parse_product_collapse_pattern(term_pattern)
    sources: set[int] = set()
    targets: set[int] = set()
    side_counts = {"left": 0, "right": 0}
    for feature, equation in parsed_features:
        source_shapes = _product_collapse_source_shapes(equation, pattern)
        if source_shapes:
            sources.add(feature.equation_id)
            for shape in source_shapes:
                side_counts[str(shape["side"])] += 1
        if _product_collapse_target_matches(equation, pattern):
            targets.add(feature.equation_id)
    return features, frozenset(sources), frozenset(targets), side_counts


def _projection_normalizer_sets(
    equations_path: Path,
    *,
    side: str,
) -> tuple[list, frozenset[int], frozenset[int], dict[str, int]]:
    parsed_features = _cached_parsed_equation_features(equations_path)
    features = [feature for feature, _ in parsed_features]
    sources: set[int] = set()
    targets: set[int] = set()
    source_counts = {"var_eq_product": 0, "product_eq_var": 0}
    for feature, equation in parsed_features:
        shape = _projection_normalizer_source_shape(equation, side=side)
        if shape is not None:
            sources.add(feature.equation_id)
            key = "var_eq_product" if shape["var_eq_product"] else "product_eq_var"
            source_counts[key] += 1
        if _is_projection_normal_target(equation, side=side):
            targets.add(feature.equation_id)
    return features, frozenset(sources), frozenset(targets), source_counts


def _law_instance_sets(
    equations_path: Path,
    law: Equation,
) -> tuple[list, frozenset[int], frozenset[int], dict[str, int]]:
    parsed_features = _cached_parsed_equation_features(equations_path)
    features = [feature for feature, _ in parsed_features]
    sources: set[int] = set()
    targets: set[int] = set()
    counts = {
        "source_direct": 0,
        "source_symm": 0,
        "target_direct": 0,
        "target_symm": 0,
    }
    for feature, equation in parsed_features:
        source_match = _match_law_instance_source(equation, law)
        if source_match is not None:
            sources.add(feature.equation_id)
            counts[f"source_{source_match[0]}"] += 1
        target_match = _match_law_instance_target(law, equation)
        if target_match is not None:
            targets.add(feature.equation_id)
            counts[f"target_{target_match[0]}"] += 1
    return features, frozenset(sources), frozenset(targets), counts


def _singleton_seedbank_sets(
    equations_path: Path,
) -> tuple[list, frozenset[int], frozenset[int], tuple[int, ...]]:
    parsed_features = _cached_parsed_equation_features(equations_path)
    features = [feature for feature, _ in parsed_features]
    seed_signatures = _verified_singleton_seed_source_signatures(equations_path)
    sources: set[int] = set()
    mismatches: list[int] = []
    for feature, equation in parsed_features:
        expected_signature = seed_signatures.get(feature.equation_id)
        if expected_signature is None:
            continue
        if _canonical_signature_from_equation(equation) == expected_signature:
            sources.add(feature.equation_id)
        else:
            mismatches.append(feature.equation_id)
    targets = frozenset(feature.equation_id for feature in features)
    return features, frozenset(sources), targets, tuple(mismatches)


def _singleton_seedbank_specialization_sets(
    equations_path: Path,
) -> tuple[list, frozenset[int], frozenset[int], dict[int, int]]:
    parsed_features = _cached_parsed_equation_features(equations_path)
    features = [feature for feature, _ in parsed_features]
    seed_equations = _singleton_seed_equations(equations_path)
    max_seed_mul_count = max(
        (_equation_mul_count(seed_equation) for _, seed_equation in seed_equations),
        default=-1,
    )
    equal_mul_seed_index = _singleton_seed_equal_mul_index(seed_equations)
    sources: set[int] = set()
    match_counts: dict[int, int] = {}
    for feature, equation in parsed_features:
        equation_mul_count = _equation_mul_count(equation)
        if equation_mul_count == max_seed_mul_count:
            match = _match_singleton_seedbank_specialization_equal_mul(
                equation,
                equal_mul_seed_index,
            )
            if match is not None:
                seed_id, _, _, _ = match
                sources.add(feature.equation_id)
                match_counts[seed_id] = match_counts.get(seed_id, 0) + 1
            continue
        if equation_mul_count > max_seed_mul_count:
            continue
        match = _match_singleton_seedbank_specialization_from_seeds(
            equation,
            seed_equations,
        )
        if match is None:
            continue
        seed_id, _, _, _ = match
        sources.add(feature.equation_id)
        match_counts[seed_id] = match_counts.get(seed_id, 0) + 1
    targets = frozenset(feature.equation_id for feature in features)
    return features, frozenset(sources), targets, match_counts


def _singleton_superpose_sets(
    equations_path: Path,
) -> tuple[list, frozenset[int], frozenset[int], dict[str, int]]:
    parsed_features = _cached_parsed_equation_features(equations_path)
    features = [feature for feature, _ in parsed_features]
    sources: set[int] = set()
    source_counts = {"eq1087": 0, "superpose_collapse": 0}
    for feature, equation in parsed_features:
        if _match_eq1087_singleton_shape(equation) is not None:
            sources.add(feature.equation_id)
            source_counts["eq1087"] += 1
            continue
        if _match_superpose_collapse_shape(equation) is not None:
            sources.add(feature.equation_id)
            source_counts["superpose_collapse"] += 1
    targets = frozenset(feature.equation_id for feature in features)
    return features, frozenset(sources), targets, source_counts


@lru_cache(maxsize=8)
def _cached_parsed_equation_features(equations_path: Path) -> tuple[tuple[object, Equation], ...]:
    return tuple(
        (feature, parse_equation(feature.equation))
        for feature in load_equation_spine_features(equations_path)
    )


def _parse_stage2_equation(source: str) -> Equation:
    return parse_equation(source.replace("◇", "*"))


def _canonical_signature_from_equation(equation: Equation) -> str:
    names: dict[str, str] = {}

    def encode(expr) -> str:
        if expr.kind == "var":
            assert expr.value is not None
            if expr.value not in names:
                names[expr.value] = f"v{len(names)}"
            return names[expr.value]
        assert expr.left is not None
        assert expr.right is not None
        return f"({encode(expr.left)}*{encode(expr.right)})"

    return f"{encode(equation.left)}={encode(equation.right)}"


@lru_cache(maxsize=4)
def _load_magmaegg_singleton_proof_bodies(
    proof_source_path: Path = DEFAULT_SINGLETON_SEEDBANK_PROOF_SOURCE,
) -> dict[int, str]:
    source = Path(proof_source_path).read_text(encoding="utf-8")
    module = ast.parse(source, filename=str(proof_source_path))
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name)
            and target.id == "_MAGMAEGG_SINGLETON_PROOF_BODIES"
            for target in node.targets
        ):
            continue
        value = ast.literal_eval(node.value)
        return {int(key): str(body) for key, body in value.items()}
    raise ValueError(
        f"_MAGMAEGG_SINGLETON_PROOF_BODIES not found in {proof_source_path}"
    )


@lru_cache(maxsize=8)
def _singleton_seed_equations(
    equations_path: Path = DEFAULT_EQ_SIZE5_PATH,
) -> tuple[tuple[int, Equation], ...]:
    equations_by_id = {
        feature.equation_id: equation
        for feature, equation in _cached_parsed_equation_features(equations_path)
    }
    seeds: list[tuple[int, Equation]] = []
    seed_signatures = _verified_singleton_seed_source_signatures(equations_path)
    for seed_id, expected_signature in sorted(seed_signatures.items()):
        equation = equations_by_id.get(seed_id)
        if equation is None:
            continue
        if _canonical_signature_from_equation(equation) != expected_signature:
            continue
        seeds.append((seed_id, equation))
    return tuple(seeds)


@lru_cache(maxsize=8)
def _verified_singleton_seed_source_signatures(
    equations_path: Path = DEFAULT_EQ_SIZE5_PATH,
    proof_bank_path: Path = DEFAULT_SINGLETON_SEEDBANK_PROOF_BANK,
) -> dict[int, str]:
    equations_by_id = {
        feature.equation_id: equation
        for feature, equation in _cached_parsed_equation_features(equations_path)
    }
    signatures = dict(MAGMAEGG_SINGLETON_SEED_SOURCE_SIGNATURES)
    for source_id, (signature, _) in _load_harvested_singleton_seed_proofs(
        proof_bank_path
    ).items():
        signatures[source_id] = signature
    return {
        source_id: signature
        for source_id, signature in signatures.items()
        if source_id in equations_by_id
        and _canonical_signature_from_equation(equations_by_id[source_id])
        == signature
    }


@lru_cache(maxsize=4)
def _load_harvested_singleton_seed_proofs(
    proof_bank_path: Path = DEFAULT_SINGLETON_SEEDBANK_PROOF_BANK,
) -> dict[int, tuple[str, str]]:
    proof_bank_path = Path(proof_bank_path)
    attempts_path = proof_bank_path / "attempts.jsonl"
    problems_path = proof_bank_path / "problems.jsonl"
    accepted_path = proof_bank_path / "accepted.jsonl"
    if (
        not attempts_path.exists()
        or not problems_path.exists()
        or not accepted_path.exists()
    ):
        return {}

    problems = {
        row["problem_key"]: row
        for row in _read_jsonl_records(problems_path)
        if "problem_key" in row
    }
    accepted_attempt_ids = {
        str(row["attempt_id"])
        for row in _read_jsonl_records(accepted_path)
        if "attempt_id" in row
    }
    proofs: dict[int, tuple[str, str]] = {}
    proof_lengths: dict[int, int] = {}
    for attempt in _read_jsonl_records(attempts_path):
        if str(attempt.get("attempt_id")) not in accepted_attempt_ids:
            continue
        source_run_id = str(attempt.get("source_run_id") or "")
        if not _is_singleton_seedbank_harvest_source_run_id(source_run_id):
            continue
        if attempt.get("official_judge_status") != "accepted":
            continue
        problem = problems.get(str(attempt.get("problem_key")))
        if problem is None:
            continue
        proof_sha = attempt.get("proof_body_sha256")
        if not isinstance(proof_sha, str) or not proof_sha:
            continue
        proof_path = proof_bank_path / "proof_bodies" / proof_sha[:2] / f"{proof_sha}.lean"
        if not proof_path.exists():
            continue
        source_id = int(problem["eq1_id"])
        signature = _proof_bank_source_signature(problem)
        if not signature:
            continue
        proof_body = proof_path.read_text(encoding="utf-8")
        try:
            _singleton_prefix_from_source_level_proof_body(
                proof_body,
                allow_bare=_is_singleton_seedbank_bare_proof_source_run_id(
                    source_run_id
                ),
            )
        except ValueError:
            continue
        proof_length = len(proof_body)
        if source_id not in proofs or proof_length < proof_lengths[source_id]:
            proofs[source_id] = (signature, proof_body)
            proof_lengths[source_id] = proof_length
    return proofs


@lru_cache(maxsize=4)
def _load_product_anchor_seed_lift_proofs(
    candidate_jsonl_path: Path = DEFAULT_PRODUCT_ANCHOR_SEED_LIFT_CANDIDATE_JSONL,
) -> dict[int, dict]:
    candidate_jsonl_path = Path(candidate_jsonl_path)
    if not candidate_jsonl_path.exists():
        return {}

    proofs: dict[int, dict] = {}
    for row in _read_jsonl_records(candidate_jsonl_path):
        if row.get("candidate_key") != PRODUCT_ANCHOR_SEED_LIFT_CANDIDATE_KEY:
            continue
        raw_source_ids = row.get("source_ids")
        source_id_scope = (
            {int(source_id) for source_id in raw_source_ids}
            if isinstance(raw_source_ids, list)
            else set()
        )
        raw_proofs = row.get("source_seed_proofs")
        if not isinstance(raw_proofs, list):
            continue
        for proof in raw_proofs:
            if not isinstance(proof, dict):
                continue
            if proof.get("official_judge_status") != "accepted":
                continue
            try:
                source_id = int(proof["source_id"])
            except (KeyError, TypeError, ValueError):
                continue
            if source_id_scope and source_id not in source_id_scope:
                continue
            seed_equation = proof.get("seed_product_anchor_equation")
            if not isinstance(seed_equation, str) or not seed_equation.strip():
                continue
            try:
                seed = _parse_stage2_equation(seed_equation)
            except Exception:
                continue
            if _product_anchor_shape(seed) is None:
                continue
            proof_body_path = proof.get("proof_body_path")
            if not isinstance(proof_body_path, str):
                continue
            if not Path(proof_body_path).exists():
                continue
            normalized = dict(proof)
            normalized["source_id"] = source_id
            normalized["proof_body_path"] = proof_body_path
            proofs[source_id] = normalized
    return proofs


@lru_cache(maxsize=8)
def _product_anchor_seed_lift_source_signatures(
    equations_path: Path = DEFAULT_EQ_SIZE5_PATH,
    candidate_jsonl_path: Path = DEFAULT_PRODUCT_ANCHOR_SEED_LIFT_CANDIDATE_JSONL,
) -> dict[int, str]:
    equations_by_id = {
        feature.equation_id: equation
        for feature, equation in _cached_parsed_equation_features(equations_path)
    }
    signatures: dict[int, str] = {}
    for source_id, proof in _load_product_anchor_seed_lift_proofs(
        candidate_jsonl_path
    ).items():
        source_equation = proof.get("source_equation")
        if not isinstance(source_equation, str) or not source_equation.strip():
            continue
        try:
            expected_signature = _canonical_signature_from_equation(
                _parse_stage2_equation(source_equation)
            )
        except Exception:
            continue
        equation = equations_by_id.get(source_id)
        if equation is None:
            continue
        if _canonical_signature_from_equation(equation) != expected_signature:
            continue
        signatures[source_id] = expected_signature
    return signatures


def _is_singleton_seedbank_harvest_source_run_id(source_run_id: str) -> bool:
    return source_run_id in SINGLETON_SEEDBANK_HARVEST_SOURCE_RUN_IDS or any(
        source_run_id.startswith(prefix)
        for prefix in SINGLETON_SEEDBANK_HARVEST_SOURCE_RUN_ID_PREFIXES
    )


def _is_singleton_seedbank_bare_proof_source_run_id(source_run_id: str) -> bool:
    return source_run_id in SINGLETON_SEEDBANK_BARE_PROOF_SOURCE_RUN_IDS or any(
        source_run_id.startswith(prefix)
        for prefix in SINGLETON_SEEDBANK_BARE_PROOF_SOURCE_RUN_ID_PREFIXES
    )


def _proof_bank_source_signature(problem: dict) -> str:
    stored_signature = problem.get("eq1_signature")
    if isinstance(stored_signature, str) and stored_signature:
        return stored_signature
    equation = problem.get("equation1")
    if not isinstance(equation, str) or not equation.strip():
        return ""
    try:
        parsed = _parse_stage2_equation(equation)
    except Exception:
        return ""
    return _canonical_signature_from_equation(parsed)


def _available_singleton_seed_source_count() -> int:
    return len(
        set(MAGMAEGG_SINGLETON_SEED_SOURCE_SIGNATURES)
        | set(_load_harvested_singleton_seed_proofs())
    )


def _read_jsonl_records(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _match_singleton_seedbank_specialization(
    source: Equation,
    equations_path: Path = DEFAULT_EQ_SIZE5_PATH,
) -> tuple[int, Equation, str, dict[str, object]] | None:
    return _match_singleton_seedbank_specialization_from_seeds(
        source,
        _singleton_seed_equations(equations_path),
    )


def _match_singleton_seedbank_specialization_from_seeds(
    source: Equation,
    seed_equations: tuple[tuple[int, Equation], ...],
) -> tuple[int, Equation, str, dict[str, object]] | None:
    source_mul_count = _equation_mul_count(source)
    for seed_id, seed_equation in seed_equations:
        if source_mul_count > _equation_mul_count(seed_equation):
            continue
        direct = _match_equation_instance(source, seed_equation)
        if direct is not None:
            return seed_id, seed_equation, "direct", direct
        reversed_seed = Equation(left=seed_equation.right, right=seed_equation.left)
        if source_mul_count > _equation_mul_count(reversed_seed):
            continue
        symm = _match_equation_instance(
            source,
            reversed_seed,
        )
        if symm is not None:
            return seed_id, seed_equation, "symm", symm
    return None


def _singleton_seed_equal_mul_index(
    seed_equations: tuple[tuple[int, Equation], ...],
) -> dict[str, tuple[tuple[int, Equation, str, Equation], ...]]:
    by_skeleton: dict[str, list[tuple[int, Equation, str, Equation]]] = {}
    for seed_id, seed_equation in seed_equations:
        by_skeleton.setdefault(_equation_skeleton(seed_equation), []).append(
            (seed_id, seed_equation, "direct", seed_equation)
        )
        reversed_seed = Equation(left=seed_equation.right, right=seed_equation.left)
        by_skeleton.setdefault(_equation_skeleton(reversed_seed), []).append(
            (seed_id, seed_equation, "symm", reversed_seed)
        )
    return {
        skeleton: tuple(candidates)
        for skeleton, candidates in by_skeleton.items()
    }


def _match_singleton_seedbank_specialization_equal_mul(
    source: Equation,
    seed_index: dict[str, tuple[tuple[int, Equation, str, Equation], ...]],
) -> tuple[int, Equation, str, dict[str, object]] | None:
    for seed_id, seed_equation, orientation, target_equation in seed_index.get(
        _equation_skeleton(source),
        (),
    ):
        substitutions = _match_equation_instance(source, target_equation)
        if substitutions is not None:
            return seed_id, seed_equation, orientation, substitutions
    return None


def _equation_skeleton(equation: Equation) -> str:
    return f"{_expr_skeleton(equation.left)}={_expr_skeleton(equation.right)}"


def _expr_skeleton(expr) -> str:
    if expr.kind == "var":
        return "_"
    assert expr.left is not None
    assert expr.right is not None
    return (
        f"({_expr_skeleton(expr.left)}*"
        f"{_expr_skeleton(expr.right)})"
    )


def _equation_mul_count(equation: Equation) -> int:
    return _expr_mul_count(equation.left) + _expr_mul_count(equation.right)


def _expr_mul_count(expr) -> int:
    if expr.kind == "var":
        return 0
    assert expr.left is not None
    assert expr.right is not None
    return 1 + _expr_mul_count(expr.left) + _expr_mul_count(expr.right)


def _match_equation_instance(
    pattern: Equation,
    target: Equation,
) -> dict[str, object] | None:
    substitutions = _match_expr_instance(pattern.left, target.left, {})
    if substitutions is None:
        return None
    return _match_expr_instance(pattern.right, target.right, substitutions)


def _match_target_instance_of_source(
    source: Equation,
    target: Equation,
) -> tuple[str, dict[str, object]] | None:
    direct = _match_equation_instance(source, target)
    if direct is not None:
        return "direct", direct
    symm = _match_equation_instance(
        source,
        Equation(left=target.right, right=target.left),
    )
    if symm is not None:
        return "symm", symm
    return None


def _match_law_instance_source(
    source: Equation,
    law: Equation,
) -> tuple[str, dict[str, object]] | None:
    direct = _match_equation_instance(source, law)
    if direct is not None:
        return "direct", direct
    symm = _match_equation_instance(
        source,
        Equation(left=law.right, right=law.left),
    )
    if symm is not None:
        return "symm", symm
    return None


def _match_law_instance_target(
    law: Equation,
    target: Equation,
) -> tuple[str, dict[str, object]] | None:
    direct = _match_equation_instance(law, target)
    if direct is not None:
        return "direct", direct
    symm = _match_equation_instance(
        law,
        Equation(left=target.right, right=target.left),
    )
    if symm is not None:
        return "symm", symm
    return None


def _match_expr_instance(
    pattern,
    target,
    substitutions: dict[str, object],
) -> dict[str, object] | None:
    if pattern.kind == "var":
        assert pattern.value is not None
        existing = substitutions.get(pattern.value)
        if existing is None:
            return {**substitutions, pattern.value: target}
        return substitutions if existing == target else None
    if target.kind != "mul":
        return None
    assert pattern.left is not None
    assert pattern.right is not None
    assert target.left is not None
    assert target.right is not None
    left_substitutions = _match_expr_instance(
        pattern.left,
        target.left,
        substitutions,
    )
    if left_substitutions is None:
        return None
    return _match_expr_instance(pattern.right, target.right, left_substitutions)


def _match_eq1087_singleton_shape(equation: Equation) -> dict[str, str] | None:
    base = _bare_variable_name(equation.left)
    if base is None:
        return None
    rhs = equation.right
    if rhs.kind != "mul" or rhs.left is None or rhs.right is None:
        return None
    left = _bare_variable_name(rhs.left)
    if left is None:
        return None
    tail = rhs.right
    if tail.kind != "mul" or tail.left is None or tail.right is None:
        return None
    tail_variable = _bare_variable_name(tail.right)
    if tail_variable is None:
        return None
    middle = tail.left
    if middle.kind != "mul" or middle.left is None or middle.right is None:
        return None
    if middle.left != equation.left:
        return None
    square = middle.right
    if square.kind != "mul" or square.left is None or square.right is None:
        return None
    if square.left != rhs.left or square.right != rhs.left:
        return None
    role_by_variable = {
        base: "base",
        left: "left",
        tail_variable: "tail",
    }
    if len(role_by_variable) != 3:
        return None
    if any(variable not in role_by_variable for variable in equation.variables()):
        return None
    return role_by_variable


def _match_superpose_collapse_shape(equation: Equation) -> dict[str, object] | None:
    return (
        _match_superpose_collapse_oriented(equation.left, equation.right, True, equation)
        or _match_superpose_collapse_oriented(equation.right, equation.left, False, equation)
    )


def _match_superpose_collapse_oriented(
    base_expr,
    rhs,
    uses_symm: bool,
    equation: Equation,
) -> dict[str, object] | None:
    base = _bare_variable_name(base_expr)
    if base is None:
        return None
    if rhs.kind != "mul" or rhs.left is None or rhs.right is None:
        return None
    prefix = _bare_variable_name(rhs.left)
    if prefix is None:
        return None
    inner = rhs.right
    if inner.kind != "mul" or inner.left is None or inner.right is None:
        return None
    if inner.left != base_expr:
        return None
    tail_pair = inner.right
    if tail_pair.kind != "mul" or tail_pair.left is None or tail_pair.right is None:
        return None
    tail = _bare_variable_name(tail_pair.right)
    if tail is None:
        return None
    left_pair = tail_pair.left
    if (
        left_pair.kind != "mul"
        or left_pair.left is None
        or left_pair.right is None
        or left_pair.right != base_expr
    ):
        return None
    left = _bare_variable_name(left_pair.left)
    if left is None:
        return None
    role_by_variable = {
        base: "base",
        prefix: "prefix",
        left: "left",
        tail: "tail",
    }
    if len(role_by_variable) != 4:
        return None
    if any(variable not in role_by_variable for variable in equation.variables()):
        return None
    return {
        "role_by_variable": role_by_variable,
        "uses_symm": uses_symm,
    }


def _singleton_collapse_shape(equation: Equation) -> tuple[str, str] | None:
    left_variable = _bare_variable_name(equation.left)
    if (
        left_variable is not None
        and left_variable not in set(equation.right.variable_names())
    ):
        return "left", left_variable
    right_variable = _bare_variable_name(equation.right)
    if (
        right_variable is not None
        and right_variable not in set(equation.left.variable_names())
    ):
        return "right", right_variable
    return None


def _product_anchor_shape(equation: Equation) -> tuple[str, str, str] | None:
    left_product = _distinct_bare_product_variables(equation.left)
    if left_product is not None and set(left_product).isdisjoint(
        set(equation.right.variable_names())
    ):
        return "left", left_product[0], left_product[1]
    right_product = _distinct_bare_product_variables(equation.right)
    if right_product is not None and set(right_product).isdisjoint(
        set(equation.left.variable_names())
    ):
        return "right", right_product[0], right_product[1]
    return None


@lru_cache(maxsize=32)
def _parse_product_collapse_pattern(term_pattern: str) -> Expr:
    return parse_equation(f"{term_pattern} = sentinel").left


def _product_collapse_template_match(
    source: Equation,
    target: Equation,
    *,
    term_pattern: str | None,
) -> tuple[Expr, dict[str, object], dict[str, Expr], dict[str, Expr]] | None:
    templates = (
        [template for template in PRODUCT_COLLAPSE_TEMPLATES if template["term_pattern"] == term_pattern]
        if term_pattern is not None
        else PRODUCT_COLLAPSE_TEMPLATES
    )
    for template in templates:
        pattern = _parse_product_collapse_pattern(str(template["term_pattern"]))
        source_shape = _product_collapse_source_shape(source, pattern)
        if source_shape is None:
            continue
        left_env = _product_collapse_pattern_match(pattern, target.left)
        if left_env is None:
            continue
        right_env = _product_collapse_pattern_match(pattern, target.right)
        if right_env is None:
            continue
        return pattern, source_shape, left_env, right_env
    return None


def _product_collapse_source_shape(
    equation: Equation,
    pattern: Expr,
) -> dict[str, object] | None:
    shapes = _product_collapse_source_shapes(equation, pattern)
    return shapes[0] if shapes else None


def _product_collapse_source_shapes(
    equation: Equation,
    pattern: Expr,
) -> tuple[dict[str, object], ...]:
    shapes: list[dict[str, object]] = []
    for side, pattern_side, anchor_side in (
        ("left", equation.left, equation.right),
        ("right", equation.right, equation.left),
    ):
        env = _product_collapse_pattern_match(pattern, pattern_side)
        if env is None:
            continue
        if any(_bare_variable_name(value) is None for value in env.values()):
            continue
        source_var_by_pattern_var = {
            pattern_variable: _bare_variable_name(value)
            for pattern_variable, value in env.items()
        }
        mapped_source_variables = set(source_var_by_pattern_var.values())
        if len(mapped_source_variables) != len(source_var_by_pattern_var):
            continue
        if not mapped_source_variables.isdisjoint(set(anchor_side.variable_names())):
            continue
        shapes.append(
            {
                "side": side,
                "source_var_by_pattern_var": source_var_by_pattern_var,
                "anchor_vars": frozenset(anchor_side.variable_names()),
            }
        )
    return tuple(shapes)


def _product_collapse_target_matches(equation: Equation, pattern: Expr) -> bool:
    return (
        _product_collapse_pattern_match(pattern, equation.left) is not None
        and _product_collapse_pattern_match(pattern, equation.right) is not None
    )


def _product_collapse_pattern_match(
    pattern: Expr,
    expr: Expr,
    env: dict[str, Expr] | None = None,
) -> dict[str, Expr] | None:
    env = {} if env is None else dict(env)
    if pattern.kind == "var":
        assert pattern.value is not None
        existing = env.get(pattern.value)
        if existing is None:
            env[pattern.value] = expr
            return env
        return env if existing == expr else None
    if expr.kind != "mul":
        return None
    assert pattern.left is not None
    assert pattern.right is not None
    assert expr.left is not None
    assert expr.right is not None
    left_env = _product_collapse_pattern_match(pattern.left, expr.left, env)
    if left_env is None:
        return None
    return _product_collapse_pattern_match(pattern.right, expr.right, left_env)


def _distinct_bare_product_variables(expr) -> tuple[str, str] | None:
    if expr.kind != "mul":
        return None
    assert expr.left is not None
    assert expr.right is not None
    left_variable = _bare_variable_name(expr.left)
    right_variable = _bare_variable_name(expr.right)
    if left_variable is None or right_variable is None:
        return None
    if left_variable == right_variable:
        return None
    return left_variable, right_variable


def _is_product_root_target(equation: Equation) -> bool:
    return equation.left.kind == "mul" and equation.right.kind == "mul"


def _projection_normalizer_source_shape(
    equation: Equation,
    *,
    side: str,
) -> dict[str, object] | None:
    return _match_projection_source_oriented(
        equation.left,
        equation.right,
        side=side,
        var_eq_product=True,
        equation=equation,
    ) or _match_projection_source_oriented(
        equation.right,
        equation.left,
        side=side,
        var_eq_product=False,
        equation=equation,
    )


def _match_projection_source_oriented(
    variable_side,
    product_side,
    *,
    side: str,
    var_eq_product: bool,
    equation: Equation,
) -> dict[str, object] | None:
    anchor = _bare_variable_name(variable_side)
    if anchor is None or product_side.kind != "mul":
        return None
    assert product_side.left is not None
    assert product_side.right is not None
    product_left = _bare_variable_name(product_side.left)
    product_right = _bare_variable_name(product_side.right)
    if product_left is None or product_right is None or product_left == product_right:
        return None

    if side == "left":
        if product_left != anchor:
            return None
        role_by_variable = {product_left: "a", product_right: "b"}
    elif side == "right":
        if product_right != anchor:
            return None
        role_by_variable = {product_left: "a", product_right: "b"}
    else:
        raise ValueError(f"unknown projection normalizer side: {side}")

    if any(variable not in role_by_variable for variable in equation.variables()):
        return None
    return {
        "role_by_variable": role_by_variable,
        "var_eq_product": var_eq_product,
    }


def _is_projection_normal_target(equation: Equation, *, side: str) -> bool:
    return _projection_edge_variable(
        equation.left,
        side=side,
    ) == _projection_edge_variable(equation.right, side=side)


def _projection_edge_variable(expr, *, side: str) -> str:
    while expr.kind == "mul":
        assert expr.left is not None
        assert expr.right is not None
        if side == "left":
            expr = expr.left
        elif side == "right":
            expr = expr.right
        else:
            raise ValueError(f"unknown projection normalizer side: {side}")
    assert expr.value is not None
    return expr.value


def _bare_variable_name(expr) -> str | None:
    if expr.kind != "var":
        return None
    return expr.value


def _singleton_h_args(
    equation: Equation,
    distinguished_variable: str,
    distinguished_value: str,
    filler_value: str,
) -> str:
    return " ".join(
        distinguished_value if variable == distinguished_variable else filler_value
        for variable in equation.variables()
    )


def _product_anchor_h_args(
    equation: Equation,
    first_variable: str,
    second_variable: str,
    first_value: str,
    second_value: str,
) -> str:
    return " ".join(
        first_value
        if variable == first_variable
        else second_value
        if variable == second_variable
        else "p"
        for variable in equation.variables()
    )


def _product_collapse_h_call(
    equation: Equation,
    source_shape: dict[str, object],
    target_env: dict[str, Expr],
    anchor_seed: Expr,
) -> str:
    source_var_by_pattern_var = source_shape["source_var_by_pattern_var"]
    assert isinstance(source_var_by_pattern_var, dict)
    pattern_var_by_source_var = {
        source_variable: pattern_variable
        for pattern_variable, source_variable in source_var_by_pattern_var.items()
    }
    args: list[str] = []
    for source_variable in equation.variables():
        pattern_variable = pattern_var_by_source_var.get(source_variable)
        value = target_env[pattern_variable] if pattern_variable is not None else anchor_seed
        args.append(f"({lean_expr(value, top=True)})")
    return "h " + " ".join(args)


def _model_family(table: tuple[tuple[int, ...], ...]) -> str:
    if table == LEFT_PROJECTION_2_TABLE:
        return "fin2_left_projection"
    if table == CONSTANT_2_TABLE:
        return "fin2_constant"
    if table == RIGHT_PROJECTION_2_TABLE:
        return "fin2_right_projection"
    if table == COMPLEMENT_LEFT_PROJECTION_2_TABLE:
        return "fin2_complement_left_projection"
    if table == COMPLEMENT_RIGHT_PROJECTION_2_TABLE:
        return "fin2_complement_right_projection"
    if table == LEFT_AND_COMPLEMENT_RIGHT_2_TABLE:
        return "fin2_left_and_complement_right"
    if table == COMPLEMENT_LEFT_AND_RIGHT_2_TABLE:
        return "fin2_complement_left_and_right"
    if table == XOR_2_TABLE:
        return "fin2_xor"
    if table == AND_2_TABLE:
        return "fin2_and"
    if table == NOR_2_TABLE:
        return "fin2_nor"
    if table == STEINER_QUASIGROUP_3_TABLE:
        return "fin3_steiner_quasigroup"
    if table == RIGHT_MINUS_LEFT_3_TABLE:
        return "fin3_right_minus_left"
    if table == LEFT_MINUS_RIGHT_3_TABLE:
        return "fin3_left_minus_right"
    if table == FIN3_TABLE_020_110_122_TABLE:
        return "fin3_table_020_110_122"
    if table == LEFT_CYCLIC_SUCCESSOR_3_TABLE:
        return "fin3_left_cyclic_successor"
    if table == RIGHT_CYCLIC_SUCCESSOR_3_TABLE:
        return "fin3_right_cyclic_successor"
    if table == FIN3_TABLE_022_010_112_TABLE:
        return "fin3_table_022_010_112"
    if table == ADDITION_MOD3_3_TABLE:
        return "fin3_addition_mod3"
    if table == FIN4_TABLE_0231_3102_1320_2013_TABLE:
        return "fin4_table_0231_3102_1320_2013"
    if table == FIN3_TABLE_000_211_122_TABLE:
        return "fin3_table_000_211_122"
    if table == FIN3_TABLE_012_012_102_TABLE:
        return "fin3_table_012_012_102"
    if table == FIN3_TABLE_011_012_012_TABLE:
        return "fin3_table_011_012_012"
    if table == FIN3_TABLE_000_110_222_TABLE:
        return "fin3_table_000_110_222"
    if table == FIN3_TABLE_122_020_110_TABLE:
        return "fin3_table_122_020_110"
    if table == FIN3_TABLE_002_112_102_TABLE:
        return "fin3_table_002_112_102"
    if table == FIN3_TABLE_011_012_110_TABLE:
        return "fin3_table_011_012_110"
    if table == FIN4_TABLE_2013_3102_0231_1320_TABLE:
        return "fin4_table_2013_3102_0231_1320"
    if table == FIN4_TABLE_0011_2233_0011_2233_TABLE:
        return "fin4_table_0011_2233_0011_2233"
    if table == FIN5_TABLE_02413_41302_30241_24130_13024_TABLE:
        return "fin5_table_02413_41302_30241_24130_13024"
    if table == FIN5_TABLE_03142_31420_14203_42031_20314_TABLE:
        return "fin5_table_03142_31420_14203_42031_20314"
    if table == FIN5_TABLE_02143_41320_34201_10432_23014_TABLE:
        return "fin5_table_02143_41320_34201_10432_23014"
    if table == FIN7_TABLE_0214365_3150624_4625031_6543210_5361402_2406153_1032546_TABLE:
        return "fin7_table_0214365_3150624_4625031_6543210_5361402_2406153_1032546"
    if table == FIN5_TABLE_31420_02341_14032_40213_23104_TABLE:
        return "fin5_table_31420_02341_14032_40213_23104"
    if table == FIN5_TABLE_34120_20413_01234_13042_42301_TABLE:
        return "fin5_table_34120_20413_01234_13042_42301"
    if table == FIN4_TABLE_1032_3210_2301_0123_TABLE:
        return "fin4_table_1032_3210_2301_0123"
    if table == FIN3_TABLE_000_000_001_TABLE:
        return "fin3_table_000_000_001"
    if table == FIN3_TABLE_000_000_010_TABLE:
        return "fin3_table_000_000_010"
    if table == FIN3_TABLE_000_000_020_TABLE:
        return "fin3_table_000_000_020"
    if table == FIN3_TABLE_000_000_100_TABLE:
        return "fin3_table_000_000_100"
    if table == FIN3_TABLE_001_000_000_TABLE:
        return "fin3_table_001_000_000"
    if table == FIN3_TABLE_000_000_011_TABLE:
        return "fin3_table_000_000_011"
    if table == FIN3_TABLE_000_001_001_TABLE:
        return "fin3_table_000_001_001"
    if table == FIN3_TABLE_000_001_010_TABLE:
        return "fin3_table_000_001_010"
    if table == FIN3_TABLE_000_020_001_TABLE:
        return "fin3_table_000_020_001"
    if table == FIN3_TABLE_000_122_122_TABLE:
        return "fin3_table_000_122_122"
    for spec in STRUCTURED_AFFINE_MOD11_TOP2_MATCHOP_NOHB_SPECS:
        if table == spec["table"]:
            return f"fin11_structured_{spec['label']}"
    for spec in STRUCTURED_AFFINE_MOD11_COMBO9_MATCHOP_NOHB_SPECS:
        if table == spec["table"]:
            return f"fin11_structured_{spec['label']}"
    for spec in STRUCTURED_AFFINE_LOW_ORDER_LE9_COMBO19_SPECS:
        if table == spec["table"]:
            return f"fin{len(table)}_structured_{spec['label']}"
    return f"fin{len(table)}_explicit"


def _table_signature(table: tuple[tuple[int, ...], ...]) -> str:
    return "/".join("".join(str(value) for value in row) for row in table)


def write_strategy_registry_outputs(
    registry: Order5StrategyRegistry,
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> tuple[list[dict], dict]:
    registry = registry.without_source_target_exclusions()
    strategies = registry.strategies_manifest()
    summary = registry.coverage_summary()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "strategies.json").write_text(
        json.dumps(strategies, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (output_dir / "coverage_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return strategies, summary


def _block_count(source_ids: frozenset[int], target_ids: frozenset[int]) -> int:
    return len(source_ids) * len(target_ids) - len(source_ids & target_ids)


def _block_union_count(
    base_sources: frozenset[int],
    base_targets: frozenset[int],
    blocks: Sequence[tuple[frozenset[int], frozenset[int]]],
) -> int:
    clipped_blocks: list[tuple[frozenset[int], frozenset[int]]] = []
    seen_blocks: set[tuple[frozenset[int], frozenset[int]]] = set()
    for sources, targets in blocks:
        clipped_sources = base_sources & sources
        clipped_targets = base_targets & targets
        if not clipped_sources or not clipped_targets:
            continue
        clipped_block = (clipped_sources, clipped_targets)
        if clipped_block in seen_blocks:
            continue
        seen_blocks.add(clipped_block)
        clipped_blocks.append(clipped_block)
    total = 0
    for size in range(1, len(clipped_blocks) + 1):
        sign = 1 if size % 2 else -1
        for subset in combinations(clipped_blocks, size):
            sources = frozenset.intersection(*(item[0] for item in subset))
            targets = frozenset.intersection(*(item[1] for item in subset))
            total += sign * _block_count(sources, targets)
    return total


def _strategy_by_id(
    strategies: Sequence[CoverageStrategy],
    strategy_id: str,
) -> CoverageStrategy:
    for strategy in strategies:
        if strategy.strategy_id == strategy_id:
            return strategy
    raise KeyError(strategy_id)


def _union_count_for_rules(rules: Sequence[CoverageRule]) -> int:
    if not rules:
        return 0
    source_target_rules = [
        rule for rule in rules if isinstance(rule, SourceTargetSetsRule)
    ]
    pair_index_rules = _pair_index_rules(rules)
    total = (
        _union_count_by_source_signature(source_target_rules)
        if source_target_rules
        else 0
    )
    pair_index_law_count = _shared_pair_index_law_count(pair_index_rules)
    if pair_index_law_count is None:
        return total + _union_count_for_pair_index_rules_by_tuple(
            pair_index_rules,
            source_target_rules,
        )

    source_target_cache: dict[int, tuple[tuple[int, tuple[int, ...]], ...]] = {}
    seen_pair_indexes: set[int] = set()
    for rule in pair_index_rules:
        for pair_index in rule.pair_indexes:
            if pair_index in seen_pair_indexes:
                continue
            seen_pair_indexes.add(pair_index)
            eq1_id, eq2_id = pair_index_to_ids(
                pair_index,
                law_count=pair_index_law_count,
            )
            if _pair_covered_by_source_target_rules_cached(
                (eq1_id, eq2_id),
                source_target_rules,
                source_target_cache,
            ):
                continue
            total += 1
    return total


def _union_count_for_pair_index_rules_by_tuple(
    pair_index_rules: Sequence[PairIndexRule],
    source_target_rules: Sequence[SourceTargetSetsRule],
) -> int:
    total = 0
    seen_pairs: set[tuple[int, int]] = set()
    source_target_cache: dict[int, tuple[tuple[int, tuple[int, ...]], ...]] = {}
    for rule in pair_index_rules:
        for pair in rule.iter_covered_pairs():
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            if _pair_covered_by_source_target_rules_cached(
                pair,
                source_target_rules,
                source_target_cache,
            ):
                continue
            total += 1
    return total


def _union_count_by_source_signature(rules: Sequence[SourceTargetSetsRule]) -> int:
    source_groups: dict[tuple[tuple[int, tuple[int, ...]], ...], set[int]] = {}
    all_sources = frozenset().union(*(rule.source_ids for rule in rules))
    for source_id in all_sources:
        signature: list[tuple[int, tuple[int, ...]]] = []
        for rule_index, rule in enumerate(rules):
            if source_id not in rule.source_ids:
                continue
            excluded_block_indexes = tuple(
                block_index
                for block_index, (block_sources, _) in enumerate(rule.excluded_blocks)
                if source_id in block_sources
            )
            signature.append((rule_index, excluded_block_indexes))
        if signature:
            source_groups.setdefault(tuple(signature), set()).add(source_id)

    total = 0
    for signature, source_ids in source_groups.items():
        covered_targets = _targets_for_source_signature(signature, rules)
        total += len(source_ids) * len(covered_targets)
        total -= len(source_ids & covered_targets)
    return total


def _targets_for_source_signature(
    signature: tuple[tuple[int, tuple[int, ...]], ...],
    rules: Sequence[SourceTargetSetsRule],
) -> frozenset[int]:
    covered_targets: set[int] = set()
    for rule_index, excluded_block_indexes in signature:
        rule = rules[rule_index]
        if not excluded_block_indexes:
            covered_targets.update(rule.target_ids)
            continue
        excluded_targets = frozenset().union(
            *(
                rule.excluded_blocks[block_index][1]
                for block_index in excluded_block_indexes
            )
        )
        covered_targets.update(rule.target_ids - excluded_targets)
    return frozenset(covered_targets)


def _union_count_for_rules_inclusion_exclusion(rules: Sequence[CoverageRule]) -> int:
    if not rules:
        return 0
    total = 0
    for size in range(1, len(rules) + 1):
        sign = 1 if size % 2 else -1
        for subset in combinations(rules, size):
            total += sign * _intersect_rules(subset).coverage_count()
    return total


def _conflict_count(
    false_strategies: Sequence[CoverageStrategy],
    true_strategies: Sequence[CoverageStrategy],
) -> int:
    false_rules = [strategy.coverage_rule for strategy in false_strategies]
    true_rules = [strategy.coverage_rule for strategy in true_strategies]
    false_source_target_rules = [
        rule for rule in false_rules if isinstance(rule, SourceTargetSetsRule)
    ]
    true_source_target_rules = [
        rule for rule in true_rules if isinstance(rule, SourceTargetSetsRule)
    ]
    false_pair_index_rules = _pair_index_rules(false_rules)
    true_pair_index_rules = _pair_index_rules(true_rules)

    total = _source_target_overlap_count(
        false_source_target_rules,
        true_source_target_rules,
    )

    pair_index_law_count = _shared_pair_index_law_count(
        [*false_pair_index_rules, *true_pair_index_rules],
    )
    if pair_index_law_count is None:
        return total + _conflict_count_pair_index_rules_by_tuple(
            false_pair_index_rules=false_pair_index_rules,
            true_pair_index_rules=true_pair_index_rules,
            false_source_target_rules=false_source_target_rules,
            true_source_target_rules=true_source_target_rules,
        )

    false_source_target_cache: dict[
        int, tuple[tuple[int, tuple[int, ...]], ...]
    ] = {}
    true_source_target_cache: dict[
        int, tuple[tuple[int, tuple[int, ...]], ...]
    ] = {}
    pair_index_conflict_pairs: set[int] = set()
    for rule in false_pair_index_rules:
        for pair_index in rule.pair_indexes:
            pair = pair_index_to_ids(pair_index, law_count=pair_index_law_count)
            if _pair_covered_by_source_target_rules_cached(
                pair,
                true_source_target_rules,
                true_source_target_cache,
            ) or (
                _pair_index_covered_by_pair_index_rules(
                    pair_index,
                    true_pair_index_rules,
                )
            ):
                pair_index_conflict_pairs.add(pair_index)
    for rule in true_pair_index_rules:
        for pair_index in rule.pair_indexes:
            pair = pair_index_to_ids(pair_index, law_count=pair_index_law_count)
            if _pair_covered_by_source_target_rules_cached(
                pair,
                false_source_target_rules,
                false_source_target_cache,
            ) or (
                _pair_index_covered_by_pair_index_rules(
                    pair_index,
                    false_pair_index_rules,
                )
            ):
                pair_index_conflict_pairs.add(pair_index)

    for pair_index in pair_index_conflict_pairs:
        pair = pair_index_to_ids(pair_index, law_count=pair_index_law_count)
        if _pair_covered_by_source_target_rules_cached(
            pair,
            false_source_target_rules,
            false_source_target_cache,
        ) and _pair_covered_by_source_target_rules_cached(
            pair,
            true_source_target_rules,
            true_source_target_cache,
        ):
            continue
        total += 1
    return total


def _conflict_count_pair_index_rules_by_tuple(
    *,
    false_pair_index_rules: Sequence[PairIndexRule],
    true_pair_index_rules: Sequence[PairIndexRule],
    false_source_target_rules: Sequence[SourceTargetSetsRule],
    true_source_target_rules: Sequence[SourceTargetSetsRule],
) -> int:
    false_source_target_cache: dict[
        int, tuple[tuple[int, tuple[int, ...]], ...]
    ] = {}
    true_source_target_cache: dict[
        int, tuple[tuple[int, tuple[int, ...]], ...]
    ] = {}
    pair_index_conflict_pairs: set[tuple[int, int]] = set()
    for rule in false_pair_index_rules:
        for pair in rule.iter_covered_pairs():
            if _pair_covered_by_source_target_rules_cached(
                pair,
                true_source_target_rules,
                true_source_target_cache,
            ) or (
                _pair_covered_by_pair_index_rules(pair, true_pair_index_rules)
            ):
                pair_index_conflict_pairs.add(pair)
    for rule in true_pair_index_rules:
        for pair in rule.iter_covered_pairs():
            if _pair_covered_by_source_target_rules_cached(
                pair,
                false_source_target_rules,
                false_source_target_cache,
            ) or (
                _pair_covered_by_pair_index_rules(pair, false_pair_index_rules)
            ):
                pair_index_conflict_pairs.add(pair)

    total = 0
    for pair in pair_index_conflict_pairs:
        if _pair_covered_by_source_target_rules_cached(
            pair,
            false_source_target_rules,
            false_source_target_cache,
        ) and _pair_covered_by_source_target_rules_cached(
            pair,
            true_source_target_rules,
            true_source_target_cache,
        ):
            continue
        total += 1
    return total


def _source_target_overlap_count(
    left_rules: Sequence[SourceTargetSetsRule],
    right_rules: Sequence[SourceTargetSetsRule],
) -> int:
    if not left_rules or not right_rules:
        return 0
    left_sources = frozenset().union(*(rule.source_ids for rule in left_rules))
    right_sources = frozenset().union(*(rule.source_ids for rule in right_rules))
    source_groups: dict[
        tuple[
            tuple[tuple[int, tuple[int, ...]], ...],
            tuple[tuple[int, tuple[int, ...]], ...],
        ],
        set[int],
    ] = {}
    for source_id in left_sources & right_sources:
        left_signature = _source_signature(source_id, left_rules)
        right_signature = _source_signature(source_id, right_rules)
        if left_signature and right_signature:
            source_groups.setdefault((left_signature, right_signature), set()).add(
                source_id
            )

    total = 0
    for (left_signature, right_signature), source_ids in source_groups.items():
        left_targets = _targets_for_source_signature(left_signature, left_rules)
        right_targets = _targets_for_source_signature(right_signature, right_rules)
        overlap_targets = left_targets & right_targets
        total += len(source_ids) * len(overlap_targets)
        total -= len(source_ids & overlap_targets)
    return total


def _source_signature(
    source_id: int,
    rules: Sequence[SourceTargetSetsRule],
) -> tuple[tuple[int, tuple[int, ...]], ...]:
    signature: list[tuple[int, tuple[int, ...]]] = []
    for rule_index, rule in enumerate(rules):
        if source_id not in rule.source_ids:
            continue
        excluded_block_indexes = tuple(
            block_index
            for block_index, (block_sources, _) in enumerate(rule.excluded_blocks)
            if source_id in block_sources
        )
        signature.append((rule_index, excluded_block_indexes))
    return tuple(signature)


def _pair_covered_by_source_target_rules(
    pair: tuple[int, int],
    rules: Sequence[SourceTargetSetsRule],
) -> bool:
    return any(rule.covers(*pair) for rule in rules)


def _pair_covered_by_source_target_rules_cached(
    pair: tuple[int, int],
    rules: Sequence[SourceTargetSetsRule],
    source_signature_cache: dict[int, tuple[tuple[int, tuple[int, ...]], ...]],
) -> bool:
    if not rules:
        return False
    source_id, target_id = pair
    if source_id == target_id:
        return False
    signature = source_signature_cache.get(source_id)
    if signature is None:
        signature = _source_signature(source_id, rules)
        source_signature_cache[source_id] = signature
    for rule_index, excluded_block_indexes in signature:
        rule = rules[rule_index]
        if target_id not in rule.target_ids:
            continue
        if any(
            target_id in rule.excluded_blocks[block_index][1]
            for block_index in excluded_block_indexes
        ):
            continue
        return True
    return False


def _pair_covered_by_pair_index_rules(
    pair: tuple[int, int],
    rules: Sequence[PairIndexRule],
) -> bool:
    return any(rule.covers(*pair) for rule in rules)


def _pair_index_covered_by_pair_index_rules(
    pair_index: int,
    rules: Sequence[PairIndexRule],
) -> bool:
    return any(pair_index in rule.pair_indexes for rule in rules)


def _shared_pair_index_law_count(rules: Sequence[PairIndexRule]) -> int | None:
    if not rules:
        return 0
    law_counts = {rule.law_count for rule in rules}
    if len(law_counts) != 1:
        return None
    return law_counts.pop()


def _pair_index_rules(rules: Sequence[CoverageRule]) -> list[PairIndexRule]:
    return [
        rule
        for rule in rules
        if isinstance(rule, (ExplicitPairsRule, CompilerPairIndexesRule))
    ]


def _intersect_rules(rules: Sequence[CoverageRule]) -> CoverageRule:
    if not rules:
        raise ValueError("cannot intersect an empty rule list")
    source_target_rules = [
        rule for rule in rules if isinstance(rule, SourceTargetSetsRule)
    ]
    pair_index_rules = _pair_index_rules(rules)
    if pair_index_rules:
        law_counts = {rule.law_count for rule in pair_index_rules}
        if len(law_counts) != 1:
            raise ValueError(
                "cannot intersect pair-index rules with different law_count values"
            )
        law_count = law_counts.pop()
        pair_indexes = set.intersection(
            *(set(rule.pair_indexes) for rule in pair_index_rules)
        )
        for source_target_rule in source_target_rules:
            pair_indexes = {
                pair_index
                for pair_index in pair_indexes
                if source_target_rule.covers(
                    *pair_index_to_ids(pair_index, law_count=law_count)
                )
            }
        return ExplicitPairsRule(
            pair_indexes=frozenset(pair_indexes),
            law_count=law_count,
        )
    return SourceTargetSetsRule(
        source_ids=frozenset.intersection(
            *(rule.source_ids for rule in source_target_rules)
        ),
        target_ids=frozenset.intersection(
            *(rule.target_ids for rule in source_target_rules)
        ),
        excluded_blocks=tuple(
            block
            for rule in source_target_rules
            for block in rule.excluded_blocks
        ),
    )
