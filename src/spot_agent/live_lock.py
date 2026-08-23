from __future__ import annotations

import hashlib
import json
import platform
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

CONFIRMATION = "I ACCEPT BTC SPOT LOSS RISK"


def _digest(payload: dict) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def create_activation(path: str | Path, stage: int, capital_cap: Decimal, hours: int = 168) -> dict:
    if stage not in {1, 2} or capital_cap <= 0 or capital_cap > Decimal("100"):
        raise ValueError("activation only permits Stage 1/2 and at most 100 USDT")
    now = datetime.now(timezone.utc)
    unsigned = {
        "version": 1,
        "activation_id": str(uuid.uuid4()),
        "stage": stage,
        "capital_cap_usdt": str(capital_cap),
        "machine": platform.node(),
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(hours=hours)).isoformat(),
    }
    activation = {**unsigned, "checksum": _digest(unsigned)}
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(activation, indent=2), encoding="utf-8")
    return activation


def verify_activation(path: str | Path, stage: int, capital_cap: Decimal) -> tuple[bool, str]:
    target = Path(path)
    if not target.exists():
        return False, "LIVE_ACTIVATION_MISSING"
    try:
        activation = json.loads(target.read_text(encoding="utf-8"))
        checksum = activation.pop("checksum")
        expires = datetime.fromisoformat(activation["expires_at"])
    except (json.JSONDecodeError, KeyError, ValueError):
        return False, "LIVE_ACTIVATION_INVALID"
    if checksum != _digest(activation):
        return False, "LIVE_ACTIVATION_TAMPERED"
    if activation.get("machine") != platform.node():
        return False, "LIVE_ACTIVATION_WRONG_MACHINE"
    if activation.get("stage") != stage:
        return False, "LIVE_ACTIVATION_STAGE_MISMATCH"
    if Decimal(activation.get("capital_cap_usdt", "NaN")) != capital_cap:
        return False, "LIVE_ACTIVATION_CAP_MISMATCH"
    if datetime.now(timezone.utc) >= expires:
        return False, "LIVE_ACTIVATION_EXPIRED"
    return True, f"LIVE_ACTIVATION_VALID_UNTIL_{expires.isoformat()}"

