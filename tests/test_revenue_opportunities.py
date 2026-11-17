from pathlib import Path

import pytest

from ultron.revenue_opportunities import (
    OPPORTUNITIES,
    Opportunity,
    rank_opportunities,
    render_report,
    write_report,
)


def test_opportunities_are_ranked_highest_score_first():
    ranked = rank_opportunities()
    assert ranked
    assert [item.score for item in ranked] == sorted(
        (item.score for item in ranked), reverse=True
    )
    assert ranked[0].key == "revenue-recovery"


def test_scores_are_bounded_and_weighted_to_one_hundred():
    assert all(0 <= item.score <= 100 for item in OPPORTUNITIES)
    assert all(item.score == round(item.score, 1) for item in OPPORTUNITIES)


def test_invalid_score_is_rejected():
    with pytest.raises(ValueError, match="between 0 and 5"):
        Opportunity(
            key="bad",
            name="Bad score",
            customer="Buyer",
            problem="Problem",
            offer="Offer",
            setup_price_gbp=(1, 2),
            monthly_price_gbp=(0, 0),
            revenue_score=6,
            speed_score=1,
            zero_cost_score=1,
            demand_score=1,
            delivery_score=1,
            evidence="Not evidence",
        )


def test_reversed_price_range_is_rejected():
    with pytest.raises(ValueError, match="reversed"):
        Opportunity(
            key="bad",
            name="Bad range",
            customer="Buyer",
            problem="Problem",
            offer="Offer",
            setup_price_gbp=(500, 100),
            monthly_price_gbp=(0, 0),
            revenue_score=1,
            speed_score=1,
            zero_cost_score=1,
            demand_score=1,
            delivery_score=1,
            evidence="Not evidence",
        )


def test_report_labels_prices_as_hypotheses_and_revenue_as_unverified():
    report = render_report()
    assert "not proof of customer demand or revenue" in report
    assert "prices below are hypotheses" in report
    assert "£750–£2,500" in report
    assert "No external contact" in report


def test_write_report_creates_parent_directory(tmp_path: Path):
    target = tmp_path / "nested" / "report.md"
    result = write_report(target)
    assert result == target
    assert target.exists()
    assert "# ULTRON Revenue Opportunity Lab" in target.read_text(encoding="utf-8")
