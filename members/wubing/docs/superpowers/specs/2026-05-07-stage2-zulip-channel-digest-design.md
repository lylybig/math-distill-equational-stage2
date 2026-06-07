# Stage 2 Zulip 频道归档与每日摘要设计

## 背景

SAIR Zulip 频道 `Math Distillation Challenge - equational theories` 可能包含 Stage 2 规则澄清、官方实现细节、公开数据讨论、Lean 证书经验和参赛策略线索。当前项目已有 `stage2-info-competition` 技能，用于刷新官方页面、API 和 judge 仓库快照，但没有覆盖需要登录的 Zulip 频道内容。

用户需求是保存“全量原文归档 + 每日中文摘要”。由于 `https://zulip.sair.foundation/#narrow/channel/13-Math-Distillation-Challenge---equational-theories` 匿名访问会跳转登录页，自动更新必须使用 Zulip API 和本地凭据，不应依赖浏览器会话或手工复制。

## 目标

1. 新增项目私有技能 `stage2-info-zulip-channel`，用于触发和规范 Zulip 频道同步整理流程。
2. 新增可复现同步脚本，支持首次全量回填和后续增量更新。
3. 保存 Zulip 原文消息归档，保留足够字段以便以后重新整理、查证和按 topic 回放。
4. 每日生成中文摘要，突出与 Stage 2 solver、judge、Lean certificate、数据集和规则相关的信息。
5. 支持由人工、cron 或 systemd timer 每日调用，但不在实现中擅自修改用户的系统定时配置。

## 非目标

- 不绕过 Zulip 登录或权限控制。
- 不把 Zulip 内容视为高于官方规则、官方 API 或官方 judge 仓库的权威来源。
- 不把摘要直接写入 solver、cheatsheet、评估输入或提交目录。
- 不提交 Zulip 凭据、`.zuliprc`、API key 或包含私人 token 的日志。
- 不实现长期运行的 daemon（守护进程）；第一版使用可重复执行的命令行脚本。

## 推荐方案

采用“项目技能 + 可复现同步脚本 + 本地 daily 入口”。

- 技能目录：`skills/stage2-info-zulip-channel/`
- CLI 入口：`scripts/data/sync_zulip_channel.py`
- 可测试业务逻辑：`src/math_distill_stage2/zulip_archive.py`
- 原文归档：`data/raw/references/zulip/math-distillation-challenge-equational-theories/messages/YYYY-MM-DD.jsonl`
- 同步状态：`data/raw/references/zulip/math-distillation-challenge-equational-theories/state.json`
- 每日摘要：`docs/zulip-digests/YYYY-MM-DD.md`

`data/raw/` 是本地生成快照目录，按项目现有约定不提交。`docs/zulip-digests/` 保存人类可读中文摘要，可随项目版本管理；如果摘要包含不适合公开提交的内容，后续可改为 git ignored 目录或只提交索引说明。

## 认证与配置

默认读取 `ZULIP_CONFIG_FILE` 指向的 Zulip 配置文件；未设置时尝试 `~/.zuliprc`。配置文件应包含：

- `site=https://zulip.sair.foundation`
- `email=<Zulip API email>`
- `key=<Zulip API key>`

脚本也可支持显式参数：

```bash
python scripts/data/sync_zulip_channel.py \
  --channel "Math Distillation Challenge - equational theories" \
  --site https://zulip.sair.foundation
```

凭据只从本地文件或环境读取，不写入产物。错误信息不得打印 API key。

## 数据流

1. 读取配置、归档目录和 `state.json`。
2. 调用 Zulip `GET /api/v1/messages`，使用 narrow：
   - `{"operator": "channel", "operand": "Math Distillation Challenge - equational theories"}`
