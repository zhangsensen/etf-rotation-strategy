# 历史运行说明：任务已退役

2026-10-03：本文对应的旧 Pi/GLM 候选生成及控制定时任务已移出活跃目录，[配置归档](../archive/etf_research_20261003/README.md)保留原配置。下文用于解释历史日志，不作为重启指令；现行 ETF 入口见[自动发现流程](../../frameworks/etf_rotation/docs/ETF_AUTORESEARCH_PROGRAM.md)。

---

# ETF pi 持续挖掘

DAG `etf_pi_glm_mining` 在 coral 工作区运行 ETF 发现层实验。pi 固定为
`zai/glm-5.3-flash`；同一个 RPC 进程、同一个会话连续接收多个批次，
从 `get_session_stats.contextUsage.percent` 读取实际上下文占用，达到 65%
时压缩并保留研究合同、历史尝试、结果路径及下一批队列，不按累计消耗 token 判断。

Dagu 每 5 分钟提供启动恢复机会。文件锁防双跑；正常运行没有整项超时。
每批 60 分钟内必须结束一次模型运行；连续两轮没有完整计算产物则报告
`INSTRUMENT_BLOCKED`。重启从 checkpoint 的会话和当前批次恢复，跳过已经
生成有效 `STATUS.json` 和 `candidate_metrics.csv` 的批次。旧 print 模式批次
在迁移期间自然完成后，原会话才切换到 RPC。

若冻结输入面确实没有未测的新机制，worker 写入本轮
`MECHANISM_EXHAUSTED.json`。控制器将它转成运行根的同名等待标记并正常退出；
Dagu 预条件阻止五分钟重复空转。新增家族或数据面经过复核并接入新研究 epoch
后，才应移除该标记继续运行。

当前本地运行根：`runtime_outputs/etf_pi_glm_mining_20260919/`。
该目录包含既有隔离源码工作区、PROMPT.md、CONTINUATION.md、migration.json、
pi 会话及结果；它不是可上传的数据包，也不会由此 DAG 自动复制到其他机器。
迁移到新运行根需要显式准备这些本地输入。

- `supervisor_status.json`：当前进程、批次、会话、上下文占用及错误原因。
- `supervisor_heartbeat.json`：长计算期间每 30 秒更新的独立存活信号。
- `context_usage.jsonl`：逐批实际上下文与累计用量，二者分列。
- `completed_rounds.jsonl`：去重批次索引；worker 结果仍待主控复核。
- `workspace/outputs/round_*/`：预登记、全候选指标、时序检查与报告。

Dagu 状态：

```bash
DAGU_HOME=/home/sensen/.config/dagu-gpuml dagu status etf_pi_glm_mining
```

禁止上传行情、模型、生成结果或会话。不得触碰 QMT、交易、其他工作区；
新候选仍是 `discovery_candidate_not_certified`，自动接续不授予因子认证。
写入运行根的 `STOP` 文件会阻止新调度并要求控制器停止；重新启动前需移除它。
