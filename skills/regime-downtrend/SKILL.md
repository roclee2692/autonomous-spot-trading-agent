---
name: regime-downtrend
description: Govern BTC spot capital preservation in a DOWNTREND and prevent dense grids or martingale buying.
---

# Downtrend

Read [the Constitution](../../references/trading-constitution.md). Stop ordinary Grid. Preserve Reserve and prohibit increasing order sizes such as `10 → 20 → 40`; any future Sparse Buy plan must use equal or decreasing sizes and pass the deterministic Risk Gate.

The V1 Stage 0 harness has no Sparse Buy execution planner. Return `NO_TRADE` until one is implemented, tested, and approved.

