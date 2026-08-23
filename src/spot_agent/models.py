from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum


class Regime(StrEnum):
    UPTREND = "UPTREND"
    DOWNTREND = "DOWNTREND"
    RANGE = "RANGE"
    BREAKOUT = "BREAKOUT"
    PANIC = "PANIC"
    UNCERTAIN = "UNCERTAIN"


class Side(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True)
class TradeProposal:
    client_order_id: str
    symbol: str
    market_type: str
    side: Side
    order_type: str
    price: Decimal
    quantity: Decimal
    created_at: datetime
    regime: Regime
    strategy: str
    reason: str
    thesis_id: str
    evidence: tuple[str, ...]
    invalidating_conditions: tuple[str, ...]
    exit_conditions: tuple[str, ...]

    @property
    def notional(self) -> Decimal:
        return self.price * self.quantity


@dataclass(frozen=True)
class BalanceSnapshot:
    base_free: Decimal
    quote_free: Decimal
    base_locked: Decimal = Decimal("0")
    quote_locked: Decimal = Decimal("0")


@dataclass(frozen=True)
class RiskDecision:
    accepted: bool
    reasons: tuple[str, ...] = field(default_factory=tuple)

    @property
    def code(self) -> str:
        return "ACCEPT_ORDER" if self.accepted else "REJECT_ORDER"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)

