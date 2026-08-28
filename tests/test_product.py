from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
import tempfile
import time
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from spot_agent.binance_signed import (
    BinanceAPIError,
    BinanceSignedClient,
    HTTPResult,
    UnknownExecutionStatus,
)
from spot_agent.config import AgentConfig, load_config
from spot_agent.credentials import APICredentials
from spot_agent.execution import ExecutionEngine, ReconciliationError
from spot_agent.grid import build_stage2_grid
from spot_agent.journal import HashChainJournal
from spot_agent.live_lock import create_activation, verify_activation
from spot_agent.market_analysis import analyze_daily_klines
from spot_agent.pairing import build_paired_order
from spot_agent.preflight import run_preflight
from spot_agent.process_lock import ProcessLock
from spot_agent.rules import SymbolRules
from spot_agent.runner import run_cycle
from spot_agent.state import StateStore

D = Decimal
ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "btcusdt_exchange_info.json"


class SignedClientTests(unittest.TestCase):
    def test_signed_request_has_correct_hmac_and_never_contains_secret(self) -> None:
        captured = {}

        def transport(method, url, headers, timeout):
            captured.update(method=method, url=url, headers=headers, timeout=timeout)
            return HTTPResult({"canTrade": True, "balances": []}, {})

        credentials = APICredentials("api-key-123456789", "secret-abcdefghijklmnop", "test")
        client = BinanceSignedClient("testnet", credentials, transport=transport)
        with patch("spot_agent.binance_signed.time.time", return_value=1000.0):
            client.account()
        parsed = urlparse(captured["url"])
        parameters = parse_qs(parsed.query)
        supplied = parameters.pop("signature")[0]
        unsigned_query = parsed.query.rsplit("&signature=", 1)[0]
        expected = hmac.new(
            credentials.api_secret.encode(), unsigned_query.encode(), hashlib.sha256
        ).hexdigest()
        self.assertEqual(supplied, expected)
        self.assertEqual(captured["headers"]["X-MBX-APIKEY"], credentials.api_key)
        self.assertNotIn(credentials.api_secret, captured["url"])
        self.assertEqual(parameters["timestamp"], ["1000000"])

    def test_mutating_timeout_is_unknown_and_not_silently_retried(self) -> None:
        calls = 0

        def transport(*_args):
            nonlocal calls
            calls += 1
            raise TimeoutError("network timeout")

        client = BinanceSignedClient(
            "testnet", APICredentials("k" * 20, "s" * 20, "test"), transport=transport
        )
        with self.assertRaises(UnknownExecutionStatus):
            client.new_order({"symbol": "BTCUSDT"})
        self.assertEqual(calls, 1)


class FakePreflightClient:
    environment = "live"

    def __init__(self, permissions=None):
        self.permissions = permissions or {
            "ipRestrict": True,
            "enableReading": True,
            "enableSpotAndMarginTrading": True,
            "enableWithdrawals": False,
            "enableMargin": False,
            "enableFutures": False,
            "enableVanillaOptions": False,
            "enablePortfolioMarginTrading": False,
            "enableInternalTransfer": False,
            "permitsUniversalTransfer": False,
        }

    def sync_time(self):
        return 25

    def account(self):
        return {
            "canTrade": True,
            "accountType": "SPOT",
            "balances": [
                {"asset": "BTC", "free": "0.0005", "locked": "0.0001"},
                {"asset": "USDT", "free": "40", "locked": "10"},
            ],
        }

    def api_restrictions(self):
        return self.permissions

    def commission(self, _symbol):
        return {
            "standardCommission": {"maker": "0.0004", "taker": "0.0006", "buyer": "0.0001", "seller": "0.0002"},
            "specialCommission": {"maker": "0", "taker": "0", "buyer": "0", "seller": "0"},
            "taxCommission": {"maker": "0", "taker": "0", "buyer": "0", "seller": "0"},
        }


class ProductSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.rules = SymbolRules.from_exchange_info(payload)
        self.plan = build_stage2_grid(
            self.rules, D("76000"), D("0.03"), D("0.001"), D("0.001")
        )

    def test_live_preflight_accepts_least_privilege_and_sums_side_fees(self) -> None:
        result = run_preflight(FakePreflightClient())
        self.assertTrue(result.accepted, result.failures)
        self.assertEqual(result.maker_fee, D("0.0006"))
        self.assertEqual(result.taker_fee, D("0.0008"))
        self.assertEqual(result.free_balances["USDT"], D("40"))
        self.assertEqual(result.locked_balances["BTC"], D("0.0001"))

    def test_live_preflight_rejects_withdrawal_or_internal_transfer(self) -> None:
        permissions = dict(FakePreflightClient().permissions)
        permissions["enableWithdrawals"] = True
        permissions["enableInternalTransfer"] = True
        result = run_preflight(FakePreflightClient(permissions))
        self.assertFalse(result.accepted)
        self.assertIn("DANGEROUS_PERMISSION_enableWithdrawals", result.failures)
        self.assertIn("DANGEROUS_PERMISSION_enableInternalTransfer", result.failures)

    def test_all_shipped_configs_validate(self) -> None:
        for name in ("config.testnet.toml", "config.stage1-live.toml", "config.stage2-live.toml"):
            with self.subTest(name=name):
                self.assertEqual(load_config(ROOT / name).symbol, "BTCUSDT")

    def test_live_activation_is_machine_stage_cap_and_checksum_bound(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "activation.json"
            create_activation(path, 2, D("100"), hours=1)
            self.assertTrue(verify_activation(path, 2, D("100"))[0])
            self.assertFalse(verify_activation(path, 1, D("100"))[0])
            content = json.loads(path.read_text(encoding="utf-8"))
            content["capital_cap_usdt"] = "1000"
            path.write_text(json.dumps(content), encoding="utf-8")
            self.assertEqual(verify_activation(path, 2, D("100"))[1], "LIVE_ACTIVATION_TAMPERED")

    def test_cross_process_style_lock_rejects_second_cycle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "agent.lock"
            with ProcessLock(path):
                with self.assertRaisesRegex(RuntimeError, "already running"):
                    with ProcessLock(path):
                        self.fail("second lock must never be acquired")

    def test_state_keeps_theses_and_fills_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with StateStore(Path(directory) / "state.sqlite3") as state:
                proposal = self.plan.orders[0]
                state.record_proposal(proposal)
                state.update_order({
                    "clientOrderId": proposal.client_order_id,
                    "orderId": 42,
                    "status": "FILLED",
                    "executedQty": str(proposal.quantity),
                    "cummulativeQuoteQty": str(proposal.notional),
                })
                inserted = state.record_trade("BTCUSDT", {
                    "id": 7, "orderId": 42, "price": str(proposal.price),
                    "qty": str(proposal.quantity), "quoteQty": str(proposal.notional),
                    "commission": "0.0000001", "commissionAsset": "BTC",
                    "time": int(time.time() * 1000), "isBuyer": True, "isMaker": True,
                })
                self.assertTrue(inserted)
                with self.assertRaises(sqlite3.IntegrityError):
                    state.connection.execute("UPDATE theses SET payload_json='{}'")
                with self.assertRaises(sqlite3.IntegrityError):
                    state.connection.execute("DELETE FROM fills")

    def test_state_rejects_id_collisions_and_terminal_regressions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with StateStore(Path(directory) / "state.sqlite3") as state:
                proposal = self.plan.orders[0]
                state.record_proposal(proposal)
                conflicting = proposal.__class__(
                    **{
                        **proposal.__dict__,
                        "price": proposal.price + D("1"),
                        "thesis_id": proposal.thesis_id + "-different",
                    }
                )
                with self.assertRaisesRegex(ValueError, "client order id collision"):
                    state.record_proposal(conflicting)
                state.update_order({
                    "clientOrderId": proposal.client_order_id, "orderId": 42, "status": "FILLED",
                    "executedQty": str(proposal.quantity), "cummulativeQuoteQty": str(proposal.notional),
                })
                with self.assertRaisesRegex(ValueError, "status regression"):
                    state.update_order({
                        "clientOrderId": proposal.client_order_id, "orderId": 42, "status": "NEW",
                        "executedQty": str(proposal.quantity), "cummulativeQuoteQty": str(proposal.notional),
                    })

    def test_pair_uses_actual_fill_minus_base_fee_and_buffer(self) -> None:
        parent = {
            "client_order_id": "asv1-parent",
            "status": "FILLED",
            "side": "BUY",
        }
        fills = [{
            "qty": "0.00013", "quote_qty": "9.88", "commission": "0.00000013",
            "commission_asset": "BTC",
        }]
        pair = build_paired_order(parent, fills, self.rules, D("0.01"))
        self.assertIsNotNone(pair)
        self.assertEqual(pair.side.value, "SELL")
        self.assertEqual(pair.quantity, D("0.00011"))
        self.assertTrue(pair.client_order_id.startswith("asv1-"))

    def test_execution_timeout_persists_unknown_without_retry(self) -> None:
        class UnknownClient:
            def new_order(self, _params):
                raise UnknownExecutionStatus("unknown")

        with tempfile.TemporaryDirectory() as directory:
            with StateStore(Path(directory) / "state.sqlite3") as state:
                engine = ExecutionEngine(
                    UnknownClient(), state, HashChainJournal(Path(directory) / "journal.jsonl")
                )
                result = engine.submit(self.plan.orders[0])
                self.assertIsNone(result)
                self.assertEqual(state.order(self.plan.orders[0].client_order_id)["status"], "UNKNOWN")

    def test_unknown_order_requires_human_confirmation_before_release(self) -> None:
        class NotFoundClient:
            def get_order(self, _symbol, _client_id):
                raise BinanceAPIError(400, -2013, "Order does not exist")

        with tempfile.TemporaryDirectory() as directory:
            with StateStore(Path(directory) / "state.sqlite3") as state:
                journal = HashChainJournal(Path(directory) / "journal.jsonl")
                state.record_proposal(self.plan.orders[0])
                state.set_order_status(self.plan.orders[0].client_order_id, "UNKNOWN")
                engine = ExecutionEngine(NotFoundClient(), state, journal)
                with self.assertRaises(ReconciliationError):
                    engine.resolve_unknown(self.plan.orders[0].client_order_id)
                self.assertEqual(
                    state.order(self.plan.orders[0].client_order_id)["status"], "UNKNOWN"
                )
                result = engine.resolve_unknown(
                    self.plan.orders[0].client_order_id, confirm_not_found=True
                )
                self.assertEqual(result["resolution"], "HUMAN_CONFIRMED_NOT_FOUND")
                self.assertEqual(
                    state.order(self.plan.orders[0].client_order_id)["status"], "REJECTED"
                )

    def test_reconciliation_blocks_remote_agent_order_without_local_thesis(self) -> None:
        class RemoteClient:
            def open_orders(self, _symbol):
                return [{"clientOrderId": "asv1-foreign", "status": "NEW"}]

        with tempfile.TemporaryDirectory() as directory:
            with StateStore(Path(directory) / "state.sqlite3") as state:
                engine = ExecutionEngine(
                    RemoteClient(), state, HashChainJournal(Path(directory) / "journal.jsonl")
                )
                with self.assertRaises(ReconciliationError):
                    engine.reconcile()

    def test_reconciliation_adopts_elysia_remote_order(self) -> None:
        remote = {
            "clientOrderId": "elysia-sell-test01",
            "orderId": 7000000001,
            "symbol": "BTCUSDT",
            "side": "SELL",
            "type": "LIMIT_MAKER",
            "price": "83400.00",
            "origQty": "0.00006000",
            "executedQty": "0.00000000",
            "status": "NEW",
            "time": 1787880000000,
        }

        class RemoteClient:
            def open_orders(self, _symbol):
                return [remote]

            def trades(self, _symbol):
                return []

        with tempfile.TemporaryDirectory() as directory:
            with StateStore(Path(directory) / "state.sqlite3") as state:
                engine = ExecutionEngine(
                    RemoteClient(), state, HashChainJournal(Path(directory) / "journal.jsonl")
                )
                result = engine.reconcile()
                self.assertEqual(result["adopted"], 1)
                self.assertEqual(result["remote_agent_open"], 1)
                order = state.order("elysia-sell-test01")
                self.assertIsNotNone(order)
                self.assertEqual(order["status"], "NEW")
                self.assertEqual(order["side"], "SELL")
                self.assertTrue(order["thesis_id"].startswith("adopted-"))
                # second reconcile is idempotent — no new adoption
                result2 = engine.reconcile()
                self.assertEqual(result2["adopted"], 0)

    def test_reconciliation_can_cancel_adopted_elysia_order(self) -> None:
        remote = {
            "clientOrderId": "elysia-sell-cancelme",
            "orderId": 7000000002,
            "symbol": "BTCUSDT",
            "side": "SELL",
            "type": "LIMIT_MAKER",
            "price": "83400.00",
            "origQty": "0.00006000",
            "executedQty": "0.00000000",
            "status": "NEW",
            "time": 1787880000000,
        }

        class RemoteClient:
            def __init__(self):
                self.open = [remote]
                self.canceled = None

            def open_orders(self, _symbol):
                return self.open

            def cancel_order(self, _symbol, client_id):
                self.canceled = client_id
                self.open = []
                return {**remote, "status": "CANCELED"}

            def trades(self, _symbol):
                return []

        with tempfile.TemporaryDirectory() as directory:
            with StateStore(Path(directory) / "state.sqlite3") as state:
                engine = ExecutionEngine(
                    RemoteClient(), state, HashChainJournal(Path(directory) / "journal.jsonl")
                )
                engine.reconcile()
                self.assertIsNotNone(state.order("elysia-sell-cancelme"))
                engine.cancel("elysia-sell-cancelme")
                self.assertEqual(state.order("elysia-sell-cancelme")["status"], "CANCELED")

    def test_market_analysis_uses_only_closed_candles(self) -> None:
        now_ms = int(time.time() * 1000)
        day_ms = 86_400_000
        klines = []
        for index in range(40):
            close = D("100") + (D("1") if index % 2 else D("-1"))
            close_time = now_ms - (40 - index) * day_ms
            klines.append([0, "100", "102", "98", str(close), "1000", close_time])
        klines.append([0, "100", "200", "50", "150", "9999", now_ms + day_ms])
        analyzed = analyze_daily_klines(klines)
        self.assertEqual(analyzed.closed_candles, 40)
        self.assertEqual(analyzed.features.price, D("101"))
        self.assertTrue(analyzed.features.data_valid)

    def test_full_testnet_cycle_dry_run_then_six_idempotent_submissions(self) -> None:
        class FakeExchange:
            environment = "testnet"

            def __init__(self):
                self.submitted = []

            def sync_time(self):
                return 0

            def account(self):
                return {
                    "canTrade": True,
                    "accountType": "SPOT",
                    "balances": [
                        {"asset": "BTC", "free": str(D("50") / D("76000")), "locked": "0"},
                        {"asset": "USDT", "free": "50", "locked": "0"},
                    ],
                }

            def commission(self, _symbol):
                return {"standardCommission": {"maker": "0.001", "taker": "0.001", "buyer": "0", "seller": "0"}}

            def exchange_info(self, _symbol):
                return json.loads(FIXTURE.read_text(encoding="utf-8"))

            def ticker_price(self, _symbol):
                return D("76000")

            def klines(self, _symbol, _interval, _limit):
                now_ms = int(time.time() * 1000)
                day_ms = 86_400_000
                rows = []
                for index in range(60):
                    close = D("76000") + (D("1000") if index % 2 else D("-1000"))
                    rows.append([0, "76000", "78000", "74000", str(close), "1000", now_ms - (60 - index) * day_ms])
                return rows

            def open_orders(self, _symbol):
                return list(self.submitted)

            def trades(self, _symbol):
                return []

            def get_order(self, _symbol, client_id):
                return next(item for item in self.submitted if item["clientOrderId"] == client_id)

            def new_order(self, params):
                response = {
                    "clientOrderId": params["newClientOrderId"],
                    "orderId": len(self.submitted) + 1,
                    "status": "NEW",
                    "executedQty": "0",
                    "cummulativeQuoteQty": "0",
                }
                self.submitted.append(response)
                return response

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = AgentConfig(
                environment="testnet", stage=2, database_path=root / "state.sqlite3",
                journal_path=root / "journal.jsonl", activation_path=root / "unused.json",
            ).validate()
            fake = FakeExchange()
            with patch("spot_agent.runner.load_credentials", return_value=APICredentials("k" * 20, "s" * 20, "test")), patch(
                "spot_agent.runner.BinanceSignedClient", return_value=fake
            ):
                dry = run_cycle(config, execute=False)
                self.assertEqual(dry["action"], "DRY_RUN_ACCEPTED")
                self.assertEqual(len(fake.submitted), 0)
                executed = run_cycle(config, execute=True)
                self.assertEqual(executed["action"], "ORDERS_SUBMITTED")
                self.assertEqual(len(fake.submitted), 6)
                self.assertEqual(len({item["clientOrderId"] for item in fake.submitted}), 6)
                self.assertTrue(all(item["clientOrderId"].startswith("asv1-") for item in fake.submitted))


if __name__ == "__main__":
    unittest.main()
