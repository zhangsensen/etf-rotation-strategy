# 历史存档：2026-10-03 清理前版本

本页仅供追溯旧规则与版本沿革，不作为当前执行指令。
[返回现行入口](../../../README.md) · [归档索引](README.md)

原文内部的“当前”“最新”仅描述原撰写时点；下列正文仅调整了相对链接。

---

# ETF 轮动开发入口

当前研究以 [ETF轮动方法论](../../../ETF_ROTATION_METHODOLOGY.md) 为准：固定14只、八组经济分类，
先研究组间因子，再研究组内增量。分类见 [分组说明](../../candidate14_economic_groups_v1.md)。
现有引擎和旧参数见 [工程交接](../../../ENGINEERING_HANDOFF.md)，不代表八组裁判已经实现。
旧方案及验收记录的用途见 [文档状态索引](../../document_status.md)。
当前仅做因子挖掘、IC主评；数值硬门、旁报指标、分工与开跑条件见[IC挖掘规则](../../IC_MINING_RULES.md)。

2026-09-18历史本地结论与来源核对见仓库根
`runtime_outputs/etf_research_handoff_20260918/HANDOFF.md`。
源码阅读顺序见[策略来源指南](../../../RESEARCH_GUIDE.md)。生成报告与账单不随代码提交。
旧因子挖掘的公式、WFO、方向/权重和标签问题见
[因子挖掘来源与证据边界](../../../FACTOR_MINING_PROVENANCE.md)。

ETF 轮动今后在当前 `gpu_ml` 仓库开发。本目录整合本机 `-0927` 的研究源码，
原项目保持不动。当前维护池和下载器继续使用仓库根目录的实现。

## 目录与来源

- `src/etf_strategy/`：原有因子、WFO、换仓缓冲、成本、VEC/BT 支持与 GPU 模块。
- `scripts/`：原有研究、回测与诊断脚本；历史脚本的依赖产物需显式提供。
- `tests/`：原有回归测试及新数据读取边界测试，新增测试在临时目录合成行情。
- `configs/`：保留旧49只与命名含`current20`的历史研究配置；当前14只的经济分组见`etf_candidate14_economic_groups_v1.yaml`，分类配置不等于已启用组间引擎。
- `SOURCE_MANIFEST.json`：来源提交及迁入文件原始 SHA256，用于追溯后续修改。
- 根目录 `scripts/etf_rotation.py`：新维护数据 → 迁入因子代码的只读 smoke 入口。

来源为本地 `/home/sensen/dev/projects/-0927` 的提交
`4e5d1fbde56b0094db976cbebb6cf5020105bd98`，MIT 许可保留在 `LICENSE`。
四个源文件仅清理行尾空白和末尾空行，清单列于 manifest 的 `migration_changes`；
迁入当时除文档字符串空白外，Python AST 与原始源码一致；后续执行层修复见下文。
迁入清单只包含代码、必要配置、测试与许可。未复制数据、缓存、模型、回测输出、
历史报告和封版产物；未迁入旧下载器、QMT 更新脚本和每日信号发布入口。
历史研究脚本引用的封版文件与结果不因此自动可用。

## 新数据入口：从仓库根目录运行

复用根项目的 uv 环境；本目录不创建第二套项目锁文件。
`requirements-research.txt` 声明研究包需要的附加依赖，`--with-requirements`
使用 uv 临时依赖层，不修改共享环境。此工作树没有 `.venv` 时，先设置：

```bash
export UV_PROJECT_ENVIRONMENT=/home/sensen/dev/projects/gpu_ml/.venv
```

检查当前 20 只池并计算两个参考因子（日期须替换成已完成且已入库的交易日）：

```bash
uv run --no-sync --with-requirements frameworks/etf_rotation/requirements-research.txt \
  python scripts/etf_rotation.py \
  --data-root /home/sensen/dev/projects/gpu_ml/data/etf_rotation_v1 \
  --as-of 2026-09-17
```

