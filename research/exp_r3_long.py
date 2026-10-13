"""Round 3: long horizons and returns on principal.

L1 cohorts: every coin in the point-in-time top-30 (liquidity, age >= 180 d,
   delisted coins kept with a 10% exit haircut) at a start date, plus BTC and
   ETH, run from that date to the end of the data (5.75 - 8.25 years).
L2 rolling 5-year and 7-year windows (start every 90 days) on the same universe.
Every run is reported on the whole budget (ret_B) and on the principal actually
used (ret_P, shadow buy-and-hold, IRR) - see principal.py.
"""
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

import engine as E
import lab
import principal as PR
import runner as R
from exp_final import V3P, V31P

pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 400)
DAY = E.DAY_MS


def v2p(sym):
    return E.CoreParams(d=E.V2_CORE.get(sym.replace("USDT", ""), (0.07, 0.17, 0.29)), max_gens=3, spike_frac=0.075)


def v2ext(sym):
    """the other report's convention: fixed $200 per generation, 6 gens, no gap, $1,700 per coin,
    TP1 50% / TP2 25% / permanent 25% tail, $50 spike."""
    return E.CoreParams(d=E.V2_CORE.get(sym.replace("USDT", ""), (0.07, 0.17, 0.29)), w=(0.40, 0.35, 0.25),
                        tp1=0.25, tp1_frac=0.5, tp2=0.5, tp2_frac=0.25, tail_exit=("none",), max_gens=6,
                        gen_gap=0.0, fixed_g=200 / 1700, spike_frac=50 / 1700, drift=0.20, tp2_reanchor=True)


STRATS = {
    "V3.2": lambda s: V31P(tp1_frac=0.90, tail_exit=("target", 4.0)),
    "V3.1": lambda s: V31P(),
    "V3.0": lambda s: V3P(),
    "V2": v2p,
    "V2ext": v2ext,
    "V3.1 tail3x": lambda s: V31P(tail_exit=("target", 2.0)),
    "V3.1 tail5x": lambda s: V31P(tail_exit=("target", 4.0)),
    "V3.1 tailPerm": lambda s: V31P(tail_exit=("none",)),
    "V3.1 tp50": lambda s: V31P(tp1_frac=0.5),
    "V3.1 fixedG": lambda s: V31P(fixed_g=(1 - 0.075) / 3),
    "bh": None,
}
TAILS = {f"tail{m}x": (lambda m: (lambda s: V31P(tail_exit=("target", m - 1.0))))(m) for m in (2, 3, 4, 5, 7, 10, 20)}
TAILS.update({"tailPerm": lambda s: V31P(tail_exit=("none",)), "bh": None,
              "tail5x share35": lambda s: V31P(tail_exit=("target", 4.0), tp1_frac=0.65),
              "tail5x share15": lambda s: V31P(tail_exit=("target", 4.0), tp1_frac=0.85),
              "tail3x share35": lambda s: V31P(tail_exit=("target", 2.0), tp1_frac=0.65)})
GRID2 = {"bh": None}
for _share in (0.10, 0.15, 0.20, 0.25):
    for _m in (2, 3, 4, 5, 7, 10):
        GRID2[f"s{int(_share*100)}x{_m}"] = (lambda sh, m: (lambda s: V31P(tail_exit=("target", m - 1.0), tp1_frac=1 - sh)))(_share, _m)
GRID2["s0"] = lambda s: V31P(tp1_frac=1.0)
SETS = {"main": STRATS, "tail": TAILS, "grid2": GRID2}
MAJORS = ["BTC", "ETH"]


def end_day():
    return int(R.universe_panel()["close"].index.max())


def bars_for(sym, d0, d1):
    if sym in MAJORS:
        b = lab.coin_bars(sym, "1d")
        days = b.t // DAY
        if days[0] > d0:
            return None
        return lab.slice_days(b, d0, d1)
    return R.symbol_bars(sym, d0, d1)


def job(args):
    tag, sym, d0, d1 = args[:4]
    strats = SETS[args[4]] if len(args) > 4 else STRATS
    b = bars_for(sym, d0, d1)
    if b is None or len(b) < 30:
        return []
    out = []
    for name, mk in strats.items():
        r = E.run_bh(b) if mk is None else E.run_core(b, mk(sym))
        st = PR.principal_stats(r, b)
        eq = r["equity"]
        yrs = len(eq) / 365
        st.update(tag=tag, sym=sym, d0=d0, strat=name, years=yrs,
                  cagr_B=eq[-1] ** (1 / yrs) - 1 if eq[-1] > 0 else -1,
                  maxdd=float((1 - eq / np.maximum.accumulate(eq)).max()),
                  util=float(np.mean(r["pos_value"] / np.maximum(eq, 1e-12))),
                  bh_ret=b.c[-1] / b.o[0] - 1, eq=eq.astype(np.float32))
        out.append(st)
    return out


