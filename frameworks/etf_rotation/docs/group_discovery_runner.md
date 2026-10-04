# 八组历史发现入口

范围：固定14只ETF、八组经济分类、D收盘信号、D+2至D+7标签。
这是独立的发现诊断入口，不是旧v4.3裁判迁移完成，也不提供认证或交易许可。
当前执行条件以[IC挖掘规则](IC_MINING_RULES.md)为准；以下既有批次与命令是历史记录，不是新批授权。

## 首批配置

[group_discovery_daily_v1.yaml](../configs/group_discovery_daily_v1.yaml)固定24条日线候选、
方向、窗口、K=2、组内入场等权、组间等权、HAC滞后10与筛选门。
24条包括先验方向相反的动量/反转假设，均计入96条预算上限；并非24个独立机制。
单因子pilot复用同批momentum_20定义，不增加新候选；全部运行仍保留揭盲记录。
首批未覆盖分钟、份额可用时点来源核验和外部货架增量，不得声称六类机制已完成。

后续固定配置为[group_discovery_minute_v1.yaml](../configs/group_discovery_minute_v1.yaml)的16条分钟候选，
以及[group_discovery_share_v1.yaml](../configs/group_discovery_share_v1.yaml)的8条份额候选。
分钟特征必须有240根完整且有效的当日bar，再做5/20日平滑；份额采用20/40日回看。
份额可用日来自导入脚本的下一交易日假设，不是原始公告时间戳；源日期相同的重复记录拒绝，
不同源日期落在同一可用日时取最新源日期，超过7个自然日未更新置缺失。
份额结果只能是该假设下的研究线索，不能标成真实发布时间核验通过。

后续还有两批独立登记：

- [自身状态](../configs/group_discovery_self_state_v1.yaml)：8条，沿用原分数方向，用本组先前60日均值和标准差
  标准化当前分数；当前D不进入均值/标准差。选择来自已见发现期的组内赢家／输家画像，非独立确认。
- [净值基差](../configs/group_discovery_nav_v1.yaml)：8条，用估值日未复权收盘价配同日单位净值，
  只在记录公告日之后的可用日进入特征。取截至D已披露的最新估值日，迟发旧季度净值不覆盖更新估值。
  没有估值日价格不换日期配对；QDII时钟不同，称已披露NAV基差，不声称同步公允价值折价。

画像入口为`scripts/research/profile_etf_group_mechanisms.py`。其组固定效应均值仅作发现面描述，
不写入交易特征、不作为样本外证据；具体公式必须重新登记后通过因果重算检查。

[交互批次](../configs/group_discovery_interaction_v1.yaml)定义16条八组秩乘积，不拟合权重。
旧冻结联合门要求IC差与头部超额差均通过，历史结果保留。
当前因子挖掘分别报告两腿IC增量与收益增量：收益失败不否决IC线索，但不能宣称有新增收益。
逐组剔除要在剩余七组重新计算两个秩算子；不能只删除八组复合分数的一列。
已运行批次的该项诊断补正在其`CORRECTIONS.md`和`loso_recomputed_v1/`中记录，原始输出不覆盖。

主指标为H5组间秩IC。头部收益主基准B8，原池对照B14，两者均输出。
原始数据中有缺失、停牌或零振幅时不会填补价格；全部24条采用相同的D日特征齐备日期。
标签缺失剔除整个评价日，不能换组选票。年度分解按退出日期剔除跨年标签。
评分日有重叠H5标签，行数不等于独立观测数；不将重叠收益连续复利为策略净值。

## 运行与产物

以下为历史复现命令（旧配置不满足新运行的显式evaluation_start要求，不能直接用来开新批）。
新批按当前规则先审签冻结；每次使用新的run-id，已有目录拒绝覆盖：

```bash
uv run --no-sync python frameworks/etf_rotation/scripts/research/discover_etf_groups.py --run-id group_daily_v1_pilot_20260922 --pilot
uv run --no-sync python frameworks/etf_rotation/scripts/research/discover_etf_groups.py --run-id group_daily_v1_batch_20260922
uv run --no-sync python frameworks/etf_rotation/scripts/research/discover_etf_groups.py --config frameworks/etf_rotation/configs/group_discovery_minute_v1.yaml --run-id group_minute_v1_batch_20260922
uv run --no-sync python frameworks/etf_rotation/scripts/research/discover_etf_groups.py --config frameworks/etf_rotation/configs/group_discovery_share_v1.yaml --run-id group_share_v1_loaderfix_20260922
PYTHONPATH=frameworks/etf_rotation/src uv run --no-sync pytest -q frameworks/etf_rotation/tests/test_etf_group_discovery.py frameworks/etf_rotation/tests/test_etf_mining_referee.py frameworks/etf_rotation/tests/test_canonical_data.py
```

