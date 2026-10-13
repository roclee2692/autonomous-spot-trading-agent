
=== VERDICT exposure refuted= False conf= 0.65
Lens tested: is the gain just from holding less coin? I compared gap=0.40 with V3 scaled down, k*V3 plus (1-k) in cash. Equity and position paths were regenerated for both variants. They reproduce the CSV ret, util and maxdd to 5e-7, and the basket returns to 6e-8. Windows were matched by coin or symbol and start_day. k was solved per cell to match seven statistics: median, mean and p90 util; median, mean and p90 maxdd; and p10 ret. I also did the same at basket level (all30 and top8 basket equity paths, with k matched to basket util and maxdd), ran a per-window matching that uses hindsight, ran a 180-day block bootstrap (B=2000), and swept k from 0.05 to 1.00 to check whether any scaled V3 dominates the proposal.

The claim's exposure numbers reproduce exactly. In the full sample the scaled V3 never matches or beats the proposal on mean logret: not in any of the 4 per-coin cells, not in any of the 4 basket cells, and not under any of the 7 matching statistics. No k from 0.05 to 1.00 makes k*V3 at least as good on logret and also on p10, median maxdd or p90 maxdd in any full-sample cell. The block bootstrap 5th percentile of the paired logret advantage is above 0 in F540, F1095, U1095 and in all four basket cells. So on my lens's own test (scaled V3 matches or beats it, then refute) the claim is not refuted at the full-sample level.

The weaknesses are real, which is why confidence is moderate.
(1) U540 per-coin is a statistical tie. The logret advantage over scaled V3 is only +0.009 to +0.012 under every matching, and the bootstrap 5-95% range includes 0 ([-0.012, +0.034] util-matched; [-0.020, +0.038] maxdd-matched).
(2) Much of the headline p10 gain over raw V3 is just lower exposure. Matched on median maxdd, the remaining p10 edge is: U1095 -0.003, about 100% explained by exposure; U540 +0.039, about 77% explained; F540 +0.065, about 57% explained; F1095 +0.298, about 6% explained. For the first three cells the bootstrap 5th percentile is at or below 0. At the same median maxdd, scaled V3 also has a lower worst-decile (p90) drawdown than the proposal (U1095 0.745 vs 0.831; U540 0.624 vs 0.646; F540 0.491 vs 0.506).
(3) Sub-periods. In U540 OOS, V3 held at k <= 0.71 per-coin (k <= 0.62 for the all30 basket) dominates the proposal on both logret and p10. In U1095 straddle windows, k <= 0.75 per-coin dominates on logret, p10 and drawdown. With maxdd matching, the per-coin universe advantage sits in pre-2024 windows: U1095 IS +0.171, straddle -0.0075.
(4) The focus advantage is concentrated in one coin, RENDER (F1095 per-coin logret over util-matched V3 is +0.44). At F540, HYPE (-0.039) and TAO (-0.005) do worse than util-matched V3. Under maxdd matching, 4 of 9 coins have a worse per-coin p10 (AAVE, HYPE, LINK, PENDLE).

The portfolio-level evidence holds up well, and the basket is what actually gets traded. The basket advantage over basket-matched V3 is positive in IS and OOS, with only n=9 straddle starts showing about 0. So it is not just holding less coin. But the claimed risk reduction should be read mostly as an exposure cut plus a modest efficiency gain, not as free p10.
NUMS: Proposal minus k*V3 (per-coin, full sample).
- Matched on median util: k = 0.816 / 0.784 / 0.824 / 0.797 (F540 / F1095 / U540 / U1095). Logret delta +0.0489 / +0.1971 / +0.0097 / +0.0674; bootstrap 5th pct +0.032 / +0.128 / -0.012 / +0.021. p10 delta +0.086 / +0.300 / +0.064 / +0.046.
- Matched on median maxdd: k = 0.757 / 0.753 / 0.781 / 0.725. Logret delta +0.062 / +0.210 / +0.0089 / +0.065; bootstrap 5th pct +0.044 / +0.144 / -0.020 / +0.010. p10 delta +0.065 / +0.298 / +0.039 / -0.0028; bootstrap 5th pct of the p10 delta -0.007 / +0.185 / -0.021 / -0.104.
- p90 maxdd at matched median maxdd, proposal vs scaled V3: F540 0.506 vs 0.491; U540 0.646 vs 0.624; U1095 0.831 vs 0.745.

Baskets (k matched on basket median util).
- all30: U540 +0.022 [0.0075, 0.040]; U1095 +0.095 [0.061, 0.129].
- top8: U540 +0.027 [0.012, 0.044]; U1095 +0.074 [0.042, 0.109].
- all30 with per-coin k, as in the claim: +0.0242 / +0.0914 (reproduced).
- Basket maxdd-matched, all30: U540 +0.026; U1095 +0.088.

