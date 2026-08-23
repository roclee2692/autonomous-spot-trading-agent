from __future__ import annotations

import tomllib
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

D = Decimal
ENVIRONMENTS = {"simulation", "testnet", "live"}


@dataclass(frozen=True)
class AgentConfig:
    environment: str = "simulation"
    stage: int = 0
    symbol: str = "BTCUSDT"
    maximum_account_value: Decimal = D("100")
    quote_reserve: Decimal = D("20")
    core_btc_value: Decimal = D("20")
    order_budget: Decimal = D("10")
    max_open_orders: int = 6
    max_daily_turnover: Decimal = D("60")
    max_daily_loss: Decimal = D("5")
    max_data_age_seconds: int = 60
    maximum_fee_rate: Decimal = D("0.0015")
    levels_per_side: int = 3
    assumed_slippage: Decimal = D("0.0002")
    cycle_minutes: int = 240
    database_path: Path = Path("state/agent.sqlite3")
    journal_path: Path = Path("state/journal.jsonl")
    activation_path: Path = Path("state/live-activation.json")

    def validate(self) -> "AgentConfig":
        if self.environment not in ENVIRONMENTS:
            raise ValueError(f"environment must be one of {sorted(ENVIRONMENTS)}")
        if self.symbol != "BTCUSDT":
            raise ValueError("V1 only permits BTCUSDT")
        if self.stage not in {0, 1, 2}:
            raise ValueError("V1 stage must be 0, 1, or 2")
        if self.environment == "simulation" and self.stage != 0:
            raise ValueError("simulation environment requires stage 0")
        if self.environment == "live" and self.stage == 0:
            raise ValueError("live environment requires an explicitly selected stage")
        monetary = (
            self.maximum_account_value,
            self.quote_reserve,
            self.core_btc_value,
            self.order_budget,
            self.max_daily_turnover,
            self.max_daily_loss,
            self.maximum_fee_rate,
            self.assumed_slippage,
        )
        if any(not value.is_finite() or value < 0 for value in monetary):
            raise ValueError("numeric limits must be finite and non-negative")
        if self.maximum_account_value > D("100") and self.stage <= 2:
            raise ValueError("Stage 0-2 capital cap cannot exceed 100 USDT")
        if self.quote_reserve <= 0:
            raise ValueError("Reserve must remain positive")
        if self.stage == 2 and self.core_btc_value <= 0:
            raise ValueError("Stage 2 Core BTC must remain positive")
        if self.order_budget <= D("5"):
            raise ValueError("order budget must be safely above the known 5 USDT snapshot")
        if self.levels_per_side not in {1, 2, 3}:
            raise ValueError("V1 permits 1-3 levels per side")
        if self.stage == 1 and self.max_open_orders != 1:
            raise ValueError("Stage 1 must allow exactly one open order")
        if self.order_budget + self.quote_reserve > self.maximum_account_value:
            raise ValueError("one order plus Reserve exceeds the capital cap")
        if self.stage == 2 and self.max_open_orders > 6:
            raise ValueError("Stage 2 permits at most six open orders")
        if self.max_data_age_seconds <= 0 or self.cycle_minutes <= 0:
            raise ValueError("time intervals must be positive")
        return self


def _resolve(base: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()


def load_config(path: str | Path) -> AgentConfig:
    config_path = Path(path).resolve()
    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)
    agent = raw.get("agent", {})
    capital = raw.get("capital", {})
    risk = raw.get("risk", {})
    strategy = raw.get("strategy", {})
    storage = raw.get("storage", {})
    base = config_path.parent
    config = AgentConfig(
        environment=str(agent.get("environment", "simulation")),
        stage=int(agent.get("stage", 0)),
        symbol=str(agent.get("symbol", "BTCUSDT")),
        maximum_account_value=D(str(capital.get("maximum_account_value_usdt", "100"))),
        quote_reserve=D(str(capital.get("quote_reserve_usdt", "20"))),
        core_btc_value=D(str(capital.get("core_btc_value_usdt", "20"))),
        order_budget=D(str(capital.get("order_budget_usdt", "10"))),
        max_open_orders=int(risk.get("max_open_orders", 6)),
        max_daily_turnover=D(str(risk.get("max_daily_turnover_usdt", "60"))),
        max_daily_loss=D(str(risk.get("max_daily_loss_usdt", "5"))),
        max_data_age_seconds=int(risk.get("max_data_age_seconds", 60)),
        maximum_fee_rate=D(str(risk.get("maximum_fee_rate", "0.0015"))),
        levels_per_side=int(strategy.get("levels_per_side", 3)),
        assumed_slippage=D(str(strategy.get("assumed_slippage", "0.0002"))),
        cycle_minutes=int(strategy.get("cycle_minutes", 240)),
        database_path=_resolve(base, str(storage.get("database_path", "state/agent.sqlite3"))),
        journal_path=_resolve(base, str(storage.get("journal_path", "state/journal.jsonl"))),
        activation_path=_resolve(base, str(storage.get("activation_path", "state/live-activation.json"))),
    )
    return config.validate()
