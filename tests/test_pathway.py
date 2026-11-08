import sqlite3

import pytest

from ultron.pathway import create_order, dispatch_delivery, initialize_db, seed_catalog


@pytest.fixture()
def db_path(tmp_path):
    db = tmp_path / "ultron.db"
    initialize_db(str(db))
    seed_catalog(str(db))
    return str(db)


def test_payment_to_delivery_success_path(db_path):
    result = create_order(
        db_path,
        customer_email="ops@ultron.local",
        product_id=1,
        quantity=2,
        payment_token="ultron-test-token-approved",
        delivery_address="42 Tower Plaza",
    )

    assert result.payment_status == "AUTHORIZED"
    assert result.delivery_status == "READY"
    assert result.total_cents == 4998

    tracking_id = dispatch_delivery(db_path, result.order_id)
    assert tracking_id.startswith("TEST-ULTRON-")

    with sqlite3.connect(db_path) as conn:
        stock = conn.execute("SELECT stock FROM products WHERE id = 1").fetchone()[0]
        delivery = conn.execute(
            "SELECT status FROM deliveries WHERE order_id = ?",
            (result.order_id,),
        ).fetchone()[0]
        order_status = conn.execute(
            "SELECT delivery_status FROM orders WHERE id = ?",
            (result.order_id,),
        ).fetchone()[0]

    assert stock == 48
    assert delivery == "DISPATCHED"
    assert order_status == "DISPATCHED"


def test_declined_payment_cancels_delivery_and_preserves_stock(db_path):
    result = create_order(
        db_path,
        customer_email="ops@ultron.local",
        product_id=2,
        quantity=1,
        payment_token="bad-token",
        delivery_address="42 Tower Plaza",
    )

    assert result.payment_status == "DECLINED"
    assert result.delivery_status == "CANCELLED"

    with sqlite3.connect(db_path) as conn:
        stock = conn.execute("SELECT stock FROM products WHERE id = 2").fetchone()[0]
    assert stock == 20

    with pytest.raises(ValueError, match="not dispatchable"):
        dispatch_delivery(db_path, result.order_id)


def test_insufficient_stock_is_rejected(db_path):
    with pytest.raises(ValueError, match="insufficient stock"):
        create_order(
            db_path,
            customer_email="ops@ultron.local",
            product_id=3,
            quantity=999,
            payment_token="ultron-test-token-approved",
            delivery_address="42 Tower Plaza",
        )
