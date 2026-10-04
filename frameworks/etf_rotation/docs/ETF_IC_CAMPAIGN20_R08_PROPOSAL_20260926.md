# ETF IC 20 轮第 8 轮：香港科技指数隔日传导，正式运行前提案

状态：`R08_EXT_HKTECH_COMPLETED`。本文件保留 554 条登记后的**事前草案**与无标签预检原貌；该草案当时没有读取新候选 H5 标签。其后 master 批准冻结，一次性计算三条原 H5 IC，结果见[逐轮进度](ETF_IC_CAMPAIGN20_PROGRESS_20260926.md)。配置字节和事前方向未随结果更改。

研究问题仍固定为 14 ETF/8 经济组、D 收盘分数、D+2 复权开盘至 D+7 开盘 H5、每日完整八组 signed Rank IC、`cold_250_v1`。起点本地库存 `ic_inventory_20260926_554_r07` 为 554 条登记、531 条语义索引、16 条基础历史 IC 线索。拟新增 3 条至预算 557；不改原门槛、月度 v4 或评价人口。

**经济机制与事前方向。**恒生科技指数上行反映香港科技板块风险偏好与南向资金预期改善。上一已知港市收盘恒科上行时，历史上对该冲击正向联动的组（港股科技组本身、创新药港股腿等跨境科技暴露）假设在 D+2 至 D+7 继续相对走强；恒科下行时符号反转。三条方向均事前固定为 `+1`，只是可证伪的跨市场传导延续假设。与 R01–R07 属不同经济机制。

数据为本地 `long_history_proxies/HKTECH.parquet`（恒生科技指数日收盘，2014-12-31 至冷线 2026-03-24 共 2762 个观测，无缺失、无重复、全部为正），SHA256 `3777af65b2406d0bf9bf71c6157594f9b7aa1099792cf6c7069ac89aec534610`。港股 16:00（北京时间）收盘晚于 A 股 15:00 收盘，因此对 A 股 D 只取观测日期**严格早于 D** 且距 D 至多 5 自然日的最近港市冲击；同日港收在 A 股 D 收盘时不可知，从不用作 D 日信息。快照非逐日归档，指数修订是版本限制；这是已见历史发现，不是 PIT 前向确认。

配置 [`group_ic_campaign20_r08_ext_hktech_20260926.yaml`](../configs/group_ic_campaign20_r08_ext_hktech_20260926.yaml) 与特征模块 `etf_group_ext_hktech.py` 复用 R01 冻结的 D−1 结束三 beta 算术。三条均在中国 D 使用 `x_D`，历史估计配对日严格为 `t=D−60,…,D−1`；60 行完整配对，`ddof=0`、方差非正则缺失。成员分数按固定八组组内等权聚合；只有完整八组日进入原 IC。D 当日 ETF 收益与 `x_D` 均不进入暴露估计。

| 拟登记定义（方向均 `+1`） | 冻结统计及区分 |
|---|---|
| `hktech_same_day_response_60` | `cov(r_i,t,x_t)/var(x_t) × x_D`；此前同日响应的港市重定价若未完成，预期延续。 |
| `hktech_delayed_response_60` | `cov(r_i,t,x_{t−1})/var(x_{t−1}) × x_D`；此前隔一中国交易日响应的再配置若未完成，预期延续；需要 D−61 的辅助源冲击。 |
| `hktech_sign_asymmetry_60` | 历史 `x_t>0` 与 `<0` 各自估 beta，每支至少 10 日；按 D 的符号选支后乘 `x_D`，零冲击缺失；检验风险偏好修复上行与流出压力下行的传导差异。 |

**查重近邻。**513130（港股科技 ETF）本身在候选池内，旧 peer_overnight_price_transmission 等以其为同伴的隔夜传导族是显见近邻；`us_lagged_transmission_60` 与 R01–R07 传导分数为参考。事前不设相关性门，预检只按现有 0.7 口径注记。

**无标签预检。**见本地 `runtime_outputs/etf_rotation_research/preflight_ext_hktech_r08_draft_20260926/`。复算命令：

```bash
.venv/bin/python frameworks/etf_rotation/scripts/research/preflight_ext_hktech_r08.py \
  --output runtime_outputs/etf_rotation_research/preflight_ext_hktech_r08_NEW
```

master 审阅点是事前 `+1` 方向机制、三条定义的可区分性、与 513130 同伴传导族的近邻冗余注记、港历严格前置时点与快照版本限制，以及预算 554→557；若批准，配置、源码及本地源须按 SHA 冻结并一次性运行，不能按结果挑定义或翻方向。
