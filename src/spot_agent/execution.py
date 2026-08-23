from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .binance_signed import BinanceAPIError, BinanceSignedClient, UnknownExecutionStatus
from .journal import HashChainJournal
from .models import TradeProposal
from .state import StateStore

AGENT_ORDER_PREFIX = "asv1-"


class ReconciliationError(RuntimeError):
    pass


class ExecutionEngine:
    def __init__(self, client: BinanceSignedClient, state: StateStore, journal: HashChainJournal) -> None:
        self.client = client
        self.state = state
        self.journal = journal

    def submit(self, proposal: TradeProposal, parent_client_order_id: str | None = None) -> dict[str, Any] | None:
        if not proposal.client_order_id.startswith(AGENT_ORDER_PREFIX):
            raise ValueError("agent orders must use the asv1- prefix")
        self.state.record_proposal(proposal, parent_client_order_id)
        self.journal.append("ORDER_SUBMIT_INTENT", asdict(proposal))
        params = {
            "symbol": proposal.symbol,
            "side": proposal.side.value,
            "type": proposal.order_type,
            "quantity": str(proposal.quantity),
            "price": str(proposal.price),
            "newClientOrderId": proposal.client_order_id,
            "newOrderRespType": "RESULT",
        }
        try:
            response = self.client.new_order(params)
        except UnknownExecutionStatus:
            self.state.set_order_status(proposal.client_order_id, "UNKNOWN")
            self.journal.append(
                "ORDER_SUBMIT_UNKNOWN", {"client_order_id": proposal.client_order_id, "retry": False}
            )
            return None
        except BinanceAPIError as exc:
            self.state.set_order_status(proposal.client_order_id, "REJECTED")
            self.journal.append(
                "ORDER_REJECTED",
                {"client_order_id": proposal.client_order_id, "code": exc.code, "message": exc.message},
            )
            raise
        self.state.update_order(response)
        self.journal.append("ORDER_ACKNOWLEDGED", response)
        return response

    def cancel(self, client_order_id: str, symbol: str = "BTCUSDT") -> dict[str, Any] | None:
        local = self.state.order(client_order_id)
        if not client_order_id.startswith(AGENT_ORDER_PREFIX) or local is None:
            raise ValueError("refusing to cancel an unowned order")
        self.state.set_order_status(client_order_id, "PENDING_CANCEL")
        try:
            response = self.client.cancel_order(symbol, client_order_id)
        except UnknownExecutionStatus:
            self.state.set_order_status(client_order_id, "UNKNOWN")
            self.journal.append("ORDER_CANCEL_UNKNOWN", {"client_order_id": client_order_id})
            return None
        self.state.update_order(response)
        self.journal.append("ORDER_CANCELED", response)
        return response

    def resolve_unknown(
        self,
        client_order_id: str,
        symbol: str = "BTCUSDT",
        *,
        confirm_not_found: bool = False,
    ) -> dict[str, Any]:
        """Query an ambiguous submission and require a human decision before releasing it."""
        local = self.state.order(client_order_id)
        if (
            not client_order_id.startswith(AGENT_ORDER_PREFIX)
            or local is None
            or local["status"] not in {"PENDING_SUBMIT", "UNKNOWN"}
        ):
            raise ValueError("order is not an owned unresolved submission")
        try:
            response = self.client.get_order(symbol, client_order_id)
        except BinanceAPIError as exc:
            if exc.code != -2013:
                raise
            if not confirm_not_found:
                raise ReconciliationError(
                    "Binance reports order not found; exact human confirmation is required"
                ) from exc
            self.state.set_order_status(client_order_id, "REJECTED")
            result = {
                "clientOrderId": client_order_id,
                "status": "REJECTED",
                "resolution": "HUMAN_CONFIRMED_NOT_FOUND",
            }
            self.journal.append("UNKNOWN_ORDER_HUMAN_RESOLVED_NOT_FOUND", result)
            return result
        self.state.update_order(response)
        self.journal.append("UNKNOWN_ORDER_RECONCILED", response)
        return response

    def reconcile(self, symbol: str = "BTCUSDT") -> dict[str, int]:
        remote_open = self.client.open_orders(symbol)
        remote_agent = {
            item["clientOrderId"]: item
            for item in remote_open
            if str(item.get("clientOrderId", "")).startswith(AGENT_ORDER_PREFIX)
        }
        known = self.state.known_order_ids()
        unknown_remote = set(remote_agent) - known
        if unknown_remote:
            raise ReconciliationError(
                f"remote agent-prefixed orders lack immutable local theses: {sorted(unknown_remote)}"
            )
        for response in remote_agent.values():
            self.state.update_order(response)

        queried = 0
        for local in self.state.local_open_orders():
            client_id = local["client_order_id"]
            if client_id in remote_agent:
                continue
            try:
                response = self.client.get_order(symbol, client_id)
            except BinanceAPIError as exc:
                if exc.code == -2013 and local["status"] in {"PENDING_SUBMIT", "UNKNOWN"}:
                    continue
                raise
            self.state.update_order(response)
            queried += 1

        new_fills = 0
        for trade in self.client.trades(symbol):
            if self.state.record_trade(symbol, trade):
                new_fills += 1
                self.journal.append("TRADE_RECONCILED", trade)
        return {"remote_agent_open": len(remote_agent), "queried": queried, "new_fills": new_fills}
