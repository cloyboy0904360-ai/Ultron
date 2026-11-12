import json
import sqlite3

import pytest

from ultron.coordination import (
    add_evidence,
    create_opportunity,
    get_opportunity_context,
    handoff_task,
    record_lesson,
)


@pytest.fixture
def board(tmp_path):
    return str(tmp_path / "shared-board.sqlite3")


def test_agents_share_opportunity_evidence_and_lessons(board):
    opportunity = create_opportunity(
        board,
        opportunity_key="uk-dehumidifier-01",
        title="UK dehumidifier product opportunity",
        created_by="NOVA",
        description="Research demand, supplier availability and contribution margin.",
    )
    evidence_id = add_evidence(
        board,
        opportunity_key=opportunity,
        agent="OPS",
        evidence_type="supplier_check",
        status="UNVERIFIED",
        payload={"supplier": "Example Supplier", "stock": None},
    )
    record_lesson(
        board,
        opportunity_key=opportunity,
        agent="OPS",
        lesson="Do not shortlist without timestamped supplier stock evidence.",
        evidence_id=evidence_id,
    )
    context = get_opportunity_context(board, opportunity)
    assert context["opportunity"]["status"] == "OPEN"
    assert context["evidence"][0]["agent"] == "OPS"
    assert context["evidence"][0]["payload"]["stock"] is None
    assert context["lessons"][0]["lesson"].startswith("Do not shortlist")
    assert context["evidence"][0]["status"] == "UNVERIFIED"


def test_handoff_is_idempotent_and_routes_between_agents(board):
    create_opportunity(
        board, opportunity_key="opp-2", title="Digital offer", created_by="NOVA",
        description="Validate demand and cost basis.",
    )
    first = handoff_task(
        board, opportunity_key="opp-2", task_key="opp-2-sales", from_agent="NOVA",
        to_agent="SALES", instruction="Validate demand; return sourced evidence.",
    )
    second = handoff_task(
        board, opportunity_key="opp-2", task_key="opp-2-sales", from_agent="NOVA",
        to_agent="SALES", instruction="Validate demand; return sourced evidence.",
    )
    assert first == second
    context = get_opportunity_context(board, "opp-2")
    assert len(context["tasks"]) == 1
    assert context["tasks"][0]["assigned_to"] == "SALES"
    assert context["tasks"][0]["status"] == "READY"


@pytest.mark.parametrize("agent", ["NOVA", "FORGE", "SALES", "OPS", "FINANCE", "PIXEL"])
def test_shared_board_accepts_only_known_agents(board, agent):
    create_opportunity(
        board, opportunity_key="opp-3", title="Test", created_by="NOVA", description="Test",
    )
    add_evidence(
        board, opportunity_key="opp-3", agent=agent, evidence_type="test",
        status="NOT_VERIFIED", payload={"agent": agent},
    )


def test_shared_context_does_not_allow_unknown_agent_or_missing_opportunity(board):
    with pytest.raises(ValueError, match="unknown agent"):
        create_opportunity(
            board, opportunity_key="bad", title="Bad", created_by="ROGUE", description="x",
        )
    with pytest.raises(ValueError, match="not found"):
        get_opportunity_context(board, "missing")
