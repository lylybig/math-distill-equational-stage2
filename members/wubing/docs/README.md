# 文档索引

本目录保存 `Math-Distill-Stage2` 的项目文档。当前工作台位于团队 monorepo 的 `members/wubing/`；本文档索引里的相对路径默认都相对 `members/wubing/`。旧实验记录里的历史绝对路径只作 provenance（来源记录），不要当作当前工作目录。新增文档默认使用中文；需要保留英文术语时，第一次出现尽量附中文解释。

## 核心文档

- `architecture.md` 是唯一的当前架构说明文档。它是活文档，随着实验、solver 版本和官方规则变化持续更新。
- `competition-analysis.md`：比赛规则、公开数据范围和策略分析。
- `data-inventory.md`：原始数据、处理后数据、外部代码和本地代码清单。
- `judge-v2-api.md`：新分布式 judge 服务的 API、调用示例、错误语义和运维入口。
- `sources.md`：数据和代码来源记录。

## 记录目录

- `experiments/`：实验记录。用于记录探索性实验、覆盖率结果、失败样例和后续动作。
- `blog/`：适合 GitHub Pages 或外部发布的技术文章草稿。公开版应保留方法论、聚合指标和经验，避免泄露比赛中可直接复现 solver 的细节。
- `reports/`：面向领导和团队沟通的短报告，例如 Stage 2 Solo baseline 简报。
- `superpowers/`：自动化设计和实施计划文档，保留现有流程输出。
- `zulip-digests/`：官方 Zulip 频道摘要，配合 `stage2-info-zulip-channel` 更新。

## 仓库根目录约定

- `../skills/`：仓库内项目私有技能目录，保存 `stage2-*` 比赛技能。
- `stage2-train-improve-solver`：根据官方 run 失败样例改进 Solo solver。
- `stage2-train-version-solver`：管理 `solvers/solo_official/current/`、`drafts/`、`versions/` 和官方提交目录同步。
- `stage2-report-solver-baseline`：生成 baseline、版本对比和沟通材料。
- `stage2-info-competition`：同步官方页面、API、judge/evaluation 仓库快照和规则文档。
- `stage2-info-zulip-channel`：同步外部讨论快照并维护 `docs/zulip-digests/`。

## 写作约定

- 文档先写清事实，再写判断；不确定的信息要标注“待确认”。
- 实验记录至少包含：目标、输入、命令或方法、结果、结论、下一步。
- 自动化实验的完整机器产物放在 `artifacts/runs/`；`docs/experiments/` 只写摘要、关键指标、错误模式、改进策略和是否接受。
- 架构相关内容直接维护在 `architecture.md`，不要新增分散的当前架构说明。
- 与官方规则相关的信息要写具体日期和来源，避免只写“现在”“最新”。
