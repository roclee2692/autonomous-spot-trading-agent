

##### q1_tail_longterm_md
### Q1. Removing the permanent tail: what happens long term?

**Bottom line.** V3 sells the 25% tail at 2C. Compared with V3 plus a permanent tail, it compounds better per coin over the long run in 8 of 9 focus coins and across the survivorship-free universe. Its drawdowns are lower everywhere. The permanent tail only wins as a big-cap bull-market bet: rank 1-8 baskets whose windows start in 2019-2020 and run through the 2021 peak, plus a few H540 windows ending in the 2024 H1 rally. Outside the top 8 it almost never wins. Removing it passes your rule (B): risk is clearly down, and return is the same or better except in one regime (2019-21 big caps). That makes it an "only works in one period" rule, so it should not be kept.

**1. Full history, one path per focus coin** (from listing+3d to Oct-2026; cells are final equity multiple / CAGR / maxDD; source: longterm_focus_fullhistory.csv)

| coin (years) | V2 | V3 | V3 tail permanent | V3 no tail (reference) | B&H |
|---|---|---|---|---|---|
| LINK (7.7) | 15.57x / 42.6% / 0.90 | 20.64x / 47.9% / 0.71 | 14.34x / 41.1% / 0.89 | 16.83x / 44.1% / 0.66 | 27.17x / 53.3% / 0.90 |
| UNI (6.1) | 1.88x / 11.0% / 0.93 | 7.03x / 38.0% / 0.71 | 4.39x / 27.6% / 0.86 | 10.16x / 46.6% / 0.63 | 1.36x / 5.2% / 0.94 |
| AAVE (6.0) | 4.93x / 30.5% / 0.89 | 5.89x / 34.5% / 0.72 | 3.71x / 24.5% / 0.88 | 6.70x / 37.4% / 0.69 | 4.15x / 26.8% / 0.92 |
| NEAR (6.0) | 5.56x / 33.2% / 0.95 | 9.13x / 44.7% / 0.88 | 4.00x / 26.1% / 0.94 | 8.39x / 42.6% / 0.85 | 7.21x / 39.1% / 0.95 |
| RENDER (4.9) | 0.69x / -7.5% / 0.91 | 1.32x / 5.8% / 0.87 | 1.04x / 0.7% / 0.87 | 1.35x / 6.4% / 0.87 | 0.29x / -22.3% / 0.95 |
| PENDLE (3.3) | 2.32x / 29.4% / 0.80 | 2.77x / 36.5% / 0.64 | 2.23x / 27.7% / 0.74 | 3.55x / 47.3% / 0.46 | 2.51x / 32.5% / 0.85 |
| TAO (2.5) | 2.45x / 43.1% / 0.57 | 2.78x / 50.7% / 0.40 | 2.46x / 43.4% / 0.45 | 3.40x / 63.2% / 0.37 | 0.58x / -19.6% / 0.80 |
| ZRO (2.3) | 0.76x / -11.1% / 0.86 | 1.02x / 0.7% / 0.76 | 0.91x / -4.1% / 0.79 | 1.06x / 2.5% / 0.75 | 0.68x / -15.2% / 0.90 |
| HYPE (1.9, daily bars) | 5.26x / 143.8% / 0.56 | 2.86x / 75.7% / 0.28 | 3.46x / 94.6% / 0.44 | 2.20x / 52.5% / 0.26 | 9.07x / 226.5% / 0.68 |
| **mean CAGR / median CAGR / mean maxDD** | 35.0% / 30.5% / 0.818 | 37.1% / 38.0% / 0.663 | 31.3% / 27.6% / 0.762 | 38.1% / 44.1% / 0.615 | 36.2% / 26.8% / 0.878 |

- V3 beats the permanent tail on final multiple in **8/9 coins**. The only exception is HYPE (3.46x vs 2.86x), a 1.9-year, almost one-way rally. The CAGR cost of the permanent tail ranges from -4.8 pp (ZRO) to -18.6 pp (NEAR).
- V3 beats B&H in 7/9 coins; B&H wins on LINK and HYPE. MaxDD is lower for V3 than for the permanent tail on every coin.
- **Why:** the permanent tail never gets sold, so it turns into a buy-and-hold position. At the end of the history it is 0.18-0.85 of equity (LINK 0.72, NEAR 0.85). V3's tail share is 0.09-0.36.

**2. Universe, 5-year windows** (H=1825, step 90, starts 2019-01 to 2021-09, 314 coin-windows, PIT top-30, daily bars)

| strategy | median ret | mean ln(1+ret) | p10 | median maxDD |
|---|---|---|---|---|
| V2 | -0.076 | -0.277 | -0.923 | 0.917 |
| **V3** | **0.594** | **0.121** | -0.828 | 0.800 |
| V3 no spike | 0.520 | 0.108 | -0.819 | 0.800 |
| V3 no tail | 0.641 | 0.078 | -0.851 | 0.761 |
| V3 tail permanent | 0.144 | -0.123 | -0.892 | 0.895 |
| B&H | -0.058 | -0.258 | -0.951 | 0.942 |

**3. 5-year equal-weight baskets** (cells are lr / p10 / median maxDD; the last column counts start dates where the permanent tail's basket return beat V3's)

| bucket | n | V3 | V3 tail permanent | B&H | V2 | perm > V3 |
|---|---|---|---|---|---|---|
| rank1-4 | 12 | 1.095 / 0.613 / 0.506 | 1.380 / 0.376 / 0.671 | 1.845 / -0.036 / 0.757 | 1.490 / 0.343 / 0.686 | 8 of 12 |
| rank5-8 | 12 | 0.786 / -0.226 / 0.665 | 0.724 / -0.352 / 0.841 | 0.739 / -0.737 / 0.895 | 0.553 / -0.530 / 0.848 | 5 of 12 |
| rank9-16 | 11 | 0.798 / -0.040 / 0.680 | 0.755 / -0.116 / 0.803 | 0.773 / -0.215 / 0.883 | 0.649 / -0.217 / 0.828 | 5 of 11 |
| rank17-30 | 9 | 0.219 / -0.306 / 0.705 | -0.174 / -0.592 / 0.833 | -0.060 / -0.741 / 0.905 | -0.246 / -0.601 / 0.878 | **0 of 9** |
| top8 | 12 | 0.985 / 0.233 / 0.568 | **1.128** / 0.016 / 0.719 | 1.464 / -0.424 / 0.791 | 1.158 / -0.094 / 0.750 | 8 of 12 |
| top30 | 9 | **0.614** / -0.088 / 0.601 | 0.522 / -0.238 / 0.748 | 0.788 / -0.553 / 0.841 | 0.479 / -0.404 / 0.792 | 1 of 9 |

**4. Where the permanent tail wins: 5-year top-8 basket return by start date** (recomputed by start date; it reproduces the aggregates in r2_longterm.txt exactly)

| start to end | V3 | V3 tail perm | B&H | perm - V3 | maxDD V3 / perm |
|---|---|---|---|---|---|
| 2019-01 to 2023-12 | 2.388 | 4.032 | 8.982 | +1.645 | 0.570 / 0.741 |
| 2019-04 to 2024-03 | 2.537 | 4.713 | 6.078 | +2.176 | 0.567 / 0.743 |
| 2019-06 to 2024-06 | 1.819 | 3.709 | 2.379 | +1.890 | 0.534 / 0.736 |
| 2019-09 to 2024-09 | 2.654 | 3.974 | 7.276 | +1.320 | 0.410 / 0.672 |
| 2019-12 to 2024-12 | 4.749 | 7.457 | 15.586 | +2.709 | 0.582 / 0.814 |
| 2020-03 to 2025-03 | 2.381 | 2.994 | 11.526 | +0.613 | 0.508 / 0.715 |
| 2020-06 to 2025-06 | 1.671 | 1.726 | 6.665 | +0.055 | 0.622 / 0.722 |
| 2020-09 to 2025-09 | 2.433 | 2.704 | 10.341 | +0.271 | 0.609 / 0.725 |
| 2020-12 to 2025-12 | 1.823 | 1.531 | 3.447 | -0.292 | 0.612 / 0.685 |
| 2021-03 to 2026-03 | 0.594 | 0.384 | -0.042 | -0.210 | 0.589 / 0.620 |
| 2021-06 to 2026-06 | 0.193 | -0.032 | -0.467 | -0.225 | 0.505 / 0.547 |
| 2021-09 to 2026-09 | 0.153 | -0.025 | -0.477 | -0.178 | 0.555 / 0.565 |

