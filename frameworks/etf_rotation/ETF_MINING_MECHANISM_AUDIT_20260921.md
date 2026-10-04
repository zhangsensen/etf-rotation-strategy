# ETF 单因子挖掘机制审计（2026-09-21 15:10）

USER 指令："先去审核因子挖掘机制有没有问题。" 审的是机制（候选生成 → 门 → 去重 → 裁判 → 时序 → 复现 → 主控），不是结果。证据来自引擎源码（两线副本一致的裁判/门/去重段）、5065 条历史候选的裁判数字、六代表的重算。独立审阅者（Sonnet，只读）结论附 §9。

## 0. 一句话
机制没有前视，但**门 7 的审计半边几乎不筛、H10/H20 的 t 被 block-5 系统性高估 30–45%、发现窗人口中位数只有 3 只、方向在发现期拟合后没有任何多重检验扣减**——四件事叠加，使"过门"约等于"发现期 t≥2"，而发现期 t≥2 在 5065 条里有 24.7% 达到。这解释了为什么审计期看着漂亮的候选到干净面上归零或反向。

## 1. 时序与标签（无问题）
- 信号用 ≤D；标签 open(D+2+H)/open(D+2)−1（`_raw_forward`，唯一负 shift）；泄漏硬门（截断副本重算、掩码一致、静态扫描）每轮跑。
- 合格性 = 已观测 ≥120 日 + 当日 OHLCV 齐 + 量>0，不含未来存在性（`build_pit_eligibility`）。
- 结论：**未发现前视**。今日两线复现逐 bp 一致（QA8）支持这一点。

## 2. 人口与样本（主要问题 A）
- 14 只 ETF 上市时间错开：合格名字/日在发现窗（≤2023-12-31）**中位数 3、75% 分位 ≤13、最大 13**；≥8 只（MIN_PAIRS）始于 2021-08-09，14 只齐全始于 2024-01-19。
- 因此"发现期"实际只有 2021-08→2023-12 约 580 日、8–13 只；top-3 在 8 只里 = 37.5% 基线命中率。"2021/22/23 三年同向"里 2021 只有 5 个月。
- 审计窗 320 日 → block-5 只有 64 块。
- 后果：发现 t 的分母极小，任何 t 门都在噪声区；年度方向门形同虚设。

## 3. 门 7 裁判（主要问题 B、C）
**B. 审计半边几乎不筛。** 门是"发现 block-t ≥2 **且** 审计超额 ≥5bp"，审计侧没有 t 要求。5065 条历史候选：审计 ≥5bp 的占 **56.1%**；发现 t<0 的候选里也有 **43.0%** 审计 ≥5bp；发现 t≥2 的候选里 74.3% 过审计。审计中位数 +8bp（方向按发现期拟合后整体右偏）。**审计门的筛选力接近抛硬币。**

**C. block=5 对所有视界。** H10/H20 的日频超额是重叠收益，5 日块消不掉自相关。六代表审计窗实测（block=5 → block=H）：QA8 H20 3.89→2.71，S27B5 6.15→4.34，CO36 5.12→3.32，PA1 4.72→2.98，CK04 1.40→0.99。**H20 t 高估 30–45%**；"H=20 系统性强于 H=5"的口径待决项有一半是这个 artifact（S64 的 5.84 折算约 4）。

**D. 方向拟合 + 无多重检验。** 方向取发现期符号，等于单边检验；每阶段 15–30 条、一个左腿配 ≤8 右腿、下一阶段按上一阶段结果自适应生成。发现 t≥2 达成率 24.7%（5065 条），Bonferroni 门 2.64 只写在报告里不在门里。**"过门"的含义 ≈ "在被拟合方向上发现期 t≥2"。**

## 4. 其他门（近乎空转）
- |IC| ≥0.01、审计 IC 同向 ≥0.01、三视界同向、年度同向 ≥2/3、identity 门：拒绝主要来自 topk_gate 与 identity_gate；IC 门 0.01 在 14 只上无意义。
- 精确度 P@3 只报不判。

## 5. 去重（设计与合同不一致，已部分修）
- 固定预注册顺序、先入选者留（`_dedup_pass`），合同写"簇内审计最高者留"——今日已用登记脚本补。
- 参照集此前无基础收益/价格位置/beta 控制——E30 一日收益影子因此过门；今日已加 RET1/RET20 参照，价格位置/beta 未加。
- 门 0.70 对配对偏松（单原子影子 0.98 → 配对稀释到 0.62 过门）。
- 作废候选此前仍作参照（已修）。

