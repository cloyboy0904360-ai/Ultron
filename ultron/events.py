"""Central trigger registry and audited event log.

Events are logged with `verified_source`. Only events from a real provider call or a
verified signature may set it True; simulated events are stored but flagged and never
counted as genuine.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime

from ultron.agents import AGENTS


@dataclass(frozen=True)
class EventSpec:
    name: str
    source: str
    required_data: tuple[str, ...]
    conditions: str
    agent: str
    action: str
    success: str
    retry: str = "3 attempts, exponential backoff (1m, 5m, 25m)"
    escalation: str = "Dead-letter, mark status FAILED, notify owner"


def _e(name, source, data, cond, agent, action, success, **kw) -> EventSpec:
    return EventSpec(name, source, tuple(data), cond, agent, action, success, **kw)


_SCHED = "scheduler (GitHub Actions cron or Make)"
_NONE = "No automatic retry; surfaced for human decision"

EVENTS: dict[str, EventSpec] = {
    e.name: e
    for e in (
        _e("SYSTEM_START", "process start", ["version", "env"], "config valid", "ULTRON",
           "Load registries, run health check", "Health check recorded"),
        _e("DAILY_RESEARCH", _SCHED, ["date"], "once per day", "NOVA",
           "Research opportunities and record sources", "Records have source URL and date"),
        _e("NEW_OPPORTUNITY", "NOVA", ["opportunity_id", "source_url"], "source URL present",
           "NOVA", "Calculate demand, cost and margin", "Opportunity marked VALIDATED/REJECTED"),
        _e("OPPORTUNITY_VALIDATED", "NOVA", ["opportunity_id", "gross_margin"],
           "supplier and margin verified", "PROJECT_MANAGER", "Queue for owner approval",
           "Approval requested"),
        _e("PRODUCT_APPROVED", "owner approval", ["product_id", "approver"],
           "approval recorded", "PIXEL", "Prepare listing drafts", "Drafts ready for review"),
        _e("PRODUCT_LISTING_READY", "PIXEL", ["product_id", "channel"],
           "all 10 product gates passed", "SALES", "Publish (needs approval)",
           "Listing URL captured"),
        _e("STOCK_CHANGE", "supplier API or scheduled check", ["product_id", "stock"],
           "stock differs from published", "OPS", "Sync availability", "Channel matches supplier"),
        _e("NEW_ORDER", "channel webhook (signature verified)", ["order_ref", "items", "amount"],
           "signature valid; order_ref unseen", "OPS", "Create order (idempotent)",
           "Order recorded once"),
        _e("PAYMENT_CONFIRMED", "payment provider API lookup", ["order_ref", "payment_ref"],
           "provider reports succeeded with matching amount/currency", "FINANCE",
           "Verify with provider, then release for fulfilment", "Order PAYMENT_VERIFIED",
           retry="3 attempts for provider errors; declines are not retried",
           escalation="PAYMENT_FAILED state, no fulfilment"),
        _e("SUPPLIER_CONFIRMED", "supplier API", ["order_ref", "supplier_ref"],
           "order profitable; approval for supplier spend", "OPS", "Record supplier order",
           "Supplier reference stored"),
        _e("ORDER_DISPATCHED", "supplier API", ["order_ref", "dispatched_at"],
           "supplier confirmed", "OPS", "Record dispatch", "Status DISPATCHED"),
        _e("TRACKING_UPDATED", "carrier API", ["order_ref", "tracking_id", "status"],
           "tracking id valid", "OPS", "Store tracking and push to channel", "Tracking verified"),
        _e("ORDER_DELIVERED", "carrier API", ["order_ref", "delivered_at"],
           "carrier reports delivered", "OPS", "Close order", "Status CLOSED"),
        _e("ORDER_EXCEPTION", "any fulfilment agent", ["order_ref", "state"],
           "state is an exception state", "OPS", "Open exception case", "Case resolved",
           retry=_NONE),
        _e("SEO_RESEARCH", _SCHED, ["site"], "weekly", "SEO_BACKLINK",
           "Keyword and content-gap research", "Keyword map updated"),
        _e("BACKLINK_OPPORTUNITY", "SEO_BACKLINK", ["prospect_url", "relevance"],
           "relevance reasoned; not paid or spam", "SEO_BACKLINK", "Draft outreach for approval",
           "Draft awaiting approval", retry=_NONE),
        _e("CONTENT_READY", "PIXEL", ["content_id", "url"], "reviewed", "SEO_BACKLINK",
           "Plan internal links", "Links planned"),
        _e("DEPLOYMENT_REQUEST", "workflow_dispatch", ["environment", "ref"],
           "CI green; production needs approval", "FORGE", "Run controlled deploy",
           "Post-deploy check passes"),
        _e("DEPLOYMENT_FAILED", "deploy workflow", ["run_id", "error"], "deploy failed",
           "FORGE", "Roll back and diagnose", "Previous version healthy", retry=_NONE),
        _e("DAILY_PERFORMANCE", _SCHED, ["date"], "daily", "FINANCE",
           "Reconcile and report actuals (never forecasts)", "Report generated"),
        _e("SYSTEM_FAILURE", "any component", ["component", "error"], "unhandled error",
           "GUARDIAN", "Contain and investigate", "Incident closed", retry=_NONE),
        _e("WEEKLY_R_AND_D_REVIEW", _SCHED, ["week"], "weekly", "PROJECT_MANAGER",
           "Review research and reprioritise", "Next task selected on evidence"),
    )
}


def _utc_now() -> str:
    return datetime.now(tz=UTC).isoformat()


def log_event(
    db_path: str,
    event: str,
    *,
    source: str,
    verified_source: bool,
    payload: dict,
    status: str = "READY",
) -> int:
    spec = EVENTS.get(event)
    if spec is None:
        raise ValueError(f"unknown event: {event}")
    missing = [k for k in spec.required_data if k not in payload]
    if missing:
        raise ValueError(f"{event} missing required data: {', '.join(missing)}")
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO events(event, source, verified_source, payload, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (event, source, int(verified_source), json.dumps(payload), status, _utc_now()),
        )
        return int(cur.lastrowid)


def validate_registry() -> list[str]:
    problems = []
    for spec in EVENTS.values():
        if spec.agent not in AGENTS:
            problems.append(f"{spec.name}: unknown agent {spec.agent}")
    for agent in AGENTS.values():
        for trig in agent.triggers:
            if trig not in EVENTS:
                problems.append(f"{agent.name}: unknown trigger {trig}")
    return problems
