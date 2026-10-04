# ETF IC 20 轮第 3 轮：美国大盘价值相对成长风格，正式运行前提案

状态：`R03_US_STYLE_COMPLETED`。本文件保留 539 条登记后的**事前草案**与无标签预检原貌；该草案当时没有读取新候选 H5 标签。其后 master 批准冻结，一次性计算三条原 H5 IC，结果见[逐轮进度](ETF_IC_CAMPAIGN20_PROGRESS_20260926.md)。配置字节和事前方向未随结果更改。

研究问题仍固定为 14 ETF/8 经济组、D 收盘分数、D+2 复权开盘至 D+7 开盘 H5、每日完整八组 signed Rank IC、`cold_250_v1`。起点本地库存 `ic_inventory_20260926_539_r02` 为 539 条登记、516 条语义索引、16 条基础历史 IC 线索。拟新增 3 条至预算 542；不改原门槛、月度 v4 或评价人口。

**经济机制与事前方向。**[Nasdaq 美国风格指数方法](https://indexes.nasdaq.com/docs/methodology_USStyleFamily.pdf)定义同一美国大盘基准中的[价值](https://fred.stlouisfed.org/series/NASDAQNQUSLV)与[成长](https://fred.stlouisfed.org/series/NASDAQNQUSLG)证券。上一已知美国收盘价值相对成长走强时，全球风险预算可能向低久期/价值风格逐步移动；此前对这种*相对风格冲击*有正收益暴露的 ETF 组，假设会在 D+2 至 D+7 继续相对走强。相对成长走强时，符号反转。三条方向均事前固定为 `+1`；这只是可证伪的跨市场风格延续假设，不保证中国 ETF 跟随，更不保证 H5 延续。它与 R01 半导体行业信息、R02 期权隐含风险冲击属于不同经济机制；但三轮都有历史暴露统计，必须检查分数冗余。

使用两条 **price index**，不混用 total return：在两个指数都有有效值的同一个美国日期集合上，各自对前一个**共同有效美国日**计算简单收益，`x_US = r_value − r_growth`。对 A 股 D 只取观测日期**严格早于 D**且距 D 至多 5 自然日的最近 `x_US`。同一美国日的收盘无论网站何时更新，都不能在中国同日收盘使用。当前 FRED 历史快照各 6518 行、6299 个有效指数值；截至冷线 2026-03-24 的本地文件 SHA256 分别 `19d72245683272a969ee265bc98930c34e815d2eb3a8c003fc002c347b9cac71`、`d36977206b2b311ff982177afae832a53f03fd4236b8f05af4d42c1c47a10288`。中国评价日期最近源最大旧度 4 自然日。Nasdaq 收盘可能校正，FRED 快照并非逐日归档；这是已见历史发现，不是 PIT 前向确认。

配置 [`group_ic_campaign20_r03_us_style_20260926.yaml`](../configs/group_ic_campaign20_r03_us_style_20260926.yaml) SHA256 `1d2023193822a209c10cad93c6486b931a4d8eaa2e65f3f67c753ce7ffbe2c86`；特征模块 `etf_group_us_style.py` SHA256 `f1d43d6a53ed49bd46ad2b3c651fe2ac675d6e9bae6c4994e79630bcf7f6774c`。三条均在中国 D 使用 `x_D`，ETF 复权收盘日收益 `r_i,t` 的历史估计配对日严格为 `t=D−60,…,D−1`；60 行完整配对，`ddof=0`、方差非正则缺失。成员分数按固定八组组内等权聚合；只有完整八组日进入原 IC。D 当日 ETF 收益与 `x_D` 均不进入暴露估计。

| 拟登记定义（方向均 `+1`） | 冻结统计及区分 |
|---|---|
| `us_style_same_day_response_60` | `cov(r_i,t,x_t)/var(x_t) × x_D`；此前同日响应的风格轮动若未完成，预期延续。 |
| `us_style_delayed_response_60` | `cov(r_i,t,x_{t−1})/var(x_{t−1}) × x_D`；此前隔一中国交易日响应的风格轮动若未完成，预期延续；需要 D−61 的辅助源冲击。 |
| `us_style_sign_asymmetry_60` | 历史 `x_t>0` 与 `<0` 各自估 beta，每支至少 10 日；按 D 的符号选支后乘 `x_D`，零冲击缺失；检验价值主导和成长主导传导速度差异。 |

**无标签预检。**三条各有 294 个完整八组分数日，2025-01-02 至 2026-03-24。2024-12-31 前缀的冷线重载收益与分数一致，未来输入扰动不改变过去分数。对 516 条索引旧定义形成 1512 个有共同完整日期的候选-旧库相关性结果，另有 9 份旧保存分数缺失。平均绝对逐日八组秩相关的最近旧定义：同期 0.543（R01 SOX 同期，n294）；滞后 **0.740**（旧 `us_lagged_transmission_60`，n294），另有 0.712 对 `l64_post_outside_return_spread_20` 但只共同 11 日；不对称 0.518（`market_residual_market_beta_20`，n243）。本轮内部三对为 0.406、0.459、0.368（各 n294）。滞后项按现有 0.7 口径标分数冗余；若正式运行，仍保存其原方向 IC 算术及成败，不声称独立新信息。稀疏 n11 的相关只作为不稳定提示。现有国内 `cn_mid_large_style_transmission_60` 是大中盘尺寸差异而非美国价值-成长，其与本轮不对称项相关 0.494，不足以证明经济增量。

预检工件只在本地 `runtime_outputs/etf_rotation_research/preflight_us_style_r03_draft_20260926/`。复算命令：

```bash
.venv/bin/python frameworks/etf_rotation/scripts/research/preflight_us_style_r03.py \
  --output runtime_outputs/etf_rotation_research/preflight_us_style_r03_NEW
```

正式 H5 结果尚不存在。master 审阅点是事前 `+1` 方向机制、三条定义的可区分性、滞后项的 0.740 冗余注记、Nasdaq/FRED 版本限制，以及预算 539→542；若批准，配置、源码及两条本地源须按 SHA 冻结并一次性运行，不能按结果挑定义或翻方向。
