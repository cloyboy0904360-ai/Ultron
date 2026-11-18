# ULTRON Revenue-First Recovery Implementation Plan

> **For agentic workers:** Use the host's available task-by-task implementation workflow. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish the fastest evidence-backed, zero-upfront route to a first legitimate customer payment while repairing the minimum runtime controls required to operate safely.

**Architecture:** Revenue research and offer validation run first, in parallel with a narrow reliability repair. The six existing role-scoped workers remain draft/research-only until their controls are independently tested. A commercial pathway progresses from lead evidence to offer, approval, payment, fulfilment and reconciliation; no simulated event is treated as revenue.

**Tech Stack:** Python 3.12, pytest, Ruff, GitHub Issues, GitHub Actions, GitHub API, existing ULTRON modules.

## Global Constraints

- £0 upfront. No paid subscriptions, credits, advertising, stock purchases, loans, transfers or financial commitments without specific approval.
- No customer contact, public listing, publication, payment processing, order placement, stock reservation or dispatch without the specific approval required for that action.
- No secrets in source, issues, logs or documentation. No new service connection or credential creation without explicit approval.
- No merge to main, production deployment, repository-setting change or branch-protection change as part of this plan.
- No invented demand, stock, supplier terms, asset ownership, valuation, sale, settlement, shipment or profit. Unknown values remain NOT VERIFIED.
- GitHub Actions is scheduled/event-driven and is not represented as continuous 24/7 operation.
- Preserve fail-closed behaviour whenever evidence is absent, conflicting, stale or unverifiable.

---

## Stage 0 — Revenue evidence and first-offer selection

### Task 0.1: Establish a ranked opportunity register

**Files:**
- Create: `docs/REVENUE_OPPORTUNITY_REGISTER.md`
- Reference: `docs/ASSET_AUDIT.md`
- Reference: `docs/TASK_REGISTER.md`

**Interfaces:**
- Consumes: documented business/asset candidates, verified public market evidence, and user-authorized account access.
- Produces: one ranked opportunity with evidence links, customer segment, deliverable, price basis, zero-upfront delivery method, variable costs, fees, expected contribution, risks, and next proof required.

- [ ] Record only opportunities supported by evidence. Candidate categories: fixed-scope digital services, digital products, marketplace products with verified supplier fulfilment, affiliate referrals, and monetisation of owned assets/domains.
- [ ] Treat any previously stated price or valuation as a hypothesis until its current offer, ownership, costs and marketability are revalidated.
- [ ] Rank by time-to-cash, net contribution, evidence strength, delivery certainty and compliance risk. Unknown cost or demand prevents READY status.
- [ ] Select exactly one first opportunity only after comparison; retain the others as research candidates.

**Acceptance:** The register contains source links and explicit NOT VERIFIED fields. No opportunity is called READY without demand, price, delivery and cost evidence.

### Task 0.2: Validate one offer before any external launch

**Files:**
- Create: `docs/FIRST_REVENUE_OFFER.md`
- Reference: `ultron/agents.py`

**Interfaces:**
- Consumes: selected opportunity from Task 0.1.
- Produces: a reviewable offer specification with exact audience, problem, deliverables, exclusions, price basis, delivery capacity, refund/consumer obligations, fees, costs and net contribution calculation.

- [ ] Verify that the offer can be delivered using currently accessible tools and existing capability at £0 upfront.
- [ ] Calculate contribution using integer pence and include all known fees/costs; unknown costs remain explicit and block a profitability claim.
- [ ] Draft customer-facing copy only. Do not publish, send, advertise or promise outcomes.
- [ ] Require user approval of the exact offer, price, channel and wording before any customer-facing action.

**Acceptance:** A complete offer specification exists and has passed a human review. No contact or publication occurs automatically.

---

## Stage 1 — Minimum reliability repair required for revenue work

### Task 1.1: Unexpected worker exceptions produce failure evidence

**Files:**
- Modify: `ultron/worker.py`
- Test: `tests/test_worker.py`

**Interfaces:**
- Consumes: `execute_task(agent, operation, task_input)`, `GitHubQueue.add_comment`, and `GitHubQueue.set_status`.
- Produces: structured FAILED result for any ordinary unexpected exception, plus a non-zero worker exit when execution or failure reporting cannot be completed.

- [ ] Add a regression test where the allowlisted handler raises `RuntimeError`; assert one failure report, `error_type`, bounded error text, and issue status `failed`.
- [ ] Verify the test fails because the exception escapes the current narrow exception tuple.
- [ ] Catch `Exception` around task execution, but do not catch process-control exceptions derived directly from `BaseException`.
- [ ] Attempt to write structured failure evidence and set the issue to failed. If either reporting action fails, emit a concise machine-readable stderr/stdout failure and return a failed process result; never mark the task verified.
- [ ] Preserve the original exception classification and run/attempt identifiers in the report.

**Acceptance:** Regression and existing worker tests pass; failure-reporting failure remains fail-closed. The observed red and green CI run links are recorded in the PR.

