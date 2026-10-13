"""Round 3: reconcile the other lab's V2->V3 report with ours.
 X1 generations 1..6 under both budget conventions (their fixed $200/gen with a
    $1,700 cap vs our fraction-of-budget), on their TEST window and on rolling
    universe windows; reported on the budget, on peak principal and in dollars.
 X2 their TEST window (2025-01-01 .. 2026-10-11): V2 / V3.1 / new tail / B&H.
 X3 their health indicator: fewer than 2 completed cycles in the last 12 months
    -> does it predict the next 540 days? (universe, point in time)
 X4 UNI vs ZRO on the common window."""
import sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import pandas as pd
import engine as E
import lab
import principal as PR
import runner as R
from exp_final import V31P

pd.set_option('display.width', 250); pd.set_option('display.max_rows', 300)
DAY = E.DAY_MS
EIGHT = ['HYPE', 'TAO', 'LINK', 'AAVE', 'NEAR', 'ZRO', 'PENDLE', 'RENDER']
NEW = dict(tp1_frac=0.90, tail_exit=('target', 4.0))


def theirs(coin, gens, fixed=True):
    d = E.V2_CORE.get(coin, (0.07, 0.17, 0.29))
    kw = dict(d=d, w=(0.40, 0.35, 0.25), tp1=0.25, tp1_frac=0.5, tp2=0.5, tp2_frac=0.25, tail_exit=('none',),
              max_gens=gens, gen_gap=0.0, spike_frac=50 / 1700, drift=0.20, tp2_reanchor=True)
    if fixed:
        kw['fixed_g'] = 200 / 1700
    return E.CoreParams(**kw)


def ours(gens, fixed=False):
    kw = dict(max_gens=gens, **NEW)
    if fixed:
        kw['fixed_g'] = (1 - 0.075) / 3
        kw['budget_units'] = gens
    return V31P(**kw)


def gen_specs(coin):
    sp = {}
    for g in (1, 2, 3, 4, 6):
        sp[f'their fixed$ g{g}'] = theirs(coin, g, True)
        sp[f'ours share g{g}'] = ours(g, False)
        sp[f'ours fixedG g{g}'] = ours(g, True)
    return sp


def run_set(b, coin):
    out = []
    for n, p in gen_specs(coin).items():
        r = E.run_core(b, p)
        st = PR.principal_stats(r, b)
        eq = r['equity']
        st.update(spec=n, maxdd=float((1 - eq / np.maximum.accumulate(eq)).max()), deployed_max=st['P'])
        out.append(st)
    return out


def ujob(a):
    sym, d0, H = a
    b = R.symbol_bars(sym, d0, d0 + H)
    if b is None:
        return []
    rows = run_set(b, sym.replace('USDT', ''))
    for x in rows:
        x.update(sym=sym, d0=d0, H=H)
    return rows


