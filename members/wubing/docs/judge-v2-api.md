# judge_v2 API 接口文档

## 概览

`judge_v2` 是新的分布式 Lean judge 服务，由两层组成：

- `judge-v2-control`：总控服务，负责接收本机或上游程序请求、缓存结果、维护任务队列、选择健康且负载较低的 worker。
- `judge-v2-worker`：执行服务，负责调用官方 Stage 2 `judge/verify.py`，实际运行 Lean 校验。

调用方默认只需要访问总控：

```text
http://10.220.69.172:8890
```

当前总控后端池：

```text
http://10.220.69.172:8889
http://10.220.69.153:8889
http://10.220.69.85:8889
http://10.220.69.89:8889
```

当前每台 worker 配置 `workers_total=24`，总控可调度并发槽位约为 `4 * 24 = 96`。

## 使用建议

- 普通少量校验可以用同步接口 `POST /verify`。
- 大批量或执行时间不确定的校验建议用异步接口 `POST /jobs` + `GET /jobs/{job_id}/wait`。
- 调用方判断是否通过时，以 `status == "accepted"` 且 `error_code == "ACCEPTED"` 为准。
- 当前服务部署在内网，未加鉴权；不要暴露到公网。

## Lean 代码和 artifact 保存策略

当前 `judge_v2` 不会把提交的 Lean 代码作为 `Submission.lean`、`JudgeProblem.lean`、`Problem.lean` 或 `.olean` artifact 在 worker 服务器上永久保存。

实际校验时，官方 `verify.py` 仍需要把 Lean 文件写到磁盘供 Lean 编译使用；worker 默认会为每次 verify 创建临时 artifact 目录，校验结束后自动删除该目录。响应中的 `artifact_path` 固定返回 `null`，调用方不能依赖远端 artifact 路径取回源码或编译产物。

总控为了排队和重试，会在 job 运行期间保存完整请求体；job 进入 `done`、`failed` 或 `cancelled` 后，会把 `request_json.code` 脱敏为占位文本，只保留 `code_sha256` 和 `code_bytes` 这类审计字段。worker cache 和总控结果 cache 也不保存原始 Lean 代码，只保存判定响应或基于代码计算出的 key。

只有运维人员显式设置 worker 部署参数 `ARTIFACT_DIR` / 环境变量 `JUDGE_ARTIFACT_DIR` 时，Lean artifact 才会保留在指定目录用于调试。生产默认不设置该参数。

## 统一请求体

`/verify` 和 `/jobs` 使用相同请求体：

```json
{
  "problem": {
    "id": "p_true_basic",
    "eq1_id": 38,
    "eq2_id": 42,
    "equation1": "x ◇ x = x ◇ y",
    "equation2": "x ◇ y = x ◇ z"
  },
  "verdict": "true",
  "code": "import JudgeProblem\n\ndef submission : Goal := by\n  intro G _ h\n  intro x y z\n  rw [← h, h]\n",
  "timeout_seconds": 120
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `problem` | object | 是 | Stage 2 problem 对象。必须包含非空字符串 `id`。 |
| `problem.id` | string | 是 | 缓存和任务去重 key 的一部分。对不同测试请求应保持唯一或与真实 problem id 一致。 |
| `verdict` | string | 是 | 只能是 `"true"` 或 `"false"`。 |
| `code` | string | 是 | 完整 Lean 文件内容，通常包含 `import JudgeProblem` 和 `def submission : Goal := ...`。 |
| `timeout_seconds` | integer/null | 否 | 单次 Lean 校验 timeout。worker 会限制在自身 timeout cap 内。 |

## 同步校验

### `POST /verify`

同步提交一条校验请求。总控会创建或复用 job，等待结果返回。

```bash
curl -fsS http://10.220.69.172:8890/verify \
  -H 'Content-Type: application/json' \
  -d @/Users/yanliang3612/Documents/math-distill-equational-stage2/members/wubing/docs/request.json | python3 -m json.tool