默认读取全部维护标的，可用 `--roles candidate` 限定当前候选。
唯一维护配置为根目录 `config/etf_rotation_universe_v1.json`，不另建一份 20 只清单。
数据根必须显式传入，不自动猜测股票库或旧 ETF 库。命令只输出工程摘要，
不生成排名、收益、下单信号，不修改行情，不调用供应商。

读取器用 `1d` 原价与 `adj_factor` 构造截至日复权研究视图，量额不复权；
截止日之后的因子不进入归一分母。保留交易所后缀、上市前和缺日的 NaN；
不填价格 1、不前向填充 OHLCV。缺调整因子、代码错配、重复日期、非法价量、
尾日期不达标时拒绝读取；生产更新锁被占用时拒绝读取。
原价仍是后续成交核算的基础，复权视图不是可直接成交的报价。
当前分类仅供研究选池，不代表历史 PIT 成分股或历史可知标签。

以下为旧自动挖掘入口（不是当前家族裁判）：读取全部维护数据，20只均可在满足120日历史后进入横截面排名。
角色只作为维护和分类元数据，不擅自转成交易资格。入口示例：

```bash
PYTHONPATH=frameworks/etf_rotation/src .venv/bin/python \
  frameworks/etf_rotation/scripts/run_automated_factor_mining.py \
  --canonical-data-root /home/sensen/dev/projects/gpu_ml/data/etf_rotation_v1 \
  --universe-config config/etf_rotation_universe_v1.json --as-of 2026-09-17 \
  --mining-config frameworks/etf_rotation/configs/automated_mining_current20_v1.yaml \
  --output runtime_outputs/new_empty_run --ledger runtime_outputs/local_ledger.duckdb
```

上述旧入口的历史结果及统计口径见[已归档自动化方案](../../../ETF_AUTOMATED_MINING_PLAN.md)。

## 验证

从仓库根目录运行独立测试配置，避免与其他策略的同名测试冲突：

```bash
uv run --no-sync --with-requirements frameworks/etf_rotation/requirements-research.txt \
  python -m pytest -c frameworks/etf_rotation/pytest.ini frameworks/etf_rotation/tests -q
```

旧测试中需要旧行情库的测试会跳过；它们的跳过不能作为回测通过的证据。
本次整合验证的是迁移回归与新数据/因子接线，不是完整 WFO→VEC→BT 收益复现。

## 旧研究入口与数据边界

`scripts/run_full_pipeline.py`、`src/etf_strategy/run_combo_wfo.py` 等保留旧行为。
它们不是根目录只读 smoke 命令的下游，不能直接喂入新数据目录。
复现历史实验前须显式准备旧格式的研究配置、输入和本地输出路径；
可通过 `WFO_CONFIG_PATH` 指向本地配置，并在配置 `data.data_dir` 中引用
`/home/sensen/dev/projects/-0927/raw/ETF/daily`，不复制或重命名这批行情。
旧 loader 需要 `*_daily_*.parquet` 和 `adj_open/adj_close/...` 等字段；
`fund_share`、`margin` 等是该旧数据根下的邻接目录，尚未纳入新日更契约。

旧脚本按项目根寻找 `results`、`.cache` 等目录，必须在本目录运行并将
`src`、`scripts` 加入 `PYTHONPATH`。这些输出已被本目录 `.gitignore` 排除。
任何提交仍须执行仓库根的 `scripts/guard_no_data_in_git.sh`；忽略规则不是检查豁免。
不要将旧 `raw`、`results`、`sealed_strategies` 目录整体复制进来。

## 历史研究实现与边界（截至2026-09-21）

以下记录旧版本的实现和结果，不是重开指令。当前研究设计以[方法论](../../../ETF_ROTATION_METHODOLOGY.md)为准；旧实现不能直接当作组间研究已落地。

### 旧14只横截面候选生成入口

2026-09-21版本的14只候选生成入口为
`scripts/research/pi_glm_mining/discover_from_outcomes.py discover`，核心实现为
`src/etf_strategy/core/etf_outcome_discovery.py`。它读取 v3 家族目录的因果原子，用固定发现面
的可执行 H5 结果做赢家/输家画像，再输出有限候选；结果标签不能进入公式、人口、缺失处理或
时间戳。候选随后交给 v4.3 PLAN 与裁判，发现器本身不作认证。

