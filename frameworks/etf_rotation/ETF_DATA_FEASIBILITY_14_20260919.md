# 14 只 ETF 数据面可用性核查（2026-09-19，只读探测，未写任何数据）

目的：裸 K + 量面已用尽（17 轮 94 条），目录里 5 个家族因缺数据 blocked。逐项核"能用 / 不能用"，不凭印象。
探测方式：本地 `data/tech_etf_ts` 现有文件 + Tushare pro 只读查询（`fund_share` / `fund_nav` / `fund_basic` / `index_basic` / `index_daily` / `index_global` / `sge_daily`）。

## 结论表

| 数据 | 结论 | 证据 | 解封家族 |
|---|---|---|---|
| **日度份额（净申赎）** | **能用** | 本地已有 7/14（2019-08～2023-07 起，PIT `usable_from_date` 中位滞后 1 天）；Tushare 补齐另 7 只全部有数：159611 自 2021-12、159992 自 2020-03、512400/513100/518880 自 2018-07、512890 自 2018-12、513120 自 2022-07；字段 `fd_share` 日频 | share_creation_redemption_flow |
| **NAV → 折溢价** | **能用** | Tushare `fund_nav` 14/14 全有，`ann_date` 全部非空（PIT 可按公告日对齐；本地 2 只样本 `usable_from_date` 滞后中位 2 天）；起点 = 各自成立日；折溢价 = 已有收盘价 / NAV − 1 | nav_premium_discount |
| **标的指数日线（境内 11 只）** | **能用，但映射必须用官方指数代码** | `index_basic` CSI 8000 / CNI 1134 条，`index_daily` 2020-01 有数（抽样 8 只）；`fund_basic` 只给基准文字不给代码，按名字模糊匹配会错（例：159995 匹到 HKD 版、512890 匹到大湾区版、562500 匹到科创创业版）→ 映射表须从基金合同/指数公司取代码后逐只核对 | tracking_quality（境内部分） |
| 标的指数（恒生科技、纳指 100） | **当前不能用** | `index_global` HSTECH / NDX 返回 0 行（权限或代码不通）；2 只 QDII 的跟踪质量暂缺 | tracking_quality 缺 2 只 |
| 黄金现货 Au99.99 | **能用** | `sge_daily` 2020-01 有数 | tracking_quality（518880） |
| 持仓明细 | 不做 | Tushare `fund_portfolio` 季频，PIT 靠公告日，对 5 日持有期几乎无信息 | holdings_concentration_drift 保持 blocked |
| 盘中 IOPV / 申赎清单 / L2 | **不能用（无历史）** | QMT 只能从今往后取；CMES 无此字段 | primary_market_microstructure 保持 blocked |
| 股票侧库（money_flow 5873 个股、margin、daily_basic、limit_list、fundamentals、events） | **无关** | 14 只 ETF 均不在其中 | — |
| 更多 K 线周期 / 1m 更长历史 / 更多 ETF | **不需要** | K 线面已测尽；人口固定 14 | — |

## 发现期覆盖提醒
份额/NAV 起点 = 成立日，与 K 线 eligibility 一致：159516（2023-07）、513120（2022-07）、159611/562500（2021-12）、159732（2021-08）、513130（2021-05）在 2021–2023 发现期内只有部分覆盖，与现有因子相同，不新增偏差。

## 生产边界
ETF 主库 `etf_rotation_v1` 由 Linux 侧 TuShare/CMES 独立生产（`docs/data/ETF_DATA_PIPELINE.md`），不涉及 Windows QMT VM。现成代码：`data/downloaders/tech_etf_ts_downloader.py`（`normalize_fund_share`、nav 的 `ann_date`/`usable_from_date` 处理）。
落地顺序（获批后）：① 份额 14 只 → ② NAV 14 只 + 折溢价 → ③ 官方指数代码映射表 + 11 只境内指数 + Au99.99 → 并入日更 → 解封 3 个家族 → pi 在原合同（14 只、单因子、门 7）下继续。

## 落地记录（2026-09-19 23:20）
- 已拉入 `data/etf_rotation_v1/fund_share/`（14 只，`fd_share`/`fund_shares`，`usable_from_date` = trade_date 后一个交易日）与 `data/etf_rotation_v1/nav/`（14 只，`unit_nav`/`accum_nav`/`adj_nav`，`ann_date` 14/14 非空，`usable_from_date` = ann_date 后一个交易日）。PIT 校验：首次拉取有 56 行 NaT（本地交易日历止于 2026-09-17，最后 1–2 天算不出下一交易日），已改为回退到下一个工作日；复核后 usable ≤ 源日期或 NaT 的行数 = 0。
- Tushare `fund_share` 单次上限 2000 行：518880/512400/513100 从 2018-07 起，覆盖 2021+ 研究窗。
- 日更：Dagu `etf_pi_fund_data_daily`（工作日 19:00），脚本 `pi_glm_mining/audit/update_etf_fund_share_nav.py`，整表幂等覆盖。
- 标的指数三张表按前文判断不拉。
