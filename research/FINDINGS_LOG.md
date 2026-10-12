# Findings log (working notes, appended as experiments finish)

Data: Binance spot daily for 680 USDT pairs incl. delisted (redenominations back-adjusted,
LUNA/VEN symbol reuse split); 1h for 14 focus symbols; HYPE daily = Hyperliquid spot
(Binance spot only since 2026-09-24), HYPE 1h = Binance USD-M perp.
Data reproduces the user's 180d/365d drawdown table to within 1pp.

## Baselines (focus coins, 540d windows, coin-equal)
V2 median +45%, p10 -59%, maxDD med 62%; B&H +18% / -74% / 73%; simple all-in ladder +28%/-70%.
365d and 1095d horizons same ordering. On PIT universe (survivorship-free) V2 median only +9%,
B&H -20%: focus-coin results are inflated by coin selection (survivors chosen with hindsight).

## Exp1 per-coin params
Uniform == group == per-coin OOS (IS-coins mean logret -0.019/-0.020/-0.017). V2's per-coin
ladders == uniform 7/18/30. d1,d2 nearly irrelevant; d3 depth matters (deeper better, monotone
to 0.40 within grid). Cross-coin OOS template rank corr ~0.9 except HYPE (negative; bull run).

## Execution realism
Daily(conservative buy-first) vs 1h: logret 0.107 vs 0.113, cycles 5.18 vs 5.35/yr: bias small.
Spike order value survives wick clipping (0.148 vs 0.156 vs no-spike 0.118). Fees 0.1%: -0.7pp/540d.

## Rules (IS<2024, OOS>=2024, all, universe all agree in sign)
+ gen gap 15-30% below B3 fill; + deeper d3 (0.35-0.40); + tail exit (+50..100% target or
trail 25-35% after +50%); + 4 gens > 3 > 2 at fixed gen-1 size; - remove spike hurts;
0 TP2-reanchor (remove), 0 weights 33/33/33 == 40/35/25, 0 TP1 level 20-40% flat,
- gen rebound wait, - half-size gen2. Drift: neutral but needed for engagement.
1095d: V2 logret 0.307 vs B&H 0.280 (permanent tail eats the edge); tail exits 0.45-0.57.

## Exp2 selection
Momentum/recovery/cycle-count features: IC ~0 or negative for forward strategy result.
top4 by mom365 -> fwd logret -0.20 vs random 0.00. Age & liquidity only positive predictors.
cycles365 buckets: 0-1 -> +0.40 fwd, 7+ -> -0.28: the "<2 cycles/yr -> replace" rule is backwards.

## Depth plateau (budget 4 units, eq weights, focus 1h + universe 1d)
g=3: logret flat across d3 0.30-0.40 x gap 0-0.3 (focus 0.244-0.269, universe 0.155-0.177);
deeper/gap mostly improves p10 (focus -0.40 -> -0.25; universe -0.59 -> -0.39).
Pick d=(7,17,35) gap=20% g=3: interior of plateau.

## Rules batch 2 (universe 540d)
K (eq w, 7/17/35, gap20, 3 gens, spike, no TP2-reanchor, permanent tail): logret 0.121 vs V2 0.009,
p10 -0.63 vs -0.76, maxdd med 0.51 vs 0.63, basket_p10 -0.40 vs -0.55, basket_med 0.25 vs 0.29.
pergen cost worse than pooled (0.089 vs 0.121; V2 -0.023 vs 0.009) -> keep pooled C.
anchor at C worse unless gap enlarged; stale180 small + (0.131, p10 -0.56); stale90 hurts median.
Spike: removing hurts (0.108); depth 60-70 / size 7.5-15% / tp 25-60% all similar -> robust.
Tail exits on K all beat permanent tail on logret, basket_med, basket_p10.

## Regime split (universe, ex-post labels)
strong_up 26% of windows, crash 31%. Permanent tail wins only in strong_up (K 1.64 vs t100 1.50 vs
tr50_30 1.38 median); exits win in slow_up, slow_bear, crash, V_rebound. No regime switch needed.

## Lineup 2024-12..2026-10 (actual 8 coins, 20%x4 core + 5%x4 sat)
B&H +152% (HYPE ~7x), V2 +96% maxDD 44%, K +70% maxDD 27%, exposure med 0.78 vs 0.47.
Max portfolio share newly filled in 1 day 13-17% (2025-10-10), 7 days 19-26%.
Pairwise corr 0.56 normal days -> 0.67 on BTC<-5% days; all 8 coins fall ~10-12% on those days.

