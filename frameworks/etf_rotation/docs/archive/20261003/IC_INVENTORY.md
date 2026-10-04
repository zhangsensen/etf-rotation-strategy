# 历史存档：2026-10-03 清理前版本

本页仅供追溯旧规则与版本沿革，不作为当前执行指令。
[返回现行入口](../../../README.md) · [归档索引](README.md)

原文内部的“当前”“最新”仅描述原撰写时点；下列正文仅调整了相对链接。

---

# ETF IC 因子库

用途：接手者一次查询即可了解挖过哪些定义、有IC与未检出IC的数量及所属机制，避免重复挖掘。
仅含固定14只ETF、8组、close(D)信号、open(D+2)→open(D+7)标签，不并入其他项目。

## 查询

当前快照入口：`runtime_outputs/etf_rotation_research/IC_INVENTORY_LATEST.json`。
继续挖掘时，先用本库选不同家族的已有 IC 线索或确认未测方向；父因子的自适应迭代入口、全库查重与冻结后正式登记步骤见 [ETF IC autoresearch 规则](../../ETF_AUTORESEARCH_PROGRAM.md)。试验目录不增加本库的累计登记数，只有原正式 runner 完成审批与计算后才更新库存。
截至2026-09-26最新快照为`ic_inventory_20260926_563_r10`：累计登记563、索引540、正IC201、负IC124、近零62、不可计算153、基础历史IC线索**17**。第1–9轮各三条均未新增基础线索；R10焦煤滞后项`coal_delayed_response_60`（IC +0.0503、HAC t +2.16、n=284、分年同正、剔组全正）为campaign20首条新增基础线索；R08恒生科技符号不对称项显著负向（IC −0.0956，HAC t −2.87）在反向观察清单，不翻向；各条 signed IC/HAC t/n 与冗余注记见[逐轮进度](../../ETF_IC_CAMPAIGN20_PROGRESS_20260926.md)。旧批口径不变；完整逐条数字以本地快照为准。
每次成功更新自动指向新的完整快照；旧快照保留。初版v1遗漏外部8条，v2起纳入并核对登记映射。
先读其中的 `README.md` 和 `manifest.json`；后者记录输入、统计窗口规则、重建命令及登记差额。
v4补齐分年指标、定向年份角色和显式基础线索入口；预算不一致或登记无法关联时拒绝发布新快照，保留原入口。

| 文件 | 用途 |
|---|---|
| `positive_ic.csv` | 主描述视图：有效质量/时序面上的 IC ≥ 0.01 |
| `negative_ic.csv` | 主描述视图：有效质量/时序面上的 IC ≤ -0.01，保留原方向 |
| `near_zero.csv` | 主描述视图：有效质量/时序面上的 -0.01 < IC < 0.01 |
| `uncomputable.csv` | 缺少数值IC或质量、标签、时序面无效；原始IC仍在完整记录中 |
| `reverse_watch.csv` | 既有反向诊断视图：IC≤-0.01、HAC t≤-2、块t≤-2；覆盖另行标注 |
| `basic_ic_leads.csv` | 通过既有基础筛选的历史线索；含公式、方向、评价面、n、分年IC/t及剔组诊断 |
| `has_ic.csv` / `no_ic.csv` | 兼容性视图，沿用 legacy 基础筛选通过/未通过状态，不是主IC数量 |
| `pending.csv` | 兼容性视图，沿用 legacy 未计算/无效/覆盖不足状态 |
| `all_factors.csv` | 所有可定位定义、方向、机制配置、IC、HAC t、块t、有效日及证据路径 |
| `families.csv` | 描述性方向计数与 legacy 筛选计数分列，及是否应避免重复已测变体 |
| `registrations.csv` | 每条实现版本登记与语义定义的映射，用于核对累计预算 |

逐条先读 `directional_classification`、`signed_ic`、`n`、`coverage_status`，再看诊断列。
`ic_window_start` 表示主IC评价起点，`label_exit_cutoff` 是标签退出截止日，不能把它误读为最后信号日。
`y2025_role=DIRECTION_SELECTION_ONLY` 的候选只用2026段作主IC；其他候选的两年列也是已见历史诊断。
`y2025_*` / `y2026_*` 直接列出有效日数、IC、HAC t和块t；缺失值留空，不填零。
按t排序仅方便查询，不说明不同样本窗的结果可以直接比较。

