# Fulfilment lifecycle

Code: `ultron/fulfilment.py`. This module stores evidence. It does not call Stripe, a supplier, or a carrier, and it does not spend money.

Allowed order states, in order:

`ORDER_RECEIVED` → `PAYMENT_VERIFIED` → `SUPPLIER_CONFIRMED` → `DISPATCHED` → `TRACKING_VERIFIED` → `DELIVERED` → `CLOSED`

Refusals:

- A `ultron-test-token-*` authorization cannot verify payment. The provider name `test` is rejected.
- Payment amount must match the order, and `verified_with_provider` must be true with status `succeeded`.
- Supplier confirmation requires identity, availability, UK delivery, a supplier reference, and owner approval. Profit at or below zero is a known loss and is refused.
- Tracking must come from a named carrier that has accepted the id. `pathway.dispatch_delivery` generates a local id and is not this proof.
- Reconciliation runs only from `DELIVERED` and returns stored cents. It is not evidence that funds settled in a bank account.

No live order has passed this chain. There is no connected payment provider, supplier, or carrier in this session.
