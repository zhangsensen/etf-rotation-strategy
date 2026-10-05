# 已停用的历史 ETF 挖掘 DAG

2026-10-05 核查收尾：两个定义已从 `~/.config/dagu-gpuml/dags/` 移出，原字节保存在本目录，扩展名为 `.yaml.archived`。GPU ML 仓库跟踪的 T+0 定义已一并撤下。这里是来源归档，不是调度安装目录；不复制回在用 DAG 目录，不启动旧任务。

| 文件 | 原合同与归档 SHA-256 |
|---|---|
| `t0_etf9_sonnet_factor_mining_20r.yaml.archived` | 九只 T+0 ETF 日内挖掘，原为手动任务；`425c716b5e6389d198179a4c230345cf148f1de89399ebdfb6c3cc686b799a1f` |
| `luna_v12_diversity20_20260928.yaml.archived` | 2026-09-28 一次性挖掘，旧入口已失效；`93bd92d27b13089d37517c2d2f12f945e44b76a3a01e9e8e63c59a0d444cd788` |

旧模型、机器路径、人口和评价设置只描述原任务，不替代当前 14 ETF / 8 组 IC 合同。T+0 的历史计算源码、配置和证据按原范围保留；归档不授予继续挖掘、开 holdout、策略验收或订单权限。

本次没有执行任务或重启服务。历史实验与缓存仅在本地 `runtime_outputs/legacy_worktree_cleanup_20261005/` 保存，不随这些源定义上传。