`run_automated_factor_mining.py`、`run_factor_mining.py` 和历史 pi/Sonnet round driver 只保留为
旧实验与审计重放入口，不得再产出当前候选。`run_family_adjudication.py` 是目录裁判/治理入口，
不是候选生成器；`run_regime_switch_mining.py` 回答独立的进攻/防守状态问题，不属于横截面因子。

### 暂停的ETF状态切换支线

该阶段主任务曾恢复为ETF候选池的横截面IC因子挖掘。原20只全角色排名会把货币、国债和宽基混入
小横截面，已判定需要重写；以下状态切换工作回答的是独立的现金/防守
问题，不是排序因子结果，停止继续扩代。归因见
[`ETF_FACTOR_TASK_ROOT_CAUSE.md`](../../../ETF_FACTOR_TASK_ROOT_CAUSE.md)。

该版本家族优先挖掘器使用14只`candidate`、共同样本Spearman IC、全搜索pooled max-stat、5/10/20方向门
和跨代alpha预算。ETF家族通过本目录内的插件注册加载，累计账本与个股完全分离。旧日线3家族及
60分钟日内路径家族最终均失败，组合WFO关闭。证据在
`runtime_outputs/etf_family_engine_v5_independent_20260919/`。

### 独立家族插件引擎

ETF家族挖掘只导入`etf_strategy`本地模块，不依赖`alpha_mining`、个股因子注册表、个股标签、裁判或
账本。新增信息家族只需增加`src/etf_strategy/core/families/<name>.py`注册provider，并增加对应的
`configs/automated_<name>.yaml`后写入adjudication配置；主运行器和裁判不再增加`if/elif`分支。

历史V7裁判/治理入口为`scripts/run_family_adjudication.py`；它不是组间候选生成入口。该版本流程包含共同样本IC、pooled与家族内max-stat、
5/10/20方向门、跨代alpha预算、逐ETF剔除、相对已录取因子的横截面残差IC、产物哈希和独立累计
DuckDB账本。V7仍为0个通过家族，证据在
`runtime_outputs/etf_family_engine_v7_final_20260919/`。

### 家族广度目录

Claude协作扩展版见 [FAMILY_BREADTH_V3.md](../../../FAMILY_BREADTH_V3.md)。v3目录为45个家族、179个原子，
归入11个经济轴；当时规划的入口配置为`configs/family_adjudication_breadth_v3.yaml`，不作为当前重开授权。
历史 [v2](../../../FAMILY_BREADTH_V2.md) 的31家族/147原子/10经济轴配置保留。
本轮仅验收信息覆盖与去重，没有运行新一代IC筛选。以下25家族/135原子的结果属于v1历史版本。


#### 分钟机制独立诊断

`configs/family_intraday_tail_reversal_jump_v1.yaml`、
`family_intraday_return_distribution_v1.yaml` 和
`family_intraday_turnover_asymmetry_v1.yaml` 是独立的分钟发现面，provider 位于
`src/etf_strategy/core/families/intraday_novel_mechanisms.py`。它们只读取完整的 D 日
1m/5m/15m/30m/60m bar，在 D 收盘形成信号；诊断标签从 D+2 开盘开始计算 H5/H10/H20，
不写共享裁判、shelf 或正式 ledger。尾段成交额原子使用成交额加权价格冲击，避免把既有的
时段成交构成重复登记。独立诊断输出只保留在本地 `runtime_outputs/`，没有晋级即不代表认证。

`configs/family_catalog_v1.yaml`是自动挖掘前的唯一家族入口。它把过去混在`price_path`中的机制拆成
25个一对一注册的信息家族，共135个原子：方向趋势、价格位置、下行风险、日线形态、路径效率、
收益尾部形态、交易活跃度、价量耦合、市场敏感度、类别状态、序列依赖、跨ETF滞后传导、
日内收益路径、日内成交结构、日内VWAP位置、日内趋势一致性、日内波动结构、日内量价冲击、
振幅记忆、gap响应、尾段成交价格冲击、尾段跳跃不对称、日内收益分布、gap波动分配和成交额变化波动。
目录阶段只允许`atomic`，组合表达式留给后续自动挖掘。

