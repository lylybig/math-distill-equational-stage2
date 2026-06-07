# Stage 2 Solver-First 重构设计

## 背景

官方 Stage 2 仓库 `SAIRcompetition/equational-theories-lean-stage2`
已经明确 Solo track（单题独立求解模式）的提交物是单文件
`solver.py`，通过 stdin/stdout JSON 协议向 proxy（代理）请求
`judge` 或 `llm`。官方 Tutorial 中的 `baseline`、`twophase`、
`opnorm` 都是围绕 `solver.py` 迭代，而不是围绕外部
cheatsheet（提示表）迭代。

本项目早期保留了 LLM-output-as-certificate（模型输出即证书）
实验闭环，并把 cheatsheet 作为主要可变对象。现在目标切换为
构建可提交、可复现、Lean 4 可验证的官方 Solo solver。因此
cheatsheet 工作流不再保留为项目能力，项目主线改为迭代
`submissions/solo_official/solver.py`。

## 目标

1. 删除 cheatsheet 主流程和对应技能，避免后续默认路径继续优化
   prompt 文件。
2. 把 README、架构文档、脚本索引和技能说明切换为 solver-first。
3. 让本地评估默认使用官方 runner、official proof checker（官方证明检查器）
   和 history-style summary（历史页风格汇总）。
4. 先提升 deterministic solver（确定性求解器）：移植官方 baseline 的
   singleton proof（单元素证明）策略，使 `sample_200` 从当前约
   `94/200` 提升到约 `111/200`。
5. LLM fallback（大模型兜底）暂不默认启用，因为当前 mass zhangkang endpoint
   入口可见但 completion 生成不可用或不稳定。保留 solver 协议层占位，
   等 endpoint 恢复后再接入。

## 非目标

- 本轮不把官方 `opnorm` 的全部 16 个策略一次性塞入 solver。
- 本轮不实现 Kubernetes executor（K8s 执行器）。
- 本轮不删除历史实验产物 `artifacts/runs/`。
- 本轮不改官方 external 仓库源码作为项目主线；只把它当参考和本地 judge。

## 目标架构

项目主线分为五层：

1. **提交 solver 层**
   - `submissions/solo_official/solver.py` 是唯一提交态文件。
   - solver 内部包含确定性策略、Lean certificate renderer（证书渲染器）
     和可选 LLM fallback 协议。
   - `submissions/solo_official/` 必须只包含 `solver.py`，保持官方单文件约束。

2. **官方 runner 评估层**
   - `scripts/evaluator/run_official_solo_history.py` 是默认评估入口。
   - 输入官方 problem JSON/JSONL，输出官方 runner 原始 JSON、log、
     `summary.json` 和 `history.md`。
   - 默认 suite（套件）优先支持 `sample20`、`sample200`、
     `public-examples`。

3. **官方 judge 验证层**
   - `src/math_distill_stage2/official_stage2_judge.py` 继续封装官方
     `judge/verify.py`。
   - Docker 镜像 `math-distill-stage2-official-judge:official-6805e23`
     继续作为批量验证后端。

4. **solver 分析层**
   - 新增或改造 run analysis（运行分析）面向 official runner 结果，
     统计 accepted、failed/no-candidate、judge rejected、LLM error、
     按 `answer` 标签和 verdict 分组。
   - 错误样例用于下一轮 solver 策略设计，而不是编辑 cheatsheet。

5. **历史实验层**
   - 早期 LLM-output-as-certificate 代码如果仍需保留，应改名为
     legacy（旧实验）或直接删除；默认文档和技能不再引用。

## LLM 策略

当前 mass zhangkang endpoint 探测结果：

- `/v1/models` 返回 `gpt-oss-120b`。
- `/v1/chat/completions` 对最小请求返回 `500 Internal Server Error`
  或 SSL EOF。

因此本轮默认不启用 LLM fallback。solver 中可以保留协议 helper
`call_llm` 和 top-level `PROMPT` 的设计占位，但默认控制流必须先做到：

1. 小阶和结构化 finite magma counterexample search（有限岩浆反例搜索）。
2. singleton proof。
3. 后续再逐步移植 twophase/opnorm 的确定性策略。
4. LLM endpoint 恢复后，把 solver-side structural context（结构化上下文）
   送给 proxy，而不是恢复外部 cheatsheet 文件。

## 删除范围

本轮删除或停止主线引用：

- `cheatsheets/`
- `scripts/cheatsheets/`
- `src/math_distill_stage2/cheatsheets/`
- `skills/stage2-optimize-cheatsheet/`
- `skills/stage2-version-cheatsheet/`
- `docs/cheatsheet-optimization.md`

旧 LLM evaluator 相关文件如果仍被测试或历史文档引用，可先作为
legacy 删除计划的一部分处理；默认 README 不再把它列为第一命令。

## 验证标准

1. `submissions/solo_official/` 仍只有 `solver.py`，小于 500000 bytes。
2. 官方 `sample_20` 可跑完并输出 history-style artifacts。
3. 官方 `sample_200` 可跑完，目标 accepted 数不低于 baseline deterministic
   对照的 `111/200`。
4. focused tests 通过：
   - `tests/test_official_solo_submission.py`
   - `tests/test_official_stage2_history.py`
   - `tests/test_official_stage2_judge.py`
   - `tests/test_official_stage2_docker_batch.py`
5. 文档不再把 cheatsheet 作为 Stage 2 主线。

## 风险

- 删除 cheatsheet 相关代码会导致旧测试失败；需要同步删除或改写测试。
- 项目已有大量 dirty worktree，需要严格限定本轮修改范围，不回滚已有文件。
- LLM endpoint 暂不可用，因此不能用 LLM 提升 true proof 覆盖率；短期提升只能来自确定性策略。
