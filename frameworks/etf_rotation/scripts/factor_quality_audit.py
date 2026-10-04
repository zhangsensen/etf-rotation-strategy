#!/usr/bin/env python3
"""
因子质量深度审计脚本 v2

基于真实数据评估当前17个活跃因子的质量：
1. 单因子 Rank IC (5日前瞻)
2. IC稳定性 (IC_IR)
3. 正样本率
4. 分层收益 (Top/Bottom组)
5. 基准收益对比
6. 最终评级

输出: 审计报告到控制台 + results/factor_audit_report.md
"""

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main():
    import yaml
    from etf_strategy.core.data_loader import DataLoader
    from etf_strategy.core.precise_factor_library_v2 import PreciseFactorLibrary

    print("=" * 80)
    print("🔍 因子质量深度审计 v2")
    print("=" * 80)

    # ========== 1. 加载配置和数据 ==========
    config_path = ROOT / "configs" / "combo_wfo_config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    loader = DataLoader(
        data_dir=config["data"].get("data_dir"),
        cache_dir=config["data"].get("cache_dir"),
    )
    data_end = config["data"].get("training_end_date") or config["data"]["end_date"]

    print(f"📊 加载OHLCV: {config['data']['start_date']} → {data_end}")
    ohlcv = loader.load_ohlcv(
        etf_codes=config["data"]["symbols"],
        start_date=config["data"]["start_date"],
        end_date=data_end,
        use_cache=True,
    )
    close = ohlcv["close"]
    print(f"  交易日: {len(close)}, ETF: {len(close.columns)}")

    # ========== 2. 基准收益 ==========
    bench_col = "510300" if "510300" in close.columns else close.columns[0]
    bench = close[bench_col]
    bench_total_ret = (bench.iloc[-1] / bench.iloc[0]) - 1
    print(f"  基准 ({bench_col}): {bench.index[0].date()} → {bench.index[-1].date()}, 收益={bench_total_ret:.2%}")

    # ========== 3. 计算因子 ==========
    print(f"\n🔧 计算全部因子...")
    lib = PreciseFactorLibrary()
    all_factors_df = lib.compute_all_factors(ohlcv)

    # all_factors_df有MultiIndex列: (factor_name, symbol)
    factor_names_available = list(all_factors_df.columns.get_level_values(0).unique())
    print(f"  已计算因子: {len(factor_names_available)}")

    # ========== 4. 前瞻收益 ==========
    fwd_5d = close.pct_change(5).shift(-5)  # 5日前瞻收益

    # ========== 5. 活跃因子列表 ==========
    active_factors = config.get("active_factors", [])
    factors_to_audit = [f for f in active_factors if f in factor_names_available]
    not_found = set(active_factors) - set(factor_names_available)
    if not_found:
        print(f"  ⚠️ 未找到: {sorted(not_found)}")
    print(f"  待审计: {len(factors_to_audit)}")

    # ========== 6. 逐因子审计 ==========
    print(f"\n🔍 逐因子审计 (5日前瞻 Rank IC)...")
    print("-" * 100)

    results = []
    symbols = list(close.columns)

    for fname in factors_to_audit:
        # 提取该因子的DataFrame (T x N)
        factor_df = all_factors_df[fname]  # MultiIndex slice

        # 计算Rank IC
        ic_list = []
        dates = factor_df.index.intersection(fwd_5d.index)
        for dt in dates:
            fv = factor_df.loc[dt].dropna()
            rv = fwd_5d.loc[dt].dropna()
            common = fv.index.intersection(rv.index)
            if len(common) < 5:
                continue
            corr = fv[common].rank().corr(rv[common].rank())
            if np.isfinite(corr):
                ic_list.append(corr)

        if len(ic_list) < 30:
            print(f"  ⚠️ {fname}: IC样本不足 ({len(ic_list)})")
            continue

        ic_arr = np.array(ic_list)
        ic_mean = ic_arr.mean()
        ic_std = ic_arr.std()
        ic_ir = ic_mean / ic_std if ic_std > 0 else 0
        pos_rate = (ic_arr > 0).mean()

        # 分层收益 (3组)
        g_rets = {1: [], 2: [], 3: []}
        for dt in dates:
            fv = factor_df.loc[dt].dropna()
            rv = fwd_5d.loc[dt].dropna()
            common = fv.index.intersection(rv.index)
            if len(common) < 6:
                continue
            ranks = fv[common].rank(pct=True)
            for g, (lo, hi) in enumerate([(0, 1/3), (1/3, 2/3), (2/3, 1.01)], 1):
                mask = (ranks >= lo) & (ranks < hi)
                if mask.sum() > 0:
                    g_rets[g].append(rv[common][mask].mean())

        g1 = np.mean(g_rets[1]) if g_rets[1] else np.nan
        g3 = np.mean(g_rets[3]) if g_rets[3] else np.nan
        spread = (g3 - g1) if np.isfinite(g1) and np.isfinite(g3) else 0

        # 评级
        score = 0
        abs_ic = abs(ic_mean)
        if abs_ic >= 0.05: score += 3
        elif abs_ic >= 0.03: score += 2
        elif abs_ic >= 0.02: score += 1

        abs_ir = abs(ic_ir)
        if abs_ir >= 0.3: score += 3
        elif abs_ir >= 0.2: score += 2
        elif abs_ir >= 0.1: score += 1

        if pos_rate >= 0.55: score += 2
        elif pos_rate >= 0.50: score += 1

        if abs(spread) >= 0.003: score += 2
        elif abs(spread) >= 0.001: score += 1

        if score >= 8: rating = "🟢强"
        elif score >= 5: rating = "🟡中"
        elif score >= 3: rating = "🟠弱"
        else: rating = "🔴无效"

        results.append({
            "因子": fname,
            "IC均值": ic_mean,
            "IC_IR": ic_ir,
            "正样本率": pos_rate,
            "G1(低)": g1,
            "G3(高)": g3,
            "多空价差": spread,
            "评级": rating,
            "评分": score,
            "样本数": len(ic_list),
        })

        print(f"  {fname:<32} IC={ic_mean:+.4f} IR={ic_ir:+.3f} "
              f"正样本={pos_rate:.1%} 多空={spread:+.5f} → {rating}")

    # ========== 7. 汇总 ==========
    print("\n" + "=" * 80)
    print("📋 审计汇总")
    print("=" * 80)

    df = pd.DataFrame(results)
    if df.empty:
        print("❌ 没有成功审计任何因子!")
        return

    df["|IC|"] = df["IC均值"].abs()
    df = df.sort_values("|IC|", ascending=False)

    strong = len(df[df["评级"].str.contains("强")])
    medium = len(df[df["评级"].str.contains("中")])
    weak = len(df[df["评级"].str.contains("弱")])
    invalid = len(df[df["评级"].str.contains("无效")])

    print(f"\n基准收益 ({bench_col}): {bench_total_ret:.2%}")
    print(f"数据: {close.index[0].date()} → {close.index[-1].date()} ({len(close)}天)")
    print(f"\n🟢 强因子: {strong}个")
    print(f"🟡 中等因子: {medium}个")
    print(f"🟠 弱因子: {weak}个")
    print(f"🔴 无效因子: {invalid}个")

    avg_ic = df["|IC|"].mean()
    avg_ir = df["IC_IR"].abs().mean()
    print(f"\n平均|IC|: {avg_ic:.4f} {'⚠️极弱' if avg_ic < 0.03 else '⚠️偏弱' if avg_ic < 0.05 else '✅可用'}")
    print(f"平均|IC_IR|: {avg_ir:.3f} {'⚠️不稳定' if avg_ir < 0.2 else '⚠️边缘' if avg_ir < 0.3 else '✅稳定'}")

    # 保存报告
    report_path = ROOT / "results" / "factor_audit_report.md"
    with open(report_path, "w") as f:
        f.write("# 因子质量深度审计报告\n\n")
        f.write(f"**审计日期**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**数据范围**: {close.index[0].date()} → {close.index[-1].date()} ({len(close)}天)\n")
        f.write(f"**基准 ({bench_col}) 累计收益**: {bench_total_ret:.2%}\n\n")
        f.write(f"## 评级统计\n\n| 评级 | 数量 |\n|------|------|\n")
        f.write(f"| 🟢 强 | {strong} |\n| 🟡 中 | {medium} |\n| 🟠 弱 | {weak} |\n| 🔴 无效 | {invalid} |\n\n")
        f.write(f"**平均|IC|**: {avg_ic:.4f} | **平均|IC_IR|**: {avg_ir:.3f}\n\n")
        f.write("## 因子排名 (按|IC|降序)\n\n")
        f.write("| 因子 | IC均值 | IC_IR | 正样本率 | G1(低) | G3(高) | 多空价差 | 评级 |\n")
        f.write("|------|--------|-------|----------|--------|--------|----------|------|\n")
        for _, row in df.iterrows():
            f.write(f"| {row['因子']} | {row['IC均值']:+.4f} | {row['IC_IR']:+.3f} | "
                    f"{row['正样本率']:.1%} | {row['G1(低)']:.5f} | {row['G3(高)']:.5f} | "
                    f"{row['多空价差']:+.5f} | {row['评级']} |\n")

    print(f"\n📄 报告: {report_path}")


if __name__ == "__main__":
    main()
