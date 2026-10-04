# ETF 历史文档归档

整理日期：2026-10-03。现行规则从 [ETF README](../../../README.md) 进入；本目录内的旧命令、数量、状态和版本门仅用于解释历史。

## 已移出当前入口的版本沿革

| 存档 | 保留内容 |
|---|---|
| [自动发现流程](ETF_AUTORESEARCH_PROGRAM.md) | v1–v15 的追加条款、旧 mixed/explore/refine 调度与单候选迭代接口 |
| [IC 规则](IC_MINING_RULES.md) | 历史用户约束、数值条件来源及被替代的家族配额 |
| [Dagu 操作说明](ETF_LUNA_DAGU_OPERATIONS.md) | 2026-09-27 一次性预算链与旧恢复操作 |
| [开发指南](ETF_DEVELOPMENT_GUIDE.md) | 旧人口、WFO、组合、回测与工程验收入口 |
| [源码来源指南](RESEARCH_GUIDE.md) | 历史因子库、方向权重与旧策略来源链 |
| [方法论](ETF_ROTATION_METHODOLOGY.md) | 历史设计、目标账本与分阶段设想 |
| [文档状态](document_status.md) | 2026-09-25 时点的结果与文档状态 |
| [库存说明](IC_INVENTORY.md) | 历史库存数字和快照示例 |

这八份存档保留清理前正文，仅增加历史提示并调整相对链接。当前版本已在原入口整理。累计六份退役任务配置另存[部署归档](../../../../../deployments/archive/etf_research_20261003/README.md)。完整文档归属见[逐项清单](../../HISTORICAL_DOCUMENTS.md)。

## 原址归档

下列材料仍可能被冻结 PLAN、脚本常量或外部路径引用，因此保留原文原路径；它们不作为当前运行指令。

| 原址材料 | 历史用途 |
|---|---|
| [旧自动挖掘方案](../../../ETF_AUTOMATED_MINING_PLAN.md)、[GPU WFO 迁移](../../../GPU_WFO_MIGRATION.md)、[旧公式规格](../../../ETF_FACTOR_MINING_SPEC.md) | 旧人口、搜索代际与接线来源 |
| [工程交接](../../../ENGINEERING_HANDOFF.md)、[因子来源](../../../FACTOR_MINING_PROVENANCE.md) | 当时实现、旧信号/收益时序及筛选来源 |
| [全 ETF 方案](../../all_etf_daily_factor_mining_v1.md)、[旧挖掘器说明](../../../scripts/research/pi_glm_mining/README.md) | 其他人口或旧裁判路径 |
| [八组历史 runner](../../group_discovery_runner.md) | 已冻结正式批次与命令追溯 |
| [2026-09-23 复盘](../../RETROSPECTIVE_20260923.md)、[2026-09-25 复盘](../../RETROSPECTIVE_20260925.md) | 对应日期的发现、失败与限制 |
| [campaign20 提案](../../ETF_IC_CAMPAIGN20_PROPOSAL_20260926.md)、同目录 R02–R10 提案、[历史进度](../../ETF_IC_CAMPAIGN20_PROGRESS_20260926.md) | 原批次冻结范围与逐条结果，不代表当前累计进度 |

同目录其他带日期的预登记、历史合同、冻结/验收报告、审计与 FAMILY_BREADTH 记录按各自日期解释。当前执行规则、范围和查询入口以[文档状态索引](../../document_status.md)为准。

`runtime_outputs/` 下的 PLAN、候选源码快照、请求、分数、IC、失败记录和旧 summary 保留原位；需要新解释时生成派生报告，不能回写旧证据。本次整理的文件映射、原始哈希和核查凭据仅留本地 `runtime_outputs/etf_autoresearch_ic/cleanup_20261003/`。
