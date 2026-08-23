from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .rules import SymbolRules


class BinancePublicClient:
    """Public market-data client. Deliberately contains no order or secret-key methods."""

    BASE_URL = "https://data-api.binance.vision"

    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self.timeout_seconds = timeout_seconds

    def _get(self, path: str, params: dict[str, str]) -> dict | list:
        query = urlencode(params)
        request = Request(
            f"{self.BASE_URL}{path}?{query}",
            headers={"User-Agent": "autonomous-spot-agent-stage0/0.1"},
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))

    def exchange_info(self, symbol: str = "BTCUSDT") -> dict:
        result = self._get("/api/v3/exchangeInfo", {"symbol": symbol})
        if not isinstance(result, dict):
            raise ValueError("unexpected exchangeInfo payload")
        return result

    def symbol_rules(self, symbol: str = "BTCUSDT") -> SymbolRules:
        return SymbolRules.from_exchange_info(self.exchange_info(symbol), symbol)

    def ticker_price(self, symbol: str = "BTCUSDT") -> tuple[Decimal, datetime]:
        result = self._get("/api/v3/ticker/price", {"symbol": symbol})
        if not isinstance(result, dict) or "price" not in result:
            raise ValueError("unexpected ticker payload")
        return Decimal(result["price"]), datetime.now(timezone.utc)

    def klines(self, symbol: str = "BTCUSDT", interval: str = "1d", limit: int = 30) -> list:
        result = self._get(
            "/api/v3/klines",
            {"symbol": symbol, "interval": interval, "limit": str(limit)},
        )
        if not isinstance(result, list):
            raise ValueError("unexpected klines payload")
        return result

