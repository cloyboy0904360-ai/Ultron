# ULTRON Architecture

## Proposed modular system

ULTRON is organized as independent, testable modules with explicit interfaces:

1. **Order Intake**
   - Accepts customer order requests.
   - Validates required data and item quantities.
2. **Payment Processing**
   - Authorizes and records payments.
   - Rejects invalid tokens and non-positive payment amounts.
3. **Inventory Control**
   - Tracks product stock.
   - Reserves stock only after successful payment authorization.
4. **Delivery Orchestration**
   - Creates delivery records for paid orders.
   - Dispatches shipments with generated tracking identifiers.
5. **Audit and Observability**
   - Preserves transactional records in SQLite.
   - Enables deterministic reconstruction of order lifecycle states.

## Current implementation boundary

The repository currently implements one complete payment-to-delivery pathway in `ultron/pathway.py`:

- Catalog seed
- Payment authorization
- Stock reservation
- Delivery creation
- Delivery dispatch

## Data model (current)

- `products(id, name, price_cents, stock)`
- `orders(id, customer_email, total_cents, payment_status, delivery_status, created_at)`
- `order_items(order_id, product_id, quantity, unit_price_cents)`
- `payments(id, order_id, amount_cents, status, payment_token, created_at)`
- `deliveries(id, order_id, address, status, tracking_id, created_at, dispatched_at)`

## Environment separation

- `development`: fast iteration, local data.
- `staging`: production-like validation before release.
- `production`: controlled, approved deployments only.

Environment config files are stored in `config/environments/` and intentionally exclude secrets.
