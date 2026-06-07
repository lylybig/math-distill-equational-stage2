# 2026-05-09/v9 no-LLM MagmaEgg singleton compiler order4 dev_fast 1641

这是从 `2026-05-08/d11` promote 的 no-LLM 当前最佳版本，基于 `2026-05-08/v8`。

- order4 dev_fast：`1641/2000`
- accepted rate：`82.05%`
- accepted true / false：`641 / 1000`
- LLM calls：`0`
- judge calls：`5211`
- aggregate problem elapsed：`42945.76s`（parallel run 中不是 wall time）
- wall time：`5735.14s`（`95m35.1s`，来自 `/usr/bin/time -p real`）
- solver hash：`d063fdd26977286c96a8eddc1b28f71a8191a148dd31eb2c97e06d49ae5c7c54`
- solver bytes：`244919`
- dev_fast run：`artifacts/runs/2026-05-09/order4-d11-magmaegg-singleton-dev-fast-w8/`
- targeted run：`artifacts/runs/2026-05-09/order4-d11-magmaegg-singleton-rfix-targeted-w8/`

相对 `2026-05-08/v8` 的 order4 dev_fast baseline：

- accepted：`1591 -> 1641`（`+50`）
- rejected：`409 -> 359`（`-50`）
- errors：`0 -> 0`（`+0`）
- true accepted：`591 -> 641`（`+50`）
- false accepted：`1000 -> 1000`（`+0`）
- LLM calls：`0 -> 0`（`+0`）
- judge calls：`5599 -> 5211`（`-388`）
- observed regressions：`0`

核心改动：

- 新增 MagmaEgg singleton proof compiler：把已验证 direct `EquationN -> Equation2` proof term 编译成 judge 可接受的本地 `have singleton : ∀ (x y : G), x = y` 证书。
- 证书全部在 `submission` 内部生成，不使用 private top-level helper，不 import 外部 `equational_theories` theorem。
- 保持 `MAX_LLM_ROUNDS = 0`，不依赖 mass/gemma runtime。
- 不使用大规模 known proof pair table；只收录少量高价值、已验证、可压缩成通用 compiler 的 proof-source seed。

新增解决：

- stable direct compiler：`49` 个 baseline failed true，targeted run 全部 `judge:1` accepted。
- extra observed：`true_275_2363` 在完整 `dev_fast` 中 accepted，但它不是 d11 singleton compiler 的 `judge:1` 命中，暂按观测增量记录。

仍失败：

- order4 dev_fast remaining failed：`359`，全部是 true 方向未证明项。
- top eq1 clusters 见 `artifacts/runs/2026-05-09/order4-d11-magmaegg-singleton-dev-fast-w8/analysis-dev-fast-delta-vs-current.md`。

`submissions/solo_official/solver.py` 仍未自动同步；最终官方导出单独处理。