## 6. 候选生成（结构性问题 E）
- rank(A) − rank(B) 把任意两个弱信号拼成新候选；去重只查与在册相关，不查"配对相对 A、B 各自的增量"。第 11 阶段做过一次单腿增量复核后未常规化。beta 簇已证信息在右腿，左腿换来换去都过。
- 配对纪律限制了数量（≤8 右腿/左腿、≤3 左腿/右腿），但不限制信息重复。
- 家族构造由 agent 自拟 + 主控文字指令，文字到代码的歧义今日三次（换手率分母、"日值"两读、复现口径）。

## 7. 复现与两线（必要非充分）
- 两线独立实现能排实现错误（QA8 逐 bp、E30 两线同错说明规格错误它排不掉）。
- "跨实现成立"此前只要求发现期两线 ≥2 + 审计同向，审计 t 未要求两线都 ≥2。
- 第 61 阶段 0.03 相关 → 61b 成立，说明复现结论高度依赖规格到代码级。

## 8. 主控层
- 审计窗被用于换代表、定窗口、排阶段、判方向 → 不再是样本外（North Star 审核已指出）。
- 生产指标（轮数、入选数、队列）替代研究指标。
- 三次规格歧义、一次"低相关=新信息"误推。

## 9. 独立审阅者结论（Sonnet，只读，与主控独立）
审阅者读了引擎、裁判、语法、identity、一个 split 家族及其助手、canonical_data。九条，与主控对照：
1. **[严重，bug] 门 7 top-3 的并列打破按列顺序**：`sig.rank(method="first")`，信号是 14 只百分位秩的差/积，并列很常见，并列时按 universe JSON 里的列顺序选入 top-3。主控实测六代表（≥8 只的日子）：**配对类候选 12–28% 的日子 top-3 边界并列**（S27B5 22%、CO36 26%、CR08 28%、CK04 12%），单原子 QA8/PA1 ≈0%。并列日与非并列日的超额在这六条上没有系统差异（27–30 vs 23–27bp），所以未见方向性偏差，但**结果依赖 JSON 排序、不可作为统计量**，且 P@3 被污染。主控此前未发现——新增为问题 I。
2. [主要] 审计门无 t——与主控 B 一致，审阅者独立得出。
3. [主要] IC 门 0.01 近乎空转，且方向 = sign(发现 IC) 使发现侧 IC 门接近同义反复——与主控 §4/D 一致，补充了"同义反复"这一点。
4. [主要] 去重按作者写入顺序——与主控 §5 一致。
5. [主要] 无多重检验校正，且报告里的 Bonferroni 计数只数 `cond_` 算子、不数 `rank_interaction`——比主控 D 更具体：连"只报不改门"的那个数都数漏了。
6. [主要，已知局限] 14 只人口用今天的知识选定（分类复核日 2026-09-18，要求数据到 as_of），是人口层幸存者偏差——主控 §2 只写了人口小，没写这一层；补为问题 J。
7. [次要，bug] `_rolling_sign_split_diff` 有两份不等价副本（组内最少 5 日 vs 1 日），家族按"复用"引用其一——与主控今日的"日值/同窗/组内天数"歧义同源。
8. [次要] 作废候选的原轮 STATUS 仍是 gate_pass=true——主控已知，作废只在 CONTROLLER_VOID.json。
9. **确认无前视**：标签隔离、split 窗口只到当前行、PIT 合格性、方向与去重只用发现窗、泄漏门"异常严格"——与主控 §1 一致。
审阅者总评：反泄漏工程是系统最强的部分；弱点全在显著性侧（并列 bug、审计/IC 门无离散度控制、多重检验未校正、去重按顺序），"过门候选的假发现率很可能远高于单条门槛暗示的水平"。**主控综合：一致 8 条；分歧 0；新增 I（并列 bug）、J（人口幸存者）两条进处置表。**

