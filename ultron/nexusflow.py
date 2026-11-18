"""NexusFlow's signed Stripe ingress and tamper-evident accounting ledger.

This module records verified payment evidence and queues digital fulfilment.
It deliberately does not send customer files, issue refunds, or move money.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
import sqlite3
import time
from pathlib import Path
from typing import Any

ZERO_HASH = "0" * 64
SIGNATURE_TOLERANCE_SECONDS = 300


class LedgerIntegrityError(RuntimeError):
    """Raised when an append-only ledger record no longer matches its hash."""


def initialize_nexusflow_db(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS revenue_ledger (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                checkout_session_id TEXT NOT NULL UNIQUE,
                payment_intent_id TEXT NOT NULL UNIQUE,
                order_id TEXT NOT NULL,
                sku TEXT NOT NULL,
                amount_minor INTEGER NOT NULL CHECK(amount_minor > 0),
                currency TEXT NOT NULL,
                stripe_created INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                entry_hash TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS digital_fulfilments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL UNIQUE,
                checkout_session_id TEXT NOT NULL UNIQUE,
                sku TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('PENDING', 'DELIVERED', 'FAILED')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


def _verify_signature(payload: bytes, signature: str, secret: str, now: int | None = None) -> None:
    if not isinstance(payload, bytes) or not signature or not secret:
        raise ValueError("Stripe signature, payload and endpoint secret are required")
    parts: dict[str, list[str]] = {}
    for item in signature.split(","):
        key, separator, value = item.partition("=")
        if separator:
            parts.setdefault(key, []).append(value)
    try:
        timestamp = int(parts["t"][0])
    except (KeyError, ValueError, IndexError) as exc:
        raise ValueError("invalid Stripe signature timestamp") from exc
    current = int(time.time()) if now is None else now
    if abs(current - timestamp) > SIGNATURE_TOLERANCE_SECONDS:
        raise ValueError("Stripe signature timestamp outside tolerance")
    signed_payload = str(timestamp).encode("ascii") + b"." + payload
    expected = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    if not any(hmac.compare_digest(expected, candidate) for candidate in parts.get("v1", [])):
        raise ValueError("invalid Stripe signature")


def _canonical_entry(record: dict[str, Any]) -> bytes:
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def verify_ledger(db_path: str) -> dict[str, Any]:
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """SELECT sequence,event_id,checkout_session_id,payment_intent_id,order_id,sku,
                      amount_minor,currency,stripe_created,event_type,previous_hash,entry_hash
               FROM revenue_ledger ORDER BY sequence"""
        ).fetchall()
    previous = ZERO_HASH
    for row in rows:
        (sequence, event_id, session_id, intent_id, order_id, sku, amount, currency,
         created, event_type, previous_hash, entry_hash) = row
        record = {
            "sequence": sequence, "event_id": event_id, "checkout_session_id": session_id,
            "payment_intent_id": intent_id, "order_id": order_id, "sku": sku,
            "amount_minor": amount, "currency": currency, "stripe_created": created,
            "event_type": event_type,
        }
        if previous_hash != previous:
            raise LedgerIntegrityError(f"previous hash mismatch at sequence {sequence}")
        expected = hashlib.sha256(previous.encode("ascii") + _canonical_entry(record)).hexdigest()
        if not hmac.compare_digest(expected, entry_hash):
            raise LedgerIntegrityError(f"entry hash mismatch at sequence {sequence}")
        previous = entry_hash
    return {"valid": True, "entries": len(rows), "head_hash": previous}


def process_stripe_webhook(
    db_path: str,
    payload: bytes,
    signature: str,
    endpoint_secret: str,
    *,
    now: int | None = None,
) -> dict[str, str]:
    _verify_signature(payload, signature, endpoint_secret, now=now)
    try:
        event = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid Stripe event JSON") from exc
    if not isinstance(event, dict) or event.get("type") != "checkout.session.completed":
        raise ValueError("unsupported event: only checkout.session.completed is accepted")
    event_id = event.get("id")
    created = event.get("created")
    session = event.get("data", {}).get("object", {})
    metadata = session.get("metadata") or {}
    payment_intent = session.get("payment_intent")
    order_id, sku = metadata.get("order_id"), metadata.get("sku")
    amount, currency = session.get("amount_total"), session.get("currency")
    if session.get("payment_status") != "paid":
        raise ValueError("checkout session is not paid")
    if not isinstance(event_id, str) or not event_id.startswith("evt_"):
        raise ValueError("Stripe event ID is missing or invalid")
    if not isinstance(created, int) or created <= 0:
        raise ValueError("Stripe event creation time is missing or invalid")
    if not isinstance(session.get("id"), str) or not session["id"].startswith("cs_"):
        raise ValueError("Stripe checkout session ID is missing or invalid")
    if not isinstance(payment_intent, str) or not payment_intent.startswith("pi_"):
        raise ValueError("Stripe payment intent is missing or invalid")
    if not isinstance(order_id, str) or not order_id.strip() or not isinstance(sku, str) or not sku.strip():
        raise ValueError("Stripe session metadata must include order_id and sku")
    if type(amount) is not int or amount <= 0:
        raise ValueError("Stripe amount_total must be a positive integer in minor units")
    if not isinstance(currency, str) or not re.fullmatch(r"[a-z]{3}", currency):
        raise ValueError("Stripe currency must be a three-letter lowercase code")

    initialize_nexusflow_db(db_path)
    session_id = session["id"]
    with sqlite3.connect(db_path, timeout=20) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("BEGIN IMMEDIATE")
        duplicate = conn.execute(
            """SELECT 1 FROM revenue_ledger
               WHERE event_id = ? OR checkout_session_id = ? OR payment_intent_id = ?""",
            (event_id, session_id, payment_intent),
        ).fetchone()
        if duplicate:
            conn.commit()
            return {"status": "DUPLICATE", "event_id": event_id, "fulfilment": "UNCHANGED"}
        last = conn.execute(
            "SELECT entry_hash FROM revenue_ledger ORDER BY sequence DESC LIMIT 1"
        ).fetchone()
        previous_hash = last[0] if last else ZERO_HASH
        sequence = conn.execute(
            "SELECT COALESCE(MAX(sequence), 0) + 1 FROM revenue_ledger"
        ).fetchone()[0]
        record = {
            "sequence": sequence, "event_id": event_id, "checkout_session_id": session_id,
            "payment_intent_id": payment_intent, "order_id": order_id.strip(),
            "sku": sku.strip(), "amount_minor": amount, "currency": currency,
            "stripe_created": created, "event_type": event["type"],
        }
        entry_hash = hashlib.sha256(previous_hash.encode("ascii") + _canonical_entry(record)).hexdigest()
        conn.execute(
            """INSERT INTO revenue_ledger
               (sequence,event_id,checkout_session_id,payment_intent_id,order_id,sku,
                amount_minor,currency,stripe_created,event_type,previous_hash,entry_hash)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (sequence,event_id,session_id,payment_intent,order_id.strip(),sku.strip(),
             amount,currency,created,event["type"],previous_hash,entry_hash),
        )
        conn.execute(
            """INSERT INTO digital_fulfilments
               (order_id,checkout_session_id,sku,status) VALUES (?,?,?,'PENDING')""",
            (order_id.strip(),session_id,sku.strip()),
        )
        conn.commit()
    return {"status": "RECORDED", "event_id": event_id, "fulfilment": "PENDING"}