For the 5-year top-30 basket, perm - V3 by start date is: 2019-09 -0.661, 2019-12 **+1.038**, 2020-03 -0.045, 2020-06 -0.092, 2020-09 -0.148, 2020-12 -0.278, 2021-03 -0.216, 2021-06 -0.162, 2021-09 -0.102.

**5. Sensitivity grid: `tail_target=none` (permanent tail) vs V3, absolute values** (cells are V3 / permanent)

| metric | Focus H540 | Focus H1095 | Universe H540 | Universe H1095 |
|---|---|---|---|---|
| logret (coin) | 0.314 / 0.286 | 0.567 / **0.395** | 0.132 / 0.125 | 0.116 / **-0.042** |
| p10 (coin) | -0.348 / -0.368 | -0.083 / -0.254 | -0.595 / -0.609 | -0.688 / -0.739 |
| maxDD (coin) | 0.385 / 0.473 | 0.617 / 0.700 | 0.392 / 0.506 | 0.658 / 0.768 |
| all30 basket lr / p10 | - | - | 0.253 / **0.314**; -0.348 / -0.380 | 0.437 / 0.404; -0.077 / -0.190 |
| top8 basket lr / p10 | - | - | 0.266 / **0.353**; -0.236 / -0.258 | 0.539 / **0.626**; 0.170 / 0.058 |
| IS lr (coin; all30; top8) | 0.150 / 0.122 | 0.322 / 0.061 | 0.208 / 0.231; 0.358 / **0.489**; 0.327 / **0.458** | 0.483 / 0.307; 0.792 / **0.866**; 0.769 / **0.997** |
| OOS lr (H1095: windows ending in 2024 or later) | 0.207 / 0.158 | 0.558 / 0.398 | -0.231 / -0.279; all30 -0.114 / -0.157; top8 0.007 / -0.017 | -0.133 / -0.279; all30 0.147 / 0.025; top8 0.350 / 0.323 |

**6. Baskets by window start, H540 / H1095 / 5y** (source: portfolio2_runs_H*.csv and the 5-year recomputation; lr cells are V3 / permanent)

| H | bucket | n | perm better / worse | lr, all windows | lr, starts before 2021 | lr, starts 2021 or later |
|---|---|---|---|---|---|---|
| 540 | top8 | 39 | 16 / 21 | 0.266 / 0.353 | 0.686 / 0.937 | 0.056 / 0.060 |
| 540 | top30 | 35 | 12 / 23 | 0.222 / 0.291 | 0.967 / 1.346 | -0.036 / -0.074 |
| 540 | rank17-30 | 34 | 8 / 24 | 0.181 / 0.189 | 1.016 / 1.235 | -0.075 / -0.133 |
| 1095 | top8 | 20 | 11 / 9 | 0.539 / 0.626 | 0.769 / 0.997 | 0.350 / 0.323 |
| 1095 | top30 | 17 | 4 / 13 | 0.300 / 0.211 | 0.581 / 0.551 | 0.147 / 0.025 |
| 1095 | rank17-30 | 17 | **0 / 17** | 0.201 / -0.027 | 0.497 / 0.200 | 0.039 / -0.150 |
| 1825 | top8 | 12 | 8 / 4 | 0.985 / 1.128 | 1.226 / 1.475 | 0.262 / 0.089 |
| 1825 | top30 | 9 | 1 / 8 | 0.614 / 0.522 | 0.951 / 0.906 | -0.061 / -0.244 |
| 1825 | rank17-30 | 9 | **0 / 9** | 0.219 / -0.174 | 0.501 / 0.079 | -0.344 / -0.681 |

**Where the permanent tail would have been better**
- **Top-4/top-8 baskets in the 2019-21 bull.** At H540, top-8 windows starting 2019-08 to 2020-08 (ending 2021-02 to 2022-02) gained +0.144 to +8.046 in basket return; the 2019-12 to 2021-06 window was V3 2.644 vs perm 10.690 vs B&H 18.820. At H1095, top-8 windows starting in 2019 gained +0.456 lr. At 5 years, top-8 windows starting 2019-01 to 2020-09 gained +0.055 to +2.709.
- **The 2024 H1 rally.** H540 top-8 windows starting 2022-10 to 2023-02 gained +0.092 to +0.444.
- **HYPE's full history.**

**Where it would have been worse**
- **Every bucket below the top 8:** rank17-30 lost in 0/9 five-year and 0/17 three-year windows, and top-30 five-year baskets were better in only 1/9.
- **Every 3-year or 5-year window starting in 2021 or later.**
- **The 2024-26 out-of-sample period:** Universe H540 OOS all30 basket -0.043, Focus H540 OOS coin lr -0.049.
- **Per-coin compounding:** universe 5-year coin lr goes from 0.121 to -0.123, and median return from 0.594 to 0.144.
- **Drawdown, always:** median maxDD of the 5-year top-8 basket goes from 0.568 to 0.719, and the mean full-history focus maxDD from 0.663 to 0.762.

**Exposure-matched context** (r2_portfolio.txt). At H540, B&H scaled down to V3's median drawdown (k=0.30-0.39) slightly beats V3 in rank1-4 (0.318 vs 0.290), top8 (0.285 vs 0.266) and top30 (0.249 vs 0.222). It is slightly behind in rank5-8 (0.203 vs 0.219), rank9-16 (0.205 vs 0.223) and rank17-30 (0.172 vs 0.181). At H1095, V3 beats both scaled V2 and scaled B&H in every bucket: top8 0.539 vs 0.484 / 0.450; top30 0.300 vs 0.155 / 0.251; rank17-30 0.201 vs -0.067 / 0.033.


##### q2_gap_md
### Q2. How large should the generation gap be?

**Bottom line.** Gaps of 0-0.10 are clearly worse, mainly in the universe sample and out of sample: universe coin lr is -0.026 to -0.115 vs V3, and p10 is -0.05 to -0.11. From **0.15 to 0.40** logret is flat or better in all four cells. Over the same range, p10, maxDD and "worst equity vs principal" improve monotonically, in sample and out of sample. 0.40, the edge of the grid, is best in every cell.

**Recommendation: move gap to 0.30.**
- It passes rule (B) in all four cells and both periods: Δlr is +0.008 to +0.075, Δp10 is +0.057 to +0.147, and the worst in-sample Δlr is -0.018 (Universe H1095).
- 0.30 sits in the middle of the good region, not at its edge.
- Before going to 0.40, test 0.5/0.6 and a joint gap x gen_mult grid. gap, gen_mult and d3 are one lever: they all put money deeper. Change only one of them.

**What gap means in price terms** (fill levels below the generation-1 anchor A, ladder 7/17/35%)