## 10. 判定与建议（按严重度）
| # | 问题 | 性质 | 影响 | 处置建议 |
|---|---|---|---|---|
| A | 发现窗人口中位数 3 只、有效发现期 2.4 年 | 数据/设计 | 所有发现 t 的分母 | 明确发现窗 = 2021-08 起；14 只齐全前的年度方向门去掉或改为"有效年" |
| B | 审计门只有 ≥5bp、无 t | 设计缺陷 | 过门 ≈ 发现期过门 | 审计侧加 block-t ≥2（或至少 ≥1.5）；历史 320 条名义入选按此重判 |
| C | block=5 用于 H10/H20 | 统计错误 | H20 t 高估 30–45%，口径待决项失真 | block = max(5, H)；H20 口径讨论先重算 |
| D | 方向拟合 + 无多重检验 | 设计缺陷 | 24.7% 候选过发现门 | 门 t 按每阶段 N 做 Bonferroni/BH；或发现期用一半拟合方向、另一半判 t |
| E | 配对无单腿增量检验 | 设计缺陷 | 右腿驱动的伪新候选 | 配对必须优于两腿各自（同 D 口径）才入选 |
| F | 去重无基础控制（部分已修） | 设计缺陷 | 收益/价格位置影子 | 加 PRICE_POSITION、beta 参照；配对影子门降到 0.6 或按单原子判 |
| G | 审计窗被主控反复使用 | 流程 | 无独立样本外 | 冻结 + 一次性干净面（已做）；今后审计窗只看一次 |
| H | 规格到代码歧义 | 流程 | 复现失效、假发现 | 指令写到分母/窗口/日值级；主控自算一遍量级 |
| I | top-3 并列按 JSON 列顺序打破（配对类 12–28% 的日子） | **bug** | 裁判统计量依赖列顺序，P@3 失真 | 并列按 `average` 取分数或并列名等权分摊；历史门 7 数字须重算 |
| J | 14 只人口按今日知识选定 | 人口幸存者 | alpha 只在这 14 只上成立 | 交付表明写；任何外推需重选人口 |

B、C、D、I 是引擎改动，需 USER 批准；A 是口径声明；E、F 可在包装层做；G、H 是流程。

**这套机制在修 B/C/D/I 之前，不应再用于产出任何"入选"；修完后历史 320 条名义入选须按新门重判一次（不重挖）。**

## 11. 修复执行（2026-09-21 15:50，USER："开始修，按 I → C → D → B"）
两线引擎副本 `pi_round002_mine.py` 同步改，`REFEREE_VERSION = v3_20260921`；`controller_verify.py` 同步改 top-K 权重。
- **I** `_topk_weights`：边界并列名分摊剩余权重，权重和 = K；引擎与验证器同一实现。
- **C** `_block_t(block = max(PRIMARY, H))`（裁判视界 H5 → 块 5，不变）；新增 `_hac_t`（Newey–West，滞后 H−1）并列报告 `topk_t_hac_disc/audit`。H10/H20 的块长修正落在使用这些视界的工具（`run_once`、h_backfill、基线脚本）——尚未改，其 H20 数字仍高估。
- **D** 方向 = 预注册 `expected_sign`（`_evaluate_one(preregistered_direction)`），发现期符号另存 `discovery_direction`；发现 IC 门改为带方向的 `signed_discovery_ic`；轮内 Holm（α 0.05，单侧 p 来自发现 block-t，全部预注册候选计数）加入门 `holm_round`。
- **B** 门 7 新增 `topk_t_block_audit ≥ 2.0`。
- **测试（`audit/referee_selftest.py`，Sonnet 工作区 round_673 的 16 条）**：T1 列顺序扰动 max|diff| 3.6e−15 → 通过；T2 随机标签（前向收益时间循环移位，192 候选-抽样）门 7 通过率 0.0%、Holm 通过率 0.0% → 通过；T3 注入信号（前向秩 + 噪声）发现 t 15.6、审计 t 12.4、过门 → 通过；T4 round_673 在 v3 下：原 3 条入选（含 PERMENT_TURNOVER_SPLIT × beta 发现 4.16）**审计 t 0.30–1.47，全部不过门**；Holm 过 3 条（发现 t 3.67–4.16）。
- 未做（下一步）：E 单腿增量门、F PRICE_POSITION/beta 参照；随后重判 320 条名义入选（清库存，不认证）。
- **E/F 已加（16:05）**：F 去重参照新增 `base:PRICE_POS_20 / PRICE_POS_250 / BETA_60`（60 日对 14 只等权篮子 beta），round_673 六原子实测与五个基础参照 corr ≤0.16；E `leg_increment` 门——配对发现 block-t 必须高于两腿各自（各取较优方向）的 t，round_673 六条配对实测：UWCHG × beta 2.47 < 右腿 beta 单独 2.79 → 不过；PERMENT × beta 4.16 > 2.79 → 过；LUNCHPR × GAP_DD 3.67 > 1.98 → 过。CONTINUOUS_BETA_60 单原子发现 t 2.79，是 beta 配对簇"信息在右腿"的直接量化。

