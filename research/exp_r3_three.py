"""Your 9 coins only, 1h bars: your original V2 vs V3.1 vs V3.2 vs buy-and-hold, side by side.
V2 as written in the brief: per-coin ladder, 40/35/25, TP1 1.25C sells 50%, TP2 1.50C sells 25%,
25% permanent tail, next gen at the B3 fill (no gap), $200 per gen up to 6 gens within a $1,700
cap, $50 spike at -60% sold +40%. All runs fill at the limit price (conservative)."""
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import pandas as pd
import engine as E
import lab
import principal as PR
import runner as R
from exp_final import V31P
from exp_r3_ext import theirs

COINS = lab.CORE + lab.SAT + ['UNI']


def specs(coin):
    return {'V2 (yours)': E.with_(theirs(coin, 6, True), fill_at_limit=True),
            'V3.1': V31P(fill_at_limit=True, tail_intraday=True),
            'V3.2': V31P(tp1_frac=0.90, tail_exit=('target', 4.0), fill_at_limit=True, tail_intraday=True),
            'bh': None}


def one(b, coin):
    out = []
    for n, p in specs(coin).items():
        r = E.run_bh(b) if p is None else E.run_core(b, p)
        eq = r['equity']; ret = eq - 1
        st = PR.principal_stats(r, b)
        win = ret > 0
        out.append({'strat': n, 'end_B': ret[-1], 'end_P': st['ret_P'], 'P': st['P'],
                    'maxdd': float((1 - eq / np.maximum.accumulate(eq)).max()),
                    'p_win': win.mean(), 'gain': ret[win].mean() if win.any() else 0.0,
                    'loss': ret[~win].mean() if (~win).any() else 0.0,
                    'lev': float(np.mean(np.log(np.maximum(eq, 1e-6))))})
    return out


def job(a):
    coin, H = a
    b = R._bars(coin, '1d' if coin == 'HYPE' else '1h')
    days = b.t // E.DAY_MS
    rows = []
    if H == 0:
        for x in one(b, coin):
            rows.append(dict(x, coin=coin, H='full', d0=int(days[0])))
        return rows
    d = int(days[0]) + 3
    while d + H <= int(days[-1]) + 1:
        for x in one(lab.slice_days(b, d, d + H), coin):
            rows.append(dict(x, coin=coin, H=H, d0=d))
        d += 30
    return rows


if __name__ == '__main__':
    with ProcessPoolExecutor(4) as ex:
        df = pd.DataFrame([x for p in ex.map(job, [(c, H) for c in COINS for H in (540, 1095, 0)]) for x in p])
    df.to_pickle('results/r3_three.pkl')
    pd.set_option('display.width', 250)
    order = ['V2 (yours)', 'V3.1', 'V3.2', 'bh']
    for H in (540, 1095):
        w = df[df.H == H]
        t = w.groupby('strat').agg(n=('end_B', 'size'), end_B_med=('end_B', 'median'), end_P_med=('end_P', 'median'),
                                   P_mean=('P', 'mean'), dd_med=('maxdd', 'median'), dd_p90=('maxdd', lambda x: x.quantile(.9)),
                                   p_win=('p_win', 'mean'), gain=('gain', 'mean'), loss=('loss', 'mean'), lev=('lev', 'mean'))
        print(f'\n=== your 9 coins, {H}-day windows (step 30), conservative fills'); print(t.loc[order].round(3).to_string())
        wins = w.pivot_table(index=['coin', 'd0'], columns='strat', values='end_B')
        print('share of windows where each beats V2 (end of window):', {s: round(float((wins[s] > wins['V2 (yours)']).mean()), 2) for s in ['V3.1', 'V3.2', 'bh']})
    f = df[df.H == 'full']
    print('\n=== full history per coin: final multiple of budget (end_B+1) / max drawdown')
    print(f.pivot_table(index='coin', columns='strat', values='end_B')[order].add(1).round(2).to_string())
    print(f.pivot_table(index='coin', columns='strat', values='maxdd')[order].round(2).to_string())
    print(f.pivot_table(index='coin', columns='strat', values='end_P')[order].add(1).round(2).to_string())
