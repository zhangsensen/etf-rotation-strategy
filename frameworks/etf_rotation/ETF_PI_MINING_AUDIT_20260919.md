# ETF pi/GLM 持续挖掘线 工程审计（2026-09-19）

审计对象：`runtime_outputs/etf_pi_glm_mining_20260919/`，Dagu DAG `etf_pi_glm_mining`，
pi RPC 常驻会话（zai/glm-5.3-flash，同一 session 连挖多批，65% 上下文才压缩）。
审计时点：2026-09-19 16:00–16:45，已完成 round_001～006。

## 〇、问题登记表（持续更新；状态：OPEN / FIXING / FIXED / RECORDED / WAITING_USER）

| ID | 问题 | 归属 | 状态 | 处置 |
|---|---|---|---|---|
| E01 | 前轮入选因子未接入去重，round_006 AssertionError | pi | FIXED 16:38 | 从不可变 PLAN 重建 + 校验哈希，未删断言 |
| E02 | 2000+ 行挖掘代码在 .gitignore 目录 | 本会话 | FIXED 0e83c65c | `scripts/research/pi_glm_mining/` 存档 |
| E03 | 基座跨轮变更，round_002 与后续不同尺子 | 本会话 | FIXED 16:55 | 隔离工作区用 `bea695d0` 重跑 R1–R8（同 expression_hashes、同 gates）：8 条发现/审计 IC 与原结果最大差 0.0e+00，拒绝原因逐条相同，0 过门。lead-lag bug 不影响 round_002（R1–R8 未用该家族），四轮结果可直接比较 |
| E04 | 静态泄漏扫描只扫薄驱动 | 本会话 | FIXED | 基座 + 6 驱动全扫，4 命中均已解释 |
| E05 | supervisor 无心跳 | 并发会话 | FIXED 16:49 | supervisor 已轮换（PID 3073532），`supervisor_heartbeat.json` 30 秒刷新，pi 同一会话恢复 |
| E06 | 无产出时 Dagu 空转 | Codex/并发会话 | FIXED 16:49 | `MECHANISM_EXHAUSTED.json` 干净退出 + precondition，新代码已在跑；round_007 普查按 `mechanism_census_not_exhaustion_permission` 记账，不当穷尽 |
| E07 | 每轮驱动未进快照 | pi | RECORDED | PLAN.json 固定候选，代码存档已覆盖 |
| E08 | `identity_gate` 借用 `min_abs_seen_audit_ic` | pi | FIXED（v2 引擎） | 拆为 `identity_min_abs_ic`，值不变 |
| E09 | 会话目录/checkpoint 命名脱节 | Codex | RECORDED | 无功能影响 |
| E10 | 14 只人口，IC 标准误 0.023 > 门槛 0.01，无显著性检验 | 研究口径 | SUPERSEDED→E12 | "扩人口"提议已撤回（USER：这是 14 只轮动，人口是给定输入）。正确解法是换裁判，见 E12 |
| E12 | 裁判与用途不匹配（截面 IC ≠ 轮动 top-3 收益） | 研究口径 | FIXED 17:48 | pi 已在引擎加第 7 道 top-3 门并重打 5 个入选（`outputs/referee_v2_rescore/`）：数值与我的独立裁判逐项一致（如 W1 +9.874 bp、N6 +23.11 bp），W1/W5/Z5/Y3 降为拒绝，仅 N6 过（审计 +0.37 bp）。17:50 追加 v2.1：审计期超额 ≥ 5 bp，下一轮起生效 |
| E13 | 主控无法不重启就改 pi 的指令；两次轮换（16:49、17:39）各丢一段在跑的回合 | 本会话 | FIXED 3bca8dcb | supervisor 每轮拼指令时追加 `CONTROLLER_DIRECTIVE.md`；以后改方向只改这个文件 |
| E14 | 产物一致性（不影响数值）：15 轮 REPORT 硬编码引用 round_002 的静态扫描文件；round_012/013 STATUS 缺 topk 字段（014 起已补，csv 齐全）；round_007 普查轮 leak_checks 写 pass=false 应为 N/A；穷尽文件 active_candidates 含 v2.1 未过的 N6、written_at 时间写错 | pi | RECORDED→指令 12 | 全库一致性脚本核过：17 轮 plan 哈希全对、账本与 STATUS 计数全对、泄漏门 16/16 实算轮全绿 |
| E15 | 指令漂移：第三阶段（条件化算子，指令 19–22）22:30 下达后，pi 在 round_025–027 仍只跑两原子价差（从 untested_pairs.csv 选对），未实现 cond 算子，round_028 再次未按"三轮零"提前宣布穷尽并"建议主控追加 19–22"；自动推进随即套上第四阶段。根因：指令文件是追加式历史，pi 取最近最具体的一条（25 条供给假设对）执行，19–22 被当成"穷尽后才生效"的预告 | 本会话 | FIXING 23:05 | 指令文件加"当前生效"头块（唯一权威、含本阶段必须实现的算子与验证步骤）；controller_advance 加算子守卫：本阶段 PLAN 里没出现过阶段算子就拒绝推进，改为写驳回指令 |
| E16 | 主控设计错误：条件化算子（第 3/4 阶段）在 14 只上算术不可行——半区条件后每日 ≤7 只 < MIN_PAIRS=8，有效日恒为 0（pi round_029 六条全部 discovery_days=0 并给出证明，`CONDITIONAL_STAGE_CLOSED.json`）。主控下达前未做 MIN_PAIRS 算术检查 | 本会话 | CLOSED 23:15 | 阶段关闭；教训：任何新构造先算"条件后每日剩几只 vs MIN_PAIRS/K+1"。转第 5 阶段：Tushare 份额/NAV 两家族（本地派生已尽，USER 定的顺序） |
| E17 | 压缩后 `get_session_stats` 短暂 tokens=None，状态文件上下文显示 None | Codex 文件 | RECORDED | 阈值判断对 None 安全；下一轮刷新恢复 |
| E18 | LM_JUMP_COUNT_20 发现 IC +0.296 / 审计 −0.045，疑 1m 数据质量断裂 | 数据 | CHECKED 02:30 | 逐年 1m 质检（159995/518880/513100）：2020–2025 年 5σ 跳跃数、零量 bar 占比稳定，无源切换断裂；跳跃计数的高 IC 来自截面流动性差异（稀疏成交 ETF 的伪跳跃），是经济现象非数据故障，审计反号即"低流动性溢价 2024 起消失"。**观察项**：513100 2026 年零量 bar 6.8%（2025 为 0），不在研究窗，交 ETF 数据链核 |
| E19 | 双线轮次编号冲突：Sonnet 线从 pi 历史 079 接着编 080，与 pi 线的 080+ 同名，且共用归档目录会互相覆盖（Sonnet 自己在简报里指出并拒绝跑归档） | 本会话 | FIXED 14:20 | Sonnet 线改用 500+ 编号（round_080→round_500，文件内引用同步改写），归档脚本按 `ETF_ARCHIVE_LANE` 分目录；修复时 `pkill -f` 匹配到自己的 shell 把命令杀了一半（老坑，用 `[e]tf_…` 括号模式 + 按 PID 杀），第二次干净完成，Sonnet 以原 session 续跑 round_501 |
| E11 | round_007 pi 自称两原子层穷尽（只普查未算 IC） | 研究口径 | CLOSED 18:50 | 当时不成立（supervisor 按"普查≠穷尽许可"记账并要求继续）。合同定义"连续 3 轮门 7 零入选"后，round_015/016/017 达成，pi 于 18:50 写 `MECHANISM_EXHAUSTED.json`，supervisor 写标记进入 `WAITING_FOR_NEW_MECHANISM`，Dagu precondition 阻止重拉。**这是按合同的干净终态，不是故障** |

## 一、结果账本

| 轮次 | 预注册 | 过门 | 基座版本 | 泄漏硬门 | 构造类型 |
|---|---|---|---|---|---|
| round_001 | 6 | 0 | `fd0c53ad`（独立脚本） | 通过 | 交互 |
| round_002 | 8 | 0 | `267d144b` | 通过 | 交互 |
| round_003 | 8 | 0 | `830bb0e5` | 通过 | 交互 |
| round_004 | 6 | 0 | `830bb0e5` | 通过 | 交互 |
| round_005 | 6 | **2**（W1、W5） | `830bb0e5` | 通过 | **价差** |
| round_006 | 6 | 0 | `bea695d0` | 通过 | 价差 |

40 条表达式，2 条入选，均标 `discovery_candidate_not_certified`，无独立 OOS。

前 34 条全是 `rank(A) * rank(B)` 交互式，全灭。round_005 改为 `rank(A) - rank(B)` 价差式后
当批出 2 条入选——乘积被"两个都高"的共同方向主导，截面上信息量低于差值。这是本次挖掘
唯一的结构性发现，属于构造方式层面，不是机制层面。

## 二、统计功效：当前门槛不可通过（未修复，待 USER 决策）

候选人口只有 **14 只 ETF**（`config/etf_rotation_universe_v1.json` 20 条里，2 只 benchmark、
2 只 defensive_tool、2 只 observation 不入截面；引擎内有 `assert len(symbols) == 14`）。

截面 Spearman IC 的噪声：单日 std ≈ 1/√13 = 0.277；标签是 5 日重叠收益，3 年发现期的
独立块约 110 个，故 IC 均值标准误 ≈ **0.023**；审计期（320 天）≈ **0.035**。

而 `GATES["min_abs_ic"] = 0.01`，**比一个标准误还小**。实测 40 条的 |IC| 落在 0.0015～0.072，
t 值 0.06～3.1，绝大多数不可与零区分。后果：

1. "发现期有 IC、审计期符号翻转"（`signed_seen_audit_ic` 是最高频的拒绝原因）在这个
   噪声水平下是预期现象，不构成机制失效的证据。
2. `identity_gate`（14 个 leave-one-out 的带符号 IC 每个都要 ≥ 0.01）在 SE=0.035 下几乎不可能过。
3. 整条流水线**没有任何显著性检验**，全部门槛建在点估计与符号一致上。

要让"IC=0.02 过门"等价于 t≈2，3 年期需要 N≈90，或 N=20 但历史拉到 8 年以上。

| N | 3 年 SE | 8 年 SE |
|---|---|---|
| 14（现状） | 0.023 | 0.014 |
| 20 | 0.019 | 0.012 |
| 50 | 0.012 | 0.0072 |
| 100 | 0.0083 | 0.0051 |

此外 14 只里含强相关对（159992 创新药 / 513120 港股创新药、159995 芯片 / 159516 半导体设备），
有效截面宽度还不到 14。

**扩人口与给门加 t 检验属于改研究口径，未执行，等 USER 定。**

### 二 b. top-3 轮动裁判：4 个入选候选对 14-EW 的超额（2026-09-19 17:12）

同一冻结上下文（标签 open(D+2)→open(D+7)、同 eligibility、同原子），每日按分数选 3 只，
与 14 只等权比。`t_block5` = 5 日非重叠块 t；`p_fam` = 20 日块 sign-flip 族 max-|t| p 值（4 候选同族）。

| 候选 | 窗口 | 天数 | 5日超额 bp | 年化超额 | 胜率 | t_block5 | p_fam | P@3 | 基线 P@3 |
|---|---|---|---|---|---|---|---|---|---|
| W1 | 发现 | 579 | +9.9 | +4.8% | 0.544 | 1.46 | 0.83 | 0.283 | 0.265 |
| W1 | 审计 | 320 | +6.0 | +2.9% | 0.481 | 0.50 | 1.00 | 0.212 | 0.215 |
| W5 | 发现 | 559 | +1.6 | +0.8% | 0.510 | 0.20 | 0.95 | 0.277 | 0.263 |
| W5 | 审计 | 320 | −4.9 | −2.4% | 0.547 | −0.24 | 1.00 | 0.249 | 0.215 |
| Z5 | 发现 | 552 | +19.0 | +9.3% | 0.569 | 1.70 | 0.83 | 0.287 | 0.265 |
| Z5 | 审计 | 320 | +4.6 | +2.3% | 0.500 | 0.25 | 1.00 | 0.227 | 0.215 |
| Y3 | 发现 | 559 | +17.5 | +8.6% | 0.556 | 1.62 | 0.45 | 0.279 | 0.262 |
| Y3 | 审计 | 320 | −13.1 | −6.4% | 0.484 | −0.50 | 0.99 | 0.240 | 0.215 |

读法：发现期 Z5/Y3/W1 的 top-3 年化超额 5–9%，t 1.5–1.7，族 p ≥ 0.45；到审计期全部塌回 ±3% 以内，
Y3 转负 6.4%。Precision@3 在两个窗口都贴着 3/14 的随机基线（差 ≤ 2 个百分点）。
**结论：截面 IC 门放进来的 4 条，在"选 3 只"这件事上没有一条可与噪声区分。** 老裁判的"入选"
不预示轮动收益；这条比"入选数"本身更重要。产物：`scripts/research/pi_glm_mining/audit/`。

### 七 b. Z2 稳健性（独立裁判，2026-09-19 22:15）

| 年 | 天数 | top-3 超额 bp/5日 | t_block5 | 胜率 |
|---|---|---|---|---|
| 2021 | 95 | +17.7 | 0.77 | 0.537 |
| 2022 | 242 | +31.4 | 2.03 | 0.599 |
| 2023 | 242 | +45.2 | 2.93 | 0.686 |
| 2024 | 242 | +41.5 | 2.33 | 0.591 |
| 2025(–04) | 78 | +73.3 | 2.18 | 0.654 |

五个年份全部正向，2022–2025 每年 t > 2；K=2 下发现期 +42.2 bp / t 3.08、审计期 +38.8 bp / t 1.85，P@2 高于基线。对照 C3 在 2022、2025 转负，F2 各年 t 1.1–1.7。
Z2 是目前唯一"逐年同向 + 两窗口显著 + K 不敏感"的候选。仍为 `discovery_candidate_not_certified`；审计面为已见面；唯一独立 OOS 是 2025-05 之后未触碰数据。

## 三、工程缺陷与处置

### 1. 前轮入选因子未接入去重（已由 pi 修复，做法正确）
`_dedup_pass` 把前轮 `gate_pass` 候选放进对比集但值填 `None`，随后
`assert not prior_keys` 兜底。round_005 首次产生入选（W1、W5）后该假设破裂，
round_006 于 16:33:45 抛 `AssertionError: prior admitted candidates present but not rebuilt`。
pi 在同一会话内改为：从不可变 `PLAN.json` 加载 + 校验 `plan_sha256` + 新增
`_prior_admitted_vectors` 重算前轮入选信号，**未删断言绕过**，16:38:14 重跑通过。
（若当时改为删断言，后续会静默跳过与历史入选因子的去重，源源不断"发现"换皮版本。）

### 2. 挖掘代码不在版本控制内（已修）
`pi_round001~006_mine.py` 共 2000+ 行只存在于 `runtime_outputs/`，而 `.gitignore:168` 忽略该目录。
已在 `frameworks/etf_rotation/scripts/research/pi_glm_mining/` 建立受跟踪存档（三个基座版本 +
六个驱动 + 哈希清单），见该目录 README。

### 3. 基座脚本跨轮变更，round_002 与后续不可直接比较（已记录，未重跑）
`script_sha256`：`267d144b`（round_002）→ `830bb0e5`（round_003–005）→ `bea695d0`（round_006）。
第一次变更修的是 `cross_etf_lead_lag` 家族取不到 benchmark 腿的 bug
（`ValueError: Invalid lead-lag benchmark symbols; missing=['510300.SH','510500.SH']`）。
**round_002 那 8 条是用带该 bug 的引擎算的**，其结果与 round_003 之后不是同一把尺子。
已重跑（`runtime_outputs/etf_pi_glm_mining_20260919/audit_rerun_round002_bea695d0/`）：8 条 IC 最大差 0.0e+00，拒绝原因逐条相同。结论：引擎变更不影响 round_002，跨轮可比。

### 4. 静态泄漏扫描扫的是空壳（已补齐）
round_003 起每轮只扫当轮 100 余行的薄驱动（`Scanned 1 file(s)`），未扫 1110 行基座；
round_004/005 报告里还写着"静态扫描见 `future_leak_scan_round002.txt`"，引用别轮文件。
动态泄漏门（物理截断副本 + 截后扰动副本重算，要求缺失掩码完全一致，四项 max_abs_diff 全 0）
是真测且覆盖基座，**所以不构成泄漏风险，但静态这条证据链是虚的**。

已用 `~/.codex/skills/future-function-killer/scripts/scan_future_leaks.py` 对基座 + 全部 6 个驱动
重扫：6 文件 4 处命中，全部在基座，两类均已解释（`entry_lag_sessions` 字段、
`pivot(index="signal_date", ...)` 日期列），`negative_shift` 未触发。结果存
`scripts/research/pi_glm_mining/full_static_leak_scan_20260919.txt`。

### 5. supervisor 无心跳（已由并发会话修复，待生效）
`supervisor_status.json` 只在轮次边界写 `updated_at`，外部无法区分 pi 卡死与正常计算 30 分钟
（`run_prompt` 3600 秒才超时）。另一会话已加 `supervisor_heartbeat.json`（30 秒原子刷新，
覆盖 `event()` 等待路径）。**新逻辑需下次 supervisor 启动后生效，当前进程仍是旧版，未擅自重启。**

### 6. 无产出时的空转循环（已由并发会话修复）
supervisor 连续两轮拿不到 `candidate_metrics.csv` 即抛错退出，而 Dagu 每 5 分钟无条件重拉，
会撞同一堵墙。已加 `MECHANISM_EXHAUSTED.json` 干净退出路径与同名 precondition。

### 7. 每轮驱动脚本未进快照（已记录，未改）
`_snapshot` 只快照基座，不快照当轮驱动。候选定义由带哈希的 `PLAN.json` 固定，科学内容不丢，
但驱动代码只有运行态一份。存档已覆盖当前六轮。

### 8. `identity_gate` 借用 `min_abs_seen_audit_ic` 作阈值（未改）
两个语义不同的门共用同一个 0.01，调其一会意外改动另一个。

### 9. 会话与轮次命名脱节（未改，无功能影响）
会话目录固定叫 `sessions_round_002` 而实际已到 round_006；恢复路径同时存在
`migration.json` 与 `supervisor_status.json`，优先级靠代码顺序隐式决定。

## 四、查过且不是问题

- 标签时序：`_raw_forward` 入场 `open(D+2)`、出场 `open(D+2+H)`，负向 shift 只在标签内，
  标签从不作特征。比 close(D) → open(D+1) 的项目惯例还晚一天，偏保守。
- 泄漏检查的临时截断/扰动数据副本有正常 `rmtree`，无残留；原始数据根未被改动。
- 文件锁防双跑实测有效（duplicate launch 保留在跑的 supervisor 与检查点）。
- 磁盘：整个 run 目录 5.3 MB，无压力。
- 去重本身工作正常：round_005 的 W3（发现 IC +0.054 / 审计 +0.074，数字最好看）因与货架
  `market_sensitivity` 因子 rank corr = 0.70 被判重复剔除——这是对的，它只是重新发现了已有因子。

## 五、分工（防撞车，2026-09-19 16:40 经 a2a 确认）

- `deployments/dagu/etf_pi_glm_mining.{yaml,py}` — Codex 及并发会话持有。
- `runtime_outputs/.../workspace/frameworks/etf_rotation/scripts/research/pi_round*.py` — pi 实时持有，他人不得改。
- 本文档、`pi_glm_mining/` 存档、完整静态扫描 — 本次审计会话持有。

## 六、终局（2026-09-19 18:50）

17 轮，94 条预注册（交互 27 / 价差 67），泄漏硬门 17/17 全绿，无独立 OOS。

| 裁判 | 入选 |
|---|---|
| 旧六门（截面 IC） | 6：W1、W5、Z5、Y3、N6、T5 |
| 门 7 v2（top-3 超额，审计 > 0） | 2：N6、T5 |
| **门 7 v2.1（审计 ≥ 5 bp，合同现行）** | **1：T5** `rank(SIGN_ACF1_5) − rank(LOG_AMOUNT_VOL_20)` |

T5：发现期 top-3 超额 +20.0 bp/5 日（年化 +9.7%）、5 日块 t 2.78、20 日块 t 2.20、族 p 0.15；
审计期 +15.7 bp、t 0.85、族 p 0.81；P@3 0.299/0.243（基线 0.273/0.230）；方向与预注册假设相反（数据定负向）。
身份 `discovery_candidate_not_certified`，登记为前向候选；唯一能定性它的是 2025-05 之后未触碰数据，合同现阻止查看。

穷尽判定：round_015（4 条）、016（5 条）、017（3 条）连续三轮门 7 零入选，满足合同；pi 写 `MECHANISM_EXHAUSTED.json`，
supervisor 进入 `WAITING_FOR_NEW_MECHANISM`，Dagu 停拉。主导失败模式：identity LOSO（靠一两只票撑）、审计期不持续、
与货架强原子冗余、P@3 贴基线。

pi 列出的继续条件（均需 USER 授权，不属于本线权限）：(a) 新数据面——申赎/NAV/IOPV/持仓/盘口（目录中 blocked 家族）；
(b) 新构造——三原子、条件化算子；(c) 纳入其他工作线的目录外 provider；(d) 终止本线。
**本线口径不变：14 只、只挖单因子、不做策略。**

## 七、第二阶段：本地派生三家族（2026-09-19 20:05 重开，USER 定向"先算本地能派生的"）

新增 `cost_distribution`（筹码/成本分布 5 原子）、`bar_size_order_flow`（1m 按 bar 大小分层量方向 5 原子）、`intraday_volume_profile_1m`（1m 量时间分布 5 原子）；1m 首次进入研究面，泄漏硬门含 1m 实测全绿。
新原子与货架 16 因子最大 rank corr 0.61，其余 0.13–0.47，无影子。

| 轮 | 预注册 | 门 7 入选 | 入选表达式 | 发现 top-3 超额 / t | 审计 top-3 超额 / t（独立裁判） |
|---|---|---|---|---|---|
| 018 | 6 | 1 | C3 `rank(CHIP_RANGE_90_60) − rank(BIGBAR_VOL_SHARE_20)` | +21.5 bp / 2.56 | +22.8 bp / 1.51 |
| 019 | 6 | 0 | — | — | — |
| 020 | 6 | 0 | — | — | — |
| 021 | 5 | 2 | F1 `rank(TICK_IMBALANCE_20) − rank(OPEN30_VOL_SHARE_20)` | +26.4 bp / 2.23 | +20.5 bp / 1.07 |
| | | | F2 `rank(CLOSE5_DAY_CONSIST_20) − rank(PRICE_POSITION_20)` | +24.2 bp / 2.38 | **+27.3 bp / 1.64** |
| 022 | 5 | 1 | **Z2** `rank(BIGBAR_DIR_SKEW_20) − rank(VOL_AUTOCORR_20)`（1m 大 bar 方向偏度 − 1m 量自相关；方向与假设一致） | **+34.9 bp / 3.56** | **+49.2 bp / 3.02**（族 p 0.36） |

Z2 是全部 10 个历史入选里唯一在审计期也显著的（t 3.02；P@3 0.324/0.268 vs 基线 0.265/0.215；与 C3 corr 0.41）。审计面仍是"已见"面，不是独立 OOS。
对照第一阶段（17 轮 94 条、旧原子、门 7 v2.1 入选 1：T5）：新家族 5 轮 28 条入选 4，且三条审计期超额 +20~27 bp、全部同向，是全部 9 个历史入选里审计期最稳的一组（T5 审计 t 0.85）。
F2 方向与预注册假设相反（数据定负向：尾盘贯彻弱 + 位置高 的一端跑赢），F1、C3 与假设一致。
所有入选仍为 `discovery_candidate_not_certified`，独立 OOS 只有 2025-05 之后未触碰数据。pi 引擎与独立裁判数值逐项一致。

### 七 c. 第二阶段终态（round_024，2026-09-19 22:23）

pi 以配对占优审计宣布穷尽：含新家族原子的 2416 个合法未测配对中 `fully_fresh = 0`（每一对至少一端已被检验过；1281 对含多次烧毁端点、240 对含 shelf 端点），继续预注册即"换搭档重 skin"。复盘 `outputs/round_024/RETROSPECTIVE.md`（指令 18 首次执行）：125 条实算的拒绝原因频次——identity LOSO 72%、审计同号 50%、门 7 45%、冗余墙 4%；结构结论：LOSO 与审计持续性是主导截断，全部入选均为"净差/错配"构造，1m 家族贡献 4/6。
阶段计分：7 轮（018–024）31 条实算，门 7 v2.1 入选 4（C3、F1、F2、Z2）。

