# ULTRON GitHub Actions Runtime (zero-upfront design)

## Deployment model

Six workers run as six independent GitHub Actions matrix jobs. Triggers are issue opened/labeled/reopened events, a 15-minute scheduled poll, and manual workflow dispatch.

Each job runs one bounded task and exits. This is event-driven/scheduled execution, not a continuously running 24/7 process. GitHub-hosted runners are provisioned only for a job. Public-repository standard runner usage is generally available without a paid server, subject to current account limits and GitHub Actions policy.

## Why this is the £0 starting point

- Uses the existing public GitHub repository and GitHub Actions.
- Uses the automatically provided GITHUB_TOKEN; no extra API key or AI-provider subscription is required.
- Uses GitHub Issues as the durable queue and evidence ledger.
- Uses Python standard library only in the runtime.
- Does not require Make, Stripe, Shopify, supplier, or carrier credentials for safe internal tasks.

No paid AI inference is included. Initial handlers are deterministic, role-scoped operations: plans, code review checklists, draft-only sales replies/listings, fulfilment readiness checks, and margin calculations. They are not general-purpose language-model agents until an approved model provider is connected.

## Task submission format

Create an issue, apply exactly one agent label (for example agent:finance) plus status:ready, and include this block:

```ultron-task
{
  "operation": "calculate_margin",
  "input": {
    "revenue_pence": 900,
    "cost_pence": 300,
    "fees_pence": 50
  }
}
```

| Agent | Operation | Effect |
| --- | --- | --- |
| NOVA | break_down_objective | Produces a bounded execution plan |
| FORGE | code_review_checklist | Produces a code/security review checklist |
| SALES | draft_reply | Produces a draft only; never sends |
| OPS | fulfilment_readiness | Checks evidence flags; never dispatches |
| FINANCE | calculate_margin | Calculates GBP margin using integer pence |
| PIXEL | draft_product_listing | Produces a listing draft; never publishes |

## Queue lifecycle

READY -> RUNNING -> VERIFIED. Missing evidence moves a task to BLOCKED; exceptions move it to FAILED. Workers record a lease, attempt number, result/failure JSON, and timestamps in issue comments. A lease older than 30 minutes with no result is requeued. Each worker processes at most one issue per run.

Each agent has a concurrency group so its own jobs do not overlap. Different agents can execute concurrently. Operations are allowlisted and side-effect-free. GitHub Issues does not provide a transactional lease primitive, so no external payment, order, message, shipment, or irreversible operation is allowed in this first runtime.

## Retry and duplicate controls

- Per-agent Actions concurrency prevents overlapping jobs for the same worker.
- Issue status changes to running before task execution.
- Run ID and attempt marker are recorded before execution.
- Maximum three manual attempts are accepted; after that the task remains failed.
- Crashed runs are eligible for lease recovery after 30 minutes.
- Side-effect-free operations reduce duplicate execution risk.

## Security

- Workflow permissions are contents:read and issues:write only.
- No repository write, deployment, payment, supplier, or customer-message credentials are requested.
- GITHUB_TOKEN is passed only through the Actions secret context.
- Only issues authored by repository owners, collaborators, or members are eligible for execution; this prevents arbitrary public users from injecting queue tasks.
- Do not put customer secrets, payment credentials, or unnecessary personal data in task bodies.
- Evidence is bounded to 6,000 characters.
- Review any new operation before adding it to the allowlist.

## Operational limits and next gate

- Scheduled runs can be delayed by GitHub; the system is not real-time.
- Public runner availability is subject to GitHub Actions policy and fair-use limits.
- The six jobs are independent worker executions, but task intelligence is deterministic rather than LLM-powered.
- GitHub Actions logs and issue comments provide evidence; alerting and long-term metrics are not yet configured.
- Production commerce actions remain blocked by the production release gate.
