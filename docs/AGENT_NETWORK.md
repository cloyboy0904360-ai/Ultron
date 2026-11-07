# ULTRON Agent Network

This repository uses a **task-queue model** with GitHub issues as the execution ledger.

## Operational model

- Queue source: `Ultron` issue tracker.
- Assignment mechanism: `agent:*` labels.
- Status mechanism: `status:*` labels (`ready`, `running`, `verified`, `blocked`, `awaiting-approval`, `failed`, `paused`).
- Evidence requirement: each task must link commits, PRs, workflow runs, or external proof.

## Agent responsibilities and queues

| Agent | Responsibility | Queue filter | Current queue |
| --- | --- | --- | --- |
| NOVA | Central prioritization, dashboard maintenance, sequencing | `label:agent:nova` | #12 |
| FORGE | Repository code, integrations, tests, deployments | `label:agent:forge` | #13 |
| SALES | Revenue offers, acquisition, conversion execution | `label:agent:sales` | #14 |
| OPS | Workflow execution, fulfilment reliability | `label:agent:ops` | #15 |
| FINANCE | Revenue/expense reconciliation and evidence | `label:agent:finance` | #16 |
| PIXEL | Customer-facing pages/materials/listings | `label:agent:pixel` | #17 |
| SEO | Domain/indexing/backlink monitoring | `label:agent:seo` | #18 |
| GUARDIAN | Security/compliance controls and approvals | `label:agent:guardian` | #19 |

## Access boundaries

- Least privilege only.
- No credentials are stored in this repository.
- No spend, irreversible financial commitments, or destructive data operations without explicit approval.
- Branch-protection and security-analysis settings currently require permissions not available to this session.

## Tooling note

Direct Copilot Automation Group provisioning tools were not available in this session.  
Execution is therefore implemented with GitHub issues + labels as the live, auditable queue system.