### 八、第三阶段（条件化算子，2026-09-19 22:30 重开）
指令 19–22：`cond(A | B 在截面上/下半区)`，B 限三家族/状态原子（截面状态，不允许时间序列/市场级条件——策略边界）；每轮 ≤6 条，REPORT 报 Bonferroni 等价 t 门但不改门；连续 3 轮零入选 → 穷尽 → 转 Tushare 份额/NAV。
主控侧新增：`controller_verify.py`（入选自动交叉验证 + 逐年 + K=2）、`build_untested_pairs.py`（12,527 对盘点供 pi 选题）、`forward_ledger.py` + Dagu `etf_pi_forward_ledger`（工作日 19:30，门 7 入选自动前向登记，只记 2026-09-19 起）。

## 九、第五阶段终态与全线总结（2026-09-20 00:40）

### 第五阶段（份额 / NAV）
`fund_flow` 6 原子 + `nav_premium` 4 原子，PIT 抽检全绿，与货架最大 rank corr 0.42。round_032–034 共 18 条 `rank_spread`（每条含新家族腿）**全部门 7 拒绝**（18/18 topk_gate；identity 14/18）。最好一条 X5 `rank(SHARE_CHG_20) − rank(TAIL_Q10_20)` 发现 t 1.82、审计 +0.6 bp。pi 按合同（连续 3 轮零）写穷尽，守卫 OK，队列空，线进入 `WAITING_FOR_NEW_MECHANISM`。

### 全线（34 轮，178 条预注册，泄漏硬门全绿）

| 阶段 | 数据/构造 | 条数 | 门 7 v2.1 入选 |
|---|---|---|---|
| 1 | 135 旧原子，两原子价差/交互 | 94 | 1（T5） |
| 2 | +筹码/1m 订单流代理/1m 量分布 | 48 | 4（C3、F1、F2、Z2）+ BB1（round_027） |
| 3/4 | 条件化算子 | 18 | 0（算术不可行，E16） |
| 5 | +份额/NAV | 18 | 0 |

两窗口都显著的只有 **Z2**（审计 t 3.02）和 **BB1**（审计 t 2.46）；C3/F1/F2/T5 审计期同向但 t 0.85–1.64。6 条全部登记前向账本（`etf_pi_forward_ledger`，2026-09-22 起逐日累积真样本外）。

### 结论
在"14 只、单因子、top-3 对等权"这个合同下，本地能派生的全部数据面（日线/日内到 1m、筹码、订单流代理、一级市场份额/NAV）和可行的两原子构造已系统测完。**再挖只能靠新输入**：ETF 逐笔/盘口（CMES 未订、QMT 无历史）、或改合同（人口/K/裁判——需 USER）。pi 建议的"份额历史回补到 2015"不可行：多数候选基金 2019–2021 才成立，份额起点就是成立日。

主控建议：线保持 armed（4 个 DAG 不停，队列空则 supervisor 等待、不烧轮次），让前向账本跑 2–3 个月给 Z2/BB1 判决；新数据或新合同到位时向 `DIRECTIVE_QUEUE/` 放一个阶段文件即自动重开。

## 十、第 6/7 阶段排队（2026-09-20 00:55，USER goal：线不停）

队列空不等于面用尽——1m 数据上还有**有文献出处、未做过**的构造。已排入并自动生效：
- **第 6 阶段 `microstructure_1m` + `benchmark_leadlag_1m`**（00:55 起，round_035）：VPIN（Easley–LdP–O'Hara 2012，BVC 估算）、Kyle λ 代理、Roll 有效价差、1m Amihud、订单流不平衡持续性（Cont et al. 2014）、买卖冲击非对称；对 510300/510500 基准 1m 的领先滞后相关、同步 β/R²、尾 30 分钟 β 差。
- **第 7 阶段 `realized_measures_1m` + `intraday_periodicity`**（队列中）：BPV/RV 跳跃份额（BNS 2004）、Lee–Mykland 跳跃计数、已实现偏度/峰度（ACJV 2015）、已实现半方差差（BNKS 2010）、RV 日内 U 形偏离；同时段收益持续性（HKS 2010）、隔夜-日内差（LPS 2019）、尾 30 分钟 β。
每个原子必须在 REPORT 写出处；无出处不建（"三个来源"规则）。

### 十 a. 第 6 阶段结果（round_035–037，2026-09-20 01:20–02:00）
`microstructure_1m` 6 原子 + `benchmark_leadlag_1m` 5 原子（SYNC_BETA_20 与货架 corr 0.76 标 shadow 排除），泄漏门含基准 1m 副本。18 条 `rank_spread` **零入选**，连续 3 轮零 → 穷尽 → 自动进第 7 阶段。
最接近：K1 `rank(VPIN_CLOSE_20) − rank(PRIMARY_SHARE_20)`（VPIN − 一级市场量占比）发现 +25.7 bp / t 2.39、审计 +17.7 bp、P@3 高于基线——**只倒在 identity LOSO**；M4 `rank(TAIL30_BETA_GAP_20) − rank(PRIMARY_SHARE_20)` 发现 t 2.60 但审计 −16.9 bp。
单原子体检：VPIN_CLOSE_20 发现 IC +0.036（与货架 corr 0.38，是新轴）；TAIL30_BETA_GAP_20 +0.091 最强但审计归零；SYNC_R2_20 −0.083 / 审计 −0.069 两窗口同向。
65% 压缩（00:45）首次走通：压缩后 pi 直接接续压缩前任务，合同未丢；压缩后 `get_session_stats` 短暂返回 tokens=None（E17，仪表，无功能影响）。

### 十 b. 第 7 阶段结果（round_038–040）
`realized_measures_1m` 7 原子 + `intraday_periodicity` 3 原子。18 条 **零入选**，三轮零 → 穷尽 → 自动进第 8 阶段。
最接近：R3 `rank(RSKEW_20) − rank(TAIL_Q10_20)` 发现 t 2.12 但审计 +2.3 bp（<5）；S4 `rank(VOL_USHAPE_20) − rank(PROFIT_RATIO_60)` 发现 t 1.96 / 审计 +15.2 bp 差 0.04 个 t；S1 `JV_RV_SHARE − SHARE_Z_60` 发现 t 3.39 但审计翻负。
单原子体检异常：**LM_JUMP_COUNT_20 发现 IC +0.296、审计 −0.045**——发现期 IC 高到不正常且审计反号，怀疑 1m 数据质量随时间变化（跳跃计数对停牌/零量 bar/数据源切换极敏感），已做逐年 1m 质量检查（见 E18）。VOL_USHAPE_20 两窗口同向（−0.083 / −0.089）是新家族里最稳的原子。

**第 5–7 阶段合计 54 条零入选**，拒绝结构：topk 52、identity 39、审计同号 21。只倒在 topk 的 14 条、只倒在 identity 的 1 条。第 2 阶段（筹码/订单流代理/量分布）仍是唯一产出阶段（5/48）。

### 十 c. 第 8 阶段进行中（round_041–048，2026-09-20 02:05–02:35）
`cojump_1m` + `liquidity_commonality_1m`。8 轮 48 条，门 7 入选 2（独立裁判均 CONSISTENT）：
- **W3** `rank(RESILIENCY_20) − rank(SHARE_RET_CORR_20)`（1m 冲击后 5 分钟回复力 − 份额-收益相关；方向与假设相反）：发现 +39.1 bp / t 3.57；审计 +21.2 bp / t 1.06；逐年全正（2021 t 4.4、2022 2.2、2023 2.2、2024 0.7、2025 0.7）；P@3 0.368/0.347 vs 基线 0.309/0.292。
- **Z1**（round_046）：发现 +29.3 bp / t 2.27；审计 +6.4 bp / t 0.29（v2.1 门 ≥5 bp 勉强过）；逐年不同向。弱。
注意：新家族原子有缺失，每日合格票数降到 ~10（P@3 基线由 0.265 升到 0.31），距 MIN_PAIRS=8 不远，第 8 阶段原子覆盖需留意。
控制器：round_043 STATUS 与 02:25 tick 同秒落地被跳过，02:30 tick 补齐——文件时序竞争，无需修（下一 tick 必补）。
累计 48 轮 ~260 条，门 7 v2.1 入选 9：T5、C3、F1、F2、Z2、BB1、W3、Z1 +（round_027 BB1 已计）。两窗口显著仍只有 Z2、BB1。

## 十一、第 8 阶段终态与第 9 阶段（2026-09-20 02:45）

第 8 阶段 9 轮 54 条，入选 W3、Z1；round_047–049 三轮零 → 按合同穷尽，pi 复盘：49 轮 268 条预注册、八个构造阶段全部按合同穷尽、泄漏门 49/49 全绿、有效候选 9。pi 提出的下一步：真实订单簿（需 tick/盘口）、更长份额历史（不可行：基金成立日即起点）、多资产横截面依赖（本地可算，问是否属单因子）、事件日历（需数据）。
主控裁定：**每天每只一个分数、不合成不加权不择时 = 单因子**，同伴关系只是特征输入 → 第 9 阶段 `peer_relative_value`（GGR 2006 / Avellaneda–Lee 2010）+ `cross_dependence_1m`（Billio 2012 / Diebold–Yilmaz 2014）已排队并自动生效。
pi 提醒前向账本为空表：符合预期——只记 2026-09-19 起，数据止于 09-17，09-22（周一）起有第一行。

**口径问题（待 USER，主控不动）**：268 条中 identity LOSO 是主导截断（第 5–7 阶段 54 条里 39 条倒在它），且多条"只差 LOSO"（K1、S4 等）。14 只上逐个剔除本身就要求因子对 14 只中任意 13 只都成立，比 identity 门的原意（不靠单票）严得多。可选：LOSO 改为"剔除后 IC 同号且 ≥ 0.5×原值"或"14 次中允许 1 次失败"。改之前需 USER 点头，改后要用 268 条重打对照。

## 十二、第 9 阶段结果与第 10 阶段（2026-09-20 03:40）
`peer_relative_value` 4 原子（PEER_RELSTR_Z_20 与货架 corr 0.72 shadow）+ `cross_dependence_1m` 4 原子。round_050–052 共 18 条**零入选**，三轮零 → 穷尽。最接近 Q3 `rank(PEER_OU_HALFLIFE_20) − rank(CATEGORY_MOM_60)` 发现 t 2.39 / 审计 +9.1 bp，倒在 P@3 审计 0.208 < 基线。单原子 GRANGER_IN_DEGREE_20 两窗口同向（−0.079 / −0.044）是本阶段最稳的原子。
第 10 阶段已排队：**全部原子在门 7 下单原子重裁**（旧 135 + 新增 ~55 此前只在 v9 截面 IC 下裁过）——同一把尺子重量货架，一轮完成，复盘单列"只差 identity LOSO"的原子清单供 USER 定口径。之后队列空。
累计 52 轮 286 条，门 7 入选 9，两窗口显著 Z2、BB1。

## 十三、第 10 阶段：全部原子在门 7 下重裁（round_053，2026-09-20 03:38–04:0x）

246 个非 shadow 原子（62 族）作 `atomic` 一次过七道门 + 去重。**7 个入选**：

| 原子 | 方向 | 发现 top-3 超额 / t | 审计超额 | P@3 发现/审计 | 与货架最大 corr |
|---|---|---|---|---|---|
| BIGBAR_VOL_SHARE_20（1m 大 bar 量占比） | + | +24.5 bp / 2.92 | **+41.6 bp** | 0.271 / 0.232 | 0.686 |
| BIGBAR_EDGE_CONC_20（大 bar 时点集中度） | − | +21.9 / 2.55 | **+30.7** | 0.273 / 0.229 | 0.634 |
| VOL_USHAPE_20（RV 日内 U 形偏离） | − | +27.0 / 2.12 | **+33.9** | 0.320 / 0.297 | 0.506 |
| CATEGORY_VOL_20（类别波动） | − | +35.8 / 2.42 | +19.0 | 0.310 / 0.267 | 0.671 |
| WORST_DAY_20（20 日最差日） | + | +30.0 / 2.18 | +16.2 | 0.312 / 0.262 | 0.648 |
| VOL_PROFILE_DISTANCE（量分布距离） | + | +37.1 / **4.04** | +10.1 | 0.333 / 0.227 | 0.353 |
| GAP_FILL_FRACTION_60（跳空回补比例） | − | +32.6 / 2.59 | +9.8 | 0.327 / 0.298 | 0.469 |

拒绝频次（246）：topk 230、identity 169、审计同号 106、abs IC 64、horizon 57、年度 48；只倒在 identity LOSO 的 4 个：**RANGE_OVERLAP_20、DOWN_UP_ACTIVITY_60、VPIN_CLOSE_20、VOL_RESPONSE_ASYMMETRY_60**（供 USER 定 LOSO 口径）。5 个过了七道门但撞冗余墙（CATEGORY_VOL_60、CATEGORY_DISPERSION_20、GAP_VOL_RATIO_20、VOL_SPIKE_FREQ_20、LOG_AMOUNT_VOL_20）。
读法：**单原子在门 7 下的表现优于绝大多数两原子价差**——本线新增的 1m 家族里 BIGBAR_VOL_SHARE / BIGBAR_EDGE_CONC / VOL_USHAPE 三个单原子审计期超额 +31~42 bp，比 Z2（+49）之外的所有组合都高。两原子组合大部分是在稀释单原子信号。7 个原子自动进前向账本。独立裁判验证见 controller_verification.json。

### 十三 a. 7 个原子的独立裁判验证（CONSISTENT）

| 原子 | 审计 t（K=3） | K=2 审计 | 逐年 t（21/22/23/24/25） |
|---|---|---|---|
| **BIGBAR_VOL_SHARE_20** | **2.26** | +51.7 bp / **2.59** | 3.0 / −0.4 / 3.7 / 1.8 / 1.2 |
| BIGBAR_EDGE_CONC_20 | 1.84 | +22.8 / 0.99 | 3.3 / −1.2 / 4.1 / 1.8 / 0.8 |
| VOL_USHAPE_20 | 1.24 | +44.1 / 1.55 | 0.5 / 0.7 / 2.5 / 0.7 / 1.8（全正） |
| CATEGORY_VOL_20 | 0.70 | +3.2 / 0.10 | 2.2 / 1.1 / 1.8 / 0.8 / 0.1（全正） |
| WORST_DAY_20 | 0.61 | +1.6 / 0.05 | 全正但 2024–25 弱 |
| VOL_PROFILE_DISTANCE | 0.66 | +17.8 / 0.97 | 2023 t 4.7 主导 |
| GAP_FILL_FRACTION_60 | 0.32 | +10.8 / 0.26 | 2025 转负 |

**审计期显著的单原子只有 BIGBAR_VOL_SHARE_20**（与 Z2、BB1 并列为全线三个两窗口显著的候选；三者都含 1m 大 bar / 量 spike 信息）。其余 6 个是"发现强、审计弱"。

## 十四、十阶段总结（2026-09-20 04:10）

54 轮，≈540 条实算（含 246 原子重裁），泄漏硬门 54/54 全绿，预注册哈希无覆盖，两套裁判逐项一致。

**两窗口显著（发现 t≥2 且审计 t≥2）——3 个，全部含 1m 大 bar / 量 spike 信息：**
- Z2 `rank(BIGBAR_DIR_SKEW_20) − rank(VOL_AUTOCORR_20)`：审计 +49 bp / t 3.02
- BB1 `rank(VOL_SPIKE_FREQ_20) − rank(ULCER_20)`：审计 +36 bp / t 2.46
- BIGBAR_VOL_SHARE_20（单原子）：审计 +42 bp / t 2.26（K=2 t 2.59）

**门 7 入选、审计弱**：T5、C3、F1、F2、W3、Z1 + 6 个单原子。全部 `discovery_candidate_not_certified`，前向账本 2026-09-22 起逐日记。

**结构性结论**
1. 信息在 1m 大 bar / 量分布形状里，不在日线价量形态里（第 1 阶段 94 条只出 T5）。
2. 单原子 > 两原子组合：组合多数在稀释。第 11 阶段只在已验证原子之间做定向配对收尾。
3. identity LOSO 是主导截断：246 原子里 169 倒在它；4 个原子只差它（RANGE_OVERLAP_20、DOWN_UP_ACTIVITY_60、VPIN_CLOSE_20、VOL_RESPONSE_ASYMMETRY_60）。**口径决定权在 USER。**
4. 14 只人口下每天合格票数 10–14，任何减少样本的构造（条件化、含缺失的新原子）都直接撞 MIN_PAIRS=8。

**工程终态**：4 个 Dagu DAG 自动闭环（挖掘、控制器、前向账本、份额/NAV 日更）；控制器今晚修过 3 个自身 bug（验证器 t 定义、守卫读旧块、单轮阶段规则）；pi 修过 6 个引擎问题（去重重建、benchmark 腿、模板字面量、缓存、1m 泄漏副本含基准、加载器早退）；一次 65% 压缩走通。

### 十四 a. 第 11 阶段进行中（round_056–057）
AF6 `rank(OPEN30_VOL_SHARE_20) − rank(LOG_AMOUNT_VOL_20)`（开盘 30 分钟量占比 − 成交额波动；方向与假设相反）：截面 IC −0.100 / −0.085（全线最高的 IC 对），top-3 发现 +26.3 bp / t 2.51，审计 +27.7 bp / t 1.35（K=2 +43.7 / 1.67），2023 主导（t 3.88）、2022 −7.9 bp；与货架 liquidity_variability corr 0.61。两腿单原子在门 7 重裁中均未入选 → 组合有增量。CONSISTENT。

### 十四 b. round_060：一轮三入选（CONSISTENT）
| 候选 | 表达式 | 发现 / t | 审计 / t | 逐年 t |
|---|---|---|---|---|
| **AI4** | `rank(GAP_FILL_FRACTION_60) − rank(VOL_SPIKE_FREQ_20)`（IC −0.114 / −0.070，全线最高） | +37.5 bp / 3.55 | **+42.7 bp / 2.58** | 1.9 / 1.7 / 3.3 / 2.6 / 1.0（全正） |
| AI6 | `rank(BIGBAR_EDGE_CONC_20) − rank(SIGN_ACF1_5)` | +21.4 / 2.55 | +34.1 / 1.85（K=2 1.89） | 3.0 / −1.1 / 4.5 / 2.1 / −0.3 |
| AI1 | `rank(BIGBAR_VOL_SHARE_20) − rank(RESILIENCY_20)`（IC +0.140，全线最高单值） | +34.1 / 3.34 | +17.2 / 1.17 | 2021 无样本 |

**AI4 成为第 4 个两窗口显著候选**，且是唯一逐年全正且 2024 仍 t 2.6 的组合。两腿（GAP_FILL_FRACTION_60、VOL_SPIKE_FREQ_20）在门 7 重裁中分别为"审计弱入选"与"冗余墙拒绝"——组合增量真实。第 11 阶段（已验证原子定向配对）5 轮 4 入选，是第 2 阶段之后最高产的构造。
### 十四 c. round_063：AL3 `rank(LOG_AMOUNT_VOL_20) - rank(RESILIENCY_20)`（CONSISTENT）
发现 +26.4 bp / t 2.08；审计 +24.7 bp / t 1.56（K=2 +36.0 / 1.88）；逐年 −0.6 / 0.5 / 2.5 / 1.5 / 0.3。审计中等。第 11 阶段 8 轮 5 入选。
### 十四 d. round_065：AN2 / AN6（CONSISTENT，审计弱）
- AN2 `rank(VOL_PROFILE_DISTANCE) - rank(RESILIENCY_20)`：发现 +34.5 bp / t 2.95，审计 +17.8 bp / t 0.88。
- AN6 `rank(BIGBAR_DIR_SKEW_20) - rank(RESILIENCY_20)`：发现 +19.0 / 2.12，审计 +7.7 / 0.54。
控制器：round_065 的自动验证一次失败（无产物），tick 已改为"验证未产出则不标已见、下一 tick 重试，并保留 stderr"（`dfced37e`）；手动补验一致。第 11 阶段 12 轮 7 入选。

## 十五、第 11 阶段终态：组合 vs 单腿增量复核（2026-09-20 05:30）

第 11 阶段 13 轮，入选 7（AF6、AI1、AI4、AI6、AL3、AN2、AN6），round_066–068 三轮零 → 穷尽。主控用 round_053 的单原子门 7 数字逐条对照"组合 − 最好一腿"：

| 组合 | 组合审计超额 | 最好一腿（单原子审计） | 增量 |
|---|---|---|---|
| AI4 GAP_FILL − VOL_SPIKE_FREQ | +42.7 | VOL_SPIKE_FREQ_20 **+50.7** | **负**（VOL_SPIKE 单原子更强，但它被冗余墙拒） |
| AI6 BIGBAR_EDGE_CONC − SIGN_ACF1_5 | +34.1 | BIGBAR_EDGE_CONC_20 +30.7 | +3（≈持平） |
| AF6 OPEN30_VOL_SHARE − LOG_AMOUNT_VOL | +27.7 | LOG_AMOUNT_VOL_20 +36.8 | 负 |
| AL3 LOG_AMOUNT_VOL − RESILIENCY | +24.7 | LOG_AMOUNT_VOL_20 +36.8 | 负 |
| AI1 BIGBAR_VOL_SHARE − RESILIENCY | +17.2 | BIGBAR_VOL_SHARE_20 +41.6 | 负 |
| AN2 VOL_PROFILE_DISTANCE − RESILIENCY | +17.8 | VOL_PROFILE_DISTANCE +10.1 | +8 |
| AN6 BIGBAR_DIR_SKEW − RESILIENCY | +7.7 | BIGBAR_DIR_SKEW_20 +8.7 | 负 |

**结论：第 11 阶段 7 条入选里 5 条是对更强单腿的稀释**；RESILIENCY_20 作减腿的四条全是负增量（RESILIENCY 单原子审计仅 +2.2）。指令要求的"报增量"pi 没有当门用（也不该——那是口径），主控在此补上。

**冗余墙复核（提前给出，第 12 阶段正式成表）**：
- VOL_SPIKE_FREQ_20（审计 +50.7，全线最高）被拒是因与**同批入选** BIGBAR_VOL_SHARE_20 corr 0.92——两者是同一信息（1m 量 spike）的两种度量，去重选了先入选者；
- LOG_AMOUNT_VOL_20（+36.8）、CATEGORY_DISPERSION_20（+23.3）、GAP_VOL_RATIO_20（+21.8）与货架因子 corr **1.00**——货架 16 里的 liquidity_variability / category_state / gap_volatility 就是这三个原子本身。即：**货架 16 里至少有 3 个在门 7 下审计期 +22~37 bp 的因子**，它们从未按门 7 记账。

**对 USER 的口径问题再加一条**：门 7 之外是否加"组合必须优于最好单腿"（增量门）。不加则组合入选名单会被稀释项占满；加了则第 11 阶段只剩 AI6/AN2。

## 十六、第 12 阶段：货架 16 在门 7 下重裁 + 冗余墙复核（round_071，2026-09-20 04:55）

| 货架因子 | 发现 top-3 / t | 审计超额 | 门 7 |
|---|---|---|---|
| liquidity_variability（= LOG_AMOUNT_VOL_20） | +22.9 bp / 2.23 | **+36.8** | 过 |
| category_state（= CATEGORY_DISPERSION_20） | +32.9 / 2.11 | +23.3 | 过 |
| gap_volatility（= GAP_VOL_RATIO_20） | +30.5 / 2.34 | +21.8 | 过 |
| cross_etf_lead_lag | +2.6 / 0.25 | +29.3 | 发现不显著 |
| intraday_return_distribution | −1.5 / −0.16 | +26.9 | 发现不显著 |
| 其余 11 个 | — | ≤ +20.8，6 个为负 | 拒 |

