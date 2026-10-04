# 历史存档：2026-10-03 清理前版本

本页仅供追溯旧规则与版本沿革，不作为当前执行指令。
[返回现行入口](../../../README.md) · [归档索引](README.md)

原文内部的“当前”“最新”仅描述原撰写时点；下列正文仅调整了相对链接。

---

# ETF研究阅读入口与历史来源

当前方法统一见 [ETF轮动研究方法论](../../../ETF_ROTATION_METHODOLOGY.md)：
固定14只，按八个经济暴露主组先研究组间价值，组内选优后置；D+2开盘开始评价。
先读 [经济暴露分类](../../candidate14_economic_groups_v1.md)，再填齐冻结实验计划。
文档有效性以 [文档状态索引](../../document_status.md) 为准。
`GPU_WFO_MIGRATION.md`仅保留历史接线说明，旧ETF WFO结果只作历史基线。

历史ETF候选公式、资金流定义和旧本地数据开关见
[`ETF_FACTOR_MINING_SPEC.md`](../../../ETF_FACTOR_MINING_SPEC.md)。份额变化是一级市场申赎代理；
大单资金流是二级市场订单分类，两者不能混称ETF净流入。

本页说明源码关系和研究边界；本地实验结果及交接存于仓库根
`runtime_outputs/etf_research_handoff_20260918/HANDOFF.md`，不随代码提交。

[`ETF_AUTOMATED_MINING_PLAN.md`](../../../ETF_AUTOMATED_MINING_PLAN.md)已原址归档，
仅用于追溯旧分代搜索；不能作为当前研究运行计划。

## 两个池各是什么

- [旧研究配置](../../../configs/combo_wfo_config.yaml)的`data.symbols`用于旧49只池回放。
  股票、债券、黄金及QDII都可能在其中，`A_SHARE_ONLY`文字不是封存BT已经执行的过滤。
- [当前维护配置](../../../../../config/etf_rotation_universe_v1.json)用于20只行情维护与角色分类。
  它不是已验证的交易池；日更OHLCV不等于旧策略所需份额/融资输入也已接入。
- [科技覆盖依据](../../../../../docs/data/ETF_TECHNOLOGY_COVERAGE.md)解释当前维护池的分类。
  换池会改变横截面排名与标准化，不能只过滤旧分数。

## 因子与策略的来源链

1. [因子注册表](../../../src/etf_strategy/core/factor_registry.py)描述数据源、边界与语义，
   不代表所有注册因子都进入回测；真正启用清单是配置的`active_factors`。
2. [量价因子公式](../../../src/etf_strategy/core/precise_factor_library_v2.py)与
   [份额/融资公式](../../../src/etf_strategy/core/non_ohlcv_factors.py)是预先编写的公式库。
   搜索在这些候选公式之间组装组合，并非本轮自动发明新公式。
3. [横截面处理](../../../src/etf_strategy/core/cross_section_processor.py)按日期和指定池标准化。
4. [WFO优化器](../../../src/etf_strategy/core/combo_wfo_optimizer.py)产生窗口统计、方向与ICIR元数据。
   方向使用窗口IC的符号一致性，权重在回测入口按绝对ICIR归一化。
5. [最终筛选](../../../scripts/final_triple_validation.py)同时使用训练、滚动和留出表现。
   因此旧留出段已经参与选择，不是新的独立确认集。
6. [BT入口](../../../scripts/batch_bt_backtest.py)读取冻结候选的方向与权重；
   [择时](../../../src/etf_strategy/core/market_timing.py)和
   [仓位/交易执行](../../../src/etf_strategy/auditor/core/engine.py)是不同层。

完整的旧挖掘流程、当前两套组合权重和标签时序审查见
[因子挖掘来源](../../../FACTOR_MINING_PROVENANCE.md)。旧单因子IC将D日收盘因子与已经结束的
D-1收盘到D收盘收益放在同日比较，因此不得继续解释为可执行预测IC。

阅读时以运行路径和候选元数据为准，不把注释中的旧数量、旧参数或注册表默认方向替代实际值。
本轮所用两套冻结策略的逐项因子、方向、权重、历史筛选来源见本地交接。

## 后续顺序

按当前方法执行：组结构诊断 → 组间单因子发现 → 基线/单腿/货架增量 → 冻结确认。
计划明确评价面、累计预算、失败记录、前向起点与开判规则。
旧14只裁判尚不等于八组裁判，持仓、成本和仓位管理属于之后的策略研究。
每轮保留输入、命令、源码版本与逐期评分证据。

不要把融资买入代理当作已经校准的真实比例，也不要把份额变化直接等同资金净流入。
研究性IC/留出收益与可执行收益分开；复现一致、测试通过和可上线是不同结论。

日常代码入口与执行模式详见[开发说明](../../../README.md)；
市场数据、冻结候选表、账单、报告和模型产物始终留在本地，不能随代码传输。
