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

**Status: NOT LIVE**

The six-worker runtime is implemented in PR #27, which is ready for review against `main` using GitHub Actions matrix jobs, GitHub Issues queues, per-agent concurrency, leases, stale-lease recovery, bounded attempts, and structured evidence/failure comments. It is **not active on the default branch yet** ; CI, automated tests and security scans passed on the PR head, while the controlled live-task acceptance test remains pending. Initial handlers are deterministic and side-effect-free, not LLM-powered. No agent should be represented as live until PR #27 is merged and the workflow is exercised against controlled tasks.

## Access and financial boundaries

- Least privilege only.
- No credentials or personal data in source code, logs, docs, or CI output.
- No spend, irreversible financial commitments, customer messages, or destructive operations without explicit approval.
- No simulated payment, shipment, sale, or delivery may be represented as real.
- Production promotion requires passing CI/security checks, configured secrets, a tested payment provider, and a tested fulfilment provider.