绝对IC 0.01 是现有幅度参考，仅用于描述分档，不是有效因子门槛。有限IC即使覆盖不足仍显示 signed IC，并标注 coverage insufficient；这不构成支持或认证。无效质量/标签/时序记录不作为可信 signed IC 分类，但完整记录保留原始数值和原因。负IC保留原值，不自动翻向。`has_ic.csv` 和 `no_ic.csv` 只是 legacy 筛选兼容视图，不应当作正/负IC主分类。
家族按来源类型和机制名归并窗口与方向别名，不把一条失败扩大成整个经济机制无效。
新批次可在每条定义中预先声明 `family`，按经济机制归并多个不同统计量；`family_basis` 记录声明或名称推导的来源。
家族表以 `indexed_definitions` 统计索引数，`computable_definitions` 统计有效描述IC数；
历史字段 `tested_definitions` 仅保留为索引数兼容别名，包含未判定记录，不可用来声称实际检验次数。
同一失败定义、同一数据、同一标签，无新信息不重复跑；家族还有待判项时先查原因。
预算登记包含实现版本，库按语义定义归并，两者数量不必相等；必须逐条检查登记映射。
不能将版本归并差额误称缺失因子，也不能将真正无法定位的条目归为无IC。

## 更新

每次新批次或重判后，从最新全量重判 `summary.csv` 生成新快照，不覆盖旧目录：

```bash
.venv/bin/python frameworks/etf_rotation/scripts/research/build_ic_inventory.py \
  --summary runtime_outputs/etf_rotation_research/vix_risk_merged_539/summary.csv \
  --external-run runtime_outputs/etf_rotation_research/group_next8_20260922_v4 \
  --output runtime_outputs/etf_rotation_research/ic_inventory_NEW
```

使用最新全量输入及尚不存在的输出目录。脚本不启动行情计算。
重判时必须显式传入与登记账本相符的 `--conditional-budget`，不能沿用历史默认预算。
保存结果合并后建库时，`build_ic_inventory.py`从合并摘要目录的`verdict.json`读取累计登记数，并与PLAN账本逐条核对；该脚本本身没有`--conditional-budget`参数。上句所述显式预算参数适用于前置重判命令，不适用于本建库命令。
分类读取原始基础IC筛选字段，不读取受旧增量门影响的 `factor_evidence_pass` 作为分类依据。
2025定向的定义使用2026段；原冻结方向使用全窗。冻结阈值不因入库而改变。
未进入正式计算的固定范围结构性预检拒绝可用重复参数 `--structural-rejection <json>` 一并索引；文件需含完整 `config`、`candidate_ids`、`rejections`（逐候选记录 `reason` 和日期计数）。这类定义进入不可计算/PENDING，并保留拒绝原因，不增加正式注册预算。
机器配置中的机制说明与历史PLAN一起可定位；源码公式仍在相应运行的保存源码中。
全部生成文件只留本地，代码和说明可按项目代码检查流程提交。

## 基础线索的重复性检查

```bash
.venv/bin/python frameworks/etf_rotation/scripts/research/audit_ic_lead_redundancy.py \
  --snapshot runtime_outputs/etf_rotation_research/ic_inventory_20260924_clean_v4 \
  --output runtime_outputs/etf_rotation_research/ic_lead_redundancy_NEW
```

只读取保存的分数及有效IC日期。每对候选按各自评价面取共同有效日期，计算
`mean(abs(每日8组截面排名相关))`，不是 `abs(mean(每日相关))`。
`pairs.csv` 保留两条候选、共同样本数、首末日期、相关性及0.7注记；`leads.csv` 汇总最近邻。
这只检验当前基础线索之间的重复性，不覆盖全库所有定义，也不证明家族独立或组合有增益。
高相关仅注记，不删除IC、不自动翻向、不重估权重。增量检验未做时标 `NOT_TESTED`。

## 自动发现库（v2）

后续统一命令见 [ETF 自动试验规则](../../ETF_AUTORESEARCH_PROGRAM.md)。本地跨 campaign 全量记录在 `runtime_outputs/etf_autoresearch_ic/library/library.csv`，含探索/改进、父子关系、精确 IC、HAC t、n、分年值、源码和失败原因。每次试验后自动重建。该库包含未进入正式 PLAN 的自适应试验；与本页历史正式库分别计数，不把多次迭代冒充独立因子或认证。