## 12. v3.1（2026-09-21 16:40）— 回应"引擎 BLOCKED"清单
| 项 | 状态 | 实现 |
|---|---|---|
| v3 未进源码入口 | 已改 | `round_drivers/pi_round002_mine.py` 与 `round_drivers/sonnet/` 与两线工作区副本同步（v3.1） |
| C：HAC 未进门 | 已改 | 门 7 同时要求 block-t 与 HAC-t（发现 ≥2、审计 ≥2）；H10/H20 只在引擎 IC 里出现，无 top-K 门；使用 H10/H20 top-K 的外部脚本（`run_once.py`、基线脚本）块长仍为 5，其 H20 t 标"高估 30–45%"不改数 |
| D：轮内 Holm 未控跨轮 | 已改 | 新增 `bonferroni_cumulative`：单侧 p ≤ α / N_cum，N_cum = 该线全部 PLAN 预注册候选数；Sonnet 线 N_cum 3081 → 发现 t 门等价 **4.16**；pi 线 2143 → 约 4.0 |
| E：只比 t 不比收益差 | 已改 | 配对日超额序列 − 最优单腿日超额序列，发现窗 block-t ≥1.5 且均值 >0。round_673 六条配对实测：PERMENT × beta 差 +1.2bp t 0.09、LUNCHPR × GAP_DD +6.3bp t 0.59、ULCER_NOISERATIO × beta +3.5bp t 0.30，其余为负——**六条全部不过**，配对相对最优单腿无增量 |
| 历史重建 IC 不一致 | 已定因 | 146 条（不是 73），全部在 pi/Sonnet 共同继承的 round_018–034（09-19 21:00→09-20 夜）。两个原因：① 数据根 sha 变了（then `ff8477a9…` → now `94153da5…`，E23 恢复 + 日更）；② 家族 Python（`etf_mined_families.py`，09-20 13:39 修改）未被快照，快照只有 yaml 与驱动脚本。**这 30 轮的入选不可重判，标 NON_REPRODUCIBLE**；引擎已加 `family_py:*` 与 `referee_version` 进 snapshot_hashes |
| 重判扫描 | 作废 | 16:15 的扫描用的是 v3（无 HAC 门、无累计 Bonferroni、E 为 t 比较、void 路径错）；结果只作参考，不作定案 |

自检 T1–T3 在 v3.1 下通过（并列扰动 3.6e−15；随机标签门 7 与 Holm 通过率 0.0%；注入信号过门）。

**当前判定：引擎 v3.1 可用于重判。重判范围 = round_035 起（可重建的轮）；round_018–034 标 NON_REPRODUCIBLE。**

## 13. v4 源码修复（2026-09-21 17:20）

v3.1 判定由本节替代。

| 项 | v4 实现 | 门 |
|---|---|---|
| I 并列 | 信号 top-K、真实收益 top-K 均用边界并列分摊 | 列顺序不进入权重 |
| C 重叠收益 | block 长度 = H；HAC lag = H−1 | 发现、审计同时要求 block t 与 HAC t |
| D 方向与多检验 | 方向只取 `expected_sign`；发现符号只报告；固定 6000 假设 Bonferroni | 单边 p ≤ 0.05/6000 |
| B 审计 | 审计超额、block t、HAC t | ≥5bp、≥2、≥2 |
| E 单腿增量 | 候选超额减每条腿的最优方向超额，使用配对日序列 | 两腿均需发现 HAC t≥2、审计 HAC t≥1.5、审计均值>0 |
| F 影子 | RET1、RET20、PRICE_POS_20、PRICE_POS_250、BETA_60 | 配对候选基础影子相关 <0.60；其他候选 <0.70 |
| 复现 | 每轮复制 `src/etf_strategy` Python 源码和哈希 | 缺少快照或重建 IC 误差>1e−10，重判停止 |

源码：`src/etf_strategy/core/etf_mining_referee.py`。两线入口：`round_drivers/pi_round002_mine.py`、`round_drivers/sonnet/pi_round002_mine.py`。历史重判：`audit/rejudge_referee_v4.py`。

测试：ETF 测试集 367 通过、3 跳过、0 失败。两条冻结工作区已同步 v4；家族注册加载数 pi=104、Sonnet=120。round_020 烟测：6 个候选，快照一致性失败 6 个，v4 通过 0；程序退出码 2。该轮没有家族 Python 快照，不能给出重判结论。历史重判必须先按轮恢复原家族源码；不能用当前家族源码代替。

