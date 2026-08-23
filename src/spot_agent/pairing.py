from __future__ import annotations

import uuid
from decimal import Decimal

from .models import Regime, Side, TradeProposal, utc_now
from .rules import SymbolRules

D = Decimal


def build_paired_order(
    order: dict,
    fills: list[dict],
    rules: SymbolRules,
    spacing: Decimal,
) -> TradeProposal | None:
    if order.get("status") != "FILLED" or not fills:
        return None
    total_qty = sum((D(fill["qty"]) for fill in fills), D("0"))
    total_quote = sum((D(fill["quote_qty"]) for fill in fills), D("0"))
    if total_qty <= 0 or total_quote <= 0:
        return None
    average_price = total_quote / total_qty
    original_side = Side(order["side"])
    now = utc_now()
    token = uuid.uuid4().hex[:8]
    if original_side is Side.BUY:
        base_commission = sum(
            (D(fill["commission"]) for fill in fills if fill["commission_asset"] == rules.base_asset),
            D("0"),
        )
        quantity = rules.round_qty(total_qty - base_commission - rules.step_size)
        price = rules.round_price(average_price * (D("1") + spacing), upward=True)
        side = Side.SELL
        reason = "paired take-profit after actual BUY fills, fees, and one-step rounding buffer"
    else:
        quote_commission = sum(
            (D(fill["commission"]) for fill in fills if fill["commission_asset"] == rules.quote_asset),
            D("0"),
        )
        proceeds = total_quote - quote_commission
        price = rules.round_price(average_price * (D("1") - spacing), upward=False)
        quantity = rules.round_qty(proceeds / price)
        side = Side.BUY
        reason = "paired re-entry after actual SELL fills and quote commission"
    if quantity <= 0 or rules.validate_limit(price, quantity):
        return None
    parent = str(order["client_order_id"])
    return TradeProposal(
        client_order_id=f"asv1-p{token}-{side.value[0].lower()}",
        symbol=rules.symbol,
        market_type="SPOT",
        side=side,
        order_type="LIMIT_MAKER",
        price=price,
        quantity=quantity,
        created_at=now,
        regime=Regime.RANGE,
        strategy="LOW_FREQUENCY_RANGE_GRID_PAIR",
        reason=reason,
        thesis_id=f"pair-{token}-{side.value.lower()}",
        evidence=(
            f"parent_client_order_id={parent}",
            f"actual_fill_quantity={total_qty}",
            f"actual_quote_quantity={total_quote}",
            f"spacing={spacing}",
        ),
        invalidating_conditions=("regime leaves RANGE", "risk veto", "data becomes stale"),
        exit_conditions=("paired grid target reached", "thesis invalidated", "rebalance"),
    )

