from __future__ import annotations

import hashlib
import json
import os
import threading
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterator

GENESIS = "0" * 64


def _json_default(value: Any) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if hasattr(value, "value"):
        return str(value.value)
    raise TypeError(f"unsupported journal value: {type(value)!r}")


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=_json_default,
        allow_nan=False,
    ).encode("utf-8")


class HashChainJournal:
    """Append-only by API contract; external edits are detected by verify()."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()

    def records(self) -> Iterator[dict[str, Any]]:
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if line.strip():
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise ValueError(f"invalid JSON at line {line_number}") from exc

    def verify(self) -> tuple[bool, str]:
        previous = GENESIS
        expected_seq = 1
        try:
            for record in self.records():
                supplied_hash = record.get("hash")
                unsigned = {k: v for k, v in record.items() if k != "hash"}
                expected_hash = hashlib.sha256(_canonical(unsigned)).hexdigest()
                if record.get("seq") != expected_seq:
                    return False, f"sequence mismatch at {expected_seq}"
                if record.get("prev_hash") != previous:
                    return False, f"previous hash mismatch at {expected_seq}"
                if supplied_hash != expected_hash:
                    return False, f"content hash mismatch at {expected_seq}"
                previous = supplied_hash
                expected_seq += 1
        except ValueError as exc:
            return False, str(exc)
        return True, f"verified {expected_seq - 1} records"

    def append(self, event: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            ok, message = self.verify()
            if not ok:
                raise ValueError(f"refusing to append to invalid journal: {message}")
            existing = list(self.records())
            seq = len(existing) + 1
            previous = existing[-1]["hash"] if existing else GENESIS
            unsigned = {
                "seq": seq,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": event,
                "payload": payload,
                "prev_hash": previous,
            }
            record = {**unsigned, "hash": hashlib.sha256(_canonical(unsigned)).hexdigest()}
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(
                    json.dumps(record, ensure_ascii=False, default=_json_default, allow_nan=False) + "\n"
                )
                handle.flush()
                os.fsync(handle.fileno())
            return record
