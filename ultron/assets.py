"""Asset and opportunity registries. Evidence in, no invented demand or revenue."""
from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

STATUSES = frozenset(
    {"READY", "RUNNING", "VERIFIED", "BLOCKED", "AWAITING APPROVAL", "FAILED", "PAUSED"}
)


class RegistryError(ValueError):
    pass


def _now() -> str:
    return datetime.now(tz=UTC).isoformat()


def ensure_registry(db_path: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS assets (
                asset_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                platform TEXT NOT NULL,
                access_evidence TEXT NOT NULL,
                url TEXT NOT NULL,
                status TEXT NOT NULL,
                cost_cents INTEGER,
                revenue_cents INTEGER NOT NULL DEFAULT 0,
                payment_ref TEXT,
                monetisation TEXT NOT NULL,
                dependencies TEXT,
                security_notes TEXT,
                next_action TEXT NOT NULL,
                verified_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                source_url TEXT NOT NULL,
                research_date TEXT NOT NULL,
                demand_evidence TEXT NOT NULL,
                who_pays TEXT,
                problem TEXT,
                startup_cost_cents INTEGER,
                monthly_cost_cents INTEGER,
                selling_price_cents INTEGER,
                gross_margin_bps INTEGER,
                risks TEXT NOT NULL,
                status TEXT NOT NULL,
                next_action TEXT NOT NULL
            );
            """
        )


def record_asset(
    db_path: str,
    *,
    asset_id: str,
    name: str,
    category: str,
    platform: str,
    access_evidence: str,
    url: str,
    status: str,
    next_action: str,
    cost_cents: int | None = None,
    revenue_cents: int = 0,
    payment_ref: str | None = None,
    monetisation: str = "unknown",
    dependencies: str | None = None,
    security_notes: str | None = None,
    verified_at: str | None = None,
) -> str:
    if not access_evidence.strip() or not url.strip():
        raise RegistryError("access evidence and a URL or repository reference are required")
    if status not in STATUSES:
        raise RegistryError(f"invalid status: {status}")
    if revenue_cents and not payment_ref:
        raise RegistryError("revenue requires a payment reference")
    if revenue_cents < 0 or (cost_cents is not None and cost_cents < 0):
        raise RegistryError("money fields cannot be negative")
    ensure_registry(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO assets(
                asset_id, name, category, platform, access_evidence, url, status,
                cost_cents, revenue_cents, payment_ref, monetisation, dependencies,
                security_notes, next_action, verified_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(asset_id) DO UPDATE SET
                access_evidence = excluded.access_evidence,
                status = excluded.status,
                revenue_cents = excluded.revenue_cents,
                payment_ref = excluded.payment_ref,
                next_action = excluded.next_action,
                verified_at = excluded.verified_at
            """,
            (
                asset_id,
                name,
                category,
                platform,
                access_evidence,
                url,
                status,
                cost_cents,
                revenue_cents,
                payment_ref,
                monetisation,
                dependencies,
                security_notes,
                next_action,
                verified_at or _now(),
            ),
        )
        conn.commit()
    return asset_id


def record_opportunity(
    db_path: str,
    *,
    name: str,
    source_url: str,
    demand_evidence: str,
    risks: str,
    next_action: str,
    status: str = "READY",
    who_pays: str | None = None,
    problem: str | None = None,
    startup_cost_cents: int | None = None,
    monthly_cost_cents: int | None = None,
    selling_price_cents: int | None = None,
    research_date: str | None = None,
) -> int:
    if not source_url.startswith("https://"):
        raise RegistryError("an idea without a source URL is not an opportunity")
    if not demand_evidence.strip():
        raise RegistryError("demand evidence is required; do not invent it")
    if status not in STATUSES:
        raise RegistryError(f"invalid status: {status}")
    costs = (startup_cost_cents, monthly_cost_cents, selling_price_cents)
    if status == "VERIFIED" and any(item is None for item in costs):
        raise RegistryError("VERIFIED requires recorded costs and a selling price")
    margin = None
    if None not in costs and selling_price_cents:
        margin = round(
            (selling_price_cents - startup_cost_cents - monthly_cost_cents)
            * 10000
            / selling_price_cents
        )
    ensure_registry(db_path)
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO opportunities(
                name, source_url, research_date, demand_evidence, who_pays, problem,
                startup_cost_cents, monthly_cost_cents, selling_price_cents,
                gross_margin_bps, risks, status, next_action
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                source_url,
                research_date or _now(),
                demand_evidence,
                who_pays,
                problem,
                startup_cost_cents,
                monthly_cost_cents,
                selling_price_cents,
                margin,
                risks,
                status,
                next_action,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)


def counts(db_path: str) -> dict[str, int]:
    ensure_registry(db_path)
    with sqlite3.connect(db_path) as conn:
        assets = conn.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
        opportunities = conn.execute("SELECT COUNT(*) FROM opportunities").fetchone()[0]
        verified = conn.execute(
            "SELECT COUNT(*) FROM assets WHERE status = 'VERIFIED'"
        ).fetchone()[0]
    return {
        "assets": int(assets),
        "verified_assets": int(verified),
        "opportunities": int(opportunities),
    }