```

通过示例：

```json
{
  "status": "accepted",
  "error_code": "ACCEPTED",
  "message": "certificate accepted",
  "verdict": "true",
  "artifact_path": null,
  "direct_declarations": [],
  "axioms": [],
  "stdout": "",
  "stderr": "",
  "cached": false,
  "elapsed_ms": 9726,
  "service_rev": "judge-214e32b70b08-lean-fbbd4a8e-mathlib-896cc56a395e",
  "control_cached": false,
  "control_job_id": "9e35fea1a12b441caa563f6842282f9a",
  "control_backend_url": "http://10.220.69.153:8889"
}
```

未通过示例：

```json
{
  "status": "incorrect",
  "error_code": "LEAN_REJECTED",
  "message": "Submission.lean:4:8: error(lean.unknownIdentifier): Unknown identifier `this_is_not_a_valid_proof`",
  "verdict": "true",
  "artifact_path": null,
  "direct_declarations": [],
  "axioms": [],
  "stdout": "Submission.lean:4:8: error(lean.unknownIdentifier): Unknown identifier `this_is_not_a_valid_proof`",
  "stderr": "",
  "cached": false,
  "elapsed_ms": 3942,
  "service_rev": "judge-214e32b70b08-lean-fbbd4a8e-mathlib-896cc56a395e",
  "control_cached": false,
  "control_job_id": "5fccf4b892694247b397916c2637cf09",
  "control_backend_url": "http://10.220.69.153:8889"
}
```

同步接口的业务失败仍通常返回 HTTP 200。调用方不要只看 HTTP status，要看响应 JSON 里的 `status` 和 `error_code`。

## 异步校验

### `POST /jobs`

提交一条异步任务，立即返回 job 信息。相同请求如果已有排队或运行中的 job，会返回已有 `job_id`；如果结果已缓存，会直接返回 `status="done"` 的 job。

```bash
curl -fsS http://10.220.69.172:8890/jobs \
  -H 'Content-Type: application/json' \
  -d @request.json | python3 -m json.tool
```

响应示例：

```json
{
  "job_id": "4d0b9a1f49f24cb2952d1f37c1c9e3c1",
  "status": "queued",
  "result": null,
  "error": null,
  "backend_url": null,
  "attempts": 0,
  "created_at": 1780311475.12,
  "updated_at": 1780311475.12,
  "started_at": null,
  "finished_at": null
}
```

### `GET /jobs/{job_id}`

查询 job 当前状态。

```bash
curl -fsS http://10.220.69.172:8890/jobs/4d0b9a1f49f24cb2952d1f37c1c9e3c1 \
  | python3 -m json.tool
```

job 状态：

| 状态 | 说明 |
| --- | --- |
| `queued` | 已入队，等待 dispatcher 分配 worker。 |
| `running` | 已分配到某个 worker，正在执行 Lean。 |
| `done` | 已完成，`result` 字段保存 judge 响应。 |
| `failed` | 多次重试后失败，`error` 字段保存失败原因。 |
| `cancelled` | 预留状态，当前没有对外取消接口。 |

完成示例：

```json
{
  "job_id": "4d0b9a1f49f24cb2952d1f37c1c9e3c1",
  "status": "done",
  "result": {
    "status": "accepted",
    "error_code": "ACCEPTED",
    "message": "certificate accepted",
    "verdict": "true",
    "cached": false,
    "elapsed_ms": 9726,
    "service_rev": "judge-214e32b70b08-lean-fbbd4a8e-mathlib-896cc56a395e",
    "control_cached": false
  },
  "error": null,
  "backend_url": "http://10.220.69.153:8889",
  "attempts": 1,
  "created_at": 1780311475.12,
  "updated_at": 1780311485.10,
  "started_at": 1780311475.30,
  "finished_at": 1780311485.10
}
```

### `GET /jobs/{job_id}/wait`

长轮询等待任务完成。适合调用方提交后等待一段时间，不想自己频繁轮询。

参数：

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | ---: | --- |
| `timeout_seconds` | float | 30.0 | 本次 wait 请求最多等待多久。不会改变 Lean 校验 timeout。 |

```bash
curl -fsS 'http://10.220.69.172:8890/jobs/4d0b9a1f49f24cb2952d1f37c1c9e3c1/wait?timeout_seconds=60' \
  | python3 -m json.tool
