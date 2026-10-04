# 历史存档：2026-10-03 清理前版本

本页仅供追溯旧规则与版本沿革，不作为当前执行指令。
[返回现行入口](../../../README.md) · [归档索引](README.md)

原文内部的“当前”“最新”仅描述原撰写时点；下列正文仅调整了相对链接。

---

# ETF Luna / Sol：后台运行与恢复

## 任务和预算

统一入口为 `etf_luna_ic20_once`，仓库配置在 `deployments/dagu/etf_luna_ic20_once.yaml`，部署副本在 `/home/sensen/.config/dagu-gpuml/dags/`。使用 `DAGU_HOME=/home/sensen/.config/dagu-gpuml` 查询本任务。

执行顺序固定：

1. 完成 `luna_v6_campaign20_20260927` 的原 20 轮预算；已完成轮次不重跑。
2. 执行 `luna_v6_dagu20_20260927` 的额外一次 20 轮。
3. 两批完成后结束，不新增第三批，不每日循环。

首次计划触发时间为 2026-09-27 16:52（Asia/Shanghai），已消费的一次性时间不会再次定时执行。修复后由明确的人工安排重新入队同一入口。旧 `etf_luna_ic20_recover_sol` 为历史故障恢复配置，不再作为后续恢复入口。

新批使用 Luna (`gpt-6-luna`) 规划并实现，Sol (`gpt-5.6-sol`) 审阅，开放探索每轮默认最多 4 条；使用当前已批准的输入 profile。20 轮不保证 80 个提案或正 IC。上面的 v6 一次性任务与配额属于历史安排，不能直接续写为 v15 新批。

原 signed Rank IC 方法不变：14 ETF / 8 组，D 收盘信息，D+2 到 D+7 复权开盘标签，冷线 2026-03-24。正负 IC、失败、空轮、重复、是否替换父版本分别记录。

## 恢复规则

- 基线以源码、输入 profile、数据和评价契约的内容哈希标识；旧序号基线只读匹配，不覆盖旧源码。
- 提案、审阅、父基线准备、候选评价、结果落盘、汇总分别记录。父基线准备不会标记候选已开启评价。
- 完整结果带 `evaluation_complete.json` 文件哈希凭据。恢复时先校验；只补汇总和入库，不重新计算 IC。
- 已启动评价但结果不完整：停止，要求排查。不能删除目录或更换 ID 伪装成未运行。
- 冻结源码、数据、评价契约不一致：停止，不自动绕过。
- 已完成批次重复触发前核对逐轮计划、请求和候选终态；只有证据一致才返回完成。
- 跨批次研究锁保证串行；等待最长 24 小时。`WAITING_LOCK` 不表示新批次已开始计算。

规划请求压缩重复历史，完整上下文另存。开放源码审阅只核对已冻结公式和输入合同。
超过 90 万字符的批量审阅拆开；单条请求超限立即暂停，不能记作无提案或空轮。
当前开放模式不按家族分配名额。

模型传输最多初次加两次重试，间隔 30、120 秒，每次最多 180 秒，次数持久化；认证、配置等确定性错误不反复提交。实现修复仍最多一次。候选评价进程强制执行 300 秒预算。

Dagu 最多重新启动任务两次，间隔 60 秒；入口只允许已知安全恢复点续跑，无法判断的中断不会重算。Dagu 重启不清零模型请求预算。这是有界自动恢复，不保证主机故障后任意阶段都可自愈。

## 查看进度

```bash
DAGU_HOME=/home/sensen/.config/dagu-gpuml dagu status etf_luna_ic20_once
```

本地证据：

- 进度：`runtime_outputs/etf_autoresearch_ic/campaigns/<campaign>/summary.json`；关注状态、轮次、`last_progress_at`、各候选 `stage` 及错误。
- 基线关联：同目录 `reference_index.json`。
- 单条结果：`runtime_outputs/etf_autoresearch_ic/<run_id>/result.json` 与 `evaluation_complete.json`。
- 请求及重试：模型调用目录下 `<role>_requests/<request_hash>/`，包括请求、每次调用和成功响应。
- 全库：`runtime_outputs/etf_autoresearch_ic/library/library.json`、`library.csv`。

报告实际完成轮次、实际计算条数、IC/HAC t/n/分年 IC，以及失败、拒绝、空轮和重复数。`keep=false` 不等于没有 IC；使用 `ic_recorded` 与 `parent_replaced` 分开解释。历史批次应使用 `report_etf_autoresearch_campaign.py --campaign <目录> --output <新报告目录>` 核对，不能只看 Dagu 的 succeeded。v15 新批 summary 自带 `progress`，全库也包含 `campaign_progress`。

## 旧状态迁移与证据边界

旧第 14 轮基线冲突只在同时满足以下条件时迁移：已知的基线准备异常、没有候选调用记录或输出目录、冻结源码与已通过审阅一致。`legacy_reference_recovery.json` 保存修复依据，旧 `outcome_opened` 值保留，另记候选实际未启动。已完成 IC 结果不改写。

旧 Astra 记录保留；模型切换写入 `reviewer_changes`，新审阅记录带 `reviewer_model`。数据、账本、结果、日志和迁移证据仅留本地。源码、测试、配置和操作说明可以提交。

主规则：[ETF_AUTORESEARCH_PROGRAM.md](../../ETF_AUTORESEARCH_PROGRAM.md)。