Frontier sweep (k from 0.05 to 1.00).
- Full sample: no k dominates the proposal in any per-coin or basket cell.
- Sub-periods where scaled V3 dominates: U540 OOS per-coin (k 0.05-0.71 on logret and p10); U540 all30 OOS (k 0.05-0.62); U1095 straddle per-coin (k 0.05-0.75); U540 straddle (k = 0.82); F540 straddle (k 0.95-1.0).

Sub-periods, maxdd-matched per-coin logret delta: U540 IS +0.014, OOS -0.003, straddle +0.009; U1095 IS +0.171, straddle -0.0075 (p10 delta -0.0875).

Focus coins, util-matched per-coin logret delta: F1095 RENDER +0.44, LINK +0.046; F540 HYPE -0.039, TAO -0.005.

Files in /tmp/claude-0/-home-user-autonomous-spot-trading-agent/89a7c8d1-f045-5346-9127-ee553eb34b09/scratchpad/r2wf/skx/:
- Scripts: expo.py, frontier.py, frontier_basket.py, gen_paths.py
- CSVs: skx_percoin_matched.csv, skx_basket_matched.csv, skx_perwindow_matched.csv, skx_focus_bycoin.csv, skx_frontier.csv, skx_frontier_basket.csv
- Path files: paths_*_V3.npz and paths_*_gap0.40_mult1.0_spike0.075.npz

The repository is untouched.

=== VERDICT period refuted= False conf= 0.7
I checked the claim through the period and event lens, using only the depth CSVs (main grid plus ext). Windows were matched by coin/symbol and start_day. Scripts and output are in /tmp/claude-0/-home-user-autonomous-spot-trading-agent/89a7c8d1-f045-5346-9127-ee553eb34b09/scratchpad/r2wf/skeptic_period/: period_lens.py, period_lens.csv, period_lens2_out.txt and p3_raw.txt.

The core risk claim survives. The per-coin p10 gain does not depend on any one period.

1. **Dropping one start cohort at a time.** For gap 0.40, the per-coin dp10 stays positive in all 4 cells when I drop each of these: 2019-20 starts, 2021 starts, 2022 starts, 2023 starts, OOS (2024+) starts, or 2021+2022 together. Every gap 0.35 and 0.45 value is also positive. The smallest value for gap 0.40 is +0.065 (U540, drop 2021+2022).
2. **First and second half.** Every gap 0.40 value is positive. There is one negative value for the plateau edge: gap 0.35 in the first half of U1095 (10 start dates) is -0.016.
3. **Removing one crash episode.** Removing windows that contain 2021-05-19, LUNA/FTX, or 2025-10-10 leaves dp10 positive for gap 0.40. The range is +0.055 to +0.453. Removing the pairs 2021-05+LUNA/FTX or 2021-05+2025-10-10 also leaves it positive in all cells.
4. **Leave-one-out.** Leaving out one coin gives minimum dp10 of +0.117 (F540), +0.199 (F1095), +0.139 (U540) and +0.178 (U1095). Leaving out one 180-day start block gives minimums of +0.104, +0.275, +0.122 and +0.152.
5. **Within each start year.** dp10 is positive in 5 of 7 years for F540 and U540, and in all 5 years for F1095 and U1095.
6. **all30 basket p10.** It stays positive in almost every subset. The exceptions are U1095 with 2021+2022 dropped (-0.011, 12 start dates) and the bull-only subsets listed next.

dp10 turns negative only in subsets that contain no bear phase. In those subsets V3's own p10 is a gain, not a loss:
- F540 with no crash at all: -0.096 (V3 p10 +0.310).
- F540 with 2021 and OOS both dropped: -0.045 (V3 p10 +0.113).
- F540 straddle windows (2022-07 to 2023 starts): -0.104 (V3 p10 +0.299).
- F540 start years 2019 and 2023: -0.112 and -0.106.

So the risk gain shows up in every bear phase: 2021-top starts, 2022 starts, 2024-25 starts, and 2020 starts at H1095. It is not one episode. The cost is less upside in bull-start windows, which is consistent with the known cost already disclosed.

The weak part is the sentence "does not lower any of the 8 mean-logret metrics". On the full sample it rests on near-zero numbers (top8 H540 +0.00001, all30 H540 +0.001). It holds only because the 2021 start cohort is included: in that year gap 0.40 gains +0.18 lr per coin and +0.127 all30 at H540, while all30 lr is negative in 4 of 7 start years (2019 -0.069, 2020 -0.057, 2022 -0.006, 2023 -0.042).
- Dropping 2021 starts makes 4 of the 8 logret metrics negative: F540 -0.003, U540 all30 -0.021, U540 top8 -0.012, U1095 top8 -0.013.
- In the H540 straddle windows, all four H540 logret metrics are negative: F540 -0.022, U540 per-coin -0.041, all30 -0.048, top8 -0.042.
- Dropping OOS gives U540 all30 -0.011.
- Dropping LUNA/FTX windows gives U540 all30 -0.031 and U1095 top8 -0.029.

