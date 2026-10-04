"""Export a local simulated ETF statement from instrumented legacy BT outputs."""
from __future__ import annotations
import argparse
import base64
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd


def period_stats(equity, start, end):
    equity = equity.loc[start:end]
    if len(equity) < 2:
        return {'return': 0., 'max_drawdown': 0.}
    return {'return': float(equity.iloc[-1] / equity.iloc[0] - 1),
            'max_drawdown': float((1 - equity / equity.cummax()).max())}


def build(run, daily_root, names_path=None, cutoff='2026-02-10'):
    names = {}
    if names_path and names_path.exists():
        names = {r.ts_code.split('.')[0]: r['name'] for _, r in pd.read_parquet(names_path).iterrows()}
    summary, orders_all, trades_all, daily_all, month_all, holdings_all, curves = [], [], [], [], [], [], {}
    for name, label in [('composite_1', '主策略'), ('core_4f', '回退策略')]:
        raw = pd.read_csv(run / f'{name}_daily_returns.csv', index_col=0, parse_dates=True).iloc[:, 0]
        eq = 1_000_000 * (1 + raw).cumprod()
        curves[label] = eq
        orders = pd.read_csv(run / f'{name}_orders.csv', dtype={'ticker': str})
        orders['日期'] = pd.to_datetime(orders['date'])
        orders['策略'] = label
        orders['名称'] = orders.ticker.map(names).fillna('')
        orders['成交金额'] = orders['size'].abs() * orders.price
        orders['资金变动'] = -orders['size'] * orders.price - orders.comm
        orders['模拟现金余额'] = 1_000_000 + orders['资金变动'].cumsum()
        orders_all.append(orders)
        trades = pd.read_csv(run / f'{name}_closed_trades.csv', dtype={'ticker': str})
        trades['策略'] = label
        trades['名称'] = trades.ticker.map(names).fillna('')
        trades_all.append(trades)
        daily_all.append(pd.DataFrame({'策略': label, '日期': eq.index, '净资产': eq.values,
                                       '净值': eq.values / 1_000_000, '当日收益率': raw.values,
                                       '历史回撤': (eq / eq.cummax() - 1).values}))
        me = eq.resample('ME').last()
        mr = me / me.shift(1).fillna(1_000_000) - 1
        month_all.append(pd.DataFrame({'策略': label, '月份': mr.index.strftime('%Y-%m'), '月收益率': mr.values,
                                      '月末净资产': me.values}))
        recent = period_stats(eq, cutoff, str(eq.index[-1].date()))
        qty = orders.groupby('ticker')['size'].sum()
        market_value = 0.
        for ticker, count in qty[qty.abs() > 1e-6].items():
            files = list(daily_root.glob(f'{ticker}*_daily_*.parquet'))
            if len(files) != 1:
                raise ValueError(f'Expected one daily file for {ticker}')
            d = pd.read_parquet(files[0]);d['date'] = pd.to_datetime(d.trade_date.astype(str), format='%Y%m%d')
            last = d[d.date.le(eq.index[-1])].sort_values('date').iloc[-1]
            price = float(last.adj_close); value = count * price; market_value += value
            holdings_all.append({'策略': label, '代码': ticker, '名称': names.get(ticker, ''), '模拟份额': count,
                                 '复权研究价格': price, '模拟市值': value, '组合权重': value / eq.iloc[-1]})
        cash = float(orders['模拟现金余额'].iloc[-1])
        residual = float(cash + market_value - eq.iloc[-1])
        if not np.isclose(residual, 0., atol=0.01):
            raise ValueError(f'Cash/holdings reconciliation failed: {name}: {residual}')
        summary.append({'策略': label, '起始本金': 1_000_000, '截止日': str(eq.index[-1].date()),
                        '期末净资产': float(eq.iloc[-1]), '全期净利润': float(eq.iloc[-1] - 1_000_000),
                        '全期收益率': float(eq.iloc[-1] / 1_000_000 - 1),
                        '全期最大回撤': float((1 - eq / eq.cummax()).max()),
                        '延长段起点': cutoff, '延长段期初净资产': float(eq.loc[cutoff]),
                        '延长段收益率': recent['return'], '延长段最大回撤': recent['max_drawdown'],
                        '成交笔数': len(orders), '累计费用': float(orders.comm.sum()),
                        '延长段成交笔数': int(orders['日期'].gt(cutoff).sum()),
                        '已平仓笔数': len(trades), '涉及标的数': orders.ticker.nunique(),
                        '期末现金': cash, '期末持仓市值': market_value, '账实勾稽差额': residual})
    tables = {'策略汇总': pd.DataFrame(summary), '月度收益': pd.concat(month_all),
              '全部成交': pd.concat(orders_all), '已平仓交易': pd.concat(trades_all),
              '每日净值': pd.concat(daily_all), '期末模拟持仓': pd.DataFrame(holdings_all)}
    tables['延长段成交'] = tables['全部成交'].loc[tables['全部成交']['日期'].gt(cutoff)]
    tables['全部成交'] = tables['全部成交'].rename(columns={'ticker':'代码','type':'方向','price':'复权成交价','size':'模拟成交份额','comm':'费用','value':'引擎账面成本'})
    # Comparable passive benchmarks, using the same adjusted-price endpoints.
    passive = []
    benchmark_curve = None
    for path in sorted(daily_root.glob('*_daily_*.parquet')):
        frame = pd.read_parquet(path)
        frame.index = pd.to_datetime(frame.trade_date.astype(str), format='%Y%m%d')
        curve = frame.adj_close.loc[cutoff:]
        passive.append(float(curve.iloc[-1] / curve.iloc[0] - 1))
        if path.name.startswith('510300.'):
            benchmark_curve = curve / curve.iloc[0]
    benchmarks = pd.DataFrame([{'基准': '沪深300ETF买入持有', '延长段收益率': float(benchmark_curve.iloc[-1] - 1)},
                               {'基准': '原49只等权买入持有', '延长段收益率': float(np.mean(passive))}])
    tables['同期基准'] = benchmarks
    coverage_path = run / 'coverage.json'
    if coverage_path.exists():
        universe = pd.DataFrame(json.loads(coverage_path.read_text()))
        universe['名称'] = universe.symbol.str.split('.').str[0].map(names)
        tables['49只池与数据覆盖'] = universe
    tables['口径说明'] = pd.DataFrame({'说明': [
        '模拟回测账单，不是券商实盘账单；每套策略独立使用100万元起始本金。',
        '完整配置为49只ETF，目标同时持有2只；旧BT未执行A_SHARE_ONLY过滤，实际可以交易QDII。',
        '原引擎使用非整手数量与复权研究报价；原价成交、拆分份额及分红现金流尚未逐笔实现。',
        '日线历史原样保留，新增价格按旧复权锚点延长，不能作为实际买卖报价。',
        '延长段收益从2026-02-10收盘已有持仓净值继续计算，未在2月重置100万元。',
        '原份额/融资因子按交易日期连接，融资次日公布；D因子在D+2成交，历史发布版本未完整留存。',
        '历史留出段参与过策略选择；本次没有调参，也没有重新挖掘组合。',
        '旧BT没有执行配置中的个券5%止损；本次保留原样，不能解释为止损已经生效。',
        '512720融资数据本次接口仅到2026-07-10，旧因子沿用旧值；159985无融资记录。',
        '被称为回退的策略在此独立运行，并未模拟与主策略之间人工或自动切换。',
        '被动基准不扣交易费用；ETF名称使用当前基金元数据，仅作识别。',
        '行情及结果只保存在本地。']})
    with pd.ExcelWriter(run / 'ETF轮动模拟账单.xlsx', engine='openpyxl') as writer:
        for name, frame in tables.items():
            frame.to_excel(writer, sheet_name=name, index=False)
            ws = writer.sheets[name];ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width=min(40,max(14,len(str(col[0].value))*2+2))
    (run / 'statement_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(2, 1, figsize=(12, 7), constrained_layout=True)
    for (label, eq), color, english in zip(curves.items(), ['#2563eb','#ea580c'], ['composite_1','core_4f']):
        axs[0].plot(eq.index, eq/1e6, label=english, color=color)
        after=eq.loc[cutoff:];axs[1].plot(after.index,after/after.iloc[0],label=english,color=color)
    if benchmark_curve is not None:
        axs[1].plot(benchmark_curve.index, benchmark_curve.values, label='510300 buy-and-hold (gross)', color='#15803d', alpha=.8)
    axs[0].axvline(pd.Timestamp(cutoff),color='grey',linestyle='--');axs[0].set_title('Full replay - net asset value (initial capital = 1 million CNY)')
    axs[1].set_title('Continuation after 2026-02-10 - no portfolio reset')
    for ax in axs:ax.legend();ax.grid(alpha=.2)
    fig.savefig(run/'equity_curves.png',dpi=150)
    buf=io.BytesIO();fig.savefig(buf,format='png',dpi=130);plt.close(fig)
    image=base64.b64encode(buf.getvalue()).decode()
    display=pd.DataFrame(summary).copy()
    for col in display:
        if '收益率' in col or '回撤' in col:display[col]=display[col].map(lambda v:f'{v:.2%}')
    recent_month=tables['月度收益'][tables['月度收益']['月份'].ge('2026-02')].copy();recent_month['月收益率']=recent_month['月收益率'].map(lambda v:f'{v:.2%}')
    html='<!doctype html><meta charset="utf-8"><title>ETF轮动模拟账单</title><style>body{font:16px sans-serif;max-width:1200px;margin:32px auto;color:#182230}table{border-collapse:collapse;font-size:13px}td,th{padding:8px;border:1px solid #ddd}img{width:100%}.wide{overflow:auto}</style>'
    html+='<h1>ETF轮动模拟账单</h1><p>历史策略原样延长；49只配置池、同时目标持有2只。非券商账单，非整手及复权成交口径保留。</p><div class="wide">'+display.to_html(index=False)+'</div>'
    html+='<img src="data:image/png;base64,'+image+'"><h2>近期月度收益</h2>'+recent_month.to_html(index=False)
    benchmark_display = benchmarks.copy()
    benchmark_display['延长段收益率'] = benchmark_display['延长段收益率'].map(lambda v: f'{v:.2%}')
    html += '<h2>同期被动基准（未扣费用）</h2>' + benchmark_display.to_html(index=False)
    html+='<h2>期末模拟持仓</h2>'+tables['期末模拟持仓'].to_html(index=False)+'<h2>最近成交</h2>'+tables['全部成交'].sort_values('日期').tail(24).to_html(index=False)
    html+='<h2>口径</h2>'+tables['口径说明'].to_html(index=False)
    (run/'ETF轮动模拟账单.html').write_text(html)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True);parser.add_argument('--daily-root',type=Path,required=True)
    parser.add_argument('--names',type=Path);args=parser.parse_args()
    build(args.run,args.daily_root,args.names)
