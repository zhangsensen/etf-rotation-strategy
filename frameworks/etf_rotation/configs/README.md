# ETF 配置入口

当前自动发现使用固定 14 ETF / 8 组，不从文件名中的 current20、v1 或日期推断“现行”。

| 用途 | 现行合同 |
|---|---|
| 14 只候选人口 | [仓库维护配置的 candidate 角色](../../../config/etf_rotation_universe_v1.json) |
| 八组经济暴露 | [etf_candidate14_economic_groups_v1.yaml](etf_candidate14_economic_groups_v1.yaml) |
| 月度前向工厂 | [etf_ic_monthly_factory_v4.yaml](etf_ic_monthly_factory_v4.yaml) |
| 独立历史线索观察 | [etf_ic_lead_watch_v2.yaml](etf_ic_lead_watch_v2.yaml) |

[历史批次与被替代合同](HISTORICAL_INDEX.md)原址归档：文件路径及正文保持不变，原 PLAN 与源码哈希仍可核对；普通 rg 搜索不再混入这些条目。显式指定文件或使用 `rg --no-ignore <模式> frameworks/etf_rotation/configs` 可查历史。

其他 automated/family/WFO/regime 配置服务旧方法或另立问题，不是当前自动发现入口，按其保存运行的合同解释。全部配置仍可由显式路径加载；本次不把文件名版本号当作删除依据。

个股的 external_stock 配置单列于[个股研究入口](https://github.com/zhangsensen/SmartMoney/tree/main/frameworks/stock_factor_research)，不计入 ETF 结果。当前批次操作见[自动发现规范](../docs/ETF_AUTORESEARCH_PROGRAM.md)。
