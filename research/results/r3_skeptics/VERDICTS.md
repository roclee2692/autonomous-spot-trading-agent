# Round 3: reviewer verdicts on V3.2 (10% tail at 5x vs V3.1's 25% at 2x)

Three independent reviewers each attacked the change from one angle. Their raw outputs are in this folder.

## A. Implementation and execution: SURVIVES

- **Hand trace (LINK 1h).** 40 take-profits produced 40 tail lots. Every lot is exactly 10% of the cycle quantity, and its C_lot equals the cycle C. The 22 lots that were sold all went at the first daily close at or above 5x C_lot. There is no look-ahead and no double counting.
- **Execution flags, universe.** With resting tail limits and fills at the limit price (`tail_intraday`, `fill_at_limit`), V3.2 minus V3.1 is still positive on basket log return at every horizon: +0.022, +0.038, +0.091 and +0.115.
- **Fees.** Raising fees to 0.2% does not hurt the edge.
- **Focus coins, 1h.** The edge is small and uneven. At H1095 it is driven by NEAR (−0.12) and RENDER (+0.13).
- **Per-coin p10 at 5 years** is slightly worse than V3.1 in every configuration.
- **Practical: order size.** At G = $200, tail lots cost $7–41 at creation and their 5x sell orders are at least $33. Open tail sells peak at 11–26 per coin, far below Binance's limit of 200. At G = $30 the 5x sells sit right at the $5 minimum notional, so satellites need G ≥ $50.
- **Practical: price band.** Binance's price band may reject a 5x sell when price is below C_lot. So the sell must be placed immediately when the lot is created, when price is about 1.25C, and never cancelled.

## B. Statistics and regime: WEAK

- **Not driven by a few coins.** V3.2 minus V3.1 basket gain stays positive after removing the top 5 coins (+0.010, +0.015, +0.052, +0.077). It also stays positive after leaving out any single start year.
- **Not just lower exposure.** V3.2 has less exposure and lower drawdown than V3.1. Against V3.1 scaled to the same drawdown, the basket edge grows.
- **Where the 5x target pays.** The 5x target pays off in windows that contain the 2020-11..2021-11 bull run. In 3-year windows without that bull run the gain is +0.004 (3 of 8 better). For starts after 2022 it is +0.002 at H1095 and +0.015 at H540.
- **Long-horizon tests carry little weight.** At 5 and 7 years there are only about 0.7 and 0.2 independent windows. The bootstrap "p = 0" values there are artifacts. The valid tests (H540 p = 0.29, H1095 p = 0.13) are not significant.

## C. Simpler alternatives and interactions: ADOPT V3.2

- **Both levers are needed.**
  - The 5x target brings the basket and long-horizon return; a 10% tail at 2x only matches V3.1.
  - The smaller share brings the drawdown and p10 gains; a 25% tail at 5x adds 7–8 points of drawdown.
- **A permanent tail** is clearly worse from 3 years on.
- **5% at 10x** is the closest challenger. It ties at 1.5–5 years with about 2 points less drawdown, but loses at 7 years (p10 −0.10) and over 10 years (log −0.23).
- **No tail** is the only simpler rule.
  - It has the lowest drawdown (−5 to −8 points).
  - It loses basket return: −0.12 at 5 years, −0.24 at 7 years, −0.92 over 10 years.
- **Interactions.** tp1 0.25, gap 0.40 and spike-on remain the best or second-best of 18 cells under every tail. V3.2's tail beats V3.1's in all 18 combinations.

## Decision

Adopt V3.2 at moderate confidence. Its gains are in basket return, drawdown and basket p10; the per-coin log return gain is not significant up to 5 years. The 5x target pays off only in long trending markets, and in sideways or bear periods it roughly ties V3.1. If drawdown matters more than 5-year-plus returns, no tail is the honest alternative.
