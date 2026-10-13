"""Two questions on the user's 9 coins (1h bars, fills at the limit price):
 A. Is TP = 1.25C special? Grid tp1 = 1.15 .. 1.50 with the V3.2 tail.
 B. Tail lots: how often does a lot reach k x its cost (k = 1.5 .. 10) within 1 / 2 / 3 years,
    how long it takes, and the expected value per lot of each target
    (hit -> k; not hit by the horizon -> the price then / C; same horizon for every k)."""
import sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import pandas as pd
import engine as E
import lab
import runner as R
from exp_final import V31P

COINS = lab.CORE + lab.SAT + ['UNI']
TPS = (0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50)


def params(tp):
    return V31P(tp1=tp, tp1_frac=0.90, tail_exit=('target', 4.0), fill_at_limit=True, tail_intraday=True)


def wjob(a):
    coin, H = a
    b = R._bars(coin, '1d' if coin == 'HYPE' else '1h')
    days = b.t // E.DAY_MS
    rows = []
    d = int(days[0]) + 3
    while d + H <= int(days[-1]) + 1:
        w = lab.slice_days(b, d, d + H)
        for tp in TPS:
            r = E.run_core(w, params(tp))
            eq = r['equity']; ret = eq - 1
            rows.append({'coin': coin, 'H': H, 'd0': d, 'tp': tp, 'end': ret[-1],
                         'lr': np.log(max(eq[-1], 1e-6)), 'lev': float(np.mean(np.log(np.maximum(eq, 1e-6)))),
                         'p_win': float((ret > 0).mean()),
                         'dd': float((1 - eq / np.maximum.accumulate(eq)).max()),
                         'cycles_py': r['tp1_count'] / (H / 365)})
        d += 30
    return rows


def lots(coin):
    """tail lots of V3.2 (TP at 1.25C) over the full history: creation time, C, then the path."""
    b = R._bars(coin, '1d' if coin == 'HYPE' else '1h')
    r = E.run_core(b, params(0.25))
    day = b.t // E.DAY_MS
    dh = pd.DataFrame({'day': day, 'h': b.h, 'c': b.c}).groupby('day').agg(h=('h', 'max'), c=('c', 'last'))
    out = []
    for ev in r['events']:
        if ev[1] != 'tp1':
            continue
        i, C = ev[0], ev[3]
        d0 = int(day[i])
        fut = dh.loc[d0 + 1:]
        rec = {'coin': coin, 'd0': d0, 'C': C, 'days_avail': len(fut)}
        for T in (365, 730, 1095):
            f = fut.iloc[:T]
            rec[f'full_{T}'] = len(f) >= T
            rec[f'end_{T}'] = f.c.iloc[-1] / C if len(f) else np.nan
            cummax = f.h.cummax().values / C
            for k in (1.5, 2, 3, 4, 5, 7, 10):
                hit = np.nonzero(cummax >= k * 1.0005)[0]
                rec[f'hit{k}_{T}'] = len(hit) > 0
                rec[f'days{k}_{T}'] = hit[0] + 1 if len(hit) else np.nan
        out.append(rec)
    return out


if __name__ == '__main__':
    pd.set_option('display.width', 250)
    with ProcessPoolExecutor(4) as ex:
        w = pd.DataFrame([x for p in ex.map(wjob, [(c, H) for c in COINS for H in (540, 1095)]) for x in p])
        L = pd.DataFrame([x for p in ex.map(lots, COINS) for x in p])
    w.to_pickle('results/r3_tp_grid.pkl'); L.to_pickle('results/r3_tail_lots.pkl')
    print('=== A. TP level, your 9 coins, V3.2 tail, conservative fills')
    for H in (540, 1095):
        t = w[w.H == H].groupby('tp').agg(n=('end', 'size'), end_med=('end', 'median'), lr=('lr', 'mean'),
                                          p10=('end', lambda x: x.quantile(.1)), lev=('lev', 'mean'), p_win=('p_win', 'mean'),
                                          dd_med=('dd', 'median'), cycles_py=('cycles_py', 'mean'))
        base = w[(w.H == H) & (w.tp == 0.25)].set_index(['coin', 'd0']).lr
        t['beats_1.25'] = [float((w[(w.H == H) & (w.tp == tp)].set_index(['coin', 'd0']).lr > base).mean()) for tp in t.index]
        print(f'-- {H}-day windows'); print(t.round(3).to_string())
        per = w[w.H == H].pivot_table(index='coin', columns='tp', values='lr')
        print('best TP per coin (mean log):', per.idxmax(axis=1).to_dict())
    print('\n=== B. tail lots (V3.2, TP 1.25C), your 9 coins, full history; n lots =', len(L))
    for T in (365, 730, 1095):
        s = L[L[f'full_{T}']]
        rows = []
        for k in (1.5, 2, 3, 4, 5, 7, 10):
            hit = s[f'hit{k}_{T}']
            val = np.where(hit, k * 0.999, s[f'end_{T}'])
            rows.append({'target': f'{k}x', 'p_hit': hit.mean(), 'median_days': s.loc[hit, f'days{k}_{T}'].median(),
                         'EV_per_lot (x cost)': val.mean(), 'EV_median': np.median(val), 'coins_hit': s.loc[hit, 'coin'].nunique()})
        rows.append({'target': 'hold (no target)', 'p_hit': np.nan, 'median_days': np.nan,
                     'EV_per_lot (x cost)': s[f'end_{T}'].mean(), 'EV_median': s[f'end_{T}'].median(), 'coins_hit': np.nan})
        print(f'-- horizon {T} days: {len(s)} lots with a full horizon, from {s.coin.nunique()} coins, '
              f'{s.d0.floordiv(30).nunique()} distinct months')
        print(pd.DataFrame(rows).round(3).to_string(index=False))
    s = L[L['full_730']]
    print('\nper coin, 2-year horizon: lots / P(2x) / P(3x) / P(5x)')
    print(s.groupby('coin').agg(lots=('C', 'size'), p2=('hit2_730', 'mean'), p3=('hit3_730', 'mean'), p5=('hit5_730', 'mean')).round(2).to_string())