**货架 16 里只有 3 个在门 7 下站得住**；serial_dependence（−13.5 bp）、intraday_turnover_asymmetry、return_tail_shape、downside_risk 审计期为负——IC 裁判下选出的货架，在轮动裁判下一半是噪声。
冗余墙复核：3 个恒等重复（corr 1.00，货架因子即载体，均过门 7，信息无损）；VOL_SPIKE_FREQ_20 与 BIGBAR_VOL_SHARE_20 corr 0.92、CATEGORY_VOL_60 与 CATEGORY_VOL_20 0.81 是本线同批入选的同通道载体。**冗余墙工作正常。**

## 十七、十二阶段终局（2026-09-20 05:00）

71 轮；实算 ≈ 560 条（含 246 原子 + 16 货架重裁）；泄漏门 71/71 全绿；两套裁判全部一致；两次 65% 压缩走通；队列空，线 `WAITING_FOR_NEW_MECHANISM`，4 个 Dagu DAG 继续运行。

**两窗口显著（发现 t≥2 且审计 t≥2）——4 个：** Z2、BB1、BIGBAR_VOL_SHARE_20、AI4。外加同通道更强但被去重挑掉的 VOL_SPIKE_FREQ_20（审计 +50.7）。**全部含 1m 大 bar / 量 spike 信息。**
**审计期 +20~37 bp 但 t<2：** 货架 liquidity_variability / category_state / gap_volatility、VOL_USHAPE_20、BIGBAR_EDGE_CONC_20、W3、F2、AI6、AL3、AF6。
**本线净贡献**：在 14 只 ETF 上，日线价量形态（阶段 1）、份额/NAV（5）、微观结构（6）、已实现测度（7）、共跳/流动性共性（8）、同伴相对价值（9）都没有产出两窗口显著的因子；产出的只有 1m 大 bar / 量 spike 家族（阶段 2 + 重裁）。这是可定案的结论。

**等 USER 的三个口径决定**（主控均不自行改动）：
1. identity LOSO 是否放宽（4 原子 + 1 组合只差它，含 VPIN_CLOSE_20）；
2. 是否加"组合必须优于最好单腿"增量门（第 11 阶段 7 条里 5 条稀释）；
3. 是否开新数据面（ETF 逐笔/盘口）——唯一还能解锁新原子族的输入。
三者任一落定，往 `DIRECTIVE_QUEUE/` 放一个阶段文件，线 5 分钟内自动重开。

## 十八、第 13 阶段：口径诊断重打（round_072，只报告不改门；2026-09-20 13:20）

636 个唯一表达式（组合 + 246 原子 + 16 货架）在六种假设口径下重打。Bonferroni 等价 t 门（N=636）≈ 3.95。

| 口径 | 入选 | 相对现行 A 新增 | 相对 A 剔除 |
|---|---|---|---|
| A 现行（LOSO 14/14） | 25 | — | — |
| **B LOSO 允许 1 次失败** | 32 | +7：VPIN_CLOSE_20、DOWN_UP_ACTIVITY_60、VOL_RESPONSE_ASYMMETRY_60、MAX_DD−RETURN_SKEW、TICK_IMBALANCE−GAP_FILL、VOL_PROFILE_DISTANCE−SIGN_ACF1、VPIN−PRIMARY_SHARE | 0 |
| C LOSO 改 ≥0.5×原 IC | 25 | +4（含上述 3 原子） | −4：**Z2**、F2、GAP_FILL_FRACTION_60、WORST_DAY_20 |
| A+D 增量门 | 16 | 0 | −9（第 11 阶段 7 条中 5 条 + CHIP−BIGBAR、BB1） |
| B+D | 22 | +6 | −9 |
| C+D | 16 | +4 | −13 |

读法：
- **B（允许 1 次失败）是纯放宽**：加 7 条、不减任何一条；VPIN_CLOSE_20 等 3 个"只差 LOSO"的原子全部进入。
- **C 会剔掉 Z2**（全线审计 t 最高的候选）——因为 Z2 剔某一只后 IC 掉到不足原值一半，即 Z2 的截面信号有一定集中度。C 不可取。
- **D（增量门）剔 9 条**，含 BB1（`VOL_SPIKE_FREQ − ULCER`，因 VOL_SPIKE 单原子审计 +50.7 更高）和 AI4。D 的效果是把"组合稀释单腿"的名单清掉，代价是 BB1/AI4 这种两窗口显著的组合也被归入"不如单腿"。
- 决定权在 USER；主控不改门。若采 B 或 B+D，需改合同 `identity_min_abs_ic` 规则并全量重打入账（本表即重打结果，可直接作为 referee v3 的账本）。
## 十九、第 14 阶段进行中（round_073–077，2026-09-20 13:05–13:45）
`largebar_footprint_1m` 8 原子零 shadow（与通道原子 corr ≤0.39）。单原子重裁：LBAR_CLOCK_STD_20（Easley 成交量钟离散度）七门全过（发现 t 3.12、审计 +9.6 bp）。配对 3 轮 1 入选：BJ5 `rank(LBAR_OVERNIGHT_20) - rank(CHIP_RANGE_90_60)`——发现 +26.2 bp / t 2.25，审计 +12.6 / t 0.55（CONSISTENT，审计弱）。

## 二十、Sonnet 5 并行线（2026-09-20 13:50 起，USER："你可以用 sonnet5 来挖掘"）

pi/opencode 无 Anthropic 通道 → 用 headless Claude Code（`claude -p --model claude-sonnet-5 --resume <sid>`，每轮一次调用，同会话续）。独立工作区 `runtime_outputs/etf_sonnet_mining_20260920/`（复制引擎、缓存、pi 线 79 轮历史；CLAUDE.md 承载合同/流程/禁止项），Dagu `etf_sonnet_mining` + `etf_sonnet_controller`（控制器脚本按 `ETF_RUN_DIR` 参数化）。首轮踩坑：`--add-dir` 变参吞掉提示词 → 改 stdin 传入。
**round_080（S1 步骤 1）**：GAP_SCAN 通读五份复盘 + 62 个家族配置，先排除三个"看似新其实已有"（成交量钟已在 LBAR_CLOCK_STD；除权事件 14 只共 10 次太稀；MAX 效应属现有 return_tail_shape 的缺原子），选定 **协偏度/协峰度风险**（Harvey–Siddique 2000；Ang–Chen–Xing 2006）建 `coskewness` 家族 4 原子（COSKEW_20/60、COSKEW_CHG_20、DOWNSIDE_COSKEW_60）。门 7 单原子重裁 **0/4**（t ≤ 0.61，审计 ±8 bp）。第 2、3 名（池内收益集中度、久期利差）与既有家族撞名/撞机制，Sonnet 自己标注需先读现有实现再定。
观察：Sonnet 的缺口扫描比 pi 更审慎（先查重再建），首个家族结果为负。
## 二十一、pi 第 16 阶段（集合竞价 / 首尾 bar）进行中
round_089：**CH6** `rank(AUC_CLOSE_VOLSHARE_20) - rank(LOG_AMOUNT_VOL_20)`——发现 +37.7 bp / t 3.17，审计 +30.7 bp / **t 1.95**（K=2 +32.6 / 1.82），逐年 0.6 / 2.0 / 2.4 / 1.2 / 2.1（全正）。CONSISTENT。审计 t 差 0.05 到显著线，是 Z2/BB1/BIGBAR_VOL_SHARE/AI4 之后最接近的一条。
round_090：**CJ6** `rank(AUC_CLOSE_CONSIST_20) − rank(LOG_AMOUNT_VOL_20)`——发现 +30.6 bp / t 2.98，审计 +28.9 bp / t 1.67（K=2 +35.5 / 1.59），逐年 −0.9 / 1.3 / 3.4 / 1.1 / 1.6。CONSISTENT。
round_091：**CK4** `rank(AUC_DISCOVERY_SHIFT_20) − rank(LOG_AMOUNT_VOL_20)`——发现 +19.1 bp / t 2.15，审计 +32.2 bp / t 1.76（K=2 +33.4 / 1.49），逐年 1.7 / 0.1 / 2.6 / 1.4 / 0.9 全正。CONSISTENT。
第 16 阶段 4 轮 3 入选，三条全是"集合竞价成交量结构 − 成交额波动"：收盘竞价量占比、收盘竞价方向一致度、价格发现重心前后移。共同减腿 LOG_AMOUNT_VOL_20 单原子审计 +36.8 bp——需看增量（见 §15 的口径注记）；集合竞价面本身的信号以 AUC_* 单原子重裁结果为准（round_085/086 单原子重裁 0 过门 → 竞价原子单独不够，与 LOG_AMOUNT_VOL 相减后才过）。

## 二十二、pi 第 17 阶段（成交量时间 volume clock）5 轮总结 + 批量口径切换（2026-09-20 14:40）
round_093–097：6/6/2/4/22 条预注册，入选 1（round_095 **DA2**，volume_time 原子重裁）。round_097 是首个按 15–30 条口径跑的轮（USER 14:30 定："不要限制每轮只挖几个"）：22 条 VT_× 跨家族配对全拒，拒因分布：identity/topk 各占一半，5 条因与 DA2/F1/AN6 rank corr ≥0.7 去重挑掉——volume_time 原子与已入选的 1m 量通道高度同源。
round_098（24 条）：**CO09** `rank(VT_BUCKET_GINI_20) − rank(PRICE_POSITION_20)`（交易到达不均匀 − 价格位置）发现 IC −0.035 / 审计 −0.052，2021–23 同向 2/3，LOSO 过，max rank corr 0.52（vs BB1）。方向与预登记假设相反（预登记 +1）。待主控 tick 交叉验证（gate 7 block-t）。
观察：批量放大后单轮供给 22–24 条，跑时 ≈6 分钟，缓存命中；一轮拒绝分布可直接看出通道饱和（去重挑掉比例），比 6 条/轮时的判断快 3–4 轮。
队列：pi stage18 lunch_break_1m / stage19 vol_of_vol_1m / stage20 orderflow_persistence_1m；Sonnet S3 rescan / S4 jump_continuous_beta_1m / S5 microstructure_noise_1m。四个新族均已查重（VOLVOL/RQ/HAR、JUMP_BETA、FLOW_ACF/RUNS、TSRV/签名图在 68 个家族与全部 candidate_metrics 中零命中）。
Sonnet round_504（S2 upside_tail 原子重裁 6 条）0 入选；S2 累计 501–504 零，下一轮 15–30 条口径。
可选口径调整（不阻塞）：无新增。
round_098 CO09 主控验证：k3 发现 +22.6 bp / t 2.43，审计 +25.6 bp / t 1.27（k2 审计 +41.2 / 1.62），逐年同号，CONSISTENT。
round_099（24 条）入选 4：CO35 `VT_AUTOCORR − BIGBAR_DIR_SKEW`、CO36 `VT_AUTOCORR − VOL_SPIKE_FREQ`（审计 IC −0.062，3/3 同向）、CO43 `VT_SKEW − RESILIENCY`（+0.052，3/3，方向符合假设）、CO44 `VT_SKEW − BIGBAR_VOL_SHARE`。CO35/CO36 与 AN6/AI1 rank corr 0.69，踩在去重门 0.7 边上；四条中三条仍是"volume_time 原子 − 1m 大 bar/量 spike 腿"。待下一 tick 交叉验证。
- **E20（2026-09-20 14:40，Sonnet 线）** round_504 计算 14:22 完成后，Sonnet 在 headless 下起了后台任务并用 `tail -f`/Monitor 等日志，两个工具调用挂满 10 分钟才返回（本轮 $10.2 累计成本里约 1/3 是空等）。修：系统提示加"禁止 nohup/& + tail -f/sleep 轮询"（`8454e78f`）。附带发现：supervisor 收到 SIGTERM 后 handler 里 raise 没能打断 `communicate()`，进程不退，`dagu stop` 会失效；改为 handler 直接写 STOPPED 检查点、killpg 工作进程、`os._exit(0)`。旧 supervisor 用 SIGKILL 结束后经 Dagu 重启，round_505 从头开始（损失 <1 分钟）。
- **E21（2026-09-20 14:40）** `untested_pairs.csv` 自 13:05 未刷新：`build_untested_pairs.py` 在 round_073+ 的 `atom_health.csv`（列名改成 discovery_ic/seen_audit_ic/shelf_max_corr）上 KeyError，tick 把 stderr 丢到 /dev/null 所以无告警。修：按别名读列、缺列填 NaN 不崩；tick 保留 stderr 尾 3 行。重建后 162 原子 / 12,527 对 / 已测 190 / 含新家族腿未测 2,188。
- **E22（2026-09-20 14:50）** Sonnet 线入选轮的交叉验证一直失败：`controller_verify.py` 把引擎/家族配置工作区写死到 pi 线路径，Sonnet 自建的 `family_upside_tail_v1.yaml` 找不到。修：按被验证轮所在工作区解析（pi 保持原审计副本目录，其他线用 `<run_dir>/audit_verify_ws`）。补验 round_506：**VA3** `rank(BEST_DAY_60_XVOL) − rank(VOL_SPIKE_FREQ_20)` 发现 +17.9 bp / t 2.01，审计 +34.3 bp / **t 2.24**，逐年同号，CONSISTENT——Sonnet 线首条两窗口显著，但减腿仍是 VOL_SPIKE_FREQ，与 BIGBAR_VOL_SHARE corr 0.70。VB8 审计 +9.9 bp / t 0.60。
pi round_101 CQ08 审计 +19.6 / t 1.00；round_102 **CR08** `VT_BUCKET_COUNT_SHIFT − OPEN30_VOL_SHARE` 审计 +36.5 bp / t 2.02 逐年全正（两窗口显著）；round_104 CT11 待验。Sonnet round_507 入选 WI2、WJ4 待验。
- **E23（2026-09-20 14:55–15:00，数据事故，已恢复）** pi 在第 17 阶段自建了一个 `frequency: 1d` 的家族（`overnight_structure_1d`），引擎泄漏门 `_temp_intraday_root` 先把 `root/1d` 符号链接到规范数据根，又把 "1d" 收进待截断频率，于是截断副本**穿过符号链接写进了规范 1d 目录**：14 只候选 ETF 的原始日线被截到 2023-12-29（6 只非候选未动）。两条线同分钟报 `Daily data does not reach as_of`。pi 自己在 14:57 改引擎排除 1d，15:00:54 从 `.staging` 回写 14 个文件；主控 15:05 逐行核对：与 `.staging` 在 2026-09-17 前完全一致（staging 多一行 09-18 是日更），1m/5m/15m/30m/60m/1d_qfq 未被触碰。主控加硬防护：两条线引擎的两个写入点前加 `_assert_scratch_dir`（拒绝符号链接、拒绝 resolve 到规范根内），Sonnet 引擎同步排除 1d；违反直接抛错而非静默。Sonnet round_510（25 条已锁 PLAN 未评估）指令其原样评估；round_511 VOID。pi round_106 STOP 中断后重启。教训：泄漏门"本地物理副本"的隔离靠目录约定，没有硬断言；任何对规范根的写路径都要在代码里被拒绝，不能只靠"不写"的约定。
- **E24（2026-09-20 15:30）** E23 的两个阻塞轮（Sonnet round_510/511，`n_gate_pass: null`）把主控三处打崩：验证器每 tick 重试（无入选/无 PLAN 时不写标记）、tick 的 `['n_gate_pass']` 取 null、穷尽守卫 `int(None)` 抛错导致 S2 穷尽宣布 5 分钟没被处理。修：验证器写 NOT_APPLICABLE 标记；tick 把 null 当 0；守卫只数"已评估轮"（n_gate_pass 非空且预注册 >0）做三零判定。守卫在 pi 线回归 REJECT（未穷尽）、Sonnet 线 OK。手动推进 Sonnet 到 S3（缺口重扫）。S2 结论：upside_tail 家族 178 条，入选 8，两窗口显著 1（VA3）；配对空间用尽，三轮零。

## 二十三、pi 第 17 阶段收口（round_095–114，2026-09-20 16:00）+ Sonnet S3 进行中
第 17 阶段 20 轮，volume_time_1m 8 原子 + pi 自建 overnight_structure_1d（E23 的起因）。主控验证的入选：DA2、CO09、CO35、CO36、CO43、CO44、CQ08、CR08、CT11、CU04、CY07、CY17、CZ01。两窗口显著 3 条：**CO36** `VT_AUTOCORR − VOL_SPIKE_FREQ`（审计 +47.7 / t 3.14）、**CR08** `VT_BUCKET_COUNT_SHIFT − OPEN30_VOL_SHARE`（+36.5 / 2.02）、**CZ01** `ON_PREM − BIGBAR_EDGE_CONC`（+55.2 / 2.76，2022 −0.1）。round_113 pi 提前宣布穷尽（三轮 1/0/0）被守卫驳回；round_114 以"合法配对枚举为零 + 连续两轮零"宣布，主控把这条合同替代条款写进守卫后放行，自动进第 18 阶段（午间休市）。
Sonnet S3（round_513–518）：GAP_SCAN_2 后建日内动量家族（Gao–Han–Li–Zhou 2018）。入选 11 条全是 OVERNIGHT_FIRST30_CORR / INTRADAY_MOM_CORR 换右腿，主控验证审计 t 0.5–1.9 无一显著（GHP11 1.91）；已指令停止同左腿重 skin。两条线同日独立汇到"隔夜结构"：pi 的 ON_PREM 系列审计强，Sonnet 的隔夜–首 30 分钟相关发现强审计弱。
队列：pi stage19/20/21（vol_of_vol、orderflow_persistence、scaling_memory）；Sonnet S4/S5/S6（jump_continuous_beta、microstructure_noise、permutation_entropy）。
可选口径调整（不阻塞）：同簇归一登记（rank corr ≥0.6 的入选并簇、只留审计 t 最高一条）——只改账本不改门。
- **E25（2026-09-20 17:10，工程一次性收口）** 今天 E20–E24 全是"两条线产物格式漂移 / 阻塞轮空值 / 路径写死 pi 线"在主控不同脚本里分别崩。不再逐个撞：新增 `audit/controller_selftest.py`，对两条线全部 224 个轮目录做模式校验（STATUS/PLAN/candidate_metrics/atom_health 含别名）、守卫、配对表、验证覆盖、引擎防护断言（E23）、规范数据根完整性（对 .staging）、队列深度、supervisor 心跳、tick 脚本编译与吞错扫描。挂进主控 tick 每小时跑一次，失败发飞书；tick 另加每次回填一个"验证器上线前的入选轮"。首跑发现：pi 早期 7 个入选轮（005–021）从未交叉验证——已回填，round_005/008/009/010/014/021 CONSISTENT，**round_018 C3 MISMATCH**（pi 当年引擎 发现 t 2.56 / 主控现引擎 2.21，审计 +22.8 vs +23.4）：版本漂移不是错判，C3 在现引擎下仍过门 7；标注 MISMATCH_VERSION_DRIFT。最终自检 0 失败。
- 同日常设口径（合同新行"配对纪律"）：同一左腿一阶段只配一批（≤8 条），同一右腿 ≤3 个左腿，剩余合法配对 <12 即穷尽，同簇只登记审计 t 最高一条。起因：S3 11 条、S4 13 条入选全是一个左腿换右腿（CONTINUOUS_BETA_60 × 13）。S4 主控验证：KR1 `CONTINUOUS_BETA_60 − RET_ACF1_5` 审计 +43.1 / t 2.12、KU2 `− KYLE_LAMBDA_20` +31.3 / t 2.15 两窗口显著，其余 t 0.6–1.4；单原子 JB2 只有 t 0.43，说明信息在右腿而非 beta。
- **回填修正（17:15）** round_021 也是 MISMATCH，且性质不同于 018：F1 `TICK_IMBALANCE − OPEN30_VOL_SHARE` 现引擎发现 t **1.65**（<2）、F2 `CLOSE5_DAY_CONSIST − PRICE_POSITION` 发现 t **1.97**（<2，审计 +52.6 / t 2.64 仍强）。两条在现行门 7（发现 block-t ≥2）下**不过发现门**——当年是门 7 v1 下入选的。账本处理：F1、F2 标 `ADMITTED_UNDER_V1_FAILS_CURRENT_DISCOVERY_GATE`，不再计入"两窗口显著"，前向账本保留记录但加标注；不重打其他早期轮（005–014 CONSISTENT）。这也是 E25 自检的直接收益：早期账本里有 2 条按现行门站不住的候选。
- **E26（2026-09-20 16:45，主控自身失误）** Sonnet round_530 只写 STATUS（status=STAGE_EXHAUSTED_PAIRING_DISCIPLINE）没写穷尽产物，我在工作进程还在跑时手工造标记并推进到 S5；工作进程随后自己写了穷尽产物和标记，把检查点又拨回 530/WAITING，下一 tick 会把 S6 也套上（双跳）。已归档重复标记、检查点拨回 531、重启。规则：supervisor 处于 RUNNING 且工作进程在跑时，主控不得手造穷尽标记；等它自己落地再处理。守卫已识别"配对纪律"条款，以后不需要手工接受。

## 二十四、Sonnet S5–S6 / pi 第 18–21 阶段（2026-09-20 17:00–17:50，配对纪律生效后）
配对纪律让每阶段 2–5 轮即穷尽（一族 ≤8 原子各配一批），两条线今天下午各推进 4 个阶段。主控验证：
- **Sonnet S6 排列熵：PA1 `PERM_ENTROPY_RET_20`（单原子）发现 +32.9 bp / t 3.59，审计 +52.4 bp / t 2.09（K=2 +60.5 / 2.07），2021/2023/2024 显著正、2022 +0.4、2025 −0.4；方向符合假设（路径有序 → 超额正）。与 1m 量通道原子 max rank corr 0.61。这是全线第一条不含成交量信息、两窗口显著的单原子。** 其余 S6 配对 t 0.4–1.0。
- Sonnet S5 微观结构噪声：MB8 `NOISE_VAR_CHG − WORST_DAY` 审计 +43.3 / t 1.89（差一点）；S10 量流积累/派发：5 条验证 t 0.6–1.4 无显著；S4 跳跃/连续 beta：KR1 +43.1 / 2.12、KU2 +31.3 / 2.15（簇 CONTINUOUS_BETA_60）。
- pi 第 18 阶段午间休市：CJ16 `LUNCH_POST_RUN − LOG_AMOUNT_VOL` +42.3 / 2.30、CK04 `LUNCH_PRE_RUN − CLOSE5_DAY_CONSIST` +53.0 / 2.72 两窗口显著，CK20 +38.8 / 1.99；第 19 阶段 vol-of-vol：CQ31、CR11 待验；第 20 阶段订单流持续性：CS01 t 0.64；第 21 阶段标度/长记忆进行中（CU02、CV19、CV20 待验）。
- 两窗口显著累计（主控验证、按现行门）：Z2、BB1、BIGBAR_VOL_SHARE_20、AI4、CA1、CO36、CR08、CZ01、VA3、CJ16、CK04、KR1、KU2、**PA1**。除 PA1 与 CZ01（隔夜溢价主腿）外全部含 1m 量 spike / 大 bar / 成交额波动腿。
可选口径调整（不阻塞）：无新增。
- **补记（18:20）** Sonnet S7 日内回撤：**QA8 `UNDERWATER_FRAC_CHG_20`（单原子，日内水下时间占比的 20 日变化）发现 +23.2 bp / t 2.35，审计 +60.6 bp / t 2.88，五年全正（1.5/2.1/0.8/2.2/2.6）**——第二条不含成交量的两窗口显著单原子，审计超额全线最高。S5 补验 MH3 `NOISE_VAR − ROLL_SPREAD` +39.5 / t 2.48；S8 KQ4 `CONTINUOUS_BETA_60 − MAX5_MEAN` +44.2 / t 2.29。主控验证两窗口显著累计 22 条（pi 14、Sonnet 8），其中不含量腿：CZ01（隔夜溢价）、PA1（排列熵）、QA8（日内回撤）。自检 18:20 全绿；工程无遗留。
- **pi 第 23 阶段（跨阶段顶级原子互配扫描，round_136–137）**：顶级 12 原子 29 个跨族未测对，21 条实测入选 1（CY09 `SCL_DFA_RET − VOL_SPIKE_FREQ`，仍含量腿），剩余 8 条受配对纪律封禁。结论按预案写入：顶级原子互配没有产生任何不含 1m 量腿的入选——"信息主要在 1m 量通道"在 pi 线成立；Sonnet 线的 PA1/QA8 是例外，故排第 27 阶段在 pi 工作区**独立复现**（不看 Sonnet 代码，只按文献定义），作为跨实现验证。第 24 阶段相对 tick 两轮穷尽：RT_REL_TICK/RT_ZEROBAR 与 ROLL_SPREAD/AMIHUD corr 0.82–0.84 被影子封禁，其余 4 原子配对入选 2 条待验。