These flips are about -0.02, inside the ±0.02-0.03 plateau noise. Across leave-one-cohort-out, the all30 H540 delta runs from -0.021 to +0.034. That fits rule (B)'s "return about the same", but the literal "no logret lowered" statement does not hold up under the lens.

A factual correction to the rationale: H1095 has zero OOS windows (start >= 19723 plus 1095 days runs past the data). IS at H1095 is only 34 focus windows and 224 universe windows. "IS and OOS, both horizons" is therefore not true for H1095.

Verdict: not refuted on the p10 and risk claim. The logret-neutrality wording overstates things and depends on the 2021 cohort, but by small amounts.
NUMS: All values are gap0.40 minus V3.

**Per-coin dp10 (F540 / F1095 / U540 / U1095)**
| Subset | F540 | F1095 | U540 | U1095 |
|---|---|---|---|---|
| All | +0.150 | +0.318 | +0.169 | +0.186 |
| Drop 2019-20 | +0.147 | +0.275 | +0.136 | +0.131 |
| Drop 2021 | +0.156 | +0.445 | +0.108 | +0.168 |
| Drop 2022 | +0.146 | +0.346 | +0.160 | +0.130 |
| Drop OOS | +0.093 | (= all) | +0.161 | (= all) |
| OOS only | +0.147 | – | +0.175 | – |
| First half | +0.107 | +0.208 | +0.153 | +0.214 |
| Second half | +0.120 | +0.403 | +0.122 | +0.130 |
| No 2021-05 | +0.152 | +0.266 | +0.161 | +0.130 |
| No LUNA/FTX | +0.140 | +0.453 | +0.055 | +0.115 |
| No 2025-10-10 | +0.109 | +0.212 | +0.140 | +0.210 |
| Leave-one-coin-out min | +0.117 | +0.199 | +0.139 | +0.178 |
| Leave-one-180d-block-out min | +0.104 | +0.275 | +0.122 | +0.152 |

**Only negative per-coin dp10 (bull-only subsets)**
- F540 no-crash: -0.096 (V3 p10 +0.310)
- F540 drop 2021+OOS: -0.045 (V3 p10 +0.113)
- F540 straddle: -0.104 (V3 p10 +0.299)
- F540 start year 2019: -0.112; start year 2023: -0.106
- U540 no-crash: -0.014
- U540 straddle: -0.015
- Gap 0.35, U1095 first half: -0.016

**all30 basket dp10**
- All: +0.084 (H540) / +0.062 (H1095)
- Drop 2021: +0.061 / +0.008
- Drop 2021+2022: +0.076 / -0.011
- U540 straddle: -0.029

**Logret deltas when dropping the 2021 cohort**
- F540: -0.003
- U540 all30: -0.021
- U540 top8: -0.012
- U1095 top8: -0.013

**H540 straddle logret deltas**
- F540 per-coin: -0.022
- U540 per-coin: -0.041
- all30: -0.048
- top8: -0.042

**Within-year all30 lr, U540**
2019 -0.069, 2020 -0.057, 2021 +0.127, 2022 -0.006, 2023 -0.042, 2024 +0.035, 2025 +0.097.

**Coverage gap:** there are 0 OOS windows at H1095.

=== VERDICT sample refuted= False conf= 0.65
Verdict: the core claim survives my lens. It is that gap 0.40 raises p10 in all four cells and in all30, and that this is not just holding less. Several supporting statements are overstated, though, and should be reworded.

WHAT SURVIVES

1. None of the claim's own falsification triggers fired.
   - Gap 0.35 and 0.45 per-coin dp10 stay at +0.113 or more.
   - I re-ran with shifted window offsets: focus starts +15d, universe starts +30d at H540 and +45d at H1095. V3, gap 0.30, 0.35, 0.40 and 0.45, workers=2, outputs in r2wf/skmc/shift_*.csv. Gap 0.40 per-coin dp10 is F540 +0.109, F1095 +0.302, U540 +0.152, U1095 +0.140, and all30 dp10 is +0.076 (H540) and +0.089 (H1095). Every neighbour from 0.30 to 0.45 is also positive.
   - The p10 gains survive every trim and jackknife I tried. Dropping one 180-day block, dropping one start year, dropping V3's worst 5% or 10% of windows, and dropping the top 5% of |dlr| windows never turn a cell's dp10 negative. The minimum is +0.087 (F540, drop top-5% |dlr|).
   - Basket p10 jackknife over start dates has minimum +0.050 (top8 H540) and +0.005 (all30 H1095).
   - Leave-one-coin-out focus dp10 has minimum +0.117 (F540) and +0.199 (F1095).

