from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime


def _utc_now() -> str:
    return datetime.now(tz=UTC).isoformat()


@dataclass(frozen=True)
class OrderResult:
    order_id: int
    payment_status: str
    delivery_status: str
    total_cents: int


def initialize_db(db_path: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                price_cents INTEGER NOT NULL CHECK(price_cents > 0),
                stock INTEGER NOT NULL CHECK(stock >= 0)
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                customer_email TEXT NOT NULL,
                total_cents INTEGER NOT NULL CHECK(total_cents > 0),
                payment_status TEXT NOT NULL,
                delivery_status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY,
                order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                product_id INTEGER NOT NULL REFERENCES products(id),
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                unit_price_cents INTEGER NOT NULL CHECK(unit_price_cents > 0)
            );

            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY,
                order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
                status TEXT NOT NULL,
                payment_token TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS deliveries (
                id INTEGER PRIMARY KEY,
                order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                address TEXT NOT NULL,
                status TEXT NOT NULL,
                tracking_id TEXT,
                created_at TEXT NOT NULL,
                dispatched_at TEXT
            );
            """
        )


def seed_catalog(db_path: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        products = [
            ("ULTRON Sensor", 2499, 50),
            ("ULTRON Hub", 15999, 20),
            ("ULTRON Relay", 4999, 40),
        ]
        conn.executemany(
            """
            INSERT INTO products(name, price_cents, stock)
            SELECT ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM products WHERE name = ?
            )
            """,
            [(name, price, stock, name) for (name, price, stock) in products],
        )


def _payment_authorized(payment_token: str, amount_cents: int) -> bool:
    return payment_token.startswith("tok_") and amount_cents > 0


def create_order(
    db_path: str,
    *,
    customer_email: str,
    product_id: int,
    quantity: int,
    payment_token: str,
    delivery_address: str,
) -> OrderResult:
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    if "@" not in customer_email:
        raise ValueError("customer_email is invalid")
    if not delivery_address.strip():
        raise ValueError("delivery_address is required")

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("BEGIN")

        product = conn.execute(
            "SELECT name, price_cents, stock FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        if product is None:
            raise ValueError("product not found")
        _, unit_price_cents, stock = product
        if stock < quantity:
            raise ValueError("insufficient stock")

        total_cents = unit_price_cents * quantity
        payment_status = "AUTHORIZED" if _payment_authorized(payment_token, total_cents) else "DECLINED"
        delivery_status = "READY" if payment_status == "AUTHORIZED" else "CANCELLED"

        order_cursor = conn.execute(
            """
            INSERT INTO orders(customer_email, total_cents, payment_status, delivery_status, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (customer_email, total_cents, payment_status, delivery_status, _utc_now()),
        )
        order_id = int(order_cursor.lastrowid)

        conn.execute(
            """
            INSERT INTO order_items(order_id, product_id, quantity, unit_price_cents)
            VALUES (?, ?, ?, ?)
            """,
            (order_id, product_id, quantity, unit_price_cents),
        )

        conn.execute(
            """
            INSERT INTO payments(order_id, amount_cents, status, payment_token, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (order_id, total_cents, payment_status, payment_token, _utc_now()),
        )

        if payment_status == "AUTHORIZED":
            conn.execute(
                "UPDATE products SET stock = stock - ? WHERE id = ?",
                (quantity, product_id),
            )

        conn.execute(
            """
            INSERT INTO deliveries(order_id, address, status, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (order_id, delivery_address, delivery_status, _utc_now()),
        )

        conn.commit()
        return OrderResult(
            order_id=order_id,
            payment_status=payment_status,
            delivery_status=delivery_status,
            total_cents=total_cents,
        )


def dispatch_delivery(db_path: str, order_id: int) -> str:
    tracking_id = f"ULTRON-{order_id}-{int(datetime.now(tz=UTC).timestamp())}"
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        row = conn.execute(
            "SELECT status FROM deliveries WHERE order_id = ?",
            (order_id,),
        ).fetchone()
        if row is None:
            raise ValueError("delivery not found")
        current_status = row[0]
        if current_status != "READY":
            raise ValueError(f"delivery not dispatchable from status={current_status}")
        conn.execute(
            """
            UPDATE deliveries
            SET status = 'DISPATCHED', tracking_id = ?, dispatched_at = ?
            WHERE order_id = ?
            """,
            (tracking_id, _utc_now(), order_id),
        )
        conn.execute(
            "UPDATE orders SET delivery_status = 'DISPATCHED' WHERE id = ?",
            (order_id,),
        )
        conn.commit()
    return tracking_id