def x1():
    t0 = int(pd.Timestamp('2025-01-01').value // 10**6 // DAY)
    rows = []
    for c in EIGHT:
        b = R._bars(c, '1d' if c == 'HYPE' else '1h')
        days = b.t // DAY
        b = lab.slice_days(b, max(t0, int(days[0])), int(days[-1]) + 1)
        for x in run_set(b, c):
            x.update(sym=c); rows.append(x)
    t = pd.DataFrame(rows)
    print('=== X1a their TEST window 2025-01-01..end, 8 coins: mean over coins')
    print(t.groupby('spec')[['ret_B', 'P', 'ret_P', 'maxdd']].mean().round(3).to_string())
    jobs = []
    for H, step in ((540, 60), (1095, 90)):
        d = int(pd.Timestamp('2019-01-01').value // 10**6 // DAY)
        last = int(R.universe_panel()['close'].index.max()) - H
        while d <= last:
            jobs += [(s, d, H) for s in R.pit_universe(d, 30)]
            d += step
    with ProcessPoolExecutor(4) as ex:
        u = pd.DataFrame([x for p in ex.map(ujob, jobs, chunksize=8) for x in p])
    u['lrB'] = np.log1p(u.ret_B.clip(lower=-.99)); u['lrP'] = np.log1p(u.ret_P.clip(lower=-.99))
    u.to_pickle('results/r3_ext_gens.pkl')
    print('\n=== X1b universe windows: generations under each convention')
    print(u.groupby(['H', 'spec']).agg(medB=('ret_B', 'median'), lrB=('lrB', 'mean'), p10B=('ret_B', lambda x: x.quantile(.1)),
                                       P=('P', 'mean'), lrP=('lrP', 'mean'), p10P=('ret_P', lambda x: x.quantile(.1)),
                                       dd=('maxdd', 'median')).round(3).to_string())


def x2():
    t0 = int(pd.Timestamp('2025-01-01').value // 10**6 // DAY)
    specs = {'V2 (ours)': lambda c: E.CoreParams(d=E.V2_CORE.get(c, (0.07, 0.17, 0.29)), max_gens=3, spike_frac=0.075),
             'V2 their conv (6 gens, $200)': lambda c: theirs(c, 6, True), 'V3.1': lambda c: V31P(),
             'V3.2 cand (10%@5x)': lambda c: V31P(**NEW), 'bh': None}
    rows = []
    for c in EIGHT:
        b = R._bars(c, '1d' if c == 'HYPE' else '1h')
        days = b.t // DAY
        b = lab.slice_days(b, max(t0, int(days[0])), int(days[-1]) + 1)
        for n, mk in specs.items():
            r = E.run_bh(b) if mk is None else E.run_core(b, mk(c))
            rows.append({'coin': c, 'spec': n, 'ret_B': r['equity'][-1] - 1, 'ret_P': PR.principal_stats(r, b)['ret_P']})
    t = pd.DataFrame(rows)
    print('\n=== X2 their TEST window, return on budget (ret_P in second table)')
    print(t.pivot_table(index='coin', columns='spec', values='ret_B').round(3).to_string())
    print(t.pivot_table(index='coin', columns='spec', values='ret_P').round(3).to_string())


def hjob(a):
    sym, d0 = a
    past = R.symbol_bars(sym, d0 - 365, d0, pad=False)
    fut = R.symbol_bars(sym, d0, d0 + 540)
    if past is None or fut is None or len(past) < 300:
        return None
    rp = E.run_core(past, V31P(**NEW))
    rf = E.run_core(fut, V31P(**NEW))
    return {'sym': sym, 'd0': d0, 'cycles_past': rp['tp1_count'], 'fwd_ret': rf['equity'][-1] - 1,
            'fwd_bh': fut.c[-1] / fut.o[0] - 1}


def x3():
    jobs = []
    d = int(pd.Timestamp('2019-07-01').value // 10**6 // DAY)
    last = int(R.universe_panel()['close'].index.max()) - 540
    while d <= last:
        jobs += [(s, d) for s in R.pit_universe(d, 30)]
        d += 60
    with ProcessPoolExecutor(4) as ex:
        h = pd.DataFrame([x for x in ex.map(hjob, jobs, chunksize=8) if x])
    h['flag'] = h.cycles_past < 2
    h['lr'] = np.log1p(h.fwd_ret.clip(lower=-.99))
    print('\n=== X3 health indicator (<2 cycles in past 12 months) vs next 540 days (V3.2 candidate rules)')
    print(h.groupby('flag').agg(n=('lr', 'size'), fwd_med=('fwd_ret', 'median'), fwd_lr=('lr', 'mean'),
                                fwd_p10=('fwd_ret', lambda x: x.quantile(.1)), bh_med=('fwd_bh', 'median')).round(3).to_string())
    # within-date comparison (removes market timing)
    dm = h.groupby('d0').lr.transform('mean')
    h['rel'] = h.lr - dm
    print('relative to same-start average:', h.groupby('flag').rel.agg(['mean', 'median', 'size']).round(3).to_dict())


def x4():
    out = []
    zb = R._bars('ZRO', '1h'); d0 = int(zb.t[0] // DAY) + 3
    for c in ('UNI', 'ZRO', 'NEAR', 'PENDLE', 'RENDER'):
        b = R._bars(c, '1h'); days = b.t // DAY
        b = lab.slice_days(b, max(d0, int(days[0])), int(days[-1]) + 1)
        for n, p in (('V3.1', V31P()), ('V3.2 cand', V31P(**NEW))):
            r = E.run_core(b, p); out.append({'coin': c, 'spec': n, 'ret': r['equity'][-1] - 1,
                                              'cycles': r['tp1_count'], 'bh': b.c[-1] / b.o[0] - 1})
    print('\n=== X4 common window since ZRO listing:', pd.Timestamp(d0, unit='D').date())
    print(pd.DataFrame(out).pivot_table(index='coin', columns='spec', values=['ret', 'cycles', 'bh']).round(3).to_string())


if __name__ == '__main__':
    for part in sys.argv[1:]:
        globals()[part]()
