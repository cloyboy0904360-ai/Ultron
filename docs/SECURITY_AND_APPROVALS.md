# Security and Approvals

- Live payments are verified with the provider (`StripeVerifier` fetches the PaymentIntent and checks `succeeded`, `amount_received` and currency). A webhook alone is never proof of settlement.
- `ULTRON_PAYMENT_MODE=live` requires `STRIPE_API_KEY`; it fails closed without it and never accepts `ultron-test-token-*`. Test tokens work only in `test`, `development` and `staging`.
- Orders accept an `idempotency_key` (unique index) so retries cannot create duplicate orders or double-reserve stock.
- Secrets live only in environment variables or GitHub environment secrets.
- Additional spend is £0. These need explicit owner approval before any agent acts: subscriptions, ads, purchased stock or links, transfers, contracts, supplier orders, outreach, publishing, deleting assets.
- All changes go through feature branches and PRs (see `.github/copilot-instructions.md`).
