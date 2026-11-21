"""Evidence-first product research, supplier verification and profitability.

This module is deliberately non-publishing and non-purchasing. It evaluates
structured evidence supplied by an operator or a future read-only source adapter.
A VERIFIED result means the required fields and evidence freshness checks passed;
it does not independently prove that a supplier page is truthful.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse


def _https_url(value: str | None, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty HTTPS URL")
    parsed = urlparse(value.strip())
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"{field} must use HTTPS")


def _aware_datetime(value: datetime | None, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be a timezone-aware datetime")


def _optional_pence(value: int | None, field: str) -> None:
    if value is not None and (type(value) is not int or value < 0):
        raise ValueError(f"{field} must be a non-negative integer pence value")


def _now(value: datetime | None) -> datetime:
    result = value or datetime.now(UTC)
    _aware_datetime(result, "now")
    return result


@dataclass(frozen=True)
class ProductCandidate:
    """A product research lead with dated, traceable demand evidence."""

    name: str
    category: str
    source_url: str
    observed_price_pence: int
    demand_evidence_urls: tuple[str, ...]
    demand_evidence_checked_at: datetime

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.category.strip():
            raise ValueError("product name and category must be non-empty")
        _https_url(self.source_url, "source_url")
        if type(self.observed_price_pence) is not int or self.observed_price_pence <= 0:
            raise ValueError("observed_price_pence must be a positive integer pence value")
        if not isinstance(self.demand_evidence_urls, tuple):
            raise TypeError("demand_evidence_urls must be a tuple of HTTPS URLs")
        for url in self.demand_evidence_urls:
            _https_url(url, "demand_evidence_url")
        _aware_datetime(self.demand_evidence_checked_at, "demand_evidence_checked_at")


@dataclass(frozen=True)
class SupplierOffer:
    """A supplier offer; unknown fields remain unknown and never default to verified."""

    supplier_name: str
    product_url: str
    stock_status: str
    stock_checked_at: datetime | None
    unit_cost_pence: int | None
    shipping_cost_pence: int | None
    ships_to_uk: bool | None
    delivery_days_min: int | None
    delivery_days_max: int | None
    returns_policy_url: str | None
    evidence_url: str | None
    evidence_excerpt: str | None
    evidence_checked_at: datetime | None

    def __post_init__(self) -> None:
        if not isinstance(self.supplier_name, str) or not self.supplier_name.strip():
            raise ValueError("supplier_name must be a non-empty string")
        _https_url(self.product_url, "product_url")
        if self.stock_status not in {"in_stock", "out_of_stock", "unknown"}:
            raise ValueError("stock_status must be in_stock, out_of_stock or unknown")
        _optional_pence(self.unit_cost_pence, "unit_cost_pence")
        _optional_pence(self.shipping_cost_pence, "shipping_cost_pence")
        if self.ships_to_uk is not None and type(self.ships_to_uk) is not bool:
            raise ValueError("ships_to_uk must be true, false or unknown")
        for field in ("delivery_days_min", "delivery_days_max"):
            value = getattr(self, field)
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError(f"{field} must be a non-negative integer")
        if (
            self.delivery_days_min is not None
            and self.delivery_days_max is not None
            and self.delivery_days_min > self.delivery_days_max
        ):
            raise ValueError("delivery_days_min cannot exceed delivery_days_max")
        if self.returns_policy_url is not None:
            _https_url(self.returns_policy_url, "returns_policy_url")
        if self.evidence_url is not None:
            _https_url(self.evidence_url, "evidence_url")
        for field in ("stock_checked_at", "evidence_checked_at"):
            value = getattr(self, field)
            if value is not None:
                _aware_datetime(value, field)


@dataclass(frozen=True)
class SupplierVerification:
    status: str
    missing_evidence: tuple[str, ...]
    supplier_name: str
    unit_cost_pence: int | None
    shipping_cost_pence: int | None
    ships_to_uk: bool | None
    delivery_days_min: int | None
    delivery_days_max: int | None
    evidence_url: str | None
    stock_checked_at: str | None
    evidence_checked_at: str | None
    evidence_excerpt: str | None
    returns_policy_url: str | None


def verify_supplier_offer(
    offer: SupplierOffer,
    *,
    now: datetime | None = None,
    max_age: timedelta = timedelta(hours=24),
) -> SupplierVerification:
    """Verify that an offer has complete, recent evidence for a UK fulfilment route."""
    checked_at = _now(now)
    if max_age.total_seconds() <= 0:
        raise ValueError("max_age must be positive")
    missing: list[str] = []
    if offer.stock_status != "in_stock":
        missing.append("stock_status")
    if (
        offer.stock_checked_at is None
        or offer.stock_checked_at > checked_at
        or checked_at - offer.stock_checked_at > max_age
    ):
        missing.append("stock_checked_at")
    if offer.unit_cost_pence is None:
        missing.append("unit_cost_pence")
    if offer.shipping_cost_pence is None:
        missing.append("shipping_cost_pence")
    if offer.ships_to_uk is not True:
        missing.append("ships_to_uk")
    if offer.delivery_days_min is None or offer.delivery_days_max is None:
        missing.append("delivery_estimate")
    if offer.returns_policy_url is None:
        missing.append("returns_policy_url")
    if not offer.evidence_url or not offer.evidence_excerpt:
        missing.append("source_evidence")
    if (
        offer.evidence_checked_at is None
        or offer.evidence_checked_at > checked_at
        or checked_at - offer.evidence_checked_at > max_age
    ):
        missing.append("evidence_checked_at")
    return SupplierVerification(
        status="VERIFIED" if not missing else "BLOCKED",
        missing_evidence=tuple(missing),
        supplier_name=offer.supplier_name,
        unit_cost_pence=offer.unit_cost_pence,
        shipping_cost_pence=offer.shipping_cost_pence,
        ships_to_uk=offer.ships_to_uk,
        delivery_days_min=offer.delivery_days_min,
        delivery_days_max=offer.delivery_days_max,
        evidence_url=offer.evidence_url,
        stock_checked_at=offer.stock_checked_at.isoformat() if offer.stock_checked_at else None,
        evidence_checked_at=offer.evidence_checked_at.isoformat() if offer.evidence_checked_at else None,
        evidence_excerpt=offer.evidence_excerpt,
        returns_policy_url=offer.returns_policy_url,
    )


@dataclass(frozen=True)
class ProfitabilityResult:
    status: str
    selling_price_pence: int
    supplier_cost_pence: int | None
    supplier_shipping_pence: int | None
    marketplace_fee_pence: int | None
    payment_fee_pence: int | None
    other_costs_pence: int | None
    gross_profit_pence: int | None
    net_contribution_pence: int | None
    net_contribution_margin_percent: float | None
    missing_costs: tuple[str, ...]


def calculate_profitability(
    *,
    selling_price_pence: int,
    supplier_cost_pence: int | None,
    supplier_shipping_pence: int | None,
    marketplace_fee_pence: int | None,
    payment_fee_pence: int | None,
    other_costs_pence: int | None,
    minimum_margin_percent: float = 20.0,
) -> ProfitabilityResult:
    """Calculate a full per-unit contribution in integer pence.

    Any unknown cost makes the result UNVERIFIED; it is never treated as zero.
    """
    if type(selling_price_pence) is not int or selling_price_pence <= 0:
        raise ValueError("selling_price_pence must be a positive integer pence value")
    if (
        isinstance(minimum_margin_percent, bool)
        or not isinstance(minimum_margin_percent, (int, float))
        or not 0 <= minimum_margin_percent <= 100
    ):
        raise ValueError("minimum_margin_percent must be between 0 and 100")
    costs = {
        "supplier_cost_pence": supplier_cost_pence,
        "supplier_shipping_pence": supplier_shipping_pence,
        "marketplace_fee_pence": marketplace_fee_pence,
        "payment_fee_pence": payment_fee_pence,
        "other_costs_pence": other_costs_pence,
    }
    for field, value in costs.items():
        _optional_pence(value, field)
    missing = tuple(field for field, value in costs.items() if value is None)
    if missing:
        return ProfitabilityResult(
            status="UNVERIFIED",
            selling_price_pence=selling_price_pence,
            gross_profit_pence=None,
            net_contribution_pence=None,
            net_contribution_margin_percent=None,
            missing_costs=missing,
            **costs,
        )
    gross_profit = selling_price_pence - supplier_cost_pence - supplier_shipping_pence
    net = gross_profit - marketplace_fee_pence - payment_fee_pence - other_costs_pence
    margin = round((net / selling_price_pence) * 100, 2)
    return ProfitabilityResult(
        status="APPROVED" if margin >= minimum_margin_percent else "REJECTED",
        selling_price_pence=selling_price_pence,
        gross_profit_pence=gross_profit,
        net_contribution_pence=net,
        net_contribution_margin_percent=margin,
        missing_costs=(),
        **costs,
    )


@dataclass(frozen=True)
class ProductAssessment:
    status: str
    missing_evidence: tuple[str, ...]
    research_evidence_urls: tuple[str, ...]
    product_source_url: str
    observed_price_pence: int
    demand_evidence_checked_at: str
    supplier_evidence_url: str | None
    net_contribution_pence: int | None
    net_contribution_margin_percent: float | None
    publication_allowed: bool = False


def assess_product(
    candidate: ProductCandidate,
    supplier: SupplierVerification,
    profitability: ProfitabilityResult,
    *,
    now: datetime | None = None,
    demand_max_age: timedelta = timedelta(days=30),
) -> ProductAssessment:
    """Combine demand, supplier and margin evidence without authorising publication."""
    checked_at = _now(now)
    if demand_max_age.total_seconds() <= 0:
        raise ValueError("demand_max_age must be positive")
    missing: list[str] = []
    if not candidate.demand_evidence_urls:
        missing.append("demand_evidence")
    if (
        candidate.demand_evidence_checked_at > checked_at
        or checked_at - candidate.demand_evidence_checked_at > demand_max_age
    ):
        missing.append("demand_evidence")
    if supplier.status != "VERIFIED":
        missing.extend(f"supplier:{item}" for item in supplier.missing_evidence)
    if profitability.status != "APPROVED":
        missing.append("profitability")
    missing = list(dict.fromkeys(missing))
    return ProductAssessment(
        status="READY_FOR_LISTING_REVIEW" if not missing else "BLOCKED",
        missing_evidence=tuple(missing),
        research_evidence_urls=candidate.demand_evidence_urls,
        product_source_url=candidate.source_url,
        observed_price_pence=candidate.observed_price_pence,
        demand_evidence_checked_at=candidate.demand_evidence_checked_at.isoformat(),
        supplier_evidence_url=supplier.evidence_url,
        net_contribution_pence=profitability.net_contribution_pence,
        net_contribution_margin_percent=profitability.net_contribution_margin_percent,
        publication_allowed=False,
    )
