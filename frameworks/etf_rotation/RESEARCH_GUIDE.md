# ETF 源码阅读入口

先读[研究规则](docs/IC_MINING_RULES.md)和[自动发现流程](docs/ETF_AUTORESEARCH_PROGRAM.md)，再沿下表检查实现。当前问题、命令和结果库统一从 [README](README.md) 进入。

| 环节 | 实现 | 检查重点 |
|---|---|---|
| 命令行 | [run_etf_autoresearch_campaign.py](scripts/research/run_etf_autoresearch_campaign.py) | 当前 workflow 入口、模型传输与候选接口校验 |
| 批次控制 | [etf_autoresearch_workflow.py](scripts/research/etf_autoresearch_workflow.py) | 开放模式、预算、冻结、阶段状态和恢复 |
| 规划与上下文 | [diversity](scripts/research/etf_autoresearch_diversity.py)、[context](scripts/research/etf_autoresearch_context.py) | 开放提案与历史检索；旧家族调度已移出执行路径 |
| 输入 | [etf_autoresearch_inputs.py](scripts/research/etf_autoresearch_inputs.py) | 批准的 profile、冷线、可用时点、陈旧处理和来源哈希 |
| 公式审阅与实现 | [plan_review](scripts/research/etf_autoresearch_plan_review.py)、[implementation](scripts/research/etf_autoresearch_implementation.py) | 冻结公式优先；模板不得改变统计量；合成检查 |
| 标签前分数预检 | [score_preflight](scripts/research/etf_autoresearch_score_preflight.py) | 因果前缀、完整八组可排名日、同合同精确重复 |
| IC 评价 | [run_etf_autoresearch_ic.py](scripts/research/run_etf_autoresearch_ic.py)、[etf_group_discovery.py](src/etf_strategy/core/etf_group_discovery.py) | 原 signed Rank IC、D+2/H5、完整日历、平均并列秩 |
| 落盘与恢复 | [recovery](scripts/research/etf_autoresearch_recovery.py) | 源码、输入、分数与结果封印一致性 |
| 进度与累计库 | [status](scripts/research/etf_autoresearch_status.py)、[library](scripts/research/etf_autoresearch_library.py) | 完成证据、公式/方向/窗口、完整性、正式与自适应分别计数 |
| 正式历史库 | [build_ic_inventory.py](scripts/research/build_ic_inventory.py) | 登记映射、方向视图、旧筛选诊断、新快照 |

相关回归检查在仓库根执行：

```bash
.venv/bin/python -m pytest -q frameworks/etf_rotation/tests/test_etf_autoresearch*.py frameworks/etf_rotation/tests/test_schedule_etf_luna_campaign.py frameworks/etf_rotation/tests/test_ic_inventory.py --tb=short
```

当前测试按职责组织：`workflow` 检查审阅和结果留存，`workflow_execution` 检查开放批次、恢复和故障隔离，`source_contract` 检查候选接口。旧单因子爬山、配额与来源轮换代码及相应用例见[代码归档](legacy/autoresearch_20261003/README.md)，不在默认测试集合中。时序、方向、缺失、精确重复、封印和历史读取测试继续保留。`test_talib_golden.py` 锁 `TA-Lib==0.8.1` 版本与黄金输出值（见[预检记录](docs/RULE_INDICATOR_PRECHECK_20261003.md)），talib 缺席时跳过。TA-Lib 全部 201 函数/240 因子的普查结论见[全函数普查记录](docs/TALIB_FULL_SWEEP_20261004.md)。

[八组正式历史入口](docs/group_discovery_runner.md)保留原 PLAN 登记及复算路径；当前发现不必先进入正式账本才交付 IC。源码冻结与输入合同是结果的一部分，不能删除被历史运行引用的旧实现。

[历史开发指南](docs/archive/20261003/ETF_DEVELOPMENT_GUIDE.md)、[历史来源链](docs/archive/20261003/RESEARCH_GUIDE.md)保留旧 WFO、组合权重和 BT 接线。旧单因子同时刻收益、历史联合收益门及 20/49 只旧池不能代替当前八组 IC 合同。份额变化、融资代理、二级市场大单资金流也不能混称净流入。
