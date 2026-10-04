# ETF 旧挖掘任务归档

归档日期：2026-10-03。当前入口见 [ETF 自动发现流程](../../../frameworks/etf_rotation/docs/ETF_AUTORESEARCH_PROGRAM.md)。

以下任务绑定旧 Pi/GLM、Sonnet 挖掘线或 2026-09-27 的 v6 campaign，不适用于当前开放流程。归档前已核对最近运行有结束时间，且没有对应挖掘/控制进程。

| 原任务名 | 保存配置 |
|---|---|
| `etf_luna_ic20_once` | [原一次性配置](etf_luna_ic20_once.yaml.archived) |
| `etf_luna_ic20_recover_sol` | [旧故障恢复配置](etf_luna_ic20_recover_sol.yaml.archived) |
| `etf_pi_controller` | [旧 Pi 控制定时任务](etf_pi_controller.yaml.archived) |
| `etf_pi_glm_mining` | [旧 Pi/GLM 候选生成](etf_pi_glm_mining.yaml.archived) |
| `etf_sonnet_controller` | [旧 Sonnet 控制定时任务](etf_sonnet_controller.yaml.archived) |
| `etf_sonnet_mining` | [旧 Sonnet 候选生成](etf_sonnet_mining.yaml.archived) |

源码配置以原字节保存，移出 `deployments/dagu/` 并使用 `.archived` 后缀。本机部署副本分别保存在 `/home/sensen/.config/dagu-gpuml/archive/etf_research_20261003/`，源码与部署副本各自保留，不覆盖两者差异。

Dagu 原运行状态与日志保留在 `/home/sensen/.config/dagu-gpuml/data/dag-runs/<原任务名>/`。本次不重启调度器、不启动挖掘，不修改 `etf_ic_monthly_factory`。恢复历史实验须使用其冻结政策与证据，不能将归档配置直接复制为新批入口。

旧线 STOP 与生成许可状态保留。原源码归档、前向记账、基础数据更新等独立用途不因名称含 Pi 而删除。必要源码和配置已通过仓库 `.gitignore` 的逐文件例外纳入可跟踪范围；数据、运行日志与生成报告继续仅留本地。
