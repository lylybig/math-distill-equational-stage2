# 远程 simple-api Backend Pool 使用决策

## 结论

当前同时保留两套 Stage 2 remote simple-api（远程评测接口）：

- `http://10.220.69.172:8888`
- `http://10.220.69.153:8888`

短期不增加普通路由或反向代理服务。后续调用远程 judge（官方验证器）时，优先在客户端选择 backend（后端）：一次完整 evaluator run 固定到一台服务；proofbank（证明库）这种一题一 run 的批量验证可以按请求分摊到两台服务。

## 已验证状态

截至 2026-05-20，`153` 和 `172` health 均可用；当前挖掘优先使用 32 核的 `172`，`153` 作为 fallback。

历史验证记录：

- `http://10.220.69.153:8888/health` 返回 `{"port": 8888, "service": "simple-api", "status": "ok"}`。
- 153 smoke run：`remote-153-smoke-bing-20260514-151359`。
  - `status=done`
  - `accepted=1`
  - `rejected=0`
  - `errors=0`
  - `judgeTotalCalls=1`
  - `llmTotalCalls=0`
  - 日志尾部包含 `Result: 1A / 0R / 0E over 1 problems`
  - `output_root=/workspace/artifacts/runs/2026-05-14`
- 172 的既有使用说明见 `docs/reports/2026-05-11-remote-simple-api-10-220-69-172-usage.md`。

## 为什么不先做普通路由服务

`simple-api` 是有状态服务。`POST /runs` 在某台机器创建 run directory（运行目录），后续这些接口必须打到同一台机器：

- `GET /runs/<run_id>`
- `GET /runs/<run_id>/tail?lines=...`
- `POST /runs/<run_id>/cancel`

普通 Nginx/HAProxy 轮询会导致：

```text
POST /runs -> 153
GET /runs/<run_id> -> 172
结果：404 unknown run
```

除非新路由服务维护 `run_id -> backend` 映射、健康检查、持久化、取消和日志转发，否则它会引入新的状态服务和单点。当前没有必要先承担这部分复杂度。

## 推荐调用策略

### 1. 手动选择

当前挖掘优先使用 172：

```bash
export STAGE2_REMOTE_JUDGE_BASE_URL="http://10.220.69.172:8888"
export STAGE2_REMOTE_JUDGE_MAX_WORKERS="16"
```

需要回退到 153：

```bash
export STAGE2_REMOTE_JUDGE_BASE_URL="http://10.220.69.153:8888"
```

### 2. 后续自动选择

使用客户端 backend pool（后端池）配置时，当前默认顺序应写成：

```bash
export STAGE2_REMOTE_JUDGE_BASE_URLS="http://10.220.69.172:8888,http://10.220.69.153:8888"
export STAGE2_REMOTE_JUDGE_MAX_WORKERS="16"
```

自动选择规则：

- 调用前对每个 backend 做 `GET /health`。
- 完整 evaluator run：选择一台健康 backend，整个 run 生命周期都固定使用这台 backend，并把选中的 URL 写入 run metadata（元数据）或报告。
- proofbank 一题一 run 批量验证：可以按请求 round-robin（轮询）或 least-recently-used（最久未使用）分摊到多台 backend。
- 只有在 run 尚未创建成功前，才自动换另一台 backend。
- 一旦某个 run 已经创建，后续 `GET /runs/<run_id>`、`/tail`、`/cancel` 必须继续访问创建该 run 的 backend。
- 如果已创建 run 后 backend 失联，不要假装在另一台机器恢复同一个 run；应记录失败，必要时用新的 `run_id` 重新提交。

## 当前执行建议

当前代码已支持 `STAGE2_REMOTE_JUDGE_BASE_URLS`，并且默认 pool 顺序为 `172,153`：

- 日常 proofbank import、remote-http smoke 和小批量验证优先指定 172，或使用默认 pool。
- 172 上默认从 16 并发起步，确认服务稳定后再试 24；不直接开满 32。
- 153 保留为 fallback，避免 172 不健康或队列拥堵时阻塞挖掘。
- 报告 remote judge 结果时同时写明实际使用的 `base_url` 和 `run_id`。

## 后续实现边界

如果要把自动选择落到代码，优先改客户端：

- `src/math_distill_stage2/official_stage2_batch.py` 的 `RemoteSimpleApiJudgeConfig` 可以增加 `base_urls` 或从环境变量解析 backend pool。
- CLI 保持兼容 `--remote-judge-base-url`，新增可选 `--remote-judge-base-urls`。
- `STAGE2_REMOTE_JUDGE_BASE_URL` 继续表示单 backend。
- `STAGE2_REMOTE_JUDGE_BASE_URLS` 表示 backend pool；如果两者都设置，显式 CLI 参数优先，其次 pool，再其次单 URL 默认值。
- 不改变 official runner、Lean judge 或 solver 协议。

只有当多人需要一个固定入口，并且愿意维护有状态 `run_id` 粘滞路由时，再考虑单独的 router service（路由服务）。