2. Multiple comparisons do not inflate p10. 38 of 39 grid configs improve per-coin p10 in all 4 cells. Gap 0.40 ranks between 8th and 27th of 39 on the p10 deltas and sits below the grid median in F540, U540, U1095 and both all30 cells. The p10 gain is generic to buying deeper, not the maximum of a search.

3. The exposure-matched result holds at the shifted offsets. V3 scaled by the original k, with ret_k = k*ret exact, still trails: per-coin lr by +0.051 / +0.191 / +0.019 / +0.067, all30 by +0.034 / +0.093 and top8 by +0.035 / +0.072.

WHAT IS OVERSTATED OR NOT ROBUST

a) "Does not lower any of the 8 lr metrics" is a knife-edge, chosen after the fact.
   - In the gap family (mult 1, spike 0.075), 0.40 is the only value with all 8 deltas at zero or above. Gap 0.30 lowers at least one basket lr (min -0.004), 0.35 does too (min -0.007), and 0.45 is worse (-0.016).
   - Top8 H540: mean +0.0000 (t=0.00), median per-date delta -0.024, and gap 0.40 wins on only 15 of 39 dates. Dropping the best date gives -0.0048.
   - All30 H540: median -0.039, and dropping the best date gives -0.0028.
   - At the shifted offsets, top8 H1095 is -0.0073.
   - It should be restated as "basket lr roughly flat, -0.01 to +0.04".

b) The F1095 numbers are a local spike driven by RENDER and UNI.
   - RENDER at gap 0.40: dlr +0.366 and dp10 +0.789, against +0.083 / +0.149 at 0.35 and +0.115 / +0.254 at 0.45.
   - Without RENDER, F1095 becomes dlr +0.061 and dp10 +0.199.
   - The exposure-matched F1095 gap of +0.197 inherits this spike.
   - U540 per-coin lr against matched V3 is +0.010 only at 0.40. It is -0.012 at 0.30, -0.008 at 0.35 and +0.006 at 0.45.

c) Per-coin consistency in the focus sample is weak.
   - F540: 3 of 9 coins have negative dp10 (HYPE -0.293, TAO -0.087, PENDLE -0.017). 3 of 9 have negative dlr (HYPE -0.143, TAO -0.077, LINK -0.036). The median per-window delta is negative in 6 of 9 coins, and the pooled win rate is 44.9%.
   - LINK, the coin with the longest history, loses lr at every gap: from -0.014 down to -0.051 at H540. At H1095 it has dlr -0.057 and dp10 -0.087.
   - The F540 lr gain disappears under trimming: 10% trimmed mean +0.008, dropping the top 5% of |dlr| windows gives -0.0005, and dropping V3's worst 10% gives -0.011.

d) Universe per-symbol and rank buckets.
   - Among symbols with at least 10 windows, 45.5% at H540 (33 symbols) and 35% at H1095 (20 symbols) have negative mean dlr. 21% and 30% respectively have negative dp10.
   - U540 per-window median dlr is 0.0000 and the win rate is 46.5%.
   - The lr gain sits in ranks 9-30, not the top 8. At H1095 it is +0.042 for ranks 9-30 against +0.003 for top8. At the shifted offsets it is +0.058 against -0.007.
   - The p10 gain is smaller in top8: +0.061 / +0.023, against +0.114 / +0.070 for ranks 9-30.

e) The sample is small in independent terms. 39 start dates spaced 60 days apart for 540-day windows are about 4 non-overlapping windows. 20 dates spaced 90 days apart for 1095-day windows are about 2. The basket p10 at H1095 is roughly the 2nd-worst of 20 dates.

CONCLUSION

Under rule B (risk clearly down, return about the same) the change stands. But the "no lr lowered" claim, the F1095 magnitudes and the U540 per-coin exposure margin should not be quoted. Use the plateau averages for 0.35/0.40/0.45 instead: lr F540 +0.015, F1095 +0.061, U540 +0.027, U1095 +0.106; all30 -0.005 / +0.016; top8 -0.005 / -0.001.

Not computed: a shifted-offset run with full path-based util matching (I used fixed or ratio-based k), the bootstrap on the shifted runs, and offsets other than one half-step shift.
NUMS: Shifted offsets, gap 0.40:
- per-coin dp10: F540 +0.109, F1095 +0.302, U540 +0.152, U1095 +0.140
- all30: dp10 +0.076 / +0.089, dlr +0.016 / +0.037
- top8 dlr: +0.010 (H540), -0.0073 (H1095)

