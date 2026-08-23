from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from spot_agent.grid import build_stage2_grid, grid_spacing, sellable_quantity_from_buy
from spot_agent.journal import HashChainJournal
from spot_agent.models import BalanceSnapshot, Regime, Side
from spot_agent.regime import MarketFeatures, detect_regime
from spot_agent.risk_gate import RiskGate, RiskLimits
from spot_agent.rules import SymbolRules
from spot_agent.simulator import SimulationExecutor

D = Decimal
FIXTURE = Path(__file__).parent / "fixtures" / "btcusdt_exchange_info.json"


class HarnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rules = SymbolRules.from_exchange_info(json.loads(FIXTURE.read_text(encoding="utf-8")))
        self.price = D("76000")
        self.plan = build_stage2_grid(
            self.rules, self.price, D("0.03"), D("0.001"), D("0.001")
        )
        self.balances = BalanceSnapshot(D("50") / self.price, D("50"))

    def test_rules_parse_notional_and_round(self) -> None:
        self.assertEqual(self.rules.min_notional, D("5"))
        self.assertEqual(self.rules.round_price(D("75239.999")), D("75239.99"))
        self.assertEqual(self.rules.round_qty(D("0.00013157")), D("0.00013"))

    def test_min_notional_variant_and_missing_filter_fail_closed(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["symbols"][0]["filters"][-1] = {
            "filterType": "MIN_NOTIONAL", "minNotional": "7.00000000", "applyToMarket": True
        }
        self.assertEqual(SymbolRules.from_exchange_info(payload).min_notional, D("7"))
        payload["symbols"][0]["filters"].pop()
        with self.assertRaisesRegex(ValueError, "fail closed"):
            SymbolRules.from_exchange_info(payload)

    def test_grid_is_six_orders_near_one_percent(self) -> None:
        self.assertEqual(self.plan.spacing, D("0.010"))
        self.assertEqual(len(self.plan.orders), 6)
        self.assertEqual(sum(o.side is Side.BUY for o in self.plan.orders), 3)
        self.assertEqual(sum(o.side is Side.SELL for o in self.plan.orders), 3)
        for order in self.plan.orders:
            self.assertFalse(self.rules.validate_limit(order.price, order.quantity))
            self.assertGreaterEqual(order.notional, D("5"))
            self.assertLessEqual(order.notional, D("10"))

    def test_spacing_cost_floor_and_panic_no_grid(self) -> None:
        spacing, cost = grid_spacing(D("0.001"), D("0.001"), D("0.001"), D("0.005"))
        self.assertEqual(cost, D("0.003"))
        self.assertEqual(spacing, D("0.009"))
        with self.assertRaisesRegex(ValueError, "NO_TRADE"):
            build_stage2_grid(
                self.rules, self.price, D("0.03"), D("0.001"), D("0.001"), regime=Regime.PANIC
            )

    def test_fee_deducted_sellable_quantity_has_buffer(self) -> None:
        quantity = sellable_quantity_from_buy(
            D("0.00013"), D("0.00000013"), "BTC", "BTC", D("0.00001"), 1
        )
        self.assertEqual(quantity, D("0.00011"))

    def test_risk_gate_accepts_allocated_grid(self) -> None:
        decision = RiskGate(RiskLimits(), self.rules).evaluate_batch(
            self.plan.orders, self.balances, self.price
        )
        self.assertTrue(decision.accepted, decision.reasons)

    def test_risk_gate_rejects_duplicate_stale_live_and_reserve_breach(self) -> None:
        stale = replace(
            self.plan.orders[0], created_at=datetime.now(timezone.utc) - timedelta(minutes=5)
        )
        gate = RiskGate(replace(RiskLimits(), environment="LIVE"), self.rules)
        decision = gate.evaluate_batch(
            (stale, stale), BalanceSnapshot(D("0"), D("5")), self.price, kill_switch=True
        )
        self.assertFalse(decision.accepted)
        self.assertIn("LIVE_EXECUTION_DISABLED", decision.reasons)
        self.assertIn("KILL_SWITCH_ACTIVE", decision.reasons)
        self.assertIn("DUPLICATE_ORDER_ID", decision.reasons)
        self.assertIn("STALE_OR_FUTURE_PROPOSAL", decision.reasons)
        self.assertIn("QUOTE_RESERVE_BREACH", decision.reasons)

    def test_risk_gate_fails_closed_on_nan_and_zero_reference(self) -> None:
        gate = RiskGate(RiskLimits(), self.rules)
        decision = gate.evaluate_batch(self.plan.orders, self.balances, D("NaN"))
        self.assertFalse(decision.accepted)
        self.assertIn("INVALID_NUMERIC_CONTEXT", decision.reasons)
        malformed = replace(self.plan.orders[0], price=D("NaN"))
        decision = gate.evaluate_batch((malformed,), self.balances, self.price)
        self.assertFalse(decision.accepted)
        self.assertIn("NON_FINITE_OR_NON_POSITIVE_ORDER", decision.reasons)

    def test_hash_chain_detects_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "journal.jsonl"
            journal = HashChainJournal(path)
            journal.append("TEST", {"amount": D("1.25")})
            self.assertTrue(journal.verify()[0])
            path.write_text(path.read_text(encoding="utf-8").replace("1.25", "9.25"), encoding="utf-8")
            self.assertFalse(journal.verify()[0])

    def test_simulated_fill_records_actual_fee_and_balance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            journal = HashChainJournal(Path(directory) / "journal.jsonl")
            executor = SimulationExecutor(self.balances, RiskGate(RiskLimits(), self.rules), journal)
            executor.place_batch(self.plan.orders, self.price)
            self.assertGreater(executor.balances.base_locked, D("0"))
            self.assertGreater(executor.balances.quote_locked, D("0"))
            buy = next(order for order in self.plan.orders if order.side is Side.BUY)
            locked_before = executor.balances.quote_locked
            executor.fill(buy.client_order_id, D("0.001"))
            self.assertEqual(len(executor.open_orders), 5)
            self.assertGreater(executor.balances.base_free, self.balances.base_free - self.plan.base_required)
            self.assertLess(executor.balances.quote_free, self.balances.quote_free)
            self.assertEqual(executor.balances.quote_locked, locked_before - buy.notional)
            self.assertTrue(journal.verify()[0])

    def test_cancel_releases_locked_balance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executor = SimulationExecutor(
                self.balances,
                RiskGate(RiskLimits(), self.rules),
                HashChainJournal(Path(directory) / "journal.jsonl"),
            )
            executor.place_batch(self.plan.orders, self.price)
            sell = next(order for order in self.plan.orders if order.side is Side.SELL)
            free_before = executor.balances.base_free
            locked_before = executor.balances.base_locked
            executor.cancel(sell.client_order_id)
            self.assertEqual(executor.balances.base_free, free_before + sell.quantity)
            self.assertEqual(executor.balances.base_locked, locked_before - sell.quantity)

    def test_regime_outputs_range_breakout_panic_and_uncertain(self) -> None:
        base = MarketFeatures(
            price=D("100"), short_ma=D("100.1"), medium_ma=D("100"), short_ma_slope=D("0"),
            volume_ratio=D("1"), daily_volatility=D("0.02"), previous_range_low=D("95"),
            previous_range_high=D("105")
        )
        self.assertEqual(detect_regime(base).regime, Regime.RANGE)
        self.assertEqual(detect_regime(replace(base, price=D("106"), volume_ratio=D("1.6"))).regime, Regime.BREAKOUT)
        self.assertEqual(detect_regime(replace(base, risk_event=True)).regime, Regime.PANIC)
        self.assertEqual(detect_regime(replace(base, data_valid=False)).regime, Regime.UNCERTAIN)


if __name__ == "__main__":
    unittest.main()
