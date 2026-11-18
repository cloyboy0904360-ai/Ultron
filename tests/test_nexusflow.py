import hashlib
import hmac
import json
import sqlite3
import time

import pytest

from ultron.nexusflow import (
    LedgerIntegrityError,
    initialize_nexusflow_db,
    process_stripe_webhook,
    verify_ledger,
)


def signed(payload, secret="whsec_test", timestamp=None):
    timestamp = int(time.time()) if timestamp is None else timestamp
    signed_payload = str(timestamp).encode() + b"." + payload
    digest = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={digest}"


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "nexusflow.sqlite3")
    initialize_nexusflow_db(path)
    return path


def checkout_event(event_id="evt_1", payment_status="paid", amount=4900, currency="gbp"):
    return {
        "id": event_id,
        "type": "checkout.session.completed",
        "created": 1794480000,
        "data": {"object": {
            "id": "cs_test_1",
            "payment_intent": "pi_test_1",
            "payment_status": payment_status,
            "amount_total": amount,
            "currency": currency,
            "metadata": {"sku": "AUDIT-49", "order_id": "ORDER-1"},
        }},
    }


def test_verified_paid_checkout_records_once_and_queues_digital_fulfilment(db_path):
    payload = json.dumps(checkout_event(), separators=(",", ":")).encode()
    result = process_stripe_webhook(db_path, payload, signed(payload), "whsec_test")

    assert result == {"status": "RECORDED", "event_id": "evt_1", "fulfilment": "PENDING"}
    with sqlite3.connect(db_path) as conn:
        payment = conn.execute(
            "SELECT amount_minor, currency, sku, payment_intent_id FROM revenue_ledger"
        ).fetchone()
        fulfilment = conn.execute(
            "SELECT status, order_id, sku FROM digital_fulfilments"
        ).fetchone()
    assert payment == (4900, "gbp", "AUDIT-49", "pi_test_1")
    assert fulfilment == ("PENDING", "ORDER-1", "AUDIT-49")
    assert verify_ledger(db_path)["valid"] is True


def test_replayed_event_is_idempotent_and_does_not_duplicate_fulfilment(db_path):
    payload = json.dumps(checkout_event(), separators=(",", ":")).encode()
    signature = signed(payload)
    process_stripe_webhook(db_path, payload, signature, "whsec_test")
    result = process_stripe_webhook(db_path, payload, signature, "whsec_test")
    assert result["status"] == "DUPLICATE"
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM revenue_ledger").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM digital_fulfilments").fetchone()[0] == 1


@pytest.mark.parametrize("signature", ["", "t=1,v1=bad", "v1=bad"])
def test_invalid_signature_is_rejected_without_writing(db_path, signature):
    payload = json.dumps(checkout_event()).encode()
    with pytest.raises(ValueError, match="signature"):
        process_stripe_webhook(db_path, payload, signature, "whsec_test")
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM revenue_ledger").fetchone()[0] == 0


def test_unpaid_or_wrong_event_never_enters_revenue_ledger(db_path):
    event = checkout_event(payment_status="unpaid")
    payload = json.dumps(event).encode()
    with pytest.raises(ValueError, match="not paid"):
        process_stripe_webhook(db_path, payload, signed(payload), "whsec_test")
    event = checkout_event()
    event["type"] = "checkout.session.expired"
    payload = json.dumps(event).encode()
    with pytest.raises(ValueError, match="unsupported event"):
        process_stripe_webhook(db_path, payload, signed(payload), "whsec_test")


def test_ledger_detects_modified_financial_record(db_path):
    payload = json.dumps(checkout_event(), separators=(",", ":")).encode()
    process_stripe_webhook(db_path, payload, signed(payload), "whsec_test")
    with sqlite3.connect(db_path) as conn:
        conn.execute("UPDATE revenue_ledger SET amount_minor = 1 WHERE event_id = 'evt_1'")
    with pytest.raises(LedgerIntegrityError):
        verify_ledger(db_path)
