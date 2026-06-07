# scripts 目录说明

`scripts/` 只保留命令行入口；可测试业务逻辑应放在 `src/math_distill_stage2/`。

根目录不再放真实命令脚本，入口按领域分组：

- `scripts/evaluator/`：官方 Stage 2 Solo runner 执行和 history 风格汇总。
- `scripts/error_analysis/`：官方 runner 结果和候选验证结果分析、失败归因和报告生成。
- `scripts/counterexample/`：有限岩浆反模型搜索、反例证书、反例资产和 evidence bank。
- `scripts/data/`：公开数据下载、索引、split 和覆盖率分析。
- `scripts/lean_certificates/`：Lean smoke certificate 生成，以及官方 Stage 2 proof checker 的单题/Docker 批量验证入口。
- `scripts/public_eval/`：公开集离线覆盖率 harness；不作为官方 solver 评估入口。

新增脚本必须优先放入对应子目录；不要在 `scripts/` 根目录继续新增兼容入口。

生成物如 `__pycache__/` 不应保留。