### Task 1.2: Complete pagination for queue and evidence reads

**Files:**
- Modify: `ultron/github_queue.py`
- Test: `tests/test_github_queue.py`
- Test: `tests/test_worker.py`

**Interfaces:**
- Consumes: existing `GitHubQueue._request(method, path, payload=None)`.
- Produces: complete `list_issues(agent, status)` and `comments(issue_number)` collections using page-number pagination.

- [ ] Add tests with more than 100 issue comments and more than 100 eligible issues; assert later pages are included and no duplicates appear.
- [ ] Add a test where a later page fails; the queue must raise `GitHubAPIError` rather than return a silently truncated history.
- [ ] Request pages with `per_page=100&page=N`; stop only when a page contains fewer than 100 records.
- [ ] Keep existing trusted-author and pull-request exclusion on every issue page.
- [ ] Verify retry counting and lease/result correlation use the full comment history.

**Acceptance:** Pagination tests and all existing queue tests pass. Any API failure during pagination blocks task claiming.

### Task 1.3: Prove task ownership and bounded retry semantics

**Files:**
- Modify: `ultron/worker.py`
- Modify: `ultron/github_queue.py`
- Modify: `.github/workflows/agent-runtime.yml`
- Test: `tests/test_worker.py`
- Test: `tests/test_github_queue.py`

**Interfaces:**
- Consumes: agent label, status label, run ID, attempt marker and per-agent Actions concurrency group.
- Produces: a single eligible claim per agent run, bounded attempt accounting, and auditable recovery state.

- [ ] Add tests for attempts 1, 2 and 3 being eligible and attempt 4 being rejected, including history spanning multiple comment pages.
- [ ] Add tests proving one agent cannot claim another agent's issue and two agent workers do not process the same labeled task.
- [ ] Preserve the existing per-agent concurrency groups; document their scope and limitations.
- [ ] Treat GitHub issue label updates as non-transactional. Do not claim database-grade atomic locking from a label change. Use the existing single-agent workflow concurrency boundary and a claim marker; detect conflicting claim evidence and stop safely.
- [ ] Test stale lease with matching result (must not requeue), stale lease without result (eligible for recovery), malformed lease (must not authorize execution), and API read failure (must not claim).
- [ ] Keep all agent operations side-effect-free until a separately reviewed provider adapter and explicit approval exist.

**Acceptance:** Contention and retry tests pass. Any remaining non-atomic claim limitation is documented as NOT VERIFIED, not described as solved.

### Task 1.4: Prove authorization and fail-closed commercial boundaries

**Files:**
- Modify: `ultron/agents.py`
- Modify: `ultron/worker.py`
- Test: `tests/test_worker.py`
- Test: `tests/test_agents.py` (create only if absent)

**Interfaces:**
- Consumes: trusted issue author association, exact agent allowlist, explicit fulfilment evidence.
- Produces: role-scoped draft/research results or BLOCKED status; no external side effects.

- [ ] Test untrusted author, pull request, missing agent label, mismatched agent operation, malformed task JSON and unsupported operation.
- [ ] Replace Boolean-only commercial readiness as a sufficient proof with explicit evidence references for payment status, order identity/amount/currency, supplier stock/price, delivery quote, address completeness and freshness.
- [ ] A Boolean flag alone must never establish a real payment, stock reservation, carrier acceptance or delivery.
- [ ] Missing, stale, conflicting or unverifiable evidence must return BLOCKED and leave dispatch false.
- [ ] Keep sending, publishing, purchasing, payment capture/refund, stock reservation and dispatch outside the autonomous allowlist.

**Acceptance:** Security and fulfilment negative tests pass. No live commercial side effect is possible through the six draft-only handlers.

---

## Stage 2 — Operational observability and agent acceptance

### Task 2.1: Scheduled polling evidence and failure visibility

**Files:**
- Modify: `.github/workflows/agent-runtime.yml`
- Create: `docs/RUNTIME_MONITORING.md`
- Modify: `tests/test_repository_policy.py` (only if this test file exists)

**Interfaces:**
- Consumes: GitHub Actions schedule, issue events, workflow run metadata.
- Produces: documented expected cadence, observed run gaps, run outcomes and actionable alerts.

- [ ] Keep schedule as best-effort 15-minute polling; explicitly avoid an exact-time guarantee.
- [ ] Add a lightweight scheduled health/evidence record if it can be done without widening permissions or creating noisy issue traffic.
- [ ] Document how missed/failed runs are detected from Actions history and how an operator can trigger a manual run.
- [ ] Add repository validation that the workflow retains least-privilege permissions, timeout, six-agent matrix and non-cancelling per-agent concurrency.
- [ ] Compare actual scheduled timestamps with expected intervals; label recurrence VERIFIED only after repeated observed evidence over an agreed observation window.

**Acceptance:** Workflow configuration and actual run evidence are reported separately. No claim of 24/7 operation.

### Task 2.2: Six-agent acceptance matrix

