# 10.220.69.172 远程评测服务使用说明

## 一句话结论

`http://10.220.69.172:8888` 当前提供 `simple-api` 远程评测服务，可以把本地 `solver.py` 和题目列表提交到服务器，由服务器运行 Stage 2 Solo 官方 parallel evaluator（并行评测器）和 Lean judge（Lean 验证器）。得分口径仍然只看 judge 接受的 certificate（证书）。

## 服务定位

- base URL（接口根地址）：`http://10.220.69.172:8888`
- 健康检查：`GET /health`
- 创建评测：`POST /runs`
- 查询评测：`GET /runs/<run_id>`
- 查看日志尾部：`GET /runs/<run_id>/tail?lines=80`
- 取消评测：`POST /runs/<run_id>/cancel`
- 列出已有评测：`GET /runs`

注意：这是远程评测服务，不是 LLM endpoint（大模型接口）。2026-05-11 本地检查时，`http://10.220.69.172:8888/health` 可用；`http://10.220.69.172:30197/v1/models` 未返回可用 LLM models 响应。

## 使用前约定

1. `run_id` 必须唯一，建议格式为：`remote-<name>-<purpose>-$(date +%Y%m%d-%H%M%S)`。
2. `run_id` 只能使用字母、数字、下划线、点和连字符，最长 `128` 字符。
3. `solver.py` 不能超过 `500000` bytes。
4. 共享服务没有鉴权，不要提交私密 token、未公开数据或不应共享的 solver。
5. 大批量 run 会占用服务器 Lean/CPU 资源，`max_workers=24` 这类配置应先和同事协调；smoke 或小样本建议从 `1` 到 `6` 开始。
6. 大批量 run 可设置 `problems_per_shard`，让每个 official runner shard（官方 runner 分片）处理多题，减少进程启动和文件系统开销；默认值是 `1`，保留旧的一题一 shard 行为。
7. 新版服务默认启用 evaluator cache（评估器缓存）：exact-result cache（完整题目结果缓存）和 judge-call cache（Lean judge 调用缓存）。最终晋级或报分证据建议显式设置 `"cache": false` 跑一次无缓存 gate。

## 1. 检查服务是否可用

```bash
BASE_URL="http://10.220.69.172:8888"
curl -fsS "$BASE_URL/health"
```

正常返回类似：

```json
{"port":8888,"service":"simple-api","status":"ok"}
```

## 2. 跑一个最小 smoke

下面命令会读取本地 `solvers/solo_official/current/solver.py`，提交 1 道内联题目到远程服务。推荐先跑这个确认链路。

```bash
BASE_URL="http://10.220.69.172:8888"
RUN_ID="remote-${USER:-user}-smoke-$(date +%Y%m%d-%H%M%S)"
PAYLOAD="/tmp/${RUN_ID}.json"

python3 - "$RUN_ID" > "$PAYLOAD" <<'PY'
import json
import sys
from pathlib import Path

run_id = sys.argv[1]
problem = {
    "answer": True,
    "eq1_id": 5,
    "eq2_id": 2638,
    "equation1": "x = y ◇ x",
    "equation2": "x = (y ◇ ((z ◇ w) ◇ u)) ◇ x",
    "id": "true_5_2638",
}
payload = {
    "run_id": run_id,
    "solver_text": Path("solvers/solo_official/current/solver.py").read_text(encoding="utf-8"),
    "problems": [problem],
    "max_workers": 1,
    "problems_per_shard": 1,
    "cache": True,
}
print(json.dumps(payload, ensure_ascii=False))
PY

curl -fsS \
  -X POST "$BASE_URL/runs" \
  -H 'Content-Type: application/json' \
  --data-binary @"$PAYLOAD" \
  | python3 -m json.tool

echo "$RUN_ID"
```

如果服务接受请求，HTTP 状态是 `202`，返回 JSON 里会包含 `run_id`、`status`、`summary`、`progress` 等字段。刚提交时 `status` 可能是 `running`，稍后再查即可。

## 3. 查询进度和结果

```bash
curl -fsS "$BASE_URL/runs/$RUN_ID" | python3 -m json.tool
```

常用字段：

- `status`：`running`、`done`、`failed`、`cancelled` 或 `unknown`。
- `progress.processed`：已处理题目数。
- `progress.solved`：当前日志中显示的 solved 数。
- `summary.accepted`：judge 接受数。
- `summary.rejected`：judge 拒绝数。
- `summary.errors`：运行错误数。
- `summary.llmTotalCalls`：评测过程中记录的 LLM 调用数。
- `summary.judgeTotalCalls`：judge 调用数。
- `summary.sets[].cache`：缓存信息。常见字段包括 `exactResultHits`、`exactResultMisses`、`exactResultWrites` 和 `judgeCallPath`。注意 `judgeTotalCalls` 仍按 solver 协议调用计数统计；命中 judge-call cache 时不会真实启动 Lean。

需要最终无缓存证据时，在 payload 顶层加入：

```json
{
  "cache": false
}
```

查看 driver log（驱动日志）尾部：

