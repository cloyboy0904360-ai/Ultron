"""Evidence-led ranking for ULTRON revenue opportunities.

This module is deliberately offline and side-effect free. It ranks hypotheses;
it does not contact prospects, spend money, or claim that revenue exists.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Opportunity:
    key: str
    name: str
    customer: str
    problem: str
    offer: str
    setup_price_gbp: tuple[int, int]
    monthly_price_gbp: tuple[int, int]
    revenue_score: int
    speed_score: int
    zero_cost_score: int
    demand_score: int
    delivery_score: int
    evidence: str
    evidence_status: str = "RESEARCH LEAD — validate before selling"
    risks: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        scores = (
            self.revenue_score,
            self.speed_score,
            self.zero_cost_score,
            self.demand_score,
            self.delivery_score,
        )
        if any(score < 0 or score > 5 for score in scores):
            raise ValueError("Opportunity scores must be between 0 and 5")
        if self.setup_price_gbp[0] > self.setup_price_gbp[1]:
            raise ValueError("Setup price range is reversed")
        if self.monthly_price_gbp[0] > self.monthly_price_gbp[1]:
            raise ValueError("Monthly price range is reversed")

    @property
    def score(self) -> float:
        """Weighted score out of 100; weights total 100."""
        weighted = (
            self.revenue_score * 30
            + self.speed_score * 25
            + self.zero_cost_score * 20
            + self.demand_score * 15
            + self.delivery_score * 10
        )
        return round(weighted / 5, 1)


OPPORTUNITIES: tuple[Opportunity, ...] = (
    Opportunity(
        key="revenue-recovery",
        name="Missed-enquiry and quote recovery system",
        customer="UK trades and appointment-led service SMEs",
        problem="Enquiries and quotations can go unanswered or unchased, leaving potential work unrecovered.",
        offer="A measured workflow for enquiry capture, quote follow-up, dormant-lead review and owner-approved responses.",
        setup_price_gbp=(750, 2500),
        monthly_price_gbp=(150, 500),
        revenue_score=5,
        speed_score=4,
        zero_cost_score=4,
        demand_score=4,
        delivery_score=4,
        evidence=(
            "UK Government AI Adoption Survey 2026 indicates growing business use of AI, "
            "including administrative and marketing applications. Historical Moneypenny "
            "small-business call research is a directional signal only, not a current "
            "market-wide conversion benchmark."
        ),
        risks=(
            "Validate buyer demand and willingness to pay before building integrations.",
            "Check UK GDPR, PECR, lawful basis, suppression lists and consent before messaging.",
            "Telephony, SMS, CRM and email provider costs must be checked; £0 operation is not assumed.",
            "Keep outbound messages and customer data use behind explicit approval.",
        ),
    ),
    Opportunity(
        key="workflow-sprint",
        name="SME workflow automation sprint",
        customer="Small businesses with repetitive admin and lead-handling work",
        problem="Manual handoffs, copying data and delayed responses consume staff time.",
        offer="A tightly scoped workflow audit, one working automation, handover and measured outcome.",
        setup_price_gbp=(500, 2000),
        monthly_price_gbp=(100, 400),
        revenue_score=4,
        speed_score=4,
        zero_cost_score=4,
        demand_score=3,
        delivery_score=4,
        evidence=(
            "The 2026 UK Government AI adoption survey is a broad adoption signal. "
            "It does not establish demand for this specific service or validate these prices."
        ),
        risks=(
            "Scope one workflow and define acceptance tests before agreeing delivery.",
            "Confirm existing customer licences and API limits; do not absorb third-party costs.",
            "Obtain approval before connecting to production accounts or changing live workflows.",
        ),
    ),
    Opportunity(
        key="customer-reactivation",
        name="Dormant-customer reactivation and review workflow",
        customer="Service businesses with a permissioned customer list",
        problem="Past customers may not receive timely, compliant service reminders or review requests.",
        offer="A list-quality review, approved customer segments, draft reactivation sequence and outcome report.",
        setup_price_gbp=(500, 1500),
        monthly_price_gbp=(100, 350),
        revenue_score=3,
        speed_score=3,
        zero_cost_score=3,
        demand_score=3,
        delivery_score=4,
        evidence=(
            "Adjacent to common CRM and marketing automation use cases; specific buyer demand "
            "and list eligibility remain unverified."
        ),
        risks=(
            "Do not message contacts without a documented lawful basis and channel-specific permission.",
            "Screen suppression and opt-out records before any campaign.",
            "No campaign is sent without the customer's written approval.",
        ),
    ),
    Opportunity(
        key="paid-ai-evaluation",
        name="Paid AI evaluation and expert task work",
        customer="AI evaluation platforms and research-task providers",
        problem="Platforms need human evaluation, annotation and specialist feedback.",
        offer="Apply for suitable paid task batches and complete only accepted, paid work.",
        setup_price_gbp=(0, 0),
        monthly_price_gbp=(0, 0),
        revenue_score=2,
        speed_score=3,
        zero_cost_score=5,
        demand_score=3,
        delivery_score=3,
        evidence=(
            "Platform listings and task availability are volatile. Acceptance, task volume, "
            "rates and payment timing must be confirmed directly on each platform."
        ),
        risks=(
            "Do not treat registration, screening or an application as earnings.",
            "Verify eligibility, payment terms, identity requirements and task rates before investing time.",
        ),
    ),
)


def rank_opportunities(
    opportunities: Iterable[Opportunity] = OPPORTUNITIES,
) -> list[Opportunity]:
    """Return a deterministic highest-score-first ranking."""
    return sorted(opportunities, key=lambda item: (-item.score, item.key))


def render_report(opportunities: Iterable[Opportunity] = OPPORTUNITIES) -> str:
    ranked = rank_opportunities(opportunities)
    lines = [
        "# ULTRON Revenue Opportunity Lab",
        "",
        "This is a research-prioritisation report, not proof of customer demand or revenue.",
        "All prices below are hypotheses to test with buyers, not validated market rates.",
        "",
        "## Ranked opportunities",
        "",
    ]
    for index, item in enumerate(ranked, start=1):
        lines.extend(
            [
                f"### {index}. {item.name} — {item.score:.1f}/100",
                "",
                f"- **Target customer:** {item.customer}",
                f"- **Problem:** {item.problem}",
                f"- **Proposed offer:** {item.offer}",
                f"- **Setup price hypothesis:** £{item.setup_price_gbp[0]:,}–£{item.setup_price_gbp[1]:,}",
                f"- **Monthly price hypothesis:** £{item.monthly_price_gbp[0]:,}–£{item.monthly_price_gbp[1]:,}",
                f"- **Evidence:** {item.evidence}",
                f"- **Evidence status:** {item.evidence_status}",
                "- **Risks / validation gates:**",
            ]
        )
        lines.extend(f"  - {risk}" for risk in item.risks)
        lines.append("")
    lines.extend(
        [
            "## Scoring method",
            "",
            (
                "Weighted score out of 100: potential contract value 30%, speed to first payment 25%, "
                "zero-upfront feasibility 20%, demand evidence 15%, delivery feasibility 10%. "
                "Each dimension is scored 0–5. Scores are internal prioritisation judgements, "
                "not measured market statistics."
            ),
            "",
            "## Execution gate",
            "",
            (
                "Do not build a customer-facing system or contact prospects based on this report alone. "
                "First verify a real buyer problem, secure explicit interest, agree a paid scope, "
                "confirm delivery costs and obtain approval. Count revenue only after payment is settled."
            ),
            "",
            "No external contact, spending, account changes or deployment is performed by this module.",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(destination: str | Path) -> Path:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_report(), encoding="utf-8")
    return path
