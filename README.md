# ETF 独立研究项目

当前 ETF 因子挖掘已从 SmartMoney 迁回本仓库。本机路径为 `/home/sensen/dev/projects/-0927`，远端为 `zhangsensen/etf-rotation-strategy`。个股挖掘归 SmartMoney；源码、配置、候选登记、账本、结果和统计分母分开维护。

当前研究在固定 14 ETF / 8 经济组中评价冻结方向的有符号 Rank IC；旧策略平台使用自己的历史人口和执行合同。

2026-10-05 已完成迁移及遗留依赖复查，两边代码已推送。ETF 框架测试 1,058 项通过，根目录下载器与隔离集成测试另 8 项通过；244 个冻结 YAML 原字节一致。7 个已安装 ETF 调度定义指向本项目，另 2 个旧挖掘定义已归档停用；旧 autoresearch worktree 已收尾，历史实验原件保存在本项目本地。具体提交、验证命令与工程边界见下列迁回记录。

| 入口 | 位置 |
|---|---|
| 当前规则 | [AGENTS.md](AGENTS.md) |
| IC 挖掘源码与合同 | [frameworks/etf_rotation/README.md](frameworks/etf_rotation/README.md) |
| 当前 IC 环境与锁 | [pyproject.toml](frameworks/etf_rotation/pyproject.toml)、[uv.lock](frameworks/etf_rotation/uv.lock) |
| 独立数据更新 | `scripts/update_etf_rotation.py`、`data/downloaders/etf_rotation_backfill.py` |
| 调度定义 | `deployments/dagu/`、`deployments/etf_rotation/` |
| 迁移与原始证据路径 | [docs/IC_PROJECT_MIGRATION_20261004.md](docs/IC_PROJECT_MIGRATION_20261004.md) |
| 原平台说明 | [docs/HISTORICAL_PLATFORM_README.md](docs/HISTORICAL_PLATFORM_README.md) |

从项目根运行：

```bash
uv sync --project frameworks/etf_rotation --frozen
uv run --project frameworks/etf_rotation --no-sync python -m pytest -c frameworks/etf_rotation/pytest.ini frameworks/etf_rotation/tests
uv run --project frameworks/etf_rotation --no-sync python scripts/etf_rotation.py --data-root data/etf_rotation_v1 --as-of 2026-03-24 --roles candidate
```

当前 IC 环境与旧平台根环境分别锁定。新源码检出可运行合成测试；历史重放及行情冒烟需要本地原件。行情在 `data/etf_rotation_v1/`，IC 库和实验在 `runtime_outputs/`，均不随 Git 上传。

本次迁移不启动新因子挖掘或交易。冻结策略、历史成绩与当前发现分别解释。
