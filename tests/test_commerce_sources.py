from __future__ import annotations

from datetime import UTC, datetime
import json

import pytest

from ultron.commerce_sources import (
    SourceDefinition,
    collect_sources,
    collection_to_dict,
    fetch_https,
)


NOW = datetime(2026, 11, 21, 12, 0, tzinfo=UTC)


def source(kind="product_rss", **overrides):
    values = {
        "name": "Test Product Feed",
        "kind": kind,
        "url": "https://feeds.example/products.xml",
        "allowed_hosts": ("feeds.example",),
    }
    values.update(overrides)
    return SourceDefinition(**values)


def fake_fetch(body, content_type):
    def fetcher(url, *, allowed_hosts):
        assert url == "https://feeds.example/products.xml"
        assert "feeds.example" in allowed_hosts
        return body, content_type
    return fetcher


def test_source_requires_explicit_https_host_allowlist():
    with pytest.raises(ValueError, match="allowlisted"):
        source(allowed_hosts=("other.example",))


def test_source_rejects_http_and_unknown_types():
    with pytest.raises(ValueError, match="HTTPS"):
        source(url="http://feeds.example/products.xml")
    with pytest.raises(ValueError, match="unsupported"):
        source(kind="scrape_arbitrary_web")


def test_product_rss_collection_retains_source_and_time():
    body = b"""<?xml version="1.0"?>
    <rss version="2.0"><channel><item>
      <title>Portable dehumidifier</title>
      <link>https://feeds.example/items/dehumidifier</link>
      <description>Popular compact home appliance</description>
    </item></channel></rss>"""
    result = collect_sources([source()], fetcher=fake_fetch(body, "application/rss+xml"), now=NOW)
    assert result.sources_succeeded == 1
    assert len(result.records) == 1
    record = result.records[0]
    assert record.title == "Portable dehumidifier"
    assert record.source_name == "Test Product Feed"
    assert record.observed_at == NOW.isoformat()
    assert record.price_pence is None


def test_demand_feed_does_not_claim_product_stock_or_sales():
    body = b"""<rss><channel><item>
      <title>Home dehumidifier searches rising</title>
      <link>https://feeds.example/trends/dehumidifier</link>
      <description>Search interest signal</description>
    </item></channel></rss>"""
    result = collect_sources(
        [source(kind="demand_rss")],
        fetcher=fake_fetch(body, "application/rss+xml"),
        now=NOW,
    )
    payload = collection_to_dict(result)
    assert payload["records"][0]["source_kind"] == "demand_rss"
    assert payload["records"][0]["price_pence"] is None
    assert "not verified sales demand" in payload["limitations"][0]


def test_supplier_json_collection_rejects_non_json_content_type():
    result = collect_sources(
        [source(kind="supplier_json")],
        fetcher=fake_fetch(b'{"offers": []}', "text/html"),
        now=NOW,
    )
    assert result.sources_succeeded == 0
    assert "Test Product Feed" in result.source_errors


def test_supplier_json_rejects_invalid_price_and_external_record_url():
    invalid_price = json.dumps({"offers": [{
        "title": "Item", "url": "https://feeds.example/item", "price_pence": 12.5
    }]}).encode()
    result = collect_sources(
        [source(kind="supplier_json")],
        fetcher=fake_fetch(invalid_price, "application/json"),
        now=NOW,
    )
    assert "price_pence" in result.source_errors["Test Product Feed"]

    external_url = json.dumps({"offers": [{
        "title": "Item", "url": "https://untrusted.example/item"
    }]}).encode()
    result = collect_sources(
        [source(kind="supplier_json")],
        fetcher=fake_fetch(external_url, "application/json"),
        now=NOW,
    )
    assert "not allowlisted" in result.source_errors["Test Product Feed"]


def test_source_errors_are_isolated_and_not_silently_dropped():
    good = b"<rss><channel><item><title>One</title><link>https://feeds.example/1</link></item></channel></rss>"
    sources = [
        source(name="Good"),
        source(name="Bad", url="https://feeds.example/bad.xml"),
    ]

    def fetcher(url, *, allowed_hosts):
        if url.endswith("bad.xml"):
            raise RuntimeError("temporary upstream failure")
        return good, "application/rss+xml"

    result = collect_sources(sources, fetcher=fetcher, now=NOW)
    assert result.sources_succeeded == 1
    assert len(result.records) == 1
    assert "Bad" in result.source_errors
    assert "Good" not in result.source_errors


def test_disabled_source_is_not_requested():
    def forbidden_fetcher(*args, **kwargs):
        raise AssertionError("disabled source must not be fetched")

    result = collect_sources(
        [source(enabled=False)], fetcher=forbidden_fetcher, now=NOW
    )
    assert result.sources_configured == 0
    assert result.records == ()


def test_collection_rejects_naive_timestamps():
    with pytest.raises(ValueError, match="timezone-aware"):
        collect_sources([], now=datetime(2026, 11, 21))


def test_fetch_https_rejects_host_not_in_allowlist_before_network():
    with pytest.raises(ValueError, match="not allowlisted"):
        fetch_https("https://untrusted.example/feed", allowed_hosts=("feeds.example",))


def test_supplier_json_retains_offer_evidence_without_claiming_independent_verification():
    offer = {
        "title": "Portable dehumidifier",
        "url": "https://feeds.example/items/dehumidifier",
        "price_pence": 4200,
        "stock_status": "in_stock",
        "stock_checked_at": NOW.isoformat(),
        "unit_cost_pence": 4200,
        "shipping_cost_pence": 500,
        "ships_to_uk": True,
        "delivery_days_min": 2,
        "delivery_days_max": 4,
        "returns_policy_url": "https://feeds.example/returns",
        "evidence_excerpt": "In stock, UK delivery.",
        "evidence_checked_at": NOW.isoformat(),
    }
    result = collect_sources(
        [source(kind="supplier_json")],
        fetcher=fake_fetch(json.dumps({"offers": [offer]}).encode(), "application/json"),
        now=NOW,
    )
    assert result.sources_succeeded == 1
    record = result.records[0]
    assert record.supplier_evidence["stock_status"] == "in_stock"
    assert record.supplier_evidence["unit_cost_pence"] == 4200
    assert record.supplier_evidence["returns_policy_url"] == "https://feeds.example/returns"
    assert "not independently audited" in record.summary
