# ETF IC 20 轮研究进度（2026-09-26）

固定口径：14 只 ETF、8 个经济组；D 收盘形成分数，D+2 复权开盘至 D+7 开盘的 H5 组间收益；每日完整八组 signed Rank IC。`cold_250_v1` 评价信号日为 2025-01-02 至 2026-03-13，退出不越过 2026-03-24。判定阈值、方向、人口、月度 v4 合同均未更改。所有结果是已见历史的发现证据，不是前向或实盘收益。

已完成 **10/20 轮、30 条正式定义**；另有 511880 成交活动草案因事前正方向没有足够经济依据被否决，未登记、未读 H5 标签、不计轮次。剩余 10 轮尚无冻结定义或运行许可。路线图和事前 SOX 机制见[提案](ETF_IC_CAMPAIGN20_PROPOSAL_20260926.md)。自第 4 轮起在独立分支 `etf/ic-campaign20-mining` 上串行执行。

| 轮次与机制 | 登记/有效 IC | 完整评价窗口的冻结方向结果 | 新增基础 IC 线索 |
|---|---:|---|---:|
| R01：美国 SOX 相对纳指 100 的上一已知行业冲击，三种 D−1 结束的历史暴露 | 3/3；各 287 日 | 见下表 | 0 |
| R02：美国 VIX 上一已知期权隐含风险冲击，三种 D−1 结束的历史暴露 | 3/3；各 286 日 | 见下表；滞后项冗余 | 0 |
| R03：美国大盘价值相对成长风格的上一已知冲击，三种 D−1 结束的历史暴露 | 3/3；各 287 日 | 见下表；滞后项冗余 | 0 |
| R04：国际现货黄金上一已知冲击，三种 D−1 结束的历史暴露 | 3/3；各 287 日 | 见下表 | 0 |
| R05：沪铜结算价同日冲击，三种 D−1 结束的历史暴露 | 3/3；各 286 日 | 见下表；同期项冗余 | 0 |
| R06：INE 原油结算价同日冲击，三种 D−1 结束的历史暴露 | 3/3；各 285 日 | 见下表 | 0 |
| R07：离岸人民币上一已知冲击，三种 D−1 结束的历史暴露 | 3/3；各 286 日 | 见下表；同期项冗余 | 0 |
| R08：恒生科技指数上一已知冲击，三种 D−1 结束的历史暴露 | 3/3；各 287 日 | 见下表；不对称项入反向观察 | 0 |
| R09：美国 10 年期实际利率上一已知冲击，三种 D−1 结束的历史暴露 | 3/3；各 260 日 | 见下表；同期项冗余 | 0 |
| R10：DCE 焦煤结算价同日冲击，三种 D−1 结束的历史暴露 | 3/3；各 284 日 | 见下表；滞后项达基础门 | **1** |

| R01 定义（方向均 `+1`） | signed IC | 日历 HAC(10) t | 5 日块 t | 2025 purge IC/n | 2026 冷线 IC/n | 结论 |
|---|---:|---:|---:|---:|---:|---|
| `sox_specific_same_day_response_60` | +0.041975 | +1.734 | +1.514 | +0.049532/236 | −0.038420/44 | 正 IC，但未达基础门；分年变号 |
| `sox_specific_delayed_response_60` | +0.016482 | +0.742 | +0.715 | −0.003362/236 | +0.091991/44 | 弱正 IC，未达基础门 |
| `sox_specific_sign_asymmetry_60` | +0.000463 | +0.011 | −0.029 | +0.004396/236 | +0.005411/44 | 近零 IC，未达基础门 |

每条完整评价日数为 287。2025/2026 purge 子窗口的有效日合计小于全窗，因为跨年标签被剔除。未用结果翻转方向或改窗口；没有因 IC 未过门而删去负面证据。因无新增基础线索，本轮没有启动个人账户策略映射；收益、成本和交易价值仍是独立问题。