## 13. v3.1 重判结果（2026-09-21 17:05，`runtime_outputs/etf_rejudge_v31_20260921/`，只清库存不认证）
| 线 | 重判候选 | 可重建 | 原入选（可重建） | v3.1 通过 |
|---|---|---|---|---|
| pi | 2135 | 2053 | 118 | **1**（CA1 `PV_ELASTICITY_20`，round_080：发现 t 4.00 / HAC 3.83，审计 +52.3 t 2.75，N_cum 667） |
| Sonnet | 3074 | 2989 | 209 | **0** |

原入选被各门剔除的条数（可重建的 118 / 209）：审计 t<2：105 / 182；HAC 审计 <2：103 / 181；累计 Bonferroni：116 / 204；单腿增量（配对差）：98 / 182；轮内 Holm：92 / 154；预注册方向与发现方向相反：58 / 83；HAC 发现 <2：61 / 86。
不计累计 Bonferroni 时通过：pi 7（CA1、DA24、DA28、DA41、DA42、DA57、VTR2）、Sonnet 8（NI1、PA1、PA2、PA3、CA3、S26RA2、S32P11、S62A1）；DA41 = PA1 同原子。
**结论：按修复后的裁判，两天挖掘在可重建范围内剩 1 条，未跨实现、未上干净面；不计跨轮搜索规模剩约 12 个独立候选，全部审计 t 2.0–2.8。** 与干净面结果（主表 6 条 H5 全未过）一致。

## 14. 唯一幸存者 CA1 干净面检验（2026-09-21 17:30，`runtime_outputs/etf_ca1_clean_eval_20260921/`）
预登记：PV_ELASTICITY_20，方向 −1（round_080 预注册），面 2025-05-01→2026-09-17（该候选从未在此面评估：不在第 56 阶段清单、不在 F1–F5、前向账本未产出），门 H5 block-t ≥2 且 HAC ≥2 且 ≥5bp，块长 max(5,H)，裁判 v4 共享模块。预检复现发现 t 4.00 / 审计 +52.3 t 2.75。
结果：H5 **−24.0bp t −1.42**（HAC −1.53，331 日）；H10 −48.0 t −1.39；H20 −122.5 t −1.80。2025-05→12 −38.5bp，2026 −9.5bp。**FAIL_H5，三视界反向。** 面已用。
**两天挖掘经修复后裁判 + 干净面：可用因子 0 条。**
附：17:00–17:08 另一会话把引擎升到 v4（共享 `etf_mining_referee.py`：fractional_topk_weights / topk_series / block_t / newey_west_t / holm / campaign_bonferroni / paired_increment_stats；跨线假设预算 6000；配对增量门发现 t≥2、审计 t≥1.5；配对影子门 0.60）。referee_selftest T1–T3 在 v4 下通过，round_673 数字与 v3.1 逐位一致。v4 驱动与模块在工作区与源码入口均未提交（属该会话）。

## 15. 剩余四项修复（2026-09-21 18:10，USER："把剩下 4 项修完"）
| 项 | 实现 | 验证 |
|---|---|---|
| A 发现窗人口 | `DISCOVERY_START` 由数据推出 = 首个合格名字 ≥ MIN_PAIRS(8) 的交易日（当前面板 **2021-08-09**）；发现期 IC、门 7 发现序列、中位配对数全部切 `[DISCOVERY_START, DISCOVERY_END]`；年度方向门只计有效 IC 日 ≥120 的年份（2021 只有 5 个月，不投票），新增 `year_direction_eligible`、`ic_{year}_days`；STATUS 写 `discovery_start/discovery_end` | `_load_context` 实测 DISCOVERY_START = 2021-08-09 |
| C 外部工具 | `controller_verify.py` 新增 `k3_audit_h10/h20_{bp,t}_blockH`（块长 = max(5,H)，共享 `fractional_topk_weights`）；一次性脚本（`run_once.py`、基线脚本）不改，其 H20 数字在 §3 标"高估 30–45%" | 编译通过；下次验证轮自动带出 |
| helper 重复 | 新模块 `families/split_helpers.py`（`rolling_median_split_diff` / `rolling_sign_split_diff`，`min_group` 显式参数）；v3 / v4 / overnight 三个家族的原函数改为包装，保留各自历史 min_group（1 / 1 / 5），数字不变；pi 工作区无这三份 | 随机序列对照：wrapper vs 原实现 max|diff| 0，NaN 模式一致 |
| STATUS 不可变 | `audit/apply_void_overlay.py` 在每个作废轮目录写 `STATUS_OVERLAY.json`（逐 id gate_pass=False + 原因），STATUS.json 不动；selftest 新增 `void_overlay` 检查 | pi 2 轮、Sonnet 4 轮已写；selftest 通过 |
referee_selftest T1–T3 在此版本通过；controller_selftest 仅剩 4 项"队列 0 / STOP"——线按 USER 决定停着，属预期。
源码入口 `round_drivers/{,sonnet/}pi_round002_mine.py` 与两线工作区同步（含另一会话的 v4 核心 + 本会话 A/helper/overlay 补丁）。引擎 v4 依赖 `src/etf_strategy/core/etf_mining_referee.py`（另一会话新建，未提交）——随本提交入库，否则入口无法导入。