| gap | gen-2 B1 / B2 / B3 | gen-3 B1 / B2 / B3 |
|---|---|---|
| 0.00 | -39.6 / -46.1 / -57.7% | -60.7 / -64.9 / -72.5% |
| 0.05 | -42.6 / -48.7 / -59.9% | -64.5 / -68.4 / -75.2% |
| 0.10 | -45.6 / -51.4 / -62.0% | -68.2 / -71.6 / -77.8% |
| 0.15 | -48.6 / -54.1 / -64.1% | -71.6 / -74.7 / -80.2% |
| **0.20 (V3)** | -51.6 / -56.8 / -66.2% | -74.9 / -77.6 / -82.4% |
| 0.25 | -54.7 / -59.5 / -68.3% | -77.9 / -80.3 / -84.6% |
| 0.30 | -57.7 / -62.2 / -70.4% | -80.7 / -82.8 / -86.5% |
| 0.40 | -63.7 / -67.6 / -74.6% | -85.9 / -87.4 / -90.1% |

**Focus H540** (336 windows; IS = 117 windows ending before 2024, OOS = 124 windows starting 2024 or later; coin-equal weights)

| gap | logret | p10 | maxDD | IS lr | IS p10 | OOS lr | OOS p10 |
|---|---|---|---|---|---|---|---|
| 0.00 | 0.323 | -0.417 | 0.450 | 0.178 | -0.568 | 0.178 | -0.409 |
| 0.05 | 0.326 | -0.434 | 0.428 | 0.161 | -0.529 | 0.183 | -0.443 |
| 0.10 | 0.333 | -0.392 | 0.427 | 0.221 | -0.490 | 0.201 | -0.408 |
| 0.15 | 0.326 | -0.362 | 0.388 | 0.224 | -0.463 | 0.192 | -0.386 |
| **0.20 V3** | 0.314 | -0.348 | 0.385 | 0.150 | -0.477 | 0.207 | -0.345 |
| 0.25 | 0.307 | -0.301 | 0.375 | 0.201 | -0.415 | 0.192 | -0.301 |
| 0.30 | 0.330 | -0.243 | 0.348 | 0.214 | -0.368 | 0.223 | -0.283 |
| 0.40 | 0.330 | -0.198 | 0.317 | 0.244 | -0.351 | 0.222 | -0.198 |

**Focus H1095** (197 windows. There are no OOS windows: a 2024 start plus 1095 days runs past the data. "X" = 163 windows starting before 2024 and ending in 2024 or later; IS = 34 windows, mostly LINK)

| gap | logret | p10 | maxDD | IS lr | IS p10 | X lr | X p10 |
|---|---|---|---|---|---|---|---|
| 0.00 | 0.594 | -0.187 | 0.693 | 0.513 | -0.190 | 0.560 | -0.187 |
| 0.05 | 0.630 | -0.093 | 0.677 | 0.354 | -0.116 | 0.617 | -0.063 |
| 0.10 | 0.632 | -0.069 | 0.667 | 0.470 | -0.146 | 0.615 | -0.036 |
| 0.15 | 0.665 | -0.002 | 0.628 | 0.512 | -0.170 | 0.635 | 0.001 |
| **0.20 V3** | 0.567 | -0.083 | 0.617 | 0.322 | -0.131 | 0.558 | -0.082 |
| 0.25 | 0.607 | -0.030 | 0.592 | 0.425 | -0.027 | 0.586 | -0.030 |
| 0.30 | 0.641 | 0.064 | 0.575 | 0.503 | 0.122 | 0.622 | 0.075 |
| 0.40 | 0.679 | 0.236 | 0.513 | 0.650 | 0.368 | 0.638 | 0.193 |

**Universe H540** (1103 coin-windows; IS 593, OOS 240; maxDD = median per-coin)

| gap | coin lr | coin p10 | maxDD | all30 lr | all30 p10 | IS coin lr | OOS coin lr | IS all30 lr | OOS all30 lr | OOS all30 p10 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.00 | 0.083 | -0.708 | 0.466 | 0.251 | -0.457 | 0.180 | -0.390 | 0.375 | -0.205 | -0.434 |
| 0.05 | 0.101 | -0.692 | 0.445 | 0.252 | -0.435 | 0.196 | -0.350 | 0.372 | -0.182 | -0.417 |
| 0.10 | 0.106 | -0.657 | 0.424 | 0.251 | -0.400 | 0.184 | -0.301 | 0.358 | -0.148 | -0.377 |
| 0.15 | 0.126 | -0.624 | 0.413 | 0.258 | -0.377 | 0.212 | -0.268 | 0.373 | -0.135 | -0.354 |
| **0.20 V3** | 0.132 | -0.595 | 0.392 | 0.253 | -0.348 | 0.208 | -0.231 | 0.358 | -0.114 | -0.329 |
| 0.25 | 0.135 | -0.569 | 0.381 | 0.250 | -0.326 | 0.212 | -0.212 | 0.352 | -0.097 | -0.308 |
| 0.30 | 0.140 | -0.537 | 0.367 | 0.252 | -0.311 | 0.217 | -0.189 | 0.356 | -0.083 | -0.281 |
| 0.40 | 0.166 | -0.425 | 0.338 | 0.255 | -0.263 | 0.254 | -0.140 | 0.362 | -0.063 | -0.247 |

**Universe H1095** (554 coin-windows; IS 224, X 330, no OOS)

| gap | coin lr | coin p10 | maxDD | all30 lr | all30 p10 | IS coin lr | X coin lr | IS all30 lr | X all30 lr | X all30 p10 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.00 | 0.000 | -0.759 | 0.741 | 0.410 | -0.164 | 0.411 | -0.278 | 0.806 | 0.086 | -0.239 |
| 0.05 | 0.066 | -0.735 | 0.722 | 0.433 | -0.162 | 0.504 | -0.231 | 0.836 | 0.103 | -0.226 |
| 0.10 | 0.047 | -0.734 | 0.700 | 0.417 | -0.109 | 0.420 | -0.205 | 0.778 | 0.122 | -0.190 |
| 0.15 | 0.114 | -0.694 | 0.661 | 0.448 | -0.092 | 0.505 | -0.152 | 0.829 | 0.137 | -0.139 |
| **0.20 V3** | 0.116 | -0.688 | 0.658 | 0.437 | -0.077 | 0.483 | -0.133 | 0.792 | 0.147 | -0.132 |
| 0.25 | 0.122 | -0.615 | 0.625 | 0.417 | -0.025 | 0.451 | -0.101 | 0.736 | 0.157 | -0.141 |
| 0.30 | 0.154 | -0.618 | 0.603 | 0.445 | -0.002 | 0.465 | -0.058 | 0.768 | 0.181 | -0.058 |
| 0.40 | 0.234 | -0.501 | 0.552 | 0.467 | -0.015 | 0.587 | -0.005 | 0.806 | 0.190 | -0.041 |

**Is a deeper gap better than simply holding less?** A deeper gap deploys less capital. Median time-average exposure ("util") for V3 is 0.425 / 0.517 / 0.440 / 0.564 (F540 / F1095 / U540 / U1095); for gap 0.30 it is 0.404 / 0.475 / 0.400 / 0.504, and for gap 0.40 it is 0.360 / 0.425 / 0.369 / 0.461. The table compares each gap against V3 scaled down to the same exposure (k x V3 + (1-k) x cash; exact for returns). Cells are lr / p10.

| cell | gap 0.30 | V3 scaled to the same util | gap 0.40 | V3 scaled to the same util |
|---|---|---|---|---|
| Focus H540 | 0.330 / -0.243 | 0.306 / -0.330 (k 0.95) | 0.330 / -0.198 | 0.287 / -0.295 (k 0.85) |
| Focus H1095 | 0.641 / 0.064 | 0.536 / -0.076 (k 0.92) | 0.679 / 0.236 | 0.498 / -0.068 (k 0.82) |
| Universe H540, coin | 0.140 / -0.537 | 0.150 / -0.540 (k 0.91) | 0.166 / -0.425 | 0.156 / -0.499 (k 0.84) |
| Universe H540, all30 basket | 0.252 / -0.311 | 0.242 / -0.316 | 0.255 / -0.263 | 0.233 / -0.292 |
| Universe H1095, coin | 0.154 / -0.618 | 0.155 / -0.613 (k 0.89) | 0.234 / -0.501 | 0.165 / -0.562 (k 0.82) |
| Universe H1095, all30 basket | 0.445 / -0.002 | 0.406 / -0.069 | 0.467 / -0.015 | 0.383 / -0.063 |

