# ETF IC 因子库

用途：查定义、公式、方向、历史变体、signed IC 与证据，避免没有新信息的重复试验。范围固定为 14 ETF / 8 组、close(D) 信号、D+2→D+7 标签；ETF 与个股分开，正式历史库与自适应库也分别计数。

## 当前查询入口

路径相对仓库根：

| 结果面 | 入口 | 解释 |
|---|---|---|
| 正式历史库存 | `runtime_outputs/etf_rotation_research/IC_INVENTORY_LATEST.json` | 读取 `snapshot` 后查看该目录的 `README.md`、`manifest.json` 与下列表格 |
| 自适应发现 | `runtime_outputs/etf_autoresearch_ic/library/library.csv`、`library.json` | 全部候选、正负 IC、公式/方向/窗口、源码和失败记录；JSON 同时含 `campaign_progress` |
| 单批实际完成情况 | [只读进度报告命令](ETF_LUNA_DAGU_OPERATIONS.md) | 按冻结计划、请求与候选终态核对；不能仅信原 COMPLETED |

不在说明文档维护另一套“最新总数”。查询时记录快照名与生成时间，分别列累计及本批。自适应库不增加正式 PLAN 登记数，reference 复算也不计新增候选；同历史反复选择不是独立确认。

## 正式快照字段

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

## 更新正式快照

有新正式结果或重判时，从最新全量合并摘要生成尚不存在的新快照；不覆盖旧目录。先读当前 manifest，沿用全部外部登记和结构拒绝输入，再补入本次新结果，不能漏掉旧输入。

```bash
.venv/bin/python frameworks/etf_rotation/scripts/research/build_ic_inventory.py \
  --summary PATH_TO_LATEST_COMPLETE_SUMMARY/summary.csv \
  --external-run runtime_outputs/etf_rotation_research/group_next8_20260922_v4 \
  --output runtime_outputs/etf_rotation_research/ic_inventory_NEW
```

占位路径须替换为当前全量输入。可重复传入 `--external-run` 与 `--structural-rejection`。结构拒绝文件需含完整 config、candidate_ids、逐候选 reason 与日期计数；不增加正式登记预算。

该脚本只读保存证据，不启动行情评价。它从摘要目录 `verdict.json` 读取累计登记数并核对 PLAN 映射；没有 `--conditional-budget` 参数，该参数属于前置重判命令。输入预算不一致或登记无法关联时拒绝发布，原 LATEST 保持不变；差额不能隐去。

分类采用原 IC 与基础诊断字段，不能用含收益/增量联合门的 `factor_evidence_pass` 代替。2025 定向候选主统计只用 2026 段，原冻结方向使用对应全窗；入库不改变冻结阈值。

## 自适应库及诊断

当前 workflow 在结果变更后自动重建自动库。列中 `formula`、`direction`、`first_signal/last_signal`、`result_path`、`command` 和源码哈希便于复算；冻结哈希与当前文件哈希分开，源码不匹配保留原数字并明确证据无效。`ic_recorded` 与 `parent_replaced` 分开解释。

正式基础线索的冗余旁报可用 `audit_ic_lead_redundancy.py --snapshot <当前快照> --output <新本地目录>`。它按双方有效日期计算 `mean(abs(每日八组排名相关))`，0.7 仅作注记；不删除 IC、不翻向，不代表全库独立性或组合增益。未做增量标 `NOT_TESTED`。

全部生成快照、CSV、日志和报告仅留本地。历史数字与旧命令见[清理前存档](archive/20261003/IC_INVENTORY.md)。
