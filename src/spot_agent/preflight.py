from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .binance_signed import BinanceAPIError, BinanceSignedClient


@dataclass(frozen=True)
class PreflightResult:
    accepted: bool
    checks: tuple[str, ...]
    failures: tuple[str, ...]
    maker_fee: Decimal | None
    taker_fee: Decimal | None
    balances: dict[str, Decimal]
    free_balances: dict[str, Decimal]
    locked_balances: dict[str, Decimal]


def _balances(account: dict[str, Any]) -> dict[str, Decimal]:
    return {
        item["asset"]: Decimal(item["free"]) + Decimal(item["locked"])
        for item in account.get("balances", [])
        if Decimal(item["free"]) != 0 or Decimal(item["locked"]) != 0
    }


def _balance_part(account: dict[str, Any], key: str) -> dict[str, Decimal]:
    return {
        item["asset"]: Decimal(item[key])
        for item in account.get("balances", [])
        if Decimal(item[key]) != 0
    }


def run_preflight(client: BinanceSignedClient, symbol: str = "BTCUSDT") -> PreflightResult:
    checks: list[str] = []
    failures: list[str] = []
    offset = client.sync_time()
    checks.append(f"SERVER_TIME_OFFSET_MS={offset}")
    if abs(offset) > 4000:
        failures.append("LOCAL_CLOCK_TOO_FAR_FROM_BINANCE")
    account = client.account()
    if not account.get("canTrade", False):
        failures.append("ACCOUNT_CANNOT_TRADE")
    else:
        checks.append("ACCOUNT_CAN_TRADE")
    if account.get("accountType") not in {None, "SPOT"}:
        failures.append("ACCOUNT_TYPE_NOT_SPOT")
    else:
        checks.append("ACCOUNT_TYPE_SPOT")

    if client.environment == "live":
        permissions = client.api_restrictions()
        required_true = ("ipRestrict", "enableReading", "enableSpotAndMarginTrading")
        required_false = (
            "enableWithdrawals",
            "enableMargin",
            "enableFutures",
            "enableVanillaOptions",
            "enablePortfolioMarginTrading",
            "enableInternalTransfer",
            "permitsUniversalTransfer",
        )
        for name in required_true:
            if permissions.get(name) is not True:
                failures.append(f"PERMISSION_REQUIRED_{name}")
            else:
                checks.append(f"PERMISSION_OK_{name}")
        for name in required_false:
            if permissions.get(name) is not False:
                failures.append(f"DANGEROUS_PERMISSION_{name}")
            else:
                checks.append(f"PERMISSION_DISABLED_{name}")

    try:
        commission = client.commission(symbol)
    except BinanceAPIError:
        commission = account.get("commissionRates", {})
    standard = commission.get("standardCommission", commission)
    try:
        components = (
            commission.get("standardCommission", standard),
            commission.get("specialCommission", {}),
            commission.get("taxCommission", {}),
        )
        maker_buy = sum(
            (Decimal(part.get("maker", "0")) + Decimal(part.get("buyer", "0")) for part in components),
            Decimal("0"),
        )
        maker_sell = sum(
            (Decimal(part.get("maker", "0")) + Decimal(part.get("seller", "0")) for part in components),
            Decimal("0"),
        )
        taker_buy = sum(
            (Decimal(part.get("taker", "0")) + Decimal(part.get("buyer", "0")) for part in components),
            Decimal("0"),
        )
        taker_sell = sum(
            (Decimal(part.get("taker", "0")) + Decimal(part.get("seller", "0")) for part in components),
            Decimal("0"),
        )
        maker = max(maker_buy, maker_sell)
        taker = max(taker_buy, taker_sell)
    except (KeyError, TypeError, ValueError):
        maker = taker = None
        failures.append("COMMISSION_UNAVAILABLE")
    if maker is not None and (not maker.is_finite() or maker < 0):
        failures.append("INVALID_MAKER_FEE")
    if taker is not None and (not taker.is_finite() or taker < 0):
        failures.append("INVALID_TAKER_FEE")
    if maker is not None and taker is not None:
        checks.append(f"COMMISSION_MAKER={maker}_TAKER={taker}")
    return PreflightResult(
        accepted=not failures,
        checks=tuple(checks),
        failures=tuple(failures),
        maker_fee=maker,
        taker_fee=taker,
        balances=_balances(account),
        free_balances=_balance_part(account, "free"),
        locked_balances=_balance_part(account, "locked"),
    )
