# ETF 一次性研究工具：原址归档

整理日期：2026-10-03。以下工具绑定历史批次、来源检查或库存合并路径，不作为新候选统一入口。保留原位置和源码哈希，避免破坏历史 imports、测试与复算。

当前发现见 [run_etf_autoresearch_campaign.py](run_etf_autoresearch_campaign.py)，当前库查询见[说明](../../docs/IC_INVENTORY.md)。普通 rg 搜索排除下面的历史文件，显式指定路径或 `rg --no-ignore` 仍可查询。

- [audit_ext_cnh_r07_independent.py](audit_ext_cnh_r07_independent.py)
- [audit_ext_coal_r10_independent.py](audit_ext_coal_r10_independent.py)
- [audit_ext_copper_r05_independent.py](audit_ext_copper_r05_independent.py)
- [audit_ext_crude_r06_independent.py](audit_ext_crude_r06_independent.py)
- [audit_ext_gold_r04_independent.py](audit_ext_gold_r04_independent.py)
- [audit_ext_hktech_r08_independent.py](audit_ext_hktech_r08_independent.py)
- [audit_ext_realrate_r09_independent.py](audit_ext_realrate_r09_independent.py)
- [audit_sox_r01_independent.py](audit_sox_r01_independent.py)
- [audit_us_style_r03_independent.py](audit_us_style_r03_independent.py)
- [audit_vix_r02_independent.py](audit_vix_r02_independent.py)
- [discover_longhistory_catalog_20260924.py](discover_longhistory_catalog_20260924.py)
- [discover_longhistory_catalog_h20_20260924.py](discover_longhistory_catalog_h20_20260924.py)
- [discover_longhistory_ic_20260924.py](discover_longhistory_ic_20260924.py)
- [discover_longhistory_ic_h20_20260924.py](discover_longhistory_ic_h20_20260924.py)
- [merge_domestic_benchmark_inventory_20260925.py](merge_domestic_benchmark_inventory_20260925.py)
- [merge_ext_cnh_r07_inventory.py](merge_ext_cnh_r07_inventory.py)
- [merge_ext_coal_r10_inventory.py](merge_ext_coal_r10_inventory.py)
- [merge_ext_copper_r05_inventory.py](merge_ext_copper_r05_inventory.py)
- [merge_ext_crude_r06_inventory.py](merge_ext_crude_r06_inventory.py)
- [merge_ext_gold_r04_inventory.py](merge_ext_gold_r04_inventory.py)
- [merge_ext_hktech_r08_inventory.py](merge_ext_hktech_r08_inventory.py)
- [merge_ext_realrate_r09_inventory.py](merge_ext_realrate_r09_inventory.py)
- [merge_sox_r01_inventory.py](merge_sox_r01_inventory.py)
- [merge_us_style_r03_inventory.py](merge_us_style_r03_inventory.py)
- [merge_vix_r02_inventory.py](merge_vix_r02_inventory.py)
- [preflight_cash_activity_r01.py](preflight_cash_activity_r01.py)
- [preflight_domestic_benchmark_20260925.py](preflight_domestic_benchmark_20260925.py)
- [preflight_ext_cnh_r07.py](preflight_ext_cnh_r07.py)
- [preflight_ext_coal_r10.py](preflight_ext_coal_r10.py)
- [preflight_ext_copper_r05.py](preflight_ext_copper_r05.py)
- [preflight_ext_crude_r06.py](preflight_ext_crude_r06.py)
- [preflight_ext_gold_r04.py](preflight_ext_gold_r04.py)
- [preflight_ext_hktech_r08.py](preflight_ext_hktech_r08.py)
- [preflight_ext_realrate_r09.py](preflight_ext_realrate_r09.py)
- [preflight_sox_specific_r01.py](preflight_sox_specific_r01.py)
- [preflight_us_index_source.py](preflight_us_index_source.py)
- [preflight_us_style_r03.py](preflight_us_style_r03.py)
- [preflight_vix_risk_r02.py](preflight_vix_risk_r02.py)
- [run_group_next8_20260922.py](run_group_next8_20260922.py)

通用历史读取/复算工具继续保留在检索面：`rejudge_group_ic_scores_v5.py`、`rejudge_etf_groups_2025.py`、`rejudge_group_campaign_2025.py`、`audit_saved_etf_ic_history.py`、`build_ic_inventory.py`。它们按保存证据工作，不能按“旧”字或版本号删除。

[Pi/GLM 旧代码目录](pi_glm_mining/README.md)的 470 个 round driver 已是源代码档案，本次移出普通搜索；原址保留供哈希与引擎路径引用。旧 Pi/GLM 与 Sonnet 定时生成/控制任务均退役，调度配置见[部署归档](../../../../deployments/archive/etf_research_20261003/README.md)。
