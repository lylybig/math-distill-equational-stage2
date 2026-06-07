# Math Distill Stage 2

SAIR Mathematics Distillation Challenge: Equational Theories Stage 2 的本地工作台。

当前主线是构建可提交的官方 Solo `solver.py`：

- 输入官方 runner 发送的单题 JSON。
- 对真命题输出 Lean 4 proof certificate（证明证书）。
- 对假命题输出 finite magma counterexample certificate（有限岩浆反例证书）。
- 只以官方 judge 返回 `accepted` 作为 solved（已解决）标准。

官方当前公开规则要求输出 Lean 4 可验证 certificate；没有明文要求每题必须调用 LLM。当前本地 LLM 实验默认使用 mass zhangkang OpenAI-compatible endpoint（OpenAI 兼容接口）上的 `gemma-4-31b` chat model；LLM 输出仍必须交给官方 judge 验证后才能计为 solved（已解决）。

## 工作根目录

本工作台位于团队 monorepo 的 `members/wubing/`。下面所有相对路径和常用命令默认都从这个目录运行。

如果当前 shell 在 monorepo 根目录：

```bash
cd members/wubing
```

之后再运行 `PYTHONPATH=src`、`python scripts/...`、`pytest tests/...`、`docker build -f docker/... .` 等命令。

## 主要路径

- `submissions/solo_official/solver.py` - 当前可提交 Solo 求解器；提交目录必须只包含这一个文件。
- `external/equational-theories-lean-stage2/` - 官方 Stage 2 judge/evaluation 仓库本地克隆。
- `scripts/evaluator/run_official_solo_history.py` - 调用官方 Solo runner，并生成类似 playground history 的产物。
- `src/math_distill_stage2/official_stage2_history.py` - official runner 产物汇总和 Markdown 渲染。
- `src/math_distill_stage2/official_stage2_judge.py` - 官方 `judge/verify.py` 的本地封装。
- `src/math_distill_stage2/official_stage2_batch.py` - Docker-only 官方 judge 批量验证。
- `docker/official-stage2-judge/Dockerfile` - 固定官方仓库 commit 和 Lean toolchain 的 judge 镜像。

## 常用命令

```bash
python scripts/evaluator/run_official_solo_history.py \
  --suite sample20 \
  --run-id <run-id>

python scripts/evaluator/run_official_solo_history.py \
  --suite sample200 \
  --run-id <run-id>

docker build --network host \
  -t math-distill-stage2-official-judge:official-6805e23 \
  -t math-distill-stage2-official-judge:latest \
  -f docker/official-stage2-judge/Dockerfile .

python scripts/lean_certificates/verify_official_stage2_batch.py \
  --input artifacts/runs/<candidate-run>/candidate_answers.jsonl \
  --output artifacts/runs/<candidate-run>/official_verify.jsonl \
  --summary artifacts/runs/<candidate-run>/official_verify.summary.json \
  --artifact-dir artifacts/runs/<candidate-run>/official_stage2_judge \
  --image math-distill-stage2-official-judge:official-6805e23 \
  --max-workers 2 \
  --resume

pytest tests/official/test_official_solo_submission.py -q
pytest tests/skills/test_stage2_skills.py -q
```

## Public Problem Sets

公开数据默认使用：

| subset | rows |
| --- | ---: |
| `normal` | 1000 |
| `hard1` | 69 |
| `hard2` | 200 |
| `hard3` | 400 |

默认总数：1669。Hugging Face 中的 `hard=200` 当前不作为默认集，因为它和旧 hard/hard1 切片重复。

## Layout

- `docs/` - 架构、规则分析、数据清单和实施计划。
- `data/raw/` - 官方/API/公开数据快照。
- `data/processed/` - 本地派生索引和 split。
- `submissions/solo_official/` - 官方 Solo 单文件提交目录。
- `src/math_distill_stage2/` - 可测试业务逻辑。
- `scripts/` - 按领域分组的命令行入口。
- `tests/` - 本地工具和提交 solver 的回归测试。
