"""Validate and export frozen-strategy stop/no-stop comparisons locally."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

VARIANTS = {"baseline_verified": "原版无止损", "stop_from_feb11": "2月11日起5%成本止损",
            "stop_full": "全历史5%成本止损"}
STRATEGIES = {"composite_1": "主策略", "core_4f": "备用策略"}


def returns(path, strategy):
    return pd.read_csv(path / f"{strategy}_daily_returns.csv", index_col=0, parse_dates=True).iloc[:, 0]


def orders(path, strategy):
    return pd.read_csv(path / f"{strategy}_orders.csv", dtype={"ticker": str})


def metrics(eq):
    dd = 1 - eq / eq.cummax()
    trough = dd.idxmax()
    peak = eq.loc[:trough].idxmax()
    return {"收益率": float(eq.iloc[-1] / eq.iloc[0] - 1), "最大回撤": float(dd.max()),
            "回撤峰值日": str(peak.date()), "回撤谷值日": str(trough.date())}


def build(root, reference, cutoff="2026-02-10"):
    reference_manifest = json.loads((reference / "input_hashes.json").read_text())
    for filename, digest in reference_manifest.items():
        assert hashlib.sha256(Path(filename).read_bytes()).hexdigest() == digest, filename
    config = __import__("yaml").safe_load((reference / "replay_config.yaml").read_text())
    daily_root = Path(config["data"]["data_dir"])
    names_frame = pd.read_parquet(reference / "fund_names.parquet")
    names = {r.ts_code.split(".")[0]: r["name"] for _, r in names_frame.iterrows()}
    summary, daily, monthly, all_orders, all_trades, all_stops, checks = [], [], [], [], [], [], []
    curves = {}
    hashes = set()
    for variant, variant_label in VARIANTS.items():
        run = root / variant
        manifest = json.loads((run / "run_manifest.json").read_text())
        hashes.add(manifest["candidate_sha256"])
        for strategy, label in STRATEGIES.items():
            r = returns(run, strategy)
            eq = 1e6 * (1 + r).cumprod()
            curves[(variant, strategy)] = eq
            o = orders(run, strategy)
            o["date"] = pd.to_datetime(o["date"])
            stops = json.loads((run / f"{strategy}_stops.json").read_text())
            end = json.loads((run / f"{strategy}_end_state.json").read_text())
            assert end["margin_failures"] == 0
            assert len(stops) == int(o.reason.eq("fixed_stop").sum())

            # Reconstruct the actual execution ledger; a stop must liquidate an
            # existing position, match its entry VWAP and never create a short.
            cash, qty, cost, entry_dates = 1e6, {}, {}, {}
            stop_lookup = {(s["ticker"], s["execution_date"]): s for s in stops}
            for row in o.itertuples():
                t, size, price = row.ticker, row.size, row.price
                old_qty = qty.get(t, 0.)
                if size > 0:
                    cost[t] = cost.get(t, 0.) + size * price
                    entry_dates[t] = row.date
                else:
                    assert old_qty > 0 and -size <= old_qty + 1e-6
                    if row.reason == "fixed_stop":
                        event = stop_lookup[(t, str(row.date.date()))]
                        entry_price = cost[t] / old_qty
                        assert np.isclose(event["entry_price"], entry_price, atol=1e-8)
                        assert np.isclose(event["stop_price"], entry_price * .95, atol=1e-8)
                        assert row.date > pd.Timestamp(event["submitted_date"])
                        assert row.date > entry_dates[t]
                        if manifest["activate_on"]:
                            assert row.date >= pd.Timestamp(manifest["activate_on"])
                        assert event["open"] <= event["stop_price"] or event["low"] <= event["stop_price"]
                        assert np.isclose(price, min(event["open"], event["stop_price"]), atol=1e-8)
                        assert np.isclose(event["size"], size, atol=1e-6)
                        assert not ((o.ticker == t) & (o.date == row.date) & (o["size"] > 0)).any()
                    cost[t] *= max(0., old_qty + size) / old_qty
                qty[t] = old_qty + size
                assert qty[t] >= -1e-6
                cash -= size * price + row.comm
                assert cash >= -.01
            market = sum(v["size"] * v["close"] for v in end["positions"].values())
            assert abs(cash - end["cash"]) < .01
            assert abs(cash + market - end["nav"]) < .01
            assert abs(eq.iloc[-1] - end["nav"]) < .01
            for ticker, quantity in qty.items():
                assert abs(quantity - end["positions"].get(ticker, {}).get("size", 0.)) < 1e-6

            if variant in ("baseline_verified", "stop_from_feb11"):
                old_r = returns(reference, strategy)
                old_o = orders(reference, strategy)
                old_o["date"] = pd.to_datetime(old_o["date"])
                new_o = o
                compared = r
                if variant == "stop_from_feb11":
                    compared, old_r = r.loc[:cutoff], old_r.loc[:cutoff]
                    new_o = o.loc[o.date.le(cutoff)]
                    old_o = old_o.loc[old_o.date.le(cutoff)]
                assert compared.index.equals(old_r.index)
                delta = float((compared - old_r).abs().max())
                assert delta <= (0 if variant == "baseline_verified" else 1e-12)
                pd.testing.assert_frame_equal(new_o[old_o.columns].reset_index(drop=True), old_o.reset_index(drop=True),
                                              check_exact=variant == "baseline_verified", rtol=1e-12, atol=1e-7)
                checks.append({"variant": variant, "strategy": strategy, "daily_prefix_max_error": delta,
                               "matched_order_rows": len(old_o)})

            after = eq.loc[cutoff:]
            row = {"版本": variant_label, "策略": label, "起始本金": 1e6,
                   "期末净资产": float(eq.iloc[-1]), "全期收益率": float(eq.iloc[-1] / 1e6 - 1),
                   "全期最大回撤": metrics(eq)["最大回撤"], "延长段期初净资产": float(after.iloc[0]),
                   "延长段收益率": metrics(after)["收益率"], "延长段最大回撤": metrics(after)["最大回撤"],
                   "延长段回撤峰值日": metrics(after)["回撤峰值日"], "延长段回撤谷值日": metrics(after)["回撤谷值日"],
                   "全期止损次数": len(stops), "延长段止损次数": sum(s["execution_date"] > cutoff for s in stops),
                   "全期成交笔数": len(o), "全期手续费": float(o.comm.sum()),
                   "延长段手续费": float(o.loc[o.date.gt(cutoff), "comm"].sum()),
                   "期末现金": cash, "期末持仓市值": market, "账实差额": cash + market - end["nav"]}
            summary.append(row)
            daily.append(pd.DataFrame({"版本": variant_label, "策略": label, "日期": eq.index,
                                       "净资产": eq.values, "日收益率": r.values,
                                       "历史回撤": (1 - eq / eq.cummax()).values}))
            me = eq.resample("ME").last()
            monthly.append(pd.DataFrame({"版本": variant_label, "策略": label,
                                         "月份": me.index.strftime("%Y-%m"),
                                         "月收益率": (me / me.shift(1).fillna(1e6) - 1).values}))
            o["版本"], o["策略"] = variant_label, label
            o["名称"] = o.ticker.map(names)
            o["现金变动"] = -o["size"] * o.price - o.comm
            o["模拟现金余额"] = 1e6 + o["现金变动"].cumsum()
            all_orders.append(o)
            trades = pd.read_csv(run / f"{strategy}_closed_trades.csv", dtype={"ticker": str})
            trades["版本"], trades["策略"] = variant_label, label
            trades["名称"] = trades.ticker.map(names)
            all_trades.append(trades)
            for event in stops:
                event.update({"版本": variant_label, "策略": label, "名称": names.get(event["ticker"], "")})
                all_stops.append(event)

    assert len(hashes) == 1
    summary = pd.DataFrame(summary)
    stops_frame = pd.DataFrame(all_stops)
    notes = [
        "研究模拟账单；没有实盘下单。输入池49只、目标2只、FREQ=5、普通换仓最少持有9天、排名差0.1。",
        "固定成本止损：成交均价乘0.95；买入后的下一交易日起每日有效，独立于旧的移动止损调仓日开关。",
        "止损绕过最短持有期；跳空低开按开盘价，否则盘中触线按保护价；手续费另扣。",
        "止损当日不生成该标的新买入目标，下一个调仓决策日可重新评估；不强制当天填满仓位。",
        "原普通换仓逻辑不调整保留标的的数量；本次只增加价格止损，未改写整体仓位控制。",
        "普通轮动时序：D因子数据，D+1形成目标，D+2开盘交易；止损线在触发日以前已确定。",
        "延长段窗口：2026-02-10收盘至2026-09-18收盘。止损延后启用版与原版在2月10日前持仓和成交一致。",
        "全历史止损版从最早成交开始启用，会改变2月10日的持仓和本金；不能当作相同起点的修复对照。",
        "成本：境内ETF单边20bp，QDII单边50bp；基准为未扣费的被动买入持有。",
        "止损执行日线模型假设保护价可成交；没有模拟封死跌停、流动性不足或额外冲击。5%并非净亏损上限。",
        "沿用旧复权研究价格与非整手数量；不是实际报单价格，分红/拆分现金流没有独立逐笔建模。",
        "原49只池、因子权重和数据未重选；历史留出段已参与筛选，新增规则也在已看过的行情上比较，不是新独立样本外认证。",
        "512720融资只到2026-07-10，159985缺融资；其余份额/融资大多到9月17日；历史发布版本不完整。",
        "所有生成产物仅保存在本地。",
    ]
    benchmark = []
    for path in sorted(daily_root.glob("*_daily_*.parquet")):
        f = pd.read_parquet(path)
        f.index = pd.to_datetime(f.trade_date.astype(str), format="%Y%m%d")
        c = f.adj_close.loc[cutoff:]
        benchmark.append((path.name.split("_")[0], float(c.iloc[-1] / c.iloc[0] - 1)))
    benchmarks = pd.DataFrame([{"基准": "沪深300ETF买入持有", "收益率": next(v for n, v in benchmark if n.startswith("510300"))},
                               {"基准": "原49只等权买入持有", "收益率": np.mean([v for _, v in benchmark])}])
    tables = {"策略对照": summary, "止损成交": stops_frame, "全部成交": pd.concat(all_orders),
              "已平仓交易": pd.concat(all_trades), "每日净值": pd.concat(daily),
              "月度收益": pd.concat(monthly), "同期基准": benchmarks,
              "核对结果": pd.DataFrame(checks), "口径说明": pd.DataFrame({"说明": notes})}
    with pd.ExcelWriter(root / "ETF止损对照账单.xlsx", engine="openpyxl") as writer:
        for sheet, table in tables.items():
            table.to_excel(writer, sheet_name=sheet, index=False)
            ws = writer.sheets[sheet]
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = min(45, max(15, len(str(col[0].value)) * 2 + 2))
    (root / "comparison_summary.json").write_text(summary.to_json(orient="records", indent=2, force_ascii=False))
    (root / "validation.json").write_text(json.dumps({"verdict": "PASS", "checks": checks,
        "validated_stop_fills": len(all_stops), "candidate_hashes_identical": True,
        "all_runs_cash_positions_reconciled": True, "original_inputs_hash_verified": len(reference_manifest),
        "certification": "NEEDS_REWRITE: research prices, liquidity assumptions and historical data vintages remain"}, indent=2))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 2, figsize=(13, 8), constrained_layout=True)
    for column, strategy in enumerate(STRATEGIES):
        for variant, label, color in [("baseline_verified", "No stop", "#64748b"),
                                      ("stop_from_feb11", "5% stop from Feb 11", "#2563eb"),
                                      ("stop_full", "5% stop from first entry", "#d97706")]:
            eq = curves[(variant, strategy)].loc[cutoff:]
            axes[0, column].plot(eq.index, eq / eq.iloc[0], label=label, color=color)
            axes[1, column].plot(eq.index, 100 * (eq / eq.cummax() - 1), label=label, color=color)
        axes[0, column].set_title(strategy + " | 2026-02-10 to 2026-09-18")
        axes[1, column].set_ylabel("Interval drawdown (%)")
        for ax in axes[:, column]:
            ax.grid(alpha=.2)
            ax.legend(fontsize=8)
    fig.savefig(root / "stop_comparison.png", dpi=150)
    plt.close(fig)
    display = summary[["版本", "策略", "延长段收益率", "延长段最大回撤", "延长段止损次数"]].copy()
    for col in ["延长段收益率", "延长段最大回撤"]:
        display[col] = display[col].map(lambda x: f"{x:.2%}")
    chart = base64.b64encode((root / "stop_comparison.png").read_bytes()).decode()
    html = ('<!doctype html><html lang="zh"><meta charset="utf-8"><title>ETF止损对照</title>'
            '<style>body{max-width:1200px;margin:32px auto;font-family:system-ui;padding:16px;color:#182235}'
            'table{border-collapse:collapse;width:100%;margin:20px 0}td,th{padding:9px;border:1px solid #dce1e8}'
            'img{width:100%}li{margin:10px 0}</style><h1>ETF 5% 成本止损对照</h1>'
            '<p>相同2月10日期初持仓：主策略未触发止损，备用策略触发7次；备用策略回撤下降，收益转负。</p>'
            + display.to_html(index=False, escape=True)
            + f'<img alt="净值及回撤对照" src="data:image/png;base64,{chart}">'
            + '<h2>2月11日起启用版本的止损成交</h2>'
            + stops_frame.loc[stops_frame["版本"].eq(VARIANTS["stop_from_feb11"])].to_html(index=False, escape=True)
            + '<h2>口径</h2><ul>' + ''.join(f'<li>{n}</li>' for n in notes) + '</ul></html>')
    (root / "ETF止损对照账单.html").write_text(html)
    report = "\n".join([
        "# ETF 固定成本止损执行对照", "",
        "执行层审查：KEEP / Sailor；只修复冻结5%成本止损，不调整标的池、因子、权重、频率或普通换仓阈值。",
        "执行时序审查：PASS / Strategy（新增止损）；实盘认证：NEEDS_REWRITE。",
        "信号：D数据→D+1目标→D+2开盘；止损价最晚前一交易日确定，下一交易日起盘中触发。",
        "收益：现金加持仓收盘市值；境内单边20bp、QDII单边50bp；没有用未来低价生成此前开盘交易。",
        "输入：" + str(reference), "输出：" + str(root), "",
        "比较窗口为2026-02-10收盘至2026-09-18收盘。原版与2月11日起启用版的起点持仓相同。",
        display.to_markdown(index=False), "",
        "## 全历史结果", "",
        summary[["版本", "策略", "全期收益率", "全期最大回撤", "全期止损次数"]].to_markdown(index=False), "",
        "## 验证与解释", "",
        f"核对 {len(all_stops)} 笔止损成交；输入文件 SHA256 {len(reference_manifest)} 项全部一致。",
        "关闭止损的两套策略每日收益与封存引擎延长结果逐日完全一致。延后启用版此前成交一致，日收益误差仅浮点舍入（<1e-12）。",
        "各版逐笔重建现金、份额和期末净值，差额均小于0.01元；无负现金、无卖空、无保证金失败。",
        "备用策略的7次止损中1次黄金ETF跳空，其余按保护线成交。成本止损改变了之后的持仓路径，不能简单从旧收益扣掉7笔损失。",
        "成本止损也不会保护所有浮盈：曾大涨的持仓只要未跌破买入成本线，仍可能回吐较大收益。",
        "本次结果不支持‘直接加5%成本止损就改善这套轮动策略’；这是已看过数据上的固定规则对照，不是新的独立样本外认证。",
        "", "## 同期基准（未扣费）", "", benchmarks.to_markdown(index=False), "",
        "## 口径", "", *["- " + n for n in notes], "",
        "## 复跑", "",
        "从当前仓库根目录运行；每次使用新的空输出目录。三个版本分别运行：", "",
        "```bash",
        "uv run --no-project --python /home/sensen/dev/projects/etf-rotation-strategy/.venv/bin/python --with-requirements runtime_outputs/etf_legacy_reproduction_20260918/requirements-historical.txt python -B frameworks/etf_rotation/scripts/replay_fixed_strategies.py --reference-run runtime_outputs/etf_legacy_extension_20260918 --output runtime_outputs/NEW_COMPARISON/baseline_verified --stop-loss 0",
        "uv run --no-project --python /home/sensen/dev/projects/etf-rotation-strategy/.venv/bin/python --with-requirements runtime_outputs/etf_legacy_reproduction_20260918/requirements-historical.txt python -B frameworks/etf_rotation/scripts/replay_fixed_strategies.py --reference-run runtime_outputs/etf_legacy_extension_20260918 --output runtime_outputs/NEW_COMPARISON/stop_from_feb11 --stop-loss .05 --activate-on 2026-02-11",
        "uv run --no-project --python /home/sensen/dev/projects/etf-rotation-strategy/.venv/bin/python --with-requirements runtime_outputs/etf_legacy_reproduction_20260918/requirements-historical.txt python -B frameworks/etf_rotation/scripts/replay_fixed_strategies.py --reference-run runtime_outputs/etf_legacy_extension_20260918 --output runtime_outputs/NEW_COMPARISON/stop_full --stop-loss .05",
        "uv run --project frameworks/etf_rotation --no-sync python frameworks/etf_rotation/scripts/build_stop_comparison.py --root runtime_outputs/NEW_COMPARISON --reference-run runtime_outputs/etf_legacy_extension_20260918",
        "```", "",
        "详细输入、源码快照、依赖与原始命令见各版本 run_manifest.json；核对结果见 validation.json。",
    ])
    (root / "STOP_COMPARISON_REPORT.md").write_text(report)
    print(display.to_string(index=False))
    print(f"Validated {len(all_stops)} protective fills; workbook and HTML: {root}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--reference-run", type=Path, required=True)
    a = p.parse_args()
    build(a.root.resolve(), a.reference_run.resolve())