冻结配置为 `frameworks/etf_rotation/configs/group_ic_campaign20_r01_sox_specific_20260926.yaml`，SHA256 `1d19c3b05d7e41e85a779433d531b768a5dfb004874c041d0eb7e44ad1bce775`；其中 `PROPOSED_NOT_APPROVED_NO_H5_LABELS_READ` 是冻结**前**状态，实际批准记录在本地 `runtime_outputs/etf_rotation_research/approvals/group_ic_campaign20_r01_sox_specific_20260926.json`，配置字节未在结果后改写。SOX 与 NDX 原始冷线文件 SHA256 分别为 `aefe68ce126f8eaeb2c13a2132d38f8305082ada3204054b60f21833859e372b` 和 `2e38516acc7da9fba531edae2aa82d1fd663254db71541bff828a6093fa68abc`。美国观测日期严格早于 A 股 D，最大旧度 4 个自然日；FRED 历史抓取非逐日归档，存在数据修订限制。来源是 [FRED SOX](https://fred.stlouisfed.org/series/NASDAQSOX) 和 [Nasdaq SOX 方法](https://indexes.nasdaq.com/docs/methodology_SOX.pdf)。

无标签预检位于本地 `runtime_outputs/etf_rotation_research/preflight_sox_specific_r01_frozen_20260926/`：三条各有 294 个完整八组分数日；与旧库存可比较的 1494 对中最近相关 0.526/0.537/0.506，本轮内部相关 0.360/0.517/0.345，均低于现有 0.7 冗余注记阈值；另有 9 份旧保存分数缺失。正式工件位于 `runtime_outputs/etf_rotation_research/runs/group_ic_campaign20_r01_sox_specific_20260926/`。独立脚本复算了 287 个逐日 IC、D+2/D+7 标签和日历 HAC；最大 IC 差为 `1.1e−16`，在 `independent_check.json` 留痕。它验证计算一致性，不使已见历史成为前向证据。

运行命令：

```bash
.venv/bin/python frameworks/etf_rotation/scripts/research/discover_etf_groups.py \
  --config frameworks/etf_rotation/configs/group_ic_campaign20_r01_sox_specific_20260926.yaml \
  --run-id group_ic_campaign20_r01_sox_specific_20260926 \
  --approval runtime_outputs/etf_rotation_research/approvals/group_ic_campaign20_r01_sox_specific_20260926.json
```

第 1 轮后本地累计库存 `runtime_outputs/etf_rotation_research/ic_inventory_20260926_536_r01/`：登记 536、已链接 536、未链接 0；语义索引 513，基础历史 IC 线索仍 16。主显示为正 IC 192、负 IC 115、近零 53、不可计算 153；旧筛选视图 HAS_IC 16、NO_IC 321、PENDING 176。登记数与语义索引差 23 是实现版本与语义定义的口径差，并非未对账记录。合并输入位于本地 `runtime_outputs/etf_rotation_research/sox_specific_merged_536/`。上述数据/账本/运行产物只留本地，不纳入代码提交。

第 2 轮的[VIX 风险预期提案](ETF_IC_CAMPAIGN20_R02_PROPOSAL_20260926.md)经 master 审阅后按冻结配置正式运行。三条各 286 个有效 IC 日（2025-01-02 至冷线可成熟日期），正方向结果如下；2025/2026 purge 分年有效日为 236/43，跨年标签不计任一分年。

| R02 定义（方向均 `+1`） | signed IC | 日历 HAC(10) t | 5 日块 t | 2025 purge IC/n | 2026 冷线 IC/n | 结论 |
|---|---:|---:|---:|---:|---:|---|
| `vix_risk_same_day_response_60` | +0.020989 | +0.879 | +0.694 | +0.002837/236 | +0.090808/43 | 弱正 IC，未达基础门 |
| `vix_risk_delayed_response_60` | −0.005942 | −0.274 | −0.031 | +0.009042/236 | −0.082503/43 | 近零负 IC，未达基础门；与旧纳指传导分数相关 0.727，标冗余 |
| `vix_risk_sign_asymmetry_60` | +0.019698 | +0.805 | +0.525 | +0.008436/236 | +0.078073/43 | 弱正 IC，未达基础门 |

无标签预检的完整八组分数日为 294/294/293；与此前 513 条索引定义有 1503 个可比较配对、9 份旧分数缺失。滞后项的 0.727 是冗余诊断，不曾用作丢弃其 IC 算术的门。正式工件在本地 `runtime_outputs/etf_rotation_research/runs/group_ic_campaign20_r02_vix_risk_20260926/`；独立脚本复算了各 286 个逐日 IC、D+2/D+7 标签和 HAC t，最大 IC 差 `1.1e−16`，见该目录的 `independent_check.json`。源文件是历史 FRED 快照，并非逐日版本认证。无新增基础 IC 线索，未启动策略映射。

运行命令：

```bash
.venv/bin/python frameworks/etf_rotation/scripts/research/discover_etf_groups.py \
  --config frameworks/etf_rotation/configs/group_ic_campaign20_r02_vix_risk_20260926.yaml \
  --run-id group_ic_campaign20_r02_vix_risk_20260926 \
  --approval runtime_outputs/etf_rotation_research/approvals/group_ic_campaign20_r02_vix_risk_20260926.json
```

第 2 轮后本地库存 `runtime_outputs/etf_rotation_research/ic_inventory_20260926_539_r02/`：登记 539、已链接 539、未链接 0；语义索引 516，基础历史 IC 线索仍 16。主显示正 IC 194、负 IC 115、近零 54、不可计算 153；旧筛选视图 HAS_IC 16、NO_IC 324、PENDING 176。登记与语义索引差仍为 23 个实现版本；合并输入 `runtime_outputs/etf_rotation_research/vix_risk_merged_539/`。

第 3 轮的[美国价值-成长风格提案](ETF_IC_CAMPAIGN20_R03_PROPOSAL_20260926.md)经 master 审阅放行后按冻结配置正式运行；审批记录在本地 `runtime_outputs/etf_rotation_research/approvals/group_ic_campaign20_r03_us_style_20260926.json`。三条各 287 个有效 IC 日（2025-01-02 至冷线可成熟日期），正方向结果如下；2025/2026 purge 分年有效日为 236/44，跨年标签不计任一分年。

| R03 定义（方向均 `+1`） | signed IC | 日历 HAC(10) t | 5 日块 t | 2025 purge IC/n | 2026 冷线 IC/n | 结论 |
|---|---:|---:|---:|---:|---:|---|
| `us_style_same_day_response_60` | −0.002400 | −0.107 | −0.207 | −0.004734/236 | −0.001623/44 | 近零 IC，未达基础门 |
| `us_style_delayed_response_60` | +0.000654 | +0.027 | −0.106 | +0.016533/236 | −0.066017/44 | 近零 IC，未达基础门；预检与旧 `us_lagged_transmission_60` 相关 0.740，标冗余 |
| `us_style_sign_asymmetry_60` | −0.023500 | −0.558 | −0.676 | −0.027267/236 | +0.047078/44 | 弱负 IC，未达基础门 |

无标签预检（本地 `runtime_outputs/etf_rotation_research/preflight_us_style_r03_draft_20260926/`）的完整八组分数日为 294/294/294；与此前 516 条索引定义有 1512 个可比较配对、9 份旧分数缺失；本轮内部三对相关 0.406/0.459/0.368。滞后项的 0.740 是冗余诊断，不曾用作丢弃其 IC 算术的门。正式工件在本地 `runtime_outputs/etf_rotation_research/runs/group_ic_campaign20_r03_us_style_20260926/`；独立脚本 `audit_us_style_r03_independent.py` 复算了各 287 个逐日 IC、D+2/D+7 标签和 HAC t，最大 IC 差 `1.1e−16`，见该目录的 `independent_check.json`。源文件是历史 FRED 快照（NQUSLV/NQUSLG，SHA 钉死、裁至冷线），并非逐日版本认证。无新增基础 IC 线索，未启动策略映射。

运行命令：

```bash
.venv/bin/python frameworks/etf_rotation/scripts/research/discover_etf_groups.py \
  --config frameworks/etf_rotation/configs/group_ic_campaign20_r03_us_style_20260926.yaml \
  --run-id group_ic_campaign20_r03_us_style_20260926 \
  --approval runtime_outputs/etf_rotation_research/approvals/group_ic_campaign20_r03_us_style_20260926.json
```

第 3 轮后本地库存 `runtime_outputs/etf_rotation_research/ic_inventory_20260926_542_r03/`：登记 542、已链接 542、未链接 0；语义索引 519，基础历史 IC 线索仍 16。主显示正 IC 194、负 IC 116、近零 56、不可计算 153；旧筛选视图 HAS_IC 16、NO_IC 327、PENDING 176。登记与语义索引差仍为 23 个实现版本；合并输入 `runtime_outputs/etf_rotation_research/us_style_merged_542/`。后续轮次不能以 R03 近零或弱负 IC 重新挑方向或窗口。

第 4 轮的[黄金现货提案](ETF_IC_CAMPAIGN20_R04_PROPOSAL_20260926.md)经 master 审阅放行后按冻结配置正式运行；审批记录在本地 `runtime_outputs/etf_rotation_research/approvals/group_ic_campaign20_r04_ext_gold_20260926.json`。数据为本地 FXCM 现货金快照（SHA 钉死、裁至冷线）。三条各 287 个有效 IC 日，正方向结果如下；2025/2026 purge 分年有效日为 236/44。

| R04 定义（方向均 `+1`） | signed IC | 日历 HAC(10) t | 5 日块 t | 2025 purge IC/n | 2026 冷线 IC/n | 结论 |
|---|---:|---:|---:|---:|---:|---|
| `gold_same_day_response_60` | −0.037833 | −1.577 | −1.795 | −0.049944/236 | +0.000541/44 | 弱负 IC，未达基础门 |
| `gold_delayed_response_60` | +0.000993 | +0.050 | −0.061 | −0.004947/236 | +0.024351/44 | 近零 IC，未达基础门 |
| `gold_sign_asymmetry_60` | +0.012323 | +0.355 | +0.229 | +0.006209/236 | +0.014069/44 | 弱正 IC，未达基础门 |

无标签预检（本地 `runtime_outputs/etf_rotation_research/preflight_ext_gold_r04_draft_20260926/`）的完整八组分数日为 294/294/294；与此前 519 条索引定义有 1521 个可比较配对、9 份旧分数缺失；最近旧定义最高 0.519，轮内三对相关 0.426/0.654/0.426，均低于 0.7 冗余注记阈值。正式工件在本地 `runtime_outputs/etf_rotation_research/runs/group_ic_campaign20_r04_ext_gold_20260926/`；独立脚本 `audit_ext_gold_r04_independent.py` 复算逐日 IC、D+2/D+7 标签和 HAC t，最大 IC 差 `1.1e−16`，见 `independent_check.json`。FXCM 快照非逐日版本认证。无新增基础 IC 线索，未启动策略映射。

运行命令：

```bash
.venv/bin/python frameworks/etf_rotation/scripts/research/discover_etf_groups.py \
  --config frameworks/etf_rotation/configs/group_ic_campaign20_r04_ext_gold_20260926.yaml \
  --run-id group_ic_campaign20_r04_ext_gold_20260926 \
  --approval runtime_outputs/etf_rotation_research/approvals/group_ic_campaign20_r04_ext_gold_20260926.json
```

第 4 轮后本地库存 `runtime_outputs/etf_rotation_research/ic_inventory_20260926_545_r04/`：登记 545、已链接 545、未链接 0；语义索引 522，基础历史 IC 线索仍 16。主显示正 IC 195、负 IC 117、近零 57、不可计算 153。合并输入 `runtime_outputs/etf_rotation_research/ext_gold_merged_545/`。后续轮次不能以 R04 结果重新挑方向或窗口。

第 5 轮的[沪铜提案](ETF_IC_CAMPAIGN20_R05_PROPOSAL_20260926.md)经 master 审阅放行后按冻结配置正式运行；审批记录在本地 `runtime_outputs/etf_rotation_research/approvals/group_ic_campaign20_r05_ext_copper_20260926.json`。数据为本地 SHFE 铜前连续期货结算价快照（SHA 钉死、裁至冷线）；D 日结算按冻结 close(D) 口径作同日信息使用，与 `domestic_benchmark` 同日收盘约定一致。三条各 286 个有效 IC 日，正方向结果如下；2025/2026 purge 分年有效日为 235/44。

| R05 定义（方向均 `+1`） | signed IC | 日历 HAC(10) t | 5 日块 t | 2025 purge IC/n | 2026 冷线 IC/n | 结论 |
|---|---:|---:|---:|---:|---:|---|
| `copper_same_day_response_60` | −0.014080 | −0.534 | −0.889 | −0.024734/235 | +0.000000/44 | 弱负 IC，未达基础门；预检与旧 `macro_r2_60` 相关 0.709，标冗余 |
| `copper_delayed_response_60` | +0.002605 | +0.096 | +0.262 | +0.022725/235 | −0.095779/44 | 近零 IC，未达基础门 |
| `copper_sign_asymmetry_60` | +0.010311 | +0.227 | +0.011 | −0.018252/235 | +0.112013/44 | 弱正 IC，未达基础门 |

无标签预检（本地 `runtime_outputs/etf_rotation_research/preflight_ext_copper_r05_draft_20260926/`）的完整八组分数日为 294/294/293；与此前 522 条索引定义有 1530 个可比较配对、9 份旧分数缺失；轮内三对相关 0.388/0.692/0.372。同期项的 0.709 是冗余诊断，不曾用作丢弃其 IC 算术的门。正式工件在本地 `runtime_outputs/etf_rotation_research/runs/group_ic_campaign20_r05_ext_copper_20260926/`；独立脚本 `audit_ext_copper_r05_independent.py` 复算逐日 IC、D+2/D+7 标签和 HAC t，最大 IC 差 `1.1e−16`，见 `independent_check.json`。期货结算快照非逐日版本认证。无新增基础 IC 线索，未启动策略映射。

运行命令：

```bash
.venv/bin/python frameworks/etf_rotation/scripts/research/discover_etf_groups.py \
  --config frameworks/etf_rotation/configs/group_ic_campaign20_r05_ext_copper_20260926.yaml \
  --run-id group_ic_campaign20_r05_ext_copper_20260926 \
  --approval runtime_outputs/etf_rotation_research/approvals/group_ic_campaign20_r05_ext_copper_20260926.json
```

第 5 轮后本地库存 `runtime_outputs/etf_rotation_research/ic_inventory_20260926_548_r05/`：登记 548、已链接 548、未链接 0；语义索引 525，基础历史 IC 线索仍 16。主显示正 IC 196、负 IC 118、近零 58、不可计算 153。合并输入 `runtime_outputs/etf_rotation_research/ext_copper_merged_548/`。后续轮次不能以 R05 结果重新挑方向或窗口。

第 6 轮的[INE 原油提案](ETF_IC_CAMPAIGN20_R06_PROPOSAL_20260926.md)经 master 审阅放行后按冻结配置正式运行；审批记录在本地 `runtime_outputs/etf_rotation_research/approvals/group_ic_campaign20_r06_ext_crude_20260926.json`。数据为本地 INE 原油前连续期货结算价快照（SHA 钉死、裁至冷线）；同日 close(D) 口径与 R05 一致。三条各 285 个有效 IC 日，正方向结果如下；2025/2026 purge 分年有效日为 234/44。

| R06 定义（方向均 `+1`） | signed IC | 日历 HAC(10) t | 5 日块 t | 2025 purge IC/n | 2026 冷线 IC/n | 结论 |
|---|---:|---:|---:|---:|---:|---|
| `crude_same_day_response_60` | +0.013728 | +0.635 | +0.498 | +0.000644/234 | +0.077381/44 | 弱正 IC，未达基础门 |
| `crude_delayed_response_60` | −0.005478 | −0.207 | −0.357 | +0.001671/234 | −0.079545/44 | 近零负 IC，未达基础门 |
| `crude_sign_asymmetry_60` | −0.004154 | −0.106 | −0.227 | −0.013301/234 | −0.062229/44 | 近零负 IC，未达基础门 |

无标签预检（本地 `runtime_outputs/etf_rotation_research/preflight_ext_crude_r06_draft_20260926/`）的完整八组分数日为 294/294/292；与此前 525 条索引定义的可比较配对中，唯一 ≥0.7 的是同期项对 `l64_post_outside_return_spread_20` 的 0.721，但仅 11 个共同日，作不稳定提示处理；最大稳妥样本相关为 `bond_trend_exposure_60` 0.486（n=292）。轮内三对相关 0.332/0.493/0.353。正式工件在本地 `runtime_outputs/etf_rotation_research/runs/group_ic_campaign20_r06_ext_crude_20260926/`；独立脚本 `audit_ext_crude_r06_independent.py` 复算逐日 IC、D+2/D+7 标签和 HAC t，最大 IC 差 `1.1e−16`，见 `independent_check.json`。期货结算快照非逐日版本认证。无新增基础 IC 线索，未启动策略映射。

运行命令：

```bash
.venv/bin/python frameworks/etf_rotation/scripts/research/discover_etf_groups.py \
  --config frameworks/etf_rotation/configs/group_ic_campaign20_r06_ext_crude_20260926.yaml \
  --run-id group_ic_campaign20_r06_ext_crude_20260926 \
  --approval runtime_outputs/etf_rotation_research/approvals/group_ic_campaign20_r06_ext_crude_20260926.json
```

第 6 轮后本地库存 `runtime_outputs/etf_rotation_research/ic_inventory_20260926_551_r06/`：登记 551、已链接 551、未链接 0；语义索引 528，基础历史 IC 线索仍 16。主显示正 IC 197、负 IC 118、近零 60、不可计算 153。合并输入 `runtime_outputs/etf_rotation_research/ext_crude_merged_551/`。后续轮次不能以 R06 结果重新挑方向或窗口。

第 7 轮的[离岸人民币提案](ETF_IC_CAMPAIGN20_R07_PROPOSAL_20260926.md)经 master 审阅放行后按冻结配置正式运行；审批记录在本地 `runtime_outputs/etf_rotation_research/approvals/group_ic_campaign20_r07_ext_cnh_20260926.json`。数据为本地 FXCM USDCNH 快照（SHA 钉死、裁至冷线）。三条各 286 个有效 IC 日，正方向结果如下；2025/2026 purge 分年有效日为 236/44。

| R07 定义（方向均 `+1`） | signed IC | 日历 HAC(10) t | 5 日块 t | 2025 purge IC/n | 2026 冷线 IC/n | 结论 |
|---|---:|---:|---:|---:|---:|---|
| `cnh_same_day_response_60` | +0.035408 | +1.403 | +1.208 | +0.032518/236 | +0.003247/44 | 正 IC，未达基础门（t<2）；预检与旧 `usd_beta_60` 相关 0.737，标冗余 |
| `cnh_delayed_response_60` | +0.009736 | +0.463 | +0.219 | +0.003425/236 | +0.002706/44 | 弱正 IC，未达基础门 |
| `cnh_sign_asymmetry_60` | +0.043107 | +1.178 | +1.015 | +0.035997/236 | +0.037338/44 | 正 IC，未达基础门（t<2），分年同号为 campaign 内最强弱证据 |

无标签预检（本地 `runtime_outputs/etf_rotation_research/preflight_ext_cnh_r07_draft_20260926/`）的完整八组分数日为 294/294/293；轮内三对相关 0.368/0.527/0.337。同期项的 0.737 是冗余诊断，不曾用作丢弃其 IC 算术的门。正式工件在本地 `runtime_outputs/etf_rotation_research/runs/group_ic_campaign20_r07_ext_cnh_20260926/`；独立脚本 `audit_ext_cnh_r07_independent.py` 复算逐日 IC、D+2/D+7 标签和 HAC t，最大 IC 差 `1.1e−16`，见 `independent_check.json`。FXCM 快照非逐日版本认证。无新增基础 IC 线索，未启动策略映射；不因接近门槛而放宽阈值或追跑窗口。

运行命令：

```bash
.venv/bin/python frameworks/etf_rotation/scripts/research/discover_etf_groups.py \
  --config frameworks/etf_rotation/configs/group_ic_campaign20_r07_ext_cnh_20260926.yaml \
  --run-id group_ic_campaign20_r07_ext_cnh_20260926 \
  --approval runtime_outputs/etf_rotation_research/approvals/group_ic_campaign20_r07_ext_cnh_20260926.json
```

第 7 轮后本地库存 `runtime_outputs/etf_rotation_research/ic_inventory_20260926_554_r07/`：登记 554、已链接 554、未链接 0；语义索引 531，基础历史 IC 线索仍 16。主显示正 IC 199、负 IC 118、近零 61、不可计算 153。合并输入 `runtime_outputs/etf_rotation_research/ext_cnh_merged_554/`。后续轮次不能以 R07 弱正 IC 重新挑方向或窗口。

第 8 轮的[恒生科技提案](ETF_IC_CAMPAIGN20_R08_PROPOSAL_20260926.md)经 master 审阅放行后按冻结配置正式运行；审批记录在本地 `runtime_outputs/etf_rotation_research/approvals/group_ic_campaign20_r08_ext_hktech_20260926.json`。数据为本地恒生科技指数快照（SHA 钉死、裁至冷线）；港历严格前置（16:00 港收晚于 A 股 15:00 收盘）。三条各 287 个有效 IC 日，正方向结果如下；2025/2026 purge 分年有效日为 236/44。

| R08 定义（方向均 `+1`） | signed IC | 日历 HAC(10) t | 5 日块 t | 2025 purge IC/n | 2026 冷线 IC/n | 结论 |
|---|---:|---:|---:|---:|---:|---|
| `hktech_same_day_response_60` | −0.013423 | −0.692 | −0.952 | −0.021772/236 | +0.013528/44 | 近零负 IC，未达基础门 |
| `hktech_delayed_response_60` | −0.014727 | −0.687 | −0.603 | +0.004084/236 | −0.125541/44 | 近零负 IC，未达基础门 |
| `hktech_sign_asymmetry_60` | −0.095643 | −2.866 | −3.273 | −0.087559/236 | −0.183983/44 | 显著负 IC，入反向观察（REVERSE_WATCH_NOT_VALIDATED），不翻向 |

无标签预检（本地 `runtime_outputs/etf_rotation_research/preflight_ext_hktech_r08_draft_20260926/`）的完整八组分数日为 294/294/294；最近旧定义最高 0.608（n=45 稀疏），稳妥样本最高 0.538（`lag1_beta_to_market_60`，n=294），均低于 0.7；轮内三对相关 0.333/0.578/0.358。正式工件在本地 `runtime_outputs/etf_rotation_research/runs/group_ic_campaign20_r08_ext_hktech_20260926/`；独立脚本 `audit_ext_hktech_r08_independent.py` 复算逐日 IC、D+2/D+7 标签和 HAC t，最大 IC 差 `1.1e−16`，见 `independent_check.json`。指数快照非逐日版本认证。`hktech_sign_asymmetry_60` 是 campaign 内首个显著负向结果：冻结 +1 方向下两年分年同负（−0.088/−0.184），按规则记入反向观察清单，不自动翻向、不改窗口；反向方向若立题须由已见负向结果显式提出并另登记。无新增基础 IC 线索，未启动策略映射。

运行命令：

```bash
.venv/bin/python frameworks/etf_rotation/scripts/research/discover_etf_groups.py \
  --config frameworks/etf_rotation/configs/group_ic_campaign20_r08_ext_hktech_20260926.yaml \
  --run-id group_ic_campaign20_r08_ext_hktech_20260926 \
  --approval runtime_outputs/etf_rotation_research/approvals/group_ic_campaign20_r08_ext_hktech_20260926.json
```

第 8 轮后本地库存 `runtime_outputs/etf_rotation_research/ic_inventory_20260926_557_r08/`：登记 557、已链接 557、未链接 0；语义索引 534，基础历史 IC 线索仍 16。主显示正 IC 199、负 IC 121、近零 61、不可计算 153。合并输入 `runtime_outputs/etf_rotation_research/ext_hktech_merged_557/`。后续轮次不能以 R08 结果重新挑方向或窗口。

第 9 轮的[美债实际利率提案](ETF_IC_CAMPAIGN20_R09_PROPOSAL_20260926.md)经 master 审阅放行后按冻结配置正式运行；审批记录在本地 `runtime_outputs/etf_rotation_research/approvals/group_ic_campaign20_r09_ext_realrate_20260926.json`。数据为本地美债 10 年期实际收益率快照（SHA 钉死、裁至冷线）；冲击为算术一阶差分（水平可负）。三条各 260 个有效 IC 日（294 个评价日中 7 日为未成熟尾部、27 日 y10 无变化 x_D=0 致八组分数为常数行、秩相关无定义，冻结引擎按无效处理，非事后剔除；n≥250 覆盖门通过），正方向结果如下；2025/2026 purge 分年有效日为 216/40。

| R09 定义（方向均 `+1`） | signed IC | 日历 HAC(10) t | 5 日块 t | 2025 purge IC/n | 2026 冷线 IC/n | 结论 |
|---|---:|---:|---:|---:|---:|---|
| `realrate_same_day_response_60` | −0.044723 | −1.773 | −1.998 | −0.028150/216 | −0.135714/40 | 弱负 IC，未达基础门；预检与旧 `real_rate_beta_60` 相关 0.860，标冗余 |
| `realrate_delayed_response_60` | −0.007930 | −0.302 | +0.433 | +0.004233/216 | −0.062500/40 | 近零负 IC，未达基础门 |
| `realrate_sign_asymmetry_60` | −0.046749 | −1.200 | −1.438 | −0.044919/216 | −0.022024/40 | 弱负 IC，未达基础门；分年同负 |

无标签预检（本地 `runtime_outputs/etf_rotation_research/preflight_ext_realrate_r09_draft_20260926/`）的完整八组分数日为 294/294/266（不对称项因利率趋势期符号分支不足少 28 日）；轮内三对相关 0.294/0.482/0.367。正式工件在本地 `runtime_outputs/etf_rotation_research/runs/group_ic_campaign20_r09_ext_realrate_20260926/`；独立脚本 `audit_ext_realrate_r09_independent.py` 复算逐日 IC、D+2/D+7 标签和 HAC t，最大 IC 差 `1.1e−16`，见 `independent_check.json`。实际收益率曲线快照非逐日版本认证。无新增基础 IC 线索，未启动策略映射。

运行命令：

```bash
.venv/bin/python frameworks/etf_rotation/scripts/research/discover_etf_groups.py \
  --config frameworks/etf_rotation/configs/group_ic_campaign20_r09_ext_realrate_20260926.yaml \
  --run-id group_ic_campaign20_r09_ext_realrate_20260926 \
  --approval runtime_outputs/etf_rotation_research/approvals/group_ic_campaign20_r09_ext_realrate_20260926.json
```

第 9 轮后本地库存 `runtime_outputs/etf_rotation_research/ic_inventory_20260926_560_r09/`：登记 560、已链接 560、未链接 0；语义索引 537，基础历史 IC 线索仍 16。主显示正 IC 199、负 IC 123、近零 62、不可计算 153。合并输入 `runtime_outputs/etf_rotation_research/ext_realrate_merged_560/`。后续轮次不能以 R09 结果重新挑方向或窗口。

第 10 轮的[焦煤燃料成本提案](ETF_IC_CAMPAIGN20_R10_PROPOSAL_20260926.md)经 master 审阅放行后按冻结配置正式运行；审批记录在本地 `runtime_outputs/etf_rotation_research/approvals/group_ic_campaign20_r10_ext_coal_20260926.json`。数据为本地 DCE 焦煤前连续期货结算价快照（SHA 钉死、裁至冷线）；同日 close(D) 口径与 R05/R06 一致；单腿成本冲击版，不主张 R15 煤-电双腿利润差机制。三条各 284 个有效 IC 日，正方向结果如下；2025/2026 purge 分年有效日为 233/44。

| R10 定义（方向均 `+1`） | signed IC | 日历 HAC(10) t | 5 日块 t | 2025 purge IC/n | 2026 冷线 IC/n | 结论 |
|---|---:|---:|---:|---:|---:|---|
| `coal_same_day_response_60` | −0.014838 | −0.478 | −0.604 | −0.025053/233 | +0.010224/44 | 近零负 IC，未达基础门 |
| `coal_delayed_response_60` | **+0.050269** | **+2.163** | **+2.121** | +0.045638/233 | +0.049242/44 | **基础 IC 线索**：覆盖、IC、HAC、块 t、分年同正、剔组全正（最小 +0.0317）均过 |
| `coal_sign_asymmetry_60` | +0.056597 | +1.512 | +1.015 | +0.058594/233 | +0.040615/44 | 正 IC，未达基础门（HAC/块 t<2） |

`coal_delayed_response_60` 是 campaign20 前十轮的首条新增基础历史 IC 线索（第 17 条累计）。剔任一组后 IC 均 >0（0.0317–0.0649），无单组主导；多重检验预算诊断（对 563 分母的单边 p）与 B8 经济收益未过，按冻结 IC-first 规则分栏报告、不作为保留门，也不因此宣称统计确认或可交易。无标签预检（本地 `runtime_outputs/etf_rotation_research/preflight_ext_coal_r10_draft_20260926/`）的完整八组分数日为 294/294/291；稳妥样本最高旧相关 0.561（`macro_r2_60`），轮内三对 0.364/0.443/0.360，均低于 0.7。正式工件在本地 `runtime_outputs/etf_rotation_research/runs/group_ic_campaign20_r10_ext_coal_20260926/`；独立脚本 `audit_ext_coal_r10_independent.py` 复算逐日 IC、D+2/D+7 标签和 HAC t，最大 IC 差 `1.1e−16`，见 `independent_check.json`。期货结算快照非逐日版本认证。本轮无策略映射；收益、成本与增量检验另行分栏。

运行命令：

```bash
.venv/bin/python frameworks/etf_rotation/scripts/research/discover_etf_groups.py \
  --config frameworks/etf_rotation/configs/group_ic_campaign20_r10_ext_coal_20260926.yaml \
  --run-id group_ic_campaign20_r10_ext_coal_20260926 \
  --approval runtime_outputs/etf_rotation_research/approvals/group_ic_campaign20_r10_ext_coal_20260926.json
```

第 10 轮后本地库存 `runtime_outputs/etf_rotation_research/ic_inventory_20260926_563_r10/`：登记 563、已链接 563、未链接 0；语义索引 540，基础历史 IC 线索 **17**（+1）。主显示正 IC 201、负 IC 124、近零 62、不可计算 153；旧筛选视图 HAS_IC 17。合并输入 `runtime_outputs/etf_rotation_research/ext_coal_merged_563/`。第 11–20 轮尚未启动；不能以 R10 结果重新挑方向、窗口或分组。
