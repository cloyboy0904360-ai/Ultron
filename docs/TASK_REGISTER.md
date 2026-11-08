# ULTRON Master Task Register

## Mandatory status system

- `READY`
- `RUNNING`
- `VERIFIED`
- `BLOCKED`
- `AWAITING APPROVAL`
- `FAILED`
- `PAUSED`

## Completion gates

Every task follows:

`CORRECT -> COMPLETE -> CONNECTED -> WORKING -> LIVE -> MEASURED -> EVIDENCE CAPTURED`

## Six-agent operational queue

| Task | Agent / owner | Status | Evidence target | Tracker |
| --- | --- | --- | --- | --- |
| Maintain master dashboard, priorities and dependency sequencing | NOVA | RUNNING | Dashboard updates tied to run/PR evidence | #12 |
| Build secure core, integrations, tests and deployment controls | FORGE | BLOCKED | Passing tests, provider adapters, release evidence | #13 |
| Close first paid transaction through an approved channel | SALES | BLOCKED | Settled provider payment plus customer/order evidence | #14 |
| Validate customer-to-delivery workflow and supplier/carrier operations | OPS | READY | Provider acceptance, dispatch and delivery evidence | #15 |
| Build reconciled financial ledger and transaction controls | FINANCE | READY | Reconciled ledger with traceable provider references | #16 |
| Prepare product research, customer-facing assets, listings and SEO | PIXEL | READY | Approved assets connected to a verified fulfilment path | #17, #18 |

## Core-controller security responsibilities

Security, compliance, approvals, credential handling, and policy enforcement are mandatory core-controller controls, not a separate autonomous agent. Guardian work previously tracked under #19 remains a core release dependency and requires explicit evidence before production.

## Current verified execution evidence

1. Closed duplicate PR: #7.
2. Merged repository hardening and initial pathway PR: #8.
3. Created agent/status labels and issue-based queues: #12-#19.
4. Production-safety patch is under review in PR #26; it is not merged or deployed.

## Runtime truth

The six roles currently have documented responsibilities and issue queues. They are **not yet six independent autonomous workers**. Worker processes, model/provider adapters, leases, heartbeats, retries, and continuous monitoring remain BLOCKED. See `docs/CORE_RELEASE_GATE.md`.
