# pi/GLM ETF 挖掘代码存档（2026-09-19）

2026-10-03 整理：Pi/GLM、Sonnet 的候选生成与控制定时任务共四个已退役，源码与部署副本均见[调度归档](../../../../../deployments/archive/etf_research_20261003/README.md)。`round_drivers/` 的 470 份脚本和 `engine_versions/` 保留原路径及哈希，但移出默认 rg 搜索；可通过显式路径或 `rg --no-ignore` 检索。它们不是当前审核或挖掘入口。

> 旧入口说明（2026-09-22原址归档）：下面的“当前入口”仅指2026-09-21版本。
> 新研究按 [组间优先方法论](../../../ETF_ROTATION_METHODOLOGY.md) 定义；
> 本目录仍为旧14只发现/裁判实现，命令示例不构成重启指令或八组接线验收。

## 当前候选生成入口（2026-09-21）

历史 round driver 中手写 `CANDIDATES` 的方式只保留作审计存档，不再是当前候选生成机制。
当前入口为 `discover_from_outcomes.py discover`：它在发现窗内按可执行 H5 收益定义同日
Top-3 赢家和 Bottom-3 输家，比较因果原子在两组之间的差异，并在 `RET_20`、
`MARKET_BETA_60`、`AMOUNT_Z_20` 横截面控制后检查方向和分年度稳定性。每个家族最多
提炼一个原子，并只在正负方向原子之间生成有限的跨家族 rank-spread。输出
`CANDIDATE_PROPOSAL.json` 后，由同一脚本的 `plan` 子命令交给现有 v4.3 PLAN 封印器；
最终验收仍由 v4.3 完成，发现器不复制裁判。

最小真实发现命令（省略 `--sources` 即跑当前 v3 完整家族目录，45 家族 / 179 原子）：

```bash
uv run --no-sync python \
  frameworks/etf_rotation/scripts/research/pi_glm_mining/discover_from_outcomes.py discover \
  --config frameworks/etf_rotation/configs/outcome_discovery_current14_v1.yaml \
  --output runtime_outputs/etf_outcome_discovery_<run_id>
```

发现器直接读取配置声明的 canonical 数据、人口和截至日；默认绑定仓库内受跟踪的 v4.3
引擎版本，不依赖某条历史运行态 workspace。`--workspace` 仅为重放旧运行态引擎副本保留。

候选公式只读取 D 日原子；未来收益只用于发现期赢家/输家标签，不进入公式、人口、缺失值
填充或时间戳。发现产物是候选，不是认证或策略许可。

这些文件是 `runtime_outputs/etf_pi_glm_mining_20260919/` 里持续挖掘会话实际执行的代码副本。
原始位置在 `.gitignore:168` 忽略的 `runtime_outputs/` 下，无版本控制、worktree 删除即丢失，
故在此建立受跟踪副本。**这里是存档，不是运行副本**；跑批仍由 pi 在 workspace 内进行。

## 目录

- `engine_versions/` — 基座引擎 `pi_round002_mine.py` 的三个版本，文件名后缀是 sha256 前 8 位。
- `round_drivers/` — 每轮薄驱动脚本（含 `pi_round007_census.py`：两原子层普查，不读行情不算 IC）（定义该轮预注册候选），取自 2026-09-19 16:40 的运行态。
- `full_static_leak_scan_20260919.txt` — 覆盖基座 + 全部驱动的完整静态泄漏扫描结果。

## 基座引擎版本与影响范围

| sha256 前缀 | 使用轮次 | 说明 |
|---|---|---|
| `267d144b` | round_002 | 初版。`cross_etf_lead_lag` 家族取不到 benchmark 腿（510300.SH/510500.SH）。 |
| `830bb0e5` | round_003 / 004 / 005 | 修复上述 benchmark bug。 |
| `bea695d0` | round_006 | 重建 `_previously_admitted`：从不可变 PLAN.json 加载并校验 plan 哈希，新增 `_prior_admitted_vectors` 重算前轮入选信号，使去重能对比历史入选因子。 |
| `6d09ebdc` | round_008 起 | 只加溯源：STATUS/REPORT 记录 `prior_admitted_references`（对比过的前轮入选因子及其 plan_sha256）。无计算变更。 |

`round_001` 用的是独立脚本 `pi_round001_mine.py`（`fd0c53ad`），其残差诊断已由后续轮次撤回
（见 `outputs/round_002/correction.json`）。

## 文件哈希（复制时点）

```
267d144b40b6846e69e0255148ef2b827eb9e93b206595269c6fc52ce7421199  engine_versions/pi_round002_mine.267d144b.py
830bb0e57c0fb12b01422798dd9054c2b0b5e891daace55733b74091dda2769e  engine_versions/pi_round002_mine.830bb0e5.py
bea695d0b8edd6421a8e4c3590ead55ea046d78b9e9a6536b3d4ce529fb20d8c  engine_versions/pi_round002_mine.bea695d0.py
fd0c53adf9ba0b6b019010b98b9f6d958e28a3829cb06b616ae04c86298d40ab  round_drivers/pi_round001_mine.py
bea695d0b8edd6421a8e4c3590ead55ea046d78b9e9a6536b3d4ce529fb20d8c  round_drivers/pi_round002_mine.py
b534c9c47b7f46860072866f4f5013a090ee737c4f5832a8d9eadf55bd56f94f  round_drivers/pi_round003_mine.py
6826e4d1496a4196862e4d098186d09665899e9346d7824862da271b17fcc034  round_drivers/pi_round004_mine.py
09230abf2f3e0465b79df55ab2c82169ce1d2d467a6d78470282a38b0e025f2a  round_drivers/pi_round005_mine.py
4cbe285ebc5eb7af14895cfac5d39ddf8bd806d188ac9554f632e618073ea0f6  round_drivers/pi_round006_mine.py
```

`round_drivers/pi_round002_mine.py` 与 `engine_versions/pi_round002_mine.bea695d0.py` 同文件：
round_002 的驱动本身就是基座。

## 已知缺陷：每轮驱动未进快照

`_snapshot` 只快照基座，不快照当轮驱动脚本。各轮的候选定义由 `PLAN.json`（带 `plan_sha256`）
固定，科学内容不丢，但驱动代码本身只有运行态一份——这也是建立本存档的原因之一。

审计结论见 `frameworks/etf_rotation/ETF_PI_MINING_AUDIT_20260919.md`。
6d09ebdcb1bd5555c6b4ed26b28a45f411092db6c7873589281c53b4d5a8ebd9  engine_versions/pi_round002_mine.6d09ebdc.py
d410927db1eaea8d439594a84e103963f3f3ffd6848acec09f4649ec275b3ba5  round_drivers/pi_round007_census.py
3817d299a5462d478812b35b4dfe0c8b26b3564735c453d65d2769f457c99457  round_drivers/pi_round008_mine.py
