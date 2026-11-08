# ULTRON Six-Agent Operating Network

ULTRON has six required operational agent roles. Each role has a separate responsibility boundary, task queue, status, and evidence trail. The central controller owns scheduling, authentication, policy enforcement, and audit records.

## Six operational agents

| Agent | Independent responsibility | Queue filter | Authority boundary |
| --- | --- | --- | --- |
| NOVA | Prioritization, orchestration, dashboard and dependency management | `label:agent:nova` | May sequence and assign work; cannot approve spending or override policy |
| FORGE | Core code, integrations, tests, CI and deployment engineering | `label:agent:forge` | May propose code changes; production promotion requires approval and passing checks |
| SALES | Lead qualification, offer preparation, sales pipeline and conversion analysis | `label:agent:sales` | Drafts customer communications; no sending, commitments or claims of sale without authorization/evidence |
| OPS | Order processing, inventory checks, supplier and fulfilment coordination | `label:agent:ops` | No dispatch or stock commitment without verified payment and supplier/carrier evidence |
| FINANCE | Payment reconciliation, expense controls, margin and ledger reporting | `label:agent:finance` | Read/reconcile only by default; no transfers, refunds or spending without specific approval |
| PIXEL | Product research, listings, customer-facing assets, marketing and SEO | `label:agent:pixel` | Can prepare drafts; publication, paid promotion and external changes require approval |

## Cross-cutting system controls

Security, compliance, approvals, credential handling, and audit enforcement are core-controller responsibilities, not a seventh autonomous agent. Search-engine and domain tasks are routed through PIXEL; NOVA owns their priority and dependency tracking. Repository security-setting review is assigned to FORGE, but applying protection changes remains approval-gated.

## Queue and evidence protocol

- Queue source: GitHub issues in this repository.
- Assignment: `agent:<name>` labels.
- Status: `status:ready`, `status:running`, `status:verified`, `status:blocked`, `status:awaiting-approval`, `status:failed`, `status:paused`.
- Every task must link commits, pull requests, workflow runs, test results, or external evidence.
- Each agent must have an independent lease/heartbeat and must not claim another agent's task.
- A task is VERIFIED only after independent evidence confirms its outcome.

## Current implementation status

<badge>ACTIVE — LIMITED SMOKE TEST VERIFIED</badge>

The six-worker GitHub Actions runtime was merged to `main` in PR #27. The first controlled NOVA task, issue #28, completed successfully: the worker acquired a lease, executed the deterministic objective-breakdown handler, posted structured evidence, and changed the issue to `status:verified`. This verifies one NOVA execution path only; the other five agent roles and full operational acceptance remain to be tested.

The handlers are deterministic and side-effect-free, not LLM-powered. The runtime is scheduled/event-driven, not a continuously resident 24/7 service. No agent should be represented as a general-purpose AI agent or as independently verified until its own tests and acceptance evidence exist.

## Access and financial boundaries

- Least privilege only.
- No credentials or personal data in source code, logs, docs, or CI output.
- No spend, irreversible financial commitments, customer messages, or destructive operations without explicit approval.
- No simulated payment, shipment, sale, or delivery may be represented as real.
- Production promotion requires passing CI/security checks, configured secrets, a tested payment provider, and a tested fulfilment provider.