Gap family, minimum of the 8 lr deltas: 0.30 -0.004, 0.35 -0.007, 0.40 +0.000, 0.45 -0.016, 0.50 -0.052.

Configs that improve all 4 per-coin p10 cells: 38 of 39. Gap 0.40 p10 rank: 8th to 27th of 39.

Top8 H540 basket: mean +0.0000, median -0.024, wins 15 of 39 dates, -0.0048 after dropping the best date.

RENDER, F1095:
- gap 0.40: dlr +0.366, dp10 +0.789
- gap 0.35: +0.083 / +0.149
- gap 0.45: +0.115 / +0.254
- F1095 without RENDER: dlr +0.061, dp10 +0.199

Focus coins worse at gap 0.40:
- F540 negative dp10, 3 of 9: HYPE -0.293, TAO -0.087, PENDLE -0.017
- F540 negative dlr, 3 of 9: HYPE -0.143, TAO -0.077, LINK -0.036
- LINK F1095: dlr -0.057, dp10 -0.087

Universe symbols with at least 10 windows, share with dlr < 0: 45.5% (H540), 35% (H1095). Share with dp10 < 0: 21% and 30%.

Rank buckets, H1095 lr: ranks 9-30 +0.042, top8 +0.003.

Trimming, F540 lr: 10% trimmed mean +0.008; dropping V3's worst 10% of windows -0.011.

Jackknife minimum of dp10 by start year: F540 +0.093, F1095 +0.233, U540 +0.108, U1095 +0.130.

Util-matched U540 per-coin lr: 0.30 -0.012, 0.35 -0.008, 0.40 +0.010, 0.45 +0.006.

Scripts and outputs in /tmp/claude-0/-home-user-autonomous-spot-trading-agent/89a7c8d1-f045-5346-9127-ee553eb34b09/scratchpad/r2wf/skmc/: a1-a7*.py, shift_*.csv, shift_summary.csv.


######## REDTEAM

-- high | (a) Metric choice. The V3 decisions were scored mainly on per-coin, coin-equal mean ln(1+ret). The user's wealth is the sum of separate sub-accounts, which is an equal-weight basket with no rebalancing. Per-coin log returns punish per-coin variance that a basket partly diversifies away, so they favour lower-exposure rules.
CHECK: From sens_focus/sens_universe H540/H1095 I recomputed per-coin lr and basket lr (deltas vs V3) for 23 variants. The focus basket is crude: start days binned by 30 days, equal weight across the coins present. I also checked it with bins restricted to >=5 and >=7 coins, and cross-checked against the r2_scores top8/all30 columns and r2_portfolio. Script: scratchpad/r2wf/ana_existing.py (out_a.txt).
RESULT: V3 vs V2 flips at portfolio level at H540. Universe all30 basket: V2 0.266 vs V3 0.253 (V2 +0.013); top8: V2 +0.072. Per-coin the same comparison is V2 -0.123. Crude focus basket: V2 +0.101, but this depends on which bins are used: with >=5 coins V2 0.376 vs V3 0.345, and with >=7 coins (13 bins, all from 2024 on) V3 0.184 vs V2 0.013. At H1095 V3 still wins on all30 (+0.054) and on the focus basket (+0.181), but loses on top8 (V2 +0.135). Other sign flips, per-coin to basket: permanent tail at H540 goes from -0.028 to +0.032 (focus) and from -0.006 to +0.061 (universe). gen_mult=2 at H540 goes from +0.027 to -0.040 (focus) and from +0.003 to -0.013 (universe). tail_target=3.0 is positive at basket level at both horizons (+0.052/+0.028 at H540, +0.051/+0.020 at H1095). Some flips go in V3's favour: in the universe at H1095, per-coin lr says to drop gens/drift/roll (gens=1 +0.084, drift=none +0.026, roll=off +0.009), but the basket says keep them (-0.157, -0.103, -0.160).
OVERTURNS: It does not directly overturn a single V3 rule. Every basket-level flip toward more exposure (permanent tail, higher tail target, smaller tp_sell) is either period-dependent or just extra exposure; see (e). It does overturn the headline claim that V3 beats V2 at 1.5 years: at portfolio level the two tie. All future decisions should be scored on basket lr as well as per-coin lr.

