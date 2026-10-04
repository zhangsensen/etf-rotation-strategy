# ETF IC 20 轮第 9 轮：美国 10 年期实际利率冲击，正式运行前提案

状态：`R09_EXT_REALRATE_COMPLETED`。本文件保留 557 条登记后的**事前草案**与无标签预检原貌；该草案当时没有读取新候选 H5 标签。其后 master 批准冻结，一次性计算三条原 H5 IC，结果见[逐轮进度](ETF_IC_CAMPAIGN20_PROGRESS_20260926.md)。配置字节和事前方向未随结果更改。

研究问题仍固定为 14 ETF/8 经济组、D 收盘分数、D+2 复权开盘至 D+7 开盘 H5、每日完整八组 signed Rank IC、`cold_250_v1`。起点本地库存 `ic_inventory_20260926_557_r08` 为 557 条登记、534 条语义索引、16 条基础历史 IC 线索。拟新增 3 条至预算 560；不改原门槛、月度 v4 或评价人口。

**经济机制与事前方向。**美债 10 年期实际收益率上行收紧全球实际贴现率，降低长久期与零息资产吸引力。上一已知美市观测实际利率上行时，历史上与该冲击正向联动的组假设在 D+2 至 D+7 继续相对走强（长久期/黄金组历史 beta 多为负，负 beta × 正冲击自然排后）；实际利率下行时符号反转。三条方向均事前固定为 `+1`，只是可证伪的实际利率传导延续假设。与 R01–R08 属不同经济机制。旧 `real_rate_beta` 是显见近邻：那是候选对美国实际利率代理的暴露本身，本轮是实际利率冲击的历史响应传导，须检查分数冗余。

数据为本地 `long_history_proxies/macro/us_trycr.parquet`（美债平价实际收益率曲线，取 y10，百分比水平，2014-01-02 至冷线 2026-03-24 共 3053 个观测、无缺失；水平可负），SHA256 `21b2f6979e061c4fdbbab3bb89d40212c94c7e480c2b25ab8fd6e84f8e1d5471`。**冲击采用算术一阶差分**（水平可负，不得取对数）。对 A 股 D 只取观测日期**严格早于 D**且距 D 至多 5 自然日的最近冲击。财政部实际收益率曲线存在修订，快照非逐日归档；这是已见历史发现，不是 PIT 前向确认。

配置 [`group_ic_campaign20_r09_ext_realrate_20260926.yaml`](../configs/group_ic_campaign20_r09_ext_realrate_20260926.yaml) 与特征模块 `etf_group_ext_realrate.py` 复用 R01 冻结的 D−1 结束三 beta 算术。三条均在中国 D 使用 `x_D`，历史估计配对日严格为 `t=D−60,…,D−1`；60 行完整配对，`ddof=0`、方差非正则缺失。成员分数按固定八组组内等权聚合；只有完整八组日进入原 IC。D 当日 ETF 收益与 `x_D` 均不进入暴露估计。

| 拟登记定义（方向均 `+1`） | 冻结统计及区分 |
|---|---|
| `realrate_same_day_response_60` | `cov(r_i,t,x_t)/var(x_t) × x_D`（x 为 y10 算术差分）；此前同日响应的久期重定价若未完成，预期延续。 |
| `realrate_delayed_response_60` | `cov(r_i,t,x_{t−1})/var(x_{t−1}) × x_D`；此前隔一中国交易日响应的配置调整若未完成，预期延续；需要 D−61 的辅助源冲击。 |
| `realrate_sign_asymmetry_60` | 历史 `x_t>0` 与 `<0` 各自估 beta，每支至少 10 日；按 D 的符号选支后乘 `x_D`，零冲击缺失；检验紧缩上行与宽松下行的传导差异。 |

**查重近邻。**旧 `real_rate_beta`、`us_lagged_transmission_60`、R01–R08 传导分数与黄金组动量族为参考（实际利率与金价强负相关是已知关系）。事前不设相关性门，预检只按现有 0.7 口径注记。

**无标签预检。**见本地 `runtime_outputs/etf_rotation_research/preflight_ext_realrate_r09_draft_20260926/`。复算命令：

```bash
.venv/bin/python frameworks/etf_rotation/scripts/research/preflight_ext_realrate_r09.py \
  --output runtime_outputs/etf_rotation_research/preflight_ext_realrate_r09_NEW
```

master 审阅点是事前 `+1` 方向机制、三条定义的可区分性、与 `real_rate_beta` 的近邻冗余注记、算术差分口径与快照版本限制，以及预算 557→560；若批准，配置、源码及本地源须按 SHA 冻结并一次性运行，不能按结果挑定义或翻方向。
