# ETF IC 20 轮第 5 轮：沪铜结算价冲击，正式运行前提案

状态：`R05_EXT_COPPER_COMPLETED`。本文件保留 545 条登记后的**事前草案**与无标签预检原貌；该草案当时没有读取新候选 H5 标签。其后 master 批准冻结，一次性计算三条原 H5 IC，结果见[逐轮进度](ETF_IC_CAMPAIGN20_PROGRESS_20260926.md)。配置字节和事前方向未随结果更改。

研究问题仍固定为 14 ETF/8 经济组、D 收盘分数、D+2 复权开盘至 D+7 开盘 H5、每日完整八组 signed Rank IC、`cold_250_v1`。起点本地库存 `ic_inventory_20260926_545_r04` 为 545 条登记、522 条语义索引、16 条基础历史 IC 线索。拟新增 3 条至预算 548；不改原门槛、月度 v4 或评价人口。

**经济机制与事前方向。**沪铜主力连续结算价上行反映全球工业需求与顺周期风险偏好增强。上一已知期货交易日铜价上行时，历史上与铜价正向联动的组（有色、工业/科技制造周期暴露）假设在 D+2 至 D+7 继续相对走强；铜价下行时符号反转。三条方向均事前固定为 `+1`，只是可证伪的工业需求传导延续假设。与 R01–R04 属不同经济机制。

数据为本地 `long_history_proxies/macro/CU.parquet`（SHFE 铜前连续期货日结算价，2014-01-02 至冷线 2026-03-24 共 2970 行），SHA256 `3b9c25f6fcea3f20c72bedeb997e6eddd0038366012f27a149b720599017fd1e`。SHFE 与 A 股共用交易所休市日历；D 日结算价在 15:00 期货收盘定出，按冻结规则的 close(D) 口径作 D 日信息使用，与 `domestic_benchmark` 对 510300/510500 同日收盘的既有约定一致。期货缺值日保持缺失不填补，休市间隔自然累积为区间结算变化。主力连续合约换月与结算修订是版本限制；这是已见历史发现，不是 PIT 前向确认。

配置 [`group_ic_campaign20_r05_ext_copper_20260926.yaml`](../configs/group_ic_campaign20_r05_ext_copper_20260926.yaml) 与特征模块 `etf_group_ext_copper.py` 复用 R01 冻结的 D−1 结束三 beta 算术。三条均在中国 D 使用 `x_D`，历史估计配对日严格为 `t=D−60,…,D−1`；60 行完整配对，`ddof=0`、方差非正则缺失。成员分数按固定八组组内等权聚合；只有完整八组日进入原 IC。D 当日 ETF 收益与 `x_D` 均不进入暴露估计。

| 拟登记定义（方向均 `+1`） | 冻结统计及区分 |
|---|---|
| `copper_same_day_response_60` | `cov(r_i,t,x_t)/var(x_t) × x_D`；此前同日响应的工业需求重定价若未完成，预期延续。 |
| `copper_delayed_response_60` | `cov(r_i,t,x_{t−1})/var(x_{t−1}) × x_D`；此前隔一中国交易日响应的库存与订单链调整若未完成，预期延续；需要 D−61 的辅助源冲击。 |
| `copper_sign_asymmetry_60` | 历史 `x_t>0` 与 `<0` 各自估 beta，每支至少 10 日；按 D 的符号选支后乘 `x_D`，零冲击缺失；检验需求复苏上行与增长担忧下行的传导差异。 |

**查重近邻。**512400 有色金属 ETF 本身在候选池内，其内部动量族是显见近邻；R04 黄金、旧金属关联族与 `us_lagged_transmission_60` 为参考。事前不设相关性门，预检只按现有 0.7 口径注记。

**无标签预检。**见本地 `runtime_outputs/etf_rotation_research/preflight_ext_copper_r05_draft_20260926/`。复算命令：

```bash
.venv/bin/python frameworks/etf_rotation/scripts/research/preflight_ext_copper_r05.py \
  --output runtime_outputs/etf_rotation_research/preflight_ext_copper_r05_NEW
```

master 审阅点是事前 `+1` 方向机制、三条定义的可区分性、近邻冗余注记、期货结算版本限制与同日 close(D) 口径，以及预算 545→548；若批准，配置、源码及本地源须按 SHA 冻结并一次性运行，不能按结果挑定义或翻方向。
