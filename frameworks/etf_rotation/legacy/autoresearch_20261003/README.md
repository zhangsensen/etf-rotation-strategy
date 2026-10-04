# ETF 自动发现旧代码与测试

2026-10-03 归档，供代码追溯和版本比较。当前入口见 [ETF README](../../README.md)。本目录保存清理前原字节，不随当前修复或模型设置更新；其中旧指令不作为运行入口。

当前挖掘/实现使用 `gpt-6-luna`，审核使用 `gpt-6.1-sol`。新 Python 工作流与 CLI 均只接受 `open`。

| 存档 | 移出当前路径的内容 |
|---|---|
| [旧 campaign](source/run_etf_autoresearch_campaign.py) | 单候选最高 IC 爬山、全局候选文件替换、连续失败停轮 |
| [旧 workflow](source/etf_autoresearch_workflow.py) | mixed/explore/refine 配额、父基线调度、家族冷却/重开与改进筛选 |
| [旧规划](source/etf_autoresearch_diversity.py) | 按来源/问题轮换、语义家族准入和旧提示词 |
| [旧计划审阅](source/etf_autoresearch_plan_review.py) | 因旧家族或同家族兄弟候选而拒绝的规则 |
| `tests/*_historical.py` | 六份清理前测试文件，保存旧规则断言与迁移来源 |

源码四份、测试六份均为清理前完整快照，便于核对删除内容。历史测试不用 `test_*.py` 文件名，默认 pytest 不收集；生产代码不导入本目录。它们依赖当时配套实现，不应将单个旧模块塞进当前 Python 路径运行。历史实验按各自保存的源码、配置、输入标识与环境复算。

仍有价值的测试迁移到了当前 `tests/`：审阅在标签前完成、原方向正负 IC 留存、同家族开放提案、实现修正、模型故障暂停、恢复不重算、精确重复与源数据/分数封印。读旧账本的兼容性测试仍保留，因为历史记录需要继续查询。

未移动原 PLAN、运行源码快照、IC、分数、失败记录或历史日志；评价器、输入适配、排名与 IC 数值代码未因清理改变。本地映射、哈希与验收见仓库根 `runtime_outputs/etf_autoresearch_ic/code_cleanup_20261003/`，这些生成工件不提交。
