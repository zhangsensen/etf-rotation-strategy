# ETF 文档状态索引

整理日期：2026-10-03。当前入口只陈述现行规则；版本沿革与旧命令归入[历史档案](archive/20261003/README.md)。本页不复制累计数或批次运行状态，结果以机器产物为准。

| 当前用途 | 文档 |
|---|---|
| 总入口 | [README](../README.md) |
| 资料基准与完整文档归属 | [基准说明](RESEARCH_BASELINE.md) / [逐项清单](HISTORICAL_DOCUMENTS.md) |
| 研究问题与证据边界 | [方法论](../ETF_ROTATION_METHODOLOGY.md) |
| 规则类指标与 TA-Lib 预检（2026-10-03） | [预检记录](RULE_INDICATOR_PRECHECK_20261003.md) |
| TA-Lib 全函数普查，201 函数/240 因子（2026-10-04） | [普查记录](TALIB_FULL_SWEEP_20261004.md) |
| 冻结范围、时序、数值条件 | [IC_MINING_RULES](IC_MINING_RULES.md) |
| 开放发现与模型分工 | [ETF_AUTORESEARCH_PROGRAM](ETF_AUTORESEARCH_PROGRAM.md) |
| 进度核对与恢复 | [运行说明](ETF_LUNA_DAGU_OPERATIONS.md) |
| 正式与自适应结果查询 | [IC_INVENTORY](IC_INVENTORY.md) |
| 源码与测试 | [RESEARCH_GUIDE](../RESEARCH_GUIDE.md) |
| 经济暴露分组 | [说明](candidate14_economic_groups_v1.md) / [配置](../configs/etf_candidate14_economic_groups_v1.yaml) |
| 月度前向合同 | [v4](../configs/etf_ic_monthly_factory_v4.yaml)；旁路观察名单为[历史线索 v2](../configs/etf_ic_lead_watch_v2.yaml) |
| 当前配置与历史批次 | [配置入口](../configs/README.md) / [原址归档清单](../configs/HISTORICAL_INDEX.md) |
| 历史一次性工具 | [脚本索引](../scripts/research/HISTORICAL_INDEX.md) |
| 个股研究归属 | [独立项目入口及测试](../../stock_factor_research/README.md)，不并入 ETF |

当前进度从 `runtime_outputs/etf_autoresearch_ic/library/library.json` 的 `campaign_progress` 或只读核查报告读取；当前正式库存由 `runtime_outputs/etf_rotation_research/IC_INVENTORY_LATEST.json` 定位。

历史开发指南、v1–v14 流程沿革和旧 Dagu 指令已有独立归档。带日期的提案、进度、复盘、历史合同及来源说明按原路径保留，供原代码与冻结证据引用；目录见[原址归档清单](archive/20261003/README.md#原址归档)。其中“当前”“最新”“首次尚未到期”仅描述原撰写时点，不构成当前状态或新批授权。

历史 PLAN、源码哈希、原始结果与失败记录不随文档整理改写。已见面的历史线索、自适应发现、月度前向结果分别解释，不互认独立确认。

旧 Pi/GLM、Sonnet 的生成及控制定时任务已退役；与之前两份 v6 一次性任务合计六份配置见[部署归档](../../../deployments/archive/etf_research_20261003/README.md)。源码档案使用精确 Git 忽略例外；默认搜索由 `.ignore` 隔离历史条目，显式路径与复算保持可用。
