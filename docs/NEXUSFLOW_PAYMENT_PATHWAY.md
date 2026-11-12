# NexusFlow payment-to-fulfilment pathway

## Current implementation status

The code in `ultron/nexusflow.py` is a source-level webhook processor and evidence ledger. It is not a deployed HTTP endpoint and it is not connected to the live Stripe account. Stripe currently reports zero webhook endpoints. Do not configure a production endpoint to this module until a hosting route and secret are installed and verified.

## Accepted event contract

The processor accepts only a Stripe-signed `checkout.session.completed` event whose Checkout Session has `payment_status=paid`. The session metadata must contain:

- `order_id`: stable ULTRON order reference
- `sku`: stable product identifier

The session must also contain a Stripe Checkout Session ID, PaymentIntent ID, positive `amount_total` in minor units and three-letter lowercase currency.

The processor verifies the `Stripe-Signature` HMAC using the endpoint secret, enforces a 300-second timestamp tolerance, and rejects malformed, unpaid, unsupported or unverifiable events.

## Idempotency and accounting evidence

The SQLite `revenue_ledger` stores one row per unique Stripe event, Checkout Session and PaymentIntent. It stores integer minor units, currency, order and SKU references, Stripe event time, the previous hash and a SHA-256 entry hash. Replayed identifiers do not create another ledger or fulfilment row.

`verify_ledger(db_path)` recomputes the complete chain and raises `LedgerIntegrityError` on a modified row or broken predecessor link. This is tamper-evident local storage, not an externally anchored immutable ledger; protect the database with backups and access controls before production.

**Storage constraint:** SQLite is suitable for local testing or a single persistent host volume. It is not a production persistence solution on a serverless/ephemeral filesystem such as a default Vercel function runtime. Production requires an already-approved durable database with transactional writes and backups. Do not substitute a paid database or silently use ephemeral disk.

## Fulfilment boundary

A verified paid event creates one `digital_fulfilments` row in `PENDING`. It does not send a download, email a customer, provision access or mark a delivery complete. A separately authenticated fulfilment worker must verify the order-to-SKU mapping, locate the actual approved digital asset, deliver it through an approved channel, and record the provider/customer delivery evidence before changing the state to `DELIVERED`.

Physical goods require separate supplier stock, price, delivery, address and human approval evidence. This webhook must never dispatch physical goods.

## Required deployment work — not yet completed

1. Select an approved hosting route for this repository. The connected Vercel project currently found is `north-mind-audit`, not a NexusFlow deployment.
2. Select a zero-additional-cost durable database only if one is already available and approved; otherwise production persistence remains BLOCKED.
3. Add a thin HTTP adapter that passes the exact raw request bytes and `Stripe-Signature` header to `process_stripe_webhook`; never parse and re-serialize the payload before signature verification.
4. Store `STRIPE_WEBHOOK_SECRET` and the database connection details in the hosting environment, not in source, issues or logs.
5. Configure the Stripe endpoint for `checkout.session.completed` only after the deployed URL has been tested in Stripe test mode.
6. Verify the endpoint receives a signed test event, returns a successful response, records one pending fulfilment and safely handles a replay.
7. Before live use, reconcile a real Stripe PaymentIntent and balance transaction; webhook payment status alone is not proof that a payout has settled in the bank.

## Explicitly disabled

No charge creation, refund, invoice, payment-link creation, customer outreach, file delivery, supplier purchase, carrier dispatch, money movement, secret creation, production deployment or paid service is performed by this module.