运行`python scripts/validate_family_catalog.py ...`会在不读取未来收益标签的前提下验证全部原子可物化，
并阻止跨家族横截面排序相关系数达到0.98的重复机制。基金份额申赎、IOPV/NAV折溢价、底层指数跟踪、
持仓漂移和一级市场微观结构在缺少点时数据前保持关闭，成交额不得冒充这些ETF专属数据。

多源V9统一裁判实际运行135个原子、25个家族和10个冻结经济轴，覆盖日线及1m/5m/15m/30m/60m分钟
诊断；第16代以54,401次置换使最严格的轴级Holm阈值可达，正式认证仍为0。正式清单同时固定
100个实际输入文件及二级类别映射配置的内容哈希，发现层按原始横截面IC、5/10/20日同向、
2021–2023至少2年同向、已见审计同向、
14只逐标的剔除和横截面rank相关小于0.70筛选；纯窗口变体自动归为一个机制，成交时段构成、低波、
趋势、回撤和资金压力还执行跨家族子机制上限。每个家族最多保留一个代表，最终从40个门内候选
保留16个因子，覆盖16个家族和7个经济轴；相关矩阵有效因子数9.76，最大两两相关0.6945。
候选表位于本地`runtime_outputs/etf_ic_factor_shelf_v11_20260919/`，正式裁判位于本地
`runtime_outputs/etf_family_multisource_v9_20260919/`，其状态明确为
`discovery_candidate_not_certified`，不能表述为独立样本外认证或策略许可。

ETF 主问题是“何时进入进攻、何时进入防守”。独立入口
`scripts/run_regime_switch_mining.py` 使用 `configs/regime_switch_current20_v1.yaml`
固定进攻/防守篮子，以 close(D) 形成状态、open(D+2) 执行，标签是未来 5/10/20 个开盘的
进攻篮子减防守篮子收益。预声明的2022与2025-01-01至2026-09-17承担方向一致硬门，
2023–24只检查显著负伤害，2020与2021只作诊断；多重检验按状态家族分层，并写入独立
`etf_regime_attempts` DuckDB 账本。旧自动挖掘的横截面 rank IC 结果降为第二层历史诊断，
不能作为状态切换第一层的晋级证据。

首轮修正版累计承担958次账本尝试，只有1个表达式通过四块×三周期方向硬门，家族分层检验为0，
最终晋级0。证据只在本地`runtime_outputs/etf_regime_switch_current20_v2_20260918/`，未来确认起点为
2026-09-17之后的新数据。

加入6个进攻篮子收益、相对防守和回撤原子后，V5共评价881个表达式；114个通过方向门，
105个通过完整状态硬门，其中32个含ATTACK原子。跨代账本累计3601次后家族Holm仍为0，
所以当前只有发现候选、没有认证因子。证据位于
`runtime_outputs/etf_regime_switch_attack_v5_20260918/`。

策略审查：`REWRITE`，Mixed（选池、排序、执行），噪声风险中高。
研究实验需固定池、公式、时间合同和基准。

- 原 VEC 的 `T1_OPEN` 实现读取 `t-1` 因子、在 `t+1` 开盘成交；不能当成
  “D 收盘信号、D+1 开盘成交”来解读。正式新回测应显式统一时间合同。
- 原因子质检的 close→future close 是研究标签，不能当成执行收益。
- 原回测入口有价格填充行为；止损修复仍沿用该数据口径。
- 原价格位置因子会把窗口不足变为 0.5；新 `reference_factors` 在适配边界
  强制满窗掩码，旧因子实现保留原样以便比较。
