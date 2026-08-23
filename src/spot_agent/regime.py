from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from .models import Regime

D = Decimal


@dataclass(frozen=True)
class MarketFeatures:
    price: Decimal
    short_ma: Decimal
    medium_ma: Decimal
    short_ma_slope: Decimal
    volume_ratio: Decimal
    daily_volatility: Decimal
    previous_range_low: Decimal
    previous_range_high: Decimal
    risk_event: bool = False
    data_valid: bool = True


@dataclass(frozen=True)
class RegimeDecision:
    regime: Regime
    evidence_for: tuple[str, ...]
    evidence_against: tuple[str, ...]
    confidence: Decimal
    reevaluate_at: datetime


def detect_regime(features: MarketFeatures, now: datetime | None = None) -> RegimeDecision:
    now = now or datetime.now(timezone.utc)
    next_check = now + timedelta(hours=4)
    if not features.data_valid or min(
        features.price,
        features.short_ma,
        features.medium_ma,
        features.previous_range_low,
        features.previous_range_high,
    ) <= 0:
        return RegimeDecision(Regime.UNCERTAIN, ("invalid or missing data",), (), D("0.95"), now + timedelta(minutes=15))
    if features.risk_event:
        return RegimeDecision(Regime.PANIC, ("high-severity risk veto",), (), D("0.90"), now + timedelta(minutes=15))

    above_breakout = features.price > features.previous_range_high * D("1.002")
    below_breakout = features.price < features.previous_range_low * D("0.998")
    if (above_breakout or below_breakout) and features.volume_ratio >= D("1.5"):
        direction = "above" if above_breakout else "below"
        return RegimeDecision(
            Regime.BREAKOUT,
            (f"price broke {direction} previous range", "volume ratio >= 1.5"),
            ("breakout still requires follow-through",),
            D("0.78"),
            now + timedelta(hours=1),
        )

    separation = features.short_ma / features.medium_ma - D("1")
    if separation >= D("0.005") and features.short_ma_slope > 0 and features.price >= features.short_ma:
        return RegimeDecision(
            Regime.UPTREND,
            ("short MA > medium MA by >= 0.5%", "short MA slope positive", "price above short MA"),
            ("trend can still mean-revert",),
            D("0.75"),
            next_check,
        )
    if separation <= D("-0.005") and features.short_ma_slope < 0 and features.price <= features.short_ma:
        return RegimeDecision(
            Regime.DOWNTREND,
            ("short MA < medium MA by >= 0.5%", "short MA slope negative", "price below short MA"),
            ("trend can reverse",),
            D("0.75"),
            next_check,
        )
    inside = features.previous_range_low <= features.price <= features.previous_range_high
    if abs(separation) < D("0.005") and inside and D("0.006") <= features.daily_volatility <= D("0.05"):
        return RegimeDecision(
            Regime.RANGE,
            ("short and medium MA are close", "price remains inside previous range", "volatility can cover costs"),
            ("range may break",),
            D("0.72"),
            next_check,
        )
    return RegimeDecision(
        Regime.UNCERTAIN,
        ("signals do not meet one deterministic regime",),
        ("conflicting trend/range evidence",),
        D("0.60"),
        now + timedelta(hours=1),
    )

