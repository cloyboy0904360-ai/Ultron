# Revenue Opportunity Lab

## Purpose

This workflow ranks revenue hypotheses for ULTRON. It is a research and prioritisation aid, not a lead database, sales automation, or revenue ledger. It does not send messages, access customer data, spend money, alter accounts, or deploy customer-facing services.

## First priority: revenue recovery for service SMEs

The highest-ranked hypothesis is a missed-enquiry and quote-recovery workflow for UK trades and appointment-led service businesses.

Proposed scope:

1. Capture inbound enquiries from channels the customer already uses.
2. Identify unanswered enquiries and quotes awaiting a response.
3. Prepare owner-reviewed follow-up drafts.
4. Record outcomes and report recovered, lost and unresolved opportunities.
5. Add integrations only after a buyer has agreed a paid scope and provider costs are understood.

Initial commercial hypothesis only: £750–£2,500 setup and £150–£500 per month. These figures are not validated market prices, customer commitments, or revenue.

## Research signals and limitations

- The UK Government AI Adoption Survey 2026 was reported as showing increased UK business adoption of AI, with administrative and marketing applications among common uses. This is a broad adoption signal, not proof that a particular SME will buy this service.
- Historical Moneypenny small-business call research reported missed-call and voicemail behaviour. It is old directional evidence and must not be presented as a current universal benchmark.
- Competitor price examples found during desk research suggest that some providers charge for missed-call response, implementation, CRM integration and reactivation services. Advertised prices are not evidence of achievable ULTRON pricing, delivered value or buyer willingness to pay.

Before using any statistic or competitor price in sales material, independently re-open the original source, record its publication date, geography, sample and exact scope, and retain a source URL. The current ranking deliberately does not treat these desk-research signals as verified demand.

## Ranked alternatives

1. **Missed-enquiry and quote recovery:** strongest initial hypothesis; higher potential contract value and recurring service opportunity.
2. **SME workflow automation sprint:** one bounded automation with acceptance tests and handover.
3. **Dormant-customer reactivation:** only for customer lists with a documented lawful basis and channel permissions.
4. **Paid AI evaluation tasks:** low-upfront fallback; applications, screening and task availability are not earnings.

## Scoring

The code scores each opportunity from 0–5 on five dimensions:

| Dimension | Weight |
|---|---:|
| Potential contract value | 30% |
| Speed to first payment | 25% |
| Zero-upfront feasibility | 20% |
| Demand evidence | 15% |
| Delivery feasibility | 10% |

The score is an internal prioritisation judgement, not a market statistic.

## Mandatory commercial validation

Before building or selling:

- Interview or otherwise validate the problem with a real prospective buyer.
- Confirm the buyer's current process, volume, cost of failure and decision-maker.
- Obtain explicit agreement on scope, acceptance criteria, price and payment terms.
- Confirm delivery effort and any telephony, SMS, email, CRM, hosting or API costs.
- Keep within the £0-upfront rule; do not absorb provider charges.
- Check UK GDPR and PECR requirements, lawful basis, retention, suppression and opt-out handling.
- Keep outbound communications, production account changes and deployments behind explicit approval.

## Revenue evidence standard

- An enquiry is not a sale.
- A verbal expression of interest is not a signed contract.
- An issued invoice or payment link is not revenue.
- Count revenue only when payment is confirmed as settled and reconciled.
- Record refunds and chargebacks separately.
- Never fabricate customers, conversion rates, delivery evidence or financial results.

## Automation

The GitHub Actions workflow runs daily at 08:15 UTC and can also be started manually. It runs the focused tests, generates a Markdown ranking report and stores it as a workflow artifact for 14 days. The workflow requests read-only repository permissions and performs no external contact or deployment.

## Current implementation boundary

This lab is offline and deterministic. It does not scrape websites, contact leads, send email or SMS, connect payment providers, or claim that any opportunity has been accepted. Those capabilities require separately approved integrations, source validation, security review and customer-specific consent.
