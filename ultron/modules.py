"""Subordinate reporters. They do not schedule work or start their own cycle."""
from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass

from ultron.assets import counts as registry_counts
from ultron.assets import ensure_registry


@dataclass(frozen=True)
class ModuleReport:
    name: str
    agent: str
    status: str
    summary: str
    evidence: dict


def _count(conn: sqlite3.Connection, sql: str) -> int:
    try:
        row = conn.execute(sql).fetchone()
    except sqlite3.OperationalError:
        return 0
    return int(row[0] or 0)


def collect_reports(db_path: str) -> tuple[ModuleReport, ...]:
    ensure_registry(db_path)
    registry = registry_counts(db_path)
    with sqlite3.connect(db_path) as conn:
        closed = _count(conn, "SELECT COUNT(*) FROM fulfilment WHERE state = 'CLOSED'")
        received = _count(conn, "SELECT COUNT(*) FROM orders")
        verified_events = _count(conn, "SELECT COUNT(*) FROM events WHERE verified_source = 1")
        unverified_events = _count(conn, "SELECT COUNT(*) FROM events WHERE verified_source = 0")
    stripe_configured = bool(os.environ.get("STRIPE_API_KEY"))
    payment_status = "READY" if stripe_configured else "AWAITING APPROVAL"
    return (
        ModuleReport(
            "payments",
            "FINANCE",
            payment_status,
            "Stripe key present" if stripe_configured else "No Stripe key; no payment is verified",
            {"stripe_configured": stripe_configured},
        ),
        ModuleReport(
            "fulfilment",
            "OPS",
            "VERIFIED" if closed else "READY",
            f"orders={received} closed={closed}",
            {"orders": received, "closed": closed},
        ),
        ModuleReport(
            "events",
            "ULTRON",
            "READY",
            f"verified_events={verified_events} unverified_events={unverified_events}",
            {"verified_events": verified_events, "unverified_events": unverified_events},
        ),
        ModuleReport(
            "assets",
            "ASSET_MANAGER",
            "READY",
            f"assets={registry['assets']} verified={registry['verified_assets']}",
            registry,
        ),
        ModuleReport(
            "opportunities",
            "R_AND_D",
            "READY" if registry["opportunities"] else "AWAITING APPROVAL",
            f"sourced_opportunities={registry['opportunities']}",
            {"opportunities": registry["opportunities"]},
        ),
    )
