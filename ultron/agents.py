"""Agent registry: responsibilities, I/O, triggers, permissions, failure handling, evidence."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Agent:
    name: str
    responsibilities: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    triggers: tuple[str, ...]
    permissions: tuple[str, ...]
    failure_handling: str
    evidence: str
    completion: str


_ESC = "Record FAILED in the event log; ULTRON escalates to the owner after retries are exhausted."

AGENTS: dict[str, Agent] = {
    a.name: a
    for a in (
        Agent("NOVA", "Research: products, business and technical opportunities.",
              ("source URLs", "market data"), ("opportunity records",),
              ("DAILY_RESEARCH", "NEW_OPPORTUNITY", "WEEKLY_R_AND_D_REVIEW"),
              ("read:web", "write:opportunities"), _ESC,
              "Every opportunity has a source URL and research date; unknowns stay unknown.",
              "Opportunity is VALIDATED or REJECTED with recorded reasons."),
        Agent("ULTRON", "Central orchestration; routes events, prevents duplicate work.",
              ("events",), ("agent assignments", "status changes"),
              ("SYSTEM_START", "SYSTEM_FAILURE"), ("read:all", "write:events"), _ESC,
              "Event log entry per routing decision.", "Event reaches a terminal status."),
        Agent("PROJECT_MANAGER", "Priorities, dependencies, task tracking.",
              ("task register", "events"), ("ordered queue",),
              ("OPPORTUNITY_VALIDATED", "WEEKLY_R_AND_D_REVIEW"),
              ("write:issues",), _ESC, "Issue/PR links per task.", "Queue reflects actual state."),
        Agent("FORGE", "Software, APIs, integrations, tests, deployments.",
              ("task issues",), ("PRs", "tests"),
              ("DEPLOYMENT_REQUEST", "DEPLOYMENT_FAILED"),
              ("write:branches", "open:pull_requests"), _ESC,
              "CI run IDs and test output.", "PR merged with passing CI."),
        Agent("SALES", "Listings, customer acquisition, conversion.",
              ("approved products",), ("published listings",),
              ("PRODUCT_APPROVED", "PRODUCT_LISTING_READY"),
              ("write:listings (approval required)",), _ESC,
              "Listing URL and channel confirmation.", "Listing live; sales counted only when paid."),
        Agent("PIXEL", "Websites, product presentation, creative assets.",
              ("product data",), ("pages", "images", "copy"),
              ("PRODUCT_APPROVED", "CONTENT_READY"), ("write:assets",), _ESC,
              "Published URL.", "Asset reachable and reviewed."),
        Agent("SEO_BACKLINK", "Search visibility and legitimate backlinks only.",
              ("keywords", "site pages"), ("content plans", "outreach drafts"),
              ("SEO_RESEARCH", "BACKLINK_OPPORTUNITY"),
              ("read:web", "send:outreach (approval required)"), _ESC,
              "Link counted only after the live page is fetched and the link found.",
              "Link verified live."),
        Agent("OPS", "Order processing, fulfilment, supplier orders, tracking.",
              ("paid orders",), ("supplier orders", "tracking"),
              ("NEW_ORDER", "PAYMENT_CONFIRMED", "SUPPLIER_CONFIRMED", "ORDER_DISPATCHED",
               "TRACKING_UPDATED", "ORDER_DELIVERED", "ORDER_EXCEPTION", "STOCK_CHANGE"),
              ("write:orders", "place:supplier_orders (approval required)"), _ESC,
              "Supplier confirmation and tracking reference per order.",
              "Order CLOSED after delivery verified."),
        Agent("FINANCE", "Revenue, costs, margins, reconciliation.",
              ("payments", "supplier costs", "fees", "refunds"), ("ledger", "reports"),
              ("DAILY_PERFORMANCE",), ("read:payments",), _ESC,
              "Each ledger row traces to a provider reference.",
              "Orders, payments and costs reconcile."),
        Agent("GUARDIAN", "Security, permissions, approvals, risk controls.",
              ("diffs", "configs", "events"), ("findings", "approvals"),
              ("SYSTEM_FAILURE", "DEPLOYMENT_REQUEST"), ("read:all",), _ESC,
              "Scan results and approval records.", "No unresolved high-risk findings."),
    )
}
