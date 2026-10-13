"""Return accounting on the principal actually put in (round 3).

The engine keeps a per-coin sub-account that starts with the whole budget
B = 1 in cash. Three ways to state the result of the same run:

  ret_B    (final equity - 1) / 1          return on the whole budget, idle cash included
  ret_P    (final equity - 1) / P          return on the principal actually used:
           P = peak of (B - cash) over the run = the most outside money the
           strategy ever needed at once if cash were only transferred in when
           a buy fills. Profits that are re-deployed are not new principal.
  shadow   "same money, same days, never sell": every time the strategy needs
           new principal (P makes a new high) the same amount buys the coin at
           the strategy's own fill prices that day and is held to the end.
           shadow_ret = (final value of those coins - P) / P.

IRRs are money-weighted (dated injections, terminal value), annualised.
ret_B of buy-and-hold equals its ret_P (it uses the whole budget on day 1).
"""

from __future__ import annotations

import numpy as np

import engine as E


def _irr(flows: list[tuple[float, float]]) -> float:
    """flows: (years_from_start, amount); outflows negative. Annualised IRR by bisection."""
    if not flows or all(a <= 0 for _, a in flows) or all(a >= 0 for _, a in flows):
        return float("nan")

    def npv(r):
        return sum(a / (1 + r) ** t for t, a in flows)

    lo, hi = -0.9999, 100.0
    f_lo, f_hi = npv(lo), npv(hi)
    if f_lo * f_hi > 0:
        return float("nan")
    for _ in range(200):
        mid = (lo + hi) / 2
        f = npv(mid)
        if f_lo * f <= 0:
            hi = mid
        else:
            lo, f_lo = mid, f
        if hi - lo < 1e-7:
            break
    return (lo + hi) / 2


def principal_stats(r: dict, bars: E.Bars, fee: float = 0.001) -> dict:
    eq = r["equity"]
    days = r["days"]
    n = len(eq)
    yrs = max(n / 365.0, 1e-9)
    final_close = bars.c[np.where(bars.day_end)[0][-1]]
    if "cash_min" not in r:          # buy-and-hold / static mix: whole budget at t0
        bh_t = eq[-1] ** (1 / yrs) - 1 if eq[-1] > 0 else -1.0
        return {"P": 1.0, "ret_B": eq[-1] - 1, "ret_P": eq[-1] - 1, "irr": bh_t,
                "shadow_ret": eq[-1] - 1, "shadow_irr": bh_t, "worst_P": eq.min() - 1,
                "avg_drawn": 1.0, "edge_vs_shadow": 0.0}
    drawn = np.maximum.accumulate(np.maximum(1.0 - r["cash_min"], 0.0))
    P = float(drawn[-1])
    inc = np.diff(np.concatenate([[0.0], drawn]))
    # day -> volume-weighted strategy buy price
    day_of_bar = bars.t // E.DAY_MS
    px_usd: dict = {}
    for ev in r["events"]:
        if ev[1].startswith("buy_g") or ev[1] == "spike_buy":
            d = int(day_of_bar[ev[0]])
            usd = ev[3] if len(ev) > 3 else 0.0
            a = px_usd.setdefault(d, [0.0, 0.0])
            a[0] += usd
            a[1] += usd / ev[2]
    coins = 0.0
    flows = []
    for k in np.nonzero(inc > 1e-12)[0]:
        d = int(days[k])
        if d in px_usd and px_usd[d][1] > 0:
            vwap = px_usd[d][0] / px_usd[d][1]
        else:
            vwap = bars.c[np.where(bars.day_end)[0][k]]
        coins += inc[k] * (1 - fee) / vwap
        flows.append((k / 365.0, -inc[k]))
    shadow_final = coins * final_close
    profit = eq[-1] - 1.0
    term_t = (n - 1) / 365.0
    irr = _irr(flows + [(term_t, P + profit)]) if P > 1e-9 else float("nan")
    s_irr = _irr(flows + [(term_t, shadow_final)]) if P > 1e-9 else float("nan")
    return {
        "P": P,
        "ret_B": profit,
        "ret_P": profit / P if P > 1e-9 else 0.0,
        "irr": irr,
        "shadow_ret": shadow_final / P - 1 if P > 1e-9 else 0.0,
        "shadow_irr": s_irr,
        "worst_P": float((eq - 1.0).min() / P) if P > 1e-9 else 0.0,
        "avg_drawn": float(drawn.mean()),
        "edge_vs_shadow": (P + profit) / max(shadow_final, 1e-12) - 1 if P > 1e-9 else 0.0,
    }
