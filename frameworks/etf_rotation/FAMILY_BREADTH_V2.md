# ETF 家族广度第二版

入口为 `configs/family_catalog_v2.yaml`，对应分类为
`configs/economic_axis_taxonomy_v2.yaml`。v1 保持不变，用于复现历史。
本版扩展到31个家族、147个原子，仍归入10个经济轴；家族名称不等于经济独立性。
当前20只维护、14只候选的角色合同不变。仅使用D收盘及之前的信息；后续标签仍为
D+2开盘开始的5/10/20日收益。本轮广度验收不读取未来收益，不进行IC筛选。

| 新家族 | 机制 | 20/60日原子前缀 |
|---|---|---|
| transaction_friction | 滞后一期收益的负协方差，交易摩擦代理 | RETURN_REVERSAL_COV |
| conditional_activity | 下跌日与上涨日平均成交额之比 | DOWN_UP_ACTIVITY |
| return_concentration | 收益平方和除以绝对收益总和的平方 | RETURN_CONCENTRATION |
| auction_range_overlap | 相邻交易日价格区间交集与并集之比 | RANGE_OVERLAP |
| activity_response | 前日绝对收益与当日成交额对数变化的相关性 | SHOCK_ACTIVITY_RESPONSE |
| uncertainty_activity | 振幅比例变化与成交额对数变化的相关性 | RANGE_ACTIVITY_ELASTICITY |

每家族两个窗口共12个原子，不能称为12个独立机制。交易摩擦是价格代理，不能称为实际买卖价差。
成交额也不等于申赎或资金净流入。条件成交统计要求窗口至少各有3个上涨、下跌日；零成交、
无定义分母和恒定振幅变化保留缺失，不回填。五类ETF原生数据家族仍保留明确缺口：份额申赎、
NAV/IOPV折溢价、底层指数跟踪、持仓漂移、一级市场篮子与报价。

验收使用 `scripts/validate_family_catalog.py`，参数为 v2目录、根目录
`config/etf_rotation_universe_v1.json`、数据根
`/home/sensen/dev/projects/gpu_ml/data/etf_rotation_v1`、`--as-of 2026-09-17`。
本地输出为 `runtime_outputs/etf_family_catalog_v2_breadth_20260919.json`。
要求所有原子有真实合格样本、没有完全秩别名、跨家族绝对秩相关没有达到0.98的组合。
测试 `tests/test_breadth_extensions.py` 检查未来扰动、截断一致性、价格缩放和无定义输入。
目录验收通过不等于IC认证；后续挖掘仍需更严格的候选相关性去重与有效维数检查。

本轮曾提出 `liquidity_cost`，但其20/60日原子与已有 `AMIHUD` 原子绝对秩相关为
0.9885/0.9840，已删除实现并在v2目录记录为关闭的重复家族。最终新增6个家族、12个原子。