## 二十五、跨线独立复现（pi 第 27 阶段，round_147，2026-09-20 19:05）
pi 在自己工作区按文献定义独立实现（代码与 Sonnet 两个家族文件只共享 15 行引擎模板样板，RPC 日志无一次引用 Sonnet 工作区）：
| 原子 | Sonnet（主控验证） | pi 复现（主控验证） |
|---|---|---|
| 排列熵 PERM_ENTROPY_RET_20 / RP_PERM_ENT_D3_20 | 发现 +32.9 / t 3.59；审计 +52.4 / t 2.09 | 发现 +32.9 / t 3.59；审计 +52.4 / t 2.09；逐年 t 完全一致 |
| 日内水下占比变化 UNDERWATER_FRAC_CHG_20 / RP_UW_CHG_20 | 发现 +23.2 / t 2.35；审计 +60.6 / t 2.88 | 发现 +23.2 / t 2.35；审计 +60.6 / t 2.88；逐年 t 完全一致 |
逐 bp 一致说明两套独立代码给出了逐日相同的 top-3 排序（rank 裁判对实现细节不敏感），两条不含成交量的单因子在跨实现下成立。附带：RP_UW_LVL_20（水下占比水平）发现 t 2.82、审计 +33.3 / t 1.26；d=4 变体与 d=3 影子近亲被正确拒；复现原子与 pi 已验证腿的 12 条配对 0 入选——信息在原子层已兑现，配量腿无增量。
可选口径调整（不阻塞）：无新增。
- **pi 第 29 阶段价格延迟（Hou–Moskowitz，round_149–151）**：主控验证 **DA57 `PD_D1_CHG_20 − AUC_VARIANCE_RATIO_20`（价格延迟 D1 的 20 日变化 − 开盘/收盘方差比）发现 t 3.29，审计 +43.7 bp / t 2.07——不含成交量的两窗口显著配对**；CZ60 `VT_BUCKET_GINI − PD_D1_CHG` 审计 +55.7 / t 2.72（带成交量时间腿）。PD_D1_CHG 成为新活原子（吸收速度变快 → 超额）。DA55/DA61 审计 t 0.26/0.96。第 30 阶段流动性动量 5 原子三轮穷尽，入选待验。Sonnet S11：MSPE_5M 单原子审计 t 1.25，`MSPE_15M − VOL_SPIKE` +41.8 / t 2.31。不含成交量的两窗口显著累计：CZ01、PA1、QA8、DA57。
- **Sonnet S12 日内痛苦/恢复（round_561–563）主控验证**：FC3 `UNDERWATER_FRAC_Z_60 − CATEGORY_DISPERSION` 审计 +37.6 / t 2.31；**FC8 `UNDERWATER_FRAC_Z_60 − PERM_ENTROPY_RET_20` 审计 +33.0 / t 2.17（发现 t 2.63）——两条不含成交量通道（回撤几何 × 路径复杂度）的第一条合成配对，两窗口显著。** S13 频域 beta 三轮零入选穷尽。不含成交量的两窗口显著累计 6：CZ01、PA1、QA8、DA57、FC3、FC8。S14（对称复现 pi 的 DA57/CZ01/CA1/CK04）进行中。

## 二十六、对称复现：Sonnet 独立实现 pi 的四条候选（S14，round_569，2026-09-20 19:50）
| pi 候选 | pi 主控数字 | Sonnet 独立实现 | 判定 |
|---|---|---|---|
| CK04 `LUNCH_PRE_RUN − CLOSE5_DAY_CONSIST` | +53.0 / t 2.72 | **+49.2 / t 2.30，入选** | 跨实现成立（差 3.8 bp） |
| DA57 `PD_D1_CHG − AUC_VARIANCE_RATIO` | +43.7 / t 2.07 | +29.5 / t 1.30，同号未过 t 门 | **实现敏感**（D1 的 60 日窗/滞后期/自由度细节），降为"单实现显著" |
| CA1 `PV_ELASTICITY_20` | +52.3 / t 2.75 | +34.6 / t 2.35 过门，但与 downside_risk 族原子 corr 0.76 被去重挑掉 | 效应同向存在；结构性发现：量价弹性与下行风险实质重叠 |
| CZ01 `ON_PREM − BIGBAR_EDGE_CONC` | +55.2 / t 2.76 | +6.8 / t 1.01 | **不可复现**：BIGBAR_EDGE_CONC（前 10% 大 bar × 首尾 30 分钟）依赖阈值与窗口选择；降为"实现特异"，从"不含成交量显著"名单移除（它本来含大 bar 腿） |
对照 pi 对 Sonnet 的复现（§25，两条逐 bp 一致）：**简单构造（排列熵、水下占比、午前抢跑量、尾 5 分钟一致度）跨实现稳；依赖阈值/窗口的构造（大 bar 边缘集中、价格延迟）跨实现不稳。** 这条规律以后写进家族设计：新原子优先无阈值定义。账本：CZ01、DA57 标 `SINGLE_IMPLEMENTATION_ONLY`；不含成交量且跨实现成立的 = PA1、QA8、CK04（半含量：午前量占比是量的时间分布，不是量水平）、FC3/FC8 待 pi 复现。
可选口径调整（不阻塞）：把"跨实现复现"作为认证前的必经步骤（目前只是主控加排的阶段）。
- Sonnet S15 相对篮子路径（round_571–573）：REL_MAXDD 单原子发现 t 2.76、审计 t 0.60；配对最高 NC1 `REL_MAXDD − OVERNIGHT_INTRA_DIFF` 审计 +28.3 / t 1.67。相对路径几何不如绝对路径（QA8）。round_570 Sonnet 空档自开的 money_flow_extremes 两条审计 t 0.5–1.0，族已关闭。S16（本线顶级原子互配）、S17（首达时间）、S18（无量原子跨线互配）已排。
- **pi 第 31 阶段无量通道加深（round_156，一轮 1 小时：样本熵/LZ 在 1m 上算量大）——结构性结论**：Lempel–Ziv 复杂度与排列熵 rank corr 0.93、样本熵与排列熵 0.97、日内溃疡指数与日区间 0.73，全部影子。独立切面只有回撤恢复时间（0.41 vs 水下水平）与溃疡变化（0.33），单原子审计 t ≤1.75，配对 CZ96 `VFP_RECOVERY − ON_PREM` 发现 t 2.84 / 审计 +21.2 待验。**无量通道到此只有两个独立维度：路径序数复杂度（排列熵一族）与水下/回撤占比（QA8 一族），加隔夜溢价与价格延迟两条实现敏感的腿。** Sonnet S11 同结论（MSPE 与 PERM_ENTROPY 同族）。设计规则补充：同一数学对象的不同估计量（熵/复杂度/分形维）在 14 只截面上不可区分，一族取一个即可。
- **E27（2026-09-20 21:05）** 第 31 阶段的样本熵/LZ 原子让主控交叉验证一轮要 15+ 分钟，tick 是串行的：20:45 那次 tick 卡在验证上（900 s 超时后又进回填验证），Dagu `max_active_runs: 1` 使后续 tick 全部排队，pi 第 31 阶段的穷尽标记在那里躺了 15 分钟没人推进（supervisor 心跳停 → 观察器 HEARTBEAT_STALE）。修：验证改为**脱离 tick 的后台进程**（每轮一个 pid 锁、3600 s 超时、日志落在轮目录），tick 只负责启动/收割，永远秒级返回；穷尽推进不再被验证阻塞。手动推进 pi 到第 32 阶段、Sonnet 到 S17。
- **Sonnet S16 本线顶级原子互配（round_575）主控验证：UE3 `YZ_OVERNIGHT_SHARE_20 − UNDERWATER_FRAC_CHG_20`（Yang–Zhang 隔夜方差占比 − 日内水下占比变化）发现 t 3.03，审计 +53.3 bp / t 3.08——两腿都不含成交量，全线审计 t 最高的配对；UE1 `YZ_OVERNIGHT_SHARE − MSPE_5M` +41.9 / t 2.09（亦无量）。** UD1/UG1 t 1.0–1.8。pi 第 31/32 阶段配对：CY95 `ON_PREM − RP_UW_CHG` 发现 t 3.58 / 审计 t 1.76；CZ136 `AUC_VARIANCE_RATIO − RCC_BB_SQUEEZE` t 1.08。S17 首达时间 4 轮入选 1 后穷尽。无量两窗口显著累计 8：PA1、QA8、FC3、FC8、UE3、UE1、CK04（半）、DA57（实现敏感）。隔夜方差占比（YZ_OVERNIGHT_SHARE）与隔夜溢价（ON_PREM）是"隔夜"维度的两个切面，与水下占比组合最强。

## 二十七、pi 复现 Sonnet 六条显著配对（第 33 阶段，round_162，2026-09-20 21:35）
| Sonnet 候选 | Sonnet 数字 | pi 独立实现 | 判定 |
|---|---|---|---|
| VA3 `BEST_DAY_60_XVOL − VOL_SPIKE_FREQ` | +34.3 / t 2.24 | **+32.4 / t 2.73 入选** | 跨实现成立 |
| NI1 `MFI_EXTREME_FRAC − VOL_USHAPE` | +43.6 / t 2.12 | **+55.9 / t 3.39 入选**（组合 IC +0.113） | 成立且更强 |
| KR1 `CONTINUOUS_BETA_60 − RET_ACF1_5` | +43.1 / t 2.12 | +12.4 / t 1.60 | pi 用 SIGN_ACF1_5 替代 RET_ACF1_5，不是同一右腿——复现无效，需重做 |
| KU2 `CONTINUOUS_BETA_60 − KYLE_LAMBDA_20` | +31.3 / t 2.15 | +10.1 / t 2.36（用 ROLL 替代 KYLE） | 同上，复现无效 |
| KQ4 `CONTINUOUS_BETA_60 − MAX5_MEAN_20` | +44.2 / t 2.29 | 未做（pi 把两腿判为同族） | 未复现 |
| MH3 `NOISE_VAR_20 − ROLL_SPREAD_20` | +39.5 / t 2.48 | +32.8 / t 1.18，identity 拒 | 幅度接近、t 不足；噪声方差归一化细节敏感 |
结论：无阈值构造（MAX、MFI 极值占比、VOL_USHAPE）再次跨实现成立；beta 系列的复现因 pi 换了右腿而无效（复现纪律：右腿必须按原定义实现，不得用"近似原子"替代——写进第 35 阶段与以后所有复现指令）。
- **Sonnet S18 无量原子跨线互配（round_581–582）**：16 条入选 1（ZA9 `ON_PREM − GAP_FILL_RATE`，审计 IC +0.045 待验）。Sonnet 独立实现的 PD_D1_CHG 发现 IC −0.006（无信号）——价格延迟变化第二次被判实现敏感，正式降为不可信；LUNCH_PRE_RUN 单原子过六门败在门 7。**结论：无量原子之间基本不互相增强**（S16 的 UE3/UE1 是例外，依赖隔夜方差占比这条腿）；无量通道的信息集中在 3–4 条单原子/单配对上，不是一个可扩展的族。
- **Sonnet S21 隔夜结构镜像（round_592–595）：HB1 `ON_SIGN_STREAK_20 − UNDERWATER_FRAC_CHG_20`（隔夜收益符号连续天数 − 日内水下占比变化）发现 t 3.19，审计 +56.5 bp / t 2.98，无量。** 这是"隔夜维度 × 水下占比"第三次组合出两窗口显著（UE3 隔夜方差占比、HB1 隔夜符号连续、pi 的 CY95 隔夜溢价 t 1.76）：隔夜行为与日内回撤几何是当前最稳的一对无量腿。S20 价格延迟镜像：4 轮入选 5 条审计 t 0.56–0.65，与 pi 结论一致，价格延迟（日频与 1m）正式关闭。无量两窗口显著累计 9。
- **Sonnet S22 午间休市镜像（round_596–599）**：LB7 `LUNCH_POST_RUN_20 − BEST_DAY_20` 审计 +36.5 / t 2.05（两窗口显著）；午前/午后抢跑量比单原子发现 t 3.53、审计 t 1.00；LA1 `抢跑比 − UNDERWATER_FRAC_Z` t 1.55。午后抢跑量占比（LUNCH_POST_RUN）在两条线独立实现下都出显著配对（pi CJ16、Sonnet LB7），午间族跨实现成立。
- **Sonnet S23 成交量时间下的回撤几何（round_600–602）**：VT_UNDERWATER_FRAC_20 与日历时间水下占比 corr <0.7（独立切面），WA1 `VT_UNDERWATER_FRAC_20 − MFI_EXTREME_FRAC_20` 发现 t 4.11、审计 +45.3 / t 2.15（两窗口显著，MFI 腿含量）；VT_MAXDD 与日历 MAXDD corr 0.93 影子。成交量时间只改变"回撤占比"这一个切面，其余是日历版的影子。pi 第 34 阶段首达时间：体检 8/8 干净（最大 corr 0.5），但每步计算 20–40 分钟，本阶段耗时将超 2 小时。
- **Sonnet S24 成交量时间镜像（round_603–）**：CO36 `VT_AUTOCORR − VOL_SPIKE_FREQ` 独立实现 +45.4 / t 3.63（pi +47.7 / t 3.14）——**跨实现成立**；CR08 `VT_BUCKET_COUNT_SHIFT − OPEN30_VOL_SHARE` 审计 +44.3 但发现 t 1.79 未过门，未复现。VT_AUTOCORR 簇代表 XB3 发现 t 5.48（待主控验证）。至此跨实现成立的两窗口显著：PA1、QA8、CK04、VA3、NI1、CO36（+ UE3/HB1/FC8 等 Sonnet 单实现待 pi 复现）。

## 二十八、Sonnet 重写 pi 量通道核心原子（S26R，round_612，2026-09-20 23:45）
主控用 `--all` 模式验证全部 11 条重写候选（R_ 版本与 pi 原版 rank corr 0.78–0.89，确为不同实现）：
| 构造 | pi 原版（主控验证） | Sonnet 重写 R_ 版 | 判定 |
|---|---|---|---|
| BIGBAR_VOL_SHARE_20（大 bar 量占比，单原子） | +41.6 / t 2.26 | **+53.2 / t 2.67** | 成立 |
| VOL_SPIKE_FREQ_20（量 spike 频率，单原子） | +50.7 | +10.4 / t 0.62 | **不成立** |
| Z2 大 bar 方向偏度 − 量自相关 | +49.2 / t 3.02 | +13.3 / t 0.57 | 不成立 |
| CO36 成交量时间自相关 − 量 spike | +47.7 / t 3.14（S24 用 pi 原版 spike 腿：+45.4 / t 2.63） | +22.9 / t 1.56 | 减半 |
| BB1 量 spike − 溃疡 | +36.3 / t 2.46 | +23.4 / t 1.25 | 减半 |
| AI4 跳空回补 − 量 spike | +42.7 / t 2.58 | +20.2 / t 1.24 | 减半 |
**但**：S26R 用的是主控转述的定义（前 10% bar / 均值+3σ / 正比例−0.5），事后核对 pi 代码，实际定义是"成交额 > 当日中位数×5 判大 bar；spike = 成交量 > 中位数×5 的 bar 占比；方向偏度 = 大 bar 买卖量差/总量（tick rule）"。所以本轮检验的是**阈值/定义敏感性**：换一种合理的 spike 定义，量 spike 腿的信息掉一半到全部；只有"大 bar 量占比"对定义不敏感。已排 S26R2 用 pi 精确定义再复现一次，区分"同定义独立代码是否一致"与"定义敏感"。无论结果如何，账本规则：含 VOL_SPIKE_FREQ 腿的候选标 `DEFINITION_SENSITIVE`，等 S26R2。

## 二十九、Sonnet S27 隔夜×日内回撤机制原子（round_614–616，2026-09-21 00:05）
按 UE3/HB1 指向的机制建单原子（无阈值）：GAP_DD_CONSUMPTION_RATIO_20（隔夜跳空被日内最大回撤吃掉的比例）单原子发现 IC −0.085 / 审计 −0.071，与现有原子 max corr 0.645（独立切面）。主控验证：**S27B5 `GAP_DD_CONSUMPTION_RATIO − MFI_EXTREME_FRAC` 发现 t 3.16，审计 +58.3 bp / t 3.89——全线审计 t 最高**（MFI 腿含量）；S27D5 `ON_STREAK_UF_COV − SAMPEN_RET` +41.3 / t 2.34（无量）；S27B2 +29.8 / t 1.91、S27D1 +37.5 / t 1.94 差一点。机制原子比换搭档配对更有效：一轮新构造出 1 条 t 3.89 + 1 条 t 2.34，而 S18/S25 的原子互配两阶段合计 0 条显著。设计规则再补一条：**有了显著配对后，下一步是把配对暗示的机制写成单原子，而不是继续配对。**

## 三十、S26R2：用 pi 精确定义的独立代码复现量通道核心（round_617，2026-09-21 00:15）
| 构造 | pi 原版 | S26R（转述定义） | S26R2（精确定义、独立代码） | 判定 |
|---|---|---|---|---|
| VOL_SPIKE_FREQ_20 单原子 | 审计 +50.7 | +10.4 / t 0.62 | **+46.6 / t 2.36**（发现 t 0.69） | 审计期成立，发现期不稳 |
| BB1 spike − 溃疡 | +36.3 / t 2.46 | +23.4 / t 1.25 | **+35.0 / t 2.30** | 成立 |
| Z2 大 bar 方向偏度 − 量自相关 | +49.2 / t 3.02 | +13.3 / t 0.57 | **+44.2 / t 2.50**（发现 t 1.07） | 审计期成立，发现期不稳 |
| CO36 VT 自相关 − spike | +47.7 / t 3.14 | +22.9 / t 1.56 | +32.2 / t 1.89 | 减弱 |
| AI4 跳空回补 − spike | +42.7 / t 2.58 | +20.2 / t 1.24 | +19.2 / t 1.09 | 不成立 |
| BIGBAR_VOL_SHARE_20 单原子 | +41.6 / t 2.26 | +53.2 / t 2.67 | +36.9 / t 1.85 | 成立（幅度对定义不敏感） |
结论：**量 spike 通道是真实的但定义敏感**——同一文字定义下独立代码能复现审计期超额（spike、BB1、Z2 审计 t 2.3–2.5），换一种合理定义（均值+3σ / 前 10%）信息掉一半到全部；发现期数字对实现细节更敏感（R2 有效日 508 vs 579，中位数法需要更长历史）。AI4 与 CO36 在任何重写下都减弱，降为单实现。账本规则落地：含 spike 腿的候选标 `DEFINITION_SENSITIVE_REPLICATES_AUDIT`；AI4 标 `SINGLE_IMPLEMENTATION_ONLY`。跨实现成立总表（两线独立代码、审计 t ≥2）：PA1、QA8、CK04、VA3、NI1、CO36（S24 版）、BB1、Z2（审计）、BIGBAR_VOL_SHARE、VOL_SPIKE_FREQ（审计）。
- **S28 第三批复现（round_618）**：CJ16 `LUNCH_POST_RUN − LOG_AMOUNT_VOL` 独立实现审计 +40.8 / t 2.04（pi +42.3 / 2.30）**成立**；CK20 `LUNCH_GAP − ULCER` +38.8 / t 1.99（pi +38.8 / 1.99）成立；CQ31（HAR 残差 − 量价弹性）审计 t 0.88（pi 2.03）不成立；CN08、CZ60、CO09 不成立（含成交量时间 Gini 或价格延迟腿）。午间族两条再次跨实现成立。
- **E28（2026-09-21 00:30）** Sonnet 在"只此一轮"阶段结束后不写穷尽产物，只写 STATUS=QUEUE_EMPTY，supervisor 每分钟重新调用一次空转（round_619–623 五轮，每轮约 $0.3）。修：supervisor 把 QUEUE_EMPTY / STAGE_COMPLETE / STAGE_EXHAUSTED 状态视为穷尽（合成产物→标记→主控推进）。SIGTERM 修复（E20）已验证生效：supervisor 收到信号立即写 STOPPED 退出。
- **pi 第 34 阶段首达时间（round_164，历时 2.5 小时：体检 37 分钟、评估两次共 65 分钟）**：8 原子体检全独立（corr ≤0.5）但单原子 8/8 门 7 不过（FP_FALSE 假突破率审计 IC +0.039 最强）；配对 19 条入选 1（DB09 `FP_UP − RP_UW_CHG`，审计 IC +0.077，待验）。Sonnet S17 同族 4 轮入选 1 亦弱。**首达时间在两条线上都不是有效通道**；同时首次记录：按日循环的原子计算成本（每步 20–40 分钟）× 会话压缩打断 = 一个阶段 2.5 小时，占今天 pi 全部时间的 1/6，产出 1 条弱候选。规则：新族预估单步 >10 分钟的，先用 3 只 ETF × 1 年做小样本试算，再决定是否全量。
- **Sonnet S29 机制原子第二批（round_625–626）主控验证**：S29P10 `REL_UNDERWATER_CATEGORY_20 − R_LOG_AMOUNT_VOL_20`（相对同类别的水下占比 − 成交额波动）审计 **+66.8 bp / t 2.84**（全线审计超额新高）；S29Q1 `UNDERWATER_FRAC_CHG_20 − MFI_EXTREME_UNDERWATER_SKEW_20`（水下占比变化 − MFI 极值发生在回撤中的偏度）发现 t 3.60，审计 +58.0 / t 3.44。注意：REL_UNDERWATER_CATEGORY 与 UNDERWATER_FRAC corr 0.82、MFI_EXTREME_UNDERWATER_SKEW 与 A/D 族 0.74——两条都是"水下占比 × MFI/成交额"同一机制的更好切面，簇归一后与 S27B5、WA1 同簇。机制原子两轮出 3 条 t>2.8，方向确认：**回撤中的量能极值**是当前最强机制（含量），**隔夜×回撤**是最强无量机制。
- **Sonnet S30 pi 配对的机制原子（round_627–628）**：pi 侧配对暗示的机制写成单原子后无一过门：VT 自相关高低活动日之差、午前/午后抢跑与方向一致率、HAR 残差分半的量价弹性差，单原子 IC 0.01–0.04；首 30 分钟桶占比与既有量分布原子 corr 0.84（影子）。配对 S30P11 审计 +35.4 / t 1.65、S30Q8 t 0.68。**机制原子规则有边界：它对"回撤×量能极值"和"隔夜×回撤"有效，对 pi 量通道的配对（spike/成交量时间/午间）无效——后者的信息本来就在原子层，配对只是去重后的残余。** pi 第 37 阶段同一任务在跑，可对照。
- **pi 第 34 阶段首达时间配对主控验证**：DB09 `FP_UP_20 − RP_UW_CHG_20`（触及 +1σ 的首达 bar 数 − 水下占比变化）审计 +31.9 / t 2.06（两窗口显著，无量）；DB22 t 1.12、DB43 t 0.27。首达时间族唯一站住的仍是与水下占比变化的组合——**水下占比变化（QA8 一族）作为右腿与几乎任何路径原子配都能出 t≈2，它本身就是主信号**，配对的增量要靠簇归一剔除。Sonnet S31 跳空吸收：S31Q16 `PV_ELASTICITY − GAP_FILL_TIMING` 审计 t 1.55、S31P7 t 0.72，通道加深无效。
- **Sonnet S32 同类别相对几何（round_631）**：7 个"相对同类别"原子里 6 个与绝对版 corr 0.87–0.93（影子）——14 只里类别内只有 2–4 只，减类别均值几乎不改变排序；S29P10 的强结果来自 REL_UNDERWATER_CATEGORY 恰好落在 0.82（勉强独立）。唯一独立的是相对水下占比的变化（corr 0.30，IC −0.069/−0.064）。**类别内相对不是一个新参照系，是绝对版的影子**；S29P10 归入水下占比簇。
- **Sonnet S32 唯一独立原子的配对主控验证**：S32P1 `rank(REL_UNDERWATER_CATEGORY_CHG_20)` 发现 t 2.23，审计 **+58.6 bp / t 3.10，逐年同号**——相对同类别水下占比的**变化**（唯一非影子原子）配对出全线第三高的审计 t；S32P12 t 1.24。归入水下占比簇（左腿是 QA8 一族的类别相对变体）。
- **Sonnet S33 回撤段量能（round_632）主控验证**：新原子发现期强（RECOVERY_VOL_SHARE_EXCESS 单原子发现 t 3.22）但审计期塌（t 0.36）；S33P6 `DD_RET_VOL_CORR − PV_ELASTICITY`（回撤段量价相关 − 量价弹性）审计 +35.0 / t 2.01 勉强两窗口；其余 t 0.3。**"回撤段放量"这条比"MFI 极值在回撤中"弱得多**：S29Q1 的信息在 MFI 极值的位置，不在成交量份额。S34（稳健性剖面，只报不改门）已开始。

