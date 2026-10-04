# IC 项目迁回记录与操作路径

来源为 SmartMoney 提交 `b638ac85`；目的仓库原基线为 `4e5d1fb`，本地 `/home/sensen/dev/projects/-0927`。移入 1,399 个已跟踪 ETF 源码、配置、测试和说明文件，另补独立环境、数据传输依赖和项目路径适配。原策略平台及封印目录原位保留。

当前入口仍用 `frameworks/etf_rotation/` 相对布局，以保留配置内部来源路径。冻结 YAML 原字节保持不变。Python 的机器绝对路径改为项目本地根；旧配置物理路径由 `etf_strategy.project_paths.local_path` 映射到本项目，不更改标签、方向、人口、阈值、数据单位或计算逻辑。路径改动前的源码哈希见 [IC_MIGRATION_SOURCE_PATHS.json](IC_MIGRATION_SOURCE_PATHS.json)。

114 个 ETF 本地运行产物路径及 `data/etf_rotation_v1/` 的原件已在同一机器上迁入本项目，原件没有重算或改写。旧 SmartMoney 数据/结果路径保留兼容链接，指向本项目同一原件，供原绝对证据路径核对。原配置和旧源码哈希应按原提交解释；迁移后的入口不能冒充原封印代码。新 campaign 的代码指纹须重新登记，迁移不授予继续旧批次或新研究的权限。

数据源、实验源码快照、库、账本、凭据与结果不进 Git；不复制数据快照用于源码交接。原框架中的未跟踪私有说明、会话状态和结果也只在本项目本地保存。

个股当前挖掘仍归 SmartMoney 的 `alpha_mining/AI/`。其历史外部个股评价目录拥有独立的冻结计算模块、分类配置和来源公式记录，命名空间为 `stock_strategy`，不访问本项目或导入 `etf_strategy`。历史复用的算术不构成共享候选库、人口或 IC 结论。

复核命令：

```bash
uv sync --project frameworks/etf_rotation --frozen
uv run --project frameworks/etf_rotation --no-sync python -m pytest -c frameworks/etf_rotation/pytest.ini frameworks/etf_rotation/tests
uv run --project frameworks/etf_rotation --no-sync python -m pytest tests/test_etf_rotation_backfill.py tests/test_etf_project_isolation.py
uv run --project frameworks/etf_rotation --no-sync python scripts/etf_rotation.py --data-root data/etf_rotation_v1 --as-of 2026-03-24 --roles candidate
bash scripts/guard_no_data_in_git.sh
```

行情冒烟截止 2026-03-24、14 个候选 ETF，读取 21,609 个有效日线观测；只核验数据到参考特征链，不打开新收益标签或作因子认证。累计 IC 结果仍由原本地库读取，迁移不改变其统计。
