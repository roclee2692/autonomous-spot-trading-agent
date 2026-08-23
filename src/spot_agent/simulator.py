from __future__ import annotations

from dataclasses import asdict
from decimal import Decimal

from .journal import HashChainJournal
from .models import BalanceSnapshot, Side, TradeProposal
from .risk_gate import RiskGate

D = Decimal


class SimulationExecutor:
    def __init__(self, balances: BalanceSnapshot, risk_gate: RiskGate, journal: HashChainJournal) -> None:
        self.balances = balances
        self.risk_gate = risk_gate
        self.journal = journal
        self.open_orders: dict[str, TradeProposal] = {}

    def place_batch(self, proposals: tuple[TradeProposal, ...], reference_price: Decimal) -> None:
        decision = self.risk_gate.evaluate_batch(
            proposals,
            self.balances,
            reference_price,
            existing_order_ids=set(self.open_orders),
            current_open_orders=len(self.open_orders),
        )
        self.journal.append("RISK_DECISION", {"code": decision.code, "reasons": decision.reasons})
        if not decision.accepted:
            raise ValueError(f"REJECT_ORDER: {decision.reasons}")
        buy_quote = sum((p.notional for p in proposals if p.side is Side.BUY), D("0"))
        sell_base = sum((p.quantity for p in proposals if p.side is Side.SELL), D("0"))
        self.balances = BalanceSnapshot(
            base_free=self.balances.base_free - sell_base,
            quote_free=self.balances.quote_free - buy_quote,
            base_locked=self.balances.base_locked + sell_base,
            quote_locked=self.balances.quote_locked + buy_quote,
        )
        for proposal in proposals:
            self.open_orders[proposal.client_order_id] = proposal
            self.journal.append("ORDER_ACCEPTED", asdict(proposal))

    def cancel(self, client_order_id: str) -> None:
        if client_order_id not in self.open_orders:
            raise KeyError("unknown open order")
        proposal = self.open_orders.pop(client_order_id)
        if proposal.side is Side.BUY:
            self.balances = BalanceSnapshot(
                base_free=self.balances.base_free,
                quote_free=self.balances.quote_free + proposal.notional,
                base_locked=self.balances.base_locked,
                quote_locked=self.balances.quote_locked - proposal.notional,
            )
        else:
            self.balances = BalanceSnapshot(
                base_free=self.balances.base_free + proposal.quantity,
                quote_free=self.balances.quote_free,
                base_locked=self.balances.base_locked - proposal.quantity,
                quote_locked=self.balances.quote_locked,
            )
        self.journal.append("ORDER_CANCELED", {"client_order_id": client_order_id})

    def fill(self, client_order_id: str, fee_rate: Decimal) -> None:
        if fee_rate < 0:
            raise ValueError("fee_rate must be non-negative")
        proposal = self.open_orders.pop(client_order_id)
        notional = proposal.notional
        if proposal.side is Side.BUY:
            fee_asset = self.risk_gate.rules.base_asset
            fee = proposal.quantity * fee_rate
            self.balances = BalanceSnapshot(
                base_free=self.balances.base_free + proposal.quantity - fee,
                quote_free=self.balances.quote_free,
                base_locked=self.balances.base_locked,
                quote_locked=self.balances.quote_locked - notional,
            )
        else:
            fee_asset = self.risk_gate.rules.quote_asset
            fee = notional * fee_rate
            self.balances = BalanceSnapshot(
                base_free=self.balances.base_free,
                quote_free=self.balances.quote_free + notional - fee,
                base_locked=self.balances.base_locked - proposal.quantity,
                quote_locked=self.balances.quote_locked,
            )
        self.journal.append(
            "ORDER_FILLED",
            {
                "client_order_id": client_order_id,
                "side": proposal.side,
                "price": proposal.price,
                "executed_quantity": proposal.quantity,
                "commission_amount": fee,
                "commission_asset": fee_asset,
                "balances": asdict(self.balances),
            },
        )