**引擎问题清单结算：已修 12，不可修 2（J 人口幸存者、G 审计窗已用——只能靠前向新数据）。**

## 16. v4 复核补丁（2026-09-21 18:00）

| 问题 | 修复 | 判定 |
|---|---|---|
| PLAN 只有存在检查，内容可在结果计算前后改写 | `PLAN.sha256` 在 wrapper 的 plan hook 返回后生成；evaluate 先验 seal | 篡改后拒绝 |
| evaluate 不核验计划时的数据、配置、源码、货架 | PLAN 写入 base/driver/Python 树、配置、输入内容、shelf 哈希；evaluate 全量重算核对 | 任一变化拒绝 |
| atom/leak 缓存未绑定家族 Python，数据键只用 size/mtime | 缓存键加入 Python 树哈希；数据键改用 PLAN 输入内容哈希 | 旧缓存失效 |
| 历史入选信号用当前家族代码重建 | v4 每轮保存 `admitted_rank_vectors.parquet` 及哈希；去重只读冻结向量 | v1–v3 STATUS 不进入 v4 引用 |
| 两线计划查重在锁外 | 跨线表达式哈希查重与 6000 条预算进入同一 `flock` | 并发重复计划拒绝 |
| 发现窗改为 2021-08-09 后，去重仍含早期不足 8 只 ETF 的日期 | rank 向量窗口改为 `[DISCOVERY_START, DISCOVERY_END]` | 去重口径与发现门一致 |
| STOP 只停调度器，手工 `plan` 可继续 | `cmd_plan` 检查线根 `STOP` | 当前两线 plan 拒绝 |
| STATUS 的 PASS 可能被解释为因子认证 | STATUS 写 `certified_factor=false`、`promotion_allowed=false`、`external_validity=false` | PASS 只表示 discovery lead |

验证：ETF 测试 **369 passed / 3 skipped / 0 failed**。真实候选 pi round_213 NS67A 走当前数据→原子→表达式→泄漏门→v4 裁判→单腿增量→去重链：泄漏门通过；最终拒绝，失败项 `campaign_bonferroni, leg_increment, topk_gate`。

剩余证据边界：① 5219 条历史假设按前轮结果在同一发现/审计面自适应生成，固定预算 Bonferroni不能把这批 p 值变成确认性证据；② 14 只 ETF 人口按当前知识选择，未控制人口幸存者；③ 2024-01→2025-04 审计面已被反复使用。三项不能靠重算修复。当前可认证因子 **0**；新认证只允许前向新数据。

历史 `*_profile.py`、`*_h_backfill.py`、`topk_referee_admitted.py` 中的 `method="first"` 或固定 5 日块结果保留为历史诊断，不进入 v4 证据链。

## 16. v4 引擎重判（2026-09-21 18:40，`rejudge_v4.py`，镜像 cmd_evaluate 门线：预注册方向、门 7 含审计 t/HAC/跨线预算 6000、两腿配对增量、identity、基础参照 <0.7、作废、可重建）
| 线 | 可评估 | 可重建 | 原入选 | v4 通过 |
|---|---|---|---|---|
| pi | 1860 | 1782 | 117 | **0** |
| Sonnet | 2822 | 2741 | 208 | **0** |
未评估 283 / 259 条：271 / 250 条无预注册 expected_sign（早期轮，v4 要求 ±1）、5 条 cond_ 算子不支持、6 条方向非 ±1；其中原入选 0 条，不影响计数。
原入选被剔（可重建、未作废）：campaign_bonferroni 105 / 193；topk_gate 105 / 194；leg_increment 95 / 180；year_direction 57 / 85（2021 不再投票后）；identity 53 / 80。v3.1 唯一幸存者 CA1 在 v4 下发现 HAC t 3.83 < 跨线预算门 4.2，campaign 不过。
"只差 campaign Bonferroni"的候选：0。
**结论：v4 引擎下历史入选剩 0 条。**

