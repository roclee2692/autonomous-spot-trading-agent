from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from .models import BalanceSnapshot, Regime, RiskDecision, Side, TradeProposal
from .rules import SymbolRules

D = Decimal


@dataclass(frozen=True)
class RiskLimits:
    environment: str = "SIMULATION"
    allowed_symbol: str = "BTCUSDT"
    max_open_orders: int = 6
    max_order_notional: Decimal = D("10")
    max_daily_turnover: Decimal = D("60")
    quote_reserve: Decimal = D("20")
    core_base_value: Decimal = D("20")
    max_data_age_seconds: int = 60
    max_daily_loss: Decimal = D("5")
    max_buy_fee_rate: Decimal = D("0.001")


class RiskGate:
    def __init__(self, limits: RiskLimits, rules: SymbolRules) -> None:
        self.limits = limits
        self.rules = rules

    def evaluate_batch(
        self,
        proposals: tuple[TradeProposal, ...],
        balances: BalanceSnapshot,
        reference_price: Decimal,
        *,
        existing_order_ids: set[str] | None = None,
        current_open_orders: int = 0,
        daily_turnover: Decimal = D("0"),
        daily_loss: Decimal = D("0"),
        kill_switch: bool = False,
        news_veto: bool = False,
        now: datetime | None = None,
        execution_authorized: bool = False,
    ) -> RiskDecision:
        failures: list[str] = []
        now = now or datetime.now(timezone.utc)
        existing_order_ids = existing_order_ids or set()
        environment = self.limits.environment.upper()
        if environment not in {"SIMULATION", "TESTNET", "LIVE"}:
            failures.append("INVALID_EXECUTION_ENVIRONMENT")
        if environment == "LIVE" and not execution_authorized:
            failures.append("LIVE_EXECUTION_DISABLED")
        if environment == "TESTNET" and not execution_authorized:
            failures.append("TESTNET_EXECUTION_NOT_REQUESTED")
        if kill_switch:
            failures.append("KILL_SWITCH_ACTIVE")
        if news_veto:
            failures.append("NEWS_RISK_VETO")
        if not proposals:
            failures.append("EMPTY_PROPOSAL_BATCH")
        if current_open_orders + len(proposals) > self.limits.max_open_orders:
            failures.append("MAX_OPEN_ORDERS_EXCEEDED")
        if daily_loss >= self.limits.max_daily_loss:
            failures.append("DAILY_LOSS_LIMIT_REACHED")

        numeric_context = (
            reference_price,
            balances.base_free,
            balances.quote_free,
            balances.base_locked,
            balances.quote_locked,
            daily_turnover,
            daily_loss,
            self.limits.max_order_notional,
            self.limits.max_daily_turnover,
            self.limits.quote_reserve,
            self.limits.core_base_value,
            self.limits.max_daily_loss,
            self.limits.max_buy_fee_rate,
        )
        if any(not value.is_finite() for value in numeric_context) or any(
            value < 0 for value in numeric_context
        ) or reference_price == 0:
            failures.append("INVALID_NUMERIC_CONTEXT")
            return RiskDecision(False, tuple(dict.fromkeys(failures)))

        ids: set[str] = set()
        buy_quote = D("0")
        sell_base = D("0")
        batch_turnover = D("0")
        core_base_qty = self.limits.core_base_value / reference_price
        for proposal in proposals:
            if proposal.client_order_id in existing_order_ids or proposal.client_order_id in ids:
                failures.append("DUPLICATE_ORDER_ID")
            ids.add(proposal.client_order_id)
            if proposal.symbol != self.limits.allowed_symbol:
                failures.append("SYMBOL_NOT_ALLOWED")
            if proposal.market_type != "SPOT":
                failures.append("NON_SPOT_FORBIDDEN")
            if proposal.order_type != "LIMIT_MAKER":
                failures.append("POST_ONLY_REQUIRED")
            if proposal.regime is not Regime.RANGE:
                failures.append("GRID_ONLY_ALLOWED_IN_RANGE")
            if not proposal.reason or not proposal.thesis_id or not proposal.evidence:
                failures.append("MISSING_TRADE_THESIS")
            if proposal.created_at.tzinfo is None:
                failures.append("STALE_OR_FUTURE_PROPOSAL")
            else:
                age = (now - proposal.created_at).total_seconds()
                if age < -5 or age > self.limits.max_data_age_seconds:
                    failures.append("STALE_OR_FUTURE_PROPOSAL")
            failures.extend(self.rules.validate_limit(proposal.price, proposal.quantity))
            if not proposal.price.is_finite() or not proposal.quantity.is_finite() or proposal.price <= 0 or proposal.quantity <= 0:
                continue
            if proposal.notional > self.limits.max_order_notional:
                failures.append("MAX_ORDER_NOTIONAL_EXCEEDED")
            batch_turnover += proposal.notional
            if proposal.side is Side.BUY:
                buy_quote += proposal.notional
            else:
                sell_base += proposal.quantity

        if daily_turnover + batch_turnover > self.limits.max_daily_turnover:
            failures.append("DAILY_TURNOVER_EXCEEDED")
        buy_cash_required = buy_quote * (D("1") + self.limits.max_buy_fee_rate)
        if balances.quote_free - buy_cash_required < self.limits.quote_reserve:
            failures.append("QUOTE_RESERVE_BREACH")
        if balances.base_free - sell_base < core_base_qty:
            failures.append("CORE_BTC_BREACH")
        unique = tuple(dict.fromkeys(failures))
        return RiskDecision(accepted=not unique, reasons=unique)
