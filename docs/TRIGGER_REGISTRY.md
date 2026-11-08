# Trigger Registry

Source of truth: `ultron/events.py` (`EVENTS`) and `ultron/agents.py` (`AGENTS`); `tests/test_registries_and_payments.py` fails if an event or agent reference is inconsistent.

Every event is written to the `events` table with `verified_source`. Simulated events must set it to `0` and are never reported as genuine. Default retry: 3 attempts with backoff (1m, 5m, 25m); default escalation: dead-letter, FAILED, notify owner. Events marked "human decision" are not retried automatically.

| Event | Source | Agent | Action |
| --- | --- | --- | --- |
| SYSTEM_START | process start | ULTRON | Load registries, health check |
| DAILY_RESEARCH | scheduler | NOVA | Research, record sources |
| NEW_OPPORTUNITY | NOVA | NOVA | Demand, cost, margin |
| OPPORTUNITY_VALIDATED | NOVA | PROJECT_MANAGER | Queue for approval |
| PRODUCT_APPROVED | owner approval | PIXEL | Prepare listing drafts |
| PRODUCT_LISTING_READY | PIXEL | SALES | Publish (needs approval) |
| STOCK_CHANGE | supplier/scheduled | OPS | Sync availability |
| NEW_ORDER | channel webhook (signed) | OPS | Idempotent order creation |
| PAYMENT_CONFIRMED | provider API lookup | FINANCE | Verify with provider |
| SUPPLIER_CONFIRMED | supplier API | OPS | Record supplier order |
| ORDER_DISPATCHED | supplier API | OPS | Record dispatch |
| TRACKING_UPDATED | carrier API | OPS | Store/push tracking |
| ORDER_DELIVERED | carrier API | OPS | Close order |
| ORDER_EXCEPTION | fulfilment agents | OPS | Open case (human decision) |
| SEO_RESEARCH | scheduler | SEO_BACKLINK | Keyword/content gaps |
| BACKLINK_OPPORTUNITY | SEO_BACKLINK | SEO_BACKLINK | Draft outreach (human decision) |
| CONTENT_READY | PIXEL | SEO_BACKLINK | Plan internal links |
| DEPLOYMENT_REQUEST | workflow_dispatch | FORGE | Controlled deploy |
| DEPLOYMENT_FAILED | deploy workflow | FORGE | Roll back (human decision) |
| DAILY_PERFORMANCE | scheduler | FINANCE | Reconcile actuals |
| SYSTEM_FAILURE | any component | GUARDIAN | Contain (human decision) |
| WEEKLY_R_AND_D_REVIEW | scheduler | PROJECT_MANAGER | Reprioritise |

Status of live event sources: none connected. No payment, channel, supplier or carrier credentials are available, so no event above has been received from a real source.
