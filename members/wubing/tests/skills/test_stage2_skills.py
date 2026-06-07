import re
from pathlib import Path


def test_stage2_skill_directories_exist():
    root = Path(__file__).resolve().parents[2]
    expected = [
        root / "skills" / "stage2-train-start",
        root / "skills" / "stage2-train-evaluate",
        root / "skills" / "stage2-train-analyze-run",
        root / "skills" / "stage2-train-improve-solver",
        root / "skills" / "stage2-train-offline-explore-solver",
        root / "skills" / "stage2-train-proof-seed",
        root / "skills" / "stage2-train-version-solver",
        root / "skills" / "stage2-info-competition",
        root / "skills" / "stage2-info-zulip-channel",
        root / "skills" / "stage2-report-solver-baseline",
        root / "skills" / "stage2-strategy-start",
        root / "skills" / "stage2-strategy-mine-setcheck",
        root / "skills" / "stage2-strategy-mine-true-template",
        root / "skills" / "stage2-strategy-mine-false-predicate",
        root / "skills" / "stage2-strategy-explore",
        root / "skills" / "stage2-strategy-report",
    ]
    for path in expected:
        assert path.is_dir(), f"missing skill directory: {path}"

    removed = [
        root / "skills" / "stage2-optimize-cheatsheet",
        root / "skills" / "stage2-version-cheatsheet",
        root / "skills" / "stage2-train-explore-solver",
        root / "skills" / "stage2-update-competition-info",
        root / "skills" / "stage2-update-zulip-channel",
    ]
    for path in removed:
        assert not path.exists(), f"removed skill still exists: {path}"


def frontmatter_text(skill_dir: Path) -> str:
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    assert match, f"missing frontmatter in {skill_dir / 'SKILL.md'}"
    return match.group(1)


def test_stage2_evaluate_skill_targets_official_solver_runs():
    root = Path(__file__).resolve().parents[2]
    skill_dir = root / "skills" / "stage2-train-evaluate"
    frontmatter = frontmatter_text(skill_dir)
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    defaults = (skill_dir / "references" / "evaluator-defaults.md").read_text(encoding="utf-8")

    assert "name: stage2-train-evaluate" in frontmatter
    assert "official Stage 2 Solo solver evaluation" in frontmatter
    assert "run_official_solo_history.py" in text
    assert "run_official_solo_history_parallel.py" in text
    assert "http://10.220.69.172:8890" in text
    assert "judge-v2" in text
    assert "local diagnostic run" in text
    assert "history.md" in text
    assert "order4_splits" in text
    assert "dev_fast" in text
    assert "dev_main" in text
    assert "test_locked" in text
    assert "sample200" not in text
    assert "`sample20`" not in text
    assert "`sample_20`" not in text
    assert "sample_20.json" not in text
    assert "order4_splits" in defaults
    assert "dev_fast" in defaults
    assert "dev_main" in defaults
    assert "test_locked" in defaults
    assert "sample200" not in defaults
    assert "run_official_solo_history_parallel.py" in defaults
    assert "--max-workers" in defaults
    assert "http://10.220.69.172:8890" in defaults
    assert "judge-v2" in defaults
    assert "Local diagnostic entrypoint" in defaults
    assert "`sample20`" not in defaults
    assert "`sample_20`" not in defaults
    assert "sample_20.json" not in defaults
    assert "cheatsheet" not in text.lower()
    assert "solvers/solo_official/current/solver.py" in text
    assert "failed subset" in text
    assert "solver snapshot" in text
    assert "solver_snapshot.json" in text
    assert "submission/solver.py" in text
    assert "submissions/solo_official/solver.py" not in text
    assert (skill_dir / "agents" / "openai.yaml").exists()
    assert (skill_dir / "references" / "stage2-shared-rules.md").exists()


