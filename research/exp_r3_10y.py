"""Round 3: 10-year tests on non-Binance long histories (research/data/long).

T1 rolling 10-year windows (start every 90 days) for every series with >= 10 years:
   BTC (Bitstamp 2011-, Bitfinex 2013-, Coinbase 2015-), LTC (Bitfinex 2013-),
   ETH (Bitfinex 2016-03), ETC (Bitfinex 2016-07).
T2 the Bitfinex 2017-10-01 cohort (9 years): every fetched USD pair listed by
   then, dead ones included (delisted -> frozen at last close with a 10% haircut).
Same strategies and principal accounting as exp_r3_long.
"""
import gzip
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

import engine as E
import principal as PR
from exp_r3_long import STRATS

LONG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "long")
DAY = E.DAY_MS


def load(name):
    df = pd.read_csv(os.path.join(LONG, f"{name}.csv.gz"))
    df = df.set_index("day").sort_index()
    full = np.arange(df.index[0], df.index[-1] + 1)
    df = df.reindex(full)
    df["close"] = df["close"].ffill()
    for c in ("open", "high", "low"):
        df[c] = df[c].fillna(df["close"])
    return df


def bars(name, d0, d1, pad_to=None):
    df = load(name)
    df = df.loc[d0:d1 - 1]
    if len(df) < 30:
        return None
    days = df.index.values.astype(np.int64)
    o, h, l, c = (df[x].values.astype(float) for x in ("open", "high", "low", "close"))
    if pad_to and days[-1] < pad_to - 1:
        extra = np.arange(days[-1] + 1, pad_to, dtype=np.int64)
        last = c[-1] * 0.9
        days = np.concatenate([days, extra])
        o, h, l, c = (np.concatenate([x, np.full(len(extra), last)]) for x in (o, h, l, c))
    return E.make_bars(days * DAY, o, h, l, c, name)


def job(args):
    tag, name, d0, d1, pad = args
    b = bars(name, d0, d1, d1 if pad else None)
    if b is None:
        return []
    out = []
    for s, mk in STRATS.items():
        r = E.run_bh(b) if mk is None else E.run_core(b, mk(name))
        st = PR.principal_stats(r, b)
        eq = r["equity"]
        yrs = len(eq) / 365
        st.update(tag=tag, sym=name, d0=d0, strat=s, years=yrs,
                  cagr_B=eq[-1] ** (1 / yrs) - 1 if eq[-1] > 0 else -1,
                  maxdd=float((1 - eq / np.maximum.accumulate(eq)).max()),
                  util=float(np.mean(r["pos_value"] / np.maximum(eq, 1e-12))),
                  bh_ret=b.c[-1] / b.o[0] - 1, eq=eq.astype(np.float32))
        out.append(st)
    return out


TEN = ["bitstamp_BTCUSD", "bitfinex_BTCUSD", "coinbase_BTCUSD", "bitfinex_LTCUSD", "bitfinex_ETHUSD",
       "coinbase_ETHUSD", "bitfinex_ETCUSD", "coinbase_LTCUSD"]
COHORT17 = ["bitfinex_BTCUSD", "bitfinex_LTCUSD", "bitfinex_ETHUSD", "bitfinex_ETCUSD", "bitfinex_XMRUSD",
            "bitfinex_ZECUSD", "bitfinex_DSHUSD", "bitfinex_XRPUSD", "bitfinex_EOSUSD", "bitfinex_IOTUSD",
            "bitfinex_OMGUSD", "bitfinex_SANUSD", "bitfinex_QTMUSD", "bitfinex_ETPUSD", "bitfinex_EDOUSD",
            "bitfinex_AVTUSD", "bitfinex_BTGUSD", "bitfinex_NEOUSD"]


if __name__ == "__main__":
    H = 3650
    jobs = []
    for name in TEN:
        df = load(name)
        d = int(df.index[0]) + 3
        while d + H <= int(df.index[-1]) + 1:
            jobs.append(("H3650", name, d, d + H, False))
            d += 90
        jobs.append(("full", name, int(df.index[0]) + 3, int(df.index[-1]) + 1, False))
    c0 = int(pd.Timestamp("2017-10-01").value // 10**6 // DAY)
    end = int(pd.Timestamp("2026-10-01").value // 10**6 // DAY)
    for name in COHORT17:
        if int(load(name).index[0]) <= c0 - 30:
            jobs.append(("cohort2017-10", name, c0, end, True))
    with ProcessPoolExecutor(2) as ex:
        rows = [x for p in ex.map(job, jobs, chunksize=1) for x in p]
    pd.DataFrame(rows).to_pickle("results/r3_10y.pkl")
    print(len(rows))
