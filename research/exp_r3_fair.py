"""Round 3 follow-up (user's fairness request):
 1. Random exit: for every window, the outcome if you liquidate on a random day of the window
    (uniform), for buy-and-hold and for V3.2: P(profit), mean gain when in profit, mean loss when
    in loss, expected value = P*gain + (1-P)*loss.
 2. Capital tied up: return per unit of capital actually tied up (position cost + resting buy
    orders on the exchange); not-yet-posted reserves count as free cash.
V3.2 uses conservative execution (fills at the limit price, tail sells as resting limits)."""
import sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import pandas as pd
import engine as E
import lab
import runner as R
from exp_final import V31P

P32 = V31P(tp1_frac=0.90, tail_exit=('target', 4.0), fill_at_limit=True, tail_intraday=True)


def stats(b):
    out = {}
    for name in ('V3.2', 'bh'):
        r = E.run_core(b, P32) if name == 'V3.2' else E.run_bh(b)
        eq = r['equity']; ret = eq - 1.0
        win = ret > 0
        yrs = len(eq) / 365
        tied = (r['pos_cost'] + r.get('pending', 0.0)) if name == 'V3.2' else np.ones(len(eq))
        out[name] = {'p_win': win.mean(), 'gain': ret[win].mean() if win.any() else 0.0,
                     'loss': ret[~win].mean() if (~win).any() else 0.0, 'ev': ret.mean(),
                     'end': ret[-1], 'lev': float(np.mean(np.log(np.maximum(eq, 1e-6)))), 'tied': float(np.mean(tied)),
                     'roc_py': (eq[-1] - 1) / yrs / max(float(np.mean(tied)), 1e-9)}
    return out


def ujob(a):
    sym, d0, H = a
    b = R.symbol_bars(sym, d0, d0 + H)
    if b is None or len(b) < H * 0.5:
        return []
    s = stats(b)
    return [dict(v, strat=k, sym=sym, d0=d0, H=H, src='universe') for k, v in s.items()]


def fjob(a):
    coin, H = a
    b = R._bars(coin, '1d' if coin == 'HYPE' else '1h')
    days = b.t // E.DAY_MS
    rows = []
    d = int(days[0]) + 3
    while d + H <= int(days[-1]) + 1:
        s = stats(lab.slice_days(b, d, d + H))
        rows += [dict(v, strat=k, sym=coin, d0=d, H=H, src='your coins') for k, v in s.items()]
        d += 30
    return rows


if __name__ == '__main__':
    jobs = []
    for H in (540, 1095, 1825):
        d = int(pd.Timestamp('2019-01-01' if H < 1825 else '2018-07-01').value // 10**6 // E.DAY_MS)
        last = int(R.universe_panel()['close'].index.max()) - H
        while d <= last:
            jobs += [(s, d, H) for s in R.pit_universe(d, 30)]
            d += 90
    fj = [(c, H) for c in lab.CORE + lab.SAT + ['UNI'] for H in (540, 1095)]
    with ProcessPoolExecutor(4) as ex:
        rows = [x for p in ex.map(ujob, jobs, chunksize=8) for x in p]
        rows += [x for p in ex.map(fjob, fj) for x in p]
    df = pd.DataFrame(rows)
    df.to_pickle('results/r3_fair.pkl')
    pd.set_option('display.width', 250)
    g = df.groupby(['src', 'H', 'strat']).agg(n=('ev', 'size'), p_win=('p_win', 'mean'), gain=('gain', 'mean'),
                                               loss=('loss', 'mean'), ev=('ev', 'mean'), ev_med=('ev', 'median'),
                                               end=('end', 'mean'), lev=('lev', 'mean'), tied=('tied', 'mean'), roc_py=('roc_py', 'median'))
    g['check_p*gain+(1-p)*loss'] = g.p_win * g.gain + (1 - g.p_win) * g.loss
    print(g.round(3).to_string())
