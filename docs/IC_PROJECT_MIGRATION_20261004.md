# IC 项目迁回记录与操作路径

更新：2026-10-05。源码迁移、独立环境、数据原件归属、现有调度路径及个股遗留依赖复查已完成；这是工程交接记录，不是因子研究或策略验收结果。

来源为 SmartMoney 提交 `b638ac85`；目的仓库原基线为 `4e5d1fb`，本地 `/home/sensen/dev/projects/-0927`。移入 1,399 个已跟踪 ETF 源码、配置、测试和说明文件，另补独立环境、数据传输依赖和项目路径适配。原策略平台及封印目录原位保留。

当前入口仍用 `frameworks/etf_rotation/` 相对布局，以保留配置内部来源路径。冻结 YAML 原字节保持不变。Python 的机器绝对路径改为项目本地根；旧配置物理路径由 `etf_strategy.project_paths.local_path` 映射到本项目，不更改标签、方向、人口、阈值、数据单位或计算逻辑。路径改动前的源码哈希见 [IC_MIGRATION_SOURCE_PATHS.json](IC_MIGRATION_SOURCE_PATHS.json)。

114 个 ETF 本地运行产物路径及 `data/etf_rotation_v1/` 的原件已在同一机器上迁入本项目，原件没有重算或改写。旧 SmartMoney 数据/结果路径保留兼容链接，指向本项目同一原件，供原绝对证据路径核对。原配置和旧源码哈希应按原提交解释；迁移后的入口不能冒充原封印代码。新 campaign 的代码指纹须重新登记，迁移不授予继续旧批次或新研究的权限。

数据源、实验源码快照、库、账本、凭据与结果不进 Git；不复制数据快照用于源码交接。原框架中的未跟踪私有说明、会话状态和结果也只在本项目本地保存。

个股当前挖掘仍归 SmartMoney 的 `alpha_mining/AI/`。其历史外部个股评价目录拥有独立的冻结计算模块、分类配置和来源公式记录，命名空间为 `stock_strategy`，不访问本项目或导入 `etf_strategy`。历史复用的算术不构成共享候选库、人口或 IC 结论。

个股历史资金流下载器原先读取已迁走的 ETF 配置，现已改读 SmartMoney 自有的 `alpha_mining/AI/config/stock_flow_proxy_funds_20260919.json`。20 个代理代码及名称与迁移前一致，仅保留个股特征所需的外部输入名单，不读取本项目的人口、账本或结果。SmartMoney 的本地 `frameworks/etf_rotation/results` 兼容链接已明确忽略，不随提交传输。

## 已推送代码与复核

