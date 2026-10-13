"""Depth grid around V3: gen_gap x gen_mult x spike_frac (+ reference variants).

Run from anywhere; imports research code from the repo without writing into it.
Usage:
  python3 depth_grid.py focus 540 30
  python3 depth_grid.py focus 1095 30
  python3 depth_grid.py universe 540 60
  python3 depth_grid.py universe 1095 90
  python3 depth_grid.py all                 # the four runs above, sequentially
  python3 depth_grid.py ext                 # finer gap fill-in (0.25/0.35/0.45, mult 1.25) -> depth_ext_*.csv
  python3 depth_grid.py paths NAME [NAME..] # equity paths (focus H540/H1095, universe H540/H1095) -> npz
Outputs go to research/results/.
"""
import sys, os, time, itertools
sys.dont_write_bytecode = True
REPO_RESEARCH = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO_RESEARCH)

import numpy as np, pandas as pd
import engine as E, lab, runner as R
from exp_final import V3P

OUT = os.path.join(REPO_RESEARCH, "results")
FOCUS = lab.CORE + lab.SAT + ['UNI']
WORKERS = 2

GAPS = [0.20, 0.30, 0.40, 0.50, 0.60]
MULTS = [1.0, 1.5, 2.0]
SPIKES = [0.075, 0.15]


def vname(gap, mult, spike):
    m = f"{mult:.1f}" if abs(mult * 10 - round(mult * 10)) < 1e-9 else f"{mult:.2f}"
    return f"gap={gap:.2f} mult={m} spike={spike:.3f}"


SPECS = {}
for gap, mult, spike in itertools.product(GAPS, MULTS, SPIKES):
    SPECS[vname(gap, mult, spike)] = ('core', V3P(gen_gap=gap, gen_mult=mult, spike_frac=spike))
SPECS['gens=2 gap0.4 (budget 2u)'] = ('core', V3P(max_gens=2, gen_gap=0.4))
SPECS['gens=2 gap0.4 (budget 3u)'] = ('core', V3P(max_gens=2, gen_gap=0.4, budget_units=3))
SPECS['V3'] = ('core', V3P())

# finer fill-in around the turning region (run with 'ext'; written to depth_ext_*.csv)
EXT_SPECS = {}
for gap, mult, spike in list(itertools.product([0.25, 0.35, 0.45], [1.0], SPIKES)) + [(0.35, 1.25, 0.075), (0.40, 1.25, 0.075)]:
    EXT_SPECS[vname(gap, mult, spike)] = ('core', V3P(gen_gap=gap, gen_mult=mult, spike_frac=spike))
EXT_SPECS['V3'] = SPECS['V3']


def run_focus(H, step, specs=None, prefix='depth'):
    t = time.time()
    df = R.grid(FOCUS, specs or SPECS, horizon=H, step=step, workers=WORKERS)
    p = os.path.join(OUT, f'{prefix}_focus_H{H}.csv'); df.to_csv(p, index=False)
    print(f'focus H{H}: {len(df)} rows, {df.variant.nunique()} variants, {time.time()-t:.0f}s -> {p}', flush=True)


def run_universe(H, step, specs=None, prefix='depth'):
    t = time.time()
    df = R.universe_grid(specs or SPECS, horizon=H, step=step, top=30, workers=WORKERS)
    p = os.path.join(OUT, f'{prefix}_universe_H{H}.csv'); df.to_csv(p, index=False)
    print(f'universe H{H}: {len(df)} rows, {df.variant.nunique()} variants, {time.time()-t:.0f}s -> {p}', flush=True)


# ---------------------------------------------------------------- equity paths
def _fpath_job(args):
    coin, names, H, step = args
    iv = '1d' if coin == 'HYPE' else '1h'
    b = R._bars(coin, iv)
    days = b.t // E.DAY_MS
    d_first, d_last = int(days[0]), int(days[-1])
    out = []
    s = d_first
    while s + H <= d_last + 1:
        x = lab.slice_days(b, s, s + H)
        if len(x) > 10:
            for nm in names:
                r = R.run_strategy(x, SPECS[nm])
                out.append((nm, coin, s, r['equity'].astype(np.float32), r['pos_value'].astype(np.float32)))
        s += step
    return out


def _upath_job(args):
    sym, d0, H, names = args
    b = R.symbol_bars(sym, d0, d0 + H)
    if b is None:
        return []
    out = []
    for nm in names:
        r = R.run_strategy(b, SPECS[nm])
        out.append((nm, sym, d0, r['equity'].astype(np.float32), r['pos_value'].astype(np.float32)))
    return out


def run_paths(names):
    from concurrent.futures import ProcessPoolExecutor
    for kind, H, step in [('focus', 540, 30), ('focus', 1095, 30), ('universe', 540, 60), ('universe', 1095, 90)]:
        t = time.time()
        if kind == 'focus':
            jobs = [(c, names, H, step) for c in FOCUS]
            fn = _fpath_job
        else:
            d = int(pd.Timestamp('2019-01-01').value // 10**6 // E.DAY_MS)
            end_day = int(R.universe_panel()['close'].index.max()) - H
            jobs = []
            while d <= end_day:
                for sym in R.pit_universe(d, 30):
                    jobs.append((sym, d, H, names))
                d += step
            fn = _upath_job
        with ProcessPoolExecutor(WORKERS) as ex:
            parts = list(ex.map(fn, jobs, chunksize=1 if kind == 'focus' else 4))
        rows = [r for p in parts for r in p]
        for nm in names:
            sel = [r for r in rows if r[0] == nm]
            tag = nm.replace(' ', '_').replace('=', '').replace('(', '').replace(')', '')
            p = os.path.join(OUT, f'paths_{kind}_H{H}_{tag}.npz')
            np.savez_compressed(p, key=np.array([r[1] for r in sel]), start=np.array([r[2] for r in sel]),
                                eq=np.array([r[3] for r in sel], dtype=object),
                                pos=np.array([r[4] for r in sel], dtype=object))
        print(f'paths {kind} H{H}: {len(rows)} runs, {time.time()-t:.0f}s', flush=True)


if __name__ == '__main__':
    which = sys.argv[1]
    print(f'{len(SPECS)} variants', flush=True)
    if which == 'focus':
        run_focus(int(sys.argv[2]), int(sys.argv[3]))
    elif which == 'universe':
        run_universe(int(sys.argv[2]), int(sys.argv[3]))
    elif which == 'all':
        run_focus(540, 30); run_focus(1095, 30)
        run_universe(540, 60); run_universe(1095, 90)
    elif which == 'ext':
        for H in (540, 1095):
            run_focus(H, 30, EXT_SPECS, 'depth_ext')
        run_universe(540, 60, EXT_SPECS, 'depth_ext'); run_universe(1095, 90, EXT_SPECS, 'depth_ext')
    elif which == 'paths':
        run_paths(sys.argv[2:])
    else:
        raise SystemExit(__doc__)
