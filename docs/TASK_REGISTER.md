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
| Build reconciled financial ledger and transaction controls | FINANCE | BLOCKED — verified transaction source data required | Reconciled ledger with traceable provider references | #16 |
| Prepare product research, customer-facing assets, listings and SEO | PIXEL | BLOCKED — offer details and registrar/search-console access required | Approved assets connected to a verified fulfilment path | #17, #18 |

## Core-controller security responsibilities

Security, compliance, approvals, credential handling, and policy enforcement are mandatory core-controller controls, not a separate autonomous agent. FORGE owns the technical review in issue #19; applying repository protection changes remains AWAITING APPROVAL.

## Current verified execution evidence

1. Closed duplicate PR: #7.
2. Merged repository hardening and initial pathway PR: #8.
3. Created agent/status labels and issue-based queues: #12-#19.
4. Production-safety baseline merged to `main` in PR #26; this is a code change, not a production deployment.
5. Six-agent GitHub Actions runtime merged to `main` in PR #27; CI, automated tests, dependency audit and Gitleaks passed on the merged PR head.
6. Controlled smoke tasks #28-#33 exercised all six workers: NOVA, FORGE, SALES, FINANCE and PIXEL completed with structured evidence; OPS returned BLOCKED as expected because required fulfilment evidence was absent, with `dispatch_performed: false`.

## Runtime truth

The six role-scoped worker processes, GitHub Issues queue integration, concurrency controls, lease recovery and evidence reporting are merged to `main`. All six role handlers have a controlled smoke-test result in issues #28-#33. Five completed; OPS correctly failed closed as BLOCKED with no dispatch. Scheduled recurrence, stale-lease recovery in the live workflow, concurrency under contention, bounded retries, and the complete acceptance matrix remain unverified. Task handlers are deterministic and side-effect-free; LLM provider integration and continuous always-on hosting remain BLOCKED. See `docs/GITHUB_ACTIONS_RUNTIME.md` and `docs/CORE_RELEASE_GATE.md`.