3. 首次同步使用 `anchor=newest` 分批向前回填，直到频道可见历史拉完或达到用户指定 `--since`。
4. 增量同步使用 `state.json` 中的 `last_message_id` 作为 anchor，只拉取之后的新消息。
5. 规范化每条消息，按消息 UTC 日期写入 JSONL，避免重复写入同一 message id。
6. 从本次新增消息和当日已有归档生成或更新 `docs/zulip-digests/YYYY-MM-DD.md`。
7. 更新 `state.json`，记录最大 message id、最后同步时间、频道名、站点和同步批次统计。

## 原文归档格式

JSONL 每行保存一条消息，字段至少包括：

- `id`
- `timestamp`
- `datetime_utc`
- `date_utc`
- `sender_full_name`
- `sender_email`
- `sender_id`
- `topic`
- `content`
- `rendered_content`
- `reactions`
- `links`
- `stream_id`
- `raw`

`raw` 保存 Zulip 返回的原始消息对象，用于未来兼容字段变更。归档写入时按 `id` 去重并排序。

## 每日中文摘要格式

每日摘要是 Markdown 文件，建议结构：

```markdown
# Zulip 每日摘要：YYYY-MM-DD

## 关键信息

## 按 Topic 整理

## 规则与官方信息

## Judge / Lean / Certificate

## Solver 策略线索

## 重要链接

## 待跟进

## 原文索引
```

第一版摘要生成以确定性规则为主：按 topic 分组、提取链接、标注包含 `judge`、`Lean`、`certificate`、`solver`、`dataset`、`rule`、`official` 等关键词的消息，并生成中文要点草稿。若未来接入 LLM 摘要，必须保留原文索引和人工可复查路径，且不能把 LLM 摘要当成官方事实。

## 技能职责

`stage2-info-zulip-channel` 技能负责：

1. 检查 Zulip 凭据是否存在，但不展示密钥。
2. 运行同步脚本，默认同步指定频道全量可见历史和最新增量。
3. 检查原文归档、摘要文件和状态文件是否更新。
4. 将摘要中的官方事实和待确认信息与 `stage2-info-competition` 的官方快照边界区分开。
5. 报告新增消息数、涉及日期、摘要路径、状态文件路径和验证结果。

技能不直接修改 solver、评估结果、官方快照或提交文件。

## 错误处理

- 缺少凭据：提示创建 `~/.zuliprc` 或设置 `ZULIP_CONFIG_FILE`，不继续同步。
- 权限不足或未订阅频道：报告 Zulip API 错误和频道名，提示检查账号订阅状态。
- 网络失败：保留已有归档和 state，不写入部分损坏状态；可重试。
- API 分页中断：只在成功写入归档后更新 state；下次可从旧 state 继续。
- 日期边界：统一使用 UTC 日期归档；摘要标题可明确为 UTC 日期，避免本地时区造成重复。
- 消息编辑：归档保留 `last_edit_timestamp` 和 `edit_history`（如果 API 返回）；后续同步遇到相同 id 时用新 raw 覆盖旧行。

## 测试策略

先补 focused tests，再实现：

1. 规范化 Zulip 消息字段，保留 `raw` 和日期字段。
2. JSONL 归档按 id 去重、排序，并支持同 id 更新。
3. `state.json` 从新增消息中更新最大 message id。
4. 摘要生成按日期和 topic 分组，提取链接和 Stage 2 关键词消息。
5. CLI 支持使用假 Zulip client 或 fixture 数据运行，不依赖真实 Zulip 网络。

实现后至少运行：

```bash
pytest tests/data/test_zulip_archive.py -q
```

如脚本新增 CLI 参数解析，再补充对应 CLI smoke test。

## 文档更新

实现时同步更新：

- `docs/README.md`：加入 `docs/zulip-digests/` 和新技能说明。
- `docs/data-inventory.md`：记录 Zulip 原始归档目录和 state 文件。
- `docs/architecture.md`：在数据快照层或项目技能层补充 Zulip 频道信息来源。

## 待人工提供

实现不需要知道 API key，但运行真实同步前需要用户在本机准备 Zulip API 凭据。建议使用 `~/.zuliprc` 或 `ZULIP_CONFIG_FILE` 指向的配置文件。