| 仓库与分支 | 代码提交及范围 |
|---|---|
| ETF `master` | [7ab178e](https://github.com/zhangsensen/etf-rotation-strategy/commit/7ab178ea1a1dc516aa3adaee4e1c7a4001138378)：完整迁入当前 IC 项目 |
| SmartMoney `main` | [e3f96aad](https://github.com/zhangsensen/SmartMoney/commit/e3f96aadf498eb2581065be02eff46b37ceb3c9e)：移出 ETF 实现并解除历史个股计算依赖 |
| SmartMoney 补漏 | [5b6c048e](https://github.com/zhangsensen/SmartMoney/commit/5b6c048ed81d2b0c29a322fb6148fe22f35316f3)：固定个股资金流代理名单，忽略本地结果链接 |

两边代码提交均已在 2026-10-05 通过远端分支引用回读核对。文档后续更新另行提交，不改变以上代码基线。

迁移期间记录的工程验证：ETF 框架测试 1,058 项通过，根目录下载器与项目隔离集成测试另 8 项通过；两套命令合计 1,066 项，单独运行框架命令只计 1,058。历史外部个股测试 26 项通过，补漏后的 SmartMoney 根隔离测试 6 项通过。244 个冻结 ETF YAML 原字节对照一致；56 个历史个股计算模块在命名空间与上下文名称归一后 AST 一致，提取的上下文与执行收益标签逻辑另行对照未变。测试数量只表示工程检查，不是因子数量。

7 个已安装 Dagu 定义为 `etf_luna_open50_once`、`etf_ic_monthly_factory`、`etf_pi_forward_ledger`、`etf_pi_fund_data_daily`、`etf_rotation_paper_signal`、`etf_rotation_daily`、`etf_pi_round002_rerun_audit`。定义中的运行路径及 Python 环境改为本项目，原 schedule、max_active_runs、retry_policy、timeout、skip_if_successful 设置保持不变；历史 audit 使用迁入的原工作区。未触发这些任务，也未重启服务。

## 工程复核命令

以下 ETF 命令从本项目根运行；历史数据冒烟需要本机原件。

```bash
uv sync --project frameworks/etf_rotation --frozen
uv run --project frameworks/etf_rotation --no-sync python -m pytest -c frameworks/etf_rotation/pytest.ini frameworks/etf_rotation/tests
uv run --project frameworks/etf_rotation --no-sync python -m pytest tests/test_etf_rotation_backfill.py tests/test_etf_project_isolation.py
uv run --project frameworks/etf_rotation --no-sync python scripts/etf_rotation.py --data-root data/etf_rotation_v1 --as-of 2026-03-24 --roles candidate
bash scripts/guard_no_data_in_git.sh
```

行情冒烟截止 2026-03-24、14 个候选 ETF，读取 21,609 个有效日线观测；只核验数据到参考特征链，不打开新收益标签或作因子认证。累计 IC 结果仍由原本地库读取，迁移不改变其统计。

个股工程验证从 SmartMoney 根运行：

```bash
uv run --no-sync python -m pytest -q -c frameworks/stock_factor_research/pytest.ini frameworks/stock_factor_research/tests
uv run --no-sync python -m pytest -q tests/test_etf_equity_isolation.py
```

两边 commit 前检查暂存区，push 前用 `bash scripts/guard_no_data_in_git.sh --range BASE TIP` 检查每个新增提交，并由已安装 Git 钩子再次检查。只上传源码及必要配置、锁与文档；数据、账本、结果和凭据保持本地。迁移和这些复核不解除新挖掘暂停，也不授予交易、订单或实盘部署权限。

## 迁移后命令与依赖补漏（2026-10-05）

两份历史比较报告生成器的复现命令仍指定 SmartMoney 的 Python 环境，现改为本项目的 `uv run --project frameworks/etf_rotation --no-sync`。独立环境补入 `tabulate==0.9.0`，供现有 pandas Markdown 表格输出使用；锁文件只增加该依赖，报告计算逻辑与冻结结果没有改写。

独立环境的框架测试 1,058 项通过，根迁移/隔离测试另 8 项通过；两份命令入口及合成 Markdown 输出检查通过。日志仅留本地，不运行历史收益重放或启动挖掘。

## 核查残留与本地恢复（2026-10-05）

旧 `t0_etf9_sonnet_factor_mining_20r` 为九只 T+0 ETF 手动日内挖掘，沿用历史合同；`luna_v12_diversity20_20260928` 是已过期、旧入口失效的一次性挖掘。二者已从本机在用 Dagu 目录撤下，GPU ML 跟踪的 T+0 DAG 源副本也已撤下。原定义字节保存在 [归档说明](../deployments/archive/etf_mining_retired_20261005/README.md) 同目录的 `.yaml.archived` 文件中，不作为可部署 YAML，不改成当前 IC 任务。旧路径和模型名称是出处记录；未触发任务、重启服务或改动其他任务的调度设置。

GPU ML 主线框架下的本地残留为 Python 字节码和 pytest 缓存，未发现 `.py` 源文件；已移至本项目本地 `runtime_outputs/legacy_worktree_cleanup_20261005/main_framework_cache/`。旧 `gpu_ml-coral-autoresearch` worktree 没有已跟踪修改或未忽略的新文件，也没有使用其工作目录的进程，但存在 403 个被忽略的本地文件。移除 worktree 前已逐个原件迁移到 `runtime_outputs/legacy_worktree_cleanup_20261005/autoresearch/`，其中历史实验文件 97 个；内容 SHA-256 与 inode 核对一致。移动使用同机 rename，没有创建数据副本或上传证据。

旧 worktree 已从 Git 登记和原目录移除，`etf/ic-autoresearch` 分支及原提交 `a1475a8d` 保留，用于按原源码追溯。上述本地归档中的 `LOCAL_RECOVERY_MANIFEST.json` 记录原路径、归档路径、字节数及 SHA-256。工具配置 `.serena/project.yml` 的无关修改保留；`project_paths.py` 的 LEGACY_ROOTS 及历史 audit 中的旧绝对路径仍用于冻结出处和路径重映射，不是当前运行依赖。
