---
name: market-regime
description: Classify BTC/USDT into exactly one V1 regime from structured, fresh market features; use before choosing a trading strategy.
---

# Market Regime

Read [the Constitution](../../references/trading-constitution.md) and [market structure](../../references/crypto-market-structure.md). Accept only fresh price, short/medium MA, MA slope, volume ratio, realized volatility, previous range, and risk-veto inputs.

Call deterministic `spot_agent.regime.detect_regime`. Return exactly one of `UPTREND`, `DOWNTREND`, `RANGE`, `BREAKOUT`, `PANIC`, `UNCERTAIN`, plus supporting evidence, opposing evidence, confidence, and reevaluation time. Never force a directional answer when inputs conflict.

