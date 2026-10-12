"""Experiment harness: rolling-window evaluation on focus coins and on a
point-in-time (survivorship-free) liquid-altcoin universe."""

from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache

import numpy as np
import pandas as pd

import engine as E
import lab

RESULTS = os.path.join(lab.HERE, "results")
os.makedirs(RESULTS, exist_ok=True)

LISTING_SKIP_DAYS = 3          # ignore listing-day prints
IS_END_DAY = int(pd.Timestamp("2024-01-01").value // 10**6 // E.DAY_MS)   # in-sample < 2024


# --------------------------------------------------------------------------
# strategies are described by small tuples so they can be pickled
# --------------------------------------------------------------------------
def run_strategy(bars: E.Bars, spec: tuple) -> dict:
    kind = spec[0]
    if kind == "core":
        return E.run_core(bars, spec[1], spec[2] if len(spec) > 2 else None)
    if kind == "sat":
        return E.run_sat(bars, spec[1])
    if kind == "bh":
        return E.run_bh(bars)
    if kind == "mix":                       # static u in coin, rest cash
        u = spec[1]
        r = E.run_bh(bars)
        r = dict(r)
        r["equity"] = 1 - u + u * r["equity"]
        r["pos_value"] = r["equity"] - (1 - u)
        r["pos_cost"] = np.full(len(r["equity"]), u)
        return r
    if kind == "cash":
        idx = np.where(bars.day_end)[0]
        n = len(idx)
        return {"days": (bars.t[idx] // E.DAY_MS).astype(int), "equity": np.ones(n),
                "pos_value": np.zeros(n), "pos_cost": np.zeros(n), "n_buys": 0,
                "n_sells": 0, "fees": 0.0}
    raise ValueError(kind)


def _bars(coin: str, interval: str) -> E.Bars:
    b = lab.coin_bars(coin, interval)
    days = b.t // E.DAY_MS
    return lab.slice_days(b, int(days[0]) + LISTING_SKIP_DAYS, int(days[-1]) + 1)


def window_runs(coin: str, spec: tuple, horizon: int, step: int = 30,
                interval: str = "1h", d_from: int | None = None,
                d_to: int | None = None) -> pd.DataFrame:
    b = _bars(coin, interval)
    if d_from is not None or d_to is not None:
        days = b.t // E.DAY_MS
        b = lab.slice_days(b, d_from or int(days[0]), d_to or int(days[-1]) + 1)
    df = lab.rolling(b, lambda x: run_strategy(x, spec), horizon, step)
    df["coin"] = coin
    return df


def _job(args):
    coin, name, spec, horizon, step, interval, d_from, d_to = args
    try:
        df = window_runs(coin, spec, horizon, step, interval, d_from, d_to)
    except Exception as exc:  # noqa: BLE001
        print("ERR", coin, name, exc)
        return pd.DataFrame()
    df["variant"] = name
    return df


def grid(coins, variants: dict, horizon=540, step=30, interval="1h",
         d_from=None, d_to=None, workers=4) -> pd.DataFrame:
    """variants: name -> spec or name -> callable(coin)->spec."""
    jobs = []
    for coin in coins:
        iv = "1d" if (coin == "HYPE" and interval == "1h") else interval
        for name, spec in variants.items():
            sp = spec(coin) if callable(spec) else spec
            jobs.append((coin, name, sp, horizon, step, iv, d_from, d_to))
    with ProcessPoolExecutor(workers) as ex:
        parts = list(ex.map(_job, jobs, chunksize=1))
    parts = [p for p in parts if len(p)]
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def table(df: pd.DataFrame, by=("variant",), coin_equal=True) -> pd.DataFrame:
    """Summaries; with coin_equal each coin gets equal weight in pooled rows."""
    rows = []
    for key, g in df.groupby(list(by)):
        if coin_equal and "coin" in g:
            per = [lab.summarize(x) for _, x in g.groupby("coin")]
            s = {k: np.mean([p[k] for p in per]) for k in per[0]} if per else {}
            s["n"] = len(g)
            # tails over pooled windows (each coin equally weighted by resampling)
            w = g.groupby("coin")["ret"].transform(lambda x: 1.0 / len(x))
            s["p10"] = _wq(g["ret"].values, w.values, 0.10)
            s["p05"] = _wq(g["ret"].values, w.values, 0.05)
        else:
            s = lab.summarize(g)
        key = key if isinstance(key, tuple) else (key,)
        rows.append(dict(zip(by, key), **s))
    return pd.DataFrame(rows)


def _wq(x, w, q):
    o = np.argsort(x)
    x, w = x[o], w[o]
    cw = np.cumsum(w) / w.sum()
    return float(x[np.searchsorted(cw, q)])


# --------------------------------------------------------------------------
# point-in-time universe (survivorship-free)
# --------------------------------------------------------------------------
@lru_cache(maxsize=None)
def universe_panel():
    u = lab.universe_daily()
    u = u[~u["symbol"].isin(["BTCUSDT", "ETHUSDT"])]
    piv = {}
    for col in ("open", "high", "low", "close", "quote_volume"):
        piv[col] = u.pivot(index="day", columns="symbol", values=col).sort_index()
    return piv


def pit_universe(day: int, top: int = 30, min_age: int = 180, liq_days: int = 90) -> list[str]:
    """Top `top` USDT pairs by trailing quote volume, using only data <= day."""
    piv = universe_panel()
    qv = piv["quote_volume"]
    hist = qv.loc[:day - 1]
    if len(hist) < liq_days:
        return []
    recent = hist.iloc[-liq_days:].mean()
    age = hist.notna().sum()
    alive = hist.iloc[-1].notna()
    ok = recent[(age >= min_age) & alive].sort_values(ascending=False)
    return list(ok.index[:top])


def symbol_bars(sym: str, d0: int, d1: int, pad: bool = True) -> E.Bars | None:
    piv = universe_panel()
    sl = slice(d0, d1 - 1)
    o = piv["open"][sym].loc[sl]
    o = o.dropna()
    if len(o) < 5:
        return None
    idx = o.index
    h = piv["high"][sym].loc[idx]
    lo = piv["low"][sym].loc[idx]
    c = piv["close"][sym].loc[idx]
    days = np.asarray(idx, dtype=np.int64)
    if pad and days[-1] < d1 - 1:
        # delisted inside the window: freeze at the last close (flat bars)
        extra = np.arange(days[-1] + 1, d1, dtype=np.int64)
        last = float(c.iloc[-1]) * 0.9   # 10% haircut for delisting exit
        days = np.concatenate([days, extra])
        o = np.concatenate([o.values, np.full(len(extra), last)])
        h = np.concatenate([h.values, np.full(len(extra), last)])
        lo = np.concatenate([lo.values, np.full(len(extra), last)])
        c = np.concatenate([c.values, np.full(len(extra), last)])
    else:
        o, h, lo, c = o.values, h.values, lo.values, c.values
    return E.make_bars(days * E.DAY_MS, o, h, lo, c, sym)


def _ujob(args):
    sym, d0, horizon, specs = args
    b = symbol_bars(sym, d0, d0 + horizon)
    if b is None:
        return []
    out = []
    for name, spec in specs.items():
        r = run_strategy(b, spec)
        m = lab.metrics(r, years_override=horizon / 365)
        m.update(symbol=sym, start_day=d0, variant=name)
        m["bh_ret"] = b.c[-1] / b.o[0] - 1
        m["alpha"] = np.log1p(max(m["ret"], -0.99)) - np.log1p(max(m["util"] * m["bh_ret"], -0.99))
        out.append(m)
    return out


def universe_grid(specs: dict, horizon=540, step=60, top=30, start="2019-01-01",
                  end_day=None, workers=4) -> pd.DataFrame:
    d = int(pd.Timestamp(start).value // 10**6 // E.DAY_MS)
    last = int(universe_panel()["close"].index.max())
    end_day = end_day or last - horizon
    jobs = []
    while d <= end_day:
        for sym in pit_universe(d, top):
            jobs.append((sym, d, horizon, specs))
        d += step
    with ProcessPoolExecutor(workers) as ex:
        parts = list(ex.map(_ujob, jobs, chunksize=4))
    rows = [m for p in parts for m in p]
    return pd.DataFrame(rows)


def utable(df: pd.DataFrame) -> pd.DataFrame:
    """Summaries for universe runs: each start date weighted equally."""
    rows = []
    for v, g in df.groupby("variant"):
        s = lab.summarize(g)
        per_start = g.groupby("start_day")["ret"].mean()
        s["basket_med"] = per_start.median()
        s["basket_p10"] = per_start.quantile(0.10)
        s["basket_mean"] = per_start.mean()
        s["variant"] = v
        rows.append(s)
    return pd.DataFrame(rows).set_index("variant")


def save(df: pd.DataFrame, name: str) -> str:
    path = os.path.join(RESULTS, name)
    df.to_csv(path, index=False)
    return path


# --------------------------------------------------------------------------
# price-only "slow death" / market filters (computed from data <= that day)
# --------------------------------------------------------------------------
@lru_cache(maxsize=None)
def btc_close() -> pd.Series:
    u = lab.universe_daily()
    b = u[u["symbol"] == "BTCUSDT"].set_index("day")["close"]
    return b


@lru_cache(maxsize=4096)
def halt_days(sym: str, rule: str) -> frozenset:
    piv = universe_panel()
    if sym in piv["close"].columns:
        c = piv["close"][sym].dropna()
    else:  # focus coin by short name (HYPE from Hyperliquid, RENDER stitched)
        c = lab.coin_frame(sym, "1d")
        c = pd.Series(c["close"].values, index=(c["open_time_ms"] // E.DAY_MS).astype(int).values)
    btc = btc_close().reindex(c.index).ffill()
    ratio = c / btc
    if rule == "relweak":          # coin/BTC -50% over 365d and coin below its 200d MA
        sig = (ratio / ratio.shift(365) - 1 < -0.5) & (c < c.rolling(200).mean())
    elif rule == "relweak2":       # persistent: coin/BTC down >30% in each of the last two 180d blocks
        r1 = ratio / ratio.shift(180) - 1
        r2 = ratio.shift(180) / ratio.shift(360) - 1
        sig = (r1 < -0.3) & (r2 < -0.3)
    elif rule == "idio_low":       # new 365d low in last 30d while BTC >25% above its 365d low
        low365 = c.rolling(365, min_periods=200).min()
        made_low = (c <= low365 * 1.0001).rolling(30).max() > 0
        sig = made_low & (btc > btc.rolling(365, min_periods=200).min() * 1.25)
    elif rule == "deep85":         # >85% below 2y high
        sig = c < c.rolling(730, min_periods=200).max() * 0.15
    elif rule == "btc_bear":       # BTC below its 200d MA (market filter)
        sig = btc < btc.rolling(200).mean()
    elif rule == "btc_crash":      # BTC >35% below its 365d high
        sig = btc < btc.rolling(365, min_periods=100).max() * 0.65
    else:
        raise ValueError(rule)
    return frozenset(int(d) for d in sig[sig.fillna(False)].index)


def _run_halt(bars: E.Bars, params: E.CoreParams, rule: str, mode: str) -> dict:
    days = halt_days(bars.name, rule)
    key = "halt_days" if mode == "halt" else "pause_days"
    return E.run_core(bars, params, {key: days})


_orig_run_strategy = run_strategy


def run_strategy(bars: E.Bars, spec: tuple) -> dict:  # noqa: F811
    if spec[0] == "core_halt":
        return _run_halt(bars, spec[1], spec[2], spec[3] if len(spec) > 3 else "halt")
    return _orig_run_strategy(bars, spec)
