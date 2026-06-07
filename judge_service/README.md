# judge_service/ — Local Judge HTTP Service

> 把 `third_party/equational-theories-lean-stage2/judge/verify.py` 包成 FastAPI 微服务。
> 内部用，无认证。有 sqlite 缓存按 `problem.id + verdict + code` 去重。

## 启动

### 直接运行

```bash
# 必需的 env vars
export JUDGE_REPO=$(pwd)/third_party/equational-theories-lean-stage2

# 可选 (有默认值)
export JUDGE_WORKERS=4                       # 默认: cpu_count // 2
export JUDGE_DEFAULT_TIMEOUT_SECONDS=120
export JUDGE_TIMEOUT_CAP_SECONDS=180
export JUDGE_CACHE_PATH=judge_cache.sqlite   # 默认: 当前目录
export LEAN_BIN=lean                         # 默认: lean
export LAKE_BIN=lake                         # 默认: lake

# 起服务
uvicorn judge_service.server:app --host 0.0.0.0 --port 9000
```

### Docker

```bash
cd judge_service
docker build -t etp-judge .
docker run -p 9000:9000 \
  -e JUDGE_REPO=/repo/third_party/equational-theories-lean-stage2 \
  -v $(pwd)/..:/repo:ro \
  etp-judge
```

## 端点

| Method | Path | 用途 |
|---|---|---|
| POST | `/verify` | 验证一段 Lean 证明；body: `{problem, verdict, code, timeout_seconds?}` |
| GET | `/health` | 服务状态 + worker / cache 统计 |
| GET | `/stats` | 缓存命中率 |

## 验证

```bash
curl http://localhost:9000/health
# {"status":"ok","workers":4,...}

# Smoke verify (用 examples 里的一道题)
curl -X POST http://localhost:9000/verify \
  -H "Content-Type: application/json" \
  -d @third_party/equational-theories-lean-stage2/examples/sample_request.json
```

## 缓存

- sqlite 路径由 `JUDGE_CACHE_PATH` 控制；默认 `judge_cache.sqlite` 在 cwd
- 缓存 key: `(problem.id, verdict, sha256(code))`
- 缓存大小不限；删除文件即可清空
- 别 commit `judge_cache.sqlite`，已在 `.gitignore`

## 部署到团队远端

如果团队有共享机器跑 judge，请把 URL 写到一个公共地方（e.g. `docs/playbook/judge.md`），
各成员 `.env` 把 `JUDGE_SERVICE_URL` 指过去。**不要**把 URL hardcode 进代码。

## 改 server.py 时

服务的 `/verify` 协议被 `scripts/run_generic.py` 依赖。改请求 / 响应 schema 要同步改 client。
