"""Per-coin buy ladder vs one uniform ladder, on the user's 9 coins (1h, fills at the limit).
The user's V2 ladders come from each coin's historical touch probabilities. To test that idea
without hindsight, the per-coin ladder is rebuilt at every window start from the PREVIOUS 365 days
only: d_k = the depth this coin reached within 60 days with the same probability p_k that the
uniform -7/-17/-35% ladder has on average (so both ladders target the same fill odds).
Also: (a) the V2 hand-set ladders (chosen with the full history, so they are in-sample);
(b) stability: are a coin's depth quantiles in the first half of its history similar to the second half?"""
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import pandas as pd
import engine as E
import lab
import runner as R
from exp_final import V31P

COINS = lab.CORE + lab.SAT + ['UNI']
UNI_D = (0.07, 0.17, 0.35)
LOOK, FWD = 365, 60


def daily(coin):
    f = lab.coin_frame(coin, '1d')
    d = pd.DataFrame({'day': (f['open_time_ms'] // E.DAY_MS).astype(int), 'low': f['low'].values,
                      'close': f['close'].values}).set_index('day')
    return d


def depths(d):
    """depth(t) = 1 - min(low over the next FWD days) / close(t)"""
    lows = d.low.values[::-1]
    fut = pd.Series(lows).rolling(FWD, min_periods=FWD).min().values[::-1]
    fmin = np.full(len(d), np.nan)
    fmin[:-1] = fut[1:]
    return pd.Series(1 - fmin / d.close.values, index=d.index)


def pooled_p():
    """average touch probability of the uniform ladder across the 9 coins (60-day horizon)."""
    allx = pd.concat([depths(daily(c)).dropna() for c in COINS])
    return [float((allx >= x).mean()) for x in UNI_D]


def ladder_at(dep, d0, P):
    h = dep.loc[d0 - LOOK:d0 - FWD - 1].dropna()   # only depths fully known before d0
    if len(h) < 200:
        return UNI_D
    q = [float(np.quantile(h, 1 - p)) for p in P]
    q = [min(max(x, 0.03), 0.6) for x in q]
    q = sorted(q)
    return (q[0], max(q[1], q[0] + 0.03), max(q[2], q[1] + 0.05))


def job(a):
    coin, H, P = a
    b = R._bars(coin, '1d' if coin == 'HYPE' else '1h')
    dep = depths(daily(coin))
    days = b.t // E.DAY_MS
    rows = []
    d = int(days[0]) + 3 + LOOK          # need a year of history for the PIT ladder
    while d + H <= int(days[-1]) + 1:
        w = lab.slice_days(b, d, d + H)
        lad = ladder_at(dep, d, P)
        sp = {'uniform -7/-17/-35': UNI_D, 'per-coin PIT (same fill odds)': lad,
              'V2 hand-set per coin': E.V2_CORE.get(coin, (0.07, 0.17, 0.29))}
        for n, dd in sp.items():
            r = E.run_core(w, V31P(d=dd, tp1_frac=0.90, tail_exit=('target', 4.0), fill_at_limit=True, tail_intraday=True))
            eq = r['equity']
            rows.append({'coin': coin, 'H': H, 'd0': d, 'ladder': n, 'd': tuple(round(x, 3) for x in dd),
                         'end': eq[-1] - 1, 'lr': np.log(max(eq[-1], 1e-6)),
                         'dd': float((1 - eq / np.maximum.accumulate(eq)).max())})
        d += 30
    return rows


if __name__ == '__main__':
    pd.set_option('display.width', 250)
    P = pooled_p()
    print('uniform ladder, pooled 60-day touch probability on the 9 coins:', [round(p, 3) for p in P])
    print('\n=== stability: depth reached with those probabilities, first half vs second half of each coin history')
    rows = []
    for c in COINS:
        dep = depths(daily(c)).dropna()
        h1, h2 = dep.iloc[:len(dep) // 2], dep.iloc[len(dep) // 2:]
        rows.append({'coin': c, 'years': round(len(dep) / 365, 1),
                     **{f'1st d{k+1}': round(float(np.quantile(h1, 1 - p)), 3) for k, p in enumerate(P)},
                     **{f'2nd d{k+1}': round(float(np.quantile(h2, 1 - p)), 3) for k, p in enumerate(P)}})
    st = pd.DataFrame(rows).set_index('coin'); print(st.to_string())
    for k in (1, 2, 3):
        print(f'rank correlation across coins, d{k} first vs second half:',
              round(st[f'1st d{k}'].rank().corr(st[f'2nd d{k}'].rank()), 2))
    with ProcessPoolExecutor(4) as ex:
        df = pd.DataFrame([x for p in ex.map(job, [(c, H, P) for c in COINS for H in (540, 1095)]) for x in p])
    df.to_pickle('results/r3_percoin.pkl')
    for H in (540, 1095):
        w = df[df.H == H]
        t = w.groupby('ladder').agg(n=('end', 'size'), end_med=('end', 'median'), lr=('lr', 'mean'),
                                    p10=('end', lambda x: x.quantile(.1)), dd_med=('dd', 'median'))
        base = w[w.ladder == 'uniform -7/-17/-35'].set_index(['coin', 'd0']).lr
        t['beats_uniform'] = [float((w[w.ladder == n].set_index(['coin', 'd0']).lr > base).mean()) for n in t.index]
        print(f'\n=== {H}-day windows (starts after one year of history), V3.2 rules otherwise'); print(t.round(3).to_string())
        pc = w.pivot_table(index='coin', columns='ladder', values='lr')
        print(pc.round(3).to_string())
    last = df[(df.H == 540) & (df.ladder == 'per-coin PIT (same fill odds)')].sort_values('d0').groupby('coin').d.last()
    print('\nlatest PIT per-coin ladder (what the method would set today-ish):'); print(last.to_string())
