"""Audit a fixed four-way local ETF execution experiment, then export its ledger."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from build_stop_comparison import metrics, orders, returns

VARIANTS = {"legacy_no_stop": "原执行", "cap_no_stop_verified": "仅修复降仓",
            "legacy_stop": "仅5%成本止损", "cap_stop": "降仓加5%成本止损"}
STRATEGIES = {"composite_1": "主策略", "core_4f": "备用策略"}


def build(root, reference, cutoff="2026-02-10"):
    hashes = json.loads((reference / "input_hashes.json").read_text())
    for filename, digest in hashes.items():
        assert hashlib.sha256(Path(filename).read_bytes()).hexdigest() == digest, filename
    config = yaml.safe_load((reference / "replay_config.yaml").read_text())
    qdii = set(config["universe"]["qdii_tickers"])
    prices = {}
    for path in Path(config["data"]["data_dir"]).glob("*_daily_*.parquet"):
        frame = pd.read_parquet(path)
        frame.index = pd.to_datetime(frame.trade_date.astype(str), format="%Y%m%d")
        prices[path.name.split(".")[0]] = frame[["adj_open", "adj_low", "adj_close"]].to_dict("index")
    nf = pd.read_parquet(reference / "fund_names.parquet")
    names = {row.ts_code.split(".")[0]: row["name"] for _, row in nf.iterrows()}
    summaries, daily_rows, event_rows, order_frames, trade_frames, monthly_frames, checks = [], [], [], [], [], [], []
    curves = {}
    for variant, variant_label in VARIANTS.items():
        run = root / variant
        for strategy, label in STRATEGIES.items():
            r = returns(run, strategy)
            equity = 1e6 * (1 + r).cumprod()
            curves[(variant, strategy)] = equity
            o = orders(run, strategy)
            o["date"] = pd.to_datetime(o.date)
            old_r = returns(reference, strategy)
            old_o = orders(reference, strategy)
            old_o["date"] = pd.to_datetime(old_o.date)
            prefix_error = float((r.loc[:cutoff] - old_r.loc[:cutoff]).abs().max())
            assert prefix_error < 1e-12
            pd.testing.assert_frame_equal(o.loc[o.date.le(cutoff), old_o.columns].reset_index(drop=True),
                                          old_o.loc[old_o.date.le(cutoff)].reset_index(drop=True),
                                          check_exact=False, rtol=1e-12, atol=1e-7)
            if variant == "legacy_no_stop":
                pd.testing.assert_series_equal(r, old_r, check_exact=True)
            end = json.loads((run / f"{strategy}_end_state.json").read_text())
            assert end["margin_failures"] == 0
            events = {pd.Timestamp(x["date"]): x for x in json.loads((run / f"{strategy}_exposure.json").read_text())}
            targets = {pd.Timestamp(x["decision_date"]): x for x in json.loads((run / f"{strategy}_targets.json").read_text())}
            stops = {(x["ticker"], pd.Timestamp(x["execution_date"])): x
                     for x in json.loads((run / f"{strategy}_stops.json").read_text())}
            grouped = {d: f for d, f in o.groupby("date", sort=False)}
            cash, quantities, cost_basis = 1e6, {}, {}
            max_nav_error = 0.
            local_daily, local_events = [], []
            for i, date in enumerate(r.index):
                trades_today = grouped.get(date)
                stop_proceeds = 0.
                stopped_quantity = {}
                if trades_today is not None:
                    for row in trades_today.itertuples():
                        t, size, price = row.ticker, row.size, row.price
                        old_qty = quantities.get(t, 0.)
                        fee_rate = .005 if t in qdii else .002
                        assert abs(row.comm - abs(size) * price * fee_rate) < 1e-6
                        market = prices[t][date]
                        if row.reason == "fixed_stop":
                            event = stops[(t, date)]
                            assert size < 0 and old_qty > 0
                            entry_price = cost_basis[t] / old_qty
                            assert np.isclose(event["stop_price"], .95 * entry_price, rtol=1e-9, atol=1e-8)
                            assert pd.Timestamp(event["submitted_date"]) < date
                            assert market["adj_low"] <= event["stop_price"] or market["adj_open"] <= event["stop_price"]
                            assert np.isclose(price, min(market["adj_open"], event["stop_price"]), rtol=1e-9)
                            stop_proceeds -= size * price + row.comm
                            stopped_quantity[t] = stopped_quantity.get(t, 0.) + size
                        else:
                            assert np.isclose(price, market["adj_open"], rtol=1e-9), (t, date, price)
                        if row.reason == "exposure_reduce":
                            assert variant.startswith("cap_") and date > pd.Timestamp(cutoff)
                            assert size < 0
                        if size > 0:
                            cost_basis[t] = cost_basis.get(t, 0.) + size * price
                        else:
                            assert -size <= old_qty + 1e-6
                            cost_basis[t] *= max(0., old_qty + size) / old_qty
                        quantities[t] = old_qty + size
                        assert quantities[t] >= -1e-6
                        cash -= size * price + row.comm
                        assert cash >= -.01
                market_value = sum(q * prices[t][date]["adj_close"] for t, q in quantities.items() if abs(q) > 1e-8)
                nav = cash + market_value
                max_nav_error = max(max_nav_error, abs(nav - equity.loc[date]))
                assert abs(nav - equity.loc[date]) < .01
                row = {"版本": variant_label, "策略": label, "日期": date, "净资产": nav,
                       "现金": cash, "持仓市值": market_value, "收盘仓位": market_value / nav,
                       "日收益率": r.loc[date]}
                local_daily.append(row)
                if date in events:
                    event = events[date]
                    # Targets must have been fixed the previous session. Normal
                    # rotation uses data from one further session before that.
                    decision_date = r.index[i - 1]
                    assert decision_date in targets
                    assert pd.Timestamp(targets[decision_date]["signal_date"]) < decision_date < date
                    assert event["target"] == targets[decision_date]["timing"]
                    expected = event["planned_positions"]
                    for ticker in quantities.keys() | expected.keys():
                        assert abs(quantities.get(ticker, 0.) - expected.get(ticker, 0.)
                                   - stopped_quantity.get(ticker, 0.)) < 1e-6
                    assert abs(cash - event["planned_cash"] - stop_proceeds) < .01
                    assert event["planned_cash"] >= -.01
                    open_market = sum(q * prices[t][date]["adj_open"] for t, q in quantities.items() if q > 1e-8)
                    actual_exposure = open_market / (cash + open_market)
                    excess = max(0., actual_exposure - event["target"])
                    if event["control_active"]:
                        assert event["planned_exposure"] <= event["target"] + 1e-9
                        assert excess < 1e-9
                    erow = {"版本": variant_label, "策略": label, "成交日": date,
                            "因子日期": targets[decision_date]["signal_date"], "决策日": decision_date,
                            "上限生效": event["control_active"], "目标仓位上限": event["target"],
                            "计划仓位": event["planned_exposure"], "成交份额按开盘价核对仓位": actual_exposure,
                            "超限比例": excess, "主动减仓金额": event["reduction_value"],
                            "调仓后计划现金": event["planned_cash"], "实际现金": cash,
                            "盘中止损回笼现金": stop_proceeds}
                    local_events.append(erow)
            assert abs(cash - end["cash"]) < .01
            assert max_nav_error < .01
            checks.append({"版本": variant_label, "策略": label, "启用前日收益最大误差": prefix_error,
                           "逐日净值最大勾稽差额": max_nav_error, "调仓核对次数": len(local_events),
                           "止损核对次数": len(stops), "订单失败": end["margin_failures"]})
            daily_rows.extend(local_daily)
            event_rows.extend(local_events)
            ld = pd.DataFrame(local_daily)
            le = pd.DataFrame(local_events)
            after = equity.loc[cutoff:]
            recent_orders = o.loc[o.date.gt(cutoff)]
            recent_events = le.loc[le["成交日"].gt(cutoff)]
            summaries.append({"版本": variant_label, "策略": label,
                "延长段收益率": metrics(after)["收益率"], "延长段最大回撤": metrics(after)["最大回撤"],
                "延长段期初净资产": float(after.iloc[0]), "期末净资产": float(equity.iloc[-1]),
                "延长段平均仓位": float(ld.loc[ld["日期"].gt(cutoff), "收盘仓位"].mean()),
                "延长段成交笔数": len(recent_orders), "延长段手续费": float(recent_orders.comm.sum()),
                "延长段双边换手倍数": float((recent_orders["size"].abs() * recent_orders.price).sum() / after.mean()),
                "延长段止损次数": int(recent_orders.reason.eq("fixed_stop").sum()),
                "主动减仓次数": int(recent_orders.reason.eq("exposure_reduce").sum()),
                "调仓后超限次数": int(recent_events["超限比例"].gt(1e-9).sum()),
                "最大超限比例": float(recent_events["超限比例"].max()),
                "全期收益率": float(equity.iloc[-1] / 1e6 - 1), "全期最大回撤": metrics(equity)["最大回撤"]})
            o["版本"], o["策略"], o["名称"] = variant_label, label, o.ticker.map(names)
            order_frames.append(o)
            closed = pd.read_csv(run / f"{strategy}_closed_trades.csv", dtype={"ticker": str})
            closed["版本"], closed["策略"] = variant_label, label
            trade_frames.append(closed)
            month_end = equity.resample("ME").last()
            monthly_frames.append(pd.DataFrame({"版本": variant_label, "策略": label,
                "月份": month_end.index.strftime("%Y-%m"),
                "月收益率": (month_end / month_end.shift(1).fillna(1e6) - 1).values}))
    summary = pd.DataFrame(summaries)
    checks = pd.DataFrame(checks)
    notes = [
        "本地研究回测；原49只池、两套冻结策略、目标2只、5日调仓、普通换仓最短持有9日；未做参数搜索。",
        "主要比较窗2026-02-10收盘至2026-09-18收盘，各版启用前持仓、资金与成交一致；修改从2月11日起生效。",
        "修复仅针对上限：在原调仓开盘对保留标的按比例减仓，扣除手续费后不超过原择时目标；非每日强制再平衡。",
        "目标回升时不主动补加已有持仓，仍按旧轮动规则买新标的。因此这是降仓上限修复，尚不是完整双向目标仓位管理。",
        "减仓与5%成本止损均可绕过普通最短持有期；部分减仓后剩余隔夜份额当天继续受原保护线约束。",
        "仓位核对使用实际成交份额和开盘研究价格，并单列盘中止损回笼现金；不是分钟级实盘仓位轨迹。",
        "D因子数据→D+1目标→D+2开盘成交；成本止损的保护线在触发日以前确定。",
        "境内ETF单边20bp、QDII单边50bp；换手为窗口双边成交额除以平均净资产，未年化。",
        "复权研究价格、非整手数量，未模拟跌停无法成交、流动性冲击或分红拆分的独立现金流。",
        "份额和融资数据版本限制沿用前轮；512720融资只到2026-07-10，159985无融资；并非完整历史发布版本认证。",
        "样本已经看过，旧留出段也参与过选择；本轮是机制比较，不是新独立样本外认证。",
        "所有行情、账单和报告仅保存在本地；没有实盘订单或远端上传。",
    ]
    passive = []
    for ticker, by_date in prices.items():
        start = by_date[pd.Timestamp(cutoff)]["adj_close"]
        end_price = by_date[max(by_date)]["adj_close"]
        passive.append((ticker, end_price / start - 1))
    benchmark = pd.DataFrame([{"基准": "沪深300ETF买入持有（未扣费）", "收益率": dict(passive)["510300"]},
                              {"基准": "原49只等权买入持有（未扣费）", "收益率": np.mean([v for _, v in passive])}])
    all_orders = pd.concat(order_frames)
    tables = {"策略对照": summary, "仓位执行核对": pd.DataFrame(event_rows),
              "每日净值仓位": pd.DataFrame(daily_rows), "全部成交": all_orders,
              "减仓与止损": all_orders.loc[all_orders.reason.ne("rotation")],
              "已平仓交易": pd.concat(trade_frames), "月度收益": pd.concat(monthly_frames),
              "验证结果": checks, "同期基准": benchmark, "口径说明": pd.DataFrame({"说明": notes})}
    with pd.ExcelWriter(root / "ETF本地优化第一轮.xlsx", engine="openpyxl") as writer:
        for name, table in tables.items():
            table.to_excel(writer, sheet_name=name, index=False)
            ws = writer.sheets[name]
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = min(44, max(16, len(str(col[0].value)) * 2))
    (root / "comparison_summary.json").write_text(summary.to_json(orient="records", force_ascii=False, indent=2))
    (root / "validation.json").write_text(json.dumps({"execution_verdict": "PASS", "verified_input_files": len(hashes),
        "verified_rebalance_events": len(event_rows), "verified_daily_nav_rows": len(daily_rows),
        "checks": json.loads(checks.to_json(orient="records")),
        "certification_verdict": "NEEDS_REWRITE: seen window, research prices and data vintages"}, ensure_ascii=False, indent=2))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5), constrained_layout=True)
    english = ["Legacy", "Exposure cap only", "5% stop only", "Exposure cap + stop"]
    for ax, strategy in zip(axes, STRATEGIES):
        for variant, line_label in zip(VARIANTS, english):
            eq = curves[(variant, strategy)].loc[cutoff:]
            ax.plot(eq.index, eq / eq.iloc[0], label=line_label)
        ax.set_title(strategy + " | Feb 10 - Sep 18, 2026")
        ax.grid(alpha=.2)
        ax.legend(fontsize=8)
    fig.savefig(root / "exposure_comparison.png", dpi=150)
    plt.close(fig)
    display = summary[["版本", "策略", "延长段收益率", "延长段最大回撤", "延长段平均仓位", "调仓后超限次数"]].copy()
    for c in ["延长段收益率", "延长段最大回撤", "延长段平均仓位"]:
        display[c] = display[c].map(lambda x: f"{x:.2%}")
    chart = base64.b64encode((root / "exposure_comparison.png").read_bytes()).decode()
    html = ('<!doctype html><html lang="zh"><meta charset="utf-8"><title>ETF本地优化第一轮</title>'
        '<style>body{max-width:1200px;margin:32px auto;padding:16px;font-family:system-ui;color:#172334}'
        'table{border-collapse:collapse;width:100%}td,th{padding:10px;border:1px solid #ddd}li{margin:10px 0}img{width:100%}</style>'
        '<h1>ETF 本地优化：先落实原有择时仓位上限</h1>'
        '<p>固定四版比较：原执行、仅修复降仓、仅成本止损、两者同时使用。相同2月10日期初持仓。</p>'
        + display.to_html(index=False, escape=True) + f'<img src="data:image/png;base64,{chart}" alt="四版净值对照">'
        + '<h2>执行核对</h2>' + checks.to_html(index=False, escape=True)
        + '<h2>口径</h2><ul>' + ''.join(f'<li>{n}</li>' for n in notes) + '</ul></html>')
    (root / "ETF本地优化第一轮.html").write_text(html)
    (root / "RESEARCH_REPORT.md").write_text("\n".join([
        "# ETF 本地执行优化第一轮", "", "Verdict: KEEP / Layer: Sailor（仓位上限执行修复）",
        "时间合同与实际执行：PASS / Strategy；策略独立认证：NEEDS_REWRITE。",
        "噪声风险：中；此次只验证原择时上限如何执行，没有改池、选因子或搜索新阈值。", "",
        "## 结果", "", display.to_markdown(index=False), "",
        "仓位上限修复使调仓后的超限消失。备用策略在本窗口显著降低回撤，同时保留正收益；主策略收益与回撤均小幅下降。",
        "5%成本止损在本窗口的负收益问题没有被仓位修复解决；不把两个规则叠加当作默认更优。",
        "保留当前修复作为本地研究候选，不能将这次已看过样本的对照包装为独立确认。", "",
        "## 成本、仓位与换手", "", summary.to_markdown(index=False), "",
        "## 验证", "", checks.to_markdown(index=False), "",
        f"核对{len(hashes)}份输入哈希、{len(event_rows)}次调仓和{len(daily_rows)}条逐日净值；现金与持仓逐日勾稽。",
        "因子日期<决策日<成交日，减仓使用此前已确定的目标；原版收益精确复现，各版启用前成交一致。",
        "减仓后原止损保护剩余隔夜份额，取消旧数量保护单以避免重复卖出。", "",
        "## 基准（未扣费）", "", benchmark.to_markdown(index=False), "",
        "## 口径与下一步边界", "", *["- " + n for n in notes], "",
        "后续若要验证目标回升时补仓，应单独定义规则，并处理新买份额的T+1限制；不与本轮降仓修复混作一个收益结论。",
        "本轮固定计划见 PLAN.md；每版源码快照、配置、依赖和复跑命令见 run_manifest.json。",
        "报告生成命令：", "```bash",
        "UV_PROJECT_ENVIRONMENT=/home/sensen/dev/projects/gpu_ml/.venv uv run --no-sync python frameworks/etf_rotation/scripts/build_exposure_comparison.py --root runtime_outputs/etf_exposure_research_20260918 --reference-run runtime_outputs/etf_legacy_extension_20260918",
        "```", "", "原始数据与冻结候选来自：" + str(reference),
    ]))
    print(display.to_string(index=False))
    print(f"Validated {len(event_rows)} rebalance events and {len(daily_rows)} daily NAV rows")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--reference-run", type=Path, required=True)
    a = p.parse_args()
    build(a.root.resolve(), a.reference_run.resolve())