## Base rates (Binance USDT spot)
29% of all USDT pairs ever listed are delisted/renamed; 11% within 2y of listing; 35% within 5y.
PIT top-30 liquid alts, 2y later: 5.6% delisted, 6.5% <= -90%, 16% <= -80%, 39% <= -50%, median -24%.
Cohort medians: 2019 +481%, 2020 +57%, 2021 -74%, 2022 +5%, 2023 -22%, 2024 -67%.

## Satellites (focus sats + universe)
S_v2 (V2 satellite rules) focus: med -10%, logret -0.21, p10 -0.71, maxDD 0.75, util 0.88;
K3 core rules on same coins: +34%, +0.21, -0.37, 0.43, util 0.47. Universe: S_v2 -0.111/-0.83 vs K3 0.132/-0.60.
All satellite rule variants (rebuy 5..20%, 1-3 tiers, sell 15..30%, tail 0..50%) within -0.08..-0.18 logret.
2-tier rebuy slightly better than 1-tier at the median (user's prior finding replicates) but irrelevant vs unification.

## Slow death / market filters (universe, V3 base)
Coin-level price rules (relweak, relweak2, idio_low, deep85) do not cut losses on coins that later died and
cost on survivors. pause_relweak cuts died-loss (-1.13 -> -0.80 logret) but survivors -0.11 -> net worse.
BTC<200dMA halt: logret +0.04..0.09 IS, ~+0.01 OOS (2024+), median lower; gains only from 2021-22 -> not adopted.

## Portfolio (PIT top-12, 36 starts, 540d)
core4 V3: med +43%, lr 0.290, p10 -26%, ddmed 26%, ddmax 56%; core4 V2: +65%, 0.441, -39%, 51%, 72%;
core4 B&H: +116%, 0.545, -66%, 64%, 88%. Adding 4 sats (5% each, same rules) 0.290 -> 0.276; with V2 sat rules p10 -0.33.
Lineup 2024-12..2026-10: V3 +67% maxDD 27% vs V2 +96%/44% vs B&H +152%/63% (HYPE 7x).

## Final validation (focus 1h, coin-equal)
H365 V3 0.208 vs V2 0.153, p10 -0.22 vs -0.49; boot dLR [-0.04,0.13], dP10 [0.19,0.28]
H540 0.314 vs 0.232, p10 -0.35 vs -0.59; boot dLR [-0.05,0.20], dP10 [0.20,0.31]
H1095 0.567 vs 0.307 (B&H 0.280), p10 -0.08 vs -0.43; boot dLR [0.15,0.38], dP10 [0.26,0.48]
IS(365, <2024) 0.163 vs 0.129; OOS(>=2024) 0.141 vs 0.029.
Walk-forward (universe, yearly reselect among 24 configs): WF -0.174, fixed V3 -0.129, V2 -0.313 mean test-year logret;
V3 > V2 in 4/5 test years.
Per coin 540d: V3 lowers median on AAVE/LINK/HYPE (strong coins) but halves p10; wins both on NEAR/RENDER/UNI/ZRO.

## Universe final + BTC filter on focus
Universe V3 vs V2: H365 0.072/-0.020, H540 0.132/0.009, H1095 0.091/-0.234 (boot [0.23,0.41]).
OOS 540: V3 -0.231, V2 -0.569, B&H -0.934. 2 gens beat 3 on generic alts over 3y (0.161 vs 0.091) but
3 gens beat 2 on the user's coins incl. satellites (sat+UNI 1095: 0.516 vs 0.350).
BTC200 halt on focus: ALL 0.203 vs 0.208, IS 0.194 vs 0.163, OOS 0.125 vs 0.141 -> not adopted.
Scenario (user coins, 365d, V3): gen1-only 7% (+33%), gen2 59% (+38%, p10 -4%), gen3 33% (-10%, p10 -48%).

## Tail regime exit (user follow-up: hold tail in bull, sell in bear)
Lookahead-free (independent audit). User's literal rule with BTC MA200: focus H540 -0.030 vs V3 (CI -0.052..-0.006),
H1095 -0.044; universe +0.032/+0.083 but ~0 without 2019-20 starts. R form not a plateau (MA150 vs MA200 3y diff 0.13-0.16);
R:btc_ma150 universe edge 79% from the single 2021-05-16 exit. Fast signals MA20/50/100 all ~ +0.03-0.04 on focus -> effect is
tail shortening; OOS 'no tail' ~ same gain (+0.058/+0.076 vs best +0.065/+0.083). Selection-adjusted (26 variants) RC/SPA
p 0.15-0.22 focus H540. Not adopted; record BTC vs MA100/MA200 at tail creation/sale for the 6-month review.
