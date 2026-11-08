"""Safe, deterministic task handlers for the six ULTRON roles."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

AGENT_OPERATIONS: dict[str, frozenset[str]] = {
    "NOVA": frozenset({"break_down_objective"}),
    "FORGE": frozenset({"code_review_checklist"}),
    "SALES": frozenset({"draft_reply"}),
    "OPS": frozenset({"fulfilment_readiness"}),
    "FINANCE": frozenset({"calculate_margin"}),
    "PIXEL": frozenset({"draft_product_listing"}),
}

@dataclass(frozen=True)
class TaskResult:
    operation: str
    status: str
    output: dict[str, Any]

def _required_text(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value.strip()

def _text_list(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key, [])
    if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value):
        raise ValueError(f"{key} must be a list of non-empty strings")
    return [x.strip() for x in value]

def execute_task(agent: str, operation: str, data: dict[str, Any]) -> TaskResult:
    """Execute one allowlisted, side-effect-free operation for an agent."""
    agent = agent.upper()
    if agent not in AGENT_OPERATIONS:
        raise ValueError("unknown agent")
    if operation not in AGENT_OPERATIONS[agent]:
        raise PermissionError(f"{agent} is not permitted to execute {operation}")
    if not isinstance(data, dict):
        raise TypeError("task input must be a JSON object")

    if operation == "break_down_objective":
        objective = _required_text(data, "objective")
        constraints = _text_list(data, "constraints")
        output = {
            "objective": objective, "constraints": constraints,
            "steps": [
                "Confirm the requested outcome and acceptance evidence.",
                "Identify dependencies, access requirements and approval gates.",
                "Execute one bounded task at a time and record its evidence.",
                "Verify the outcome independently before marking it complete.",
            ],
            "approval_required_for": ["spending", "external messages", "publishing", "production changes"],
        }
    elif operation == "code_review_checklist":
        objective = _required_text(data, "objective")
        files = _text_list(data, "files")
        output = {
            "objective": objective, "files_to_review": files,
            "checks": [
                "Input validation and failure handling",
                "Authentication, authorization and secret handling",
                "Idempotency and concurrency behaviour",
                "Automated tests for success and failure paths",
                "Rollback, observability and evidence capture",
            ],
            "change_policy": "Prepare changes for review; do not deploy or merge automatically.",
        }
    elif operation == "draft_reply":
        context = _required_text(data, "lead_context")
        offer = _required_text(data, "offer")
        next_step = _required_text(data, "next_step")
        output = {
            "draft": f"Thank you for your enquiry. {context}\n\nWe can help with: {offer}.\n\n{next_step}",
            "delivery": "DRAFT_ONLY", "sent": False,
        }
    elif operation == "fulfilment_readiness":
        flags = ("payment_verified", "supplier_stock_verified", "delivery_method_verified", "customer_address_present")
        if any(not isinstance(data.get(flag), bool) for flag in flags):
            raise ValueError("all fulfilment checks must be explicit boolean values")
        missing = [flag for flag in flags if data[flag] is not True]
        output = {
            "readiness": "READY_FOR_HUMAN_APPROVAL" if not missing else "BLOCKED",
            "missing_evidence": missing, "dispatch_performed": False,
        }
        return TaskResult(operation, "COMPLETED" if not missing else "BLOCKED", output)
    elif operation == "calculate_margin":
        amounts = ("revenue_pence", "cost_pence", "fees_pence")
        if any(type(data.get(key)) is not int or data[key] < 0 for key in amounts):
            raise ValueError("revenue_pence, cost_pence and fees_pence must be non-negative integers")
        revenue, cost, fees = (data[key] for key in amounts)
        profit = revenue - cost - fees
        output = {
            "revenue_pence": revenue, "cost_pence": cost, "fees_pence": fees,
            "gross_profit_pence": profit,
            "gross_margin_percent": round((profit / revenue) * 100, 2) if revenue else None,
            "currency": "GBP",
        }
    elif operation == "draft_product_listing":
        product = _required_text(data, "product_name")
        features = _text_list(data, "features")
        condition = _required_text(data, "condition")
        delivery = _required_text(data, "delivery")
        output = {
            "title": product[:80],
            "description": f"{product}. {condition}. " + " ".join(features) + f" Delivery: {delivery}.",
            "features": features, "publication": "DRAFT_ONLY", "published": False,
        }
    else:
        raise PermissionError("operation has no registered handler")
    return TaskResult(operation, "COMPLETED", output)