-- high | (e) 'V3 is just less exposure'. The engine's alpha column, and any matching on per-window util, uses exposure observed after the fact. That util is high in down windows (the strategy bought every dip) and low in up windows, which makes the benchmark pessimistic.
CHECK: I checked corr(util, bh_ret) per window. I then matched exposure with a constant, decided-in-advance k: V2*k with k = mean util V3 / mean util V2, and bh*u with u = mean util of V3. I compared lr and p10 per coin and for the all30 basket, split into IS and OOS. Script: ana_existing.py e3 (out_e3.txt).
RESULT: Correlation of util with bh_ret is -0.39 for V3 vs -0.08 for V2 (focus H540), and -0.26 vs -0.09 (universe), so the alpha column is biased in V3's favour. With a constant k, the universe at H540 gives per-coin lr V3 0.132, V2*k 0.139 (k=0.66), bh*u 0.139 (u=0.47). The all30 basket gives V3 0.253, V2*k 0.259, bh*u 0.259. Per-coin p10 is V3 -0.595 vs bh*u -0.401, i.e. worse for V3. IS: V3 0.358 vs bh*u 0.431 (basket). OOS: V3 -0.114 vs -0.199. At H1095 a real edge remains. Universe basket: V3 0.437 vs V2*k 0.328 vs bh*u 0.404. Basket p10: V3 -0.077 vs -0.222 / -0.216. Per-coin: V3 0.116 vs 0.008 / 0.058, but per-coin p10 is still worse for V3 (-0.688 vs bh*u -0.506). In the focus sample V3's edge survives: H540 0.314 vs V2*k 0.222 vs bh*u 0.164; H1095 0.567 vs 0.261 vs 0.253.
OVERTURNS: It overturns the claim that V3's edge over V2 is structural at H540; in the survivorship-free universe it is entirely lower exposure. The structure earns its keep only at 3 years. No specific rule is reversed. It also shows a per-coin tail risk: averaging down 3 generations into a dying coin gives a worse single-coin p10 than a static mix at the same exposure. That supports gen_gap 0.40; see rules_to_change.

-- medium | (d) Period dependence: is V3's edge just a bet on alt bear markets? A related point: the coin-equal focus metric puts heavy weight on recent years because TAO, ZRO, HYPE and PENDLE only exist recently.
CHECK: I computed V3-V2 lr (per coin and basket) by window start year, focus and universe, H540 and H1095 (out_d.txt). I also computed the effective start-year weights of the coin-equal focus metric.
RESULT: Universe H540, V3-V2 per coin by start year: 2019 -0.357, 2020 -0.082, 2021 +0.460, 2022 +0.110, 2023 +0.096, 2024 +0.372, 2025 +0.239. Basket by year: -0.366, -0.371, +0.365, +0.030, +0.007, +0.248, +0.199; the equal-year mean is about +0.016. Universe H1095 basket: 2019 -0.253, 2020 -0.034, 2021 +0.308, 2022 +0.099, 2023 +0.284. The edge comes from windows starting in bear years (2021 and 2024-25), and V3 loses in windows starting 2019-20. It is not only a 2024-26 effect: the 2021 start cohort is as large. In the focus metric, 57.4% of the H540 weight sits on windows starting in 2024 or later.
OVERTURNS: It does not overturn a rule. It does overturn the claim that V3 is better in every regime. V3 is a lower-beta trade-off that gives up 0.3-0.4 lr in bull-start windows. Also, the 'OOS' split (start >= 2024) is one bear regime, and V3 was designed on the full sample, so it is not a holdout.

-- medium | (b) Compounding convention. The engine sets G = free cash / 3 at every new cycle, so profits compound. A human might keep G fixed in dollars instead.
CHECK: I copied the engine to scratchpad/r2wf/engine_mod.py and added fixed_budget, where cycle budget = min(initial, cash) and the spike buy = min(spike cash, 7.5%). I checked the copy is bit-identical to the original with the new flags off. I then reran V2 and V3 on all 9 focus coins (H540 and H1095, step 30) and on the full PIT universe (H540 step 60, H1095 step 90), with workers=2. Script: run_mod.py (out_mod_focus.txt, out_mod_universe.txt).
RESULT: V3 > V2 per coin survives with a fixed G. Paired V3-V2 lr: focus H540 +0.055 (compounding: +0.082), focus H1095 +0.242 (+0.260), universe H540 +0.102 (+0.123), universe H1095 +0.403 (+0.313). Fixing G hurts V3 more than V2: focus H540 V3 -0.038 vs V2 -0.010 per coin, and on the crude focus basket V3 0.526 -> 0.431 vs V2 0.627 -> 0.621. On the universe all30 basket at H540, V2's lead grows from +0.013 to +0.050 (V2fixG 0.267 vs V3fixG 0.217). At H1095 V3 keeps its basket lead (0.431 vs 0.384). Fixed G mostly lowers V3's utilisation (universe H1095 0.41 vs 0.58), with lower drawdown and a flat basket lr.
OVERTURNS: No. It does show that the 'new G = available cash / 3' (roll profits) rule matters more for V3 than for V2, so the doc should state it as mandatory.

