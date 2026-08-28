from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from .models import TradeProposal

OPEN_STATUSES = {"PENDING_SUBMIT", "UNKNOWN", "NEW", "PARTIALLY_FILLED", "PENDING_CANCEL"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_default(value: Any) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if hasattr(value, "value"):
        return str(value.value)
    raise TypeError(type(value).__name__)


class StateStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.execute("PRAGMA journal_mode=WAL")
        self._migrate()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "StateStore":
        return self

    def __exit__(self, *_args) -> None:
        self.close()

    def _migrate(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS theses (
                thesis_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS orders (
                client_order_id TEXT PRIMARY KEY,
                exchange_order_id TEXT UNIQUE,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                order_type TEXT NOT NULL,
                price TEXT NOT NULL,
                orig_qty TEXT NOT NULL,
                executed_qty TEXT NOT NULL DEFAULT '0',
                cumulative_quote_qty TEXT NOT NULL DEFAULT '0',
                status TEXT NOT NULL,
                thesis_id TEXT NOT NULL REFERENCES theses(thesis_id),
                parent_client_order_id TEXT,
                pair_created INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS fills (
                symbol TEXT NOT NULL,
                trade_id TEXT NOT NULL,
                exchange_order_id TEXT NOT NULL,
                price TEXT NOT NULL,
                qty TEXT NOT NULL,
                quote_qty TEXT NOT NULL,
                commission TEXT NOT NULL,
                commission_asset TEXT NOT NULL,
                trade_time TEXT NOT NULL,
                is_buyer INTEGER NOT NULL,
                is_maker INTEGER NOT NULL,
                PRIMARY KEY (symbol, trade_id)
            );
            CREATE TABLE IF NOT EXISTS cycles (
                cycle_id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                environment TEXT NOT NULL,
                regime TEXT NOT NULL,
                confidence TEXT NOT NULL,
                action TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS balance_snapshots (
                snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                btc_total TEXT NOT NULL,
                usdt_total TEXT NOT NULL,
                reference_price TEXT NOT NULL,
                total_value_usdt TEXT NOT NULL
            );
            CREATE TRIGGER IF NOT EXISTS theses_no_update
            BEFORE UPDATE ON theses BEGIN SELECT RAISE(ABORT, 'theses are immutable'); END;
            CREATE TRIGGER IF NOT EXISTS theses_no_delete
            BEFORE DELETE ON theses BEGIN SELECT RAISE(ABORT, 'theses are immutable'); END;
            CREATE TRIGGER IF NOT EXISTS fills_no_update
            BEFORE UPDATE ON fills BEGIN SELECT RAISE(ABORT, 'fills are immutable'); END;
            CREATE TRIGGER IF NOT EXISTS fills_no_delete
            BEFORE DELETE ON fills BEGIN SELECT RAISE(ABORT, 'fills are immutable'); END;
            """
        )
        self.connection.commit()

    def record_proposal(self, proposal: TradeProposal, parent_client_order_id: str | None = None) -> None:
        thesis_payload = {
            "timestamp": proposal.created_at,
            "asset": proposal.symbol,
            "side": proposal.side,
            "price": proposal.price,
            "size": proposal.quantity,
            "market_regime": proposal.regime,
            "strategy": proposal.strategy,
            "reason": proposal.reason,
            "evidence": proposal.evidence,
            "invalidating_conditions": proposal.invalidating_conditions,
            "exit_conditions": proposal.exit_conditions,
        }
        thesis_json = json.dumps(
            thesis_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=_json_default,
        )
        with self.connection:
            self.connection.execute(
                "INSERT OR IGNORE INTO theses(thesis_id, created_at, payload_json) VALUES (?, ?, ?)",
                (
                    proposal.thesis_id,
                    proposal.created_at.isoformat(),
                    thesis_json,
                ),
            )
            stored_thesis = self.connection.execute(
                "SELECT payload_json FROM theses WHERE thesis_id=?", (proposal.thesis_id,)
            ).fetchone()[0]
            if stored_thesis != thesis_json:
                raise ValueError("thesis id collision with different immutable content")
            existing = self.connection.execute(
                "SELECT * FROM orders WHERE client_order_id=?", (proposal.client_order_id,)
            ).fetchone()
            if existing:
                expected = (
                    proposal.symbol,
                    proposal.side.value,
                    proposal.order_type,
                    str(proposal.price),
                    str(proposal.quantity),
                    proposal.thesis_id,
                    parent_client_order_id,
                )
                actual = (
                    existing["symbol"],
                    existing["side"],
                    existing["order_type"],
                    existing["price"],
                    existing["orig_qty"],
                    existing["thesis_id"],
                    existing["parent_client_order_id"],
                )
                if actual != expected:
                    raise ValueError("client order id collision with different immutable intent")
                return
            self.connection.execute(
                """
                INSERT OR IGNORE INTO orders(
                    client_order_id, symbol, side, order_type, price, orig_qty, status,
                    thesis_id, parent_client_order_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'PENDING_SUBMIT', ?, ?, ?, ?)
                """,
                (
                    proposal.client_order_id,
                    proposal.symbol,
                    proposal.side.value,
                    proposal.order_type,
                    str(proposal.price),
                    str(proposal.quantity),
                    proposal.thesis_id,
                    parent_client_order_id,
                    proposal.created_at.isoformat(),
                    _now(),
                ),
            )

    def order(self, client_order_id: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT * FROM orders WHERE client_order_id=?", (client_order_id,)
        ).fetchone()
        return dict(row) if row else None

    def order_by_exchange_id(self, exchange_order_id: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT * FROM orders WHERE exchange_order_id=?", (str(exchange_order_id),)
        ).fetchone()
        return dict(row) if row else None

    def adopt_remote_order(self, response: dict[str, Any]) -> str:
        """Adopt an agent-prefixed order found on the exchange that the local
        ledger has no record of (e.g. an ``elysia-`` order placed manually).

        Writes a minimal immutable adoption thesis plus the order row so that
        reconciliation can keep its status and fills tracked going forward.
        Idempotent: if the order already exists it is just refreshed.
        """
        client_id = response.get("clientOrderId") or response.get("origClientOrderId")
        if not client_id:
            raise ValueError("remote order has no clientOrderId")
        if self.order(client_id) is not None:
            self.update_order(response)
            return client_id
        token = hashlib.sha256(client_id.encode("utf-8")).hexdigest()[:8]
        thesis_id = f"adopted-{token}"
        if response.get("time"):
            created = datetime.fromtimestamp(
                int(response["time"]) / 1000, tz=timezone.utc
            ).isoformat()
        else:
            created = _now()
        thesis_payload = {
            "adopted_from_exchange": True,
            "client_order_id": client_id,
            "symbol": response.get("symbol"),
            "side": response.get("side"),
            "reason": "remote agent-prefixed order adopted during reconciliation",
        }
        with self.connection:
            self.connection.execute(
                "INSERT OR IGNORE INTO theses(thesis_id, created_at, payload_json) VALUES (?, ?, ?)",
                (
                    thesis_id,
                    created,
                    json.dumps(
                        thesis_payload,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                        default=_json_default,
                    ),
                ),
            )
            self.connection.execute(
                """
                INSERT OR IGNORE INTO orders(
                    client_order_id, exchange_order_id, symbol, side, order_type, price, orig_qty,
                    executed_qty, cumulative_quote_qty, status, thesis_id, parent_client_order_id,
                    pair_created, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, 0, ?, ?)
                """,
                (
                    client_id,
                    str(response["orderId"]) if response.get("orderId") is not None else None,
                    response.get("symbol") or "UNKNOWN",
                    response.get("side") or "UNKNOWN",
                    response.get("type") or "UNKNOWN",
                    str(response.get("price", "0")),
                    str(response.get("origQty", "0")),
                    str(response.get("executedQty", "0")),
                    str(
                        response.get(
                            "cummulativeQuoteQty", response.get("cumulativeQuoteQty", "0")
                        )
                    ),
                    str(response.get("status", "UNKNOWN")),
                    thesis_id,
                    created,
                    _now(),
                ),
            )
        if self.order(client_id) is None:
            raise ValueError(f"failed to persist adopted order {client_id!r}")
        return client_id

    def update_order(self, response: dict[str, Any]) -> None:
        client_id = response.get("clientOrderId") or response.get("origClientOrderId")
        local = self.order(client_id) if client_id else None
        if local is None and response.get("orderId") is not None:
            # Binance's cancel response returns an auto-generated clientOrderId;
            # match by exchange order id instead when the client id is unknown.
            local = self.order_by_exchange_id(str(response["orderId"]))
            if local is not None:
                client_id = local["client_order_id"]
        if not client_id or self.order(client_id) is None:
            raise ValueError(f"refusing to adopt unknown order {client_id!r}")
        existing = self.order(client_id)
        terminal = {"FILLED", "CANCELED", "REJECTED", "EXPIRED", "EXPIRED_IN_MATCH"}
        new_status = str(response.get("status", "UNKNOWN"))
        if existing["status"] in terminal and new_status != existing["status"]:
            raise ValueError("refusing an order status regression from a terminal state")
        new_executed = Decimal(str(response.get("executedQty", "0")))
        if new_executed < Decimal(existing["executed_qty"]):
            raise ValueError("refusing a decreasing executed quantity")
        with self.connection:
            self.connection.execute(
                """
                UPDATE orders SET exchange_order_id=COALESCE(?, exchange_order_id), status=?,
                    executed_qty=?, cumulative_quote_qty=?, updated_at=?
                WHERE client_order_id=?
                """,
                (
                    str(response["orderId"]) if response.get("orderId") is not None else None,
                    new_status,
                    str(new_executed),
                    str(response.get("cummulativeQuoteQty", response.get("cumulativeQuoteQty", "0"))),
                    _now(),
                    client_id,
                ),
            )

    def set_order_status(self, client_order_id: str, status: str) -> None:
        with self.connection:
            self.connection.execute(
                "UPDATE orders SET status=?, updated_at=? WHERE client_order_id=?",
                (status, _now(), client_order_id),
            )

    def local_open_orders(self) -> list[dict[str, Any]]:
        placeholders = ",".join("?" for _ in OPEN_STATUSES)
        rows = self.connection.execute(
            f"SELECT * FROM orders WHERE status IN ({placeholders}) ORDER BY created_at",
            tuple(OPEN_STATUSES),
        ).fetchall()
        return [dict(row) for row in rows]

    def known_order_ids(self) -> set[str]:
        return {row[0] for row in self.connection.execute("SELECT client_order_id FROM orders")}

    def record_trade(self, symbol: str, trade: dict[str, Any]) -> bool:
        exchange_order_id = str(trade["orderId"])
        if self.order_by_exchange_id(exchange_order_id) is None:
            return False
        trade_time = datetime.fromtimestamp(int(trade["time"]) / 1000, tz=timezone.utc).isoformat()
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT OR IGNORE INTO fills(
                    symbol, trade_id, exchange_order_id, price, qty, quote_qty, commission,
                    commission_asset, trade_time, is_buyer, is_maker
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    symbol,
                    str(trade["id"]),
                    exchange_order_id,
                    str(trade["price"]),
                    str(trade["qty"]),
                    str(trade["quoteQty"]),
                    str(trade["commission"]),
                    str(trade["commissionAsset"]),
                    trade_time,
                    int(bool(trade["isBuyer"])),
                    int(bool(trade["isMaker"])),
                ),
            )
        return cursor.rowcount == 1

    def fills_for_order(self, exchange_order_id: str) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT * FROM fills WHERE exchange_order_id=? ORDER BY trade_time", (str(exchange_order_id),)
        ).fetchall()
        return [dict(row) for row in rows]

    def unpaired_filled_orders(self) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT * FROM orders WHERE status='FILLED' AND pair_created=0 ORDER BY updated_at"
        ).fetchall()
        return [dict(row) for row in rows]

    def mark_pair_created(self, client_order_id: str) -> None:
        with self.connection:
            self.connection.execute(
                "UPDATE orders SET pair_created=1, updated_at=? WHERE client_order_id=?",
                (_now(), client_order_id),
            )

    def record_cycle(self, environment: str, regime: str, confidence: Decimal, action: str, payload: dict) -> None:
        with self.connection:
            self.connection.execute(
                "INSERT INTO cycles(created_at, environment, regime, confidence, action, payload_json) VALUES (?, ?, ?, ?, ?, ?)",
                (_now(), environment, regime, str(confidence), action, json.dumps(payload, default=_json_default)),
            )

    def record_balance(self, btc: Decimal, usdt: Decimal, reference_price: Decimal) -> Decimal:
        total = btc * reference_price + usdt
        with self.connection:
            self.connection.execute(
                "INSERT INTO balance_snapshots(created_at, btc_total, usdt_total, reference_price, total_value_usdt) VALUES (?, ?, ?, ?, ?)",
                (_now(), str(btc), str(usdt), str(reference_price), str(total)),
            )
        return total

    def daily_turnover(self) -> Decimal:
        day = datetime.now(timezone.utc).date().isoformat()
        rows = self.connection.execute(
            "SELECT quote_qty FROM fills WHERE substr(trade_time, 1, 10)=?",
            (day,),
        ).fetchall()
        return sum((Decimal(row[0]) for row in rows), Decimal("0"))

    def daily_loss(self, current_value: Decimal) -> Decimal:
        day = datetime.now(timezone.utc).date().isoformat()
        row = self.connection.execute(
            "SELECT total_value_usdt FROM balance_snapshots WHERE substr(created_at, 1, 10)=? ORDER BY snapshot_id LIMIT 1",
            (day,),
        ).fetchone()
        if not row:
            return Decimal("0")
        return max(Decimal("0"), Decimal(row[0]) - current_value)

    def summary(self) -> dict[str, Any]:
        return {
            "orders": self.connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
            "fills": self.connection.execute("SELECT COUNT(*) FROM fills").fetchone()[0],
            "cycles": self.connection.execute("SELECT COUNT(*) FROM cycles").fetchone()[0],
            "open_orders": len(self.local_open_orders()),
        }
