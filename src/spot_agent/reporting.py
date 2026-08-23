from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .state import StateStore


def write_status_report(database_path: str | Path, output_path: str | Path) -> Path:
    with StateStore(database_path) as state:
        summary = state.summary()
        recent_cycles = state.connection.execute(
            "SELECT created_at, environment, regime, confidence, action FROM cycles ORDER BY cycle_id DESC LIMIT 20"
        ).fetchall()
        recent_fills = state.connection.execute(
            "SELECT trade_time, price, qty, quote_qty, commission, commission_asset, is_buyer, is_maker FROM fills ORDER BY trade_time DESC LIMIT 20"
        ).fetchall()
    lines = [
        "# Autonomous Spot Agent Status",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Summary",
        "",
        f"- Orders: {summary['orders']}",
        f"- Open orders: {summary['open_orders']}",
        f"- Fills: {summary['fills']}",
        f"- Cycles: {summary['cycles']}",
        "",
        "## Recent cycles",
        "",
        "| Time | Environment | Regime | Confidence | Action |",
        "|---|---|---|---:|---|",
    ]
    lines.extend(
        f"| {row['created_at']} | {row['environment']} | {row['regime']} | {row['confidence']} | {row['action']} |"
        for row in recent_cycles
    )
    lines.extend(
        [
            "",
            "## Recent fills",
            "",
            "| Time | Side | Price | Qty | Quote | Fee | Maker |",
            "|---|---|---:|---:|---:|---:|---|",
        ]
    )
    lines.extend(
        f"| {row['trade_time']} | {'BUY' if row['is_buyer'] else 'SELL'} | {row['price']} | {row['qty']} | {row['quote_qty']} | {row['commission']} {row['commission_asset']} | {bool(row['is_maker'])} |"
        for row in recent_fills
    )
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target

