# Lean4 Docker Executor Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 counterexample asset（反例资产）增加可复用 Lean4 执行器，先支持本地进程和本地 Docker 并发验证。

**Architecture:** 把 Lean 执行从资产导出逻辑中抽象出来，形成 `LeanTask -> LeanExecutor -> LeanExecutionResult`。资产验证脚本只处理 `data/assets/counterexamples/<problem_key>/runs/<run_id>/certificate.lean`，并把结果写回同一 run 目录，同时刷新索引状态。

**Tech Stack:** Python 标准库、pytest、Docker CLI、Lean 4。

---

## Chunk 1: 执行器核心与 Docker 后端

### Task 1: 写执行器单元测试

**Files:**
- Create: `tests/test_lean_executor.py`

- [x] **Step 1: Write the failing tests**

覆盖：

- `LocalLeanExecutor` 调用 `lean <certificate>`，返回 `passed`。
- `LocalLeanExecutor` 超时时返回 `timeout`。
- `DockerLeanExecutor` 生成包含 `docker run --rm --network none -v <run-dir>:/work:ro` 的命令。
- `DockerLeanExecutor` 记录 image、CPU、memory。

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/test_lean_executor.py -q
```

Expected: FAIL because executor modules do not exist.

### Task 2: 实现执行器模块

**Files:**
- Create: `src/math_distill_stage2/lean_executor/base.py`
- Create: `src/math_distill_stage2/lean_executor/local.py`
- Create: `src/math_distill_stage2/lean_executor/docker.py`

- [x] **Step 1: Implement minimal executor code**

实现：

- `LeanTask`
- `LeanExecutionResult`
- `LeanExecutor`
- `LocalLeanExecutor`
- `DockerLeanExecutor`

- [x] **Step 2: Run tests**

Run:

```bash
pytest tests/test_lean_executor.py -q
```

Expected: PASS.

## Chunk 2: Counterexample asset 验证器

### Task 3: 写资产验证器测试

**Files:**
- Create: `tests/test_counterexample_asset_verifier.py`

- [x] **Step 1: Write the failing tests**

覆盖：

- 给定 `data/assets/counterexamples/eq1-1-eq2-2/runs/<run-id>/certificate.lean`，验证器发现并执行。
- 写入 `verification.json`。
- 刷新 `latest.json` 的 `verified`。
- 刷新 `index.jsonl` 的 `verified`。
- 刷新 `summary.json` 的 `verified` 和 verification metadata（验证元数据）。

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/test_counterexample_asset_verifier.py -q
```

Expected: FAIL because verifier module does not exist.

### Task 4: 实现资产验证器和 CLI

**Files:**
- Create: `src/math_distill_stage2/counterexample_asset_verifier.py`
- Create: `scripts/verify_counterexample_assets.py`

- [x] **Step 1: Implement verifier**

实现：

- 发现所有 matching run 的 `certificate.lean`。
- 使用传入 executor 并发验证。
- 写入每个 run 的 `verification.json`。
- 刷新 `latest.json`、`index.jsonl`、`summary.json`。

- [x] **Step 2: Implement CLI**

参数：

- `--root`
- `--run-id`
- `--backend local|docker`
- `--workers`
- `--timeout-seconds`
- `--image`
- `--cpu-limit`
- `--memory-limit`

- [x] **Step 3: Run tests**

Run:

```bash
pytest tests/test_counterexample_asset_verifier.py tests/test_counterexample_assets.py -q
```

Expected: PASS.

## Chunk 3: Docker 镜像和文档更新

### Task 5: 增加 Dockerfile

**Files:**
- Create: `docker/lean4-executor/Dockerfile`

- [x] **Step 1: Add Dockerfile**

基于 Debian slim 安装 elan，并安装指定 Lean 4 toolchain。

- [x] **Step 2: Keep Dockerfile simple**

默认 `CMD ["lean", "--version"]`。

### Task 6: 更新项目文档

**Files:**
- Modify: `docs/architecture.md`
- Modify: `docs/data-inventory.md`
- Modify: `README.md`

- [x] **Step 1: Document executor architecture**

说明 local/docker backend 和 K8s 预留。

- [x] **Step 2: Document commands**

写入本地 Docker 验证命令。

### Task 7: Final verification

- [x] **Step 1: Run targeted tests**

```bash
pytest tests/test_lean_executor.py tests/test_counterexample_asset_verifier.py tests/test_counterexample_assets.py -q
```

- [x] **Step 2: Run full tests**

```bash
pytest -q
```

- [x] **Step 3: Check git diff**

```bash
git diff -- docs src scripts tests docker README.md pyproject.toml
```