## 17. Codex 交叉审核结论与分工（2026-09-21 19:00，USER："你只做验收，引擎让 Codex 修"）
Codex 审核裁决 NEEDS_REWRITE。主控采纳的阻断项：
1. **裁判选股集合用未来标签可得性**：`topk_series` 先 `score.notna() & forward.notna()` 再选 top-3，D 日高分票若未来 exit 缺失被事后剔除、递补第 4 名；发现窗实测 4 个票日触发（含 2022-01-04、2022-01-11 的 513100.SH）。这是前视，推翻 §1"未发现前视"。
2. **窗口末端未按退出日 purge**：发现窗末 H5 用到 2024-01-10 价格、H20 到 2024-01-31；审计窗末 H5 到 2025-05-14、H20 到 2025-06-05。→ **今日全部"干净面"结论（§14 CA1、六代表 2026 段、F1–F4 边际检验）在标签层受污染，作废待重算。**
3. 泄漏检查缓存不区分正式/截断/扰动数据（`_build_atoms` 缓存键），差值可能恒为 0 → 泄漏门有效性待证。
4. identity 门用 legacy LOSO（日期选择偏差已知）；discovery 侧只要求同号。
5. referee_selftest：导入 Sonnet 驱动、随机标签只 12 个独立移位、T3 绕过泄漏门 → §11/§15 的"T1–T3 通过"不构成校准证据。
6. split helper 未统一：`split_math.py`（Codex）与 `split_helpers.py`（主控）并存，v7/v8/v9 用前者。
7. 历史入选须按轮冻结秩向量，不得用当前家族代码重建。
分歧：固定 6000 预算（Codex：保守且拒超；主控：数字非预注册，应进合同）；类别/AUM 参照（一致改标"机制归因风险"）。
**分工**：引擎 11 项修复由 Codex 执行（缓存隔离、PLAN 封印、运行合同哈希、缓存来源哈希、运行中变更保护、冻结秩向量、并发查重进锁、发现窗统一、STOP 下禁 plan、历史工具隔离、STATUS 写 certified_factor=false/promotion_allowed=false/external_validity=false）。主控只做验收，不再改引擎。验收项：ETF 全测 0 failure；PLAN 篡改后 evaluate 拒绝；两线并发同表达式只一个 PLAN 成功；截断/扰动分支未读正式缓存（重建数与最大差值）；pi round_213 NS67A 全链重跑（数据→原子→表达式→泄漏门→v4 裁判→单腿增量→去重）。两线不启动。

