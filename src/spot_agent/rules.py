from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal
from typing import Any

ZERO = Decimal("0")


def decimal_step(value: Decimal, step: Decimal, *, upward: bool = False) -> Decimal:
    if step == ZERO:
        return value
    rounding = ROUND_CEILING if upward else ROUND_FLOOR
    return (value / step).to_integral_value(rounding=rounding) * step


@dataclass(frozen=True)
class SymbolRules:
    symbol: str
    status: str
    base_asset: str
    quote_asset: str
    order_types: tuple[str, ...]
    min_price: Decimal
    max_price: Decimal
    tick_size: Decimal
    min_qty: Decimal
    max_qty: Decimal
    step_size: Decimal
    min_notional: Decimal
    max_notional: Decimal | None

    @classmethod
    def from_exchange_info(cls, payload: dict[str, Any], symbol: str = "BTCUSDT") -> "SymbolRules":
        matches = [item for item in payload.get("symbols", []) if item.get("symbol") == symbol]
        if len(matches) != 1:
            raise ValueError(f"expected exactly one {symbol} entry")
        item = matches[0]
        filters = {entry["filterType"]: entry for entry in item.get("filters", [])}
        missing = {"PRICE_FILTER", "LOT_SIZE"} - filters.keys()
        if missing:
            raise ValueError(f"missing required symbol filters: {sorted(missing)}")
        price_filter = filters["PRICE_FILTER"]
        lot_filter = filters["LOT_SIZE"]
        notional_filter = filters.get("NOTIONAL") or filters.get("MIN_NOTIONAL")
        if notional_filter is None:
            raise ValueError("missing NOTIONAL/MIN_NOTIONAL; fail closed")
        max_notional = notional_filter.get("maxNotional")
        return cls(
            symbol=symbol,
            status=str(item.get("status", "")),
            base_asset=str(item.get("baseAsset", "")),
            quote_asset=str(item.get("quoteAsset", "")),
            order_types=tuple(item.get("orderTypes", ())),
            min_price=Decimal(price_filter["minPrice"]),
            max_price=Decimal(price_filter["maxPrice"]),
            tick_size=Decimal(price_filter["tickSize"]),
            min_qty=Decimal(lot_filter["minQty"]),
            max_qty=Decimal(lot_filter["maxQty"]),
            step_size=Decimal(lot_filter["stepSize"]),
            min_notional=Decimal(notional_filter["minNotional"]),
            max_notional=Decimal(max_notional) if max_notional is not None else None,
        )

    def round_price(self, price: Decimal, *, upward: bool = False) -> Decimal:
        return decimal_step(price, self.tick_size, upward=upward)

    def round_qty(self, quantity: Decimal) -> Decimal:
        return decimal_step(quantity, self.step_size)

    def validate_limit(self, price: Decimal, quantity: Decimal) -> tuple[str, ...]:
        failures: list[str] = []
        if not price.is_finite() or not quantity.is_finite() or price <= ZERO or quantity <= ZERO:
            return ("NON_FINITE_OR_NON_POSITIVE_ORDER",)
        if self.status != "TRADING":
            failures.append("SYMBOL_NOT_TRADING")
        if not (self.min_price <= price <= self.max_price):
            failures.append("PRICE_OUT_OF_RANGE")
        if self.tick_size and price % self.tick_size != ZERO:
            failures.append("PRICE_TICK_MISMATCH")
        if not (self.min_qty <= quantity <= self.max_qty):
            failures.append("QUANTITY_OUT_OF_RANGE")
        if self.step_size and quantity % self.step_size != ZERO:
            failures.append("QUANTITY_STEP_MISMATCH")
        notional = price * quantity
        if notional < self.min_notional:
            failures.append("BELOW_MIN_NOTIONAL")
        if self.max_notional is not None and notional > self.max_notional:
            failures.append("ABOVE_MAX_NOTIONAL")
        return tuple(failures)
