# Lean4 Docker 执行器设计

## 背景

当前 finite magma counterexample（有限岩浆反例）的 Lean 4 证书已经按资产结构落盘：

```text
data/assets/counterexamples/<problem_key>/runs/<run_id>/certificate.lean
```

现有验证逻辑直接在 Python 里调用宿主机 `lean <certificate.lean>`。这能完成最小验证，但不够隔离，也不利于后续迁移到 Kubernetes Pod（K8s 容器任务）。

## 目标

第一版 Lean4 执行器只验证 counterexample asset（反例资产）结构中的 `certificate.lean`，并把验证结果写回同一 run 目录：

```text
data/assets/counterexamples/<problem_key>/runs/<run_id>/verification.json
```

它需要支持两个 backend（执行后端）：

- `local`：直接使用当前 WSL/宿主机里的 `lean` 命令。
- `docker`：使用本地 Docker 容器执行 `lean`，以提高隔离性和可复现性。

K8s 暂时只预留接口，不在第一版实现。

## 非目标

- 不验证任意 Lean 文件列表。
- 不负责生成 `certificate.lean`。
- 不引入 mathlib 或 `equational_theories` 依赖。
- 不在第一版实现 Kubernetes API 调度。
- 不把 executor（执行器）逻辑塞进 cheatsheet 或最终提交 solver。

## 架构

新增一个清晰边界：

```text
Counterexample asset -> LeanTask -> LeanExecutor -> LeanExecutionResult -> verification.json
```

核心文件：

- `src/math_distill_stage2/lean_executor/base.py`
  - 定义 `LeanTask`、`LeanExecutionResult`、`LeanExecutor` 协议。
  - 提供统一的时间戳、命令执行、结果序列化逻辑。
- `src/math_distill_stage2/lean_executor/local.py`
  - 实现 `LocalLeanExecutor`，直接执行 `lean <certificate.lean>`。
- `src/math_distill_stage2/lean_executor/docker.py`
  - 实现 `DockerLeanExecutor`，通过 `docker run` 验证单个证书。
- `src/math_distill_stage2/counterexample_asset_verifier.py`
  - 发现资产目录中的证书。
  - 并发验证。
  - 写回 `verification.json`。
  - 刷新 `latest.json`、`index.jsonl`、`summary.json` 中的 verified 状态。
- `scripts/verify_counterexample_assets.py`
  - 提供命令行入口。
- `docker/lean4-executor/Dockerfile`
  - 构建可复现 Lean 4 执行镜像。

## Docker 执行方式

Docker backend 每次执行单个证书时，把 run 目录只读挂载到 `/work`：

```bash
docker run --rm \
  --network none \
  --cpus 1 \
  --memory 512m \
  -v <run-dir>:/work:ro \
  <image> \
  lean /work/certificate.lean
```

默认并发建议为 `4` 到 `6`。当前 WSL 可见 8 个逻辑 CPU，因此先不默认占满全部 CPU。

## 结果格式

`verification.json` 至少包含：

```json
{
  "checked_at_utc": "2026-04-29T00:00:00Z",
  "executor_backend": "docker",
  "command": "docker run ...",
  "result": "passed",
  "returncode": 0,
  "stdout": "",
  "stderr": "",
  "timeout_seconds": 60,
  "elapsed_seconds": 1.23,
  "certificate_sha256": "...",
  "lean_image": "lean4:v4.29.1",
  "lean_image_digest": null,
  "cpu_limit": "1",
  "memory_limit": "512m"
}
```

`result` 可取：

- `passed`：Lean 返回码为 0。
- `failed`：Lean 返回码非 0。
- `timeout`：执行超时。

## K8s 迁移预留

未来 K8s backend 应复用同一个容器镜像和同一组输入输出结构：

```text
LeanTask -> Kubernetes Job/Pod -> LeanExecutionResult
```

因此第一版不把 Docker 细节暴露给资产验证脚本，只暴露 `LeanExecutor.execute(task)`。

## 测试策略

- 单元测试 `LocalLeanExecutor` 的命令、超时和结果格式。
- 单元测试 `DockerLeanExecutor` 的 `docker run` 参数，包括 `--network none`、只读挂载、CPU/内存限制。
- 单元测试资产验证器能发现 `certificate.lean`，写回 `verification.json`，并刷新 `latest.json`、`index.jsonl`、`summary.json`。
- CLI（命令行入口）至少验证 `--help` 可以运行。
