# ETF 引擎与池子工程交接

> 历史实现交接（2026-09-22标记）：正文记录旧14只裁判的能力与口径。
> 当前方法见 [组间优先方法论](ETF_ROTATION_METHODOLOGY.md)，其八组裁判及账本不因本文而视为已实现。

本轮职责是维护框架、引擎和池子契约；真实因子挖掘由挖掘负责人运行。
输入为显式指定的本地 canonical 行情、唯一维护池配置及冻结家族配置；
输出为可独立检查的池子合同、成熟标签上的 IC 诊断和因子层 WFO 表。
工程验收使用临时目录合成行情和临时账本，不以出现晋级因子为通过条件。

## 固定研究问题与范围

- 当前维护池20只，家族裁判仅排名14只 `candidate`，不是旧49只池或全20只排名。
- 45家族、179原子、11经济轴沿用 breadth v3；本轮没有扩表达式、调阈值或更换标的。
- 信号在 D 收盘可用；标签从 D+2 开盘到 D+2+H 开盘，H=5/10/20。
  IC 使用毛收益标签，不含成交成本，不能直接解释成可交易净收益。
- 发现段截至2023-12-31，已见审计段2024-01-01至2025-04-30。
  每个期限都要求退出日期在对应段内成熟；跨期限方向使用共同有限 IC 日期。
- 所有新增实现位于 ETF 目录，不导入个股的语法、因子目录、裁判或账本。
  唯一维护池仍在根目录 `config/etf_rotation_universe_v1.json`，未复制或修改。

## 修复后的含义

1. 数据加载先截到 `min(as_of, seen_audit_end)`；区间外标签不能进入统计。
   截止后才出现的维护标的保留全空列，不伪造历史；默认加载器仍保留严格失败行为。
2. LOSO 同时导出全排除共同日期和逐标的配对日期两张表，分别记录发现/审计样本损失、
   完整池基线、剔除值和差分，以及该标的实际贡献日数。身份门使用共同日期表。
3. 空录取库的增量检验为 `NOT_APPLICABLE`、通过值为空，不再冒充增量通过；
   同时不阻止首个因子录取。非空库才执行实际增量门。
4. 残差化先在共同标的上重排名，报告秩、条件数、自由度及不可估计原因。
   RET_20、REALIZED_VOL_20、AMOUNT_Z_20 是事后设定的经济对照，仅作报告，不影响正式门。
5. 池子报告区分维护数、排名数、每日资格宽度和实际标签对数；
   首个观测日不等于上市日，当前池回看历史不等于历史 PIT 成员池。
6. 账本仅新增前向溯源表；历史计数和预算不清零、不退款。
   `CORRECTED_RERUN` 必须引用已存在的代次，不能冒充免计数的确定性复现。
7. 因子层 WFO 使用冻结输入中的全部表达式，各折仅用训练 IC 定方向，
   训练/测试分别清理跨段标签。CLI 要求至少360个有效训练日；不足明确报告。
   固定8个季度折不保证每个原子有8个可用折，已见历史不成为独立样本外。
8. 日收益偏度改为逐窗口计算，避免部分 pandas 版本的全序列数值中心化使未来异常值扰动历史。

## 独立入口

以下从仓库根运行。优先使用已安装研究依赖的 `.venv/bin/python`；
环境准备与 `uv` 替代命令见 README。数据和输出均留本地。

仅检查池子，不计算因子/收益，不写账本：

```bash
.venv/bin/python frameworks/etf_rotation/scripts/inspect_pool_contract.py \
  --canonical-data-root /absolute/path/to/local/canonical/data \
  --universe-config config/etf_rotation_universe_v1.json \
  --adjudication-config frameworks/etf_rotation/configs/family_adjudication_engine_v4.yaml \
  --as-of 2025-04-30 --output runtime_outputs/new_pool_contract.json
```

实际有效截止日须为数据完整的交易日。输出文件必须不存在。
池子可观测覆盖和用于 IC 的成熟标签样本是不同口径，分别展示。

挖掘负责人后续修正重跑使用 `scripts/run_family_adjudication.py`，参数同上，
另提供新的 `--output` 目录和已有 `--ledger` 路径。
`family_adjudication_engine_v4.yaml` 的 `replay_of` 要求账本已记录
`etf_family_breadth_v3_first_adjudication`，不应为跑通而新建空账本或删除历史。
`engine_v4` 是本次输出合同版本，不是对旧工程代次的重新编号。
本工程交付没有执行这次真实重跑，也没有更新真实账本。

WFO 读取裁判导出的三个输入，不访问行情、个股引擎或研究账本：

```bash
.venv/bin/python frameworks/etf_rotation/scripts/evaluate_factor_wfo.py \
  --daily-ic runtime_outputs/YOUR_RUN/wfo_daily_ic.parquet \
  --label-dates runtime_outputs/YOUR_RUN/label_dates.parquet \
  --eligibility-counts runtime_outputs/YOUR_RUN/wfo_eligibility_counts.csv \
  --fold-config frameworks/etf_rotation/configs/factor_wfo_engine_v1.yaml \
  --output runtime_outputs/NEW_WFO_RUN
```

| 输出 | 消费约定 |
| --- | --- |
| `wfo_daily_ic.parquet` | horizon、signal_date、expression_key、ic；保留冻结列与缺失记录 |
| `label_dates.parquet` | horizon、signal_date、entry_date、exit_date |
| `wfo_eligibility_counts.csv` | signal_date、eligible_count；不冒充实际标签对数 |
| `identity_shared_dates.csv` / `identity_paired_dates.csv` | 两种日期匹配口径不能混用 |
| `marginal_ic.csv` | 空库 N/A；nullable pass 不能强转为真 |
| `economic_baseline_ic.csv` | 事后经济对照，不是新增认证门 |
| `residual_design_diagnostics.csv` | 残差设计可估计性 |
| `population_width_ic.csv` | 各宽度、区间、期限的 IC 与实际对数 |

旧代次的原产物保持不动。零描述性候选和零晋级也导出完整表结构。
WFO 只报告历史稳定性，不给独立 OOS、统计晋级或上线许可。

## 验证与后续责任

```bash
.venv/bin/python -m pytest -c frameworks/etf_rotation/pytest.ini frameworks/etf_rotation/tests -q
bash scripts/guard_no_data_in_git.sh
```

合成端到端覆盖：实际读取器、成熟标签、正式裁判、零候选及录取分支、
临时账本、WFO 导出读取、未来行扰动不变、未来才出现的观察标的和独立池子检查。
需要旧行情的跳过测试不算真实回测验收。静态扫描中的前向日期移位仅用于标签，
不进入特征；日期/入场滞后提示须结合上述时序合同解读。

剩余边界：真实数据修正重跑及结果差分由挖掘负责人完成；
历史 PIT 成员、可靠上市/清盘元数据、NAV/份额/持仓/跟踪指数数据仍需独立补齐。
它们不能靠增加表达式或工程测试证明已解决。日更下载与调度沿用其他负责人的工作，
本轮不修改共享下载器、个股引擎和 Dagu 挖掘调度。