**Plateau description**
- **Below 0.15 there is a cliff,** mostly in the universe and out of sample. At gap 0, Universe H540 OOS coin lr is -0.390 vs -0.231.
- **From 0.15 to 0.40 (the top end is open)** Δlr vs V3 stays between -0.007 and +0.119 in all four cells. Δp10 rises from about -0.03 at 0.15 to +0.15 / +0.32 / +0.17 / +0.19 at 0.40. Median maxDD falls by 0.055-0.105 at 0.40.
- **The all30 basket mean barely moves** (0.250-0.258 at H540, 0.417-0.467 at H1095). Its p10 does improve: H540 -0.348 to -0.263; H1095 -0.077 to -0.015.
- **The gains are not period-specific.** At gap 0.40, Δlr is +0.046 to +0.328 in sample and +0.016 to +0.128 OOS/X, and the all30 basket gains +0.004 / +0.014 in sample and +0.051 / +0.044 OOS/X. At gap 0.30 the worst in-sample Δlr is -0.018 (U1095) and the worst OOS/X is +0.016.
- **Against exposure-matched V3:** on the universe per-coin metric, gap 0.30 roughly ties (its gain is mostly "hold about 10% less"). It still wins on focus and on the all30 basket. Gap 0.40 beats exposure-matched V3 in every cell, on both lr and p10.


##### q3_universal_params_md
### Q3. Which parameters generalise best?

**Plateau criterion used:** a value is on the plateau if Δlogret vs V3 is at least -0.02 in all four cells (Focus H540/H1095 coin-equal lr; Universe H540/H1095 per-coin lr) and its worst Δp10 across the four cells is at least -0.03. The test is one-sided, so improvements count as on the plateau. Basket and IS/OOS deltas are in the appendix. tail_target = x means the tail sells at (1+x)·C; tp = x means TP at (1+x)·C.

| family | V3 | tested | on plateau | off plateau (worst Δlr or Δp10) | V3 position | recommended |
|---|---|---|---|---|---|---|
| d1 (B1 depth) | 0.07 | 0.04, 0.05, 0.10, 0.12 | 0.05-0.12 (0.10: Δlr -0.010 to +0.020, Δp10 +0.005 to +0.056) | 0.04 (U1095 -0.026) | interior | keep 0.07 |
| d2 | 0.17 | 0.12, 0.14, 0.20, 0.25 | the whole range 0.12-0.25 | none | interior; insensitive | keep 0.17 |
| d3 | 0.35 | 0.25, 0.29, 0.30, 0.40, 0.45, 0.50 | 0.35-0.45 (0.40: Δp10 +0.042 to +0.137; 0.45: +0.106 to +0.144; but all30 basket lr -0.013 to -0.037) | 0.25 / 0.29 / 0.30 (U1095 -0.063 / -0.069 / -0.036; Δp10 down to -0.085); 0.50 (F540 -0.042) | **shallow edge; a cliff 5 pp shallower** | keep 0.35, never shallower; do not also deepen it if gap moves |
| gap | 0.20 | 0, 0.05, 0.10, 0.15, 0.25, 0.30, 0.40 | 0.15-0.40, open at the top (0.30: Δlr +0.008 to +0.075, Δp10 +0.057 to +0.147) | 0 / 0.05 / 0.10 (U1095 -0.115 / -0.049 / -0.068; Δp10 -0.062 to -0.113) | interior for lr; p10 and maxDD keep improving to the grid edge | **0.30** (Q2) |
| gens (budget units) | 3 (3u) | 1 (3u), 2 (2u), 2 (3u), 4 (4u) | **only 3** | 1: F1095 -0.214; 2 (2u): U1095 -0.156, Δp10 -0.195; 2 (3u): F1095 -0.104; 4: F540 -0.036 (but Δp10 +0.12 to +0.185, all30 lr -0.035 / -0.031) | isolated optimum | keep 3 |
| gen_mult | 1.0 | 0.5, 1.5, 2.0 | 1.0-2.0, open at the top (1.5: Δlr +0.002 to +0.028, Δp10 +0.039 to +0.123; 2.0: +0.003 to +0.148, +0.061 to +0.317) | 0.5 (U1095 -0.055, Δp10 -0.091) | low edge, next to a cliff | keep 1.0 if gap goes to 0.3 (same lever); 1.5 is the alternative lever |
| ladder weights | 1/3 each | 50/30/20, 40/35/25, 20/30/50 | 50/30/20, 20/30/50 (Δp10 +0.026 to +0.078) | 40/35/25 (lr passes, worst -0.015; F1095 Δp10 -0.062) | interior | keep equal thirds (simplest) |
| tiers | 3 (7/17/35) | 2 (10/30), 4 (5/12/22/35) | 3, 4 | 2 tiers (U1095 -0.033, Δp10 -0.037) | - | keep 3 (4 adds complexity with no gain) |
| tp | 0.25 | 0.15, 0.20, 0.30, 0.35, 0.40, 0.50 | 0.15-0.30 | 0.35 / 0.40 / 0.50 (U1095 -0.046 / -0.044 / -0.037) | interior | keep 0.25 |
| tp_sell | 0.75 | 0.5, 0.6, 0.67, 0.8, 0.9, 1.0 | 0.75-0.90 | 0.5 / 0.6 / 0.67 (F1095 -0.071 / -0.043 / -0.023); 1.0 (U540 -0.025) | low edge | keep 0.75 (0.8 is equivalent; 0.9 is better OOS but worse in sample in the universe, -0.031) |
| tail_target | 1.0 (2C) | 0.5 (1.5C), 0.75 (1.75C), 1.5 (2.5C), 2.0 (3C), 3.0 (4C), none | 0.5-2.0, i.e. 1.5C-3C. 0.75 fails only on F1095 p10 (-0.050) while both neighbours pass, so probably noise | 3.0 (U1095 -0.021, Δp10 -0.032); none (F1095 -0.172) | interior | keep 2C |
| drift | 0.20 | 0.10, 0.15, 0.25, 0.30, 0.40, none | 0.10-0.30 | 0.40 (Δp10 -0.043); none (F1095 -0.128) | centre | keep 0.20 |
| spike size | 0.075 | 0, 0.05, 0.10, 0.15, 0.20, 0.30 | 0.05-0.30 (rises monotonically to +0.068 / +0.070 / +0.015 / +0.019) | 0 (F540 and F1095 -0.031) | interior | keep 0.075: gains above it come only from OOS / crash windows (Q4) |
| spike depth | 0.60 | 0.40, 0.50, 0.55, 0.65, 0.70, 0.80 | 0.60-0.80 (0.65 passes; 0.70 borderline at F1095 -0.024; 0.80 passes) | 0.40 / 0.50 (-0.034 / -0.025); 0.55 (all four Δlr negative; F1095 Δp10 -0.033) | shallow edge | keep 0.60 (0.65 equivalent) |
| spike tp | 0.40 | 0.20, 0.30, 0.50, 0.60, 1.00 | 0.20-0.60 | 1.00 (F1095 -0.022, Δp10 -0.027) | centre | keep 0.40 |
| roll | on | off | on only | off: F1095 -0.198, F540 -0.120, all30 basket -0.081 / -0.160. Its Δp10 of +0.16 to +0.43 comes from holding far less. | - | keep on |
| costs x2 | - | fee 0.2%, penetration 0.2% | Δlr -0.006 to -0.028 | - | - | the strategy is robust to costs |