## 18. 主控接手引擎修复：v4.1 → v4.2（2026-09-21 19:30–20:40，USER："我改，Codex 只审"）
基线 `6f3d7d06`（Codex 桌面会话 18:08 前的 v4 未提交改动原样入库）。
**v4.1（`f02d40df`）**：选票集合只由 D 日 score 决定，标签缺失日整日丢弃不递补（`dropped_label_days`）；`purge_by_exit` 接入门 7 发现/审计、三视界 IC、identity 掩码、配对增量（offset = LAG+H）；block_t 只用整块；matched LOSO + identity 发现侧幅度门 0.01；原子缓存 pending → 期末合同重验后转正，失败不留缓存不写 STATUS；split_math 单实现（split_helpers 为 shim）；历史工具 `--historical` 门；6 条回归测试。
**Codex 只读审核 f02d40df → NEEDS_REWRITE**，采纳全部 7 项：年度门用了未 purge 的 IC（P0）；期末源码树哈希是缓存值（P0）；运行中 PLAN 篡改不在期末校验（P1）；controller_verify 不可执行且不同口径（P1）；泄漏缓存非两阶段、validate 不清理（P1）；块/HAC 按剩余观测数（P2）；`--historical` 进位置参数（P2）。Codex 关闭了我的担忧 (b)（matched LOSO 列名正确）、(a)（forward.where 不删整行）；确认"无未来成分选择，仍有 outcome-missingness 条件化"是正确表述。
**v4.2（`85f080f8`）**：年度门用 purged 序列；`_verify_run_end` 期末重读 PLAN、重验封印、比对 sha、`_python_tree_hash(refresh=True)`；泄漏缓存同走 pending；validate 丢弃 pending；`block_t_calendar` 按日历会话分块、块内缺一日即弃（HAC 仍按观测数，已标注）；controller_verify 重写为直接调用引擎裁判（同 purge、同块、H10/H20 按 H 会话块）；`--historical` 从 argv 剔除；+2 测试。
**验收（A1–A12）**：A1 全测 378 通过 0 失败；A2 封印篡改拒（测试）；A3 两进程同哈希 1 OK / 1 REJECT；A4 NS67A 四分支泄漏门全新缓存 cached 0 / computed 2、max|diff| 全 0（非缓存复用）；A5 NS67A 全链 v4.2：发现 +26.2bp block-t 2.53（日历块）/ HAC 2.85，审计 +38.8bp t 2.16 / HAC 2.25，标签缺失丢弃 9 日，identity 过，**不过跨线 Bonferroni 与两腿增量（左腿 HAC 1.66/1.71，右腿负）→ LEAD_ONLY**；A6/A7 测试覆盖；A8 去重向量切 `[DISCOVERY_START, DISCOVERY_END]`；A9 引擎 sha / 配置 sha / pre-v4 计划三种拒；A10 STATUS 三个 false 字段在写入路径；A11 STOP 下 plan 拒；A12 只剩 topk_referee_admitted（门控）与 17 个冻结的每轮驱动快照。自测：驱动 sha = 源码入口 sha；并列扰动 3.6e−15；60 次独立移位 960 候选-抽样门 7 通过 0.0%、Holm 0.5%；注入信号过门（功效测试，绕过泄漏门，已标注）。
**未做 / 已知**：HAC 滞后按观测数；标签缺失日丢弃的幸存日偏差未量化；发现窗 2021-08→2023-12 的功效上限不是引擎问题。两线仍 STOP。v4.2 送 Codex 第二轮审。
- **Codex 第二轮审核（85f080f8）→ 无新 P0；3 项 P1**：① 裁判语义变了但版本号未升——已改 `REFEREE_VERSION = v4.2_20260921`，v4/v4.1 入选不再作同版本参照；② 家族延迟导入使"改→导入→恢复"逃过期末哈希——已把 `load_builtin_families()` 移到期初合同校验之前；③ round_213 的 v4.2 数字是 replay 不是正式全链工件，且 controller_verify 未查封印/版本、比较字段不全——controller_verify 已加封印/PLAN sha/版本检查与全部决定字段（双 t、双 HAC、campaign、gate），旧裁判轮次输出 `REPLAY_ONLY`。分歧 3（A4 标准写反）已改。**USER 决定（20:55）：不跑正式全链 batch，接受 replay 证据；STOP 保留。** A5 标 REPLAY_ONLY；正式 v4.2 全链 STATUS 待线重开时自然产生。提交 `8e849a80`。

## 19. 收口（2026-09-21 21:40）
- Codex 第三轮对 `70200f19` 回 **ENGINE_REVIEW_CLOSED**。
- 之后主控补两项自知未决：① HAC 滞后改按交易日历（`newey_west_t_calendar`，缺口对不计入、γ_j = 可用会话对乘积和 / count；无缺口与原估计量相等，测试 <1e-9 与 <1e-12）；门 7 与配对增量统计改用；版本升 **v4.3_20260921**（Codex 第四轮两项 P1：权重公式、版本号，已按其指正改）。② 标签缺失日整日丢弃的偏差量化（pi 工作区，H5，全部合格 ≥8 只的会话）：发现窗 581 会话丢 4（0.7%，各缺 1 只：2021-10-13/20、2022-01-04/11），丢弃日 EW 5 日前向 +19bp vs 保留日 −17bp（4 个样本，不构成结论）；审计窗 320 会话丢 0；审计后 338 会话丢 7（2.1%），全部是 2026-09-09→17 最后 7 个会话、14 只全缺（标签尚未产生，属自然截尾）。**结论：outcome-missingness 条件化在本数据上影响 ≤0.7% 的发现会话，不构成系统性幸存日偏差；每轮 STATUS 的 `topk_dropped_label_days` 持续披露。**
- 自测 v4.3：驱动 sha = 源码入口；并列扰动 3.6e−15；960 随机化门 7 通过 0.0% / Holm 0.5%；注入信号过门。全测 380/0。
- 引擎清单结算：Codex 四轮共 14 项 + 主控自审 12 项，全部处理；仅剩 USER 决定不补的正式全链工件（REPLAY_ONLY）与两项不可修（人口幸存者、审计窗已用）。两线仍 STOP。

- **Codex 第四轮：ENGINE_REVIEW_CLOSED 61107bd8（2026-09-21 21:55）。引擎审核关闭。**