def test_stage2_train_start_skill_coordinates_training_loop():
    root = Path(__file__).resolve().parents[2]
    skill_dir = root / "skills" / "stage2-train-start"
    frontmatter = frontmatter_text(skill_dir)
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")

    assert "name: stage2-train-start" in frontmatter
    assert "continue training" in frontmatter
    assert "stage2-train-analyze-run" in text
    assert "stage2-train-version-solver" in text
    assert "stage2-train-improve-solver" in text
    assert "stage2-train-offline-explore-solver" in text
    assert "stage2-train-proof-seed" in text
    assert "stage2-train-evaluate" in text
    assert "Do not load `stage2-report-solver-baseline`" in text
    assert "without asking for \"next step\" confirmation" in text
    assert "Intermediary updates should name the stage2 skills" in text
    assert "do not force a skill-name prefix" in text
    assert "promote the draft automatically" in text
    assert "order4 split" in text
    assert "dev_fast" in text
    assert "dev_main" in text
    assert "test_locked" in text
    assert "sample200" not in text
    assert "promoting a draft into `versions/` or updating `current/`" not in text


def test_stage2_explore_solver_skill_guides_offline_solver_direction():
    root = Path(__file__).resolve().parents[2]
    skill_dir = root / "skills" / "stage2-train-offline-explore-solver"
    frontmatter = frontmatter_text(skill_dir)
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")

    assert "name: stage2-train-offline-explore-solver" in frontmatter
    assert "offline" in frontmatter
    assert "solver improvement direction" in frontmatter
    assert "remaining failures" in text
    assert "candidate solver strategy" in text
    assert "bounded probes" in text
    assert "stage2-train-analyze-run" in text
    assert "stage2-train-improve-solver" in text
    assert "stage2-train-proof-seed" in text
    assert "Do not edit `solver.py`" in text
    assert "known-proof table" in text
    assert (skill_dir / "agents" / "openai.yaml").exists()


def test_stage2_strategy_skills_route_and_mine_registry_work():
    root = Path(__file__).resolve().parents[2]
    start_dir = root / "skills" / "stage2-strategy-start"
    mine_dir = root / "skills" / "stage2-strategy-mine-setcheck"
    true_dir = root / "skills" / "stage2-strategy-mine-true-template"
    false_dir = root / "skills" / "stage2-strategy-mine-false-predicate"
    explore_dir = root / "skills" / "stage2-strategy-explore"
    report_dir = root / "skills" / "stage2-strategy-report"

    for path in [start_dir, mine_dir, true_dir, false_dir, explore_dir, report_dir]:
        assert path.is_dir(), f"missing strategy skill directory: {path}"
        assert (path / "SKILL.md").exists(), f"missing SKILL.md: {path}"
        assert (path / "agents" / "openai.yaml").exists(), f"missing openai.yaml: {path}"

    start = (start_dir / "SKILL.md").read_text(encoding="utf-8")
    mine = (mine_dir / "SKILL.md").read_text(encoding="utf-8")
    true = (true_dir / "SKILL.md").read_text(encoding="utf-8")
    false = (false_dir / "SKILL.md").read_text(encoding="utf-8")
    explore = (explore_dir / "SKILL.md").read_text(encoding="utf-8")
    report = (report_dir / "SKILL.md").read_text(encoding="utf-8")

    assert "name: stage2-strategy-start" in frontmatter_text(start_dir)
    assert "stage2-strategy-mine-setcheck" in start
    assert "stage2-strategy-mine-true-template" in start
    assert "stage2-strategy-mine-false-predicate" in start
    assert "stage2-strategy-explore" in start
    assert "stage2-strategy-report" in start
    assert "2026-05-18-order5-parallel-deterministic-mining.md" in start
    assert "Do not edit `solver.py`" in start
    assert "current unresolved residual" in start
    for text in [start, mine, true, false, explore]:
        assert "coverage_summary.unresolved_estimate" in text
        assert "coverage_summary.json" in text
        assert "coverage_scope" in text
        assert "includes_order4_source_to_order4_target" in text
        assert "9.57" not in text
        assert "total_pairs=3,915,693,200" not in text

    assert "name: stage2-strategy-mine-setcheck" in frontmatter_text(mine_dir)
    assert "_finmodel_sets" in mine
    assert "_union_count_for_rules" in mine
    assert "current_union" in mine
    assert "setcheck_increment_history.jsonl" in mine
    assert "不设置 order4×order4 `excluded_blocks`" in mine
    assert "order4 source -> order4 target" in mine
    assert "order4 source -> order5 target" in mine
    assert "Do not edit `solver.py`" in mine
    assert "current unresolved residual" in mine

    assert "name: stage2-strategy-mine-true-template" in frontmatter_text(true_dir)
    assert "true.proof.templatecheck" in true
    assert "singleton_collapse" in true
    assert "singleton_seedbank_specialization" in true
    assert "term_shape_anchor.product" in true
    assert "candidates/" in true
    assert "Do not edit `solver.py`" in true
    assert "current unresolved residual" in true
    assert "residual_cluster_report_20260518.json" in true
    assert "2026-05-18-order5-residual-cluster-analysis.md" in true
    assert "Coverage Reporting Requirement" in true
    assert "coverage_summary.total_pairs" in true
    assert "after_merge_projection" in true
    assert "不能替代 union increment" in true

    assert "name: stage2-strategy-mine-false-predicate" in frontmatter_text(false_dir)
    assert "false.finmodel.predicatecheck" in false
    assert "paircheck bank" in false
    assert "estimated_union_increment" in false
    assert "1_000_000" in false
    assert "candidates/" in false
    assert "Do not edit `solver.py`" in false
    assert "current unresolved residual" in false
    assert "residual_cluster_report_20260518.json" in false
    assert "2026-05-18-order5-residual-cluster-analysis.md" in false
    assert "Coverage Reporting Requirement" in false
    assert "coverage_summary.total_pairs" in false
    assert "after_merge_projection" in false
    assert "不能替代 union increment" in false

    assert "name: stage2-strategy-explore" in frontmatter_text(explore_dir)
    assert "stage2-strategy-mine-setcheck" in explore
    assert "stage2-strategy-mine-true-template" in explore
    assert "stage2-strategy-mine-false-predicate" in explore
    assert "paircheck" in explore
    assert "predicatecheck" in explore
    assert "Parallel Candidate Mode" in explore
    assert "current unresolved residual" in explore
    assert "residual cluster report" in explore

    assert "name: stage2-strategy-report" in frontmatter_text(report_dir)
    assert "coverage_summary.json" in report
    assert "setcheck_increment_history.jsonl" in report
    assert "unresolved_estimate" in report


