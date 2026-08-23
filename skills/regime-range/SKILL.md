---
name: regime-range
description: Propose a low-frequency BTC/USDT spot grid only after a fresh RANGE classification and cost checks.
---

# Range

Read [the Constitution](../../references/trading-constitution.md). Confirm price remains inside the prior range, MA separation is small, volume is normal, data is fresh, and volatility covers costs.

Only then call `spot_agent.grid.build_stage2_grid`; never hand-calculate executable prices or sizes. Require gross spacing at least three times round-trip cost, retain Core BTC and USDT Reserve, prefer `LIMIT_MAKER`, and send every proposal through `RiskGate`. Leave RANGE, pause, or output `NO_TRADE` on breakout, panic, stale data, fee anomaly, or insufficient net edge.

