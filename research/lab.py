"""Data loading, rolling-window evaluation and metrics for the research."""

from __future__ import annotations

import gzip
import json
import os
from functools import lru_cache

import numpy as np
import pandas as pd

import engine as E

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
DAY_MS = E.DAY_MS

CORE = ["TAO", "AAVE", "HYPE", "LINK"]
SAT = ["NEAR", "ZRO", "PENDLE", "RENDER"]
EXTRA = ["UNI", "ONDO", "SOL", "ETH", "BTC"]


# --------------------------------------------------------------------------
# loading
# --------------------------------------------------------------------------
def _read(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.drop_duplicates("open_time_ms").sort_values("open_time_ms")
    return df.reset_index(drop=True)


@lru_cache(maxsize=None)
def universe_daily() -> pd.DataFrame:
    """All USDT spot pairs, daily. Redenominations (token splits/swaps that
    show up as a >5x price jump across a short trading halt) are back-adjusted;
    a symbol reused for a different asset after a long halt (LUNA 2022, VEN
    2018) is split into SYMBOL and SYMBOL_2 so the old asset dies properly."""
    df = pd.read_csv(os.path.join(DATA, "daily_universe.csv.gz"))
    df["day"] = (df["open_time_ms"] // DAY_MS).astype(int)
    df = df.sort_values(["symbol", "day"]).reset_index(drop=True)
    parts = []
    for sym, g in df.groupby("symbol", sort=False):
        g = g.copy()
        d, c, o = g["day"].values, g["close"].values, g["open"].values
        jumps = np.where((np.diff(d) > 1) & ((o[1:] / c[:-1] > 5) | (o[1:] / c[:-1] < 0.2)))[0]
        for j in jumps[::-1]:
            ratio = o[j + 1] / c[j]
            if d[j + 1] - d[j] <= 10:
                cols = ["open", "high", "low", "close"]
                g.iloc[: j + 1, [g.columns.get_loc(x) for x in cols]] *= ratio
            else:
                g.iloc[j + 1:, g.columns.get_loc("symbol")] = sym + "_2"
        parts.append(g)
    return pd.concat(parts, ignore_index=True)


def _stitch(frames: list[pd.DataFrame]) -> pd.DataFrame:
    out = []
    last = -1
    for f in frames:
        f = f[f["open_time_ms"] > last]
        if len(f):
            out.append(f)
            last = int(f["open_time_ms"].iloc[-1])
    return pd.concat(out, ignore_index=True)


def coin_frame(coin: str, interval: str = "1h") -> pd.DataFrame:
    """OHLC frame for a research coin. RENDER = RNDR (pre-migration, 1:1) +
    RENDER. HYPE = Binance spot if it exists, else Hyperliquid spot."""
    if interval == "1h":
        def load(sym):
            p = os.path.join(DATA, "h1", f"{sym}USDT.csv.gz")
            return _read(p) if os.path.exists(p) else None
    else:
        u = universe_daily()

        def load(sym):
            f = u[u["symbol"] == f"{sym}USDT"]
            return f.drop(columns=["symbol", "day"]).reset_index(drop=True) if len(f) else None
    if coin == "RENDER":
        parts = [x for x in (load("RNDR"), load("RENDER")) if x is not None]
        return _stitch(parts)
    if coin == "HYPE":
        # Binance spot only listed HYPE on 2026-09-24. Daily: Hyperliquid spot
        # (HYPE/USDC, from 2024-11-29). Hourly: Binance USD-M perp (from
        # 2025-05-30), the longest hourly series available.
        if interval == "1h":
            return _read(os.path.join(DATA, "hype_binance_perp_1h.csv.gz"))
        return _read(os.path.join(DATA, "hype_hyperliquid_spot_1d.csv.gz"))
    f = load(coin)
    if f is None:
        raise KeyError(coin)
    return f


def to_bars(df: pd.DataFrame, name: str = "") -> E.Bars:
    return E.make_bars(df["open_time_ms"].values, df["open"].values, df["high"].values,
                       df["low"].values, df["close"].values, name)


@lru_cache(maxsize=None)
def coin_bars(coin: str, interval: str = "1h") -> E.Bars:
    return to_bars(coin_frame(coin, interval), coin)


def slice_days(b: E.Bars, d0: int, d1: int) -> E.Bars:
    days = b.t // DAY_MS
    i0 = int(np.searchsorted(days, d0, "left"))
    i1 = int(np.searchsorted(days, d1, "left"))
    return b.slice(i0, i1)


# --------------------------------------------------------------------------
# metrics
# --------------------------------------------------------------------------
def spells(mask: np.ndarray) -> list[int]:
    out, run = [], 0
    for m in mask:
        if m:
            run += 1
        elif run:
            out.append(run)
            run = 0
    if run:
        out.append(run)
    return out


def metrics(r: dict, years_override: float | None = None) -> dict:
    eq = r["equity"]
    n = len(eq)
    years = years_override or max(n / 365.0, 1e-9)
    peak = np.maximum.accumulate(eq)
    dd = 1 - eq / peak
    under_principal = eq < 1.0
    pos_v, pos_c = r["pos_value"], r["pos_cost"]
    held = pos_c > 1e-9
    pos_ret = np.where(held, pos_v / np.maximum(pos_c, 1e-12) - 1, 0.0)
    cyc = r.get("cyc_pnl", pos_ret)
    sp = spells(dd > 0.0001)
    return {
        "ret": eq[-1] - 1,
        "cagr": eq[-1] ** (1 / years) - 1 if eq[-1] > 0 else -1.0,
        "maxdd": dd.max(),
        "worst_vs_principal": eq.min() - 1,
        "deep20": float((cyc < -0.20).any()),
        "deep30": float((cyc < -0.30).any()),
        "days_deep20": float((cyc < -0.20).mean()),
        "under_avg": float(np.mean(sp)) if sp else 0.0,
        "under_max": float(max(sp)) if sp else 0.0,
        "util": float(np.mean(pos_v / np.maximum(eq, 1e-12))),
        "trades": r["n_buys"] + r["n_sells"],
        "trades_py": (r["n_buys"] + r["n_sells"]) / years,
        "cycles_py": r.get("tp1_count", r.get("cycles", 0)) / years,
        "fees": r["fees"],
    }


def rolling(bars: E.Bars, fn, horizon_days: int, step_days: int = 30,
            warmup_days: int = 0) -> pd.DataFrame:
    """Run fn(bars_slice) on windows [s, s+horizon) every step_days."""
    days = bars.t // DAY_MS
    d_first, d_last = int(days[0]) + warmup_days, int(days[-1])
    rows = []
    s = d_first
    while s + horizon_days <= d_last + 1:
        b = slice_days(bars, s, s + horizon_days)
        if len(b) > 10:
            r = fn(b)
            m = metrics(r)
            m["start_day"] = s
            m["bh_ret"] = b.c[-1] / b.o[0] - 1
            m["alpha"] = np.log1p(max(m["ret"], -0.99)) - np.log1p(max(m["util"] * m["bh_ret"], -0.99))
            rows.append(m)
        s += step_days
    return pd.DataFrame(rows)


def summarize(df: pd.DataFrame) -> dict:
    if df.empty:
        return {}
    return {
        "n": len(df),
        "ret_med": df["ret"].median(),
        "ret_mean": df["ret"].mean(),
        "cagr_med": df["cagr"].median(),
        "p10": df["ret"].quantile(0.10),
        "p05": df["ret"].quantile(0.05),
        "maxdd_med": df["maxdd"].median(),
        "maxdd_p90": df["maxdd"].quantile(0.90),
        "deep20": df["deep20"].mean(),
        "deep30": df["deep30"].mean(),
        "under_avg": df["under_avg"].mean(),
        "under_max": df["under_max"].max(),
        "util": df["util"].mean(),
        "trades_py": df["trades_py"].mean(),
        "logret": np.log1p(df["ret"].clip(lower=-0.99)).mean(),
        "alpha": df["alpha"].mean() if "alpha" in df else np.nan,
        "cycles_py": df["cycles_py"].mean(),
        "fees": df["fees"].mean(),
    }


def fmt(d: dict, keys=None) -> str:
    keys = keys or list(d)
    out = []
    for k in keys:
        v = d.get(k)
        if isinstance(v, float):
            if k in ("n", "trades_py", "cycles_py", "under_avg", "under_max"):
                out.append(f"{k}={v:.1f}")
            else:
                out.append(f"{k}={v:+.3f}" if k in ("ret_med", "ret_mean", "p10", "p05", "cagr_med") else f"{k}={v:.3f}")
        else:
            out.append(f"{k}={v}")
    return " ".join(out)
