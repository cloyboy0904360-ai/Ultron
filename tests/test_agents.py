from datetime import UTC, datetime

import pytest

from ultron.agents import AGENT_OPERATIONS, execute_task

NOW = datetime.now(UTC).isoformat()


def test_six_agents_have_separate_allowlisted_capabilities():
    assert set(AGENT_OPERATIONS) == {"NOVA", "FORGE", "SALES", "OPS", "FINANCE", "PIXEL"}
    assert "verify_supplier_offer" in AGENT_OPERATIONS["OPS"]
    assert "calculate_product_profitability" in AGENT_OPERATIONS["FINANCE"]
    assert "assess_product_candidate" in AGENT_OPERATIONS["PIXEL"]


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


def test_finance_product_profitability_marks_unknown_fees_unverified():
    result = execute_task("FINANCE", "calculate_product_profitability", {
        "selling_price_pence": 9000,
        "supplier_cost_pence": 4000,
        "supplier_shipping_pence": 500,
        "marketplace_fee_pence": None,
        "payment_fee_pence": 200,
        "other_costs_pence": 0,
    })
    assert result.status == "BLOCKED"
    assert result.output["status"] == "UNVERIFIED"
    assert result.output["net_contribution_pence"] is None


def test_ops_supplier_verification_requires_recent_stock_evidence():
    result = execute_task("OPS", "verify_supplier_offer", {
        "supplier_name": "Example UK Supplier",
        "product_url": "https://supplier.example/item",
        "stock_status": "in_stock",
        "stock_checked_at": NOW,
        "unit_cost_pence": 4000,
        "shipping_cost_pence": 500,
        "ships_to_uk": True,
        "delivery_days_min": 2,
        "delivery_days_max": 4,
        "returns_policy_url": "https://supplier.example/returns",
        "evidence_url": "https://supplier.example/item",
        "evidence_excerpt": "In stock; £40; UK tracked delivery.",
        "evidence_checked_at": NOW,
    })
    assert result.status == "COMPLETED"
    assert result.output["status"] == "VERIFIED"


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


def test_pixel_product_assessment_rechecks_raw_evidence_and_never_publishes():
    result = execute_task("PIXEL", "assess_product_candidate", {
        "product": {
            "name": "Compact dehumidifier",
            "category": "home",
            "source_url": "https://retailer.example/item",
            "observed_price_pence": 8999,
            "demand_evidence_urls": ["https://trends.example/item"],
            "demand_evidence_checked_at": NOW,
        },
        "supplier_offer": {
            "supplier_name": "Example UK Supplier",
            "product_url": "https://supplier.example/item",
            "stock_status": "in_stock",
            "stock_checked_at": NOW,
            "unit_cost_pence": 4200,
            "shipping_cost_pence": 500,
            "ships_to_uk": True,
            "delivery_days_min": 2,
            "delivery_days_max": 4,
            "returns_policy_url": "https://supplier.example/returns",
            "evidence_url": "https://supplier.example/item",
            "evidence_excerpt": "In stock; £42; UK tracked delivery.",
            "evidence_checked_at": NOW,
        },
        "profitability": {
            "selling_price_pence": 8999,
            "supplier_cost_pence": 4200,
            "supplier_shipping_pence": 500,
            "marketplace_fee_pence": 900,
            "payment_fee_pence": 250,
            "other_costs_pence": 100,
        },
    })
    assert result.output["status"] == "READY_FOR_LISTING_REVIEW"
    assert result.output["publication_allowed"] is False
    assert result.output["supplier_verification"]["status"] == "VERIFIED"


def test_pixel_assessment_does_not_trust_caller_claim_of_supplier_verified():
    result = execute_task("PIXEL", "assess_product_candidate", {
        "product": {
            "name": "Compact dehumidifier",
            "category": "home",
            "source_url": "https://retailer.example/item",
            "observed_price_pence": 8999,
            "demand_evidence_urls": ["https://trends.example/item"],
            "demand_evidence_checked_at": NOW,
        },
        "supplier_offer": {
            "supplier_name": "Example UK Supplier",
            "product_url": "https://supplier.example/item",
            "stock_status": "unknown",
            "stock_checked_at": NOW,
            "unit_cost_pence": 4200,
            "shipping_cost_pence": 500,
            "ships_to_uk": True,
            "delivery_days_min": 2,
            "delivery_days_max": 4,
            "returns_policy_url": "https://supplier.example/returns",
            "evidence_url": "https://supplier.example/item",
            "evidence_excerpt": "Supplier status not confirmed.",
            "evidence_checked_at": NOW,
        },
        "profitability": {
            "selling_price_pence": 8999,
            "supplier_cost_pence": 4200,
            "supplier_shipping_pence": 500,
            "marketplace_fee_pence": 900,
            "payment_fee_pence": 250,
            "other_costs_pence": 100,
        },
    })
    assert result.status == "BLOCKED"
    assert result.output["status"] == "BLOCKED"
    assert "stock_status" in result.output["supplier_verification"]["missing_evidence"]


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
