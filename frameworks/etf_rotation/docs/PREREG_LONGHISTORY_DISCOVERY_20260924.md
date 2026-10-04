# 预注册：长历史发现 → 2025 窗判定（ETF 轮动线，2026-09-24）

USER 2026-09-24 批准：2015–2024 指数代理长历史只用于立题、定方向、去重（只选，不判门）；判门只在真实 ETF 2025-01-01..2026-03-24（冷线）窗口。本文件在任何代理面 IC 计算前写定，结果出来后不改。

## 1. 面板
- 发现面：`runtime_outputs/etf_rotation_research/long_history_proxies/`，8 组代理日收盘（映射见 `etf_group_regime_longhistory.py::build`；cn_tech = 5 个中证指数等权，hk_tech = HKTECH（港元），us_growth = 513100.SH，pharma = 931152/931250 等权，gold = 518880.SH，metals = 000819.SH，dividend = H30269，electric = H30199）。只有收盘价 → 只收可由日收盘定义的因子（无量、无 OHLC、无份额/分钟/NAV）。
- 发现窗：信号日 2015-01-05..2024-12-31；标签 close(D+1)→close(D+6)（对应真实线 open(D+2)→open(D+7) 的收盘近似），标签退出跨 2024-12-31 的日子 purge。
- 判定面：真实 14 只 ETF / 8 组，`discover_etf_groups.py`，标签 open(D+2)→open(D+7)，as_of = 2026-03-24（COLD_OK），PRIOR_DIRECTION_FULL_WINDOW，min_days 250（见 IC_MINING_RULES §2 覆盖门行）。

## 2. 候选目录（计算前冻结）
- 目录 = (a) 已登记定义中只依赖日收盘的机制；(b) 文献收盘价因子：动量 5/20/60/120/250、12-1 跳月动量、反转 5/20、波动 20/60、对 EW8 的贝塔与特质波动、残差动量、MAX5、偏度 60、下行贝塔、与 EW8 相关性变化。
- 目录写成 `runtime_outputs/etf_rotation_research/longhistory_discovery_20260924/CATALOG.csv`（name, formula, window, source=a/b, created_after_viewing_2025=是/否），sha256 记入审批后才计算。
- 同一公式在两套面板上用同一实现（代码只换输入面板）。

## 3. 发现规则（只选，不判门）
1. 每条候选在发现窗算逐日 8 组 Spearman IC，HAC t（lag 10）。
2. 方向 = 发现窗 IC 均值符号，冻结。
3. 入选：|HAC t| ≥ 3.0。不要求逐年同号（USER：因子不需穿越牛熊）；逐年 IC 只列报。
4. 去重：入选者之间逐日秩相关均值 ≥0.7 → 保留 |t| 大者。
5. 上限 K ≤ 10（按 |t| 取前 10）。入选名单与方向写入 `SELECTED.json` 并记 sha256 后，才允许读判定面标签。

## 4. 判定（只看 IC，CLAUDE.md「因子挖掘只看 IC」）
- 判定面对入选的 K 条走现有门：IC ≥0.01、HAC t 与块 t ≥2、各合格年为正、剔一组 IC >0、n ≥250。
- 标注（不作门）：Bonferroni α/K、与库内 HAS_IC 的去重、`created_after_viewing_2025=是` 的条目单独标"判定窗对该定义非未见"。
- 失败项全部登记计入累计账本。
- 结论措辞：过门 = 历史线索（判定窗未参与选择）；认证只来自前向。

## 5. 不做
- 不看收益/超额/top-K；不在发现窗做组合；不因判定结果回改方向、阈值、K 或目录。

## 6. 结果（阶段 2，2026-09-24）
57 条 0 条过 |HAC t|≥3.0；最大 |t| 2.37（residual_semideviation_asymmetry）。SELECTED.json 为空（sha256 3e99b5b4…），阶段 3 不执行。按 §5 不回改。

## 7. 附加预注册：H20 发现（2026-09-24，阶段 2 结果出来后、任何 H20 标签读取前写定）
- 理由：实际持仓按月调；跨资产组的宏观/资金类驱动在月度期限作用，H5 标签以噪声为主。
- 目录：§2 冻结目录（sha256 6d08591f…）+ 库内 16 条 HAS_IC 中只依赖日收盘、可在 8 列组面板上计算的条目（预计 market_residual_abs_cluster_20、market_coskewness_20；由 miner 核实并在计算前列入 CATALOG_H20.csv 记 sha256）。
- 标签：close(D+1)→close(D+21)；发现窗信号日 2015-01-05..2024-12-31，退出跨 2024-12-31 purge；HAC lag 30。
- 入选：方向 = 发现窗 IC 符号；|HAC t| ≥ 3.0；去重 0.7；K ≤ 10。写 SELECTED_H20.json 记 sha256。
- 判定：真实 ETF 2025-01-01..冷线只有约 14 个不重叠 H20 区间，不作门；入选条目只进前向（登记方向与公式，按月前向累计 IC）。多期限（H5、H20）共两次检验，标注不作门。
- 另列（只作画像，不作门，不影响任何入选）：库内 HAS_IC 可移植条目在代理面 2015–2024 的 H5 IC。

## 8. 结果（H20，2026-09-24）
60 条（§2 冻结 57 条 + beta_asymmetry_60、market_residual_abs_cluster_20、market_coskewness_20）0 条过 |HAC t|≥3.0（HAC lag 30）；最大 |t| 2.86（beta_horizon_ratio）。SELECTED_H20.json 为空（sha256 62ae0d66…），前向无登记条目。
H5 画像（不作门）：market_residual_abs_cluster_20 代理面 IC 0.016 / t 1.12（2025+ 真实面 0.133 / t 4.43）；beta_asymmetry_60 −0.003 / −0.19；market_coskewness_20 −0.011 / −0.72。
结论：8 组截面上，日收盘可定义的因子在 H5 与 H20 两个期限、2015–2024 十年代理面上无一达到 |t|≥3。本线（长历史发现）关闭；ETF 线因子只剩月度 IC 工厂与现有候选的前向。
