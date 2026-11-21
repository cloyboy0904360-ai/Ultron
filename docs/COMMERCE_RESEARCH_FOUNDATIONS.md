# ULTRON Commerce Research Foundations

## Scope

The commerce research foundation supplies evidence contracts and deterministic checks for three steps:

1. Product research records retain a source URL, observed price, demand-evidence URLs and the time evidence was checked.
2. Supplier offers retain supplier identity, product/evidence URLs, stock state, stock-check time, unit and shipping costs, UK delivery support, delivery estimate and returns-policy URL.
3. Profitability is calculated in integer GBP pence using selling price, supplier cost, supplier delivery, marketplace fee, payment fee and other unavoidable costs.

This is a foundation for collecting and assessing evidence. It is not a general web crawler, supplier API integration, live inventory feed or guarantee that a supplier's claims are true.

## Agent operations

- OPS: `verify_supplier_offer` evaluates a raw supplier offer. Missing, unknown or stale stock, costs, UK delivery, delivery estimate, returns policy or source evidence produce `BLOCKED`.
- FINANCE: `calculate_product_profitability` calculates gross profit and net contribution. Any unknown cost produces `UNVERIFIED`; a net contribution margin below the configured threshold produces `REJECTED`.
- PIXEL: `assess_product_candidate` independently re-runs supplier and profitability checks from the raw task input and combines them with dated demand evidence. A positive result is `READY_FOR_LISTING_REVIEW`, not publication approval.

The legacy `calculate_margin` and `draft_product_listing` operations remain available. Product listing output remains draft-only.

## Freshness and evidence rules

- Supplier stock and supplier-page evidence default to a maximum age of 24 hours.
- Product demand evidence defaults to a maximum age of 30 days.
- All evidence URLs must use HTTPS.
- All money values are integer pence. Floats and negative values are rejected.
- Unknown costs are never silently treated as zero.
- Unknown stock or delivery facts are never treated as available.
- Evidence timestamps must include a timezone.
- A task payload records what was supplied and checked; it does not independently validate a supplier's legal identity, page authenticity, stock feed, or contractual terms. Human/source verification remains required before relying on an offer.

## Safety boundary

These operations are side-effect-free. They do not:

- publish or revise marketplace listings;
- create store inventory or reserve supplier stock;
- place supplier orders or pay suppliers;
- send customer messages or advertising;
- change account, banking, payout or payment settings.

`publication_allowed` is always false in the assessment result. `READY_FOR_LISTING_REVIEW` means the evidence passed these deterministic checks and may proceed to a separate human-reviewed listing stage. It does not mean that ULTRON may publish.

## Test coverage

`tests/test_commerce_research.py` covers complete supplier evidence, unknown and stale stock, HTTPS enforcement, full-cost margin calculation, unknown fees, below-threshold margins, and stale demand evidence.

`tests/test_agents.py` covers agent allowlists, OPS supplier verification, FINANCE profitability, PIXEL evidence re-checking, and the rule that product assessment never authorises publication.