- 原 holdout 曾参与反复候选筛选，不是新实验的独立确认样本。
- 当前跨源行情差异仍需参考根目录 ETF 文档与最新 QA；当前读取器只验证日线基础结构。
- 旧组合需要份额/融资数据的可获得时点及新鲜度确认；维护 20 只池不等于已迁移这两类数据。
- 当前前复权因子历史可能包含供应商修订；按截止日裁剪不是数据版本 PIT 认证。

新策略的预期合同：D 日收盘后形成信号，最早 D+1 开盘进入，按约定未来
开盘退出，计算双边交易成本；仍需实现成交可用性、分红/拆分与跨境溢价处理。
旧参数和旧收益均不构成新池的策略认证。本次不迁移实盘调度或订单执行。

相关模块：新行情链路见 `../../docs/data/ETF_DATA_PIPELINE.md`；
`alpha_mining/AI/scripts/concept_etf_rotation_*` 是合成概念篮子，
`alpha_mining/AI/etf_t0_dual_engine` 是分钟 T0 研究，均保留独立入口。

## 历史策略延长与模拟账单

`scripts/extend_legacy_data.py` 在指定的本地研究目录下载原 49 只池的日线、复权、
份额和融资增量。旧库和正式 20 只库保持不动，历史价格逐行保留；新增价格接续旧
复权锚点，成交量沿用旧引擎的“手”单位。这是复现研究口径，不是生产数据迁移。
同一输出目录只允许相同截止日请求；缓存响应不自动刷新为未来日期。

`scripts/build_statement.py` 将观察记录导出为 Excel、HTML 与净值图，核对成交重建的
现金加持仓市值是否等于引擎净值。附加导出依赖见 `requirements-statement.txt`。
完整原样复现和本次延长的命令与证据分别在本地
`runtime_outputs/etf_legacy_reproduction_20260918/` 和
`runtime_outputs/etf_legacy_extension_20260918/`，这些目录不进入 Git。

核对旧 BT 成交后确认的两项限制：`A_SHARE_ONLY` 未在封存 BT 实现中落实，
不能把回测池说成仅境内 ETF；配置中的个券 5% 止损也没有在该 BT 实现中执行。
“复现成功”指实际代码的回放，不代表所有配置宣称的风控均已实现。

## 固定成本止损执行修复

当前维护版本的 BT 和 VEC 已接入 `backtest.risk_control.etf_stop_loss`。
它是**成交均价下跌 5%**的保护线，不是从持仓高点回撤 5%。
默认 `etf_stop_enabled: true`；显式设为 `false` 可复现历史无止损版本，
不需要改变冻结的 5% 参数，也不放宽其他冻结检查。老仓库及封存源码保持不变。

- `etf_stop_execution: next_session_intraday`：买入后的下一交易日起每日有效，
  独立于旧 `stop_check_on_rebalance_only`（仅约束移动/ATR止损）。
- BT 在实际买入成交后的回调周期提交保护单，下一交易日开始由模拟经纪商撮合。
  触线按保护价，跳空低开按开盘价，手续费另计；不利用当天高低价提前决定开盘交易。
- 止损绕过普通轮动的最短持有期。成交后清理实际/影子持仓和持有天数；
  止损当天不为该标的生成新买入目标，后续调仓日可再次评估。
- 普通轮动卖出先撤掉保护单，避免双重卖出；止损释放的盘中现金不能倒流用于当日开盘买入。
- `etf_stop_start_date` 可指定首次启用的交易日，用于从相同旧持仓继续比较。
  日期以前保留旧交易路径；既有持仓的保护价仍基于其原买入成本。
- 不支持把该模式与旧 ATR/移动止损叠加；冲突配置报错。此次没有重做 WFO 或搜索止损阈值。

本地固定策略入口（必须先有原49只延长回放的配置与冻结候选）：

```bash
python frameworks/etf_rotation/scripts/replay_fixed_strategies.py \
  --reference-run runtime_outputs/etf_legacy_extension_20260918 \
  --output runtime_outputs/my_stop_run --stop-loss .05 --activate-on 2026-02-11
```

使用历史依赖文件运行可控制环境差异，见本地对照报告的完整命令。
`scripts/build_stop_comparison.py` 汇总无止损、延后启用、全历史启用三版，核对逐笔止损、
历史前缀、现金/持仓/净值，导出仅保存在本地的 Excel、HTML 与曲线。

