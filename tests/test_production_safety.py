import sqlite3

import pytest

from ultron.pathway import create_order, dispatch_delivery, initialize_db, seed_catalog


@pytest.fixture()
def db_path(tmp_path):
    db = tmp_path / "ultron-production-safety.db"
    initialize_db(str(db))
    seed_catalog(str(db))
    return str(db)


def test_test_token_cannot_authorize_payment_in_production(db_path, monkeypatch):
    monkeypatch.setenv("ULTRON_ENV", "production")

    result = create_order(
        db_path,
        customer_email="customer@example.com",
        product_id=1,
        quantity=1,
        payment_token="ultron-test-token-approved",
        delivery_address="1 Example Street",
    )

    assert result.payment_status == "DECLINED"
    assert result.delivery_status == "CANCELLED"

    with sqlite3.connect(db_path) as conn:
        stock = conn.execute("SELECT stock FROM products WHERE id = 1").fetchone()[0]
    assert stock == 50


def test_test_token_remains_available_only_outside_production(db_path, monkeypatch):
    monkeypatch.setenv("ULTRON_ENV", "development")

    result = create_order(
        db_path,
        customer_email="customer@example.com",
        product_id=1,
        quantity=1,
        payment_token="ultron-test-token-approved",
        delivery_address="1 Example Street",
    )

    assert result.payment_status == "AUTHORIZED"
    assert result.delivery_status == "READY"


def test_dispatch_rejects_production_without_carrier_confirmation(db_path, monkeypatch):
    monkeypatch.setenv("ULTRON_ENV", "production")
    result = create_order(
        db_path,
        customer_email="customer@example.com",
        product_id=1,
        quantity=1,
        payment_token="ultron-test-token-approved",
        delivery_address="1 Example Street",
    )

    with pytest.raises(ValueError, match="production dispatch requires carrier confirmation"):
        dispatch_delivery(db_path, result.order_id)