**Files:**
- Create: `docs/AGENT_ACCEPTANCE_MATRIX.md`
- Modify: `docs/AGENT_NETWORK.md`
- Modify: `docs/CORE_RELEASE_GATE.md`

**Interfaces:**
- Consumes: per-agent focused tests, workflow jobs, task result evidence and failure tests.
- Produces: separate NOVA, FORGE, SALES, OPS, FINANCE and PIXEL acceptance status.

- [ ] Define each agent's allowed operations, inputs, outputs, prohibited side effects and failure cases.
- [ ] Record each controlled run by commit SHA, workflow run URL, job URL, issue and result.
- [ ] Distinguish configuration, unit-test proof, controlled workflow proof and production proof.
- [ ] Keep each agent NOT VERIFIED or BLOCKED where evidence is absent.
- [ ] Require a negative test for every prohibited action, especially SALES send, PIXEL publish, FINANCE transfer/refund and OPS dispatch.

**Acceptance:** No agent is called production-ready from an idle job or smoke test alone.

---

## Stage 3 — Revenue execution, one opportunity at a time

### Task 3.1: Prepare the first zero-upfront customer acquisition path

**Files:**
- Modify: `docs/FIRST_REVENUE_OFFER.md`
- Reference: GitHub issue #14
- Reference: `ultron/agents.py`

**Interfaces:**
- Consumes: approved offer, verified price/cost basis and one user-authorized channel.
- Produces: draft landing/listing/message assets and a measurable acquisition plan.

- [ ] Determine which already-accessible channel can accept the offer without new spend or an unapproved account connection.
- [ ] If no channel is accessible, report BLOCKED with the exact access requirement; do not claim acquisition is active.
- [ ] Prepare copy, response templates and tracking fields for human review.
- [ ] Obtain specific approval before any customer message, public listing, publication or account change.
- [ ] Count a sale only after independent payment-provider evidence confirms the transaction and settlement status.

**Acceptance:** A customer-facing action occurs only after the user approves its exact content, destination and timing.

### Task 3.2: Reconcile revenue and profit

**Files:**
- Create: `docs/FINANCIAL_EVIDENCE_LEDGER.md`
- Reference: issue #16
- Modify: `ultron/agents.py` only if a read-only ledger operation is separately tested

**Interfaces:**
- Consumes: verified transaction records, provider fees, refunds, supplier invoices and delivery costs.
- Produces: transaction-level revenue, costs, gross contribution, net profit and settlement reconciliation.

- [ ] Store only evidence-backed transaction rows with source reference, currency, integer minor units, timestamps and settlement state.
- [ ] Separate paid, pending, refunded, disputed and failed transactions.
- [ ] Reconcile provider settlement totals against order-level transactions.
- [ ] Do not infer profit from sales price alone; include fees, cost of goods, delivery, refunds and other known direct costs.
- [ ] Mark missing source records and unmatched balances NOT VERIFIED.

**Acceptance:** Ledger totals reconcile to source records; no synthetic test transaction appears as real revenue.

### Task 3.3: Enable fulfilment only after commercial proof

**Files:**
- Reference: issue #15
- Modify: `ultron/agents.py` only after adapter-specific review
- Test: new provider-adapter tests only after a provider is explicitly approved and accessible

**Interfaces:**
- Consumes: verified paid order, matching currency/amount, confirmed supplier stock and price, delivery quote, valid destination and explicit user approval.
- Produces: human-approval-ready fulfilment request; provider acceptance and delivery evidence only after a separately approved live integration.

- [ ] Keep dispatch disabled by default.
- [ ] Require idempotency and order/payment matching before any provider request.
- [ ] Treat uncertain provider responses as BLOCKED for human reconciliation; never blindly retry an irreversible dispatch.
- [ ] Obtain specific approval for the named provider, account, order and action before any real order, purchase or dispatch.
- [ ] Record supplier/carrier acknowledgements and delivery confirmation as separate evidence states.

**Acceptance:** All missing/uncertain evidence blocks dispatch; no test ID or mock response is treated as real delivery.

---

## Release and verification rules

- Every code change follows a focused red-green-refactor cycle. The red failure must be observed in CI before the corresponding production fix is accepted.
- Run: `pytest -q`, `ruff check .`, and `python scripts/validate_repository.py`.
- Run the Security workflow and inspect both dependency-audit and secret-scan results.
- Review every PR diff and workflow run. Keep changes on a dedicated branch; do not merge.
- Production release remains BLOCKED until provider, payment, fulfilment, security, monitoring, reconciliation and user-approval gates are independently evidenced.
- A first payment is not the finish line: the milestone is a verified, settled transaction with evidenced positive net contribution and safe fulfilment.

## Unresolved external decisions

1. Which existing customer acquisition channel is currently accessible and authorized for the first offer.
2. Which exact offer and price remain current after checking deliverables, demand, direct costs and capacity.
3. Which payment provider and fulfilment provider, if any, the user later chooses to connect and explicitly approves.
4. Whether the GitHub repository's Actions schedule and account limits support the observed operating cadence; exact 15-minute execution is not guaranteed.
