# Judge — 怎么用

## 三层结构

```
你的 solver  →  scripts/run_eval.sh  →  scripts/run_generic.py
                                            │ HTTP POST /verify
                                            ▼
                                    judge_service/server.py  (FastAPI)
                                            │ in-process import
                                            ▼
        third_party/equational-theories-lean-stage2/judge/verify.py
                                            │ subprocess
                                            ▼
                                          lean / lake CLI
```

## 必备

- Lean 4 + Lake CLI 装好（按 `third_party/equational-theories-lean-stage2/README` 操作）
- Python 3.10+ + `fastapi` + `uvicorn` + `pydantic`
- `git submodule update --init --recursive` 拉齐

## 起本地 judge

```bash
export JUDGE_REPO=$(pwd)/third_party/equational-theories-lean-stage2
uvicorn judge_service.server:app --host 0.0.0.0 --port 9000
```

或直接在 .env 里指向团队远端（如已部署）:

```ini
JUDGE_SERVICE_URL=http://10.220.69.153:9666
```

## 用 judge 验证一个 solver

```bash
bash scripts/run_eval.sh --smoke                          # 5 题烟雾
bash scripts/run_eval.sh --solver solvers/baseline_solver_v3e.py  # 200 题 baseline
bash scripts/run_eval.sh --solver members/<你>/solver.py
```

输出: `results/<solver>_<dataset>_<ts>.json`（gitignored），含每题 verdict / 用时 / stage。

## 协议

`POST /verify` 请求：

```json
{
  "problem": {"id": "...", "eq1_id": 1604, "eq2_id": 1822, ...},
  "verdict": "true" | "false",
  "code": "<Lean 4 证明文本 或 反例 JSON>",
  "timeout_seconds": 120
}
```

响应：

```json
{
  "status": "ACCEPTED" | "LEAN_REJECTED" | "BANNED_PLACEHOLDER" |
            "DISALLOWED_AXIOMS" | "DISALLOWED_DECLARATIONS" |
            "FALSE_CERT_TOO_LARGE" | "TIMEOUT" | "INFRA_ERROR",
  "stderr": "...",
  "message": "..."
}
```

详细 status 列表见 `judge_service/server.py:CACHEABLE_ERROR_CODES`。

## 缓存

判定结果按 `(problem.id, verdict, sha256(code))` 缓存到 `judge_cache.sqlite`。
**同一段证明再 verify 是秒回**。改了 verifier 行为后请手动删 cache 文件。

## 排错

- `[warn] judge ... unreachable in 3s` — server 没起 / 端口错 / 防火墙
- 大量 `INFRA_ERROR` — 检查 `LEAN_BIN`/`LAKE_BIN` 是否在 PATH；`JUDGE_REPO` 是否对
- `LEAN_REJECTED` — 你的证明错；看 `stderr` 里的 Lean 报错
- `BANNED_PLACEHOLDER` — 你用了 `sorry` / `axiom` 之类被禁的 token
