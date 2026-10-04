# ETF 挖掘引擎 v4 修复验收单（主控只验收，不改引擎；2026-09-21 19:10）

前提：Codex 在 room `etf-pi-glm-mining-20260919` 回 `READY_FOR_ACCEPTANCE + commit sha`；两线 STOP 保留；验收在源码入口 `round_drivers/pi_round002_mine.py` 与两线工作区副本三份上跑，三份 sha 必须一致。

| # | 验收项 | 方法 | 通过标准 |
|---|---|---|---|
| A1 | ETF 全测 | `uv run --no-sync pytest frameworks/etf_rotation -q` | 0 failure |
| A2 | PLAN 封印 | 复制一轮到临时 workspace；改 PLAN.json 一个字段；跑 evaluate | 拒绝，退出码非 0，错误信息含 seal |
| A3 | 并发查重 | 两进程同时 plan 同一表达式（同哈希）到两线 | 只一个 PLAN 落地，另一方被预算锁内查重拒绝 |
| A4 | 泄漏缓存隔离 | 对 round_213 NS67A 跑泄漏门，记录 4 分支（截断、扰动、intraday、副目录）的原子重建数与 max|diff| | 每分支 computed >0 且 cached = 0（证明真实重建、未读正式 cache）；截断/扰动分支 max|diff| = 0（证明无未来依赖）。Codex 第二轮指出原文写反，已更正 |
| A5 | NS67A 全链 | 真实数据→原子→表达式→泄漏门→v4 裁判（含退出日 purge、标签缺失不进入选票集合）→两腿增量→去重 | 全链跑通；报告发现/审计 bp、block-t、HAC-t、campaign、leg、dedup 结果；与 §16 数字的差异逐项解释（purge 与选票集合修正后应变化） |
| A6 | 选票集合无未来可得性 | 构造一个 D 日高分票未来 exit 缺失的用例 | 该票仍进入 top-3 权重，收益按缺失处理（不递补第 4 名） |
| A7 | 退出日 purge | 检查发现/审计/干净面切片 | 最后一个信号日的 exit 日 ≤ 窗口末端 |
| A8 | 发现窗统一 | 去重秩向量与发现统计同用 `[DISCOVERY_START, DISCOVERY_END]` | 向量首日 ≥ 2021-08-09 |
| A9 | 运行合同 | 修改任一输入（数据文件、家族源码、配置）后 evaluate | 拒绝 |
| A10 | STATUS 字段 | 任一新 STATUS | `certified_factor=false, promotion_allowed=false, external_validity=false` 存在 |
| A11 | STOP 下禁 plan | STOP 存在时调用 plan | 拒绝 |
| A12 | 历史工具隔离 | grep `method="first"` 与固定块长 5 的 H10/H20 | 只在标注"不进 v4 证据链"的历史脚本中出现 |

验收后动作：A1–A12 全过 → 用修复后引擎重跑三次干净面检验（F1–F4、六代表 2026 段、CA1）并替换 §14/§16 数字；任一不过 → 退回 Codex，不重跑。

## 验收结果（v4.2，`85f080f8`，2026-09-21 20:40）
A1 378/0 ✅ · A2 ✅ · A3 ✅ · A4 ✅（四分支 computed 2 / cached 0，max|diff| 0） · A5 ⚠ REPLAY_ONLY（NS67A 在 v4.2 裁判下重算：LEAD_ONLY，不过跨线 Bonferroni 与两腿增量；USER 20:55 决定不跑正式 plan→evaluate 全链 batch，STOP 保留，正式工件待线重开） · A6 ✅ · A7 ✅ · A8 ✅ · A9 ✅（三种篡改均拒） · A10 ✅ · A11 ✅ · A12 ✅（历史工具门控 + 冻结快照）。
Codex 第一轮审核 7 项已全部修入 v4.2；第二轮审核待回。干净面三次检验（F1–F4、六代表、CA1）尚未按 v4.2 重跑——它们的面已被用过一次，重跑只能作"同面复算"标注，不算新证据。
Codex 第二轮：无新 P0；3 项 P1 中版本号、家族预绑定、controller 字段/封印/版本检查已修（`8e849a80`）；正式全链工件一项按 USER 决定不补。