-- low | (f) Spike-order gains might be concentrated in the 2025-10-10 crash wick. The engine also fills a spike sell at the next bar's open when that open is above the +40% target.
CHECK: From spike_events.csv I computed P&L by year, the share from 2025-10-10, and the result with sells capped at +40%. From the sens files I computed the gain from the spike (V3 minus spike_size=0, and the larger sizes) by start year, and for windows that do or do not contain 2025-10-10. I reran with fill_at_limit in engine_mod.
RESULT: 2025 accounts for 34% of summed spike-event returns (20 of 54 fills). 2025-10-10 alone is 14.5% (5 fills). Four of those sold at 1.48-1.76x instead of 1.40x; capped at 1.40x, their returns sum to 1.986 instead of 2.841 (total over all events: 18.695 vs 19.55). Per-coin lr gain from the spike, focus H540: +0.068 in windows containing 2025-10-10 vs +0.004 in the others. Universe: +0.022 vs +0.006. A larger spike (0.15 or 0.30) outside those windows adds only +0.0025/+0.003 (focus) and +0.004/+0.008 (universe). Under fill-at-limit the spike's value is focus +0.027 (was +0.031) and universe +0.009 (unchanged at H540), +0.014 at H1095. Spike is negative in windows starting 2019-20 (-0.01 to -0.03).
OVERTURNS: No for keeping the 7.5% spike: it is small, positive outside the crash, and spread across 2020-2026. Yes against any proposal to enlarge it: the gains from a bigger spike are almost all one event.

-- low | (c) The engine models the tail exit at daily close >= 2C, sold at the close. The strategy doc specifies a resting limit sell at 2C.
CHECK: I added tail_intraday to engine_mod: a resting limit sell at (1+x)C, filled intrabar from the next bar. I compared V3tailLimit with V3 on focus and universe at H540 and H1095.
RESULT: Paired per-coin lr: focus H540 +0.006, focus H1095 +0.032, universe H540 -0.010, universe H1095 -0.001. Basket lr: focus 0.524 vs 0.526; universe 0.250 vs 0.253 (H540) and 0.443 vs 0.437 (H1095). Median DD moves slightly lower (for example focus H540 0.359 vs 0.390).
OVERTURNS: No. The two are equivalent within noise, so keep the resting 2C order the doc already specifies, which is simpler.

-- medium | (g1) Bootstrap confidence intervals in REPORT_V3 use 180-day blocks on 540/1095-day windows. Overlapping windows break block independence, so the CIs are too narrow.
CHECK: I redid the V3-V2 block bootstrap with blocks of 180 days, H and 2H.
RESULT: With block = H there are only 5 blocks at H540 and 2 at H1095; with 2H there are 3 and 1. At H1095 two blocks cannot give a valid CI. The reported 'V3-V2 +0.15 to +0.38' (focus H1095) reflects about 2 independent periods. At H540 the CI includes zero for every block length (universe, block 540: -0.085 to +0.246).
OVERTURNS: No rule is overturned. Confidence labels should be downgraded: the H1095 V3>V2 evidence rests on about 2 independent periods per coin.

-- low | (g2) Fill-price convention: when an order created in the previous bar is gapped through, the fill is at the open. Buys get a lower price and sells a higher one, which flatters wick and gap trades, especially on daily universe bars.
CHECK: I added fill_at_limit to engine_mod (every fill at the exact limit price, a conservative bound) for V2 and V3, on focus and universe.
RESULT: V3 changes by -0.003 (focus H540), -0.003 (focus H1095), -0.015 (universe H540) and -0.022 (universe H1095). V2 changes by -0.0035, -0.003, -0.015 and -0.018. V3-V2 is unchanged: 0.082 -> 0.082, 0.260 -> 0.260, 0.123 -> 0.123, 0.313 -> 0.309.
OVERTURNS: No. The effect is symmetric and small.

-- low | (g3) Other code-level asymmetries in engine.py and runner.py.
CHECK: I read run_core, the runner, lab.metrics and the PIT universe code. I checked the universe for stablecoins and leveraged tokens (138 symbols; none found except USTC with 2 windows).
RESULT: Three things lean slightly toward V2, so they are conservative for V3. First, a V2 TP2 lot created in a bar can fill in that same bar. Second, the final mark-to-market has no exit fee or slippage, and V2 holds more inventory at the end. Third, the 'V2' baseline runs core rules on the satellite coins, which is better than real V2's satellite rules per REPORT_V3. The delisting haircut is only 10% and applies to both. I found no look-ahead in the PIT selection.
OVERTURNS: No.

