"""Download long (up to 15-year) daily OHLC histories from non-Binance venues.

Runs on a GitHub Actions runner (the research sandbox cannot reach exchanges).
Binance spot only starts in 2017-08, so for 10-year tests we need older venues:

  bitstamp   BTC/USD since 2011-08, plus ETH/LTC/XRP/BCH (single-exchange OHLC)
  bitfinex   BTC/LTC since 2013, ETH/ETC/XMR/ZEC/DASH/XRP/EOS/IOTA/NEO since 2016-17
  coinbase   BTC-USD since 2015-07, ETH-USD 2016-05, LTC-USD 2016-08 (cross-check)
  cryptocompare  aggregated index for a broad list of coins that existed in
                 2014-2017, dead ones included, so a 2015/2016 cohort can be
                 formed by contemporaneous volume without survivorship bias.
                 Best-effort: the endpoint may refuse keyless calls.

Output: research/data/long/<source>_<SYM>.csv.gz with day,open,high,low,close,volume_usd
and research/data/long/manifest.json. Every source is best-effort; failures are
recorded in the manifest instead of aborting the run.
"""

from __future__ import annotations

import csv
import datetime as dt
import gzip
import json
import os
import time

import requests

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "long")
DAY = 86400
session = requests.Session()
session.headers["User-Agent"] = "spot-strategy-research/1.0"
manifest: dict = {"generated": dt.datetime.utcnow().isoformat() + "Z", "series": {}, "errors": {}}


def get_json(url: str, params: dict | None = None, tries: int = 5):
    last = None
    for attempt in range(tries):
        try:
            r = session.get(url, params=params, timeout=60)
            if r.status_code == 200:
                return r.json()
            last = f"HTTP {r.status_code}: {r.text[:200]}"
            if r.status_code in (400, 404):
                break
        except requests.RequestException as exc:  # noqa: PERF203
            last = repr(exc)
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(last)