```bash
curl -fsS "$BASE_URL/runs/$RUN_ID/tail?lines=80" | python3 -m json.tool
```

列出服务器当前能看到的 run：

```bash
curl -fsS "$BASE_URL/runs" | python3 -m json.tool
```

当前 API 只直接返回摘要、进度和日志尾部。完整产物仍在服务器 `run_dir` 下，例如 `results/*.json`、`history.md` 和 `submission/solver.py`；需要这些文件时，需要有服务器文件系统访问权限，或请服务维护者临时导出。

## 4. 提交本地 JSONL 题目批次

如果题目文件在本地，例如 `data/processed/order4_splits/dev_fast.jsonl`，推荐把题目作为 `problems` 内联提交，避免依赖服务器上是否有同一路径文件。

```bash
BASE_URL="http://10.220.69.172:8888"
RUN_ID="remote-${USER:-user}-dev-fast-$(date +%Y%m%d-%H%M%S)"
SOLVER="solvers/solo_official/current/solver.py"
PROBLEMS="data/processed/order4_splits/dev_fast.jsonl"
PAYLOAD="/tmp/${RUN_ID}.json"

python3 - "$RUN_ID" "$SOLVER" "$PROBLEMS" > "$PAYLOAD" <<'PY'
import json
import sys
from pathlib import Path

run_id, solver_path, problem_path = sys.argv[1:4]
problems = [
    json.loads(line)
    for line in Path(problem_path).read_text(encoding="utf-8").splitlines()
    if line.strip()
]
payload = {
    "run_id": run_id,
    "solver_text": Path(solver_path).read_text(encoding="utf-8"),
    "problems": problems,
    "max_workers": 6,
    "problems_per_shard": 50,
    "cache": True,
}
print(json.dumps(payload, ensure_ascii=False))
PY

curl -fsS \
  -X POST "$BASE_URL/runs" \
  -H 'Content-Type: application/json' \
  --data-binary @"$PAYLOAD" \
  | python3 -m json.tool
```

如果确认题目文件已经存在于服务器仓库内，也可以改用 `problem_set`：

```json
{
  "run_id": "remote-name-dev-fast-20260511-001",
  "solver_text": "<solver.py content>",
  "problem_set": "data/processed/order4_splits/dev_fast.jsonl",
  "max_workers": 6,
  "problems_per_shard": 50,
  "cache": true
}
```

`problem_set` 必须是服务器 repo root（仓库根目录）内存在的文件；否则接口会返回 `400`。

## 5. 取消正在运行的任务

```bash
curl -fsS -X POST "$BASE_URL/runs/$RUN_ID/cancel" | python3 -m json.tool
```

取消后再查询：

```bash
curl -fsS "$BASE_URL/runs/$RUN_ID" | python3 -m json.tool
```

## 6. 常见错误

| 现象 | 含义 | 处理方式 |
| --- | --- | --- |
| `400 provide exactly one of solver_path or solver_text` | `solver_path` 和 `solver_text` 必须二选一 | 给同事用时优先使用 `solver_text` |
| `400 provide exactly one of problem_set or problems` | `problem_set` 和 `problems` 必须二选一 | 本地题目文件优先转成 `problems` |
| `400 solver.py exceeds 500000 bytes` | solver 超过官方提交大小硬约束 | 先压缩 solver 或切换版本 |
| `400 run_id must match ...` | `run_id` 含非法字符或过长 | 只用字母、数字、`_`、`.`、`-` |
| `400 cache_dir must be inside repo root` | 自定义缓存目录不在服务器仓库内 | 默认不要传 `cache_dir`；需要隔离缓存时传仓库内路径 |
| `409 run directory already exists` | `run_id` 已被用过 | 换一个新的 `run_id` |
| `404 unknown run` | 服务器找不到该 run | 检查 `RUN_ID` 是否复制正确 |
| `status=failed` | evaluator 或 judge 运行失败 | 先看 `/tail?lines=200` |
| curl 超时或连接失败 | 服务不可达或内网不通 | 确认是否在同一网络，并检查 `:8888/health` |

## 7. 结果口径

远程服务只是把评测搬到 `10.220.69.172` 上执行；它不改变 Stage 2 Solo 的得分边界：

- false problem（假命题）必须输出 judge 可验证的反例证书。
- true problem（真命题）必须输出 Lean 4 可验证证明。
- LLM 输出如果没有通过官方 judge，不能计为 accepted。
- 汇报时优先引用 `summary.accepted`、`summary.rejected`、`summary.errors` 和 `summary.llmTotalCalls`。

## 8. 当前已验证信息

2026-05-11 本地检查结果：

- `GET http://10.220.69.172:8888/health` 返回 `{"port":8888,"service":"simple-api","status":"ok"}`。
- `GET http://10.220.69.172:8888/runs` 可返回已有 run 列表，当前 `output_root` 为 `/workspace/artifacts/runs/2026-05-09`。
- API 行为来源于仓库内 `src/simple_api/app.py` 和 `src/simple_api/remote_eval.py`。
- 部署脚本为 `scripts/evaluator/deploy_simple_api_local.sh`，容器默认监听 `8888`。