验收覆盖真实 BT 撮合、盘中触线、跳空、买入日禁止触发、最短持有期覆盖、
再入场限制、换仓撤单与 VEC/BT 合成行情一致性。完整真实行情的收益以 BT 账单为准，
不能由少量合成测试推断两引擎在所有旧模块下完全相同。

研究限制仍包括复权价格、非整手数量、历史数据版本，以及止损价的可成交假设。
没有模拟封死跌停、流动性不足或额外冲击；5% 不等于实际净亏损上限。
保留标的的仓位数量仍按旧轮动逻辑处理，未同时重写仓位控制。

## 本地优化第一轮：落实已有择时仓位上限

`backtest.exposure_control.mode: cap_retained` 为新的 BT 研究执行模式。
原配置默认保留 `legacy`，两个模式都可重放，避免把已看过窗口中较好的结果直接当作新正式基线。

新模式在**原调仓开盘**先卖出非目标标的，再检查保留标的是否超过既有择时上限。
超过时按比例减仓，计算卖出费用，使剩余市值不高于扣费后净值乘目标比例。
该风险减仓不受9日最短持有期限制；保留标的相对权重保持不变。
部分减仓先撤销旧数量的保护单，再以原保护价保护剩余隔夜份额，当天仍能触发止损，避免重复卖出。

这是**仓位上限**修复，不是双向目标仓位再平衡：目标回升时不主动补加已有持仓，
仍按原轮动规则买新标的；没有改为等权再平衡，也没有新增择时指标。
`backtest.exposure_control.start_date` 指定首次生效交易日，支持从相同历史持仓做前后对照。

固定池、因子、5日调仓及成本，比较旧执行/仅降仓修复/仅5%成本止损/两者叠加四版。
本地完整计划、结果及账单位于 `runtime_outputs/etf_exposure_research_20260918/`。
该窗口已经看过，属于机制研究，不是新独立样本外认证；没有重新运行因子搜索。

研究入口示例（历史依赖锁定方式同前轮复现；输出需为新的空目录）：

```bash
uv run --no-project --python /home/sensen/dev/projects/-0927/.venv/bin/python \
  --with-requirements runtime_outputs/etf_legacy_reproduction_20260918/requirements-historical.txt \
  python -B frameworks/etf_rotation/scripts/replay_fixed_strategies.py \
  --reference-run runtime_outputs/etf_legacy_extension_20260918 \
  --output runtime_outputs/my_exposure_research \
  --stop-loss 0 --exposure-control cap_retained --exposure-start 2026-02-11
```

`scripts/build_exposure_comparison.py` 校验各版启用前成交、每笔费用和成交价、
信号→决策→执行日期、减仓与止损联动、实际份额及现金，并逐日重建净值。
输出 Excel 中的“仓位执行核对”保留目标比例、计划仓位、实际成交份额按开盘价核对的仓位和盘中止损现金。
不能把这份日线核对表当作分钟级实盘仓位轨迹。

本轮新模式只在 BT 中实现和验收。VEC 收到 `cap_retained` 配置会明确报错，
不会忽略该字段后输出一份看似已启用的结果；原VEC固定成本止损能力保持。

## 现金门研究状态

`backtest.cash_gate.mode: dual_worst`提供每日绝对风险退出：已经移位的轻择时防御状态
与波动门最低档同时出现时，目标仓位为0，下一交易日开盘清仓；恢复后只在正常调仓日重入。
它要求`exposure_control.mode: cap_retained`，VEC会拒绝未实现的现金门配置。

第一轮固定实验发现该联合状态仅在2020年预热期出现3日，首笔交易以后0次，
所以这个具体触发规则已关闭，不作为推荐参数。执行通路和合成测试保留，默认仍为`disabled`；
不能为了躲开已知亏损月份直接改阈值。完整负结果在本地
`runtime_outputs/etf_cash_gate_research_20260918/CASH_GATE_REPORT.md`。
