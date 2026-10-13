"""Layered tails. Design rules taken from the user's own principles:
  * the tail must be pure profit right after TP: selling s at 1.25C returns 1.25*s of cost,
    so s >= 80%, i.e. total tail <= 20%;
  * the higher the multiple, the lower its probability, so the size of a tier should not grow
    with its multiple.
Candidates are scored on the user's 9 coins (1h, fills at the limit price, tail sells resting at
their targets) and, as a stress test, on the point-in-time universe (daily)."""
import sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import pandas as pd
import engine as E
import lab
import runner as R
from exp_final import V31P

COINS = lab.CORE + lab.SAT + ['UNI']
CUT = int(pd.Timestamp('2022-01-01').value // 10**9 // 86400)


def P(tiers=None, single=None):
    base = dict(fill_at_limit=True, tail_intraday=True, tail_exit=('target', 4.0))
    if tiers is None:
        share, mult = single
        return V31P(tp1_frac=1 - share, **{**base, 'tail_exit': ('target', mult - 1.0)}) if share > 0 else V31P(tp1_frac=1.0, **base)
    return V31P(tp1_frac=1 - sum(s for s, _ in tiers), tail_tiers=tiers, **base)


CANDS = {
    'V3.1  25%@2x': P(single=(0.25, 2)),
    'V3.2  10%@5x': P(single=(0.10, 5)),
    'no tail': P(single=(0.0, 1)),
    '10%@3x': P(single=(0.10, 3)),
    '5%@2x + 5%@5x': P(((0.05, 2), (0.05, 5))),
    '10%@2x + 5%@5x': P(((0.10, 2), (0.05, 5))),
    '13%@2x + 7%@5x': P(((0.13, 2), (0.07, 5))),
    '10%@2x + 10%@5x': P(((0.10, 2), (0.10, 5))),
    '8%@2x + 5%@4x + 2%@10x': P(((0.08, 2), (0.05, 4), (0.02, 10))),
    '10%@2x + 6%@4x + 4%@10x': P(((0.10, 2), (0.06, 4), (0.04, 10))),
    '12%@3x + 8%@7x': P(((0.12, 3), (0.08, 7))),
    '25% laddered 12@2 8@4 5@10': P(((0.12, 2), (0.08, 4), (0.05, 10))),
}


def run(w):
    out = []
    for n, p in CANDS.items():
        r = E.run_core(w, p)
        eq = r['equity']; ret = eq - 1
        tail_sells = sum(1 for e in r['events'] if e[1] == 'tail_limit')
        out.append({'cand': n, 'lr': np.log(max(eq[-1], 1e-6)), 'end': ret[-1],
                    'lev': float(np.mean(np.log(np.maximum(eq, 1e-6)))), 'p_win': float((ret > 0).mean()),
                    'dd': float((1 - eq / np.maximum.accumulate(eq)).max()),
                    'tail_sells_py': tail_sells / (len(eq) / 365)})
    return out


def fjob(a):
    coin, H = a
    b = R._bars(coin, '1d' if coin == 'HYPE' else '1h')
    days = b.t // E.DAY_MS
    rows = []
    if H == 0:
        return [dict(x, coin=coin, H='full', d0=int(days[0])) for x in run(b)]
    d = int(days[0]) + 3
    while d + H <= int(days[-1]) + 1:
        rows += [dict(x, coin=coin, H=H, d0=d) for x in run(lab.slice_days(b, d, d + H))]
        d += 30
    return rows


def ujob(a):
    sym, d0, H = a
    b = R.symbol_bars(sym, d0, d0 + H)
    if b is None:
        return []
    return [dict(x, coin=sym, H=H, d0=d0) for x in run(b)]


def table(w, base='V3.1  25%@2x'):
    t = w.groupby('cand').agg(n=('lr', 'size'), lr=('lr', 'mean'), end_med=('end', 'median'),
                              p10=('end', lambda x: x.quantile(.1)), lev=('lev', 'mean'), p_win=('p_win', 'mean'),
                              dd_med=('dd', 'median'), tail_sells_py=('tail_sells_py', 'mean'))
    b = w[w.cand == base].set_index(['coin', 'd0']).lr
    t['beats_V3.1'] = [float((w[w.cand == c].set_index(['coin', 'd0']).lr > b).mean()) for c in t.index]
    t['lr_pre2022'] = w[w.d0 < CUT].groupby('cand').lr.mean()
    t['lr_2022+'] = w[w.d0 >= CUT].groupby('cand').lr.mean()
    return t.sort_values('lr', ascending=False)


if __name__ == '__main__':
    pd.set_option('display.width', 260); pd.set_option('display.max_colwidth', 40)
    with ProcessPoolExecutor(4) as ex:
        f = pd.DataFrame([x for p in ex.map(fjob, [(c, H) for c in COINS for H in (540, 1095, 0)]) for x in p])
        jobs = []
        for H in (540, 1095, 1825):
            d = int(pd.Timestamp('2019-01-01' if H < 1825 else '2018-07-01').value // 10**6 // E.DAY_MS)
            last = int(R.universe_panel()['close'].index.max()) - H
            while d <= last:
                jobs += [(s, d, H) for s in R.pit_universe(d, 30)]
                d += 90
        u = pd.DataFrame([x for p in ex.map(ujob, jobs, chunksize=8) for x in p])
    f.to_pickle('results/r3_tiers_focus.pkl'); u.to_pickle('results/r3_tiers_univ.pkl')
    for H in (540, 1095):
        print(f'\n=== YOUR 9 COINS, {H}-day windows (step 30)'); print(table(f[f.H == H]).round(3).to_string())
    full = f[f.H == 'full'].pivot_table(index='coin', columns='cand', values='lr')
    print('\n=== your coins, full history: mean log final over 9 coins')
    print(full.mean().sort_values(ascending=False).round(3).to_string())
    for H in (540, 1095, 1825):
        print(f'\n=== STRESS TEST: PIT universe, {H}-day windows'); print(table(u[u.H == H]).round(3).to_string())
