from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .credentials import APICredentials

BASE_URLS = {
    "testnet": "https://testnet.binance.vision",
    "live": "https://api.binance.com",
}


class BinanceAPIError(RuntimeError):
    def __init__(self, status: int | None, code: int | None, message: str) -> None:
        super().__init__(f"Binance API error status={status} code={code}: {message}")
        self.status = status
        self.code = code
        self.message = message


class UnknownExecutionStatus(RuntimeError):
    """A mutating request timed out; the order may have reached Binance."""


@dataclass(frozen=True)
class HTTPResult:
    payload: dict[str, Any] | list[Any]
    headers: dict[str, str]


Transport = Callable[[str, str, dict[str, str], float], HTTPResult]


def _urllib_transport(method: str, url: str, headers: dict[str, str], timeout: float) -> HTTPResult:
    request = Request(url, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8") or "{}")
            return HTTPResult(payload, dict(response.headers.items()))
    except HTTPError as exc:
        try:
            body = json.loads(exc.read().decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            body = {"msg": str(exc)}
        raise BinanceAPIError(exc.code, body.get("code"), body.get("msg", str(exc))) from exc


class BinanceSignedClient:
    def __init__(
        self,
        environment: str,
        credentials: APICredentials,
        *,
        timeout_seconds: float = 10.0,
        transport: Transport = _urllib_transport,
    ) -> None:
        if environment not in BASE_URLS:
            raise ValueError("signed client environment must be testnet or live")
        self.environment = environment
        self.base_url = BASE_URLS[environment]
        self.credentials = credentials
        self.timeout_seconds = timeout_seconds
        self.transport = transport
        self.time_offset_ms = 0

    def _public(self, path: str, params: dict[str, Any] | None = None) -> HTTPResult:
        query = urlencode(params or {})
        url = f"{self.base_url}{path}" + (f"?{query}" if query else "")
        return self.transport("GET", url, {"User-Agent": "autonomous-spot-agent/1.0"}, self.timeout_seconds)

    def sync_time(self) -> int:
        before = int(time.time() * 1000)
        result = self._public("/api/v3/time")
        after = int(time.time() * 1000)
        server_time = int(result.payload["serverTime"])
        self.time_offset_ms = server_time - ((before + after) // 2)
        return self.time_offset_ms

    def _signed(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        mutating: bool = False,
    ) -> HTTPResult:
        values = dict(params or {})
        values.setdefault("recvWindow", 5000)
        values["timestamp"] = int(time.time() * 1000) + self.time_offset_ms
        query = urlencode(values)
        signature = hmac.new(
            self.credentials.api_secret.encode("utf-8"), query.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        url = f"{self.base_url}{path}?{query}&signature={signature}"
        headers = {
            "X-MBX-APIKEY": self.credentials.api_key,
            "User-Agent": "autonomous-spot-agent/1.0",
        }
        try:
            return self.transport(method, url, headers, self.timeout_seconds)
        except (URLError, TimeoutError, OSError) as exc:
            if mutating:
                raise UnknownExecutionStatus(
                    "request status is unknown; reconcile by client order id before any retry"
                ) from exc
            raise

    def account(self) -> dict[str, Any]:
        return dict(self._signed("GET", "/api/v3/account", {"omitZeroBalances": "false"}).payload)

    def exchange_info(self, symbol: str = "BTCUSDT") -> dict[str, Any]:
        return dict(self._public("/api/v3/exchangeInfo", {"symbol": symbol}).payload)

    def ticker_price(self, symbol: str = "BTCUSDT") -> Decimal:
        return Decimal(str(dict(self._public("/api/v3/ticker/price", {"symbol": symbol}).payload)["price"]))

    def klines(self, symbol: str = "BTCUSDT", interval: str = "1d", limit: int = 60) -> list:
        return list(
            self._public(
                "/api/v3/klines", {"symbol": symbol, "interval": interval, "limit": str(limit)}
            ).payload
        )

    def commission(self, symbol: str = "BTCUSDT") -> dict[str, Any]:
        return dict(self._signed("GET", "/api/v3/account/commission", {"symbol": symbol}).payload)

    def api_restrictions(self) -> dict[str, Any]:
        if self.environment != "live":
            raise ValueError("API restriction inspection is a live-only SAPI endpoint")
        return dict(self._signed("GET", "/sapi/v1/account/apiRestrictions").payload)

    def test_order(self, params: dict[str, Any], *, compute_commission: bool = True) -> dict[str, Any]:
        values = dict(params)
        values["computeCommissionRates"] = "true" if compute_commission else "false"
        return dict(self._signed("POST", "/api/v3/order/test", values, mutating=False).payload)

    def new_order(self, params: dict[str, Any]) -> dict[str, Any]:
        return dict(self._signed("POST", "/api/v3/order", params, mutating=True).payload)

    def cancel_order(self, symbol: str, client_order_id: str) -> dict[str, Any]:
        return dict(
            self._signed(
                "DELETE",
                "/api/v3/order",
                {"symbol": symbol, "origClientOrderId": client_order_id},
                mutating=True,
            ).payload
        )

    def get_order(self, symbol: str, client_order_id: str) -> dict[str, Any]:
        return dict(
            self._signed(
                "GET", "/api/v3/order", {"symbol": symbol, "origClientOrderId": client_order_id}
            ).payload
        )

    def open_orders(self, symbol: str) -> list[dict[str, Any]]:
        return list(self._signed("GET", "/api/v3/openOrders", {"symbol": symbol}).payload)

    def trades(self, symbol: str, limit: int = 1000) -> list[dict[str, Any]]:
        return list(self._signed("GET", "/api/v3/myTrades", {"symbol": symbol, "limit": limit}).payload)