## 三十一、顶级簇稳健性剖面（Sonnet S34，round_633，只报不改门，2026-09-21 02:15）
15 条簇代表在主参数（K=3、H=5）外的表现（审计期 2024-01→2025-04，block-t）：
| 候选 | K3H5 bp/t | K2 t | K4 t | H10 bp/t | H20 bp/t | 逐年 t 21/22/23/24/25 | 子期 t | top-3 日均交集 |
|---|---|---|---|---|---|---|---|---|
| S27B5 | 58.3/3.89 | 4.76 | 3.02 | 113.6/4.41 | 229.7/6.15 | 1.5/1.1/3.6/4.3/0.3 | 2.63/2.91 | 2.63 |
| S29Q1 | 58.0/3.44 | 3.36 | 2.91 | 92.6/3.90 | 150.2/3.81 | 4.1/1.6/1.8/2.7/0.8 | 1.30/3.72 | 2.38 |
| UE3 | 53.3/3.08 | 3.17 | 2.09 | 93.9/3.24 | 168.2/4.35 | −0.2/3.0/1.7/2.3/0.4 | 1.35/2.86 | 2.43 |
| HB1 | 56.5/2.98 | 3.26 | 1.84 | 97.6/3.66 | 145.1/3.80 | 1.3/3.0/1.3/2.1/0.6 | −0.61/3.75 | 2.39 |
| QA8 | 60.6/2.88 | 2.63 | 2.71 | 112.3/3.54 | 160.8/3.89 | 1.5/2.1/0.8/2.2/1.0 | −0.28/3.53 | 2.39 |
| S29P10 | 66.8/2.84 | 3.13 | 2.97 | 95.6/2.57 | 87.3/1.73 | 2.5/0.6/2.1/2.5/−0.8 | 1.22/2.91 | 2.54 |
| XB1 | 45.4/2.63 | 2.32 | 3.28 | 105.2/3.71 | 236.4/5.12 | 1.6/1.2/3.7/2.1/−0.8 | 2.38/1.72 | 2.68 |
| MH3 | 39.5/2.48 | 2.09 | 1.65 | 58.6/2.44 | 61.4/1.46 | 2.1/1.6/2.3/2.1/1.9 | 0.99/2.02 | 2.30 |
| XC5 | 45.4/2.27 | 1.17 | 2.54 | 55.8/1.59 | 47.1/0.78 | −0.3/0.5/2.8/2.4/0.2 | 2.25/1.04 | 2.53 |
| VA3 | 34.3/2.24 | 2.10 | 2.27 | 65.4/2.69 | 120.8/3.30 | 1.7/0.0/2.3/2.1/−0.1 | 0.85/1.87 | 2.71 |
| WA1 | 45.3/2.15 | 1.89 | 2.25 | 89.7/2.68 | 179.4/3.71 | 1.9/1.2/4.5/2.1/0.2 | −0.27/2.49 | 2.62 |
| KU2 | 31.3/2.15 | 1.74 | 2.14 | 64.7/2.96 | 104.6/3.42 | 3.3/0.7/1.9/3.9/−2.0 | 3.83/0.12 | 2.50 |
| NI1 | 43.6/2.12 | 2.47 | 2.20 | 107.6/3.60 | 243.7/5.17 | 1.1/0.9/3.6/2.4/−1.2 | 0.88/1.91 | 2.74 |
| PA1 | 52.4/2.09 | 2.07 | 2.28 | 114.7/3.05 | 233.8/4.72 | 1.9/0.4/4.3/2.8/−1.9 | 0.86/1.81 | 2.89 |
| LB7 | 36.5/2.05 | 1.27 | 1.55 | 80.1/2.74 | 111.3/2.27 | 0.7/−0.1/3.0/1.9/−1.6 | 2.26/0.78 | 2.60 |
读数（只报不改门）：
- **持有期越长超额越大**：13/15 在 H=20 的 t 高于 H=5，S27B5/XB1/NI1/PA1 H=20 超额 230–244 bp、t 4.7–6.2——这些是慢信号，5 日裁判低估了它们；XC5、MH3、S29P10 是例外（H=20 衰减）。
- **K 稳健**：多数 K=2/K=4 与 K=3 同量级；HB1、XC5、LB7、KU2 在 K=2 或 K=4 上跌破 2。
- **2025 年（1–4 月）普遍弱**：15 条里 2025 t>1 的只有 MH3、QA8；PA1/NI1/LB7/KU2 为负。2025 是审计期最后 4 个月，样本 80 个交易日，不足以判定失效，但要盯前向账本。
- **子期**：2024 下半–2025Q1 多数强于 2024 上半（HB1/QA8/WA1 上半为负）；KU2/LB7/XC5 反之。
- **换手**：top-3 日均交集 2.3–2.9（每日换 0.1–0.7 只），PA1 最稳（2.89）、MH3 最勤（2.30）。
- **簇结构**（rank corr ≥0.6）：{QA8, UE3, HB1, S29Q1}（水下占比变化簇）、{PA1, WA1, NI1, S27B5, S29P10}（排列熵–MFI–水下水平簇，0.6–0.7）；其余相互独立。按簇归一，独立代表 ≈ 7：S27B5、QA8、PA1、XB1、MH3、XC5、VA3/KU2/LB7 三条弱独立。
可选口径调整（不阻塞）：H=10 或 H=20 作为并列主参数登记（不改门，只多记一列）。
- **Sonnet S35 首达前回撤机制原子（round_634）**：5 原子 IC 0.03–0.05，与水下占比 corr 0.54–0.69，15 条 0 入选，一轮穷尽。首达时间这条在两线三次尝试（pi 第 34、Sonnet S17、S35）后关闭。
- **Sonnet S36/S37**：S36 合成机制原子（隔夜条件下的回撤量能）一轮入选 1（S36P11 审计 t 1.88）；S37 MFI 极值时点结构 5 原子 IC 0.01–0.05（谷底前后偏度最强 −0.049），一轮入选 1 待验。"MFI 极值在回撤中"这一机制的信息已被 S29Q1 一条原子吃尽，位置/时点的进一步切分不再增加。含量机制通道到此收口；S38–S40 为复现与账本轮。
- **DB09 跨线复现（S38，round_637）**：Sonnet 线的 FP_UP 与 UNDERWATER_FRAC_CHG 早在 S17/S7 按文献独立实现，同一配对在 round_577 已测过：审计 +31.9 bp 与 pi 逐 bp 一致（发现 t 2.69 vs 2.06），当时因与 UE3 rank corr 0.77 被去重挑掉。判定：跨实现成立，归入水下占比变化簇。这也说明两线独立实现的首达时间与水下占比原子在数值上高度一致——无阈值构造的跨实现稳定性再次得到印证。

## 三十二、全部入选候选的 H=10/20 剖面（Sonnet S39，round_638，只报不改门，2026-09-21 03:00）
对 164 条 gate_pass 候选（Sonnet 工作区含 pi 早期轮的拷贝，同一引擎）在 K=3 下算 H=10/20 审计 block-t：
- **全视界（H=5/10/20 都 t≥2）23 条**：S27B5（6.15@H20）、AI4（5.56）、BB1（5.36）、NI1（5.17）、XB1（5.12）、PA1（4.72）、BIGBAR_VOL_SHARE（4.58）、UE3（4.35）、QA8（3.89）、HB1（3.80）、DC7、WA1、KU2、CB1、VA3、UE1、DA6、EA5、KR1、LB7……
- **慢信号（H=5 t<2 但 H=20 t≥2）40 条**：含 Z2（1.66→2.48）、C3（1.21→3.91）、BIGBAR_EDGE_CONC（1.84→5.07）、AI1（1.17→3.81）、AI6、WJ4、GHP3、VB8……
- **只有短期（H=5 显著、H=20 t<1）1 条**。
读数：H=20 上 t≥2 的候选 63 条，H=5 上 24 条——**5 日主参数系统性低估了这批因子，几乎所有信号在 20 日视界更强，没有"短期特有"的信号**。这与 14 只 ETF 的轮动特性一致（截面排序变化慢，top-3 日均只换 0.1–0.7 只）。
可选口径调整（不阻塞，第三次记录）：门 7 主参数 H=5 → 并列 H=20（或以 H=20 为主、H=5 为辅）；审计 ≥5 bp 门在 H=20 下应等比放大。不改门，只记。

## 三十三、Sonnet 簇归一账本（S40，round_639，只报不改门）
41 簇。方法缺陷先记：单链接 0.6 把 87 条候选串成一个巨簇（QA8/PA1/UE3/S27B5/S29Q1/WA1… 全被链式并入 GAP_DD_CONSUMPTION 簇），其余 40 簇几乎都是单成员——单链接在 0.6 上链式合并过度，S34 的两两矩阵显示真实结构是"水下变化簇 + 排列熵–MFI 簇 + 若干独立"。已排 S43 用平均链接 0.7 重做。账本可用部分：单成员簇里 H=20 显著而 H=5 不显著的候选（NI8 MFI×DEP_DRIFT 3.34、DA8 SAMPEN×LBAR 3.81、MB8 3.14@H10、S27C7 3.01、S31Q16 3.09）与 §32 慢信号名单一致。跨实现状态列按 §25–§30 登记（成立：S27B5 簇代表、CK04、KU2 簇、PV_ELASTICITY；其余单实现）。
- **pi 第 35 阶段复现 FC3/FC8（round_167，主控 --all 验证）**：FC3 `UNDERWATER_FRAC_Z_60 − CATEGORY_DISPERSION` pi 独立实现 +25.7 / t 1.92（Sonnet +37.6 / t 2.31）；FC8 `− PERM_ENTROPY_RET` +25.0 / t 1.70（Sonnet +33.0 / t 2.17）。同向、幅度减 1/3、t 掉到门下——水下占比的 **60 日 z 分数**比水下占比的**20 日变化**（QA8，逐 bp 复现）实现敏感（z 的窗口/标准化细节）。FC3/FC8 标 `REPLICATES_DIRECTION_ONLY`。pi 多配的 10 条非任务腿最高 DC11 `PV_ELASTICITY − UW_Z` t 1.84，无新增。KR1/KU2/KQ4 补做排在 round_168。
- **pi 第 35b 阶段：按原定义补做 Sonnet 的 beta 系列（round_168，主控 --all 验证）**：R_KR1 审计 +28.5 / t 1.13（Sonnet +43.1 / 2.12）、R_KU2 +0.5 / t 0.03（+31.3 / 2.15）、R_KQ4 +14.1 / t 0.73（+44.2 / 2.29）、连续 beta 单原子发现 t 2.52 / 审计 t 0.09。**Sonnet S4 的连续 beta 簇（KR1/KU2/KQ4）全部不可复现**，标 `SINGLE_IMPLEMENTATION_ONLY`；连续 beta（4σ 截断 + 日内回归）是又一个定义敏感构造。跨实现成立总表（两线独立代码、审计 t≥2）维持 12 条：PA1、QA8、CK04、VA3、NI1、CO36、BB1、Z2（审计）、BIGBAR_VOL_SHARE、VOL_SPIKE_FREQ（审计）、CJ16、CK20；加"仅方向复现"：FC3、FC8、DA57、DB09（成立，数值一致）。
- **Sonnet S41/S42 主控验证**：S41 隔夜分布形状一轮穷尽，S41P5 `OVERNIGHT_KURTOSIS − MFI_EXTREME_FRAC` 审计 t 0.99——隔夜分布形状无增量。S42 无量互配第二轮：S42P17 `UNDERWATER_FRAC_CHG − UNDERWATER_FRAC_Z_60` 审计 +45.5 / t 3.14（两腿同一对象的变化与水平，属簇内组合，登记但不算新信息）；S42P10 `UNDERWATER_FRAC_Z_60 − GAP_DD_CONSUMPTION_RATIO` +35.9 / t 2.37（无量，水下 × 跳空吃掉比例）；S42P14 t 1.19、S42P9 t 1.00。**无量原子互配第二轮的结论与第一轮一致：能出显著的组合都落在"水下占比 × 隔夜/跳空"这一个机制上。**
- **簇归一账本 v2（S43，round_643，平均链接）**：0.7 阈值下 135 条入选全部独立成簇——证明去重门（rank corr ≥0.7 拒）按设计工作，入选集合内部两两 |corr| <0.7；0.6 阈值下 93 簇，中等相关分组只有 2–5 成员（YZ_OVERNIGHT_SHARE 簇 4、CONTINUOUS_BETA 簇 5、VT_UNDERWATER 簇 3）。所以"簇归一"在 0.7 口径下不改变账本；有意义的归并是**机制层**（水下占比 × 隔夜/跳空/MFI 这类同机制不同切面），不是相关层。账本的"跨实现状态"列是 Sonnet 按 S43 时点填的，KU2/WJ4/GW9 标"成立"与 §35b 结论（beta 簇不可复现）不一致，以 §25–§35b 为准。
- **pi 第 36 阶段无量原子互配（round_169）**：18 条入选 2，均为 PD_D1_CHG（已判定义敏感）配腿，审计 t 0.89/1.44。与 Sonnet S18/S42 一致：pi 侧无量原子互配也无增量。S46 排定后，pi 全部两窗口显著候选在 Sonnet 都会有一次独立实现。

## 三十四、只被门 7 拒绝的候选在 H=20 下的剖面（Sonnet S44，round_644，只报不改门，2026-09-21 03:45）
样本：Sonnet 线 round_500 起 541 条"其余六门都过、只败在门 7（H=5 top-3）"的候选。H=20 两窗口（发现 + 审计）block-t 都 ≥2 的有 **80 条（14.8%）**，其中 **43 条两腿都不含成交量水平**，11 条与已入选簇代表 rank corr ≥0.7（同簇变体），**69 条是与现有入选簇不重叠的独立候选**。头部：
| 候选 | 表达式 | H5 t | H20 发现 t/bp | H20 审计 t/bp | 含量 |
|---|---|---|---|---|---|
| MB2 | NOISE_VAR_CHG × VOL_SPIKE_FREQ | 1.34 | 3.67/84 | 5.52/254 | 是 |
| PB5 | PERM_ENTROPY_RET × LOG_AMOUNT_VOL | 1.10 | 2.87/75 | 5.31/239 | 是 |
| PH1 | CEP_DISTANCE × CLOSE5_DAY_CONSIST | 1.72 | 4.15/94 | 4.83/180 | 否 |
| UB3 | PERM_ENTROPY_RET × YZ_OVERNIGHT_SHARE | 0.90 | 4.27/103 | 4.78/190 | 否（同簇） |
| BA7 | BB_WIDTH_CHG × SAMPEN_RET | 1.50 | 3.19/71 | 4.70/177 | 否 |
| KB8 | COHERENCE_LF_HF_DIFF × LZ_COMPLEXITY | 2.08 | 3.23/59 | 4.67/203 | 否 |
| S30Q5 | YZ_OVERNIGHT_SHARE × PM_POSTRUN_DAY_CONSIST | 0.70 | 2.50/55 | 4.34/142 | 否 |
读数：与 §32 合并，**H=5 主参数在这条线上系统性地漏掉了一批 20 日视界上强得多的信号**（入选 164 里 63 条 H=20 显著；拒绝 541 里 80 条 H=20 两窗口显著）。这不是某一族的问题，是 14 只 ETF 轮动的时间尺度问题：截面排序变化慢（top-3 日均换 0.1–0.7 只），5 日前向收益的信噪比天然低于 20 日。
**可选口径调整（不阻塞，第四次记录，建议 USER 决定）**：门 7 增设 H=20 并列主参数（门：发现 block-t ≥2、审计 ≥20 bp 且 t ≥2，两窗口），H=5 保留；已拒绝的 80 条按 H=20 门重打入账。主控不改门；两线继续按现行门挖。
- **S45 精确定义复现 pi 隔夜族（round_645，--all 验证）**：CZ01 `ON_PREM − BIGBAR_EDGE_CONC` 精确定义版审计 **+39.4 / t 2.09**（pi +55.2 / 2.76；S14 转述版 +6.8 / 1.01），发现 t 1.42——同 §30 的模式：审计期在精确定义下复现、发现期不稳；CZ01 从"不可复现"改标 `DEFINITION_SENSITIVE_REPLICATES_AUDIT`。CY07 `ON_PREM − OPEN30_VOL_SHARE` 发现 t 4.50 / 审计 +32.4 t 1.62（pi +28.9 / 1.41）一致；CY17 减弱。大 bar 边缘集中单原子 t 0.86、隔夜溢价单原子 t 0.07——两条腿单独都没信息，组合才有，是"配对而非原子"的信号。
- **S46 精确定义复现 CR08/CM06（round_646，--all 验证）**：CR08 `VT_BUCKET_COUNT_SHIFT − OPEN30_VOL_SHARE` 精确定义版发现 t 2.66、审计 **+40.4 / t 2.11**（pi +36.5 / 2.02；S24 自实现版发现 t 1.79 未过）——**跨实现成立**；CM06 `LUNCH_GAP − AUC_VARIANCE_RATIO` +30.6 / t 1.70（pi +34.9 / 1.98）同向一致、门边。至此 pi 全部两窗口显著候选都在 Sonnet 有过独立实现。**跨实现成立总表 13 条**：PA1、QA8、CK04、VA3、NI1、CO36、BB1、Z2（审计）、BIGBAR_VOL_SHARE、VOL_SPIKE_FREQ（审计）、CJ16、CK20、CR08；审计期复现/定义敏感：CZ01；仅方向：FC3、FC8、CM06、DA57；不成立：AI4、CQ31、KR1/KU2/KQ4、CN08、CZ60。
- **pi 第 37 阶段机制原子（round_172）**：6 个机制原子体检全独立（max corr 0.14–0.66）。**MA_GAP_DD_EAT（跳空被日内最大回撤吃掉的比例，pi 按定义独立实现）单原子入选，发现 IC −0.108 / 审计 −0.086**（Sonnet 的 GAP_DD_CONSUMPTION_RATIO：−0.085 / −0.071）——两线独立实现的同一机制原子在原子层一致；MA_LUNCH_DIR_BET（午后抢跑押对方向）− RESILIENCY 亦入选。主控验证在跑。对照 Sonnet S30（pi 配对的机制原子全不过门）：pi 侧写出的机制原子里，来自"隔夜×回撤"的成立，来自量通道配对的（VT 活动分半、HAR 分半）体检独立但未入选——与 §29/§30 的边界结论一致。
- round_172 主控验证：MA_GAP_DD_EAT 单原子发现 +29.7 / t 2.32、审计 +27.2 / t 1.06；MA14 审计 t 0.86。与 Sonnet 一致：跳空被回撤吃掉比例**单原子**过门不显著，它的强度只在与 MFI 极值占比配对时出现（S27B5 t 3.89）——pi 第 38 阶段会按定义复现 S27B5，是最后一个关键验证。
- **pi 第 36/37 阶段主控验证补记**：DD48 `VFP_ULCER_SHIFT_20 − RP_UW_CHG_20`（溃疡变化 − 水下占比变化，两条回撤几何原子）审计 **+64.0 / t 3.64**——pi 线审计超额新高，但两腿同机制，属水下占比簇内组合（对应 Sonnet S42P17 +45.5 / t 3.14）；DD49 `RP_UW_CHG − LUNCH_PRE_RUN` +39.5 / t 2.05；MA27 `RP_PERM_ENT_D3 − MA_LUNCH_DIR_BET`（排列熵 − 午后抢跑押对方向）+47.1 / t 2.12，机制原子作右腿的首条显著。回撤几何簇在两线都是最强无量簇，簇内不同切面互配能把审计 t 推到 3+，但不是新信息。

## 三十五、pi 按定义复现 Sonnet 五条最强候选（第 38 阶段，round_174，2026-09-21 04:25）
| Sonnet 候选 | Sonnet 主控数字 | pi 独立实现（主控 --all 验证） | 判定 |
|---|---|---|---|
| **S27B5** 跳空被回撤吃掉比例 − MFI 极值占比 | +58.3 / t 3.89 | **+50.8 / t 3.49**（发现 t 3.06） | **跨实现成立**——全线最强候选站住 |
| **S29P10** 相对同类别水下占比 − 成交额波动 | +66.8 / t 2.84 | **+47.4 / t 2.62**（发现 t 3.23） | 跨实现成立 |
| **HB1** 隔夜符号连续 − 水下占比变化 | +56.5 / t 2.98 | +46.4 / t 3.28（发现 t 1.20） | 审计期成立，发现期不稳 |
| UE3 隔夜方差占比 − 水下占比变化 | +53.3 / t 3.08 | +33.4 / t 1.73（发现 t 0.88） | 减弱（Yang–Zhang 隔夜份额实现敏感） |
| S29Q1 水下变化 − MFI 极值在回撤中的偏度 | +58.0 / t 3.44 | +11.7 / t 0.60 | 不成立（"极值在水下时段"的判定实现敏感） |
结论：**"隔夜跳空被日内回撤吃掉 × MFI 极值占比"（S27B5）与"相对同类别水下占比 × 成交额波动"（S29P10）在两条线独立代码下都两窗口显著，是本线迄今最可信的两条**；HB1 审计期成立。跨实现成立总表 **15 条**：PA1、QA8、CK04、VA3、NI1、CO36、BB1、Z2（审计）、BIGBAR_VOL_SHARE、VOL_SPIKE_FREQ（审计）、CJ16、CK20、CR08、**S27B5、S29P10**；审计期复现：CZ01、HB1；仅方向：FC3、FC8、CM06、DA57、UE3；不成立：AI4、CQ31、KR1/KU2/KQ4、CN08、CZ60、S29Q1。
- **Sonnet S47 从 H=20 名单头部抽机制原子（round_647）主控验证**：S47D3 `OVERNIGHT_SHARE_PMCONSIST_SPLIT − MFI_EXTREME_FRAC`（隔夜方差占比高低日的午后押方向一致率之差 − MFI 极值占比）审计 +36.6 / t 2.31 两窗口显著（含量腿）；S47B3 +28.3 / t 1.74；带宽×样本熵系列 t 0.2–0.6。把 H=20 才显著的配对写成机制原子后，1/4 在 H=5 门下站住——H=20 信号有一部分能被机制化拉回 5 日视界，多数不能。
- **Sonnet S48 隔夜×水下协变单原子（round_649–650）**：把配对关系直接写成滚动相关，6 个原子 IC 0.00–0.04，几乎无信号；S48C2 `隔夜方差占比–水下相关_60 − CONTINUOUS_BETA` 审计 +56.7 / t 2.30（beta 腿不可复现，打折）。**"配对即机制"不能写成两腿的滚动相关**——rank 差捕捉的是截面上"隔夜行为强而回撤弱"的 ETF，不是两者在时间上的协变。机制原子规则的第二条边界。
- **pi 第 39 阶段 H=10/20 剖面（round_175，只报不改门）**：pi 线 round_012 起入选 99 条：慢信号（H5 t<2、H20 t≥2）30 条、只有短期 1 条、全视界 22 条；仅门 7 拒的 464 条里 H=20 审计 t≥2 且 ≥5 bp 的 120 条（单窗口口径，比 Sonnet 的两窗口口径宽）。与 Sonnet S39/S44 完全同构：两线各自独立得出"5 日主参数系统性漏掉 20 日信号、几乎没有短期特有信号"。H=20 并列主参数的口径项证据齐备（§31/§32/§34/本条），等 USER 决定；线继续按现行门跑。

