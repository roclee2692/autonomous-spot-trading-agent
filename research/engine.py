"""Backtest engines for the core and satellite spot-volatility strategies.

Bar-level event simulation on OHLC arrays (1h or 1d). Every order is a resting
limit order. Conventions (all chosen to be conservative):

* A buy limit at P fills when bar low <= P * (1 - pen); fill price is
  min(P, open) (an order placed above the market fills at the open).
  Sells mirror this. Fee is charged on every fill.
* Orders created by a fill (new take-profits, a new ladder, the next
  generation) only become active on the NEXT bar. So a bar can never buy
  and then sell the same lot, whatever the true intrabar path was.
* When an active-cycle buy and the active-cycle take-profit could both fill
  in the same bar, the buy is processed and the take-profit is skipped
  ("buy first"). This under-counts cycles on daily bars; 1h bars are used to
  measure how much.
* Slow decisions (drift re-anchor, tail exits, risk filters) are evaluated on
  daily closes only, matching a once-a-day human check.

Money is tracked in USDT. The sub-account starts with cash = 1.0; every
result is therefore a return on the coin's whole allocated budget, idle cash
included.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
import math

import numpy as np

DAY_MS = 86_400_000


# --------------------------------------------------------------------------
# market data container
# --------------------------------------------------------------------------
@dataclass
class Bars:
    t: np.ndarray       # open time ms (int64)
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    day_end: np.ndarray  # bool: last bar of a UTC day
    name: str = ""

    def __len__(self) -> int:
        return len(self.t)

    def slice(self, i0: int, i1: int) -> "Bars":
        return Bars(self.t[i0:i1], self.o[i0:i1], self.h[i0:i1], self.l[i0:i1],
                    self.c[i0:i1], self.day_end[i0:i1], self.name)


def make_bars(t, o, h, l, c, name="") -> Bars:
    t = np.asarray(t, dtype=np.int64)
    day = t // DAY_MS
    day_end = np.empty(len(t), dtype=bool)
    day_end[:-1] = day[1:] != day[:-1]
    day_end[-1] = True
    return Bars(t, np.asarray(o, float), np.asarray(h, float), np.asarray(l, float),
                np.asarray(c, float), day_end, name)


# --------------------------------------------------------------------------
# core strategy
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class CoreParams:
    d: tuple = (0.07, 0.17, 0.29)        # gen-1 ladder offsets below anchor
    w: tuple = (0.40, 0.35, 0.25)        # ladder weights
    tp1: float = 0.25                    # TP1 = (1+tp1) * C
    tp1_frac: float = 0.50               # share of cycle position sold at TP1
    tp2: float = 0.50                    # TP2 = (1+tp2) * C
    tp2_frac: float = 0.25               # share of cycle position sold at TP2
    roll: bool = True                    # TP1 fill -> new cycle anchored at TP1 price
    tp2_reanchor: bool = True            # TP2 fill raises an unfilled new ladder
    drift: float | None = 0.20           # re-anchor if no fill and close >= A*(1+drift)
    max_gens: int = 2                    # generations per cycle (1 = stop after B3)
    gen_d: tuple | None = None           # ladder for gens >= 2 (None -> d)
    gen_w: tuple | None = None           # weights for gens >= 2 (None -> w)
    gen_gap: float = 0.0                 # next-gen anchor = B3 fill * (1 - gen_gap)
    gen_mult: float = 1.0                # size of each extra gen vs gen-1
    gen_rebound: float | None = None     # arm next gen only after +x% bounce off low
    tail_exit: tuple = ("none",)         # see _tail_should_sell
    spike_frac: float = 0.0              # budget share for the -60% wick order
    spike_depth: float = 0.60
    spike_tp: float = 0.40
    fee: float = 0.001
    pen: float = 0.0005
    budget_units: float | None = None    # gen-1 size = cash / units (None: 1+gen_mult*(gens-1))
    cost_mode: str = "pooled"            # "pooled": one C per cycle; "pergen": C and TPs per generation
    gen_anchor: str = "b3"               # next-gen anchor: "b3" fill price or "cost" (cycle C)
    stale_days: int | None = None        # cycle open & underwater this long -> drop deeper gens
    fixed_g: float | None = None         # fixed gen size (share of the initial budget) instead of cash/units
    fill_at_limit: bool = False          # conservative: limits fill at the limit even if the bar opened through it
    tail_intraday: bool = False          # ("target", x) tail = resting limit sell at (1+x)C_lot from the next bar
    tail_tiers: tuple | None = None      # ((share of cycle qty, multiple), ...): layered tail lots, each sold at multiple x C


@dataclass
class Lot:
    qty: float
    cost: float          # USDT cost basis of this lot
    t0: int              # creation bar index
    peak: float = 0.0    # for trailing exits
    armed: bool = False
    exit_next: bool = False  # regime exit decided at a daily close, executed next bar open
    target: float | None = None  # per-lot ("target", x) override for layered tails


@dataclass
class CoreState:
    cash: float = 1.0
    anchor: float = 0.0
    locked: bool = False
    gen: int = 1
    gen_low: float = math.inf          # low since last B3 (gen_rebound)
    pending_gen: tuple | None = None   # (anchor) waiting for rebound
    buys: list = field(default_factory=list)   # [price, usd, gen, is_last_of_gen]
    cyc_qty: float = 0.0
    cyc_cost: float = 0.0
    tp2_lots: list = field(default_factory=list)  # [price, qty, cost]
    tail: list = field(default_factory=list)      # Lot
    spike: list = field(default_factory=list)     # [price, usd] buy or ('sell', price, qty, cost)
    spike_pos: list = field(default_factory=list)  # [sell_price, qty, cost]
    cycle_budget: float = 0.0
    groups: dict = field(default_factory=dict)    # gen -> [qty, cost]
    cycle_t0: int = -1
    stale: bool = False


def _ladder(anchor: float, d: tuple, w: tuple, usd: float, gen: int) -> list:
    out = []
    for i, (di, wi) in enumerate(zip(d, w)):
        out.append([anchor * (1 - di), usd * wi, gen, i == len(d) - 1])
    return out


def run_core(bars: Bars, p: CoreParams, ctx: dict | None = None) -> dict:
    """Simulate the core strategy on one coin.

    ctx (optional) carries exogenous daily filters decided from information
    available at that day's close:
      ctx['halt_days']  set of UTC day numbers on which no NEW generation /
                        cycle may be armed (existing orders stay).
      ctx['pause_days'] set of day numbers on which all unfilled buys are
                        cancelled and nothing new is armed (PAUSED).
    """
    n = len(bars)
    o, h, l, c, de = bars.o, bars.h, bars.l, bars.c, bars.day_end
    fee, pen = p.fee, p.pen
    s = CoreState()
    spike_cash = p.spike_frac
    s.cash = 1.0 - spike_cash
    units = p.budget_units or (1.0 + p.gen_mult * (p.max_gens - 1))
    gen_d = p.gen_d or p.d
    halt_days = (ctx or {}).get("halt_days", ())
    pause_days = (ctx or {}).get("pause_days", ())
    bear_days = (ctx or {}).get("bear_days", ())   # tail regime filter (decided at close)

    eq_days, eq_vals, pos_vals, pos_costs, cyc_pnl, cyc_cost_log = [], [], [], [], [], []
    pend_log, cash_log, cash_min_log = [], [], []
    day_cash_min = math.inf
    n_buys = n_sells = 0
    tp1_count = 0
    fees_paid = 0.0
    max_gen_seen = 1
    tail_realized = 0.0
    events = []
    waiting = None          # None | "noroll" | "halt"

    def new_cycle(anchor: float) -> None:
        nonlocal waiting
        waiting = None
        s.anchor = anchor
        s.locked = False
        s.gen = 1
        s.pending_gen = None
        s.gen_low = math.inf
        s.cycle_budget = p.fixed_g * units if p.fixed_g else max(s.cash, 0.0)
        s.stale = False
        s.cycle_t0 = -1
        s.buys = _ladder(anchor, p.d, p.w, s.cycle_budget / units, 1)

    def spawn_gen(anchor: float) -> None:
        s.gen += 1
        s.buys.extend(_ladder(anchor, gen_d, p.gen_w or p.w, s.cycle_budget / units * p.gen_mult, s.gen))

    new_cycle(o[0])
    spike_order = o[0] * (1 - p.spike_depth) if spike_cash > 0 else None

    deferred: list = []
    for i in range(n):
        oi, hi, li, ci = o[i], h[i], l[i], c[i]
        day = int(bars.t[i] // DAY_MS)
        halted = day in halt_days or day in pause_days
        # ---- 0. tail lots flagged by a regime exit at the previous close sell at this open
        if s.tail and any(t.exit_next for t in s.tail):
            keep = []
            for lot in s.tail:
                if lot.exit_next:
                    s.cash += lot.qty * oi * (1 - fee)
                    fees_paid += lot.qty * oi * fee
                    tail_realized += lot.qty * oi * (1 - fee) - lot.cost
                    n_sells += 1
                    events.append((i, "tail_regime_exit", oi))
                else:
                    keep.append(lot)
            s.tail = keep
        # ---- 1. active-cycle buys, highest price first
        bought = False
        if s.buys and li <= max(b[0] for b in s.buys) * (1 - pen):
            s.buys.sort(key=lambda x: -x[0])
            keep = []
            for b in s.buys:
                price, usd, gen, last = b
                if li <= price * (1 - pen):
                    fill = price if p.fill_at_limit else min(price, oi)
                    usd = min(usd, s.cash)
                    if usd <= 1e-12:
                        continue
                    qty = usd * (1 - fee) / fill
                    s.cash -= usd
                    fees_paid += usd * fee
                    s.cyc_qty += qty
                    s.cyc_cost += usd
                    key = gen if p.cost_mode == "pergen" else 1
                    grp = s.groups.setdefault(key, [0.0, 0.0])
                    grp[0] += qty
                    grp[1] += usd
                    if s.cycle_t0 < 0:
                        s.cycle_t0 = i
                    s.locked = True
                    n_buys += 1
                    bought = True
                    max_gen_seen = max(max_gen_seen, gen)
                    events.append((i, f"buy_g{gen}", fill, usd))
                    day_cash_min = min(day_cash_min, s.cash + spike_cash)
                    if last and gen == s.gen and s.gen < p.max_gens and not s.stale:
                        if p.gen_anchor == "cost":
                            s.pending_gen = s.cyc_cost / s.cyc_qty * (1 - p.gen_gap)
                        else:
                            s.pending_gen = fill * (1 - p.gen_gap)
                        s.gen_low = li
                else:
                    keep.append(b)
            s.buys = keep
        # ---- 2. active-cycle TP1 (skipped when a cycle buy filled this bar).
        # pooled: one group (key 1). pergen: deepest group first; a group's
        # TP1 closes it and re-arms its own ladder at the fill (sub-roll);
        # closing generation 1 is the full roll.
        if s.cyc_qty > 0 and not bought:
            for k in sorted(s.groups, reverse=True):
                q, cst = s.groups[k]
                C = cst / q
                tp1 = C * (1 + p.tp1)
                if hi < tp1 * (1 + pen):
                    continue
                fill = tp1 if p.fill_at_limit else max(tp1, oi)
                q1 = q * p.tp1_frac
                q2 = q * p.tp2_frac
                qt = max(q - q1 - q2, 0.0)
                s.cash += q1 * fill * (1 - fee)
                fees_paid += q1 * fill * fee
                n_sells += 1
                tp1_count += 1
                if q2 > 1e-15:
                    s.tp2_lots.append([C * (1 + p.tp2), q2, q2 * C])
                if p.tail_tiers:
                    for share, mult in p.tail_tiers:
                        qq = q * share
                        if qq > 1e-15:
                            s.tail.append(Lot(qq, qq * C, i, target=mult - 1.0))
                elif qt > 1e-15:
                    s.tail.append(Lot(qt, qt * C, i))
                del s.groups[k]
                s.cyc_qty -= q
                s.cyc_cost -= cst
                events.append((i, "tp1", fill, C))
                if k == 1 or not s.groups:
                    s.cyc_qty = 0.0
                    s.cyc_cost = 0.0
                    s.groups = {}
                    s.buys = []
                    s.pending_gen = None
                    if p.roll and not halted:
                        deferred.append(("cycle", fill))
                    else:
                        deferred.append(("wait", fill, "noroll" if not p.roll else "halt"))
                    break
                # sub-roll of generation k
                s.buys = [b for b in s.buys if b[2] < k]
                s.gen = k - 1
                s.pending_gen = None
                if not halted and not s.stale:
                    deferred.append(("gen", fill))
        # ---- 3. old-cycle TP2 lots (were resting; may fill in the TP1 bar)
        if s.tp2_lots:
            keep = []
            for lot in s.tp2_lots:
                price, qty, cost = lot
                if hi >= price * (1 + pen):
                    fill = price if p.fill_at_limit else max(price, oi)
                    s.cash += qty * fill * (1 - fee)
                    fees_paid += qty * fill * fee
                    n_sells += 1
                    events.append((i, "tp2", fill))
                    if p.tp2_reanchor and not bought and not halted:
                        deferred.append(("reanchor", fill))
                else:
                    keep.append(lot)
            s.tp2_lots = keep
        # ---- 3b. tail lots as resting limit sells (intrabar), when enabled
        if p.tail_intraday and s.tail and p.tail_exit[0] == "target":
            keep = []
            for lot in s.tail:
                tgt = lot.cost / lot.qty * (1 + (p.tail_exit[1] if lot.target is None else lot.target))
                if i > lot.t0 and hi >= tgt * (1 + pen):
                    fill = tgt if p.fill_at_limit else max(tgt, oi)
                    s.cash += lot.qty * fill * (1 - fee)
                    fees_paid += lot.qty * fill * fee
                    tail_realized += lot.qty * fill * (1 - fee) - lot.cost
                    n_sells += 1
                    events.append((i, "tail_limit", fill))
                else:
                    keep.append(lot)
            s.tail = keep
        # ---- 4. spike order (independent, never joins C)
        if spike_order is not None and li <= spike_order * (1 - pen) and spike_cash > 1e-12:
            fill = spike_order if p.fill_at_limit else min(spike_order, oi)
            qty = spike_cash * (1 - fee) / fill
            fees_paid += spike_cash * fee
            s.spike_pos.append([fill * (1 + p.spike_tp), qty, spike_cash, i])
            events.append((i, "spike_buy", fill, spike_cash))
            spike_cash = 0.0
            spike_order = None
            n_buys += 1
            day_cash_min = min(day_cash_min, s.cash + spike_cash)
        if s.spike_pos:
            keep = []
            for sp in s.spike_pos:
                price, qty, cost, t0 = sp
                if i > t0 and hi >= price * (1 + pen):
                    fill = price if p.fill_at_limit else max(price, oi)
                    spike_cash += qty * fill * (1 - fee)
                    fees_paid += qty * fill * fee
                    n_sells += 1
                    spike_order = None  # re-armed at day end
                    events.append((i, "spike_sell", fill))
                else:
                    keep.append(sp)
            s.spike_pos = keep
        # ---- 5. next generation (optionally after a rebound off the low)
        if s.pending_gen is not None:
            s.gen_low = min(s.gen_low, li)
            if not halted:
                if p.gen_rebound is None:
                    deferred.append(("gen", s.pending_gen))
                    s.pending_gen = None
                elif de[i] and ci >= s.gen_low * (1 + p.gen_rebound):
                    deferred.append(("gen", min(s.pending_gen, ci)))
                    s.pending_gen = None
        # ---- 6. daily slow decisions
        if de[i] and p.stale_days and not s.stale and s.cycle_t0 >= 0 and s.cyc_qty > 0:
            age = (bars.t[i] - bars.t[s.cycle_t0]) / DAY_MS
            if age >= p.stale_days and s.cyc_qty * ci < s.cyc_cost:
                s.stale = True
                s.pending_gen = None
                s.buys = [b for b in s.buys if b[2] == 1]
                events.append((i, "stale", ci))
        if de[i]:
            if day in pause_days and s.buys:
                s.buys = []          # PAUSED: cancel unfilled buys
                if s.cyc_qty == 0:
                    waiting = "halt"
            if s.tail and p.tail_exit[0] != "none" and not (p.tail_intraday and p.tail_exit[0] == "target"):
                keep = []
                bear = day in bear_days
                for lot in s.tail:
                    rule = p.tail_exit if lot.target is None else ("target", lot.target)
                    act = _tail_decision(lot, ci, i, bars, rule, bear)
                    if act == 1:
                        s.cash += lot.qty * ci * (1 - fee)
                        fees_paid += lot.qty * ci * fee
                        tail_realized += lot.qty * ci * (1 - fee) - lot.cost
                        n_sells += 1
                    else:
                        lot.exit_next = act == 2
                        keep.append(lot)
                s.tail = keep
            if (p.drift is not None and not s.locked and s.cyc_qty == 0 and not halted
                    and ci >= s.anchor * (1 + p.drift)):
                deferred.append(("reanchor", ci))
            if waiting == "halt" and not halted and s.cyc_qty == 0:
                deferred.append(("cycle", ci))
            if p.spike_frac > 0 and not s.spike_pos and spike_cash > 0 and not halted:
                spike_order = s.anchor * (1 - p.spike_depth)
        # ---- deferred actions become active on the next bar
        if deferred:
            for act in deferred:
                kind = act[0]
                if kind == "cycle":
                    new_cycle(act[1])
                elif kind == "wait":
                    s.anchor = act[1]
                    s.buys = []
                    s.locked = False
                    waiting = act[2]
                elif kind == "reanchor":
                    if s.cyc_qty == 0 and not s.locked:
                        new_cycle(act[1])
                        events.append((i, "anchor", act[1], s.cycle_budget))
                elif kind == "gen":
                    if s.gen < p.max_gens:
                        spawn_gen(act[1])
            deferred = []
        if de[i]:
            pos_q = s.cyc_qty + sum(x[1] for x in s.tp2_lots) + sum(t.qty for t in s.tail) \
                + sum(x[1] for x in s.spike_pos)
            pos_c = s.cyc_cost + sum(x[2] for x in s.tp2_lots) + sum(t.cost for t in s.tail) \
                + sum(x[2] for x in s.spike_pos)
            eq_days.append(day)
            eq_vals.append(s.cash + spike_cash + pos_q * ci)
            pos_vals.append(pos_q * ci)
            pos_costs.append(pos_c)
            cyc_pnl.append((s.cyc_qty * ci / s.cyc_cost - 1) if s.cyc_cost > 0 else 0.0)
            cyc_cost_log.append(s.cyc_cost)
            pend_log.append(sum(b[1] for b in s.buys) + (spike_cash if spike_order is not None else 0.0))
            cash_log.append(s.cash + spike_cash)
            cash_min_log.append(min(day_cash_min, s.cash + spike_cash))
            day_cash_min = math.inf

    return {
        "days": np.array(eq_days), "equity": np.array(eq_vals),
        "pos_value": np.array(pos_vals), "pos_cost": np.array(pos_costs),
        "cyc_pnl": np.array(cyc_pnl), "cyc_cost": np.array(cyc_cost_log),
        "pending": np.array(pend_log), "cash": np.array(cash_log), "cash_min": np.array(cash_min_log),
        "n_buys": n_buys, "n_sells": n_sells, "tp1_count": tp1_count,
        "fees": fees_paid, "max_gen": max_gen_seen, "events": events,
        "tail_qty": sum(t.qty for t in s.tail), "tail_cost": sum(t.cost for t in s.tail),
        "tail_realized": tail_realized,
    }


def _tail_decision(lot: Lot, price: float, i: int, bars: Bars, rule: tuple, bear: bool) -> int:
    """0 keep, 1 sell now at this close, 2 sell at the next bar's open.
    Regime kinds use `bear`, a price-only signal known at this close:
      ("regime",)                      hold in bull, exit when bear
      ("regime_above_cost",)           exit when bear only if price >= lot cost
      ("target_or_regime", x)          close >= C*(1+x) -> sell now; else bear -> exit
      ("target_or_regime_above_cost", x)"""
    kind = rule[0]
    if kind in ("regime", "regime_above_cost", "target_or_regime", "target_or_regime_above_cost"):
        C = lot.cost / lot.qty if lot.qty else 0.0
        if kind.startswith("target") and price >= C * (1 + rule[1]):
            return 1
        if bear and (not kind.endswith("above_cost") or price >= C):
            return 2
        return 0
    return 1 if _tail_should_sell(lot, price, i, bars, rule) else 0


def _tail_should_sell(lot: Lot, price: float, i: int, bars: Bars, rule: tuple) -> bool:
    kind = rule[0]
    C = lot.cost / lot.qty if lot.qty else 0.0
    if kind == "target":            # ("target", x): sell when price >= C*(1+x)
        return price >= C * (1 + rule[1])
    if kind == "trail":             # ("trail", arm, dd): arm at C*(1+arm), sell dd off peak
        arm, dd = rule[1], rule[2]
        if not lot.armed and price >= C * (1 + arm):
            lot.armed = True
        if lot.armed:
            lot.peak = max(lot.peak, price)
            return price <= lot.peak * (1 - dd)
        return False
    if kind == "time":              # ("time", days): sell after N days if above cost
        days = (bars.t[i] - bars.t[lot.t0]) / DAY_MS
        return days >= rule[1] and price >= C
    if kind == "time_any":          # ("time_any", days): sell after N days regardless
        days = (bars.t[i] - bars.t[lot.t0]) / DAY_MS
        return days >= rule[1]
    if kind == "target_or_time":    # ("target_or_time", x, days)
        days = (bars.t[i] - bars.t[lot.t0]) / DAY_MS
        return price >= C * (1 + rule[1]) or days >= rule[2]
    if kind == "trail_or_time":     # ("trail_or_time", arm, dd, days)
        days = (bars.t[i] - bars.t[lot.t0]) / DAY_MS
        if days >= rule[3]:
            return True
        return _tail_should_sell(lot, price, i, bars, ("trail", rule[1], rule[2]))
    raise ValueError(kind)


# --------------------------------------------------------------------------
# satellite strategy (V2 rule 53-56)
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class SatParams:
    sell: float = 0.20          # sell trigger above batch cost
    sell_frac0: float = 0.75    # share of the initial position sold (rest = tail)
    rebuy: tuple = (0.08,)      # rebuy offsets below the sell price
    rebuy_w: tuple = (1.0,)     # split of proceeds across rebuy offsets
    tail_exit: tuple = ("none",)
    fee: float = 0.001
    pen: float = 0.0005
    entry: str = "market"       # "market" buy at start, or "ladder" (core-like)


def run_sat(bars: Bars, p: SatParams) -> dict:
    """Satellite: buy at market on day 0; sell sell_frac0 of it at (1+sell)*C;
    the rest is the tail. Every sale re-places the rebuy ladder below the sale
    price with ALL free cash (old unfilled rebuys cancelled). Rebuy fills pool
    into one active batch (average cost) that sells 100% at (1+sell)*C_batch.
    Never adds outside money."""
    n = len(bars)
    o, h, l, c, de = bars.o, bars.h, bars.l, bars.c, bars.day_end
    fee, pen = p.fee, p.pen
    q0 = (1 - fee) / o[0]
    cash = 0.0
    bq, bc = q0 * p.sell_frac0, p.sell_frac0          # active batch qty / cost (USDT)
    tail = [Lot(q0 * (1 - p.sell_frac0), 1.0 - p.sell_frac0, 0)] if p.sell_frac0 < 1 else []
    rebuys: list = []      # [price, usd]
    batch_t0 = 0
    eq_days, eq_vals, pos_vals, pos_costs = [], [], [], []
    n_buys, n_sells, fees_paid = 1, 0, fee
    cycles = 0
    for i in range(n):
        oi, hi, li, ci = o[i], h[i], l[i], c[i]
        bought = False
        if rebuys and li <= rebuys[0][0] * (1 - pen):
            keep = []
            for price, usd in rebuys:
                if li <= price * (1 - pen):
                    fill = min(price, oi)
                    usd = min(usd, cash)
                    if usd <= 1e-12:
                        continue
                    bq += usd * (1 - fee) / fill
                    bc += usd
                    cash -= usd
                    fees_paid += usd * fee
                    n_buys += 1
                    bought = True
                    batch_t0 = i
                else:
                    keep.append([price, usd])
            rebuys = keep
        if bq > 0 and not bought and i > batch_t0:
            target = bc / bq * (1 + p.sell)
            if hi >= target * (1 + pen):
                fill = max(target, oi)
                cash += bq * fill * (1 - fee)
                fees_paid += bq * fill * fee
                n_sells += 1
                cycles += 1
                bq = bc = 0.0
                rebuys = sorted(([fill * (1 - off), cash * wt] for off, wt in zip(p.rebuy, p.rebuy_w)),
                                key=lambda x: -x[0])
        if de[i]:
            if tail and p.tail_exit[0] != "none":
                kt = []
                for lot in tail:
                    if _tail_should_sell(lot, ci, i, bars, p.tail_exit):
                        cash += lot.qty * ci * (1 - fee)
                        n_sells += 1
                        if not bq and rebuys:   # fold tail proceeds into the waiting rebuys
                            tot = sum(r[1] for r in rebuys)
                            rebuys = [[r[0], r[1] / tot * cash] for r in rebuys] if tot else rebuys
                    else:
                        kt.append(lot)
                tail = kt
            pos_q = bq + sum(t.qty for t in tail)
            pos_c = bc + sum(t.cost for t in tail)
            eq_days.append(int(bars.t[i] // DAY_MS))
            eq_vals.append(cash + pos_q * ci)
            pos_vals.append(pos_q * ci)
            pos_costs.append(pos_c)
    return {"days": np.array(eq_days), "equity": np.array(eq_vals),
            "pos_value": np.array(pos_vals), "pos_cost": np.array(pos_costs),
            "n_buys": n_buys, "n_sells": n_sells, "cycles": cycles, "fees": fees_paid}


# --------------------------------------------------------------------------
# baselines
# --------------------------------------------------------------------------
def run_bh(bars: Bars, fee: float = 0.001) -> dict:
    q = (1 - fee) / bars.o[0]
    idx = np.where(bars.day_end)[0]
    eq = q * bars.c[idx]
    return {"days": (bars.t[idx] // DAY_MS).astype(int), "equity": eq,
            "pos_value": eq, "pos_cost": np.full(len(idx), 1.0),
            "n_buys": 1, "n_sells": 0, "fees": fee}


def simple_params(d=(0.07, 0.17, 0.29), tp=0.25) -> CoreParams:
    """Baseline C: fixed 3-tier ladder, sell 100% at +tp, re-anchor at the sale,
    no tail, no generations, no TP2, no drift chasing."""
    return CoreParams(d=d, tp1=tp, tp1_frac=1.0, tp2_frac=0.0, max_gens=1,
                      tp2_reanchor=False, drift=0.20)


V2_CORE = {
    "HYPE": (0.06, 0.12, 0.23),
    "AAVE": (0.07, 0.17, 0.29),
    "TAO": (0.07, 0.19, 0.30),
    "LINK": (0.06, 0.14, 0.25),
}
V2_SAT_REBUY = {"NEAR": 0.07, "ZRO": 0.09, "PENDLE": 0.09, "RENDER": 0.08}


def with_(p, **kw):
    return replace(p, **kw)
