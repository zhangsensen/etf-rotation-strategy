# ETF 轮动策略平台

> **生产级** A 股 ETF 轮动系统，三层验证引擎，实盘验证 6 周胜率 83.3%

---

## 实盘成绩

2025-12-18 上线，运行至今。以下为前 6 周（截至 2026-02-09）统计：

| 指标 | 数值 |
|------|------|
| 累计收益 | **+6.37%** (+49,178 CNY) |
| 交易次数 | 22 笔 |
| 胜率 | **83.3%** |
| 盈亏比 | 2.33 |
| 持仓 | 100% A 股，零 QDII |

## 回测表现 (v8.0, BT Ground Truth)

| 策略 | 因子数 | 训练期收益 | 样本外收益 | 最大回撤 | Sharpe | Calmar |
|------|--------|-----------|-----------|---------|--------|--------|
| **composite_1** (生产) | 5F | +51.6% | **+53.9%** | 10.8% | **1.38** | **7.41** |
| **core_4f** (回退) | 4F | +53.0% | **+67.4%** | 14.9% | 1.09 | 4.56 |

- 训练期: 2020-01 ~ 2025-04 (5.3 年)
- 样本外: 2025-05 ~ 2026-02 (9.3 个月)
- VEC-BT 对齐误差: composite_1 **-1.9pp**, core_4f **-0.6pp** (目标 <5pp)

---

## 核心架构

```
WFO (因子筛选)  →  VEC (向量化回测)  →  BT (事件驱动审计)
  ~2 分钟             ~5 分钟              ~30-60 分钟
  IC 门控+评分        Numba JIT 内核       Backtrader 整手约束
  12,597 组合         Top-N 精确模拟       Ground Truth 生产口径
```

**设计哲学**: 不信任任何单层结果。WFO 快速过滤噪声，VEC 用 Numba 精确模拟，BT 用整手+资金约束做最终审计。三层结果不一致时，必须排查到一致才能封版。

### 关键工程能力

**三层验证体系**
- WFO: 从 12,597 个因子组合中筛选候选，IC 门控 + 复合评分 (收益 40% + Sharpe 30% + 回撤 30%)
- VEC: Numba `@njit` 编译的向量化内核，float 份额模拟，带完整迟滞状态机
- BT: Backtrader 事件驱动引擎，整数手约束 + 真实资金限制，production ground truth

**Exp4 迟滞控制**
- 每次调仓最多换 1 只 ETF
- rank01 差值 ≥ 0.10 才触发换仓
- 持仓天数 ≥ 9 天才允许换出
- 效果: 换手率从 35x 降至 ~14.6x

**冻结参数系统**
- `frozen_params.py` 在 WFO/VEC/BT 三层入口强制校验参数一致性
- 防止配置漂移，保证研究到生产的参数完整性
- 支持多版本共存 (v3.4/v4.0/v4.1/v8.0)

**Regime Gate (动态仓位)**
- 基于 510300 波动率百分位的仓位调节
- 经 10 万组合 A/B 测试: 71.5% 组合 Sharpe 提升，86.3% 回撤降低
- 分级暴露: 低波 100% → 中低 70% → 中高 40% → 高波 10%

**ICIR 加权因子方向系统**
- 自动检测因子方向 (sign stability gate)
- 跨窗口 ICIR 加权替代等权求和
- 修复了 5/6 非 OHLCV 因子被系统性反向使用的 bug (v7→v8 核心修复)

**有状态信号生成**
- 每日信号生成器带 schema 校验和环境不匹配冷启动保护
- 持仓组合 + 持仓天数跨日持久化
- 版本/频率/universe 模式自动校验

---

## 快速开始

```bash
# 克隆项目
git clone https://github.com/zhangsensen/etf-rotation-strategy.git
cd etf-rotation-strategy

# 安装依赖 (仅支持 UV)
uv sync --dev

# 运行完整管线 (WFO → VEC → BT)
make pipeline          # ~76 秒

# 单独运行各层
make wfo               # WFO 筛选 (~2min)
make vec               # VEC 回测 (~5min)
make bt                # BT 审计 (~30-60min)

# 每日信号 (需要本地数据)
uv run python scripts/generate_today_signal.py

# 代码质量
make format            # black + isort
make lint              # ruff + mypy
make test              # pytest (210 cases)
```

> **注意**: 回测需要本地 OHLCV 数据 (`raw/ETF/daily/` parquet 文件)。数据通过 QMT 交易终端获取，不随代码分发。

---

## 生产参数 (v8.0 sealed)

| 参数 | 值 | 说明 |
|------|-----|------|
| `FREQ` | 5 | 每 5 个交易日调仓 |
| `POS_SIZE` | 2 | 同时持有 2 只 ETF |
| `COMMISSION` | 0.0002 | 手续费 2bp |
| `LOOKBACK` | 252 | 回看窗口 1 年 |
| `delta_rank` | 0.10 | 迟滞 rank01 差值门槛 |
| `min_hold_days` | 9 | 最小持仓天数 |
| ETF 池 | 49 只 | 41 A 股 + 8 QDII (仅监控) |
| Universe | `A_SHARE_ONLY` | QDII 硬阻断实盘交易 |
| Regime Gate | ON | 波动率模式，510300 代理 |
| 因子池 | 23 | 17 OHLCV + 6 non-OHLCV |

---

## 项目结构

