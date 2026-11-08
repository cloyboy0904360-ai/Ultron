# ULTRON Core Production Release Gate

## Release decision

**Current decision: BLOCKED — DO NOT DEPLOY TO PRODUCTION.**

The repository is a tested foundation, not a live commerce operating system. Production activation is prohibited until every gate below is independently evidenced.

## Mandatory release gates

| Gate | Required evidence | Current status |
| --- | --- | --- |
| Core controller | Secure runtime, validated configuration, task lifecycle, crash recovery and health checks | BLOCKED — controller runtime not implemented |
| Six independent agents | Separate queues, worker identities, permissions, leases, retries and audit records | PARTIAL — all six role smoke tasks executed; five completed and OPS correctly blocked without dispatch; full acceptance pending |
| AI execution adapters | Approved provider, credentials in secret storage, rate limits and failure handling | BLOCKED — provider not connected |
| Payment | Provider adapter, signed webhook verification, idempotency, amount/currency/order matching and settlement reconciliation | BLOCKED — no live provider adapter |
| Fulfilment | Supplier/carrier adapter, verified dispatch response and delivery confirmation | BLOCKED — no live provider adapter |
| Inventory | Authoritative supplier stock, price and availability checks; reservation and rollback | BLOCKED — seed catalogue only |
| Customer acquisition | Approved channel, compliant consent and message controls | BLOCKED — no live channel |
| Security | Secret storage, least privilege, branch protection, dependency/secret scanning and incident response | PARTIAL — repository controls exist; account-level settings need verification |
| Operations | Monitoring, alerting, backups, restore test, log retention and rollback | BLOCKED — not production-proven |
| Financial controls | No-spend default, explicit approvals, reconciled ledger and evidence capture | PARTIAL — policy documented; live ledger integration absent |

## Known code safety constraints

- The predictable `ultron-test-token-*` payment token is permitted only outside `ULTRON_ENV=production`.
- Production dispatch is blocked unless a carrier adapter is explicitly supplied.
- A locally generated test tracking identifier is prefixed `TEST-ULTRON-` and is not evidence of a real shipment.
- A configured adapter still needs a real provider integration test; a callback alone is not proof of carrier acceptance.
- No payment, dispatch, sale, or delivery is VERIFIED from a local test.

## Six-agent acceptance test

Before launch, prove all six workers can independently:
1. Acquire only their own eligible tasks using an atomic lease.
2. Record a heartbeat and bounded execution attempt.
3. Recover an expired lease without duplicating side effects.
4. Enforce role-specific permissions and approval gates.
5. Persist structured logs and evidence references.
6. Stop safely on missing credentials, provider errors, policy violations, or uncertain outcomes.

## Deployment sequence

1. Complete controller and agent runtime.
2. Pass unit, integration, concurrency, security, and recovery tests.
3. Configure development and staging credentials without exposing them in source.
4. Connect one payment provider and one fulfilment provider in test mode.
5. Verify signed webhooks, idempotency, stock reservation, refund/error handling and reconciliation.
6. Complete staging end-to-end test with no real customer impact.
7. Obtain explicit approval for the specific production account, scope and release.
8. Deploy with monitoring, rollback and evidence capture enabled.

## Operating rule

`CORRECT -> COMPLETE -> CONNECTED -> WORKING -> LIVE -> MEASURED -> EVIDENCE CAPTURED`

Any missing gate remains BLOCKED. Do not label the core or agents LIVE based on documentation, mocks, issue labels, or successful unit tests alone.
