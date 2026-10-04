# ETF 研究资料基准

本页统一现行合同、历史检索与工程验收入口。整理日期 2026-10-03；本次整理不启动新候选，不改写历史结果。旧报告中的“当前”、模型名与通过结论只适用于原报告日期。

## 现行合同

| 项目 | 基准及权威来源 |
|---|---|
| 研究问题 | 固定 14 ETF、8 个经济组的相对收益排序；[IC_MINING_RULES](IC_MINING_RULES.md) |
| 时序 | D 收盘可知信息；D+2→D+7 复权开盘 H5 标签；当前发现退出截止 2026-03-24 |
| 主证据 | signed Rank IC、HAC t、有效日数与实际窗口；正、负、近零及不可计算分列 |
| 基线含义 | 信息与评价合同统一；已有因子用于检索。B8/B14 经济结果、冗余、增量及认证单列，不增加 IC 留存门 |
| 模型与流程 | `gpt-6-luna` 提案/实现，`gpt-6.1-sol` 审核；[v15 开放发现](ETF_AUTORESEARCH_PROGRAM.md) |
| 原始数据 | 按规则访问原只读数据目录；本次仅整理保存的研究证据，不打开冷区行情 |
| 项目边界 | 个股为[独立项目](https://github.com/zhangsensen/SmartMoney/tree/main/frameworks/stock_factor_research)；其他 T0 ETF9、概念股、持仓/执行项目不并入当前因子数量或规则 |

复权开盘标签用于研究，不保证实际成交价；当前工程可运行不构成因子认证或交易许可。份额/NAV 的披露与历史版本限制仍按原规则解释。

## 结果与历史入口

路径相对仓库根；生成的目录、查询表和核对报告只留本地。

| 要查什么 | 入口 | 使用边界 |
|---|---|---|
| 正式累计结果 | `runtime_outputs/etf_rotation_research/IC_INVENTORY_LATEST.json` | 定位快照的方向视图、定义和登记映射；按每条原窗口解释 |
| 自动发现累计 | `runtime_outputs/etf_autoresearch_ic/library/library.json` | 与正式库分别计数，reference 复算不计新发现 |
| 全历史检索 | `runtime_outputs/etf_history_baseline_20261003/INDEX.md` | 覆盖 ETF 历史输出入口，包含 Pi/GLM、Sonnet、旧货架、复盘与工程修复 |
| 按家族/公式检索 | 同目录 `candidate_lookup.csv` | 正式与自适应分列；窗口终点明确区分末信号日与标签退出截止日 |
| 原始文件定位 | 同目录 `files.csv`、`roots.csv` | 路径目录，不把文件数或轮次目录数当因子数；缓存不计入 |
| 旧轮次与副本 | 同目录 `legacy_rounds.csv`、`legacy_duplicate_metrics.json` | 保留原合同、原状态和相同文件的哈希关系；不静默合并旧结果 |
| 真实批次进度 | 同目录 `campaigns.csv` | 由冻结计划与候选终态核对；原 COMPLETED 不等于实际完成 |
| 资料缺口 | 同目录 `metadata_gaps.csv`、`source_matches.json` | 原字段缺失、可找回的同哈希源码和不可恢复项显式列出；不猜公式或方向 |
| 文档归属 | [文档逐项清单](HISTORICAL_DOCUMENTS.md) | 现行入口、辅助研究和历史档案分开 |
| 配置与旧工具 | [配置索引](../configs/HISTORICAL_INDEX.md)、[工具索引](../scripts/research/HISTORICAL_INDEX.md) | 原路径及源码封印保留 |

历史登记差额按范围解释：当前正式库存可逐条核对的登记与早期未完整登记的搜索是两件事。当前表内对账成功不能证明全历史搜索次数已知。没有新信息时不要重跑相同定义，也不能把一个变体失败写成整个家族失败。

## 验收材料的先后关系

1. `runtime_outputs/etf_autoresearch_ic/repair_v15_20261003/PROOF.md`：首次执行修复与真实冻结公式回放。该报告里的旧审核模型已被下一项取代，原文保留。
2. `runtime_outputs/etf_autoresearch_ic/code_cleanup_20261003/REPORT.md`：删除旧执行分支，并生效当前 Luna/Sol 模型分工；保存更新后的真实回放证据。
3. `runtime_outputs/etf_autoresearch_ic/final_cleanup_20261003/REPORT.md`：六个旧任务退役、历史源码/配置/工具及个股入口整理。
4. `runtime_outputs/etf_history_baseline_20261003/REPORT.md`：全历史资料目录、登记与证据路径对账、当前运行条件核对。

测试和回放按各自报告日期解释，不累计测试次数。旧 v14 未执行轮次仍为未执行；整理不构成恢复旧批或追加新批预算。

后续新批从[运行说明](ETF_LUNA_DAGU_OPERATIONS.md)进入，先读家族/定义历史，冻结 4–8 条有不同假设的候选，审核后评价；不为凑轮数补定义。当前按用户安排停在资料基准整理。
