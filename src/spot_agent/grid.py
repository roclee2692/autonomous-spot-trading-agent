from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from .models import Regime, Side, TradeProposal, utc_now
from .rules import SymbolRules

D = Decimal


def volatility_spacing(daily_volatility: Decimal) -> Decimal:
    """Transparent piecewise interpolation of daily realized volatility to grid width."""
    points = (
        (D("0.01"), D("0.006")),
        (D("0.02"), D("0.008")),
        (D("0.04"), D("0.012")),
        (D("0.05"), D("0.015")),
        (D("0.08"), D("0.025")),
    )
    if daily_volatility <= points[0][0]:
        return points[0][1]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if daily_volatility <= x1:
            return y0 + (daily_volatility - x0) * (y1 - y0) / (x1 - x0)
    return points[-1][1]


def grid_spacing(
    maker_buy_fee: Decimal,
    maker_sell_fee: Decimal,
    slippage: Decimal,
    daily_volatility: Decimal,
) -> tuple[Decimal, Decimal]:
    if min(maker_buy_fee, maker_sell_fee, slippage, daily_volatility) < 0:
        raise ValueError("fees, slippage, and volatility must be non-negative")
    round_trip_cost = maker_buy_fee + maker_sell_fee + slippage
    spacing = max(D("0.006"), round_trip_cost * D("3"), volatility_spacing(daily_volatility))
    return min(spacing, D("0.025")), round_trip_cost


@dataclass(frozen=True)
class GridPlan:
    regime: Regime
    reference_price: Decimal
    spacing: Decimal
    round_trip_cost: Decimal
    orders: tuple[TradeProposal, ...]
    quote_required: Decimal
    base_required: Decimal


def build_stage2_grid(
    rules: SymbolRules,
    reference_price: Decimal,
    daily_volatility: Decimal,
    maker_buy_fee: Decimal,
    maker_sell_fee: Decimal,
    slippage: Decimal = D("0"),
    regime: Regime = Regime.RANGE,
    levels_per_side: int = 3,
    quote_budget_per_order: Decimal = D("10"),
) -> GridPlan:
    if regime is not Regime.RANGE:
        raise ValueError("NO_TRADE: grid is only allowed in RANGE")
    if rules.status != "TRADING" or "LIMIT_MAKER" not in rules.order_types:
        raise ValueError("NO_TRADE: symbol is not tradable with LIMIT_MAKER")
    if levels_per_side < 1 or levels_per_side > 3:
        raise ValueError("Stage 2 V1 permits 1-3 levels per side")
    if quote_budget_per_order <= rules.min_notional:
        raise ValueError("order budget must be safely above current min notional")

    spacing, round_trip_cost = grid_spacing(
        maker_buy_fee, maker_sell_fee, slippage, daily_volatility
    )
    now = utc_now()
    batch_id = f"{now.strftime('%m%d%H%M%S')}{uuid.uuid4().hex[:4]}"
    orders: list[TradeProposal] = []
    for side in (Side.BUY, Side.SELL):
        for level in range(1, levels_per_side + 1):
            factor = (D("1") - spacing) ** level if side is Side.BUY else (D("1") + spacing) ** level
            raw_price = reference_price * factor
            price = rules.round_price(raw_price, upward=side is Side.SELL)
            quantity = rules.round_qty(quote_budget_per_order / price)
            failures = rules.validate_limit(price, quantity)
            if failures:
                raise ValueError(f"NO_TRADE: level {side}-{level} violates {failures}")
            order_id = f"asv1-g{batch_id}-{side.value[0].lower()}{level}"
            orders.append(
                TradeProposal(
                    client_order_id=order_id,
                    symbol=rules.symbol,
                    market_type="SPOT",
                    side=side,
                    order_type="LIMIT_MAKER",
                    price=price,
                    quantity=quantity,
                    created_at=now,
                    regime=regime,
                    strategy="LOW_FREQUENCY_RANGE_GRID",
                    reason=f"RANGE level {level}; spacing covers at least 3x estimated round-trip cost",
                    thesis_id=f"range-{batch_id}-{level}-{side.value.lower()}",
                    evidence=(
                        f"reference_price={reference_price}",
                        f"daily_volatility={daily_volatility}",
                        f"round_trip_cost={round_trip_cost}",
                    ),
                    invalidating_conditions=("regime leaves RANGE", "data becomes stale", "risk veto"),
                    exit_conditions=("paired grid target reached", "thesis invalidated", "rebalance"),
                )
            )
    buys = [order for order in orders if order.side is Side.BUY]
    sells = [order for order in orders if order.side is Side.SELL]
    return GridPlan(
        regime=regime,
        reference_price=reference_price,
        spacing=spacing,
        round_trip_cost=round_trip_cost,
        orders=tuple(orders),
        quote_required=sum((o.notional * (D("1") + maker_buy_fee) for o in buys), D("0")),
        base_required=sum((o.quantity for o in sells), D("0")),
    )


def sellable_quantity_from_buy(
    executed_quantity: Decimal,
    commission_amount: Decimal,
    commission_asset: str,
    base_asset: str,
    step_size: Decimal,
    rounding_buffer_steps: int = 1,
) -> Decimal:
    available = executed_quantity
    if commission_asset == base_asset:
        available -= commission_amount
    available -= step_size * rounding_buffer_steps
    if available <= 0:
        return D("0")
    return (available // step_size) * step_size if step_size else available