```
.
├── src/etf_strategy/              # 策略核心
│   ├── run_combo_wfo.py           #   WFO 筛选入口
│   ├── core/
│   │   ├── frozen_params.py       #   冻结参数系统 (v3.4~v8.0)
│   │   ├── hysteresis.py          #   Exp4 迟滞内核 (@njit)
│   │   ├── factor_registry.py     #   因子注册表 (44 因子元数据)
│   │   ├── cost_model.py          #   分市场成本模型
│   │   ├── execution_model.py     #   T+1 Open 执行模型
│   │   ├── regime_detector.py     #   Regime Gate
│   │   └── utils/rebalance.py     #   调仓工具 (防前视+统一日程)
│   └── auditor/core/engine.py     #   Backtrader 策略引擎
│
├── scripts/
│   ├── generate_today_signal.py   #   每日信号生成 (有状态)
│   ├── batch_vec_backtest.py      #   VEC 批量回测
│   ├── batch_bt_backtest.py       #   BT 批量审计
│   ├── run_full_pipeline.py       #   完整管线
│   └── update_daily_from_qmt_bridge.py  # 数据更新
│
├── configs/
│   └── combo_wfo_config.yaml      # 单一配置源
│
├── sealed_strategies/             # 封版归档 (v3.1 ~ v8.0)
│   └── v8.0_20260215/            #   当前生产版本
│
├── tests/                         # 210 test cases
├── docs/research/                 # 研究文档
├── memory/                        # 项目知识库 (规则、研究记录)
└── Makefile                       # 快捷命令
```

---

## 研究历程与核心认知

### 执行设计 > 信号质量

这是整个项目最重要的发现:

| 优化维度 | 回报乘数 | 证据 |
|----------|---------|------|
| **执行优化** | **3.6x** | 同一信号，F3_OFF → F5_ON: +11.8% → +42.7% |
| 信号改进 | 1.25x | 不同信号，相同执行框架 |
| 因子重组 | ~1x | 信息空间已饱和 (Kaiser 5/17) |

A 股 ETF 宇宙 PC1 = 59.8%，有效因子维度仅 5/17。**大部分因子冗余，执行框架决定哪些因子能存活。**

### v5 → v8: 一周内 4 个版本的教训

| 版本 | 状态 | 原因 |
|------|------|------|
| v5.0 | 废弃 | ADX Winsorize artifact |
| v6.0 | 从未使用 | 训练期 gate 未通过 |
| v7.0 | 废弃 | VEC-BT gap +25.6pp (三大管线 bug) |
| **v8.0** | **生产** | 三大修复后首个 clean seal, 155 候选全部 gap <2pp |

三大管线修复:
1. **IC-sign 因子方向**: 5/6 非 OHLCV 因子被系统性反向使用
2. **VEC 元数据传递**: factor_signs/factor_icirs 在管线中丢失
3. **BT 执行态迟滞**: 信号态反馈环导致链式偏差 (+25.7pp)

### 研究闭环: 34 条验证规则

在 `memory/rules.md` 中积累了 34 条从实战中提炼的规则，包括:

- **四重验证**: Train → Rolling → Holdout → BT, 缺任何一关结论不可信
- **因子窗口 ≈ 执行频率**: FREQ=5 → 5D 窗口最优 (Rule 27)
- **同源变换 ≠ 新信息**: 二阶导数不是独立 alpha (Rule 28)
- **正交 ≠ 有用**: 完美正交的因子照样没有预测力 (Rule 34)
- **可信负结论 > 可疑正结论**: 在干净管线上确认饱和比"发现"新因子更有价值 (Rule 29)

### 已完成研究

| 研究方向 | 结论 | 详情 |
|----------|------|------|
| 条件因子 | NEGATIVE | 5 个假设全部推翻 |
| 行业约束 | NEGATIVE | MDD 反而恶化 |
| 跨桶约束 | POSITIVE | HO +4.9pp |
| 代数因子 | MARGINAL | OHLCV 重排，信息饱和 |
| 非 OHLCV 优化 | EXHAUSTED | v8.0 在 23 因子空间内已最优 |
| 收益离散度 | NEGATIVE | ⊂ 市场波动率 (rho=0.538) |
| 策略 Ensemble | NEGATIVE | POS_SIZE=1 崩塌 (-75% Sharpe) |
| ETF 折溢价 | NEGATIVE | 正交但无预测力 (Rule 34) |

---

## 技术栈

- **语言**: Python 3.11+
- **包管理**: UV (强制)
- **高性能**: Numba JIT (`@njit` 编译的迟滞内核和向量化回测)
- **回测引擎**: Backtrader (事件驱动，整手约束)
- **数据**: Pandas + PyArrow (parquet 存储)
- **代码质量**: black + isort + ruff + mypy strict
- **测试**: pytest (210 cases)
- **CI**: GitHub Actions (Python 3.11/3.12 矩阵)

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| **v8.0** | 2026-02-15 | 当前生产版本，三大管线修复后首个 clean seal |
| v7.0 | 2026-02-13 | 废弃: IC-sign / metadata / exec-side bugs |
| v6.0 | 2026-02-12 | 从未使用: train gate fail |
| v5.0 | 2026-02-11 | 废弃: ADX Winsorize artifact |
| v3.4 | 2025-12-16 | FREQ=3 基线，实盘启动版 |
| v1.0 | 2025-11-28 | 初版验证通过 |

---

## 免责声明

本项目仅用于量化策略研究和技术展示。历史回测和实盘结果不构成投资建议。策略表现受市场环境影响，过去表现不代表未来收益。

## License

[MIT](LICENSE)
