# v13 pre-distillation baseline

这是 `2026-05-12/v12` 当前 solver 的 identity freeze，用作 2026-05-20 solver-ready distillation 前的基线锚点。

## 基线

- solver hash：`f43c446d60073dbfcddd34858ac3cc648f4eaa78faa151b51830100f771ec570`
- solver bytes：`263124`
- 代码变更：无，和 `2026-05-12/v12` 完全相同。
- 官方提交目录：未触碰，`submissions/solo_official/` 仍单文件。
- 评估证据：继承 `2026-05-12/v12` 的 remote `dev_fast`、`dev_main` 和完整 `test_locked` gate，因为 solver hash 一致。

## 已继承的 v12 远程指标

- `dev_fast`: `1895A / 105R / 0E`
- `dev_main`: `9442A / 558R / 0E`
- `test_locked`: `47031A / 2969R / 0E`
- LLM calls：`0`

## 固化验证

- current、v13、`2026-05-12/v12` hash 完全一致：`f43c446d60073dbfcddd34858ac3cc648f4eaa78faa151b51830100f771ec570`。
- 三者大小均为 `263124` bytes。
- focused pytest：`2 passed in 0.02s`。