**Flags**
- **No family has V3 clearly off its plateau.**
- **V3 sits on an edge next to a cliff** for:
  - d3 (0.30 is off)
  - gen_mult (0.5 is off)
  - tp_sell (0.67 is slightly off)
  - spike depth (0.55 is slightly off)
  - gens (3 is the only value that passes)
- **Never move these in the cliff direction:**
  - shallower d3
  - smaller gap
  - lower tp_sell
  - shallower spike
- **For gap, gen_mult, d3 (0.40-0.45) and w=20/30/50, risk keeps improving beyond V3.** They are all one lever ("deploy deeper / hold more cash early"). Adopt only gap=0.30 and leave the others alone until a joint grid is run.

**Most robust (flat everywhere):** d2, drift 0.10-0.30, tp 0.15-0.30, spike tp 0.3-0.6, d1 0.05-0.12, tail target 1.5C-3C.

**Most sensitive:** gens, roll, drift=none, permanent tail, shallow d3, small gap.

**Appendix: every variant.** Δ = variant minus V3. "Worst Δp10" is the minimum over the four cells. "Worst IS" is over F540 / F1095 / U540 / U1095 in sample. "Worst OOS/X" is over F540 OOS, F1095 X, U540 OOS, U1095 X.

| variant | Δlr F540 | Δlr F1095 | Δlr U540 | Δlr U1095 | worst Δp10 | Δ all30 lr U540 / U1095 | worst Δ IS lr | worst Δ OOS/X lr | plateau |
|---|---|---|---|---|---|---|---|---|---|
| costs x2 | -0.025 | -0.006 | -0.022 | -0.028 | -0.003 | -0.013 / -0.018 | -0.034 | -0.032 | no |
| d1=0.04 | +0.003 | +0.040 | -0.019 | -0.026 | -0.004 | -0.004 / -0.018 | -0.028 | -0.025 | no |
| d1=0.05 | -0.006 | +0.030 | -0.004 | +0.001 | +0.005 | -0.001 / +0.005 | -0.002 | -0.011 | yes |
| d1=0.1 | +0.018 | +0.020 | -0.010 | +0.003 | +0.005 | -0.003 / +0.003 | -0.018 | -0.016 | yes |
| d1=0.12 | +0.021 | +0.060 | -0.007 | -0.013 | +0.008 | -0.012 / -0.031 | -0.030 | -0.000 | yes |
| d2=0.12 | +0.005 | +0.091 | -0.016 | -0.013 | -0.006 | +0.001 / +0.009 | -0.021 | -0.023 | yes |
| d2=0.14 | -0.006 | +0.048 | -0.018 | -0.020 | -0.021 | -0.003 / +0.001 | -0.020 | -0.035 | yes |
| d2=0.2 | -0.009 | +0.043 | -0.007 | +0.006 | +0.008 | +0.001 / +0.005 | -0.013 | -0.013 | yes |
| d2=0.25 | +0.028 | +0.003 | -0.005 | +0.012 | +0.001 | +0.000 / +0.007 | -0.015 | +0.005 | yes |
| d3=0.25 | +0.019 | +0.020 | -0.032 | -0.063 | -0.085 | +0.023 / +0.036 | -0.009 | -0.129 | no |
| d3=0.29 | +0.012 | +0.084 | -0.030 | -0.069 | -0.063 | +0.003 / -0.007 | -0.031 | -0.095 | no |
| d3=0.3 | +0.032 | +0.087 | -0.023 | -0.036 | -0.054 | +0.008 / +0.005 | -0.016 | -0.075 | no |
| d3=0.4 | -0.007 | +0.058 | -0.013 | -0.003 | +0.042 | -0.013 / -0.024 | -0.063 | -0.022 | yes |
| d3=0.45 | -0.004 | +0.005 | -0.005 | +0.033 | +0.106 | -0.028 / -0.037 | -0.021 | -0.003 | yes |
| d3=0.5 | -0.042 | +0.012 | +0.006 | +0.073 | +0.115 | -0.026 / -0.025 | +0.008 | -0.039 | no |
| drift=0.1 | +0.015 | +0.055 | -0.005 | +0.001 | -0.007 | -0.000 / +0.001 | -0.005 | -0.020 | yes |
| drift=0.15 | -0.007 | +0.012 | -0.014 | -0.011 | -0.007 | +0.000 / +0.002 | -0.019 | -0.030 | yes |
| drift=0.25 | +0.007 | +0.011 | -0.009 | +0.007 | +0.000 | -0.003 / +0.004 | -0.014 | +0.001 | yes |
| drift=0.3 | +0.008 | +0.015 | -0.012 | -0.005 | -0.029 | -0.004 / -0.006 | -0.021 | -0.002 | yes |
| drift=0.4 | -0.006 | -0.012 | -0.017 | -0.018 | -0.043 | -0.009 / -0.018 | -0.038 | -0.009 | no |
| drift=none | -0.114 | -0.128 | -0.064 | +0.026 | +0.104 | -0.081 / -0.103 | -0.130 | -0.125 | no |
| gap=0.0 | +0.009 | +0.028 | -0.049 | -0.115 | -0.113 | -0.002 / -0.027 | -0.071 | -0.159 | no |
| gap=0.05 | +0.012 | +0.063 | -0.030 | -0.049 | -0.097 | -0.001 / -0.004 | -0.012 | -0.119 | no |
| gap=0.1 | +0.019 | +0.066 | -0.026 | -0.068 | -0.062 | -0.003 / -0.020 | -0.063 | -0.072 | no |
| gap=0.15 | +0.012 | +0.098 | -0.006 | -0.002 | -0.030 | +0.005 / +0.011 | +0.004 | -0.037 | yes |
| gap=0.25 | -0.007 | +0.040 | +0.003 | +0.007 | +0.025 | -0.003 / -0.020 | -0.031 | -0.014 | yes |
| gap=0.3 | +0.016 | +0.075 | +0.008 | +0.038 | +0.057 | -0.001 / +0.008 | -0.018 | +0.016 | yes |
| gap=0.4 | +0.015 | +0.112 | +0.034 | +0.119 | +0.150 | +0.001 / +0.030 | +0.046 | +0.016 | yes |
| gen_mult=0.5 | -0.011 | +0.048 | -0.026 | -0.055 | -0.091 | +0.003 / +0.013 | -0.007 | -0.135 | no |
| gen_mult=1.5 | +0.010 | +0.012 | +0.002 | +0.028 | +0.039 | -0.007 / +0.000 | -0.055 | +0.010 | yes |
| gen_mult=2.0 | +0.027 | +0.148 | +0.003 | +0.052 | +0.061 | -0.013 / +0.004 | -0.010 | +0.062 | yes |
| gens=1 (3u) | -0.126 | -0.214 | -0.000 | +0.084 | -0.016 | -0.094 / -0.157 | -0.005 | -0.268 | no |
| gens=2 (2u) | +0.010 | -0.035 | -0.060 | -0.156 | -0.195 | +0.011 / -0.020 | -0.076 | -0.224 | no |
| gens=2 (3u) | -0.031 | -0.104 | +0.020 | +0.072 | -0.033 | -0.027 / -0.063 | +0.003 | -0.132 | no |
| gens=4 (4u) | -0.036 | -0.029 | +0.002 | +0.067 | +0.120 | -0.035 / -0.031 | -0.008 | -0.029 | no |
| roll=off | -0.120 | -0.198 | -0.025 | +0.009 | +0.164 | -0.081 / -0.160 | -0.099 | -0.218 | no |
| spike_depth=0.4 | -0.034 | -0.033 | -0.020 | -0.033 | -0.015 | -0.019 / -0.026 | -0.037 | -0.062 | no |
| spike_depth=0.5 | -0.017 | -0.022 | -0.015 | -0.025 | -0.022 | -0.014 / -0.020 | -0.032 | -0.041 | no |
| spike_depth=0.55 | -0.013 | -0.015 | -0.008 | -0.015 | -0.033 | -0.006 / -0.011 | -0.019 | -0.024 | no |
| spike_depth=0.65 | -0.001 | -0.014 | +0.007 | +0.023 | -0.004 | +0.005 / +0.023 | +0.001 | -0.019 | yes |
| spike_depth=0.7 | -0.013 | -0.024 | +0.009 | +0.014 | -0.006 | +0.003 / +0.005 | -0.009 | -0.030 | no |
| spike_depth=0.8 | -0.018 | -0.019 | +0.008 | +0.007 | +0.031 | -0.003 / -0.013 | -0.015 | -0.032 | yes |
| spike_size=0.0 | -0.031 | -0.031 | -0.009 | -0.011 | -0.006 | -0.010 / -0.008 | -0.007 | -0.057 | no |
| spike_size=0.05 | -0.010 | -0.010 | -0.003 | -0.003 | -0.000 | -0.003 / -0.003 | -0.002 | -0.018 | yes |
| spike_size=0.1 | +0.009 | +0.009 | +0.002 | +0.003 | -0.001 | +0.003 / +0.003 | -0.004 | +0.005 | yes |
| spike_size=0.15 | +0.026 | +0.027 | +0.007 | +0.009 | +0.003 | +0.009 / +0.008 | -0.013 | +0.015 | yes |
| spike_size=0.2 | +0.042 | +0.042 | +0.010 | +0.013 | +0.005 | +0.015 / +0.013 | -0.022 | +0.024 | yes |
| spike_size=0.3 | +0.068 | +0.070 | +0.015 | +0.019 | +0.003 | +0.026 / +0.022 | -0.045 | +0.039 | yes |
| spike_tp=0.2 | -0.010 | -0.020 | +0.001 | +0.011 | -0.007 | -0.001 / +0.011 | -0.010 | -0.022 | yes |
| spike_tp=0.3 | -0.005 | -0.008 | +0.001 | +0.002 | +0.000 | +0.000 / -0.001 | -0.003 | -0.009 | yes |
| spike_tp=0.5 | -0.003 | -0.009 | -0.004 | -0.003 | -0.027 | -0.003 / -0.003 | -0.002 | -0.010 | yes |
| spike_tp=0.6 | +0.001 | -0.002 | -0.006 | -0.010 | -0.025 | -0.004 / -0.008 | -0.017 | -0.008 | yes |
| spike_tp=1.0 | -0.013 | -0.022 | -0.012 | -0.019 | -0.027 | -0.010 / -0.016 | -0.032 | -0.023 | no |
| tail_target=0.5 | +0.008 | +0.076 | -0.017 | +0.003 | +0.019 | -0.010 / -0.001 | -0.054 | +0.027 | yes |
| tail_target=0.75 | +0.011 | +0.047 | -0.014 | -0.006 | -0.050 | -0.006 / -0.001 | -0.030 | -0.014 | no |
| tail_target=1.5 | -0.008 | -0.001 | -0.005 | +0.000 | -0.020 | +0.014 / +0.033 | -0.009 | -0.039 | yes |
| tail_target=2.0 | -0.009 | +0.019 | -0.002 | -0.010 | -0.025 | +0.020 / +0.022 | +0.009 | -0.060 | yes |
| tail_target=3.0 | -0.011 | +0.017 | +0.003 | -0.021 | -0.032 | +0.028 / +0.020 | +0.018 | -0.084 | no |
| tail_target=none | -0.028 | -0.172 | -0.006 | -0.157 | -0.172 | +0.061 / -0.033 | -0.261 | -0.160 | no |
| tiers=2 (10/30) | +0.034 | +0.059 | -0.015 | -0.033 | -0.037 | +0.005 / -0.014 | -0.036 | -0.053 | no |
| tiers=4 (5/12/22/35) | -0.011 | +0.035 | -0.008 | -0.018 | -0.024 | -0.004 / -0.025 | -0.028 | -0.026 | yes |
| tp=0.15 | +0.013 | +0.017 | +0.002 | +0.011 | +0.014 | -0.007 / -0.005 | +0.019 | -0.019 | yes |
| tp=0.2 | +0.031 | +0.036 | -0.002 | +0.003 | +0.016 | -0.007 / -0.009 | -0.001 | -0.020 | yes |
| tp=0.3 | -0.009 | +0.041 | -0.004 | +0.001 | -0.019 | +0.005 / +0.023 | -0.025 | -0.010 | yes |
| tp=0.35 | -0.031 | +0.027 | -0.023 | -0.046 | -0.021 | -0.003 / -0.017 | -0.103 | -0.028 | no |
| tp=0.4 | -0.024 | -0.006 | -0.022 | -0.044 | -0.071 | -0.010 / -0.017 | -0.101 | -0.011 | no |
| tp=0.5 | -0.012 | +0.023 | -0.016 | -0.037 | -0.047 | -0.005 / -0.010 | -0.118 | -0.018 | no |
| tp_sell=0.5 | -0.026 | -0.071 | -0.008 | -0.052 | -0.087 | +0.004 / -0.010 | -0.031 | -0.077 | no |
| tp_sell=0.6 | -0.015 | -0.043 | -0.003 | -0.028 | -0.071 | +0.004 / -0.004 | -0.018 | -0.047 | no |
| tp_sell=0.67 | -0.008 | -0.023 | -0.001 | -0.014 | -0.024 | +0.002 / -0.001 | -0.009 | -0.025 | no |
| tp_sell=0.8 | +0.005 | +0.014 | -0.001 | +0.006 | +0.001 | -0.002 / -0.001 | -0.008 | +0.012 | yes |
| tp_sell=0.9 | +0.013 | +0.038 | -0.008 | +0.011 | +0.019 | -0.008 / -0.007 | -0.031 | +0.035 | yes |
| tp_sell=1.0 | +0.018 | +0.057 | -0.025 | -0.003 | -0.000 | -0.018 / -0.020 | -0.084 | +0.052 | no |
| w=20/30/50 | -0.002 | +0.008 | -0.012 | -0.009 | +0.026 | -0.009 / -0.015 | -0.053 | +0.000 | yes |
| w=40/35/25 | +0.006 | -0.000 | -0.015 | +0.006 | -0.062 | +0.001 / +0.027 | -0.071 | -0.031 | no |
| w=50/30/20 | +0.009 | +0.075 | -0.016 | +0.009 | -0.023 | +0.011 / +0.045 | -0.007 | -0.055 | yes |