## 三十六、Sonnet 线总复盘（S49，round_651；文件 `runtime_outputs/etf_sonnet_mining_20260920/workspace/outputs/round_651/LANE_RETROSPECTIVE.md`）
Sonnet 自己的机制图与主控判断一致：A 日内回撤几何（QA8 簇，全线最大、无量、pi 逐 bp 复现）；B 隔夜行为 × 日内回撤（UE3/HB1/S27B5）；C 路径序数复杂度（PA1 簇）；D 含量右腿核心（MFI 极值、量 spike/大 bar、成交量时间）；E 午间/收盘时点（CK04/LB7）；F 微观结构噪声（MH3，孤立）。失败通道 10 条各一句（价格延迟、首达时间、频域 beta、类别相对、跳空吸收路径、区间收缩、隔夜分布形状、相对篮子路径、MFI 时点加深、回撤前置深度）。
两处与主控总表不一致，以主控为准：CZ01 精确定义版审计期成立（+39.4 / t 2.09，§45 条），不是"均未成立"；CO36 在 S24（XB1 +45.4 / t 2.63）已跨实现成立，R2 版只是减弱。

## 三十七、pi 线总复盘（第 40 阶段，round_176；文件 `runtime_outputs/etf_pi_glm_mining_20260919/workspace/outputs/round_176/LANE_RETROSPECTIVE.md`）
pi 的机制图 13 组与主控判断大体一致（1m 量事件、量价弹性、回撤几何、排列熵、隔夜行为、成交量时间、午间结构、MFI 极值、MAX 尾部、首达时间、类内相对水下、H20 慢信号族）。三处标签错误以主控为准：R_B5（S27B5 复现）不是"价格延迟"机制，是"隔夜跳空被回撤吃掉 × MFI 极值"，且 MFI 腿含量，不是"无量×无量"；VA3R 的 VOL_SPIKE 腿含量；"隔夜行为成立"应为"审计期复现"（CZ01）。pi 复盘的工程清单与主控 E15–E28 一致。两线复盘都指向同一张图：**信息集中在回撤几何、隔夜行为、路径复杂度三个无量维度和 1m 量事件/MFI 极值两个含量维度上；其余 15 个左右的构造通道在两线独立实现下都没有信息。**
- **Sonnet S50 复现 pi 第 36/37 阶段入选（round_652，--all 验证）**：R_MA27 `PERM_ENTROPY_RET − LUNCH_DIR_BET` **+46.4 / t 2.14**（pi +47.1 / 2.12）逐 bp 一致，跨实现成立；R_DD48 `ULCER_SHIFT − UNDERWATER_FRAC_CHG` **+69.3 / t 4.60**（pi +64.0 / 3.64）成立且更强（簇内组合，登记为回撤几何簇最强切面）；R_MA14 t 0.99（pi 0.86 一致）；LUNCH_DIR_BET 单原子 t 1.20（pi 未入选一致）。无阈值构造再次跨实现稳定。跨实现成立总表 17 条：+MA27、DD48。
- **pi 第 41 阶段午间押方向加深（round_177–178）**：4 原子体检独立（corr ≤0.45），28 条配对 0 入选，两轮穷尽。押方向类构造只有 MA_LUNCH_DIR_BET 作右腿配排列熵那一条有信息（MA27，两线成立），变体无增量——与 S37/S48 一样，机制原子的加深在第二层就饱和。

## 三十八、主控权威表：跨实现成立（17）与审计期复现（2）的候选（2026-09-21 05:40，全部数字来自 controller_verification.json，K=3、H=5、block-t）
pi 第 42 阶段的 FACTOR_CARDS.md（round_179）里"Sonnet 名"与机制标签多处错误（BB1/Z2/CJ16/CK20 的表述、S27B5 归入价格延迟并引用 Bandi–Russell/HAR），**以本表为准**，卡片只作定义细节参考。
| ID | 来源 | 表达式 | 发现 bp/t | 审计 bp/t | 逐年 t 21/22/23/24/25 | 含量 | 状态 |
|---|---|---|---|---|---|---|---|
| PA1 | Sonnet r541 | `PERM_ENTROPY_RET_20` | 32.9/3.59 | 52.4/2.09 | 1.9/0.4/4.3/2.8/−0.4 | 否 | 成立（pi 逐 bp） |
| QA8 | Sonnet r545 | `UNDERWATER_FRAC_CHG_20` | 23.2/2.35 | 60.6/2.88 | 1.5/2.1/0.8/2.2/2.6 | 否 | 成立（pi 逐 bp） |
| CK04 | pi r118 | `rank(LUNCH_PRE_RUN_20) − rank(CLOSE5_DAY_CONSIST_20)` | 31.7/3.16 | 53.0/2.72 | 1.7/1.0/3.5/2.9/0.9 | 量时间分布 | 成立 |
| VA3 | Sonnet r506 | `rank(BEST_DAY_60_XVOL) − rank(VOL_SPIKE_FREQ_20)` | 17.9/2.01 | 34.3/2.24 | 1.7/0.0/2.3/2.1/1.0 | 是 | 成立 |
| NI1 | Sonnet r539 | `rank(MFI_EXTREME_FRAC_20) − rank(VOL_USHAPE_20)` | 34.4/3.32 | 43.6/2.12 | 1.1/0.9/3.6/2.4/0.3 | 是 | 成立（pi 更强） |
| CO36 | pi r099 | `rank(VT_AUTOCORR_20) − rank(VOL_SPIKE_FREQ_20)` | 33.7/3.67 | 47.7/3.14 | 0.6/0.6/5.0/3.4/1.2 | 是 | 成立（S24 版） |
| BB1 | pi r027 | `rank(VOL_SPIKE_FREQ_20) − rank(ULCER_20)` | 26.5/2.72 | 36.3/2.46 | 2.2/0.3/3.5/2.7/0.4 | 是 | 成立（精确定义） |
| Z2 | pi r022 | `rank(BIGBAR_DIR_SKEW_20) − rank(VOL_AUTOCORR_20)` | 34.9/3.56 | 49.2/3.02 | 0.8/2.0/2.9/2.3/2.2 | 是 | 审计期成立 |
| BIGBAR_VOL_SHARE_20 | pi r053 | 单原子 | 24.5/2.92 | 41.6/2.26 | 3.0/−0.4/3.7/1.8/1.2 | 是 | 成立 |
| VOL_SPIKE_FREQ_20 | pi r053 | 单原子（去重挑掉，未入账） | — | 50.7 | — | 是 | 审计期成立（精确定义 +46.6/2.36） |
| CJ16 | pi r117 | `rank(LUNCH_POST_RUN_20) − rank(LOG_AMOUNT_VOL_20)` | 21.5/2.19 | 42.3/2.30 | 0.0/2.3/1.3/2.1/0.7 | 是 | 成立 |
| CK20 | pi r118 | `rank(LUNCH_GAP_20) − rank(ULCER_20)` | 25.1/2.18 | 38.8/1.99 | 2.3/0.5/2.0/2.6/−0.6 | 否 | 成立（Sonnet 数字相同） |
| CR08 | pi r102 | `rank(VT_BUCKET_COUNT_SHIFT_20) − rank(OPEN30_VOL_SHARE_20)` | 16.9/2.05 | 36.5/2.02 | 2.0/0.5/1.9/1.8/0.9 | 量时间分布 | 成立（精确定义） |
| S27B5 | Sonnet r614 | `rank(GAP_DD_CONSUMPTION_RATIO_20) − rank(MFI_EXTREME_FRAC_20)` | 34.8/3.16 | 58.3/3.89 | 1.5/1.1/3.6/4.3/1.2 | 是 | 成立（pi +50.8/3.49） |
| S29P10 | Sonnet r625 | `rank(REL_UNDERWATER_CATEGORY_20) − rank(LOG_AMOUNT_VOL_20)` | 25.2/2.45 | 66.8/2.84 | 2.5/0.6/2.1/2.5/1.6 | 是 | 成立（pi +47.4/2.62） |
| MA27 | pi r173 | `rank(RP_PERM_ENT_D3_20) − rank(MA_LUNCH_DIR_BET)` | 26.9/2.60 | 47.1/2.12 | 0.9/0.8/2.7/2.4/0.0 | 量时间分布 | 成立（Sonnet +46.4/2.14） |
| DD48 | pi r171 | `rank(VFP_ULCER_SHIFT_20) − rank(RP_UW_CHG_20)` | 24.5/2.27 | 64.0/3.64 | 0.8/2.3/0.6/2.8/2.4 | 否 | 成立（Sonnet +69.3/4.60；簇内） |
| CZ01 | pi r109 | `rank(ON_PREM_20) − rank(BIGBAR_EDGE_CONC_20)` | 21.8/2.33 | 55.2/2.76 | 3.1/−0.1/2.9/2.4/1.3 | 是 | 审计期复现（+39.4/2.09） |
| HB1 | Sonnet r592 | `rank(ON_SIGN_STREAK_20) − rank(UNDERWATER_FRAC_CHG_20)` | 31.8/3.19 | 56.5/2.98 | 1.3/3.0/1.3/2.1/2.8 | 否 | 审计期复现（pi +46.4/3.28） |
按机制簇归一（同簇取审计 t 最高）：回撤几何 {QA8, DD48, HB1} → DD48；隔夜×MFI {S27B5}；类内水下×成交额 {S29P10}；排列熵 {PA1, MA27}；1m 量事件 {CO36, Z2, BB1, BIGBAR_VOL_SHARE, VOL_SPIKE, VA3, NI1} → CO36；午间 {CK04, CJ16, CK20} → CK04；成交量时间 {CR08}；隔夜溢价×大 bar {CZ01}。**独立机制代表 8 条**，其中无量 3（DD48/QA8、PA1、CK20 半）。

## 三十九、独立实现一致性矩阵（Sonnet S51，round_653，只报）
同一原子两套实现的日度截面 rank corr（发现窗）：写法无关（>0.95）：VOL_AUTOCORR（1.00）、ULCER（0.999）、ON_PREM（1.00）、PRICE_POSITION（1.00）；中等：OPEN30_VOL_SHARE（0.85）；写法敏感（<0.85）：VOL_SPIKE_FREQ 转述 vs 精确（0.58）、BIGBAR_VOL_SHARE（0.46）、BIGBAR_DIR_SKEW（0.48）、BIGBAR_EDGE_CONC 转述 vs 精确（0.29）、LOG_AMOUNT_VOL（0.77）、GAP_FILL_FRACTION（0.76）、VT_BUCKET_COUNT_SHIFT（0.76）、隔夜方差占比 YZ vs 简单比（0.78）。**量化结论**：任何含"前 X%/×N 倍/阈值"的构造，换一种合理写法后截面排序相关只剩 0.3–0.6；均值/比例/自相关/位置类的无阈值构造两种写法几乎完全一致。这解释了 §28/§30 为什么 spike/大 bar 腿要"精确定义"才复现。设计规则最终版：**原子定义写进合同时必须给出可执行的精确公式（阈值、窗口、缺失处理），复现以公式为准；无阈值优先。**
- **pi 第 43 阶段复现 Sonnet 其余五条（round_180，--all 验证）**：R_S32P1 `相对同类别水下占比变化 − 成交额波动` **+74.0 / t 4.16**（Sonnet +58.6 / 3.10）——pi 侧全线审计超额与 t 新高，成立；R_WA1 `成交量时间水下占比 − MFI 极值占比` +48.1 / t 2.26（+45.3 / 2.15）成立；R_XC5 `成交量桶数变化 − 最大单日收益` +44.2 / t 2.20（+45.4 / 2.27）成立；R_MH3 `噪声方差 − Roll 价差` 审计 +32.8 / t 2.67 但发现 t 1.18（+39.5 / 2.48）审计期成立；R_S47D3 +33.0 / t 1.58（+36.6 / 2.31）减弱。至此两线互相复现闭环。**跨实现成立总表 20 条**（+S32P1、WA1、XC5），审计期复现 3 条（CZ01、HB1、MH3）。§38 表补三行：S32P1 归类内水下簇（与 S29P10 同簇，代表改为 S32P1）、WA1 归回撤几何×MFI、XC5 归成交量时间。
- **因子卡**：Sonnet S52 的 9 张卡（`runtime_outputs/etf_sonnet_mining_20260920/workspace/outputs/round_654/FACTOR_CARDS.md`：PA1、QA8、VA3、NI1、S27B5、S29P10、HB1、XB1、R2_CR08）定义、文献、数字与主控表一致，可作交付底稿；pi 第 42 阶段的 17 张卡（round_179）标签错误多，只作定义细节参考。两套卡合并后覆盖 §38 表全部 19+3 条的 15 条，缺 CK04、CJ16、CK20、Z2、BB1、BIGBAR_VOL_SHARE、MA27、DD48、CZ01、S32P1、WA1、XC5 的正确卡——主控在最终交付时按 §38 表直接生成。

## 四十、三名单交叉（Sonnet S53，round_655，只报）
在 Sonnet 工作区可完整判定的 11 条里：**三项全中（跨实现成立 + H5/H10/H20 全视界 + 2025 前 4 月 t>0）8 条：QA8、VA3、NI1、CO36（本线版 XB1）、BB1、BIGBAR_VOL_SHARE_20、S27B5、HB1**；两项中 3 条：PA1（2025 转负 −0.36，全部候选里唯一近期反号的全视界候选）、S29P10（H20 t 1.73，短周期型）、CK04（H20 t 1.40，衰减最明显）。Z2/VOL_SPIKE/CJ16/CK20/CR08/MA27/DD48/S32P1 在 Sonnet 工作区缺完整剖面，pi 第 39 阶段 h20_profile.csv 可补（主控交付时合并）。
- **pi 第 44 阶段从慢信号名单抽机制原子（round_181）**：pi 首次按新规则先做小样本试算（trial 123 秒）再全量。4 原子里"上涨前排列熵"与排列熵 corr 0.96 影子；其余 3 个体检独立但覆盖率低（0.18–0.54），12 条配对 0 入选。与 Sonnet S47（1/4）一致：H=20 才显著的信号多数不能被机制化拉回 5 日视界。
- **Sonnet S54（round_656）三参照系对照**：类内相对水下占比变化 REL_UNDERWATER_CATEGORY_CHG_20 与绝对版 QA8 rank corr **0.83**（影子）；相对全篮子版发现 t 0.87 弱。所以 S32P1 / R_S32P1（+58.6 / +74.0）的强度来自"水下占比变化 × 成交额波动"这一组合，类别参照系本身不提供信息——S32P1 归入 QA8 回撤几何簇，§38 表的簇归一相应调整（类内水下簇并入回撤几何簇，独立机制代表 8 → 7）。
- **pi 第 45 阶段一致性（round_183）**：pi 内部两套独立写法的跳空吃掉比例（MA_GAP_DD_EAT vs R_GAP_DD_CONSUMPTION）与类内相对水下占比，日度排序 corr 1.000、top-3 重合 1.00——无阈值构造写法无关，与 Sonnet S51 结论一致。
- **Sonnet S54 主控验证（round_656）**：S54P_ULCER_C `REL_ULCER_CATEGORY_CHG_20 − GAP_DD_CONSUMPTION_RATIO_20`（类内相对溃疡变化 − 跳空被回撤吃掉比例）发现 t 2.04、审计 **+60.2 / t 3.29**，无量；左腿与绝对溃疡变化 corr 0.84（影子），故它是"回撤几何 × 隔夜跳空吸收"机制的又一切面（同 S42P10 +35.9 / 2.37、pi DD48）。回撤几何簇现在有三条 t>3 的切面：DD48、S42P17、S54P_ULCER_C。
- S54 round_657：S54P_UWCAT_H `REL_UNDERWATER_CATEGORY_CHG_20 − R_VOL_SPIKE_FREQ_20`（水下变化的类内版 − 精确定义量 spike）审计 +57.9 / t 3.31（K=2 +76.0 / 3.53），2022–2025 全正；仍是"回撤几何 × 量事件"簇内切面。S54 收口：类别参照系无信息，但水下变化与任何含量右腿（成交额波动、量 spike、MFI 极值、跳空吃掉）配对都在 t 3 以上——**QA8 一族是全线最稳的左腿**。
- **E29（2026-09-21 06:42）** 守卫把 Sonnet S54 有效的穷尽宣布（"配对额度用满、合法剩余配对枚举为零"）当作措辞不符驳回，Sonnet 被要求继续，在 S54 下多跑了 round_658/659 两轮换搭档配对。修：守卫正则放宽到"合法[…]配对…为零/<12"与"额度用满"；S55 由主控直接生效。这是第三次因措辞误判（E24 之后的 REJECT 都属此类），根因是穷尽判定靠自然语言匹配——后续若继续跑，应让 worker 在 MECHANISM_EXHAUSTED.json 里写结构化字段 `legal_pairs_remaining: 0`，守卫只读字段不读文本。
- **pi 第 46 阶段（round_184–185）**：TF05 `R_REL_UW_CATEGORY_CHG − VOL_SPIKE_FREQ` 审计 +45.3 / t 2.27（Sonnet 同构 S54P_UWCAT_H +57.9 / 3.31）——两线又一次独立汇合；round_185 入选 4（TF22 `MA_GAP_DD_EAT − R_REL_ULCER_CHG` 对应 Sonnet S54P_ULCER_C 的镜像，待验）。Sonnet S54 尾轮 658：S54I_ULCER_E 审计 t 1.64。
- round_185 主控验证：TF21 `RP_PERM_ENT_D3 − R_REL_ULCER_CHG`（排列熵 − 相对溃疡变化）审计 +33.5 / t 2.21，无量；**TF22 `MA_GAP_DD_EAT − R_REL_ULCER_CHG`（Sonnet S54P_ULCER_C 的镜像）审计 +17.5 / t 0.89——不成立**，S54P_ULCER_C 标单实现（其左腿"类内相对溃疡变化"实现敏感：类别均值扣减在 2–4 只的类别里对写法敏感）。TF23/TF25 t 0.5–1.5。
- **前向账本"已确认"子集清单**：Sonnet S55 `runtime_outputs/etf_sonnet_mining_20260920/workspace/outputs/round_660/forward_confirmed.csv`（23 行：id、表达式、方向、簇、含量、跨实现状态、H5/H10/H20 t、2025 t、本线可计算表达式）。周一 19:30 前向账本首记后，主控用此清单从两线账本里筛"已确认"子集单独出表；S54P_ULCER_C 按 round_185 结果从清单降级。
- **pi 第 46 阶段收口（round_184–185）**：类内相对水下变化与绝对版同量级（审计 IC −0.10 vs −0.08，配对 TF05 +45.3 / 2.27），相对全篮子弱——与 Sonnet S54/S15 一致；参照系无独立信息。pi 已按 E29 规则在穷尽产物里写 `legal_pairs_remaining: 0`、`exhaustion_clause: pairing_discipline`，守卫按字段放行。
- **pi 第 47 阶段**：pi 侧前向账本"已确认"子集清单 `runtime_outputs/etf_pi_glm_mining_20260919/workspace/outputs/round_187/forward_confirmed.csv`（与 Sonnet round_660 清单互为镜像，Sonnet 原创候选用 pi 的 R_/RP_ 复现原子表达）。两份清单是周一起"已确认子集"前向出表的输入。
- **原子精确公式附录草案**：Sonnet S56 `runtime_outputs/etf_sonnet_mining_20260920/workspace/outputs/round_661/ATOM_FORMULAS.md`（29 个原子，按实际实现写公式、阈值、窗口、缺失处理、文献、§39 一致性分类）。合同附录以此为底稿，主控合并 pi 第 49 阶段卡片后定稿。

## 四十一、回撤几何簇代表（pi 第 48 阶段，round_188，只报）
按"跨实现成立 → 三视界 → 2025 正 → 换手低"筛：**代表 = QA8（pi 复现 RP_UW_CHG_20 单原子）**——两线逐 bp 一致、三视界全 t>2.8、2025 t 2.58 全场最高、单原子换手低。簇内替代切面：DD48（溃疡变化 − 水下变化，审计 t 3.64 但与 QA8 的 top-3 日均交集只有 0.03、信号 corr 0.3–0.6——同机制但选出的 ETF 几乎不重合，说明"变化的变化"抓的是另一批时点）、R_HB1（与 QA8 corr −0.7～−0.9，方向相反的同一信息）、R_S32P1（corr 0.1–0.45）。结论：回撤几何簇按相关归一只有 QA8 与 HB1 是一条信息的两面，DD48/S32P1 在 0.6 阈值下是独立切面，但机制同源，账本按"一簇一代表 + 替代切面"登记。Sonnet S57 平行结果待对照。
- **pi 因子卡 v2（第 49 阶段，round_189，`FACTOR_CARDS_V2.md`）**：11 张 pi 原创卡，表达式逐字复制 PLAN、原子标有无阈值、逐年数字与 H10/H20、Sonnet 复现数字齐全，标签错误已修正。一处口径差：卡片把 spike/大 bar 阈值写成"当日均值×5"，代码实际是"当日中位数×5"（§28 核对），定稿时以代码为准。交付卡片集 = Sonnet round_654（9 张）+ Sonnet round_663 S58（补 12 张，进行中）+ pi round_189（11 张），去重后覆盖 §38 全表。
- **Sonnet S57（round_662）回撤几何簇代表 = QA8**，与 pi 第 48 阶段独立得出的结论一致；QA8/HB1/UE3 审计窗 corr 0.73–0.77，同一"隔夜×水下回撤"机制的切面。两线在簇代表上也汇合。

## 四十二、两线"已确认"清单合并核对（pi 第 50 阶段，round_190）
并集 25 条。发现的错误（交付前必须修）：**方向笔误 3 处**——pi 清单 QA8 写 +1（应 −1）、CR08 写 −1（应 +1）；Sonnet 清单 CK20 写 −1（应 +1）。**规则：前向账本与交付表的方向一律以对应轮 STATUS.json 的 direction 为准，不从任何手写清单取。** 状态标签：Sonnet 清单把 VA3/NI1/S27B5/S29P10 标"未见 pi 复现/本线原创"，实际均已跨实现成立（§27/§35）；MA27 两线方向相反是 canonical 腿序交换，等价。pi 报告称 S47D3 "跨线成立 +33.0/2.42"有误：2.42 是发现 t，审计 t 1.58（§43 条），S47D3 不入成立表。2025 口径：pi 卡片用整年 2025、Sonnet 用前 4 月，并列时要标窗口；PA1 是唯一两线同为三视界却 2025 反号的候选。
- **因子卡集齐**：Sonnet S58 `round_663/FACTOR_CARDS_2.md` 补 14 张（CK04、CJ16、CK20、Z2、BB1、BIGBAR_VOL_SHARE、VOL_SPIKE_FREQ、MA27、DD48、CZ01、S32P1、WA1、XC5、MH3）。连同 round_654 的 9 张与 pi round_189 的 11 张，§38 表 23 条每条至少一张卡，多数两线各一张。交付时按 §38/§42 校方向与数字后合并。

## 四十三、pi 侧 7 簇 7 代表（第 51 阶段，round_191，只报）
| 簇 | 代表 | H5/H10/H20 t | 2025 t | 替代切面 |
|---|---|---|---|---|
| 回撤几何 | QA8（RP_UW_CHG_20） | 2.88/3.54/3.89 | +2.58 | DA45、DD48、R_HB1、R_S32P1、R_P10 |
| 1m 量事件 | NI1R（MFI 极值 − 量 U 形） | 2.61/3.87/5.17 | +0.73 | BB1、CO36、BIGBAR_VOL_SHARE、Z2、VA3R |
| 隔夜跳空 × MFI | R_B5（S27B5 复现） | 3.49/5.10/6.84 | +1.49 | R_UE3 |
| 排列熵 | MA27 | 2.12/2.52/3.42 | +0.04 | DA41(PA1)、DD38、TF21 |
| 午间结构 | CJ16 | 2.30/2.18/2.43 | +0.66 | CK04、CK20、CM06 |
| 成交量时间 | R_XC5（条件性）/ CR08 | 2.06 | — | CR08、R_WA1 |
| 隔夜溢价 × 大 bar | CZ01（挂靠隔夜簇） | 2.76/3.60/3.91 | +1.27 | CY07 |
主控意见：排列熵簇代表应为 PA1（单原子、两线逐 bp 一致、H20 t 4.72）而非 MA27（2025 t 0.04、含量时间腿）；午间簇 CK04（两线成立、H5 t 更高）与 CJ16 二选一待 Sonnet S59/S61 对照；其余五簇与预期一致。等 Sonnet S59 表并列后定稿。

