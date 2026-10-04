# ETF 因子挖掘

当前任务是在固定 **14 只 ETF、8 个经济组**中，用 D 日收盘前已知的信息预测 D+2→D+7 复权开盘收益的组间排序。主评价为有符号 Rank IC；逐条交付公式、冻结方向、IC、HAC t、有效日数、评价窗口与证据路径。

当前自动发现政策为 `workflow_v15_reliable_progress_20261003`，采用开放探索。Luna `gpt-6-luna` 提案和实现，Sol `gpt-6.1-sol` 审阅；通常每轮 4–8 条不同假设，不凑数。完整轮数、实际候选数与可计算 IC 数分别报告。

| 要做什么 | 入口 |
|---|---|
| 核对资料基准与全历史 | [研究资料基准](docs/RESEARCH_BASELINE.md) / [文档逐项归属](docs/HISTORICAL_DOCUMENTS.md) |
| 理解研究问题与证据边界 | [研究方法论](ETF_ROTATION_METHODOLOGY.md) |
| 核对人口、标签、冷线和数值条件 | [IC 挖掘规则](docs/IC_MINING_RULES.md) |
| 启动已授权批次 | [自动发现流程](docs/ETF_AUTORESEARCH_PROGRAM.md) |
| 查累计定义、公式与 IC | [因子库查询](docs/IC_INVENTORY.md) |
| 核对进度与恢复 | [运行说明](docs/ETF_LUNA_DAGU_OPERATIONS.md) |
| 找实现与测试 | [源码阅读入口](RESEARCH_GUIDE.md) |
| 找历史设计与旧批次 | [文档状态索引](docs/document_status.md) / [归档索引](docs/archive/20261003/README.md) |
| 找当前配置与历史合同 | [配置目录说明](configs/README.md) |
| 查一次性旧研究工具 | [历史脚本索引](scripts/research/HISTORICAL_INDEX.md) |

本项目独立于 SmartMoney 个股挖掘；个股不进入 ETF 默认测试集合。当前环境在本目录 `pyproject.toml` / `uv.lock` 中独立锁定，参见[迁回记录](../../docs/IC_PROJECT_MIGRATION_20261004.md)。历史批次配置、轮次驱动和旧源码通过 `.ignore` 移出普通搜索；显式文件路径或 `rg --no-ignore` 仍可查询，冻结原文与路径保留。

累计结果以本地机器产物为准，文档不维护另一套手写总数：

- 正式历史库：仓库根 `runtime_outputs/etf_rotation_research/IC_INVENTORY_LATEST.json` 指向最新完整快照。
- 自适应发现库：`runtime_outputs/etf_autoresearch_ic/library/library.csv`、`library.json`；后者含逐 campaign 的派生进度核对。
- 修复、模型更新及资料整理验收：按[资料基准中的先后关系](docs/RESEARCH_BASELINE.md#验收材料的先后关系)读取；首次修复报告的旧审核模型已被后续记录取代。

正式库与自适应库分别计数，ETF 与个股研究分别维护。负 IC、弱证据和有效但稀疏的 IC 均保留；收益、成本、相关性、增量及认证另列，不增加 IC 留存门。已见历史上的发现不构成独立确认。

[月度前向流程 v4](configs/etf_ic_monthly_factory_v4.yaml)与自动发现分别运行。市场数据、实验源码快照、账本、模型和生成结果仅留本地。旧实验工件原位保存，保证路径与哈希可核对。
