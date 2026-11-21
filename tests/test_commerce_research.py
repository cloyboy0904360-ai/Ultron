from __future__ import annotations

import pytest
from datetime import UTC, datetime, timedelta

from ultron.commerce_research import (
    ProductCandidate,
    SupplierOffer,
    assess_product,
    calculate_profitability,
    verify_supplier_offer,
)


NOW = datetime(2026, 11, 21, 12, 0, tzinfo=UTC)


def candidate() -> ProductCandidate:
    return ProductCandidate(
        name="Compact dehumidifier",
        category="home",
        source_url="https://retailer.example/products/dehumidifier",
        observed_price_pence=8999,
        demand_evidence_urls=("https://trends.example/dehumidifiers",),
        demand_evidence_checked_at=NOW,
    )


def supplier_offer(**overrides) -> SupplierOffer:
    values = {
        "supplier_name": "Example UK Supplier",
        "product_url": "https://supplier.example/dehumidifier",
        "stock_status": "in_stock",
        "stock_checked_at": NOW,
        "unit_cost_pence": 4200,
        "shipping_cost_pence": 500,
        "ships_to_uk": True,
        "delivery_days_min": 2,
        "delivery_days_max": 4,
        "returns_policy_url": "https://supplier.example/returns",
        "evidence_url": "https://supplier.example/dehumidifier",
        "evidence_excerpt": "In stock. £42.00. UK delivery £5.00, 2-4 working days.",
        "evidence_checked_at": NOW,
    }
    values.update(overrides)
    return SupplierOffer(**values)


def test_supplier_offer_is_verified_only_with_complete_fresh_evidence():
    result = verify_supplier_offer(supplier_offer(), now=NOW)
    assert result.status == "VERIFIED"
    assert result.unit_cost_pence == 4200
    assert result.shipping_cost_pence == 500


def test_supplier_offer_with_unknown_stock_is_blocked():
    result = verify_supplier_offer(
        supplier_offer(stock_status="unknown"), now=NOW
    )
    assert result.status == "BLOCKED"
    assert "stock_status" in result.missing_evidence


def test_supplier_offer_with_stale_stock_check_is_blocked():
    stale = NOW - timedelta(days=2)
    result = verify_supplier_offer(
        supplier_offer(stock_checked_at=stale, evidence_checked_at=stale),
        now=NOW,
        max_age=timedelta(hours=24),
    )
    assert result.status == "BLOCKED"
    assert "stock_checked_at" in result.missing_evidence


def test_supplier_offer_rejects_non_https_evidence_urls():
    with pytest.raises(ValueError, match="HTTPS"):
        supplier_offer(evidence_url="http://supplier.example/product")


def test_profitability_uses_all_costs_in_integer_pence():
    result = calculate_profitability(
        selling_price_pence=8999,
        supplier_cost_pence=4200,
        supplier_shipping_pence=500,
        marketplace_fee_pence=900,
        payment_fee_pence=250,
        other_costs_pence=100,
    )
    assert result.net_contribution_pence == 3049
    assert result.net_contribution_margin_percent == 33.88
    assert result.status == "APPROVED"


def test_profitability_rejects_below_margin_threshold():
    result = calculate_profitability(
        selling_price_pence=5000,
        supplier_cost_pence=3500,
        supplier_shipping_pence=500,
        marketplace_fee_pence=400,
        payment_fee_pence=150,
        other_costs_pence=100,
        minimum_margin_percent=20,
    )
    assert result.status == "REJECTED"
    assert result.net_contribution_pence == 350


def test_profitability_rejects_float_or_negative_money():
    with pytest.raises(ValueError, match="non-negative integer pence"):
        calculate_profitability(
            selling_price_pence=1000.0,
            supplier_cost_pence=100,
            supplier_shipping_pence=0,
            marketplace_fee_pence=0,
            payment_fee_pence=0,
            other_costs_pence=0,
        )
    with pytest.raises(ValueError, match="non-negative integer pence"):
        calculate_profitability(
            selling_price_pence=1000,
            supplier_cost_pence=-1,
            supplier_shipping_pence=0,
            marketplace_fee_pence=0,
            payment_fee_pence=0,
            other_costs_pence=0,
        )


def test_product_assessment_needs_demand_supplier_and_margin_evidence():
    assessment = assess_product(
        candidate(),
        verify_supplier_offer(supplier_offer(), now=NOW),
        calculate_profitability(
            selling_price_pence=8999,
            supplier_cost_pence=4200,
            supplier_shipping_pence=500,
            marketplace_fee_pence=900,
            payment_fee_pence=250,
            other_costs_pence=100,
        ),
        now=NOW,
    )
    assert assessment.status == "READY_FOR_LISTING_REVIEW"
    assert assessment.research_evidence_urls == (
        "https://trends.example/dehumidifiers",
    )


def test_product_assessment_blocks_when_demand_evidence_is_stale():
    stale_candidate = ProductCandidate(
        name="Compact dehumidifier",
        category="home",
        source_url="https://retailer.example/products/dehumidifier",
        observed_price_pence=8999,
        demand_evidence_urls=("https://trends.example/dehumidifiers",),
        demand_evidence_checked_at=NOW - timedelta(days=45),
    )
    assessment = assess_product(
        stale_candidate,
        verify_supplier_offer(supplier_offer(), now=NOW),
        calculate_profitability(
            selling_price_pence=8999,
            supplier_cost_pence=4200,
            supplier_shipping_pence=500,
            marketplace_fee_pence=900,
            payment_fee_pence=250,
            other_costs_pence=100,
        ),
        now=NOW,
    )
    assert assessment.status == "BLOCKED"
    assert "demand_evidence" in assessment.missing_evidence
