"""Round 3: spike-order economics in dollars and in actions.
For each run: value of the spike module = V3.1 minus V3.1 without spike (its
7.5% folded into the ladder), per year, as a multiple of the spike stake S;
and the number of order actions per year that the spike order adds.
Spike re-pegs that coincide with a ladder re-placement (new cycle / anchor
drift) cost no extra session; the extra ones are its own fills and sales."""
import sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import pandas as pd
import engine as E
import lab
import runner as R
from exp_final import V31P

S = 0.075
WITH = V31P(tp1_frac=0.90, tail_exit=('target', 4.0))
WITHOUT = V31P(tp1_frac=0.90, tail_exit=('target', 4.0), spike_frac=0.0)


def one(b):
    r1 = E.run_core(b, WITH); r0 = E.run_core(b, WITHOUT)
    yrs = len(r1['equity']) / 365
    ev = r1['events']
    kinds = pd.Series([e[1] for e in ev]).value_counts().to_dict() if ev else {}
    ladder_sessions = kinds.get('tp1', 0) + kinds.get('anchor', 0)
    return {'years': yrs, 'gain_per_S_py': (r1['equity'][-1] - r0['equity'][-1]) / S / yrs,
            'lr_diff': np.log(max(r1['equity'][-1], 1e-9)) - np.log(max(r0['equity'][-1], 1e-9)),
            'fills_py': kinds.get('spike_buy', 0) / yrs, 'sells_py': kinds.get('spike_sell', 0) / yrs,
            'repeg_py': ladder_sessions / yrs}


def ujob(a):
    sym, d0, H = a
    b = R.symbol_bars(sym, d0, d0 + H)
    if b is None:
        return None
    o = one(b); o.update(sym=sym, d0=d0, H=H)
    return o


if __name__ == '__main__':
    rows = []
    for c in lab.CORE + lab.SAT + ['UNI']:
        b = R._bars(c, '1d' if c == 'HYPE' else '1h')
        o = one(b); o.update(sym=c, d0=-1, H=0); rows.append(o)
    foc = pd.DataFrame(rows)
    print('=== focus coins, full history (1h)'); print(foc.round(3).to_string(index=False))
    jobs = []
    for H, step in ((540, 60), (1095, 90)):
        d = int(pd.Timestamp('2019-01-01').value // 10**6 // E.DAY_MS)
        last = int(R.universe_panel()['close'].index.max()) - H
        while d <= last:
            jobs += [(s, d, H) for s in R.pit_universe(d, 30)]
            d += step
    with ProcessPoolExecutor(4) as ex:
        u = pd.DataFrame([x for x in ex.map(ujob, jobs, chunksize=8) if x])
    u.to_pickle('results/r3_spike_univ.pkl')
    print('\n=== universe windows')
    print(u.groupby('H')[['gain_per_S_py', 'lr_diff', 'fills_py', 'sells_py', 'repeg_py']].agg(['mean', 'median']).round(3).to_string())
    print('share of windows where spike helped:', u.groupby('H').lr_diff.apply(lambda x: (x > 0).mean()).round(3).to_dict(),
          ' hurt:', u.groupby('H').lr_diff.apply(lambda x: (x < 0).mean()).round(3).to_dict())
