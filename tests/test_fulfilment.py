import pytest

from ultron.fulfilment import (
    FulfilmentError,
    PaymentEvidence,
    SupplierEvidence,
    TrackingEvidence,
    close_and_reconcile,
    confirm_payment,
    confirm_supplier,
    record_delivery,
    record_dispatch,
    record_tracking,
    start,
)
from ultron.pathway import create_order, initialize_db, seed_catalog


@pytest.fixture()
def db(tmp_path):
    path = str(tmp_path / "u.db")
    initialize_db(path)
    seed_catalog(path)
    return path


def _order(db, token="ultron-test-token-ok"):
    return create_order(
        db,
        customer_email="a@b.co",
        product_id=1,
        quantity=1,
        payment_token=token,
        delivery_address="1 High St",
    )


def _paid(db):
    """Gate fixture only. This does not contact Stripe and is not a sale."""
    result = _order(db)
    start(db, result.order_id)
    confirm_payment(
        db,
        result.order_id,
        PaymentEvidence("stripe", "pi_test_gate", result.total_cents, "gbp", "succeeded", True),
    )
    return result


def test_test_token_cannot_verify_payment(db):
    result = _order(db)
    start(db, result.order_id)
    with pytest.raises(FulfilmentError, match="test provider"):
        confirm_payment(
            db,
            result.order_id,
            PaymentEvidence("test", "ultron-test-token-ok", result.total_cents, "gbp", "succeeded", True),
        )


def test_known_loss_refuses_supplier(db):
    result = _paid(db)
    with pytest.raises(FulfilmentError, match="known loss"):
        confirm_supplier(
            db,
            result.order_id,
            SupplierEvidence("dbs", "S1", True, True, True, 2400, 50, 49),
            owner_approved_spend=True,
        )


def test_supplier_spend_needs_approval(db):
    result = _paid(db)
    with pytest.raises(FulfilmentError, match="owner approval"):
        confirm_supplier(
            db,
            result.order_id,
            SupplierEvidence("dbs", "S1", True, True, True, 1000, 200, 100),
            owner_approved_spend=False,
        )


def test_cannot_reconcile_before_delivery(db):
    result = _paid(db)
    with pytest.raises(FulfilmentError, match="PAYMENT_VERIFIED"):
        close_and_reconcile(db, result.order_id)


def test_full_chain_reconciles_recorded_cents_only(db):
    result = _paid(db)
    confirm_supplier(
        db,
        result.order_id,
        SupplierEvidence("dbs", "S1", True, True, True, 1000, 200, 100),
        owner_approved_spend=True,
    )
    record_dispatch(db, result.order_id, "DSP-1")
    record_tracking(db, result.order_id, TrackingEvidence("RM123", "royal-mail", "in_transit"))
    record_delivery(db, result.order_id, carrier_status="delivered", delivered_at="2026-11-08T12:00:00+00:00")
    rec = close_and_reconcile(db, result.order_id)
    assert rec.revenue_cents == 2499
    assert rec.profit_cents == 2499 - 1000 - 200 - 100
    assert rec.payment_ref == "pi_test_gate"
