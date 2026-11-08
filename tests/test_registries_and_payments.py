import sqlite3

import pytest

from ultron.agents import AGENTS
from ultron.events import EVENTS, log_event, validate_registry
from ultron.pathway import create_order, initialize_db, seed_catalog
from ultron.payments import PaymentVerificationError, StripeVerifier, get_verifier

REQUIRED_EVENTS = ["SYSTEM_START", "DAILY_RESEARCH", "NEW_OPPORTUNITY", "OPPORTUNITY_VALIDATED", "PRODUCT_APPROVED", "PRODUCT_LISTING_READY", "STOCK_CHANGE", "NEW_ORDER", "PAYMENT_CONFIRMED", "SUPPLIER_CONFIRMED", "ORDER_DISPATCHED", "TRACKING_UPDATED", "ORDER_DELIVERED", "ORDER_EXCEPTION", "SEO_RESEARCH", "BACKLINK_OPPORTUNITY", "CONTENT_READY", "DEPLOYMENT_REQUEST", "DEPLOYMENT_FAILED", "DAILY_PERFORMANCE", "SYSTEM_FAILURE", "WEEKLY_R_AND_D_REVIEW"]


@pytest.fixture()
def db(tmp_path):
    path = str(tmp_path / "u.db")
    initialize_db(path)
    seed_catalog(path)
    return path


def order(db, token, key=None, verifier=None):
    return create_order(
        db,
        customer_email="a@b.co",
        product_id=1,
        quantity=1,
        payment_token=token,
        delivery_address="1 High St",
        idempotency_key=key,
        verifier=verifier,
    )


def test_all_required_events_and_agents_defined():
    assert set(REQUIRED_EVENTS) == set(EVENTS)
    assert len(AGENTS) == 10
    assert validate_registry() == []


def test_event_requires_data_and_is_logged(db):
    with pytest.raises(ValueError):
        log_event(db, "NEW_ORDER", source="x", verified_source=False, payload={})
    eid = log_event(
        db,
        "NEW_ORDER",
        source="test",
        verified_source=False,
        payload={"order_ref": "1", "items": [], "amount": 1},
    )
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT verified_source FROM events WHERE id=?", (eid,)).fetchone() == (0,)


def test_live_mode_rejects_test_tokens_and_requires_key(monkeypatch):
    monkeypatch.delenv("STRIPE_API_KEY", raising=False)
    with pytest.raises(PaymentVerificationError):
        get_verifier("live")
    live = StripeVerifier("sk_x", fetch=lambda url, key: {"status": "requires_payment_method"})
    assert live.verify("ultron-test-token-1", 2499, "gbp") is False


def test_stripe_checks_status_amount_currency():
    intent = {"status": "succeeded", "amount_received": 2499, "currency": "gbp"}
    v = StripeVerifier("sk_x", fetch=lambda url, key: intent)
    assert v.verify("pi_1", 2499, "GBP") is True
    assert v.verify("pi_1", 2500, "gbp") is False
    assert v.verify("pi_1", 2499, "usd") is False


def test_declined_payment_does_not_reserve_stock(db):
    v = StripeVerifier("sk_x", fetch=lambda url, key: {"status": "processing"})
    res = order(db, "pi_1", verifier=v)
    assert res.payment_status == "DECLINED"
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT stock FROM products WHERE id=1").fetchone() == (50,)


def test_idempotency_prevents_duplicate_orders(db):
    first = order(db, "ultron-test-token-ok", key="k1")
    again = order(db, "ultron-test-token-ok", key="k1")
    assert again.order_id == first.order_id and again.duplicate
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT stock FROM products WHERE id=1").fetchone() == (49,)
