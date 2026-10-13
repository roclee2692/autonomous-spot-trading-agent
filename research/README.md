# Strategy research lab: spot volatility strategy V2.0 → V3.0

- `REPORT_V3.md`: the research report (Chinese), in the requested 11-section structure.
- `STRATEGY_V3.md`: the complete, executable rulebook (now V3.1).
- `FINDINGS_LOG.md`: working notes with the numbers behind each conclusion.

## Data
`data/` is filled by `.github/workflows/research-data.yml` (runs `fetch/fetch_binance.py` on a GitHub
runner, because this sandbox cannot reach Binance). Daily klines for every Binance USDT spot pair ever
listed (incl. delisted), 1h klines for the focus coins, and HYPE from Hyperliquid spot / Binance perp.

## Code
- `engine.py`: bar-level simulators: `run_core` (ladder, pooled cost, TP + tail lots, roll, drift
  re-anchor, generations, spike order, halt/pause filters), `run_sat` (V2 satellite rules), `run_bh`.
- `lab.py`: loading (redenomination back-adjust, symbol-reuse split), metrics, rolling windows.
- `runner.py`: parallel rolling-window grids on focus coins and on the point-in-time (survivorship-free)
  top-30 universe; price-only halt signals.
- `exp_*.py`: one script per experiment; summaries are in `results/*.txt`.

Reproduce, e.g.: `cd research && python3 exp_final.py focus && python3 exp_final.py universe`.
Per-window CSVs are not committed (≈110 MB; regenerate with the scripts); the final validation CSVs are
committed gzipped.
