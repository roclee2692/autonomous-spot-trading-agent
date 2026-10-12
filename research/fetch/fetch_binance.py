"""Download Binance public kline data for the spot-strategy research.

Runs on a GitHub Actions runner (the research sandbox cannot reach Binance).
Sources: data.binance.vision monthly/daily zip archives (spot, and USD-M
futures as a fallback for symbols without spot history), plus Hyperliquid's
public candle endpoint for HYPE spot.

Outputs (gzip CSV, prices as %.8g):
  research/data/daily_universe.csv.gz  every USDT spot pair ever listed, 1d
  research/data/h1/<SYMBOL>.csv.gz      1h klines for the focus symbols
  research/data/hype_*.csv.gz           HYPE from futures / Hyperliquid spot
  research/data/manifest.json           what was fetched, row counts, gaps
"""

from __future__ import annotations

import csv
import datetime as dt
import gzip
import io
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
import zipfile
from concurrent.futures import ThreadPoolExecutor

import requests

BUCKET = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
FILES = "https://data.binance.vision"
OUT = os.path.join(os.path.dirname(__file__), "..", "data")

FOCUS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "LINKUSDT", "AAVEUSDT", "TAOUSDT",
    "HYPEUSDT", "NEARUSDT", "ZROUSDT", "PENDLEUSDT", "RNDRUSDT",
    "RENDERUSDT", "UNIUSDT", "ONDOUSDT",
]

STABLE_OR_FIAT = {
    "USDC", "BUSD", "TUSD", "PAX", "USDP", "DAI", "FDUSD", "USDS", "USDSB",
    "EUR", "GBP", "AUD", "TRY", "BRL", "RUB", "UAH", "NGN", "ZAR", "BIDR",
    "IDRT", "BVND", "SUSD", "UST", "USDD", "AEUR", "EURI", "XUSD", "USD1",
    "PAXG", "WBTC", "WBETH", "BFUSD", "RLUSD", "USDE",
}
LEVERAGED = re.compile(r"(UP|DOWN|BULL|BEAR)USDT$")

session = requests.Session()
session.headers["User-Agent"] = "spot-strategy-research/1.0"


def get(url: str, *, ok404: bool = False, tries: int = 6) -> requests.Response | None:
    for attempt in range(tries):
        try:
            r = session.get(url, timeout=60)
            if r.status_code == 404 and ok404:
                return None
            if r.status_code == 200:
                return r
            if r.status_code in (403, 451) and ok404:
                return None
        except requests.RequestException:
            pass
        time.sleep(min(2 ** attempt, 30))
    raise RuntimeError(f"failed: {url}")


def list_prefix(prefix: str) -> tuple[list[str], list[str]]:
    """Return (sub-prefixes, keys) under an S3 prefix."""
    dirs, keys, marker = [], [], ""
    ns = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
    while True:
        url = f"{BUCKET}?delimiter=/&prefix={prefix}"
        if marker:
            url += f"&marker={marker}"
        root = ET.fromstring(get(url).content)
        for cp in root.findall("s3:CommonPrefixes/s3:Prefix", ns):
            dirs.append(cp.text)
        for k in root.findall("s3:Contents/s3:Key", ns):
            keys.append(k.text)
        truncated = root.findtext("s3:IsTruncated", default="false", namespaces=ns) == "true"
        if not truncated:
            break
        marker = root.findtext("s3:NextMarker", default="", namespaces=ns) or (keys[-1] if keys else dirs[-1])
    return dirs, keys


def parse_zip(content: bytes) -> list[list[float]]:
    rows = []
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        for name in zf.namelist():
            with zf.open(name) as fh:
                for rec in csv.reader(io.TextIOWrapper(fh, "utf-8")):
                    if not rec or not rec[0].strip().isdigit():
                        continue  # header row (futures files) or blank
                    t = int(rec[0])
                    if t > 10**14:  # microseconds (spot files from 2025-01-01)
                        t //= 1000
                    rows.append([t, float(rec[1]), float(rec[2]), float(rec[3]),
                                 float(rec[4]), float(rec[5]), float(rec[7])])
    return rows


def fetch_symbol(market: str, symbol: str, interval: str, daily_tail: bool) -> list[list[float]]:
    base = "data/spot" if market == "spot" else "data/futures/um"
    _, keys = list_prefix(f"{base}/monthly/klines/{symbol}/{interval}/")
    zips = sorted(k for k in keys if k.endswith(".zip"))
    rows: list[list[float]] = []
    last_month = None
    for k in zips:
        r = get(f"{FILES}/{k}", ok404=True)
        if r is not None:
            rows.extend(parse_zip(r.content))
            last_month = k[-11:-4]  # YYYY-MM
    if daily_tail:
        # current partial month(s) from daily archives
        today = dt.date.today()
        start = dt.date(today.year, today.month, 1)
        if last_month:
            y, m = map(int, last_month.split("-"))
            nm = dt.date(y + (m == 12), (m % 12) + 1, 1)
            start = min(start, nm)
        d = start
        while d < today:
            k = f"{base}/daily/klines/{symbol}/{interval}/{symbol}-{interval}-{d.isoformat()}.zip"
            r = get(f"{FILES}/{k}", ok404=True)
            if r is not None:
                rows.extend(parse_zip(r.content))
            d += dt.timedelta(days=1)
    dedup = {r[0]: r for r in rows}
    return [dedup[t] for t in sorted(dedup)]


