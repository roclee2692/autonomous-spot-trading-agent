from __future__ import annotations

import json
import uuid
from dataclasses import asdict, replace
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from .binance_signed import BinanceSignedClient
from .config import AgentConfig
from .credentials import load_credentials
from .execution import ExecutionEngine
from .grid import build_stage2_grid, grid_spacing
from .journal import HashChainJournal
from .live_lock import verify_activation
from .market_analysis import analyze_daily_klines
from .models import BalanceSnapshot, Regime, Side, TradeProposal, utc_now
from .pairing import build_paired_order
from .preflight import PreflightResult, run_preflight
from .process_lock import ProcessLock
from .regime import detect_regime
from .risk_gate import RiskGate, RiskLimits
from .rules import SymbolRules
from .state import StateStore

D = Decimal


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _live_policy_enabled() -> bool:
    policy = json.loads((_project_root() / "policies" / "constitution.json").read_text(encoding="utf-8"))
    return policy.get("live_trading_enabled") is True


def _kill_switch_path(config: AgentConfig) -> Path:
    return config.database_path.parent / "KILL_SWITCH"


def set_kill_switch(config: AgentConfig, active: bool) -> str:
    path = _kill_switch_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    if active:
        path.write_text(datetime.now(timezone.utc).isoformat(), encoding="utf-8")
        return f"kill switch activated at {path}"
    if path.exists():
        path.unlink()
    return f"kill switch cleared at {path}"


def _smoke_buy(rules: SymbolRules, price: Decimal, budget: Decimal) -> TradeProposal:
    now = utc_now()
    token = uuid.uuid4().hex[:8]
    order_price = rules.round_price(price * D("0.99"))
    quantity = rules.round_qty(budget / order_price)
    failures = rules.validate_limit(order_price, quantity)
    if failures:
        raise ValueError(f"Stage 1 smoke order violates {failures}")
    return TradeProposal(
        client_order_id=f"asv1-s{token}-b",
        symbol=rules.symbol,
        market_type="SPOT",
        side=Side.BUY,
        order_type="LIMIT_MAKER",
        price=order_price,
        quantity=quantity,
        created_at=now,
        regime=Regime.RANGE,
        strategy="STAGE1_LIVE_SMOKE",
        reason="single post-only buy validates the real order lifecycle; profit is not the objective",
        thesis_id=f"smoke-{token}-buy",
        evidence=(f"reference_price={price}", "stage=1", "max_concurrent_orders=1"),
        invalidating_conditions=("regime leaves RANGE", "risk veto", "data becomes stale"),
        exit_conditions=("paired sell completes", "human cancels", "thesis invalidated"),
    )


def _risk_gate(config: AgentConfig, rules: SymbolRules) -> RiskGate:
    return RiskGate(
        RiskLimits(
            environment=config.environment.upper(),
            allowed_symbol=config.symbol,
            max_open_orders=config.max_open_orders,
            max_order_notional=config.order_budget,
            max_daily_turnover=config.max_daily_turnover,
            quote_reserve=config.quote_reserve,
            core_base_value=config.core_btc_value,
            max_data_age_seconds=config.max_data_age_seconds,
            max_daily_loss=config.max_daily_loss,
            max_buy_fee_rate=config.maximum_fee_rate,
        ),
        rules,
    )


def _live_submit_authorized(config: AgentConfig, execute: bool) -> tuple[bool, str]:
    if not execute:
        return False, "DRY_RUN"
    if config.environment == "testnet":
        return True, "TESTNET_EXECUTION_REQUESTED"
    if config.environment != "live":
        return False, "SIMULATION_ONLY"
    if not _live_policy_enabled():
        return False, "CONSTITUTION_LIVE_FLAG_FALSE"
    return verify_activation(config.activation_path, config.stage, config.maximum_account_value)


def _market(client: BinanceSignedClient, config: AgentConfig) -> tuple[SymbolRules, Decimal, Any]:
    rules = SymbolRules.from_exchange_info(client.exchange_info(config.symbol), config.symbol)
    price = client.ticker_price(config.symbol)
    analyzed = analyze_daily_klines(client.klines(config.symbol, "1d", 60))
    features = replace(analyzed.features, price=price)
    analyzed = replace(analyzed, features=features, decision=detect_regime(features))
    return rules, price, analyzed