def run_jobs(jobs, workers=4):
    with ProcessPoolExecutor(workers) as ex:
        return pd.DataFrame([x for p in ex.map(job, jobs, chunksize=2) for x in p])


def cohort_jobs(starts):
    e = end_day() + 1
    jobs = []
    for s in starts:
        d0 = int(pd.Timestamp(s).value // 10**6 // DAY)
        for sym in R.pit_universe(d0, 30) + MAJORS:
            jobs.append((s, sym, d0, e))
    return jobs


def window_jobs(H, step=90, start="2018-07-01", sset="main"):
    d = int(pd.Timestamp(start).value // 10**6 // DAY)
    last = end_day() - H
    jobs = []
    while d <= last:
        for sym in R.pit_universe(d, 30) + MAJORS:
            jobs.append((f"H{H}", sym, d, d + H, sset))
        d += step
    return jobs


def basket(g):
    """equal budget per coin within one start date."""
    H = max(len(e) for e in g["eq"])
    eqs = np.vstack([np.pad(e, (0, H - len(e)), mode="edge") for e in g["eq"]])
    eq = eqs.mean(0)
    profit = g.ret_B.sum()
    P = g.P.sum()
    shadow_final = ((1 + g.shadow_ret) * g.P).sum()
    return pd.Series({
        "n": len(g), "ret_B": eq[-1] - 1, "med_B": g.ret_B.median(),
        "lr_B": np.log1p(g.ret_B.clip(lower=-0.99)).mean(),
        "maxdd": (1 - eq / np.maximum.accumulate(eq)).max(),
        "P": g.P.mean(), "ret_P": profit / P if P > 0 else 0.0,
        "shadow_P": shadow_final / P - 1 if P > 0 else 0.0,
        "irr_med": g.irr.median(), "util": g.util.mean()})


def report(df, label):
    print(f"\n######## {label}")
    alts = df[~df.sym.isin(MAJORS)]
    bk = alts.groupby(["tag", "d0", "strat"]).apply(basket, include_groups=False).reset_index()
    bh = df[df.strat == "bh"].set_index(["tag", "d0", "sym"]).ret_B
    df = df.join(bh.rename("bh_B"), on=["tag", "d0", "sym"])
    df["beat_bh_B"] = df.ret_B > df.bh_B
    df["beat_bh_P"] = df.ret_P > df.bh_B
    df["beat_shadow"] = df.edge_vs_shadow > 0
    return bk, df


if __name__ == "__main__":
    part = sys.argv[1]
    if part == "cohort":
        jobs = cohort_jobs(["2018-07-01", "2019-01-01", "2019-07-01", "2020-01-01", "2020-07-01", "2021-01-01"])
        df = run_jobs(jobs)
        df.to_pickle("results/r3_cohort.pkl")
    elif part.startswith("tail"):
        for H, step in [(540, 60), (1095, 90), (1825, 90), (2555, 90)]:
            df = run_jobs(window_jobs(H, step, "2019-01-01" if H < 1825 else "2018-07-01", "tail"))
            df.drop(columns=["eq"]).to_pickle(f"results/r3_tail_{H}.pkl")
            bk = df[~df.sym.isin(MAJORS)].groupby(["d0", "strat"]).apply(basket, include_groups=False).reset_index()
            bk.to_pickle(f"results/r3_tailbk_{H}.pkl")
            print(H, len(df), flush=True)
    elif part == "grid2":
        for H, step in [(540, 60), (1095, 90), (1825, 90), (2555, 90)]:
            df = run_jobs(window_jobs(H, step, "2019-01-01" if H < 1825 else "2018-07-01", "grid2"))
            df.drop(columns=["eq"]).to_pickle(f"results/r3_g2_{H}.pkl")
            bk = df[~df.sym.isin(MAJORS)].groupby(["d0", "strat"]).apply(basket, include_groups=False).reset_index()
            bk.to_pickle(f"results/r3_g2bk_{H}.pkl")
            print(H, len(df), flush=True)
    elif part.startswith("H"):
        H = int(part[1:])
        df = run_jobs(window_jobs(H))
        df.to_pickle(f"results/r3_win_{H}.pkl")