V3 absolute values for reference. Logret: F540 0.314, F1095 0.567, U540 0.132, U1095 0.116. p10: -0.348, -0.083, -0.595, -0.688. all30 basket lr: U540 0.253, U1095 0.437.


##### q4_spike_md
### Q4. Spike order: how big, where, and how to quantify it

**Bottom line.** The spike order is a small, positive and lumpy add-on. **Keep 7.5% of the coin budget at -60% below the anchor, selling everything at +40%.**
- In the sensitivity grid, sizes above 7.5% look better, but nearly all the gain comes from windows containing the 2025-02-03 / 2025-10-10 crashes (and 2021 starts). In windows without those crashes the gain is about zero (universe) or negative (Focus H540). That fails your "never adopt something that only works in one period" rule.
- In a survivorship-free universe check, 21% of spike fills never recover, with a median mark of -83%. That halves the edge per fill compared with the focus coins.

**1. Event study** ("focus" = spike_events.csv: 9 focus coins, full history, 1h bars. "universe" = a new check: 138 symbols that were ever in the PIT top-30, one V3 path each on daily bars from first top-30 entry to end of data or delisting)

| metric | focus | universe |
|---|---|---|
| coin-years / fills | 40.7 / 54 | 624.8 / 586 |
| **fills per coin-year** | **1.33** (by coin: 0.33 NEAR to 2.80 TAO) | **0.94** (before 2024: 1.15; 2024-26: 0.74) |
| closed trades | 49 (90.7%) | 465 (79.4%) |
| closed return, gross (sell/buy - 1) | mean +41.75%, median +40.0%, max +76.3% | - |
| closed return, net of 2 x 0.1% fee | mean +41.46%, median +39.72% | mean +40.41% |
| closed above the +40% target | 4 fills, all on 2025-10-10, sold at the next 1h bar's open: TAO +76.3%, LINK +66.0%, PENDLE +55.6%, AAVE +47.8% | - |
| days held (closed) | median 16.7, mean 90.7, p25 4.1, p75 47.5, p90 159.7, max 966 | median 35.0, p75 93.0, p90 179.6 |
| still open at end | 5 (9.3%), mark mean -15.4%, median -20.0% | 121 (20.6%), mark mean -68.8%, median -83.3%. 21 of these are on delisted symbols (LUNA -100%, FTT -98.9%) |
| wick share (fill-day daily close at least 1.15 x fill price) | 25.9% (14 of 54) | 14.2% |
| **expected value per fill (in stake units)** | **+0.362** | **+0.179** |
| **P&L per coin-year (stake units)** | +0.480, i.e. **3.6% of coin budget per year** at 7.5% size | +0.168, i.e. **1.26% per year** at 7.5% |