def _account_value(preflight: PreflightResult, price: Decimal) -> Decimal:
    return preflight.balances.get("BTC", D("0")) * price + preflight.balances.get("USDT", D("0"))


def _run_cycle_locked(
    config: AgentConfig, *, execute: bool = False, news_veto: bool = False
) -> dict[str, Any]:
    if config.environment == "simulation":
        raise ValueError("run-cycle uses authenticated Testnet/Live; use demo for simulation")
    journal = HashChainJournal(config.journal_path)
    journal_ok, journal_message = journal.verify()
    if not journal_ok:
        raise RuntimeError(f"journal integrity failure: {journal_message}")
    credentials = load_credentials(config.environment)
    client = BinanceSignedClient(config.environment, credentials)
    preflight = run_preflight(client, config.symbol)
    rules, price, analyzed = _market(client, config)
    kill_switch = _kill_switch_path(config).exists()
    submit_authorized, authorization_reason = _live_submit_authorized(config, execute)

    with StateStore(config.database_path) as state:
        if state.summary()["orders"] and journal_message == "verified 0 records":
            raise RuntimeError("state exists but the immutable journal is empty")
        engine = ExecutionEngine(client, state, journal)
        reconciliation = engine.reconcile(config.symbol)
        btc_total = preflight.balances.get("BTC", D("0"))
        usdt_total = preflight.balances.get("USDT", D("0"))
        account_value = _account_value(preflight, price)
        current_value = state.record_balance(btc_total, usdt_total, price)
        daily_loss = state.daily_loss(current_value)
        failures = list(preflight.failures)
        if preflight.maker_fee is None or preflight.maker_fee > config.maximum_fee_rate:
            failures.append("FEE_EXCEEDS_CONFIGURED_MAXIMUM")
        if config.environment == "live":
            unexpected_assets = sorted(
                asset for asset, amount in preflight.balances.items() if amount != 0 and asset not in {"BTC", "USDT"}
            )
            if unexpected_assets:
                failures.append(f"UNEXPECTED_SUBACCOUNT_ASSETS_{','.join(unexpected_assets)}")
            if account_value > config.maximum_account_value * D("1.05"):
                failures.append("ACCOUNT_VALUE_EXCEEDS_CAP_BY_MORE_THAN_5_PERCENT")
        if failures:
            journal.append("PREFLIGHT_REJECTED", {"failures": failures, "checks": preflight.checks})
            state.record_cycle(
                config.environment,
                analyzed.decision.regime.value,
                analyzed.decision.confidence,
                "NO_TRADE_PREFLIGHT",
                {"failures": failures},
            )
            return {"action": "NO_TRADE_PREFLIGHT", "failures": failures, "checks": preflight.checks}

        open_orders = state.local_open_orders()
        if kill_switch or news_veto or analyzed.decision.regime in {Regime.PANIC, Regime.UNCERTAIN}:
            canceled: list[str] = []
            if execute:
                for order in open_orders:
                    engine.cancel(order["client_order_id"], config.symbol)
                    canceled.append(order["client_order_id"])
            action = "PAUSE_AND_CANCEL" if canceled else "NO_TRADE_PAUSED"
            payload = {
                "kill_switch": kill_switch,
                "news_veto": news_veto,
                "regime": analyzed.decision.regime,
                "canceled": canceled,
            }
            journal.append(action, payload)
            state.record_cycle(config.environment, analyzed.decision.regime.value, analyzed.decision.confidence, action, payload)
            return {"action": action, **payload}

        if analyzed.decision.regime is not Regime.RANGE and not config.allow_trend_grid:
            canceled: list[str] = []
            if execute:
                for order in open_orders:
                    engine.cancel(order["client_order_id"], config.symbol)
                    canceled.append(order["client_order_id"])
            action = "NO_TRADE_NON_RANGE"
            state.record_cycle(
                config.environment, analyzed.decision.regime.value, analyzed.decision.confidence, action,
                {"canceled": canceled},
            )
            return {"action": action, "regime": analyzed.decision.regime, "canceled": canceled}

        maker_fee = max(preflight.maker_fee or D("0"), config.maximum_fee_rate)
        spacing, _ = grid_spacing(maker_fee, maker_fee, config.assumed_slippage, analyzed.features.daily_volatility)
        proposals_with_parent: list[tuple[TradeProposal, str | None]] = []
        for parent in state.unpaired_filled_orders():
            fills = state.fills_for_order(parent["exchange_order_id"])
            paired = build_paired_order(parent, fills, rules, spacing)
            if paired is not None:
                proposals_with_parent.append((paired, parent["client_order_id"]))
            else:
                state.mark_pair_created(parent["client_order_id"])
                journal.append("PAIR_SKIPPED_BELOW_FILTERS", {"parent": parent["client_order_id"]})

        available_slots = max(0, config.max_open_orders - len(open_orders))
        proposals_with_parent = proposals_with_parent[:available_slots]
        if not proposals_with_parent and open_orders:
            action = "HOLD_EXISTING_GRID"
            state.record_cycle(config.environment, "RANGE", analyzed.decision.confidence, action, reconciliation)
            return {"action": action, "open_orders": len(open_orders), "spacing": spacing}

        if not proposals_with_parent:
            if config.stage == 1:
                if state.summary()["fills"] >= 2:
                    action = "STAGE1_SMOKE_COMPLETE"
                    state.record_cycle(config.environment, "RANGE", analyzed.decision.confidence, action, {})
                    return {"action": action}
                proposals_with_parent = [(_smoke_buy(rules, price, config.order_budget), None)]
            else:
                plan = build_stage2_grid(
                    rules,
                    reference_price=price,
                    daily_volatility=analyzed.features.daily_volatility,
                    maker_buy_fee=maker_fee,
                    maker_sell_fee=maker_fee,
                    slippage=config.assumed_slippage,
                    levels_per_side=config.levels_per_side,
                    quote_budget_per_order=config.order_budget,
                )
                proposals_with_parent = [(proposal, None) for proposal in plan.orders]

        proposals = tuple(item[0] for item in proposals_with_parent)
        balances = BalanceSnapshot(
            base_free=preflight.free_balances.get("BTC", D("0")),
            quote_free=preflight.free_balances.get("USDT", D("0")),
            base_locked=preflight.locked_balances.get("BTC", D("0")),
            quote_locked=preflight.locked_balances.get("USDT", D("0")),
        )
        decision = _risk_gate(config, rules).evaluate_batch(
            proposals,
            balances,
            price,
            existing_order_ids=state.known_order_ids(),
            current_open_orders=len(open_orders),
            daily_turnover=state.daily_turnover(),
            daily_loss=daily_loss,
            kill_switch=kill_switch,
            news_veto=news_veto,
            execution_authorized=submit_authorized or not execute,
        )
        if not decision.accepted:
            state.record_cycle(config.environment, "RANGE", analyzed.decision.confidence, decision.code, {"reasons": decision.reasons})
            return {"action": decision.code, "reasons": decision.reasons}
        if not execute:
            payload = {
                "action": "DRY_RUN_ACCEPTED",
                "authorization": authorization_reason,
                "spacing": spacing,
                "proposals": [asdict(proposal) for proposal in proposals],
            }
            journal.append("DRY_RUN_ACCEPTED", payload)
            state.record_cycle(config.environment, "RANGE", analyzed.decision.confidence, "DRY_RUN_ACCEPTED", payload)
            return payload
        if not submit_authorized:
            return {"action": "REJECT_ORDER", "reasons": (authorization_reason,)}

        submitted: list[str] = []
        for proposal, parent_id in proposals_with_parent:
            response = engine.submit(proposal, parent_id)
            submitted.append(proposal.client_order_id)
            if parent_id is not None:
                state.mark_pair_created(parent_id)
            if response is None:
                break
        action = "ORDERS_SUBMITTED" if len(submitted) == len(proposals) else "SUBMISSION_STATUS_UNKNOWN"
        state.record_cycle(config.environment, "RANGE", analyzed.decision.confidence, action, {"submitted": submitted})
        return {
            "action": action,
            "submitted": submitted,
            "spacing": spacing,
            "reconciliation": reconciliation,
        }


def run_cycle(
    config: AgentConfig, *, execute: bool = False, news_veto: bool = False
) -> dict[str, Any]:
    lock_path = config.database_path.with_suffix(config.database_path.suffix + ".lock")
    with ProcessLock(lock_path):
        return _run_cycle_locked(config, execute=execute, news_veto=news_veto)
