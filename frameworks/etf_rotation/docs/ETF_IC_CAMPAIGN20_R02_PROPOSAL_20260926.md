# ETF IC 20 轮第 2 轮：VIX 风险预期冲击，正式运行前提案

状态：`R02_VIX_COMPLETED`。本文件保留 536 条登记后的**事前草案**与无标签预检原貌；该草案当时没有读取新候选 H5 标签。其后 master 批准冻结，一次性计算三条原 H5 IC，结果见[逐轮进度](ETF_IC_CAMPAIGN20_PROGRESS_20260926.md)。配置字节和事前方向未随结果更改。

固定任务仍是 14 只 ETF/8 组的 D 收盘信号、D+2 复权开盘至 D+7 开盘 H5、每日完整八组 signed Rank IC、`cold_250_v1`，不改方向、人口、阈值、v4 或历史账本。起点本地库存 `ic_inventory_20260926_536_r01` 为登记 536、索引 513、基础历史 IC 线索 16。拟登记 3 条，预算 536→539；它们是同一“美国期权隐含风险预期传导”机制的即时、滞后、上升/下降不对称响应，不按回测结果挑其中一条。

**事前正方向机制。**[CBOE VIX](https://fred.stlouisfed.org/series/VIXCLS)是由标普 500 期权价格得到的近期期待波动率，不是资金净流入或 ETF 已实现波动率。上一已知美国收盘 VIX 上升是风险预期冲击；若跨市场去风险与仓位约束逐步传播，历史上对此冲击呈正收益暴露的组（可能包括避险/防御组）有机会在 D+2 至 D+7 保留相对强势，负暴露组相对走弱。VIX 下降时按有符号冲击反向排序。三条方向在见 H5 标签前均固定 `+1`。D 当日充分定价或 H5 均值回归会推翻该假设，不能把它写成确定收益规律。与 R01 半导体行业相对股指的信息冲击不同，R02 观察期权隐含风险价格；但来源不同不保证八组排名独立。

配置文件为 [`group_ic_campaign20_r02_vix_risk_20260926.yaml`](../configs/group_ic_campaign20_r02_vix_risk_20260926.yaml)，SHA256 `5cb6a350b6bdc180eeabf8435cf55c8781ffe4f83e493fad5d142808be9cf152`；分数源码 `etf_group_us_vix.py` SHA256 `8bea3bb94709c5cc148bfdb595126ae46953f1d24f051028493a5101157bd268`。原始 VIX 是本地 FRED 历史抓取裁剪至 2026-03-24 的 `runtime_outputs/etf_rotation_research/VIXCLS_cold_20260324.csv`，9451 条日行、其中 9150 个有效收盘，SHA256 `63649f6ec65b08471c6d93b0dc217c0be93f132a7bf528be009a03b67675a8bd`。文件只留本地。[CBOE 方法文件](https://cdn.cboe.com/api/global/us_indices/governance/VIX_Methodology.pdf)说明交易时段发布；美国收盘在中国同日收盘之后。对每个 A 股 D，只选日期严格小于 D 且至多早 5 自然日的最近有效美国观测，不用同日美国收盘。2025 年至冷线的 294 个 A 股分数日全部匹配，最大旧度 4 自然日。FRED 快照不是逐日归档，历史修订风险仍在，故仅作已见历史发现。

定义 `x_D = ln(VIX_u/VIX_{u^-})`，`u` 为上述最近有效美国观测日，`u^-` 是前一个有效美国观测日；`r_i,t` 为 ETF 复权收盘至收盘收益。历史 beta 的 ETF 收益配对日严格为 `t=D−60,…,D−1`，完整 60 行，`ddof=0`，方差非正或缺任一输入即缺失。组分数为 14 只成员按固定八组等权聚合；只有完整八组日期进入原 IC。D 的 ETF 当日收益不进入 beta，D 的 `x_D` 只作乘数/分支。精确缺失条件和方向均写在配置中。

| 事前定义 | 分数公式及经济区别 | 方向 |
|---|---|---:|
| `vix_risk_same_day_response_60` | `cov(r_i,t,x_t)/var(x_t) × x_D`：历史即时防御/风险响应可能延续 | +1 |
| `vix_risk_delayed_response_60` | `cov(r_i,t,x_{t−1})/var(x_{t−1}) × x_D`：历史隔一 A 股交易日去风险响应可能延续；还需 D−61 的辅助源冲击 | +1 |
| `vix_risk_sign_asymmetry_60` | 按历史 `x_t>0` 与 `<0` 分别算 beta，每支≥10 日；以 D 的正/负冲击选支后乘 `x_D`，D 冲击为零则缺失 | +1 |

**无标签预检。**在 2025-01-02 至 2026-03-24，三条分别有 294、294、293 个完整八组分数日；少的 1 日为零冲击不进入不对称分支。2024-12-31 截断重载与截断后输入扰动均保持此前收益及分数相同。与最新 513 条索引定义比较，形成 1503 个有共同完整日期的候选-旧库配对；9 份旧保存分数缺失。最近旧定义的平均绝对逐日八组秩相关依次为 0.641（`nav_basis_volatility_20`，共同 189 日）、**0.727**（`us_lagged_transmission_60`，293 日）、0.520（`peer_corr_dispersion_60`，293 日）；本轮内部三对为 0.402、0.661、0.329（各共同 293 日）。第二条按既有 `≥0.7` 规则须标**分数冗余**，若获准正式运行仍保留其 IC 算术与负结果，不把它说成独立信息；该诊断不新增 IC 门。其余两条在现有口径下未见高相关，仍不等于可交易增量。完整预检在本地 `runtime_outputs/etf_rotation_research/preflight_vix_risk_r02_draft_20260926/`，不入代码提交。

预检命令：

```bash
.venv/bin/python frameworks/etf_rotation/scripts/research/preflight_vix_risk_r02.py \
  --output runtime_outputs/etf_rotation_research/preflight_vix_risk_r02_NEW
```

正式运行前的审核点为：VIX 风险预期冲击的 `+1` 单边假设、滞后定义与旧纳指传导分数 0.727 的冗余注记、FRED 历史版本限制、3 条定义的预算。master 已按上述条件通过；本文件无标签预检段落不因正式结果重写。