def test_stage2_proof_seed_skill_prepares_bounded_true_failure_seeds():
    root = Path(__file__).resolve().parents[2]
    skill_dir = root / "skills" / "stage2-train-proof-seed"
    frontmatter = frontmatter_text(skill_dir)
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")

    assert "name: stage2-train-proof-seed" in frontmatter
    assert "proof-seed data" in frontmatter
    assert "external proof trace clustering" in frontmatter
    assert "stage2-train-offline-explore-solver" in text
    assert "lean-proof" in text
    assert "offline translators" in text
    assert "Do not edit `solver.py`" in text
    assert "Do not add known-proof table entries" in text
    assert "MAX_LLM_ROUNDS" in text
    assert "docs/experiments/" in text
    assert (skill_dir / "agents" / "openai.yaml").exists()


def test_stage2_proofbank_skills_define_offline_certificate_bank_workflow():
    root = Path(__file__).resolve().parents[2]
    expected = [
        root / "skills" / "stage2-proofbank-start",
        root / "skills" / "stage2-proofbank-nightly-loop",
        root / "skills" / "stage2-proofbank-sample-candidates",
        root / "skills" / "stage2-proofbank-generate-true-certificate",
        root / "skills" / "stage2-proofbank-verify-import",
        root / "skills" / "stage2-proofbank-maintain",
        root / "skills" / "stage2-proofbank-quality-audit",
    ]
    for path in expected:
        assert path.is_dir(), f"missing proofbank skill directory: {path}"
        assert (path / "SKILL.md").exists(), f"missing SKILL.md: {path}"
        assert (path / "agents" / "openai.yaml").exists(), f"missing openai.yaml: {path}"

    start = (root / "skills" / "stage2-proofbank-start" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    generate = (
        root / "skills" / "stage2-proofbank-generate-true-certificate" / "SKILL.md"
    ).read_text(encoding="utf-8")
    verify = (root / "skills" / "stage2-proofbank-verify-import" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    maintain = (root / "skills" / "stage2-proofbank-maintain" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    nightly = (
        root / "skills" / "stage2-proofbank-nightly-loop" / "SKILL.md"
    ).read_text(encoding="utf-8")
    quality = (
        root / "skills" / "stage2-proofbank-quality-audit" / "SKILL.md"
    ).read_text(encoding="utf-8")

    assert "name: stage2-proofbank-start" in frontmatter_text(
        root / "skills" / "stage2-proofbank-start"
    )
    assert "offline Stage 2 GPT/Codex true certificate bank generation" in start
    assert "stage2-proofbank-sample-candidates" in start
    assert "stage2-proofbank-generate-true-certificate" in start
    assert "stage2-proofbank-verify-import" in start
    assert "stage2-proofbank-maintain" in start
    assert "stage2-proofbank-nightly-loop" in start
    assert "Do not edit `solver.py`" in start
    assert "test_locked" in start

    assert "name: stage2-proofbank-nightly-loop" in frontmatter_text(
        root / "skills" / "stage2-proofbank-nightly-loop"
    )
    assert "24-hour" in nightly
    assert "stage2-proofbank-quality-audit" in nightly
    assert "direct_order4_true_exploration" in nightly
    assert "marathon_state.json" in nightly
    assert "proof_bank_nightly_loop.py" in nightly
    assert "awaiting_codex_generation" in nightly
    assert "Codex session" in nightly
    assert "does not daemonize proof generation" in nightly
    assert "explicit user authorization" in nightly
    assert "Do not edit `solver.py`" in nightly
    assert "test_locked" in nightly

    assert "name: stage2-proofbank-generate-true-certificate" in frontmatter_text(
        root / "skills" / "stage2-proofbank-generate-true-certificate"
    )
    assert "Use the current Codex model" in generate
    assert "raw_response_path" in generate
    assert "Do not call the judge" in generate
    assert "Use `◇` and `congrArg`" in generate
    assert (
        root
        / "skills"
        / "stage2-proofbank-generate-true-certificate"
        / "references"
        / "prompt-item-contract.md"
    ).exists()

    sample = (
        root / "skills" / "stage2-proofbank-sample-candidates" / "SKILL.md"
    ).read_text(encoding="utf-8")
    assert "name: stage2-proofbank-sample-candidates" in frontmatter_text(
        root / "skills" / "stage2-proofbank-sample-candidates"
    )
    assert "可复现" in sample
    assert "分层随机抽样" in sample
    assert "candidate_pools/" in sample
    assert "direct_order4_true_exploration" in sample
    assert "22M" in sample
    assert "must draw from `data/processed/order4_implication_problems/`" in sample
    assert "seed" in sample
    assert "test_locked" in sample
    assert "Do not edit `solver.py`" in sample

    assert "name: stage2-proofbank-verify-import" in frontmatter_text(
        root / "skills" / "stage2-proofbank-verify-import"
    )
    assert "official Stage 2 judge" in verify
    assert "Do not synthesize or repair proofs" in verify
    assert "generated_attempts.jsonl" in verify
    assert (
        root
        / "skills"
        / "stage2-proofbank-verify-import"
        / "references"
        / "judge-result-contract.md"
    ).exists()

    assert "name: stage2-proofbank-maintain" in frontmatter_text(
        root / "skills" / "stage2-proofbank-maintain"
    )
    assert "data/processed/proof_banks/gpt_true_certificates/" in maintain
    assert "dry-run before write" in maintain
    assert "Do not generate proofs" in maintain
    assert (
        root / "skills" / "stage2-proofbank-maintain" / "references" / "bank-contract.md"
    ).exists()

    assert "name: stage2-proofbank-quality-audit" in frontmatter_text(
        root / "skills" / "stage2-proofbank-quality-audit"
    )
    assert "accepted yield" in quality
    assert "source balance" in quality
    assert "proof_bank_quality_audit.py" in quality
    assert "22M" in quality
    assert "Do not edit `solver.py`" in quality
    assert "test_locked" in quality


def test_stage2_analyze_run_skill_classifies_actionable_failures():
    root = Path(__file__).resolve().parents[2]
    skill_dir = root / "skills" / "stage2-train-analyze-run"
    frontmatter = frontmatter_text(skill_dir)
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    rules = (skill_dir / "references" / "stage2-shared-rules.md").read_text(encoding="utf-8")

    assert "name: stage2-train-analyze-run" in frontmatter
    for label in [
        "Lean compile error",
        "Lean timeout",
        "certificate rejected",
        "LLM timeout",
        "LLM malformed",
        "true proof miss",
        "false countermodel miss",
    ]:
        assert label in text
    assert "failed ids subset" in text
    assert "draft selection" in text
    assert "order4 split" in text
    assert "dev_fast" in text
    assert "dev_main" in text
    assert "test_locked" in text
    assert "do not infer success from solver logs alone" in rules


def test_stage2_improve_solver_skill_preserves_single_file_contract():
    root = Path(__file__).resolve().parents[2]
    skill_dir = root / "skills" / "stage2-train-improve-solver"
    frontmatter = frontmatter_text(skill_dir)
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    rules = (skill_dir / "references" / "solver-rules.md").read_text(encoding="utf-8")

    assert "name: stage2-train-improve-solver" in frontmatter
    assert "solver.py" in text
    assert "solvers/solo_official/{current,drafts,versions}" in text
    assert "stage2-train-version-solver" in text
    assert "stage2-train-offline-explore-solver" in text
    assert "drafts/YYYY-MM-DD/dN" in text
    assert "submissions/solo_official/solver.py" in rules
    assert "solvers/solo_official/current/" in rules
    assert "exactly one regular file" in rules
    assert "known-proof table" in text
    assert "hard-to-generalize" in text
    assert "order4 split evidence" in text
    assert "dev_fast" in text
    assert "dev_main" in text
    assert "test_locked" in text
    assert "Avoid sample memorization" in rules
    assert "small-dataset misses" in rules


def test_stage2_version_solver_skill_manages_solver_lifecycle():
    root = Path(__file__).resolve().parents[2]
    skill_dir = root / "skills" / "stage2-train-version-solver"
    frontmatter = frontmatter_text(skill_dir)
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    rules = (skill_dir / "references" / "solver-versioning-rules.md").read_text(encoding="utf-8")

    assert "name: stage2-train-version-solver" in frontmatter
    assert "solver version lifecycle" in frontmatter
    assert "current" in text
    assert "drafts" in text
    assert "versions" in text
    assert "submissions/solo_official/" in text
    assert "manifest.json" in text
    assert "notes.md" in text
    assert "hash" in text
    assert "accepted rate" in text
    assert "promote" in text
    assert "drafts/YYYY-MM-DD/dN" in text
    assert "versions/YYYY-MM-DD/vN" in text
    assert "solver_snapshot.json" in text
    assert "artifacts/runs/YYYY-MM-DD/<run-id>/submission/solver.py" in text
    assert "solvers/solo_official/current/" in rules
    assert "solvers/solo_official/drafts/YYYY-MM-DD/dN/" in rules
    assert "solvers/solo_official/versions/YYYY-MM-DD/vN/" in rules
    assert "solver_snapshot.json" in rules
    assert "Do not overwrite existing versions" in rules
    assert (skill_dir / "agents" / "openai.yaml").exists()


def test_stage2_report_solver_baseline_skill_covers_reports_and_pdf():
    root = Path(__file__).resolve().parents[2]
    skill_dir = root / "skills" / "stage2-report-solver-baseline"
    frontmatter = frontmatter_text(skill_dir)
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")

    assert "name: stage2-report-solver-baseline" in frontmatter
    assert "Stage 2 Solo solver baseline" in frontmatter
    assert "docs/reports/" in text
    assert "docs/experiments/" in text
    assert "LLM calls / solved" in text
    assert "accepted rate" in text
    assert "solver.py" in text
    assert "Python code snippets" in text
    assert "same directory" in text
    assert "pdftoppm" in text
    assert "pdftotext" in text
    assert "Do not edit official runner result JSON" in text
    assert (skill_dir / "agents" / "openai.yaml").exists()


def test_docs_readme_mentions_solver_skills():
    text = (Path(__file__).resolve().parents[2] / "docs" / "README.md").read_text(encoding="utf-8")
    assert "skills/" in text
    assert "stage2-train-improve-solver" in text
    assert "stage2-train-version-solver" in text
    assert "stage2-report-solver-baseline" in text
    assert "stage2-info-competition" in text
    assert "stage2-info-zulip-channel" in text
    assert "zulip-digests" in text
    assert "architecture.md` 是唯一的当前架构说明文档" in text
    assert "solver-versioning.md" not in text
    assert "cheatsheet" not in text.lower()


def test_architecture_mentions_solver_first_skills_role():
    text = (Path(__file__).resolve().parents[2] / "docs" / "architecture.md").read_text(encoding="utf-8")
    assert "stage2-*" in text
    assert "solver.py" in text
    assert "submissions/solo_official" in text
    assert "solvers/solo_official" in text
    assert "stage2-info-competition" in text
    assert "stage2-info-zulip-channel" in text
    assert "stage2-train-version-solver" in text
    assert "drafts/YYYY-MM-DD/dN" in text
    assert "versions/YYYY-MM-DD/vN" in text
    assert "solver_snapshot.json" in text
    assert "cheatsheet" not in text.lower()


def test_solver_versioning_is_documented_in_architecture_only():
    root = Path(__file__).resolve().parents[2]
    assert not (root / "docs" / "solver-versioning.md").exists()


def test_data_inventory_mentions_zulip_archive_paths():
    text = (Path(__file__).resolve().parents[2] / "docs" / "data-inventory.md").read_text(
        encoding="utf-8"
    )
    assert "data/raw/references/zulip" in text
    assert "docs/zulip-digests" in text


def test_openai_yaml_mentions_matching_skill_names():
    root = Path(__file__).resolve().parents[2]
    for name in [
        "stage2-train-start",
        "stage2-train-evaluate",
        "stage2-train-analyze-run",
        "stage2-train-improve-solver",
        "stage2-train-offline-explore-solver",
        "stage2-train-proof-seed",
        "stage2-train-version-solver",
        "stage2-info-competition",
        "stage2-info-zulip-channel",
        "stage2-report-solver-baseline",
    ]:
        text = (root / "skills" / name / "agents" / "openai.yaml").read_text(encoding="utf-8")
        assert f'default_prompt: "Use ${name}' in text
        assert "allow_implicit_invocation: true" in text


def test_stage2_info_competition_skill_mentions_official_snapshots():
    skill_dir = (
        Path(__file__).resolve().parents[2]
        / "skills"
        / "stage2-info-competition"
    )
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = frontmatter_text(skill_dir)

    assert "name: stage2-info-competition" in frontmatter
    assert "update, refresh, crawl, fetch, sync, or verify" in frontmatter
    assert "scripts/data/download_public_data.py" in text
    assert "data/raw/references/stage2_judge" in text
    assert "data/raw/references/stage2_judge/judge/verify.py" in text
    assert "BANNED_PROOF_TOKENS" in text
    assert "external/equational-theories-lean-stage2" in text
    assert "docs/competition-analysis.md" in text


def test_stage2_info_zulip_channel_skill_mentions_archive_and_digest_paths():
    skill_dir = (
        Path(__file__).resolve().parents[2]
        / "skills"
        / "stage2-info-zulip-channel"
    )
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = frontmatter_text(skill_dir)

    assert "name: stage2-info-zulip-channel" in frontmatter
    assert "Zulip" in frontmatter
    assert "scripts/data/sync_zulip_channel.py" in text
    assert "data/raw/references/zulip" in text
    assert "docs/zulip-digests" in text
    assert "ZULIP_CONFIG_FILE" in text
    assert "stage2-info-competition" in text
    assert "judge/verify.py" in text
    assert "tactic" in text
    assert "cron" in text
    assert "systemd timer" in text
    assert "不能可靠发送到当前 ChatGPT thread" in text
    assert "中文为主" in text
    assert "中英对照" in text
    assert (skill_dir / "agents" / "openai.yaml").exists()