-- medium | (e2) 'Put money deeper' signals (gen_gap 0.3-0.4, gen_mult 1.5-2, d3 0.45) lower utilisation, so their better p10 could be exposure alone. gap=0.4 was also at the edge of the tested grid.
CHECK: I compared each variant with V3 scaled to the same mean util (constant k), per coin and as a universe basket, IS and OOS. I extended the grid to gap 0.5 and 0.6 with new runs: run_gap.py (out_gap.txt), plus ana_existing.py e2/e4.
RESULT: gap=0.4 beats exposure-matched V3 in every cell. Per coin: universe +0.010 (H540) and +0.072 (H1095); focus +0.045 and +0.191. Universe basket: +0.022 and +0.076. Universe H540 IS +0.015, OOS +0.015. Absolute basket lr vs V3 is +0.001 (H540) and +0.030 (H1095). Basket p10 goes from -0.348 to -0.263 at H540; per-coin p10 from -0.595 to -0.425. gap 0.5 and 0.6 still beat matched V3, but absolute basket lr falls (-0.017/-0.032 at H540, -0.022/-0.057 at H1095), so the plateau is 0.3-0.5. gen_mult=2 is no better than scaled V3 per coin in the universe (H540 lr 0.135 vs 0.157; p10 -0.494 vs -0.472), and on the basket it is only +0.014 (H540). d3=0.45 is worse than matched V3 on the basket (0.225 vs 0.235).
OVERTURNS: It supports changing gen_gap from 0.20 to 0.40. It rejects gen_mult>1 and d3=0.45: those are mostly lower exposure.

SURVIVE: ['Ladder -7/-17/-35% with equal thirds: no robust alternative at basket level. d3=0.29 helps the focus basket but not the universe; d3=0.45 is worse than V3 at the same exposure.', 'TP = 1.25C selling 75%, with the remaining 25% as a tail. tp_sell=1.0 (no tail) is worse at basket level: universe all30 -0.018 (H540) and -0.020 (H1095), crude focus basket -0.065 (H540). tp_sell=0.5 helps only the H540 focus basket.', 'Tail exit at 2C. A permanent tail or a 4C target only adds exposure and depends on the period: permanent tail at H540 IS +0.113 / OOS -0.019 vs matched V3, and at H1095 it loses (basket 0.404 vs 0.437 for V3, or 0.485 for V3 scaled up). A resting limit at 2C is equivalent to the daily-close check (paired per-coin lr within -0.010 to +0.032) and is simpler.', 'Roll on TP fill, and the drift re-anchor at 1.2A. Both are strongly supported at basket level (universe H1095: roll=off -0.160, drift=none -0.103), even where per-coin lr disagrees.', '3 generations with pooled C. gens=1 or 2 lose at basket level (H1095 -0.157 / -0.063).', "G = available cash / 3 at each new cycle (profits roll). This is load-bearing: a fixed G cuts V3 by about 0.04 per coin in focus H540 and widens V2's basket lead at H540. Keep it and state it as mandatory.", 'Spike order at 7.5% of budget, -60%, sold at +40%. It is kept but low-confidence: value is +0.004 to +0.006 per coin outside windows containing 2025-10-10, and +0.009 to +0.031 overall. It survives fill-at-limit.', 'Uniform parameters across coins. Nothing tested here contradicts this.', 'V3 over V2 on a 3-year horizon. It survives a fixed G, fill-at-limit, the basket metric (all30 +0.054) and exposure matching (all30 +0.109 vs V2*k, +0.033 vs B&H at the same exposure). The confidence interval is overstated: about 2 independent periods.']

CHANGE: ["gen_gap 0.20 -> 0.40 (plateau 0.3-0.5). Under the user's rules B/D: it beats V3 scaled to the same exposure in all 8 cells (focus/universe, H540/H1095, per-coin and basket), in both IS and OOS. Basket lr is flat or better (+0.001 / +0.030), universe per-coin p10 goes from -0.595 to -0.425, basket p10 from -0.348 to -0.263, and median DD from 0.392 to 0.338. Complexity is unchanged (one number). Side effect: gen-2 orders sit at about -64/-68/-75% and gen 3 at about -86 to -90%, so gen 3 rarely fills and roughly 16% less capital is deployed on average.", 'Do NOT adopt gen_mult 1.5-2 or a larger spike. gen_mult is no better than V3 at the same exposure in the universe. The gain from a larger spike comes almost entirely from windows containing 2025-10-10.', "Evaluation and claims, not trading rules. (1) Score decisions on basket lr (the sum of sub-accounts) as well as per-coin lr. (2) Drop or rebuild the alpha column with a constant exposure k; the after-the-fact util benchmark favours V3. (3) Restate the V2 comparison: at 1.5 years in the unbiased universe, V3 equals a 47% B&H / 53% cash mix and an exposure-matched V2 (basket lr 0.253 vs 0.259 / 0.259). V3's structural edge shows only at 3 years, and V3 underperforms in windows that start in bull years (2019-20). (4) Use bootstrap blocks at least as long as the horizon, and say H1095 has about 2 independent periods. (5) Stop calling start >= 2024 'OOS'; it is one bear regime that the design already saw."]
