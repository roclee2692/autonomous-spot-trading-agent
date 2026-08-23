from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path

from .binance_public import BinancePublicClient
from .binance_signed import BinanceSignedClient
from .config import load_config
from .credentials import (
    credential_status,
    delete_credentials,
    load_credentials,
    store_credentials_interactive,
)
from .execution import ExecutionEngine
from .grid import build_stage2_grid
from .journal import HashChainJournal
from .live_lock import CONFIRMATION, create_activation
from .models import BalanceSnapshot
from .preflight import run_preflight
from .reporting import write_status_report
from .risk_gate import RiskGate, RiskLimits
from .rules import SymbolRules
from .runner import run_cycle, set_kill_switch
from .simulator import SimulationExecutor
from .state import StateStore


def _json_default(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    raise TypeError(type(value).__name__)


def _print(value) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=_json_default))


def command_market(_: argparse.Namespace) -> int:
    client = BinancePublicClient()
    rules = client.symbol_rules()
    price, fetched_at = client.ticker_price()
    _print({"fetched_at": fetched_at, "price": price, "rules": asdict(rules), "read_only": True})
    return 0


def _live_plan(args: argparse.Namespace):
    client = BinancePublicClient()
    rules = client.symbol_rules()
    price, _ = client.ticker_price()
    return rules, price, build_stage2_grid(
        rules, reference_price=price, daily_volatility=Decimal(args.daily_volatility),
        maker_buy_fee=Decimal(args.maker_fee), maker_sell_fee=Decimal(args.maker_fee),
        slippage=Decimal(args.slippage),
    )


def command_plan(args: argparse.Namespace) -> int:
    _, _, plan = _live_plan(args)
    _print(asdict(plan))
    return 0


def command_demo(args: argparse.Namespace) -> int:
    client = BinancePublicClient()
    rules = client.symbol_rules()
    price = Decimal(args.price)
    plan = build_stage2_grid(
        rules, reference_price=price, daily_volatility=Decimal(args.daily_volatility),
        maker_buy_fee=Decimal(args.maker_fee), maker_sell_fee=Decimal(args.maker_fee),
    )
    journal = HashChainJournal(Path(args.journal))
    gate = RiskGate(RiskLimits(), rules)
    balances = BalanceSnapshot(base_free=Decimal("50") / price, quote_free=Decimal("50"))
    executor = SimulationExecutor(balances, gate, journal)
    executor.place_batch(plan.orders, price)
    first_buy = next(o for o in plan.orders if o.side.value == "BUY")
    executor.fill(first_buy.client_order_id, Decimal(args.maker_fee))
    _print({
        "mode": "SIMULATION", "journal": str(journal.path.resolve()), "spacing": plan.spacing,
        "open_orders": len(executor.open_orders),
        "balances_after_one_simulated_fill": asdict(executor.balances),
        "journal_verification": journal.verify(),
    })
    return 0


def command_verify(args: argparse.Namespace) -> int:
    ok, message = HashChainJournal(args.path).verify()
    _print({"valid": ok, "message": message})
    return 0 if ok else 2


def command_credentials(args: argparse.Namespace) -> int:
    if args.operation == "set":
        _print({"result": store_credentials_interactive(args.environment)})
    elif args.operation == "delete":
        confirmation = input(f"Type DELETE {args.environment.upper()} to remove local credentials: ")
        if confirmation != f"DELETE {args.environment.upper()}":
            raise ValueError("confirmation did not match; credentials were not deleted")
        _print({"result": delete_credentials(args.environment)})
    else:
        _print(credential_status(args.environment))
    return 0