```

如果等待超时但 job 还没结束，响应会包含：

```json
{
  "job_id": "4d0b9a1f49f24cb2952d1f37c1c9e3c1",
  "status": "running",
  "wait_timeout": true
}
```

调用方可以继续调用 `/wait` 或 `/jobs/{job_id}`。

### `GET /jobs`

查看最近任务，默认 `limit=50`。

```bash
curl -fsS 'http://10.220.69.172:8890/jobs?limit=20' | python3 -m json.tool
```

响应：

```json
{
  "jobs": [
    {
      "job_id": "...",
      "status": "done",
      "result": {},
      "error": null,
      "backend_url": "http://10.220.69.153:8889",
      "attempts": 1,
      "created_at": 1780311475.12,
      "updated_at": 1780311485.10,
      "started_at": 1780311475.30,
      "finished_at": 1780311485.10
    }
  ]
}
```

## 健康检查

### 总控 `GET /health`

```bash
curl -fsS http://10.220.69.172:8890/health | python3 -m json.tool
```

响应示例：

```json
{
  "status": "ok",
  "service": "judge-v2-control",
  "backends": [
    {
      "url": "http://10.220.69.172:8889",
      "healthy": true,
      "workers_busy": 0,
      "workers_total": 24,
      "in_flight": 0,
      "service_rev": "judge-214e32b70b08-lean-fbbd4a8e-mathlib-896cc56a395e",
      "last_error": null,
      "last_checked_at": 1780311475.8947256,
      "score": 0.0
    }
  ],
  "queue_size": 0,
  "jobs_by_status": {
    "done": 151
  },
  "cache_entries": 150,
  "cache_total_hits": 1
}
```

关键字段：

| 字段 | 说明 |
| --- | --- |
| `backends[].healthy` | 该 worker 是否健康。总控只会选择 healthy worker。 |
| `backends[].workers_busy` | worker 当前已占用执行槽位。 |
| `backends[].workers_total` | worker 总执行槽位。 |
| `backends[].in_flight` | 总控已派发但 health 尚未反映的请求数。 |
| `backends[].score` | 负载分数，约等于 `(workers_busy + in_flight) / workers_total`。总控优先选择 score 最低的 worker。 |
| `queue_size` | 总控待分发队列长度。 |
| `jobs_by_status` | 总控本地 job 状态统计。 |
| `cache_entries` | 总控结果缓存条数。 |

### Worker `GET /health`

一般调用方不需要直接访问 worker。排查时可以使用：

```bash
curl -fsS http://10.220.69.153:8889/health | python3 -m json.tool
```

响应示例：

```json
{
  "status": "ok",
  "service": "judge-v2-worker",
  "service_rev": "judge-214e32b70b08-lean-fbbd4a8e-mathlib-896cc56a395e",
  "judge_repo": "/opt/equational-theories-lean-stage2",
  "lean_version": "Lean (version 4.30.0-rc2, x86_64-unknown-linux-gnu, commit 3dc1a088b6d2d8eafe25a7cd7ec7b58d731bd7cc, Release)",
  "mathlib_rev": "896cc56a395e",
  "judge_rev": "214e32b70b08",
  "workers_busy": 0,
  "workers_total": 24,
  "cache_entries": 40,
  "cache_bytes": 12345
}
```

### Worker `GET /stats`

查看单个 worker 的缓存和执行槽位统计：

```bash
curl -fsS http://10.220.69.153:8889/stats | python3 -m json.tool
```

## 错误语义

### 业务错误

Lean 没有通过、代码被策略拒绝、timeout 等通常是业务结果，HTTP status 仍为 200。常见 `error_code`：

| error_code | 说明 |
| --- | --- |
| `ACCEPTED` | 校验通过。 |
| `LEAN_REJECTED` | Lean 编译、类型检查或证明检查失败。 |
| `LEAN_TIMEOUT_HARD` | 超过 hard timeout。 |
| `BANNED_PLACEHOLDER` | 包含 `sorry`、`admit` 等禁用占位或禁用 token。 |
| `DISALLOWED_AXIOMS` | 使用了不允许的 axiom。 |
| `DISALLOWED_DECLARATIONS` | 使用了不允许的 declaration。 |
| `FALSE_CERT_TOO_LARGE` | false witness 超过大小限制。 |
| `CODE_TOO_LONG` | Lean 代码超过长度限制。 |
| `DUPLICATE_JSON_KEYS` | answer JSON 中存在重复 key。 |
| `ANSWER_NOT_OBJECT` | answer 不是 JSON object。 |
| `ANSWER_SCHEMA_ERROR` | answer schema 不合法。 |
| `INVALID_VERDICT` | verdict 不是 `true` 或 `false`。 |
| `INVALID_CODE_FIELD` | code 字段非法。 |
| `UNPARSED_JSON` | answer JSON 解析失败。 |

推荐判断：

```python
accepted = result.get("status") == "accepted" and result.get("error_code") == "ACCEPTED"
```

### HTTP 错误

| HTTP status | 场景 |
| ---: | --- |
| 400 | 请求不合法，例如缺少 `problem.id`、`verdict` 非 `true/false`、`code` 为空，或 problem 配置错误。 |
| 404 | 查询未知 `job_id`。 |
| 502 | 同步 `/verify` 等待到 job 失败；通常是 backend 请求失败或重试耗尽。 |
| 503 | 单个 worker 执行池已满。总控遇到此类 backend 错误会重试。 |
| 504 | 同步 `/verify` 在总控等待时间内未完成。此时建议改用异步 `/jobs`。 |

FastAPI 默认错误响应形态：

```json
{
  "detail": "problem.id required (non-empty string)"
}
```

## 缓存和去重

总控和 worker 都有缓存：

- 总控缓存 key 包含 `problem.id`、`verdict`、`code` 和 controller schema version。
- Worker 缓存 key 包含 `problem.id`、`verdict`、`code` 和 `service_rev`。
- 可缓存结果包括 `ACCEPTED`、`LEAN_REJECTED`、策略拒绝、schema 错误等确定性结果。
- 基础设施错误通常不会缓存。

响应字段：

| 字段 | 说明 |
| --- | --- |
| `control_cached` | 是否命中总控缓存。 |
| `cached` | 是否命中 worker 缓存。 |
| `control_job_id` | 同步 `/verify` 对应的总控 job id。 |
| `control_backend_url` | 实际执行该请求的 worker URL。 |

保存策略：

- 运行中的 job 会临时保存完整请求体，以便 dispatcher 派发和失败重试。
- 终态 job 的 `request_json.code` 会被脱敏，只保留 `code_sha256` 和 `code_bytes`。
- Worker 和总控的结果 cache 不保存原始 Lean 代码。

如果调用方要强制重新跑一条测试请求，可以改变 `problem.id` 或在 `code` 中加入唯一 comment。

## 负载均衡

总控每次派发前会刷新 worker health，并从 healthy backend 中选择负载分数最低的一台：

```text
score = (workers_busy + in_flight) / workers_total
```

当分数相同时，按 URL 排序选择。实际高并发下会因 `in_flight` 递增而在各 worker 间分散。

## Python 调用示例

同步：

```python
import json
import urllib.request