**Focus coins in detail**

| coin | fills | closed | open | fills per year | wick share | median days held |
|---|---|---|---|---|---|---|
| AAVE | 8 | 7 | 1 | 1.33 | 0.25 | 35.3 |
| HYPE | 3 | 3 | 0 | 1.58 | 0.00 | 11.0 |
| LINK | 11 | 11 | 0 | 1.43 | 0.27 | 11.7 |
| NEAR | 2 | 1 | 1 | 0.33 | 0.00 | 85.7 |
| PENDLE | 5 | 4 | 1 | 1.52 | 0.40 | 27.5 |
| RENDER | 7 | 6 | 1 | 1.43 | 0.14 | 16.7 |
| TAO | 7 | 7 | 0 | 2.80 | 0.43 | 18.5 |
| UNI | 10 | 10 | 0 | 1.64 | 0.30 | 11.8 |
| ZRO | 1 | 0 | 1 | 0.43 | 0.00 | - |

- **Open lots (marked to market):** AAVE 2025-11-21 +15.5%, PENDLE 2025-11-21 +6.5%, NEAR 2022-05-11 -20.0%, ZRO 2025-02-02 -27.9%, RENDER 2025-02-03 -50.9%.
- **Holding-time buckets (closed trades):** up to 1 day 8; 1-7 days 9; 7-30 days 14; 30-90 days 11; 90-365 days 3; over 365 days 4. The four longest are all 2022 fills held through the bear market: AAVE 966 d, UNI 774 d, LINK 770 d, RENDER 653 d.
- **Wick fills recycle fast:** median hold 0.88 days, vs 21.4 days for non-wick fills.

**Fills by year**

| year | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|
| focus fills (wicks) | 1 (1) | 4 (1) | 7 (2) | 8 (0) | 0 | 9 (1) | 20 (9) | 5 (0) |
| universe fills | 21 | 58 | 147 | 106 | 18 | 87 | 129 | 20 |
| universe fills still open | 0 | 0 | 11 | **44** | 1 | 6 | **51** | 8 |

In the universe, 41.5% of 2022 fills never recovered by the end of 2026. 39.5% of 2025 fills are still open, though those are not final.

**Concentration.** On 8 dates, two or more focus coins filled on the same day:
- 2021-05-23: 4 coins
- 2022-01-21/22: 2 + 2 coins
- 2024-08-04: 2 coins
- 2025-02-03: 4 coins
- 2025-10-10: 5 coins
- 2025-11-21: 2 coins
- 2026-01-31: 2 coins

2025-10-10 alone produced 2.84 of the 19.55 stake units of total focus spike P&L (14.5%). 2021-05-23 produced another 1.59.
- Before 2024: 20 fills, 7.35 units over about 17.3 coin-years (0.42 per coin-year).
- 2024-26: 34 fills, 12.20 units over about 23.4 coin-years (0.52 per coin-year).
- In the universe it reverses: 0.226 per coin-year before 2024 vs 0.112 in 2024-26.

**2. Sensitivity grid.** Δ vs V3 (size 0.075, depth 0.60, TP 0.40). F = focus, U = universe. "X" = H1095 windows starting before 2024 and ending in 2024 or later; H1095 has no OOS windows.

| variant | Δlr F540 | F1095 | U540 | U1095 | Δ all30 lr U540 / U1095 | worst Δp10 | Δ IS lr F540 / U540 | Δ OOS lr F540 / U540 | Δ IS lr F1095 / U1095 | Δ X lr F1095 / U1095 |
|---|---|---|---|---|---|---|---|---|---|---|
| size 0.00 | -0.031 | -0.031 | -0.009 | -0.011 | -0.010 / -0.008 | -0.006 | -0.007 / -0.004 | -0.057 / -0.024 | +0.011 / -0.002 | -0.040 / -0.018 |
| size 0.05 | -0.010 | -0.010 | -0.003 | -0.003 | -0.003 / -0.003 | -0.000 | -0.002 / -0.001 | -0.018 / -0.008 | +0.004 / -0.000 | -0.013 / -0.006 |
| size 0.10 | +0.009 | +0.009 | +0.002 | +0.003 | +0.003 / +0.003 | -0.001 | +0.002 / +0.001 | +0.017 / +0.007 | -0.004 / -0.000 | +0.012 / +0.005 |
| size 0.15 | +0.026 | +0.027 | +0.007 | +0.009 | +0.009 / +0.008 | +0.003 | +0.004 / +0.002 | +0.050 / +0.021 | -0.013 / -0.001 | +0.034 / +0.015 |
| size 0.20 | +0.042 | +0.042 | +0.010 | +0.013 | +0.015 / +0.013 | +0.005 | +0.006 / +0.003 | +0.080 / +0.033 | -0.022 / -0.003 | +0.055 / +0.024 |
| size 0.30 | +0.068 | +0.070 | +0.015 | +0.019 | +0.026 / +0.022 | +0.003 | +0.008 / +0.002 | **+0.135 / +0.056** | **-0.045 / -0.010** | +0.092 / +0.039 |
| depth 0.40 | -0.034 | -0.033 | -0.020 | -0.033 | -0.019 / -0.026 | -0.015 | -0.014 / -0.021 | -0.062 / -0.035 | -0.020 / -0.037 | -0.036 / -0.030 |
| depth 0.50 | -0.017 | -0.022 | -0.015 | -0.025 | -0.014 / -0.020 | -0.022 | +0.007 / -0.018 | -0.041 / -0.023 | +0.023 / -0.032 | -0.036 / -0.021 |
| depth 0.55 | -0.013 | -0.015 | -0.008 | -0.015 | -0.006 / -0.011 | -0.033 | +0.004 / -0.009 | -0.024 / -0.013 | +0.006 / -0.019 | -0.017 / -0.011 |
| depth 0.65 | -0.001 | -0.014 | +0.007 | +0.023 | +0.005 / +0.023 | -0.004 | +0.001 / +0.012 | -0.004 / +0.011 | +0.003 / +0.040 | -0.019 / +0.012 |
| depth 0.70 | -0.013 | -0.024 | +0.009 | +0.014 | +0.003 / +0.005 | -0.006 | +0.001 / +0.007 | -0.014 / +0.027 | -0.009 / +0.011 | -0.030 / +0.016 |
| depth 0.80 | -0.018 | -0.019 | +0.008 | +0.007 | -0.003 / -0.013 | +0.031 | +0.030 / +0.000 | -0.032 / +0.056 | +0.025 / -0.015 | -0.026 / +0.022 |
| tp 0.20 | -0.010 | -0.020 | +0.001 | +0.011 | -0.001 / +0.011 | -0.007 | -0.003 / +0.001 | -0.015 / +0.006 | -0.010 / +0.010 | -0.022 / +0.011 |
| tp 0.30 | -0.005 | -0.008 | +0.001 | +0.002 | +0.000 / -0.001 | +0.000 | -0.003 / +0.002 | -0.004 / +0.003 | -0.003 / +0.002 | -0.009 / +0.002 |
| tp 0.50 | -0.003 | -0.009 | -0.004 | -0.003 | -0.003 / -0.003 | -0.027 | +0.004 / -0.002 | -0.007 / -0.006 | +0.016 / -0.002 | -0.010 / -0.004 |
| tp 0.60 | +0.001 | -0.002 | -0.006 | -0.010 | -0.004 / -0.008 | -0.025 | -0.000 / -0.007 | -0.000 / -0.008 | +0.007 / -0.017 | +0.000 / -0.006 |
| tp 1.00 | -0.013 | -0.022 | -0.012 | -0.019 | -0.010 / -0.016 | -0.027 | -0.020 / -0.015 | -0.023 / -0.020 | -0.032 / -0.028 | -0.023 / -0.012 |

