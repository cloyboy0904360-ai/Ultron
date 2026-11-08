"""Payment verification. Fails closed: live mode never accepts test tokens."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Protocol

STRIPE_API = "https://api.stripe.com/v1/payment_intents/"


class PaymentVerificationError(RuntimeError):
    pass


class PaymentVerifier(Protocol):
    def verify(self, payment_ref: str, amount_cents: int, currency: str) -> bool: ...


class TestTokenVerifier:
    """Deterministic verifier for development/staging tests only."""

    __test__ = False

    def verify(self, payment_ref: str, amount_cents: int, currency: str) -> bool:
        return payment_ref.startswith("ultron-test-token-") and amount_cents > 0


def _default_fetch(url: str, api_key: str) -> dict:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as exc:
        raise PaymentVerificationError(f"payment provider unreachable: {exc.reason}") from exc


class StripeVerifier:
    """Checks the PaymentIntent with Stripe itself; a webhook alone is never proof of payment."""

    def __init__(self, api_key: str, fetch: Callable[[str, str], dict] = _default_fetch):
        if not api_key:
            raise PaymentVerificationError("STRIPE_API_KEY is required for live payments")
        self._key = api_key
        self._fetch = fetch

    def verify(self, payment_ref: str, amount_cents: int, currency: str) -> bool:
        if not payment_ref.startswith("pi_"):
            return False
        intent = self._fetch(STRIPE_API + payment_ref, self._key)
        return (
            intent.get("status") == "succeeded"
            and intent.get("amount_received") == amount_cents
            and str(intent.get("currency", "")).lower() == currency.lower()
        )


def get_verifier(mode: str | None = None) -> PaymentVerifier:
    mode = (mode or os.environ.get("ULTRON_PAYMENT_MODE", "test")).lower()
    if mode == "live":
        return StripeVerifier(os.environ.get("STRIPE_API_KEY", ""))
    if mode in ("test", "development", "staging"):
        return TestTokenVerifier()
    raise PaymentVerificationError(f"unknown payment mode: {mode}")
