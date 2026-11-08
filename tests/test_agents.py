import pytest

from ultron.agents import AGENT_OPERATIONS, execute_task


def test_six_agents_have_separate_allowlisted_capabilities():
    assert set(AGENT_OPERATIONS) == {"NOVA", "FORGE", "SALES", "OPS", "FINANCE", "PIXEL"}
    assert all(len(operations) == 1 for operations in AGENT_OPERATIONS.values())


def test_agent_cannot_execute_another_agents_operation():
    with pytest.raises(PermissionError, match="not permitted"):
        execute_task("SALES", "calculate_margin", {"revenue_pence": 100, "cost_pence": 20, "fees_pence": 5})


def test_finance_calculates_margin_using_integer_pence():
    result = execute_task("FINANCE", "calculate_margin", {
        "revenue_pence": 900, "cost_pence": 300, "fees_pence": 50
    })
    assert result.status == "COMPLETED"
    assert result.output["gross_profit_pence"] == 550
    assert result.output["gross_margin_percent"] == 61.11


def test_finance_rejects_float_currency_values():
    with pytest.raises(ValueError, match="non-negative integers"):
        execute_task("FINANCE", "calculate_margin", {
            "revenue_pence": 9.0, "cost_pence": 3, "fees_pence": 1
        })


def test_sales_output_is_draft_only():
    result = execute_task("SALES", "draft_reply", {
        "lead_context": "You asked about our audit service",
        "offer": "a fixed-price audit",
        "next_step": "Reply if you would like the scope",
    })
    assert result.output["sent"] is False
    assert result.output["delivery"] == "DRAFT_ONLY"


def test_ops_blocks_missing_payment_or_stock_evidence():
    result = execute_task("OPS", "fulfilment_readiness", {
        "payment_verified": False,
        "supplier_stock_verified": True,
        "delivery_method_verified": True,
        "customer_address_present": True,
    })
    assert result.status == "BLOCKED"
    assert result.output["dispatch_performed"] is False
    assert result.output["missing_evidence"] == ["payment_verified"]


def test_pixel_listing_is_not_published():
    result = execute_task("PIXEL", "draft_product_listing", {
        "product_name": "Portable safety gate",
        "features": ["Pressure fit", "Adjustable width"],
        "condition": "New",
        "delivery": "UK tracked delivery",
    })
    assert result.output["published"] is False
    assert result.output["publication"] == "DRAFT_ONLY"


def test_nova_requires_an_objective():
    with pytest.raises(ValueError, match="objective"):
        execute_task("NOVA", "break_down_objective", {"constraints": []})


def test_forge_returns_review_checks_without_deploying():
    result = execute_task("FORGE", "code_review_checklist", {
        "objective": "Review webhook signature verification",
        "files": ["ultron/webhooks.py"],
    })
    assert "Authentication, authorization and secret handling" in result.output["checks"]
    assert "do not deploy" in result.output["change_policy"]
