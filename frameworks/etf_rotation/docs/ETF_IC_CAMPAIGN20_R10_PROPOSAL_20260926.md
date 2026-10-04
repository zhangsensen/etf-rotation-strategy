# ETF IC 20 轮第 10 轮：焦煤结算价燃料成本冲击，正式运行前提案

状态：`R10_EXT_COAL_COMPLETED`。本文件保留 560 条登记后的**事前草案**与无标签预检原貌；该草案当时没有读取新候选 H5 标签。其后 master 批准冻结，一次性计算三条原 H5 IC，结果见[逐轮进度](ETF_IC_CAMPAIGN20_PROGRESS_20260926.md)。配置字节和事前方向未随结果更改。

研究问题仍固定为 14 ETF/8 经济组、D 收盘分数、D+2 复权开盘至 D+7 开盘 H5、每日完整八组 signed Rank IC、`cold_250_v1`。起点本地库存 `ic_inventory_20260926_560_r09` 为 560 条登记、537 条语义索引、16 条基础历史 IC 线索。拟新增 3 条至预算 563；不改原门槛、月度 v4 或评价人口。

**经济机制与事前方向。**DCE 焦煤结算价上行反映上游燃料/原材料成本压力上升（焦煤主要流向钢铁链而非电力，路线图 R15 的煤-电力双腿利润差机制在此**明确不主张**，本轮只是单源成本冲击）。D 日焦煤结算上行时，历史上与该成本冲击正向联动的组假设在 D+2 至 D+7 继续相对走强；焦煤下行时符号反转。三条方向均事前固定为 `+1`，只是可证伪的成本传导延续假设。与 R05 沪铜（工业需求）、R06 原油（能源成本，外盘口径）属不同源与不同成本链。

数据为本地 `long_history_proxies/macro/JM.parquet`（DCE 焦煤前连续期货日结算价，2014-01-02 至冷线 2026-03-24 共 2970 行），SHA256 `6a04398205a77536cad4ce2b9907fd2bc6aae84021717de7c0233c683c54c217`。DCE 与 A 股共用交易所休市日历；D 日结算价在 15:00 期货收盘定出，按冻结规则的 close(D) 口径作 D 日信息使用，与 `domestic_benchmark`、R05/R06 同日口径一致。期货缺值日保持缺失，休市间隔自然累积。主力连续换月与结算修订是版本限制；这是已见历史发现，不是 PIT 前向确认。

配置 [`group_ic_campaign20_r10_ext_coal_20260926.yaml`](../configs/group_ic_campaign20_r10_ext_coal_20260926.yaml) 与特征模块 `etf_group_ext_coal.py` 复用 R01 冻结的 D−1 结束三 beta 算术。三条均在中国 D 使用 `x_D`，历史估计配对日严格为 `t=D−60,…,D−1`；60 行完整配对，`ddof=0`、方差非正则缺失。成员分数按固定八组组内等权聚合；只有完整八组日进入原 IC。D 当日 ETF 收益与 `x_D` 均不进入暴露估计。

| 拟登记定义（方向均 `+1`） | 冻结统计及区分 |
|---|---|
| `coal_same_day_response_60` | `cov(r_i,t,x_t)/var(x_t) × x_D`；此前同日响应的成本重定价若未完成，预期延续。 |
| `coal_delayed_response_60` | `cov(r_i,t,x_{t−1})/var(x_{t−1}) × x_D`；此前隔一中国交易日响应的成本传导若未完成，预期延续；需要 D−61 的辅助源冲击。 |
| `coal_sign_asymmetry_60` | 历史 `x_t>0` 与 `<0` 各自估 beta，每支至少 10 日；按 D 的符号选支后乘 `x_D`，零冲击缺失；检验供给约束上行与需求走弱下行的传导差异。 |

**查重近邻。**R05 沪铜、R06 原油共享国内期货传导模板但经济驱动不同；旧宏观族与 `bond_trend_exposure_60` 为参考。路线图 R15 预先警示单一资源组主导剔组失败的风险，本轮 LOSO 诊断须如实检查。事前不设相关性门，预检只按现有 0.7 口径注记。

**无标签预检。**见本地 `runtime_outputs/etf_rotation_research/preflight_ext_coal_r10_draft_20260926/`。复算命令：

```bash
.venv/bin/python frameworks/etf_rotation/scripts/research/preflight_ext_coal_r10.py \
  --output runtime_outputs/etf_rotation_research/preflight_ext_coal_r10_NEW
```

master 审阅点是事前 `+1` 方向机制、三条定义的可区分性、单腿版本对 R15 双腿机制的显式降格说明、近邻冗余注记、期货结算版本限制与同日 close(D) 口径，以及预算 560→563；若批准，配置、源码及本地源须按 SHA 冻结并一次性运行，不能按结果挑定义或翻方向。
