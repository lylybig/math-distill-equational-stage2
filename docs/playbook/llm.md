# LLM 配置 & 选择

## 配在哪

所有 LLM 配置走 `.env`（不入 git）。模板见 `.env.example`：

```ini
OPENAI_API_KEY=sk-REPLACE_ME
OPENAI_BASE_URL=http://60.171.65.125:30197/v1
OPENAI_MODEL=gemma-4-31b
```

`scripts/run_eval.py` 加载 `.env` 后，**OPENAI_BASE_URL → LLM_BASE_URL**、
**OPENAI_MODEL → LLM_MODEL** 自动桥接，`run_generic.py` 真正用的是 `LLM_*`。

## 官方主推模型

| 模型 | endpoint | 备注 |
|---|---|---|
| **`gemma-4-31b`** | `http://60.171.65.125:30197/v1` | **比赛官方主推**, 全员默认用这个 |

协议：兼容 OpenAI 的 chat completions。

## Prompt 模板

baseline solver 的 prompt 在 `solvers/baseline_solver_v3e.py` 文件头 `PROMPT = "..."` (~150 行)。
要自定义 prompt：把它复制到自己的 solver，按需修改。

## 重试 / 超时

- `LLM_HTTP_TIMEOUT`: 单次请求超时（默认 900s）
- `LLM_MAX_OUTPUT_TOKENS`: max output tokens（默认 8192）
- 无 backoff 重试（设计为单次失败即放弃；其它 stage 兜底）

## 缓存

LLM 本身**无缓存**。但 judge 端有 sqlite 缓存（按 verdict + code），所以同样 prompt 走出
来再 verify 的结果会命中缓存秒回。

## 不要做

- ❌ 把真的 API key 写进 `.env.example`、`solvers/`、`docs/`、commit message
- ❌ 把 key 硬编码进 `members/<你>/solver.py`
- ❌ 在 PR description 里贴含 key 的 .env 内容
- ❌ 把 LLM 输出当 ground truth 写进 lawbook 或 cache（必须经过 judge 验证）

## 监控用量

控制台看消费。如果团队共享一个 key，建议每人各申一个，便于排查谁的 solver 在烧 token。
