from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from .regime import MarketFeatures, RegimeDecision, detect_regime

D = Decimal


@dataclass(frozen=True)
class AnalyzedMarket:
    features: MarketFeatures
    decision: RegimeDecision
    closed_candles: int
    latest_close_time: datetime


def analyze_daily_klines(klines: list, now: datetime | None = None) -> AnalyzedMarket:
    now = now or datetime.now(timezone.utc)
    closed = [row for row in klines if int(row[6]) <= int(now.timestamp() * 1000)]
    if len(closed) < 30:
        invalid = MarketFeatures(
            price=D("0"), short_ma=D("0"), medium_ma=D("0"), short_ma_slope=D("0"),
            volume_ratio=D("0"), daily_volatility=D("0"), previous_range_low=D("0"),
            previous_range_high=D("0"), data_valid=False,
        )
        return AnalyzedMarket(invalid, detect_regime(invalid, now), len(closed), now)
    closes = [D(str(row[4])) for row in closed]
    highs = [D(str(row[2])) for row in closed]
    lows = [D(str(row[3])) for row in closed]
    volumes = [D(str(row[5])) for row in closed]
    short_ma = sum(closes[-7:], D("0")) / D("7")
    previous_short_ma = sum(closes[-8:-1], D("0")) / D("7")
    medium_ma = sum(closes[-21:], D("0")) / D("21")
    returns = [math.log(float(closes[i] / closes[i - 1])) for i in range(len(closes) - 14, len(closes))]
    volatility = D(str(statistics.pstdev(returns)))
    average_volume = sum(volumes[-21:-1], D("0")) / D("20")
    volume_ratio = volumes[-1] / average_volume if average_volume > 0 else D("0")
    features = MarketFeatures(
        price=closes[-1],
        short_ma=short_ma,
        medium_ma=medium_ma,
        short_ma_slope=short_ma - previous_short_ma,
        volume_ratio=volume_ratio,
        daily_volatility=volatility,
        previous_range_low=min(lows[-21:-1]),
        previous_range_high=max(highs[-21:-1]),
        data_valid=True,
    )
    latest_close = datetime.fromtimestamp(int(closed[-1][6]) / 1000, tz=timezone.utc)
    return AnalyzedMarket(features, detect_regime(features, now), len(closed), latest_close)

