# ETF IC 20 轮第 6 轮：INE 原油结算价冲击，正式运行前提案

状态：`R06_EXT_CRUDE_COMPLETED`。本文件保留 548 条登记后的**事前草案**与无标签预检原貌；该草案当时没有读取新候选 H5 标签。其后 master 批准冻结，一次性计算三条原 H5 IC，结果见[逐轮进度](ETF_IC_CAMPAIGN20_PROGRESS_20260926.md)。配置字节和事前方向未随结果更改。

研究问题仍固定为 14 ETF/8 经济组、D 收盘分数、D+2 复权开盘至 D+7 开盘 H5、每日完整八组 signed Rank IC、`cold_250_v1`。起点本地库存 `ic_inventory_20260926_548_r05` 为 548 条登记、525 条语义索引、16 条基础历史 IC 线索。拟新增 3 条至预算 551；不改原门槛、月度 v4 或评价人口。

**经济机制与事前方向。**上海 INE 原油结算价上行反映能源成本与通胀预期上升（人民币计价，同时含全球油价与汇率成分）。D 日原油结算上行时，历史上对该成本冲击正向联动的组（通胀敏感、能源链暴露）假设在 D+2 至 D+7 继续相对走强；油价下行时符号反转。三条方向均事前固定为 `+1`，只是可证伪的成本推动传导延续假设。与 R01–R05 属不同经济机制（R05 沪铜同为商品传导但驱动是工业需求而非能源成本）。

数据为本地 `long_history_proxies/macro/SC.parquet`（INE 原油前连续期货日结算价，2018-03-26 至冷线 2026-03-24 共 1939 行，覆盖 2025 评价窗所需的全部回看历史），SHA256 `9e8aca40eee9f95adf20b4f4b7e77d01157ef7e8512a609a71d7e48b61b69d66`。INE 与 A 股共用交易所休市日历；D 日结算价在 15:00 期货收盘定出，按冻结规则的 close(D) 口径作 D 日信息使用，与 `domestic_benchmark`、R05 沪铜同日口径一致。期货缺值日保持缺失，休市间隔自然累积。主力连续换月与结算修订是版本限制；这是已见历史发现，不是 PIT 前向确认。

配置 [`group_ic_campaign20_r06_ext_crude_20260926.yaml`](../configs/group_ic_campaign20_r06_ext_crude_20260926.yaml) 与特征模块 `etf_group_ext_crude.py` 复用 R01 冻结的 D−1 结束三 beta 算术。三条均在中国 D 使用 `x_D`，历史估计配对日严格为 `t=D−60,…,D−1`；60 行完整配对，`ddof=0`、方差非正则缺失。成员分数按固定八组组内等权聚合；只有完整八组日进入原 IC。D 当日 ETF 收益与 `x_D` 均不进入暴露估计。

| 拟登记定义（方向均 `+1`） | 冻结统计及区分 |
|---|---|
| `crude_same_day_response_60` | `cov(r_i,t,x_t)/var(x_t) × x_D`；此前同日响应的成本推动重定价若未完成，预期延续。 |
| `crude_delayed_response_60` | `cov(r_i,t,x_{t−1})/var(x_{t−1}) × x_D`；此前隔一中国交易日响应的燃料成本与物流链调整若未完成，预期延续；需要 D−61 的辅助源冲击。 |
| `crude_sign_asymmetry_60` | 历史 `x_t>0` 与 `<0` 各自估 beta，每支至少 10 日；按 D 的符号选支后乘 `x_D`，零冲击缺失；检验供给冲击上行与需求走弱下行的传导差异。 |

**查重近邻。**R05 沪铜共享商品传导模板但驱动不同；旧宏观族（`macro_r2_60` 等）、通胀关联族与 `us_lagged_transmission_60` 为参考。事前不设相关性门，预检只按现有 0.7 口径注记。

**无标签预检。**见本地 `runtime_outputs/etf_rotation_research/preflight_ext_crude_r06_draft_20260926/`。复算命令：

```bash
.venv/bin/python frameworks/etf_rotation/scripts/research/preflight_ext_crude_r06.py \
  --output runtime_outputs/etf_rotation_research/preflight_ext_crude_r06_NEW
```

master 审阅点是事前 `+1` 方向机制、三条定义的可区分性、近邻冗余注记、INE 期货结算版本限制与同日 close(D) 口径，以及预算 548→551；若批准，配置、源码及本地源须按 SHA 冻结并一次性运行，不能按结果挑定义或翻方向。