def save(source: str, sym: str, rows: dict) -> None:
    """rows: {day: (o,h,l,c,vol_usd)}; drops zero/invalid rows."""
    clean = {d: v for d, v in rows.items() if all(x is not None for x in v[:4]) and min(v[:4]) > 0}
    if not clean:
        manifest["errors"][f"{source}_{sym}"] = "no valid rows"
        return
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f"{source}_{sym}.csv.gz")
    with gzip.open(path, "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(["day", "open", "high", "low", "close", "volume_usd"])
        for d in sorted(clean):
            o, h, l, c, v = clean[d]
            w.writerow([d, "%.8g" % o, "%.8g" % max(h, o, c), "%.8g" % min(l, o, c), "%.8g" % c, "%.6g" % (v or 0)])
    days = sorted(clean)
    manifest["series"][f"{source}_{sym}"] = {
        "rows": len(days), "first": str(dt.date(1970, 1, 1) + dt.timedelta(days=days[0])),
        "last": str(dt.date(1970, 1, 1) + dt.timedelta(days=days[-1])),
        "gaps_gt3d": sum(1 for a, b in zip(days, days[1:]) if b - a > 3)}
    print(source, sym, manifest["series"][f"{source}_{sym}"], flush=True)


def bitstamp(pair: str, start: str) -> None:
    rows: dict = {}
    t = int(dt.datetime.fromisoformat(start).replace(tzinfo=dt.timezone.utc).timestamp())
    now = int(time.time())
    while t < now:
        js = get_json(f"https://www.bitstamp.net/api/v2/ohlc/{pair}/",
                      {"step": DAY, "limit": 1000, "start": t})
        data = js.get("data", {}).get("ohlc", [])
        if not data:
            t += 1000 * DAY
            continue
        for k in data:
            d = int(k["timestamp"]) // DAY
            o, h, l, c, v = (float(k[x]) for x in ("open", "high", "low", "close", "volume"))
            rows[d] = (o, h, l, c, v * c)
        t = int(data[-1]["timestamp"]) + DAY
        time.sleep(0.6)
    save("bitstamp", pair.upper(), rows)


def bitfinex(sym: str) -> None:
    js = get_json(f"https://api-pub.bitfinex.com/v2/candles/trade:1D:t{sym}/hist",
                  {"limit": 10000, "start": 0, "sort": 1})
    rows = {}
    for mts, o, c, h, l, v in js:
        rows[int(mts) // 1000 // DAY] = (float(o), float(h), float(l), float(c), float(v) * float(c))
    save("bitfinex", sym, rows)
    time.sleep(2.5)


def coinbase(product: str, start: str) -> None:
    rows: dict = {}
    t0 = dt.datetime.fromisoformat(start).replace(tzinfo=dt.timezone.utc)
    end = dt.datetime.now(dt.timezone.utc)
    while t0 < end:
        t1 = min(t0 + dt.timedelta(days=299), end)
        js = get_json(f"https://api.exchange.coinbase.com/products/{product}/candles",
                      {"granularity": DAY, "start": t0.isoformat(), "end": t1.isoformat()})
        for ts, l, h, o, c, v in js:
            rows[int(ts) // DAY] = (float(o), float(h), float(l), float(c), float(v) * float(c))
        t0 = t1
        time.sleep(0.4)
    save("coinbase", product.replace("-", ""), rows)


CC_COINS = [
    # roughly the 2014-2017 market-cap / volume leaders, dead or alive
    "BTC", "LTC", "XRP", "DOGE", "PPC", "NMC", "NXT", "DASH", "XMR", "BTS", "XLM", "MAID",
    "ETH", "XEM", "BCN", "FCT", "DGB", "SC", "STEEM", "LSK", "WAVES", "REP", "DCR", "ZEC",
    "ETC", "GNT", "ARDR", "STRAT", "KMD", "EMC", "SJCX", "AMP", "NVC", "FTC", "VTC", "GRC",
    "NAV", "SYS", "VIA", "BURST", "XCP", "RDD", "LBC", "OMNI", "NEO", "GAME", "BLK", "MONA",
    "XVG", "PIVX", "ARK", "UBQ", "EXP", "QRK", "XPM", "POT", "NLG", "CLAM", "ICN", "SNGLS",
    "DGD", "MLN", "ANT", "GNO", "BAT", "EOS", "QTUM", "OMG", "IOT", "TRX", "ADA", "BNB",
]


def cryptocompare(sym: str) -> None:
    rows: dict = {}
    to_ts = int(time.time())
    for _ in range(4):
        js = get_json("https://min-api.cryptocompare.com/data/v2/histoday",
                      {"fsym": sym, "tsym": "USD", "limit": 2000, "toTs": to_ts})
        if js.get("Response") != "Success":
            raise RuntimeError(str(js.get("Message"))[:200])
        data = js["Data"]["Data"]
        live = [k for k in data if k["close"] > 0]
        for k in live:
            rows[int(k["time"]) // DAY] = (k["open"], k["high"], k["low"], k["close"], k.get("volumeto", 0.0))
        if len(live) < len(data) or not data:
            break
        to_ts = int(data[0]["time"]) - DAY
        time.sleep(1.2)
    save("cc", sym, rows)


def attempt(name: str, fn, *args) -> None:
    try:
        fn(*args)
    except Exception as exc:  # noqa: BLE001
        manifest["errors"][name] = repr(exc)[:300]
        print("ERR", name, exc, flush=True)


def main() -> None:
    for pair, start in [("btcusd", "2011-08-01"), ("ethusd", "2017-08-01"), ("ltcusd", "2017-05-01"),
                        ("xrpusd", "2017-01-01"), ("bchusd", "2017-08-01")]:
        attempt(f"bitstamp_{pair}", bitstamp, pair, start)
    for sym in ["BTCUSD", "LTCUSD", "ETHUSD", "ETCUSD", "XMRUSD", "ZECUSD", "DSHUSD", "XRPUSD",
                "EOSUSD", "IOTUSD", "NEOUSD", "OMGUSD", "XLMUSD", "TRXUSD", "BTGUSD", "SANUSD",
                "QTMUSD", "ETPUSD", "EDOUSD", "AVTUSD", "RRTUSD"]:
        attempt(f"bitfinex_{sym}", bitfinex, sym)
    for prod, start in [("BTC-USD", "2015-07-20"), ("ETH-USD", "2016-05-18"), ("LTC-USD", "2016-08-17")]:
        attempt(f"coinbase_{prod}", coinbase, prod, start)
    for sym in CC_COINS:
        attempt(f"cc_{sym}", cryptocompare, sym)
        if sum(1 for k in manifest["errors"] if k.startswith("cc_")) >= 5 and \
                not any(k.startswith("cc_") for k in manifest["series"]):
            manifest["errors"]["cc_aborted"] = "first 5 CryptoCompare calls failed"
            break
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)


if __name__ == "__main__":
    main()