def command_config_check(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    _print({"valid": True, "config": asdict(config), "secrets_in_config": False})
    return 0


def command_preflight(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    if config.environment == "simulation":
        raise ValueError("authenticated preflight requires testnet or live")
    client = BinanceSignedClient(config.environment, load_credentials(config.environment))
    result = run_preflight(client, config.symbol)
    _print(asdict(result))
    return 0 if result.accepted else 2


def command_order_test(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    if config.environment == "simulation":
        raise ValueError("signed order test requires testnet or live")
    client = BinanceSignedClient(config.environment, load_credentials(config.environment))
    client.sync_time()
    rules = SymbolRules.from_exchange_info(client.exchange_info(config.symbol), config.symbol)
    price = rules.round_price(client.ticker_price(config.symbol) * Decimal("0.99"))
    quantity = rules.round_qty(config.order_budget / price)
    failures = rules.validate_limit(price, quantity)
    if failures:
        raise ValueError(f"test order violates current filters: {failures}")
    result = client.test_order({
        "symbol": config.symbol, "side": "BUY", "type": "LIMIT_MAKER",
        "quantity": str(quantity), "price": str(price),
    }, compute_commission=True)
    _print({"accepted_by_order_test": True, "environment": config.environment, "response": result})
    return 0


def command_run_once(args: argparse.Namespace) -> int:
    result = run_cycle(load_config(args.config), execute=args.execute, news_veto=args.news_veto)
    _print(result)
    return 0 if not str(result.get("action", "")).startswith("REJECT") else 2


def command_resolve_unknown(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    if config.environment == "simulation":
        raise ValueError("unknown-order resolution requires testnet or live")
    phrase = f"MARK NOT FOUND {args.client_order_id}"
    confirmation = input(
        "This will query Binance and, only if it reports no such order, release the local lock.\n"
        f"Type exactly `{phrase}`: "
    )
    client = BinanceSignedClient(config.environment, load_credentials(config.environment))
    client.sync_time()
    with StateStore(config.database_path) as state:
        engine = ExecutionEngine(client, state, HashChainJournal(config.journal_path))
        result = engine.resolve_unknown(
            args.client_order_id,
            config.symbol,
            confirm_not_found=confirmation == phrase,
        )
    _print(result)
    return 0


def command_daemon(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    if not args.execute:
        raise ValueError("daemon requires --execute; use run-once for dry runs")
    interval_seconds = config.cycle_minutes * 60
    while True:
        try:
            _print(run_cycle(config, execute=True, news_veto=False))
        except Exception as exc:
            _print({"action": "CYCLE_FAILED_NO_TRADE", "error": type(exc).__name__, "message": str(exc)})
        remaining = interval_seconds
        while remaining > 0:
            delay = min(60, remaining)
            time.sleep(delay)
            remaining -= delay


def command_arm_live(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    if config.environment != "live":
        raise ValueError("only a live config can be armed")
    policy_path = Path(__file__).resolve().parents[2] / "policies" / "constitution.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    if policy.get("live_trading_enabled") is not True:
        raise RuntimeError("live_trading_enabled is false; complete Testnet and human review first")
    confirmation = input(f"Type exactly `{CONFIRMATION}` to arm live trading for 7 days: ")
    if confirmation != CONFIRMATION:
        raise ValueError("confirmation did not match; live trading remains locked")
    activation = create_activation(config.activation_path, config.stage, config.maximum_account_value)
    _print({"armed": True, "activation": activation, "secret_written": False})
    return 0


def command_kill(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    if args.operation == "status":
        path = config.database_path.parent / "KILL_SWITCH"
        _print({"active": path.exists(), "path": path})
    else:
        _print({"result": set_kill_switch(config, args.operation == "on")})
    return 0


def command_status(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    with StateStore(config.database_path) as state:
        summary = state.summary()
    _print({
        "config": asdict(config),
        "credentials": credential_status(config.environment) if config.environment in {"testnet", "live"}
        else {"configured": False, "required": False},
        "state": summary, "journal": HashChainJournal(config.journal_path).verify(),
        "kill_switch": (config.database_path.parent / "KILL_SWITCH").exists(),
    })
    return 0


def command_report(args: argparse.Namespace) -> int:
    path = write_status_report(load_config(args.config).database_path, args.output)
    _print({"report": path.resolve()})
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Constitution-governed BTC/USDT Spot Harness")
    sub = parser.add_subparsers(dest="command", required=True)
    market = sub.add_parser("market", help="read public BTCUSDT price and rules")
    market.set_defaults(func=command_market)
    plan = sub.add_parser("plan-grid", help="build a six-order plan without placing it")
    plan.add_argument("--daily-volatility", default="0.03")
    plan.add_argument("--maker-fee", default="0.001", help="simulation assumption")
    plan.add_argument("--slippage", default="0.0002")
    plan.set_defaults(func=command_plan)
    demo = sub.add_parser("demo", help="place and fill orders only in the local simulator")
    demo.add_argument("--price", default="76000")
    demo.add_argument("--daily-volatility", default="0.03")
    demo.add_argument("--maker-fee", default="0.001")
    demo.add_argument("--journal", default="state/demo-journal.jsonl")
    demo.set_defaults(func=command_demo)
    verify = sub.add_parser("verify-journal", help="verify the append-only hash chain")
    verify.add_argument("path")
    verify.set_defaults(func=command_verify)
    credentials = sub.add_parser("credentials", help="manage local OS-protected API credentials")
    credentials.add_argument("operation", choices=("set", "status", "delete"))
    credentials.add_argument("environment", choices=("testnet", "live"))
    credentials.set_defaults(func=command_credentials)
    config_check = sub.add_parser("config-check", help="validate a TOML configuration")
    config_check.add_argument("--config", required=True)
    config_check.set_defaults(func=command_config_check)
    preflight = sub.add_parser("preflight", help="authenticate and verify account safety without trading")
    preflight.add_argument("--config", required=True)
    preflight.set_defaults(func=command_preflight)
    order_test = sub.add_parser("order-test", help="call POST /api/v3/order/test; no order is placed")
    order_test.add_argument("--config", required=True)
    order_test.set_defaults(func=command_order_test)
    run_once = sub.add_parser("run-once", help="reconcile, decide, and optionally execute one cycle")
    run_once.add_argument("--config", required=True)
    run_once.add_argument("--execute", action="store_true")
    run_once.add_argument("--news-veto", action="store_true")
    run_once.set_defaults(func=command_run_once)
    resolve = sub.add_parser(
        "resolve-unknown", help="manually reconcile one ambiguous submission; never resubmits"
    )
    resolve.add_argument("client_order_id")
    resolve.add_argument("--config", required=True)
    resolve.set_defaults(func=command_resolve_unknown)
    daemon = sub.add_parser("daemon", help="run low-frequency cycles")
    daemon.add_argument("--config", required=True)
    daemon.add_argument("--execute", action="store_true")
    daemon.set_defaults(func=command_daemon)
    arm = sub.add_parser("arm-live", help="create a machine-bound seven-day live activation")
    arm.add_argument("--config", required=True)
    arm.set_defaults(func=command_arm_live)
    kill = sub.add_parser("kill-switch", help="activate, clear, or inspect the kill switch")
    kill.add_argument("operation", choices=("on", "off", "status"))
    kill.add_argument("--config", required=True)
    kill.set_defaults(func=command_kill)
    status = sub.add_parser("status", help="show config, credentials, journal, and state")
    status.add_argument("--config", required=True)
    status.set_defaults(func=command_status)
    report = sub.add_parser("report", help="write a Markdown state report")
    report.add_argument("--config", required=True)
    report.add_argument("--output", default="state/status-report.md")
    report.set_defaults(func=command_report)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)
