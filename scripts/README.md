# scripts/ — Manual run tools

> 仅放**手动运行**的工具脚本（评测、跑分、submission staging）。
> **没有 CI / workflows**，参见 [ADR-0001](../docs/blueprints/0001-monorepo.md)。
> 改公共脚本走 PR + review。

## 文件清单

| 文件 | 用途 | 入口 |
|---|---|---|
| `run_eval.sh` | 评测 wrapper，支持 `--background / --tail / --kill` | `bash scripts/run_eval.sh [...]` |
| `run_eval.py` | 评测协调器：load .env, validate, 调 run_generic.py, 总结 | (一般不直接调) |
| `run_generic.py` | 真正跑 pipeline：HTTP judge client + ThreadPool + 写 result.json | (一般不直接调) |

## 快速开始

```bash
# 1. 拷贝 .env 模板, 填 API key
cp .env.example .env
# 编辑 .env, 至少改 OPENAI_API_KEY

# 2. (本机) 起 judge service
JUDGE_REPO=$(pwd)/third_party/equational-theories-lean-stage2 \
  uvicorn judge_service.server:app --host 0.0.0.0 --port 9000 &

# 3. smoke (5 题, 1 worker, 60s/题)
bash scripts/run_eval.sh --smoke

# 4. 正式跑 baseline 在 sample_200 上
bash scripts/run_eval.sh --solver solvers/baseline_solver_v3e.py
# 跑你自己的 solver:
bash scripts/run_eval.sh --solver members/<你>/solver.py
```

## 后台跑长任务

```bash
bash scripts/run_eval.sh \
  --solver solvers/baseline_solver_v3e.py \
  --problems third_party/equational-theories-lean-stage2/examples/problems/contest_1669.jsonl \
  --workers 32 --timeout 1800 \
  --output results/baseline_contest_1669.json \
  --background

# 查看进度
bash scripts/run_eval.sh --tail results/baseline_contest_1669.json
# 中止
bash scripts/run_eval.sh --kill results/baseline_contest_1669.json
```

## 接 SCOREBOARD

跑完后看汇总 → 手动更新 `SCOREBOARD.md`（流程见 [SCOREBOARD.md](../SCOREBOARD.md)）。
原始结果文件 (`results/*.json`) 不入 git，需要分享用 GitHub Release。

## 依赖

- Python 3.10+
- `urllib.request` (stdlib, 调 judge)
- `concurrent.futures.ThreadPoolExecutor` (stdlib, 并发)
- `third_party/equational-theories-lean-stage2/pipeline/` —— 需要 submodule 拉齐

```bash
git submodule update --init --recursive
```

## 改这些脚本时

- 改 run_eval.py 的 CLI 接口 → 更新 `--help` 注释
- 改 run_generic.py 的判定接口 → 跟 judge_service/server.py 协议保持一致
- 任何改动都建议先在 `member/<你>/wip-script-*` 分支跑通再 PR