**3. Where the spike_size gains come from.** Mean Δln(1+ret) vs V3, split by what the window contains.

| variant / cell | windows containing 2025-10-10 | containing 2025-02-03 only | containing neither |
|---|---|---|---|
| size 0.30, F540 | +0.146 (n=101) | +0.107 (50) | **-0.030** (185) |
| size 0.30, U540 | +0.052 (180) | +0.052 (120) | **+0.002** (803) |
| size 0.30, F1095 | +0.139 (64) | +0.028 (43) | +0.041 (90) |
| size 0.30, U1095 | +0.043 (120) | +0.055 (90) | **+0.001** (344) |
| size 0.15, F540 / U540 | +0.055 / +0.019 | +0.040 / +0.019 | -0.009 / +0.002 |
| size 0.00, F540 / U540 | -0.063 / -0.022 | -0.045 / -0.022 | +0.007 / -0.004 |

By window start year, size 0.30:
- F540: 2019 -0.036, 2020 -0.029, 2021 +0.051, 2022 -0.031, 2023 -0.005, 2024 +0.127, 2025 +0.165.
- U540: -0.035, -0.015, +0.037, +0.014, +0.012, +0.055, +0.059.

**The gains are concentrated in OOS 2024-26, specifically in the 2025 crash windows.**

**4. How to quantify it**
- **EV per fill** = p_close x g - (1 - p_close) x L
  - Focus: 0.907 x 0.415 - 0.093 x 0.154 = **+0.362**.
  - Universe: 0.794 x 0.404 - 0.206 x 0.688 = **+0.179**.
- **Yearly contribution, as a share of coin budget** = size x fills per year x EV
  - Focus: 7.5% x 1.33 x 0.362 = 3.6% per year.
  - Universe: 7.5% x 0.94 x 0.179 = 1.26% per year.
  - Both are before the opportunity cost of the cash the ladder no longer gets.
- **Net of that opportunity cost** (from the grid), each extra 7.5 pp of size adds about +0.02 lr per window on focus and +0.004 to +0.008 on the universe. All of it comes from crash-containing windows.
- **Break-even stuck share** = g / (g + L) = 0.404 / (0.404 + 0.688) = **about 37%**.
  - Observed: 9% (focus) and 21% (universe).
  - But 2022 fills were 41.5% stuck, above break-even, so the edge disappears in a 2022-style bear market.
- **Downside per coin:** about size x 0.8-1.0 of the coin budget if the coin dies after the fill (universe marks reach -100% for LUNA and -98.9% for FTT).
- **Fills are correlated across coins:** on 2025-10-10, 5 of the 9 focus coins filled. The real crash-day exposure is size x the number of coins that fill on that date.

**Recommendation**
- **Size 7.5%** (acceptable band 5-10%; size 0 is worse in all four cells by -0.009 to -0.031). Do not raise it: the gain only works in one period and it raises dead-coin risk.
- **Depth 60%** (band 60-65%, with 70-80% borderline; 55% or shallower is worse in all four cells).
- **TP +40%** (band +30% to +60%; +100% is worse in all cells; +20% is slightly worse on focus).
- **Monitor live:** track pooled fills per coin-year, p_close, g, and the stuck share with its mark. Cut size if the trailing stuck share approaches about 35%.

CAVEATS:
- H1095 has no OOS windows (start >= 2024-01-01 plus 1095 days runs past the end of data, 2026-10). For H1095 I report IS (window ends before 2024) and 'X' (window starts before 2024 and ends in 2024 or later) instead. Focus H1095 IS has only 34 windows, mostly LINK.
- Focus scores weight coins equally, so HYPE (5 windows at H540, daily bars), ZRO (11) and TAO (13) count as much as LINK (77). Windows overlap heavily (steps of 30/60/90 days), so differences of about +-0.02 are within noise. No bootstrap confidence intervals were computed for the sensitivity variants.
- The plateau test in Q3 is my own definition: Δlogret >= -0.02 vs V3 in all four cells (one-sided, so improvements count) and worst Δp10 >= -0.03. Basket (all30) and IS/OOS deltas are reported separately and were not part of the test.
- Two engine runs were done beyond existing files. (1) A per-start-date breakdown of the existing 5-year universe result (V2/V3/V3 tail permanent/B&H, about 1,256 daily single-coin runs, 22 s, one process); its aggregates reproduce r2_longterm.txt exactly. (2) A universe spike-event study (138 symbols, one V3 path each on daily bars from first PIT top-30 entry to end of data or delisting). That path keeps trading a coin after it leaves the top 30, and marks delisted symbols at their last close with no haircut. Neither is in the repo.
- The 'V3 scaled to the same util' comparison in Q2 matches median time-average exposure (lab.metrics util). It is exact for returns (k x ret, cash earns 0%), but I did not compute its maxDD.
- Spike fills: 'wick' follows the definition in exp_longterm.py (fill-day daily close >= 1.15 x fill price). The four 2025-10-10 focus fills were sold at the next 1h bar's open, +48% to +76% above cost. That assumes resting orders were filled and the exchange worked normally during a flash crash; order-queue position is not modelled beyond a 0.05% penetration rule.
- Focus coins are a selected set of survivors, so the per-coin long-term multiples (and B&H in particular) are optimistic compared with the survivorship-free universe. Full-history results are one path per coin and depend heavily on the listing date. HYPE is 1.9 years of daily bars.
- Basket results come from equal-weight PIT liquidity-rank buckets with few independent start dates: 12 top-8 starts for the 5-year windows (2019-01 to 2021-09, all spanning the 2021 top), and 20 for H1095. The 'starts before 2021 vs 2021 or later' split is descriptive, not a statistical test.
- gap, gen_mult, d3 and w=20/30/50 are one lever. No joint grid was run and gap > 0.40 was not tested, so 0.40 and its interactions with other parameters are not validated.
- The 'about 17.3 / 23.4 focus coin-years before / after 2024' split assumes every coin's data ends around 2026-10 (data length minus 2.78 years). The universe coin-years per period were counted exactly from the bars.
- Another agent writes to the shared scratchpad r2wf/ and overwrote my first score.py there. All my scripts and CSVs are in /tmp/claude-0/-home-user-autonomous-spot-trading-agent/89a7c8d1-f045-5346-9127-ee553eb34b09/scratchpad/r2wf/qa4/ (score_sens.py, deltas.py, delta_all.csv, family_summary.csv, q1_*.py, u5y_baskets.csv, q2_scaled.py, q4_*.py, universe_spike_events.csv). No repository files were edited.