运行产物仅保留本地`runtime_outputs/etf_rotation_research/runs/<run-id>/`：
PLAN、源码配置快照、输入哈希、动态泄漏检查、覆盖表、逐日分数和选择权重、
双基准收益、全量筛选表、年度分解、逐组剔除、REPORT与verdict。
输入或源码在运行中变化则不出有效判定；读取规范根只读，不写规范数据。

## 证据限制

### IC优先报告（用户2026-09-22明确）

挖掘先报告覆盖合格的IC基础线索，不以B8收益失败否定排序信息。
`scripts/research/report_group_ic_evidence.py --run-id <new-id>`读取冻结80条v3结果，
输出全部候选、IC线索、反向观察和分层计数；不重算因子、不改方向或阈值、不覆盖v3。
IC基础通过、预算校正、经济指标、覆盖合格经济支持与联合通过分别命名。
负向均值/HAC/块t仅进入REVERSE_WATCH；翻向后同面重跑仍是历史发现。
正式新批必须保存数值完整PLAN；本报告模式不授权新候选或改变检验族。

新日线机制入口使用`source_type: daily_mechanisms`及独立公式模块。
用户授权后，master审核公式并提供配置/源码绑定的`--approval <local-json>`；
run-id、候选清单、新增数量、104+新增数的条件预算必须完全相符，否则不评价。
公式只读因果日线，复用当前IC裁判、输入封印及截断/扰动/重新加载规范源的前视检查。
外部next8的8次尝试计入预算但不混入当前候选。审签不是独立确认或跨入口身份认证。

### 2026-09-22：现有80条的窗口纠正入口

旧 `rejudge_group_campaign_2025.py` 已禁用执行，仅保留历史源码；其本地 `rejudge_2025/`
报告已标SUPERSEDED。它遗漏覆盖和交互增量要求，不得使用其“机制门1条”作为完整门结论。
冻结80条v3为当前重判依据。排序指标与经济指标的原始交集并非空：
own_downside_20_60同时通过两类指标，但只有226日，未过360日覆盖；不能据零入围推断两种能力分离。

原批次全段结果保留作历史记录，不能代替用户要求的2025起判定。
使用 `scripts/research/rejudge_etf_groups_2025.py --run-id <new-id>` 重判冻结的80条，
输入为原运行保存的分数、标签、完整日历和覆盖掩码，不重建或改变公式。
评价信号自2025-01-01起、标签退出不晚于2026-09-17，2023–24仅画像。
B8仍为收益主基准、B14强制对照；排序门、收益门、96项预算诊断分别报告。
360日覆盖门不变，不足的标记为覆盖不足；交互必须报告对两条单腿的配对增量。
新输出在本地 `runtime_outputs/etf_rotation_research/rejudgments/`，不覆盖原结果。
它先复现原IC和收益统计，再变更评价窗口；CSV数值使用round-trip读取以保留近似并列的顺序。
交互父分数须保留原读取及成员展开再聚合的算术，逐组剔除在重排两腿之前完成。
这是已见历史上的口径纠正，不是独立认证，不新增公式；仍记录评价面复用。
下文预算耗尽说明属于原源码版本计数，不应阻止这次冻结候选重判。

### 后续有界发现与入口状态

用户随后授权继续固定14只/八组发现，Luna执行、master审核；追加批次上限8条。
`group_next8_20260922` 是已结束的探索批，不是新通用引擎：6条组结构定义被拒绝，
两条广度定义与既有效率分数重复，未接受新因子。其运行入口已禁用，保留源码与本地快照溯源。
不能把常数单成员值与不同尺度多成员值直接排序后声称发现经济机制。
后续公式需先由master确认再冻结运行；失败设计仍计尝试，不在结果出来后修公式重置预算。
原96不清零，追加8后的104校正仅是条件诊断；历史未登记搜索未知，不声称累计认证有效。

历史已见，筛选入围也只能是LEAD_ONLY；正态尾部预算校正是本批渐近诊断，不能洗掉历史选择偏差。
调整后的开盘收益是研究标签，不保证成交，无成本净收益结论。
动态截断和未来扰动通过，只证明所测代码因果性，不认证历史数据版本或源头发布时间。
本入口新增文件锁下的累计PLAN预算检查，按来源、公式名、窗口、方向和源码版本去重；
失败但已登记的源码版本也占预算。因此工程修复可能保守地多占预算，不代表看过额外收益候选。
这不是跨其他入口的强制账本；历史搜索不被清零，前向认证仍未实现。
各来源批次内部使用共同有效日期；不同来源覆盖不同，不能仅按各批全段t值高低认定增量。
公式或筛选配置变化必须是有记录的新实验，不能覆盖旧失败或重新命名旧面为样本外。

本轮登记上限已经达到96个源码版本，实际有结果的候选为80条，另外16个登记来自读取阶段失败版本。
继续新增需要明确预算或计数口径决定；不能把预算用尽解释为轮动研究没有价值。
