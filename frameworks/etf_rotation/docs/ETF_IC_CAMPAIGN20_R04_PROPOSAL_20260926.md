# ETF IC 20 轮第 4 轮：国际黄金现货冲击，正式运行前提案

状态：`R04_EXT_GOLD_COMPLETED`。本文件保留 542 条登记后的**事前草案**与无标签预检原貌；该草案当时没有读取新候选 H5 标签。其后 master 批准冻结，一次性计算三条原 H5 IC，结果见[逐轮进度](ETF_IC_CAMPAIGN20_PROGRESS_20260926.md)。配置字节和事前方向未随结果更改。

研究问题仍固定为 14 ETF/8 经济组、D 收盘分数、D+2 复权开盘至 D+7 开盘 H5、每日完整八组 signed Rank IC、`cold_250_v1`。起点本地库存 `ic_inventory_20260926_542_r03` 为 542 条登记、519 条语义索引、16 条基础历史 IC 线索。拟新增 3 条至预算 545；不改原门槛、月度 v4 或评价人口。

**经济机制与事前方向。**国际现货黄金上涨反映避险与抗通胀需求上升及实际利率压力缓解。上一已知外市金价上行时，历史上与金价正向联动的组（黄金组本身、有色/通胀敏感暴露）假设在 D+2 至 D+7 继续相对走强；金价下行时符号反转。三条方向均事前固定为 `+1`，只是可证伪的跨资产联动延续假设。与 R01（半导体行业信息）、R02（期权隐含风险）、R03（美国风格轮动）属不同经济机制。

数据为本地 `long_history_proxies/macro/XAUUSD.parquet`（FXCM 现货金买卖收盘，mid=(bid_close+ask_close)/2，2014-01 至冷线 2026-03-24 共 3324 行，无缺失），SHA256 `8edbeb8cd1acb881e63b1eb522a07cd8ad58fe9048290bdad60999423c78ad9d`。近 24 小时全球市场，日线以纽约 ~17:00 收束；对 A 股 D 只取观测日期**严格早于 D**且距 D 至多 5 自然日的最近冲击。快照非逐日归档，可能被修订回填；这是已见历史发现，不是 PIT 前向确认。

配置 [`group_ic_campaign20_r04_ext_gold_20260926.yaml`](../configs/group_ic_campaign20_r04_ext_gold_20260926.yaml) 与特征模块 `etf_group_ext_gold.py` 复用 R01 冻结的 D−1 结束三 beta 算术（`etf_group_us_sector.score_atoms`）。三条均在中国 D 使用 `x_D`，ETF 复权收盘日收益 `r_i,t` 的历史估计配对日严格为 `t=D−60,…,D−1`；60 行完整配对，`ddof=0`、方差非正则缺失。成员分数按固定八组组内等权聚合；只有完整八组日进入原 IC。D 当日 ETF 收益与 `x_D` 均不进入暴露估计。

| 拟登记定义（方向均 `+1`） | 冻结统计及区分 |
|---|---|
| `gold_same_day_response_60` | `cov(r_i,t,x_t)/var(x_t) × x_D`；此前同日响应的避险/通胀重定价若未完成，预期延续。 |
| `gold_delayed_response_60` | `cov(r_i,t,x_{t−1})/var(x_{t−1}) × x_D`；此前隔一中国交易日响应的配置调整若未完成，预期延续；需要 D−61 的辅助源冲击。 |
| `gold_sign_asymmetry_60` | 历史 `x_t>0` 与 `<0` 各自估 beta，每支至少 10 日；按 D 的符号选支后乘 `x_D`，零冲击缺失；检验风险规避驱动的上行与正常化下行的传导速度差异。 |

**查重近邻。**518880 黄金 ETF 本身在候选池内，其内部动量族是显见近邻；旧 `us_lagged_transmission_60`、R01–R03 传导分数及有色金属相关族为参考。事前不设相关性门，预检只按现有 0.7 口径注记。正式运行后仍保存原方向 IC 算术，不以相关性丢弃或翻向。

**无标签预检。**见本地 `runtime_outputs/etf_rotation_research/preflight_ext_gold_r04_draft_20260926/`。复算命令：

```bash
.venv/bin/python frameworks/etf_rotation/scripts/research/preflight_ext_gold_r04.py \
  --output runtime_outputs/etf_rotation_research/preflight_ext_gold_r04_NEW
```

master 审阅点是事前 `+1` 方向机制、三条定义的可区分性、近邻冗余注记、FXCM 快照版本限制，以及预算 542→545；若批准，配置、源码及本地源须按 SHA 冻结并一次性运行，不能按结果挑定义或翻方向。
