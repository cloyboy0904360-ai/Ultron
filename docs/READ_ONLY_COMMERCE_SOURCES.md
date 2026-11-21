# Read-only Commerce Research Sources

## What this stage adds

ULTRON now has a read-only source adapter layer for explicitly configured:

- Product listing RSS/Atom feeds.
- Demand-signal RSS/Atom feeds.
- Supplier JSON feeds with structured offer fields.

The adapters retain source name, source URL, collection timestamp, observed title, summary and any supplier-provided stock/cost/delivery/returns evidence. Each source is handled independently so one unavailable feed does not erase results from other feeds.

## Important: no source is enabled by default

`config/commerce_sources.json` intentionally contains an empty `sources` array. This avoids inventing supplier endpoints, scraping unknown websites, or representing a test fixture as live stock. The manual GitHub Actions workflow can be run safely with this empty configuration and produces a report showing zero configured sources.

A source can only be enabled after its real endpoint and allowed hostnames are known and reviewed. Each source entry must specify:

- `name`: human-readable source name.
- `kind`: `product_rss`, `demand_rss`, or `supplier_json`.
- `url`: HTTPS feed endpoint.
- `allowed_hosts`: exact hostnames permitted for both the feed and returned record URLs.
- Optional `enabled` and `max_records`.

Example configuration shape (illustrative only; not an active source):

```json
{
  "version": 1,
  "sources": [
    {
      "name": "Approved supplier feed",
      "kind": "supplier_json",
      "url": "https://supplier.example/api/offers.json",
      "allowed_hosts": ["supplier.example"],
      "enabled": true,
      "max_records": 25
    }
  ]
}
```

## Supplier JSON feed contract

A supplier feed returns JSON with an `offers` array. Each offer may include:

- `title`, `url`, `price_pence`
- `stock_status`, `stock_checked_at`
- `unit_cost_pence`, `shipping_cost_pence`
- `ships_to_uk`, `delivery_days_min`, `delivery_days_max`
- `returns_policy_url`, `evidence_excerpt`, `evidence_checked_at`

The adapter preserves these as supplier-provided claims. It does not certify the supplier, prove inventory, or convert a feed claim into an independent verification. The next step is to map the preserved raw evidence into the existing `SupplierOffer` verifier and require all freshness, stock, UK delivery, cost and returns checks to pass.

## Network and safety limits

- HTTPS only.
- Exact configured hostname allowlist.
- Redirects rejected.
- GET requests only.
- 12-second request timeout.
- 1 MB maximum response.
- Up to 100 records per configured source.
- No arbitrary URL supplied by a feed can trigger a second network request.
- No login, account creation, purchase, publication, customer messaging, or payment operation.

Product and demand RSS entries are research leads only. RSS presence or keyword frequency is not verified sales demand. Missing prices remain null; they are never guessed.

## Run and test

Run locally or in GitHub Actions:

`python scripts/run_commerce_sources.py --config config/commerce_sources.json --output commerce_source_report.json`

The manual workflow is `.github/workflows/commerce-source-research.yml`. It has read-only repository permissions and uploads the report as a 14-day artifact.

Tests use deterministic in-memory fixtures and do not make network calls. A passing test proves parser and safety behaviour, not the availability or accuracy of a live supplier source.
