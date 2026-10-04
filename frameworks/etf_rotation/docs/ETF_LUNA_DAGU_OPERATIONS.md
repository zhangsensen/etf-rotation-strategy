# ETF 挖掘运行与恢复

现行入口为 [v15 自动发现流程](ETF_AUTORESEARCH_PROGRAM.md)。新批采用 `--mode open`、Luna `gpt-6-luna`、审阅 `gpt-6.1-sol`；批次预算沿用用户已授权范围。

2026-09-27 的 `etf_luna_ic20_once`、`etf_luna_ic20_recover_sol` 是旧 v6 一次性任务，已从源配置目录及本机 Dagu 活跃任务目录移出。归档见[配置说明](../../../deployments/archive/etf_research_20261003/README.md)。旧运行日志原位保留，旧任务名不再作为当前启动入口。

2026-10-04 用户授权一次性 50 轮任务：[etf_luna_open50_once.yaml](../../../deployments/dagu/etf_luna_open50_once.yaml)。北京时间 2026-10-04 02:00 启动 `luna_v15_dagu50_20261004`，每轮最多4条，不凑数。前序 `luna_v15_open5_20261003_continuation` 只核对完成证据，不再启动或恢复。入口必须显式传 `--rounds`；同 ID 已完成则 DONE，不增加预算；安全中断仅以相同合同恢复，已开标签无封印、修订阶段未完成及模型重试耗尽均暂停。

部署目录仅为 `/home/sensen/.config/dagu-gpuml/dags/`。任务有研究互斥锁、Dagu 单实例限制和最多两次任务重试；每个模型请求的已用次数持久保存，不因 Dagu 重试清零。真实数据预检可用 `schedule_etf_luna_campaign.py --after ... --campaign-id ... --rounds 50 --check-only` 检查启动状态，不调用模型或评价。逐轮进度与完整 IC 存在下表所列位置，完成须核对50轮证据。

## 查看真实进度

不能只看 Dagu succeeded 或原 `summary.json` 的 COMPLETED。当前 workflow 从逐轮计划、请求与候选终态核对完成证据；新 summary 含 `progress`，自动库 `library.json` 含 `campaign_progress`。

历史批次只读生成新报告：

```bash
.venv/bin/python frameworks/etf_rotation/scripts/research/report_etf_autoresearch_campaign.py \
  --campaign runtime_outputs/etf_autoresearch_ic/campaigns/CAMPAIGN_ID \
  --output runtime_outputs/etf_autoresearch_ic/REPORT_NEW
```

输出目录必须不存在。报告列完整轮数、产出候选轮数、计算轮数、候选条数、请求错误，以及逐条 IC/HAC t/n/窗口。缺少历史字段留空；未执行不冒充空轮或已完成。

| 证据 | 本地路径（相对仓库根） |
|---|---|
| 原始批次状态、计划和源码 | `runtime_outputs/etf_autoresearch_ic/campaigns/<campaign>/` |
| 完整单条结果及封印 | `runtime_outputs/etf_autoresearch_ic/<run_id>/result.json`、`evaluation_complete.json` |
| 请求与持久重试 | 调用目录的 `<role>_requests/<request_hash>/` |
| 累计候选与派生进度 | `runtime_outputs/etf_autoresearch_ic/library/library.json`、`library.csv` |
| 更新模型后的工程验收与真实回放 | `runtime_outputs/etf_autoresearch_ic/code_cleanup_20261003/REPORT.md`；此前修复报告按原日期解释 |
| 全历史资料及验收先后关系 | [研究资料基准](RESEARCH_BASELINE.md) |

## 恢复边界

- 提案、审阅、候选预检、正式评价、落盘和汇总分阶段记录；参考基线准备不表示候选标签已开。
- 完整结果须通过文件封印校验，并与标签前预检的源码、输入合同、完整分数哈希一致。恢复只补汇总和入库，不重算已完成 IC。
- 已开标签但结果不完整、版本/输入不一致或中断阶段无法确认时暂停。不能删除目录、换 ID 或改原结果伪装成未运行。
- 批次串行使用研究锁；调度等待最长 24 小时，`WAITING_LOCK` 不表示开始计算。前序完成须经证据核对。
- 同政策且处于安全恢复点，按原参数加 `--resume`；旧政策批次不自动迁移。历史迁移依据和旧字段另存，不回写原失败结论。

模型传输最多初次加两次重试，间隔 30、120 秒；Luna 提案/实现每次最多180秒，Sol 公式/源码审核每次最多300秒。尝试记录超时预算、实际耗时及超时诊断，次数持久保存，进程重启不清零。认证、配置等确定性错误不反复提交。请求超过 900000 字符时批量审阅可拆分；单条仍超限则保存长度与哈希并暂停。实现缺陷最多一次标签前修正。

规划和公式审核在历史上下文增长时使用带列名的行数组，减少重复 JSON 字段；精确本地公式、冻结方向、所需面板及正式定义索引保留，原始历史不变。50轮启动前以现有445条本地定义加200条模拟定义做容量检查；模拟数据只测请求长度，不参与挖掘或 IC 库。

候选计算及正式评价各有 300 秒预算，整个分数预检有 900 秒预算。候选自身计算错误隔离记录；公共输入、合同、封印及整体预检故障暂停批次。无限重试、故障空轮和无依据完成状态均不属于恢复。

月度前向调度 `etf_ic_monthly_factory` 与本页自动发现分别维护。历史运行日志、请求、源码和 IC 结果仍在原位置，本次调度不改写它们。
