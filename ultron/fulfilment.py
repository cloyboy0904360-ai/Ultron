"""Order lifecycle gates. Records evidence; never calls a supplier, carrier, or bank.

A local tracking id from pathway.dispatch_delivery is not carrier proof.
A test-token authorization is not a verified payment.
Profit is calculated only after CLOSED, from stored cents, and is not a bank settlement.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime

_TEST_PROVIDERS = frozenset({"", "test", "ultron-test"})


class FulfilmentError(ValueError):
    pass


@dataclass(frozen=True)
class PaymentEvidence:
    provider: str
    payment_ref: str
    amount_cents: int
    currency: str
    provider_status: str
    verified_with_provider: bool


@dataclass(frozen=True)
class SupplierEvidence:
    supplier_name: str
    supplier_ref: str
    identity_verified: bool
    product_available: bool
    uk_delivery: bool
    supplier_cost_cents: int
    delivery_cost_cents: int
    fees_cents: int


@dataclass(frozen=True)
class TrackingEvidence:
    tracking_id: str
    carrier: str
    carrier_status: str


@dataclass(frozen=True)
class Reconciliation:
    order_id: int
    revenue_cents: int
    fees_cents: int
    supplier_cost_cents: int
    delivery_cost_cents: int
    profit_cents: int
    payment_provider: str
    payment_ref: str


def _now() -> str:
    return datetime.now(tz=UTC).isoformat()


def _row(conn: sqlite3.Connection, order_id: int) -> sqlite3.Row:
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM fulfilment WHERE order_id = ?", (order_id,)).fetchone()
    if row is None:
        raise FulfilmentError("fulfilment record not found")
    return row


def _require(row: sqlite3.Row, expected: str) -> None:
    if row["state"] != expected:
        raise FulfilmentError(f"refusing transition from {row['state']}; need {expected}")


def start(db_path: str, order_id: int) -> str:
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        order = conn.execute(
            "SELECT payment_status FROM orders WHERE id = ?",
            (order_id,),
        ).fetchone()
        if order is None:
            raise FulfilmentError("order not found")
        if order[0] != "AUTHORIZED":
            raise FulfilmentError("order payment is not authorized")
        conn.execute(
            "INSERT INTO fulfilment(order_id, state, updated_at) VALUES (?, 'ORDER_RECEIVED', ?)",
            (order_id, _now()),
        )
        conn.commit()
    return "ORDER_RECEIVED"


def confirm_payment(db_path: str, order_id: int, evidence: PaymentEvidence) -> str:
    if evidence.provider.lower() in _TEST_PROVIDERS:
        raise FulfilmentError("test provider cannot verify a payment")
    if not evidence.verified_with_provider or evidence.provider_status != "succeeded":
        raise FulfilmentError("payment was not verified as succeeded with the provider")
    if not evidence.payment_ref or evidence.amount_cents <= 0:
        raise FulfilmentError("payment reference and amount are required")
    with sqlite3.connect(db_path) as conn:
        row = _row(conn, order_id)
        _require(row, "ORDER_RECEIVED")
        total = conn.execute(
            "SELECT total_cents FROM orders WHERE id = ?",
            (order_id,),
        ).fetchone()[0]
        if evidence.amount_cents != total:
            raise FulfilmentError("payment amount does not match the order")
        conn.execute(
            """
            UPDATE fulfilment
            SET state = 'PAYMENT_VERIFIED', payment_provider = ?, payment_ref = ?, updated_at = ?
            WHERE order_id = ?
            """,
            (evidence.provider, evidence.payment_ref, _now(), order_id),
        )
        conn.execute(
            "UPDATE orders SET payment_status = 'VERIFIED' WHERE id = ?",
            (order_id,),
        )
        conn.commit()
    return "PAYMENT_VERIFIED"


def confirm_supplier(
    db_path: str,
    order_id: int,
    evidence: SupplierEvidence,
    *,
    owner_approved_spend: bool,
) -> str:
    if not owner_approved_spend:
        raise FulfilmentError("supplier spend requires owner approval")
    if not (
        evidence.identity_verified
        and evidence.product_available
        and evidence.uk_delivery
        and evidence.supplier_ref
    ):
        raise FulfilmentError("supplier identity, stock, UK delivery, and reference are required")
    if evidence.supplier_cost_cents < 0 or evidence.delivery_cost_cents < 0 or evidence.fees_cents < 0:
        raise FulfilmentError("costs cannot be negative")
    with sqlite3.connect(db_path) as conn:
        row = _row(conn, order_id)
        _require(row, "PAYMENT_VERIFIED")
        revenue = conn.execute(
            "SELECT total_cents FROM orders WHERE id = ?",
            (order_id,),
        ).fetchone()[0]
        profit = (
            revenue
            - evidence.fees_cents
            - evidence.supplier_cost_cents
            - evidence.delivery_cost_cents
        )
        if profit <= 0:
            raise FulfilmentError("refusing supplier order: verified economics are a known loss")
        conn.execute(
            """
            UPDATE fulfilment
            SET state = 'SUPPLIER_CONFIRMED', supplier_name = ?, supplier_ref = ?,
                supplier_cost_cents = ?, delivery_cost_cents = ?, fees_cents = ?, updated_at = ?
            WHERE order_id = ?
            """,
            (
                evidence.supplier_name,
                evidence.supplier_ref,
                evidence.supplier_cost_cents,
                evidence.delivery_cost_cents,
                evidence.fees_cents,
                _now(),
                order_id,
            ),
        )
        conn.commit()
    return "SUPPLIER_CONFIRMED"


def record_dispatch(db_path: str, order_id: int, supplier_dispatch_ref: str) -> str:
    if not supplier_dispatch_ref.strip():
        raise FulfilmentError("supplier dispatch reference is required")
    with sqlite3.connect(db_path) as conn:
        row = _row(conn, order_id)
        _require(row, "SUPPLIER_CONFIRMED")
        conn.execute(
            "UPDATE fulfilment SET state = 'DISPATCHED', updated_at = ? WHERE order_id = ?",
            (_now(), order_id),
        )
        conn.commit()
    return "DISPATCHED"


def record_tracking(db_path: str, order_id: int, evidence: TrackingEvidence) -> str:
    if not evidence.tracking_id.strip() or not evidence.carrier.strip():
        raise FulfilmentError("carrier and tracking id are required")
    if evidence.carrier_status not in {"accepted", "in_transit", "delivered"}:
        raise FulfilmentError("carrier has not accepted the tracking id")
    with sqlite3.connect(db_path) as conn:
        row = _row(conn, order_id)
        _require(row, "DISPATCHED")
        conn.execute(
            """
            UPDATE fulfilment
            SET state = 'TRACKING_VERIFIED', tracking_id = ?, carrier = ?, updated_at = ?
            WHERE order_id = ?
            """,
            (evidence.tracking_id, evidence.carrier, _now(), order_id),
        )
        conn.commit()
    return "TRACKING_VERIFIED"


def record_delivery(db_path: str, order_id: int, *, carrier_status: str, delivered_at: str) -> str:
    if carrier_status != "delivered" or not delivered_at.strip():
        raise FulfilmentError("carrier has not reported delivery")
    with sqlite3.connect(db_path) as conn:
        row = _row(conn, order_id)
        _require(row, "TRACKING_VERIFIED")
        conn.execute(
            """
            UPDATE fulfilment
            SET state = 'DELIVERED', delivered_at = ?, updated_at = ?
            WHERE order_id = ?
            """,
            (delivered_at, _now(), order_id),
        )
        conn.execute(
            "UPDATE orders SET delivery_status = 'DELIVERED' WHERE id = ?",
            (order_id,),
        )
        conn.commit()
    return "DELIVERED"


def close_and_reconcile(db_path: str, order_id: int) -> Reconciliation:
    with sqlite3.connect(db_path) as conn:
        row = _row(conn, order_id)
        _require(row, "DELIVERED")
        revenue = conn.execute(
            "SELECT total_cents FROM orders WHERE id = ?",
            (order_id,),
        ).fetchone()[0]
        result = Reconciliation(
            order_id=order_id,
            revenue_cents=revenue,
            fees_cents=row["fees_cents"],
            supplier_cost_cents=row["supplier_cost_cents"],
            delivery_cost_cents=row["delivery_cost_cents"],
            profit_cents=revenue
            - row["fees_cents"]
            - row["supplier_cost_cents"]
            - row["delivery_cost_cents"],
            payment_provider=row["payment_provider"],
            payment_ref=row["payment_ref"],
        )
        conn.execute(
            "UPDATE fulfilment SET state = 'CLOSED', updated_at = ? WHERE order_id = ?",
            (_now(), order_id),
        )
        conn.commit()
    return result