## 四十四、7 簇代表 K×H 剖面（pi 第 52 阶段，round_192，只报；bp/t，审计期）
| 代表 | K3H5 | K3H10 | K3H20 | K2H20 | K4H20 |
|---|---|---|---|---|---|
| QA8 | 60.6/2.88 | 112.3/3.54 | 160.8/3.89 | 163.4/3.76 | 112.7/2.96 |
| DD48（替代） | 64.0/3.64 | 103.6/4.33 | 110.1/3.28 | 162.8/3.22 | 82.6/2.90 |
| NI1R | 56.4/2.64 | 121.7/3.89 | **247.1/5.16** | 288.6/4.75 | 170.2/4.71 |
| BB1（替代） | 41.5/2.65 | 89.9/3.85 | 190.2/5.36 | 227.3/4.67 | 163.1/**6.17** |
| R_B5（S27B5） | 47.7/3.25 | 102.9/4.52 | **208.5/6.67** | 250.8/5.05 | 190.8/**7.54** |
| R_UE3（替代） | 33.4/1.73 | 36.2/1.31 | −19.8/−0.49 | −11.1/−0.22 | −4.5/−0.14 |
| MA27 | 47.1/2.12 | 90.3/2.52 | 156.2/3.42 | 171.7/3.29 | 95.6/2.65 |
| DA41（PA1 复现，替代） | 52.4/2.09 | 114.7/3.05 | **233.8/4.72** | 229.5/3.63 | 191.0/4.87 |
| CJ16 | 42.3/2.30 | 62.7/2.18 | 101.0/2.43 | 129.8/2.40 | 79.5/2.37 |
| CK04（替代） | 53.0/2.72 | 66.4/2.58 | 51.3/1.33 | 70.3/1.54 | 44.0/1.49 |
| R_XC5 | 44.2/2.20 | 53.8/1.53 | 45.1/0.75 | −22.2/−0.31 | 52.9/1.06 |
读数：S27B5 与 NI1R 在 H=20 是全线最强（K4H20 t 7.54 / 4.71），QA8 全 K×H 稳；R_UE3 在 H=20 反号（隔夜方差占比是短期信号）；R_XC5 只在 K3H5 站住（脆）；CK04 随 H 衰减、CJ16 平稳——午间簇代表按"三视界"应取 CJ16，按 H5 取 CK04；排列熵簇 DA41（PA1）在 H10/H20 明显优于 MA27，支持主控意见 PA1 为代表。
- 代表间 rank corr（round_192 矩阵）：NI1R–R_B5 **0.70**（两者右腿都是 MFI_EXTREME_FRAC）、MA27–NI1R 0.54、CZ01–NI1R 0.54、CZ01–R_B5 0.50，其余 <0.5。所以 1m 量事件簇若保留 S27B5 为隔夜×MFI 代表，量事件簇代表应换成不含 MFI 腿的 BB1 或 CO36（BB1 K4H20 t 6.17；CO36 两线成立）；主控建议量事件簇代表 = **CO36**（两线成立、三视界、含成交量时间腿与 XC5 簇相关需再核）或 **BB1**，定稿时二选一。

## 四十五、两线簇代表对照与主控定稿（2026-09-21 08:20）
| 簇 | pi 第 51 阶段 | Sonnet S59 | **主控定稿** | 理由 |
|---|---|---|---|---|
| 回撤几何 | QA8 | QA8 | **QA8** `UNDERWATER_FRAC_CHG_20` | 两线一致；四项全中 |
| 隔夜跳空 × MFI 极值 | R_B5 | S27B5 | **S27B5** | 两线一致（Sonnet 标"本线原创"有误，§35 已跨实现成立）；H20 t 6.7 |
| 1m 量事件 | NI1R | XB1（CO36） | **CO36** `VT_AUTOCORR_20 − VOL_SPIKE_FREQ_20` | NI1R 与 S27B5 共用 MFI 腿 corr 0.70；CO36 两线成立、三视界 |
| 路径序数复杂度 | MA27 | PA1 | **PA1** `PERM_ENTROPY_RET_20` | 单原子、两线逐 bp、H20 t 4.72；弱点 2025 前 4 月 −0.36 |
| 午间结构 | CJ16 | CK04 | **CK04**（替代 CJ16） | 两线成立、H5 最强；CJ16 三视界更平稳，作 H20 替代 |
| 成交量时间 | XC5 / CR08 | WA1 | **CR08** `VT_BUCKET_COUNT_SHIFT_20 − OPEN30_VOL_SHARE_20` | WA1 右腿仍是 MFI（与 S27B5 重叠）；CR08 两线精确定义成立 |
| 第 7 簇 | CZ01（隔夜溢价×大 bar） | MH3（噪声） | **CZ01** 与 **MH3** 各列为审计期复现的次级簇 | 两者互不相关、都只审计期成立，不进主表 |
**主表 6 条 + 次级 2 条。** 无量：QA8、PA1；量时间分布：CK04、CR08；含量：S27B5、CO36。全部为 discovery_candidate_not_certified；前向账本周一起按"已确认子集"单独跟踪；口径待决仍只有 H=20 并列主参数一条。
- **pi 第 53 阶段慢信号第 2 梯队机制原子（round_193–194）**：机制原子本身仍不过门（M3P11 t 0.49）；唯一显著的是 M3Q5 `RP_UW_CHG_20 − M3_TAIL_ALIGN_20` 审计 +60.7 / t 2.87——又是水下占比变化作左腿。两梯队合计：机制化把 H=20 信号拉回 H=5 的成功率 1/8（Sonnet S47D3），慢信号名单的主体只能在 H=20 口径下使用。阶段按结构化字段穷尽。
- **pi 复盘补遗（第 54 阶段，round_195，`LANE_RETROSPECTIVE_ADDENDUM.md`）**：第 41–53 阶段表、机制图更新、失败通道更新（押方向加深 0/28；慢信号机制化两梯队"时序状态不可截面化，唯配对路径有效"）。一处与主控不一致：pi 称"peer 相对结构仍未开域、是两线最大剩余空间"——§45/S54/第 46 阶段已证类内相对与绝对版 corr 0.83–0.93 是影子、相对全篮子弱，参照系方向已关闭，以主控为准。
- **Sonnet S60（round_665，H=20 落选原子机制化 v2，27 条入选 4，主控验证 CONSISTENT，5 项指标 0 偏差）**：S60A2 `TURNVOL_ENTROPY_SPLIT_20` 发现 +22.5bp t 2.45 / 审计 +15.1 t 0.79（2025 前 4 月 −41bp，与 PA1 簇 corr 0.15）；S60P_VS_F `rank(VOLSPIKE_NOISECHG_SPLIT_20) − rank(CONTINUOUS_BETA_60)` 发现 +35.9 t 3.25 / 审计 +19.3 t 0.86，五年全正；S60P_TE_C `rank(TURNVOL_ENTROPY_SPLIT_20) − rank(GAP_DD_CONSUMPTION_RATIO_20)` 发现 +29.9 t 2.85 / 审计 +27.2 t 1.15，五年全正（与 S60A2 corr 0.68）；S60P_LM_F `rank(LIQSHOCK_MFI_SPLIT_20) − rank(CONTINUOUS_BETA_60)` 发现 +24.4 t 2.37 / 审计 +10.1 t 0.5（2025 −10）。主控判读：VS_F/LM_F 与 JB2 corr 0.65–0.67，右腿都是 CONTINUOUS_BETA_60（§S4 已证信息在右腿），归 beta 配对簇不另立；本轮唯一新簇代表候选 = S60P_TE_C（左腿换手-量熵拆分 × 跳空回撤消耗），待 pi 复现后进主表；四条 H=20 IC 均高于 H=5（TE_C 0.126 / VS_F 0.148 / LM_F 0.156），H=20 口径项证据 +1。
- **Sonnet S60 收口（round_666，7 条入选 1，主控验证 CONSISTENT；配对纪律穷尽，legal_pairs_remaining 0）**：S60P_TEC_I1 `rank(TURNVOL_ENTROPY_SPLIT_CHG_20) − rank(ULCER_INDEX_20)` 发现 +30.0 t 2.60 / 审计 +25.4 t 0.89（2021–24 正、2025 前 4 月 −5；与 QD5 corr 0.52）；TEC_I3（× INTRADAY_MAXDD）与之 corr 0.976 影子。S60 两轮 34 条入选 5，新家族 mechanism_atoms_v5；本阶段新簇候选仍只算 TE_C 一条（TEC_I1 为其 20 日变化 × 回撤簇变体，同源），待 pi 第 58 阶段复现。
- **pi 第 55 阶段（round_196–198，量 spike 腿无阈值改写 volume_tail_shape_1m）**：r196 20 条（4 原子 Q95/MED、Hill 尾指数、log 量 CV、最大 bar 占比 + 3 强制替换 XB1/BB1/Z2 spike 腿 + 13 左腿批）入选 0；r197 原子转右腿 × 12 已验证左腿入选 0；r198 配对纪律穷尽（r197 漏计 r196 强制替换对致 2 条超限，均被拒，已披露）。结论：**量 spike 的信息在阈值事件计数本身，无阈值尾形统计量不携带**（与 §39 定义敏感性一致：VOL_SPIKE_FREQ 是"事件"不是"分布形状"）；Sonnet S62 平行实现待对照。
- **Sonnet S61（round_667，两线 7 簇代表对照，只报不改门）**：一致 2（回撤几何 QA8=DA44 逐 bp 一致；隔夜×MFI S27B5=R_B5，Sonnet 档案"本线原创"标注滞后须更正）；分歧 3（1m 量事件 NI1R vs XB1——两个不同的跨线复现对、corr 0.44–0.75；排列熵 MA27 vs PA1——PA1 2025 前 4 月 −0.36 反号；午间 CJ16 vs CK04——CK04 H20 t 1.40 非三视界）；数据缺口 1（成交量时间：pi 缺 R_XC5/R_WA1 的 H10/H20）；簇边界 1（MH3 pi 未归簇、CZ01 Sonnet 未单列）。**主控裁决（§46）**：主表 §45 的选簇规则是"同簇审计 t 最高"，不改：QA8、S27B5、CO36（XB1 为其复现对，同一条）、PA1、CK04、CR08（WA1 右腿 MFI 与 S27B5 重叠）保持；S61 的"跨实现→三视界→2025 正"顺序用于**前向账本的已确认子集**：排列熵簇与午间簇各加一条并列跟踪（MA27、CJ16），PA1 标"2025 前 4 月反号"、CK04 标"H20 衰减"。周一 19:30 账本按此并列跟踪，代表不因单窗口翻转而换。
- **pi 第 56 阶段（round_199，2025 双窗口口径统一，只报不入门）**：§45 清单 23 条按各轮 STATUS 方向重算，K=3 H=5，左列 2025-01-01→04-30（审计末段 165 日），右列 2025 自然年（231 日，含审计窗外 5 月以后）。两窗口均正：QA8（+95.9/2.58 → +18.5/1.00）、DD48（2.40→1.40）、Z2（2.95→1.31）、CR08（0.93→1.07）、S32P1、HB1。**审计末段正、整年负 7 条：CO36、CK04、CZ01、NI1R、MA27、UE3、BIGBAR_VOL_SHARE**；两窗口均负：PA1（−0.36/−1.87）、WA1、CK20；CJ16 反向（末段 0.66、整年 +49.0/2.03，全表最强整年）。主控判读：整年列的 5–12 月是所有候选从未参与的窗外数据，等于一次前向预演——主表 6 条里只有 QA8、CR08 两窗口同向正，CO36/CK04 窗外转负，PA1 双负；与 S61 的结论合并，前向账本已确认子集按窗外表现分层标注，代表不换、门不改；H=20 口径项证据不变。复算脚本 `round_199/window_align_runner.py`。
- **Sonnet S62（round_668–669，量 spike 腿无阈值改写，与 pi 第 55 阶段平行）**：4 原子（VOL_Q95_MED、Hill 尾指数、log 量 CV、最大 bar 占比）28 条配对入选 0，配对纪律穷尽。拒因结构：LOG_VOL_CV 的 8 条里 4 条发现 t 2.32–3.61 但与 XB1/BB1/S27B5/PA1 corr 0.86–0.91 被去重；VOL_MAX_SHARE 2 条 t 2.65–2.92 与 JB2/PA1 corr 0.72–0.83 被去重。**两线结论一致（pi 32 条 0、Sonnet 28 条 0）**：无阈值尾形统计量要么是已有事件计数原子的影子（corr 0.86–0.91），要么无信号；量 spike 通道以 VOL_SPIKE_FREQ 事件定义为终版，不再改写。无阈值改写方向关闭。
  - 补记：S62 强制替换对 `VT_AUTOCORR − VOL_Q95_MED`（替 XB1 的 spike 腿）与 XB1 corr 0.96、`VOL_Q95_MED − R_ULCER`（替 BB1）与 BB1 corr 0.97，发现 IC 与原版同量级——**§39 的"VOL_SPIKE_FREQ 换写法后排序相关 0.58"是 R2 版实现差异，不是量 spike 概念本身定义敏感**；Q95/中位数比值与阈值事件计数排序等价，XB1/BB1/CO36 的 spike 腿定义稳健性由此确认（正面结果，记入因子卡"定义稳健性"行）。
- **Sonnet S63（round_670，资本利得悬垂 1d 原版 Grinblatt–Han，16 条入选 3，主控验证 CONSISTENT，5 项 0 偏差）**：4 单原子（CGO_60、GAIN_OVERHANG_60、LOSS_OVERHANG_60、RP_CHANGE_20）单独全不过门（发现 t 0–1.6），与回撤几何/量事件/量时间/午间四簇 rank corr **全部 ≤0.17——新独立信息面**（水下簇只用价格路径，CGO 用成交量加权成本，二者截面不相关）。配对入选：S63P_LOSS_3 `rank(LOSS_OVERHANG_60) − rank(GAP_DD_CONSUMPTION_RATIO_20)` 发现 +29.4 t 3.26 / 审计 +23.6 t 1.67，**五年全正（2025 前 4 月 +18）**；S63P_CGO_1 `rank(CGO_60) − rank(VOL_SPIKE_FREQ_20)` +16.4 t 2.38 / 审计 +24.1 t 1.89，五年全正；S63P_GAIN_3 `rank(GAIN_OVERHANG_60) − rank(PERM_ENTROPY_RET_20)` +19.1 t 2.35 / 审计 +25.4 t 1.56（2022 −2；与 PA1 corr 0.68 边界）。主控判读：LOSS_3 是本轮唯一新簇代表候选（"账面亏损悬垂 × 跳空被回撤消耗"，处置效应机制的量权版），审计 t 1.67 未到两窗口显著；pi 第 60 阶段已排队精确复现三条；S65 的 1m 版将测分辩率增量。
- **Sonnet S63 第二批（round_671，12 条入选 2，主控验证 CONSISTENT）**：S63P_LOSS_4 `rank(LOSS_OVERHANG_60) − rank(CONTINUOUS_BETA_60)` 发现 +30.2 t 3.83 / 审计 +15.6 t 0.96（2025 −6；与 JB2 corr 0.62，归 beta 配对簇）；S63P_CGO_5 `rank(CGO_60) − rank(LOG_AMOUNT_VOL_20)` +24.1 t 2.84 / 审计 +9.7 t 0.69（五年正，弱）。**主控指出**：S63P_LOSS_5 `rank(LOSS_OVERHANG_60) − rank(PERM_ENTROPY_RET_20)` 发现 t 3.65 / 审计 **+38.2**bp 因与 LOSS_4 corr 0.75 被同轮去重——按配对纪律"同簇只登记审计 t 最高一条"，簇代表应为 LOSS_5 而非 LOSS_4；两条都进 pi 第 60 阶段复现清单（LOSS_5 加为第 4 条），前向账本按 LOSS_5 登记。S63 累计 28 条入选 5，LOSS_OVERHANG_60 是四原子里唯一三个右腿都过门的左腿。
- **E30 主控规格错误（2026-09-21 10:40 发现）—— S63 与 pi 第 57 阶段的 CGO 家族全部退化为一日收益影子**：主控指令写"换手率用当日成交量/滚动 60 日均量代理"，该比值中位数 0.88–0.99，Grinblatt–Han 存活权 Π(1−TO) 一日后 ≈0，参考价 ≈ P_{D−1}。主控用 1d 规范数据按同一公式实测 14 只：corr(CGO_60, ret1) 0.87–0.99，corr(LOSS_OVERHANG_60, max(−ret1,0)) 0.72–0.92。**撤销**：S63 五条入选（LOSS_3/CGO_1/GAIN_3/LOSS_4/CGO_5/LOSS_8）与 pi 第 57 阶段 round_200 三条（CDP6/CDP7/CDP8）标 DEGENERATE_RET1_SHADOW；"CGO 是与四簇不相关的新信息面"结论撤销（一日收益与慢变量本就不相关，且控制集缺一日收益项使残差 IC 虚高——正是 09-19 已知缺口）；两线 CDP6 与 S63P_CGO_5 的"自发跨实现一致"只是都算了 ret1 − 成交额波动。pi 第 57 阶段其余原子（UW_VOL_SHARE_60 等基于 1m 的量）在一日存活下退化为"当日成交量在 close 上方的占比"= 日内收盘位置，CDP7（审计 +50.8/t 3.04，2025 +87）实为"日内收盘位置 × 水下比例变化"，若要保留须以该真实定义重新预注册。**修正**：换手率改用 PIT 基金份额 `fund_share/*.parquet`（14 只 2018–2026 齐，159206 缺）；pi 第 57b、Sonnet S66 平行重做；已排队的 pi 第 60 阶段（复现退化结果）取消（移入 DIRECTIVE_QUEUE/cancelled/）。**流程规则**：任何含"换手率/存活率/衰减权"的规格必须在指令里写明量级校验（TO 中位数应 0.5%–10%），体检必列与 ret1 的 corr。
- **pi 第 57 阶段第二批（round_201，12 条入选 3）**：CDQ5/CDQ9/CDQ12 左腿或右腿为 UW_VOL_SHARE_60 / COST_CONC_60，属 E30 退化原子，一并 VOID（`CONTROLLER_VOID.json` round_201）。第 57 阶段两轮 33 条名义入选 6、有效 0。
- **Sonnet S64 第一批（round_673，拆分条件化机制原子 v6，16 条入选 3，主控验证 CONSISTENT）**：8 个 split 单原子全部单独不过门（发现 t −0.03–2.58）。配对：S64P_PERMENT_TURNOVER_SPLIT `rank(PERMENT_TURNOVER_SPLIT_20) − rank(CONTINUOUS_BETA_60)` 发现 **+39.6 t 4.15** / 审计 +35.4 t 1.57，五年全正（2025 +44），H20 审计 t 5.84 全场最强，与 JB2 corr 0.68（beta 配对簇）；S64P_LUNCHPR_ONGAP_SPLIT `rank(LUNCHPR_ONGAP_SPLIT_20) − rank(GAP_DD_CONSUMPTION_RATIO_20)` +33.1 t 3.68 / 审计 +26.4 t 1.51，五年正（与 S27B4 corr 0.55）；S64P_UWCHG_TURNOVER_SPLIT × beta +27.9 t 2.48 / 审计 +9.3 t 0.43（弱）。**工程缺项**：round_673 未交 atom_health，split 原子与被拆原版（PERM_ENTROPY_RET_20 等）的 corr 未报，PERMENT × beta 是否只是 PA1/MA27 的影子无法判定；已在 S64 指令追加补交块（不改口径）。判读暂缓至体检补齐。
- **Sonnet S64 第二批（round_674，12 条入选 1，主控验证 CONSISTENT）**：S64P2_ULCER_TURNOVER_SPLIT_20_2 `rank(ULCER_TURNOVER_SPLIT_20) − rank(R2_VOL_AUTOCORR_20)` 发现 +19.9 t 2.24 / 审计 +24.1 t 1.79（2021 +2，其余年 +20–32；与 PA1 corr 0.51）。同轮 Sonnet 自行写出 `round_674/CONTROLLER_VOID.json`：自主判定 S63 六条为 E30 退化并作废（与主控清单一致），并回检 S64 八个 split 原子与 ret1 的 corr ≤0.07（S64 不受 E30 影响）。**仍缺**：split 原子与被拆原版（PERM_ENTROPY_RET_20 等）的 corr，round_674 也未交；补交块已在指令，继续等。
- **pi 第 57b 阶段第一批（round_203，真换手 CGO，24 条入选 1，主控验证 CONSISTENT）**：TO = volume/PIT fund_shares，中位数 5.95%/日（正确量级）。6 原子单独全不过门；GAIN_OVERHANG_TT_60 与 LOSS_OVERHANG_TT_60 被实现为互补占比（排序等价，指标逐位相同），实际只有 5 个原子。入选 CGP17 `rank(RP_CHANGE_TT_20) − rank(R_MFI_EXTREME_FRAC_20)` 发现 +25.2 t 2.32 / 审计 **+41.4** t 1.42，五年全正（2025 +54）。5 条 t 2.4–3.7 因与 MA09/DA41/CO09/BB1 corr 0.72–0.76 被去重（CGP11 LOSS × MFI_EXTREME 发现 t 3.69 / 审计 +60.2 与 CO09 corr 0.72）。**主控独立复算（规范 1d + fund_share，14 只）**：corr(CGO_TT_60, ret1) 0.24–0.65；**corr(CGO_TT_60, ret20) 0.52–0.88**、corr(RP_CHANGE_TT_20, ret20) 0.38–0.87——真换手版 CGO 不再是 ret1 影子，但主要是 1–3 月动量的量权改写；成本会计相对 ret20 的增量未证。已向 pi 第 57b（续）与 Sonnet S66/S65 追加：体检列 ret20/ret60/PRICE_POSITION_20，每个 CGO 配对加"ret20 替换左腿"对照对并列报 t。CGP17 暂标"动量代理候选"，待对照对。
- pi round_202《第 57 阶段穷尽复盘》称"成本会计是真新信息源（vs 四簇 corr 0.25–0.29）"——写于 E30 前，结论已被 E30 取代（那 6 个原子是当日 bar 统计量）；以主控 E30 条为准。
- **Sonnet S64 收口（round_675，4 条入选 2，主控验证 CONSISTENT；配对纪律穷尽）**：体检补齐——8 个 split 原子与被拆原版 rank corr 0.01–0.23、与 ret1 0.02–0.07，**不是影子**。**S64P3_PERMENT_TURNOVER_SPLIT `rank(PERMENT_TURNOVER_SPLIT_20) − rank(UNDERWATER_FRAC_CHG_20)` 发现 +30.2 t 2.97 / 审计 +49.7 t 2.45——两窗口显著，无量×无量，2025 前 4 月 +104bp（2023 −3）；与 QA8 corr 0.68**（回撤簇边界，右腿同源）。S64P3_ULCER_NOISERATIO_SPLIT × PERM_ENTROPY_RET 发现 +36.5 t 3.98 / 审计 +21.4 t 1.14（2025 0；与 PA1 corr 0.69）。S64 三轮 32 条入选 6（含 PERMENT_TURNOVER_SPLIT × beta t 4.15 / H20 5.84）；PERMENT_TURNOVER_SPLIT_20（高成交额日与低成交额日的排列熵之差）是三条入选的公共左腿，为本阶段机制原子。pi 第 59 阶段平行实现进行中；第 61 阶段（精确复现四条）已排队；S67（split 施于量通道原子）已排队。
- **Sonnet S65（round_676–677，1m 成本分布 Sonnet 版，真换手，23 条入选 0，配对纪律穷尽）**：6 原子体检干净——与 ret1 |corr| ≤0.18、ret20 ≤0.32、ret60 ≤0.45（COST_SKEW）、与四簇腿 ≤0.40；corr(CGO_1M_60, 1d 真换手 CGO_60) = 0.17，1m 版不是 1d 版换分辩率，也不是动量代理。但 **ret20 对照对显示成本会计无增量**：CGO_1M × {VOL_SPIKE, VT_AUTOCORR, LUNCH_PRE_RUN} 的 t/bp 与 RET_20 × 同右腿对照打平或更差；其余 4 原子 × UNDERWATER_FRAC_CHG 两条 t 2+ 但与 QA8 corr 0.72–0.75 被去重。自报流程违规一处（UNDERWATER_FRAC_CHG_20 被配 4 个左腿，超 ≤3 上限；无入选受影响，已冻结该右腿）。结论：1m 成本分布是干净的独立面但无 alpha；与 pi 第 57 阶段（退化）/57b（1d 真换手 = 动量代理）合看，**成本会计面在 14 只 ETF 上关闭**，S66（1d 真换手 Sonnet 版）作为最后一次对照后不再开。
- **pi 第 57b 阶段第二批（round_204，20 条入选 0，含 6 条 RET20 对照对）**：体检补齐——CGO_TT_60/250、GAIN/LOSS_OVERHANG_TT、UW_SHARE_TT 与 ret20 corr 0.63–0.74、与 PRICE_POSITION_20 0.70–0.79，**判影子**（成本会计的真换手版 = 20 日价格位置）；RP_CHANGE_TT_20 与 ret20 0.655 未到影子线。RET20 替换左腿的 6 条对照全部不过门（RET20 × MFI_EXTREME 对照 topk 不过，而 CGP17 RP_CHANGE × MFI 审计 +41.4 过门——单点增量迹象，不足以立簇）。与 Sonnet S65 合并：**成本会计面关闭**（1d 真换手 = 价格位置影子；1m 版干净但无增量；均量代理版退化）。CGP17 留在候选表标"RP_CHANGE 动量类，单点"，不进代表表。第 57b 待配对纪律穷尽后进第 58/59/61 阶段。
- **Sonnet S66 第一批（round_678，1d 真换手 CGO Sonnet 版，16 条入选 2，主控验证 CONSISTENT）**：体检与 pi 第 57b 一致——CGO_60/250、GAIN_OVERHANG_60 与 R2_PRICE_POSITION_20 corr 0.70–0.74 判影子；LOSS_OVERHANG_60 / UW_SHARE_250 与价格位置 −0.59/−0.62、与 ret20 −0.51/−0.49（未到影子线）；RP_CHANGE_20 与 ret60 0.68。入选：**S66P_UWSHARE250_R2VS `rank(UW_SHARE_250) − rank(R2_VOL_SPIKE_FREQ_20)` 发现 +24.7 t 2.34 / 审计 +44.5 t 2.77——两窗口显著**（五年全正，2025 +61；与 BIGBAR_VOL_SHARE corr 0.66）；S66P_RPCHANGE20_R2VS +23.4 t 2.02 / 审计 +23.7 t 1.09（2021 −16）。主控判读：UW_SHARE_250 ≈ 250 日成本高于现价的存活量占比 ≈ 长期价格位置取负，配 spike 腿的显著性可能来自"长期低位 × 量事件"而非成本会计；round_678 漏交 ret20 对照对，已追加补交块要求 −RET_250 / −PRICE_POSITION_250 / −RET_20 替换左腿的三条对照并列报告。**"成本会计面关闭"的判定暂缓到该对照落地**：若对照 t 与 CGO 版持平则关闭并把 UWSHARE250_R2VS 归入价格位置 × 量事件；若 CGO 版显著高于对照，成本会计面保留一条。
- **Sonnet S66 收口（round_679，5 条入选 1，主控验证 CONSISTENT；配对纪律穷尽）**：S66P2_GAIN60_VTAC `rank(GAIN_OVERHANG_60) − rank(VT_AUTOCORR_20)` 发现 +27.0 t 2.62 / 审计 +21.9 t 1.19（2021 +3）——左腿 GAIN_OVERHANG_60 与 R2_PRICE_POSITION_20 corr 0.705，体检已判影子，**主控按影子处理不入表**。同轮 CGO_V2 × PERM_ENTROPY 两条审计 +61.5/+66.1 但与 DA6 corr 0.75–0.76 去重（DA6 = 价格位置类 × 排列熵，再证 CGO ≈ 价格位置）。round_679 在主控补交块前启动，价格位置对照对未跑；已插入 S66b（单轮 6 条对照：−RET_250 / −PRICE_POSITION_250 / −RET_20 替换 UW_SHARE_250，RET_20 替换 RP_CHANGE，PRICE_POSITION_250 / RET_60 替换 GAIN_OVERHANG），S67 之前生效。S66 累计 21 条入选 3，有效待对照。
- **Sonnet S66b（round_680，价格位置对照 5 条，只报不改门）**：① UW_SHARE_250 × R2_VOL_SPIKE：对照 rank(−PRICE_POSITION_250) − rank(spike) 发现 t **2.50**（≥ CGO 版 2.34）/ 审计 +31.1，与 CGO 版 corr 0.72——**无增量**，S66P_UWSHARE250_R2VS 归"长期价格位置 × 量事件"，不算成本会计；② RP_CHANGE_20 × spike：对照 rank(RET_20) − rank(spike) 发现 t **−0.01** / 审计 +12.5 vs CGO 版 2.02 / +23.7（H20 审计 t 2.84）——**增量清晰**；③ GAIN_OVERHANG_60 × VT_AUTOCORR：对照 PRICE_POSITION_250 版 1.93 / +7.9，RET_60 版反号——部分增量，但左腿本身已判影子，不采。**主控裁决：成本会计面只保留一个机制原子 RP_CHANGE_20（真换手参考价的 20 日变化率 = 持仓成本的迁移速度），两线各自独立入选一条（pi CGP17 × MFI_EXTREME 审计 +41.4；Sonnet × spike 审计 +23.7），其余 CGO/GAIN/LOSS/UW_SHARE 全为价格位置影子，面关闭。**交叉复现已排队：Sonnet S69（复现 CGP17 + RP_CHANGE 剖面）、pi 第 62 阶段（复现 RP_CHANGE × spike + 对照）。
- **pi 第 58 阶段（round_206，复现 Sonnet S60 四条）——实现失败，非复现不成立**：四条 R_ 候选发现有效日 71/0/71/331（Sonnet 原版 544–579），全部因 discovery_days 被拒。原因：主控指令写"换手率高于/低于 20 日中位数"，pi 按 fund_share 真换手实现（`etf_repl_sonnet_s60.py` 第 7–9 行），fund_share 部分票 2023 年后才有且与 1m 目录对齐后大面积 NaN；Sonnet S60 的口径是当日成交额 vs 20 日中位数。主控规格再次歧义（与 E30 同类：术语"换手率"未指明分母）。已插入第 58b 阶段（修口径重跑，目标有效日 ≥540），第 59 阶段之前生效。**规则**：复现指令里的每个条件变量必须写到分母级（"成交额 / 20 日成交额中位数"），不用"换手率"这种多义词。

## §47 引擎三修（2026-09-21 12:40，USER 批准）与 S67/S68
- **修 1（包装层，两线引擎副本各改一处）**：`_previously_admitted` 读 `CONTROLLER_VOID.json`，作废候选不再进去重参照集。实测：参照集 204 条、作废 12 条 0 条在内。
- **修 3（引擎去重参照，USER 批准）**：`_dedup_pass` 新增 `base:RET1`、`base:RET20` 参照向量（close ≤D 的 1/20 日收益截面百分位秩，与 shelf 同 stride 规则），|corr| ≥0.70 即拒。实测 S63P_CGO_1（已作废的 ret1 影子配对）与 base:RET1 corr 0.62——配对会稀释单原子的影子相关（单原子 0.98），门 0.70 对配对偏松，但已能拦单原子级影子。两线已通告，不改门。
- **修 2（登记层脚本 `audit/cluster_representative_swaps.py`）**：同轮仅因固定顺序去重被拒、审计 bp 更高且发现 t ≥2 的候选登记为簇代表（`CLUSTER_REPRESENTATIVE_SWAPS.json`），forward_ledger 并列跟踪。首跑：pi 7 处（DA41→DA42 56.1、TF05→TF06 55.0、CY07→CY19 52.9 …）、Sonnet 10 处（PA1→PA3 56.4、XB1→XB7 50.2、S29A3→S29P9 53.5 …）。跨轮的（S66 vs DA6、LOSS_5 vs 已作废 LOSS_4）不在范围。判据用审计 bp（csv 无审计 t），主控复核时以 controller_verify 的审计 t 为准。
- **selftest** 放宽记账轮与 atom_health 变体的 schema 检查，并断言两线引擎含修 1/修 3 标记；0 失败。
- **Sonnet S67（round_681–682，split 施于量原子，32 条名义入选 1）**：8 个 split 量原子与原版 corr ≤0.14、与 ret1 ≤0.09。S67P_VOLSPIKE_MAXDD_SPLIT × PERM_ENTROPY_RET 发现 +? t 2.67 / 审计 +22.5 t 1.37（与 PA1 corr 0.69，边界）；另 4 条发现 t 2.0–3.0 因 identity/topk 门拒。**量原子上 split 通道明显弱于无量原子**（S64 32→6 vs S67 32→1）。
- **Sonnet S68（round_683，S64 三条稳健性剖面）**：① PERMENT_TURNOVER × BETA60 的 4.15 是**发现期 t**，审计 t 全网格 0.18–1.55，w60 时 H20 审计转负——归"发现期强、审计弱"，不入代表；② **PERMENT_TURNOVER × UNDERWATER_FRAC_CHG 基线 H5/H10/H20 审计 t 2.37/2.52/2.14 全视界过**，条件换成交量仍 2.56/2.60/2.47，但窗口 40/60 审计掉到 1.0–1.3（**窗口敏感**）；单腿诊断：高、低成交额日排列熵各自单配右腿 t 全负（H20 −3.5/−4.2），信息确实在"差"里，不是某一侧；③ LUNCHPR_ONGAP 原版窗实为 40（主控指令写 20 有误），网格里无一格复现 3.68，审计最高 H10 2.86——定义敏感，待 pi 第 61 阶段复现。主控裁决：PERMENT_TURNOVER_SPLIT × UNDERWATER_FRAC_CHG 进"待复现的两窗口显著"位，卡片标"窗口 20 专属"；另两条不进表。
- **pi 第 58b 阶段（round_207，S60 四条复现重做，口径改为成交额/20 日中位数）**：覆盖修好（494–510 日；VOLSPIKE_NOISECHG 仍只 155 日，5m 噪声方差比链路缺口）。结果：R_TURNVOL_ENTROPY_SPLIT_20 单原子 t −0.36（Sonnet 2.45）；× GAP_DD_CONSUMPTION t 0.09 / 审计 +15.9（Sonnet 2.85 / +27.2）；R_LIQSHOCK_MFI_SPLIT × beta t 0.54 / 审计 −30（Sonnet 2.37 / +10.1）。**S60 四条跨实现不成立**——TE_C 从"新簇候选"降为"Sonnet 本线原创，未复现"，不进表。S60 阶段的产出归零；S64 的 PERMENT_TURNOVER_SPLIT 仍待第 59/61 阶段。
- **Sonnet S69（round_684，复现 pi CGP17 + RP_CHANGE 对照）**：`rank(RP_CHANGE_V2_20) − rank(MFI_EXTREME_FRAC_20)` 发现 **t 2.93** / 审计 +22.9（pi 原版 2.32 / +41.4，同向）——**跨实现成立（发现期），审计 bp 两线均正**；本线因与自家 S66P_RPCHANGE20 × spike corr 0.94 被去重（说明信号主体在 RP_CHANGE 左腿）。对照 rank(RET_20) − rank(MFI_EXTREME) 发现 t 0.94 / 审计 −6.2——**增量在两线均成立**（pi CTC1 对照亦不过门）。RP_CHANGE × UNDERWATER_FRAC_CHG 1.78 / +34.9 不及 RET_20 对照 1.96 / +46.8，无增量。主控裁决：**RP_CHANGE_20（真换手参考价 20 日变化率）× MFI_EXTREME_FRAC_20 进跨实现成立表**（第 16 条），簇名"持仓成本迁移 × 资金流极值"，含量；审计 t pi 1.42、Sonnet 待 `--all` 复核（已起）。成本会计面保留此一条，其余关闭。
  - 补记（round_684 `--all` 复核 CONSISTENT）：S69R RP_CHANGE × MFI_EXTREME 审计 +22.9 **t 1.08**（五年同向），对照 RET_20 × MFI 审计 −6.2 t −0.34（年度不同向）。两线合看：发现 t 2.32/2.93 成立，审计 t 1.42/1.08 均未到 2——**第 16 条按"跨实现成立（发现期）+ 对照增量成立，审计弱"登记**，不与 QA8/S27B5 同级。
- **pi 第 59 阶段（round_208–209，split 条件化 pi 平行实现，16 条入选 0）**：8 个 split 原子与原版 corr 0.21–0.33、与 ret20 ≤0.43，无影子；16 条门 7 全拒，最佳 SCP3 `PE×成交额 − BETA` 发现 t 1.90（Sonnet 同构 4.15）、SCP1 `DD×成交额 − GAP_DD` 1.77 / 审计 +20.8。**跨线不对称：Sonnet S64 32→6，pi 同通道 16→0**。差异来源候选：pi 的排列熵原子是 RP_PERM_ENT_D3（三阶差分版）而 Sonnet 用 PERM_ENTROPY_RET_20；pi 未配 UNDERWATER_FRAC_CHG 右腿（S64 最强对的右腿）；pi 每原子只配 1 个定向右腿。**判定交给第 61 阶段精确复现**（已生效）：若 R_PERMENT_TURNOVER_SPLIT × UW_CHG 复现出 t≈2.97 / 审计 ≈+49.7，则 S64 成立且 pi 第 59 阶段的零是构造差异；若不复现，PERMENT_TURNOVER_SPLIT 降为 Sonnet 本线原创。
- **pi 第 61 阶段（round_210，S64 四条精确复现，0/4 入选；`--all` 复核 CONSISTENT）**：NS64A `R_PERMENT_TURNOVER_SPLIT × RP_UW_CHG` 发现 +18.2 t 1.86 / 审计 +32.5 **t 1.73**（Sonnet 2.97 / +49.7 t 2.45）同向减弱；× beta 1.59（Sonnet 4.15）；LUNCHPR 0.62；ULCER_NOISERATIO 覆盖 155 日。**主控实现一致性检查（两线引擎各自构造，日截面秩相关）**：右腿 UNDERWATER_FRAC_CHG_20 vs RP_UW_CHG_20 = **1.00**；左腿 PERMENT_TURNOVER_SPLIT_20 vs R_PERMENT_TURNOVER_SPLIT_20 = **0.03**——不是同一个原子。差异三处：Sonnet 的 X 是 1m 排列熵的 **20 日滚动均值**日值，pi 用当日 5m 单值；Sonnet 条件是**同窗**成交额中位数（含当日），pi 用前 20 日中位数；组内最少 1 日 vs 3 日。主控指令"X = 排列熵日值（本线现有原子的日值）"一句两读——第三次规格歧义。结论：第 61 阶段**不构成复现失败**，S64 状态维持"待复现"；第 61b 阶段按精确构造重做已插队；S72 总表须按真实构造写卡片语言（"20 日滚动排列熵在同窗高/低成交额日的均值差"）。附：Sonnet 构造把一个慢变量按同窗量分组取差，本质接近"该 ETF 排列熵趋势与成交额的窗内协变"，机制解释待 61b 复现后再写。
- **pi 第 61b 阶段（round_211，S64 精确构造复现，4 条入选 2，`--all` CONSISTENT）**：**NR2A `rank(R2_PERMENT_TURNOVER_SPLIT_20) − rank(RP_UW_CHG_20)` 发现 +26.9 t 2.47 / 审计 +38.0 t 1.80，五年同向**（Sonnet 2.97 / +49.7 t 2.45）——**跨实现成立（发现期两线 ≥2；审计同向，pi t 1.80 未到 2）**，进跨实现成立表第 17 条，簇名"排列熵-成交额窗内协变 × 水下比例变化"，无量。NR2C LUNCHPR_ONGAP × GAP_DD 发现 2.59（Sonnet 3.68）/ 审计 +15.5 t 0.90（Sonnet 1.51）——发现期成立、审计弱。× beta 1.44（Sonnet 4.15）不成立，归 Sonnet 本线。ULCER_NOISERATIO 覆盖 314 日仍不足（5m 噪声方差比链路）。**教训落地**：第 61 阶段 0.03 → 61b 成立，差别全在构造细节（滚动日值 / 同窗中位数 / 1m）；以后 split 类指令一律写这三项。
- **Sonnet S70（round_685–686，同窗成交额 split 施于第二梯队无量原子，29 条入选 5，主控验证 CONSISTENT）**：8 原子与原版 corr ≤0.10、ret1/ret20 ≤0.09。**VFPULCER_TURNOVER_SPLIT_20（DD48 左腿 VFP_ULCER_SHIFT 的同窗成交额 split）两条两窗口显著**：× PERM_ENTROPY_RET 发现 +27.3 t 2.94 / 审计 **+53.9 t 2.64**（五年正，与 PA1 corr 0.67）；× UNDERWATER_FRAC_CHG 发现 +23.2 t 2.70 / 审计 **+54.2 t 2.74**（五年正，与 QA8 corr 0.68）；× GAP_DD 2.52 / +18.1 t 0.94；VFPULCER_NOISECHG × GAP_DD 2.40 / +25.4 t 1.14；RESIL_ONGAP × beta 2.78 / +6.2（2025 −24，弱）。主控判读：与 S64 同一构造家族——**慢变量滚动原子在窗内与成交额的协变**是当前唯一持续出产的通道（S64 6、S70 5、S67 量原子 1、pi 第 59 阶段异构 0）；pi 第 64 阶段精确复现两条已排队，S73 把该构造推到六条主表代表左腿。边界：两条与 PA1/QA8 corr 0.67–0.68，是否只是回撤簇的放大版待复现与 S72 总表判。
- **主控一次性回扫（2026-09-21 13:50）：全部在册入选 vs base:RET1/RET20**（与引擎新参照同 stride/秩规则；pi 116 条、Sonnet 209 条，作废者已排除）：|corr| 中位数 0.08、95 分位 0.37–0.38；**17 条跨实现成立无一 ≥0.5**（第 17 条 NR2A ret20 0.25 最高）。唯一 ≥0.7：Sonnet round_546 **QD5** `rank(INTRADAY_MAXDD_20) − rank(REL_MARKET_MOM_20)`（右腿=相对篮子 20 日动量，本身就是 ret20 类） 与 ret20 corr **−0.705** → 作废（RET20_SHADOW，加入 CONTROLLER_VOID；它曾作为去重参照挡过 S63P_RPCHG_5 / S60P_TEC_I1）；0.5–0.7 只有 DA6（−0.52），保留并标注。结论：新参照不改变已确认表；引擎修 3 对历史无追溯影响。
- **Sonnet S71（round_687，S64 入选对的右腿也 split，14 条入选 0，配对纪律穷尽）**：右腿 UNDERWATER_FRAC_CHG / GAP_DD_CONSUMPTION / CONTINUOUS_BETA 按成交额或隔夜跳空 split 后与左腿 split 原子配对，发现 t 全部 <1.7、多数反号；同条件（两腿都按成交额拆）不优于异条件。工程发现：指令示例①的两原子同属一个家族文件，引擎 cross_family 断言不允许同族配对，Sonnet 改建新家族绕过，已如实登记。**结论：split 构造只在一侧腿上有效——右腿必须是未拆的慢变量本体**；两腿同拆把两个"窗内协变"相减，信息抵消。split 通道累计：S64 32→6、S67 32→1、S70 29→5、S71 14→0；S72 总表、S73/S74 继续单侧 split。
- **pi 第 62 阶段（round_212，复现 Sonnet RP_CHANGE × spike + 对照，3 条，`--all` CONSISTENT）**：`rank(RP_CHANGE_TT_20) − rank(VOL_SPIKE_FREQ_20)` 发现 +23.7 **t 2.29** / 审计 +25.3 t 1.22，五年同向（Sonnet 2.02 / +23.7 t 1.09）——**跨实现成立（发现期）**，本线因与 CGP17 冗余被拒（同左腿）；对照 rank(RET20) − rank(spike 类) 1.13 / +7.8，年度不同向——增量再次成立。pi 只跑了 3 条（未做 × RP_UW_CHG / × GAP_DD 两条），复现例外配额未用满，不补。**第 16 条更新**：RP_CHANGE_20 有两条跨实现成立配对（× MFI_EXTREME 2.32/2.93；× VOL_SPIKE 2.29/2.02），审计 t 两线均 1.1–1.6，五年同向；卡片定位"持仓成本迁移速度 × 量事件"，审计弱但方向与增量稳定。

## §48 冻结（2026-09-21 14:15，USER 决定"全停，先出冻结报告"）
- 触发：North Star 审核与主控复盘一致——审计面已被反复用于选择、自适应多重试验、旧信息改写、口径不稳、split 参数脆弱、生产指标替代研究指标。主控综合：一致为主体；分歧两点（round_212 同哈希是引擎挡回而非 pi 重复；两线复现降级为必要非充分而非无价值）；处置全部采纳。
- 动作：两线 `STOP`、Dagu 停运、队列移入 `DIRECTIVE_QUEUE/frozen/`；冻结 5 条（F1 PERMENT_TURNOVER_SPLIT × UW_CHG、F2/F3 VFPULCER_TURNOVER_SPLIT × PERM_ENT / × UW_CHG、F4 RP_CHANGE × MFI、F5 QA8 对照）；未触碰面盘点与一次性边际检验方案预登记；全文 `frameworks/etf_rotation/ETF_FREEZE_REPORT_20260921.md`。
- 停线前最后落地：pi round_213（第 63 阶段，`--all` CONSISTENT）：NS67A `split[VOL_SPIKE_FREQ; 日内最大回撤] × RP_PERM_ENT_D3` 发现 3.01 / 审计 +40.8 **t 2.36**（Sonnet 原版 2.67 / t 1.37，年度不全同向）；PERMENT_TURNOVER_SPLIT w40 / w60 × UW_CHG 审计 t 2.12 / 2.01——**pi 侧窗口不敏感，与 Sonnet S68 的"w20 专属"相反**，F1 的窗口敏感性两线不一致，记为未决；单腿 HI/LO 各配右腿 t 全负，与 S68 一致（信息在差）。Sonnet round_688（S72 split 原子总表）被 STOP 中断：`SPLIT_ATOMS_TABLE.md` + csv 已落地、无 STATUS，可作留档参考。
- 前向账本两线 `forward_ledger.csv` 均为 1 字节（从未成功产出）——审计窗后数据未被账本看过；这是 F1–F4 评价面干净的依据。
- **一次性边际检验已由另一会话执行（14:22，`runtime_outputs/etf_frozen_marginal_eval_20260921/`，合同提交 `39566908`，预检 F1–F4 发现 t / 审计 bp 与冻结表 MATCH）**。干净面 2025-05-01→2026-09-17（H5 331 日 / 66 块）：F1 原始 H5 −4.6bp t −0.19、残差 +0.9 t 0.08；**F2 −39.6 t −2.00（H10 −2.33、H20 −2.94，三视界反向）**；F3 +4.5 t 0.19（H20 +147.5 t 2.47）；**F4 −25.9 t −1.05（H20 −84 t −1.51）**；四条全部 `LEAD_ONLY`。基准 QA8 在 2026 干净子段 H5 +40.0 t 0.94、H20 +242.5 t 2.50。该面对 F1–F5 已用，不得再评。主控结论：本轮挖掘新增可用因子 0 条；F2/F4 在样本外反向说明审计期显著是筛选产物；F3/QA8 的 H20 表现只作留档，不构成救援（H20 是看到 5.84 后才提出的并列视界）。
- **§45 主表六代表一次性干净段检验（USER 14:40 指令，主控执行，`runtime_outputs/etf_baselines_clean2026_eval_20260921/`，预登记 H5 t≥2 且 ≥5bp）**：2026-01-01→2026-09-17，166 日 / 33 块。**六条 H5 全部未过**：QA8 +40.0 t 0.94 / H10 +60.1 t 1.08 / **H20 +242.5 t 2.50**；CK04 +47.1 t 1.16 / H10 +138.7 t 2.27 / H20 +218.9 t 1.98；CR08 +19.3 t 0.59 / H10 +82.5 t 1.40 / H20 +174.0 t 1.83；CO36 +1.8 t 0.06；PA1 −13.7 t −0.34；S27B5 −21.6 t −0.75。判读：三条（QA8、CK04、CR08）三视界同向为正、H20 接近或过 2，但 H5 主门无一通过；三条归零或反向。段内两两秩相关最高 CO36–PA1 0.69，其余 ≤0.49。该面对六条已用。**结论：按 H5 合同，本线迄今无一条单因子在未挑选过的数据上过门；H20 上 QA8/CK04/CR08 有同向证据，但 H20 是事后视界，只能作下一次预登记研究的起点，不作认证。**