def write_rows(path: str, header: list[str], rows: list[list]) -> None:
    with gzip.open(path, "wt", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows:
            w.writerow([r[0]] + [f"{x:.8g}" if isinstance(x, float) else x for x in r[1:]])


def hyperliquid_hype(interval: str) -> list[list[float]]:
    url = "https://api.hyperliquid.xyz/info"
    meta = session.post(url, json={"type": "spotMeta"}, timeout=60).json()
    hype = next(t["index"] for t in meta["tokens"] if t["name"] == "HYPE")
    usdc = next(t["index"] for t in meta["tokens"] if t["name"] == "USDC")
    pair = next(u["name"] for u in meta["universe"] if u["tokens"] == [hype, usdc])
    out: dict[int, list[float]] = {}
    end = int(time.time() * 1000)
    start = int(dt.datetime(2024, 11, 29, tzinfo=dt.timezone.utc).timestamp() * 1000)
    step = {"1d": 86_400_000, "1h": 3_600_000}[interval] * 4000
    s = start
    while s < end:
        req = {"type": "candleSnapshot", "req": {"coin": pair, "interval": interval,
                                                 "startTime": s, "endTime": min(s + step, end)}}
        data = session.post(url, json=req, timeout=60).json()
        for c in data:
            out[int(c["t"])] = [int(c["t"]), float(c["o"]), float(c["h"]), float(c["l"]),
                                float(c["c"]), float(c["v"]), float(c["v"]) * float(c["c"])]
        s += step
        time.sleep(0.5)
    return [out[t] for t in sorted(out)]


def main() -> int:
    os.makedirs(os.path.join(OUT, "h1"), exist_ok=True)
    manifest: dict = {"generated_utc": dt.datetime.utcnow().isoformat(timespec="seconds"),
                      "source": "data.binance.vision (+ api.hyperliquid.xyz for HYPE spot)",
                      "daily": {}, "h1": {}, "notes": []}

    dirs, _ = list_prefix("data/spot/monthly/klines/")
    symbols = sorted(d.rstrip("/").split("/")[-1] for d in dirs)
    usdt = [s for s in symbols if s.endswith("USDT") and not LEVERAGED.search(s)
            and s[:-4] not in STABLE_OR_FIAT]
    print(f"{len(symbols)} spot symbols listed, {len(usdt)} USDT pairs kept", flush=True)

    header = ["open_time_ms", "open", "high", "low", "close", "volume", "quote_volume"]

    def daily_job(sym: str):
        try:
            return sym, fetch_symbol("spot", sym, "1d", daily_tail=sym in FOCUS), None
        except Exception as exc:  # noqa: BLE001
            return sym, [], str(exc)

    universe_rows = []
    with ThreadPoolExecutor(max_workers=24) as pool:
        for i, (sym, rows, err) in enumerate(pool.map(daily_job, usdt)):
            if err:
                manifest["notes"].append(f"daily {sym}: {err}")
            if rows:
                manifest["daily"][sym] = {"rows": len(rows), "first": rows[0][0], "last": rows[-1][0]}
                universe_rows.extend([sym] + r for r in rows)
            if i % 50 == 0:
                print(f"daily {i}/{len(usdt)}", flush=True)

    with gzip.open(os.path.join(OUT, "daily_universe.csv.gz"), "wt", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["symbol"] + header)
        for r in universe_rows:
            w.writerow([r[0], r[1]] + [f"{x:.8g}" for x in r[2:]])
    print(f"daily universe rows: {len(universe_rows)}", flush=True)

    def h1_job(sym: str):
        try:
            return sym, fetch_symbol("spot", sym, "1h", daily_tail=True), None
        except Exception as exc:  # noqa: BLE001
            return sym, [], str(exc)

    with ThreadPoolExecutor(max_workers=8) as pool:
        for sym, rows, err in pool.map(h1_job, FOCUS):
            if err:
                manifest["notes"].append(f"h1 {sym}: {err}")
            if rows:
                write_rows(os.path.join(OUT, "h1", f"{sym}.csv.gz"), header, rows)
                manifest["h1"][sym] = {"rows": len(rows), "first": rows[0][0], "last": rows[-1][0]}
            print(f"h1 {sym}: {len(rows)} rows", flush=True)

    # HYPE: USD-M perpetual (Binance) and Hyperliquid spot as independent sources.
    for interval in ("1d", "1h"):
        try:
            rows = fetch_symbol("futures", "HYPEUSDT", interval, daily_tail=True)
            write_rows(os.path.join(OUT, f"hype_binance_perp_{interval}.csv.gz"), header, rows)
            manifest[f"hype_binance_perp_{interval}"] = len(rows)
        except Exception as exc:  # noqa: BLE001
            manifest["notes"].append(f"HYPE perp {interval}: {exc}")
        try:
            rows = hyperliquid_hype(interval)
            write_rows(os.path.join(OUT, f"hype_hyperliquid_spot_{interval}.csv.gz"), header, rows)
            manifest[f"hype_hyperliquid_spot_{interval}"] = len(rows)
        except Exception as exc:  # noqa: BLE001
            manifest["notes"].append(f"HYPE hyperliquid {interval}: {exc}")

    with open(os.path.join(OUT, "manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
    print(json.dumps(manifest["notes"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