payload = {
    "problem": {
        "id": "p_true_basic",
        "eq1_id": 38,
        "eq2_id": 42,
        "equation1": "x ◇ x = x ◇ y",
        "equation2": "x ◇ y = x ◇ z",
    },
    "verdict": "true",
    "code": (
        "import JudgeProblem\n\n"
        "def submission : Goal := by\n"
        "  intro G _ h\n"
        "  intro x y z\n"
        "  rw [← h, h]\n"
    ),
    "timeout_seconds": 120,
}

req = urllib.request.Request(
    "http://10.220.69.172:8890/verify",
    data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)

with urllib.request.urlopen(req, timeout=180) as resp:
    result = json.loads(resp.read().decode("utf-8"))

accepted = result.get("status") == "accepted" and result.get("error_code") == "ACCEPTED"
print(accepted, result.get("control_backend_url"), result.get("elapsed_ms"))
```

异步：

```python
import json
import time
import urllib.request


def request_json(method, url, payload=None, timeout=60):
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


job = request_json("POST", "http://10.220.69.172:8890/jobs", payload)
job_id = job["job_id"]

while True:
    current = request_json(
        "GET",
        f"http://10.220.69.172:8890/jobs/{job_id}/wait?timeout_seconds=30",
        timeout=40,
    )
    if current["status"] in {"done", "failed", "cancelled"}:
        break
    time.sleep(1)

if current["status"] == "done":
    result = current["result"]
    accepted = result.get("status") == "accepted" and result.get("error_code") == "ACCEPTED"
else:
    accepted = False
    result = {"error": current.get("error")}
```

## 运维入口

当前部署脚本：

```text
members/wubing/scripts/deploy/deploy_judge_v2_worker_from_harbor.sh
members/wubing/scripts/deploy/deploy_judge_v2_control_from_harbor.sh
```

worker 默认不设置 `JUDGE_ARTIFACT_DIR`，每次 Lean 校验使用临时 artifact 目录并自动删除。需要调试并保留远端 artifact 时，才在部署 worker 时显式传入：

```bash
ARTIFACT_DIR=/var/lib/judge_v2/artifacts \
bash deploy_judge_v2_worker_from_harbor.sh
```

重启 worker 后检查：

```bash
curl -fsS http://127.0.0.1:8889/health | python3 -m json.tool
```

重启 controller 后检查：

```bash
curl -fsS http://127.0.0.1:8890/health | python3 -m json.tool
```

从本机检查统一入口：

```bash
curl -fsS http://10.220.69.172:8890/health | python3 -m json.tool
```
