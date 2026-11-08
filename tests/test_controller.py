import json

import pytest

from ultron.controller import ControllerError, authorise_change, run_cycle
from ultron.github_access import GitHubAccess, probe_github_write


def _access(status="VERIFIED", can_push=True):
    return GitHubAccess(status, "cloyboy0904360-ai", can_push, f"push={can_push}", ())


def _runner(payloads):
    def run(args):
        key = args[-1]
        if key not in payloads:
            return 1, "", f"missing {key}"
        return 0, json.dumps(payloads[key]), ""

    return run


def test_write_probe_verified_and_blocked():
    ok = probe_github_write(
        "o",
        "r",
        _runner({"user": {"login": "cloyboy0904360-ai"}, "repos/o/r": {"permissions": {"push": True}}}),
    )
    blocked = probe_github_write(
        "o",
        "r",
        _runner({"user": {"login": "cloyboy0904360-ai"}, "repos/o/r": {"permissions": {"push": False}}}),
    )
    assert ok.status == "VERIFIED" and ok.recovery == ()
    assert blocked.status == "BLOCKED" and blocked.recovery


def test_blocked_github_is_the_only_decision(tmp_path):
    report = run_cycle(
        str(tmp_path / "c.db"),
        probe=lambda owner, repo: _access("BLOCKED", False),
    )
    assert report["decision"]["action"] == "recover_github_write_access"
    assert report["decision"]["agent"] == "GUARDIAN"
    assert report["changes_applied"] is False
    assert report["deployed"] is False
    assert report["measurements"]["revenue_cents"] == 0


def test_one_decision_and_memory_when_github_works(tmp_path):
    db = str(tmp_path / "c.db")
    first = run_cycle(db, cycle_key="c1", probe=lambda owner, repo: _access())
    again = run_cycle(db, cycle_key="c1", probe=lambda owner, repo: _access())
    assert first["decision"]["status"] == "AWAITING APPROVAL"
    assert first["decision"]["agent"] == "FORGE"
    assert len(first["modules"]) == 5
    assert again["duplicate"] is True
    assert again["decision"] == first["decision"]


def test_lock_blocks_a_second_cycle(tmp_path):
    import sqlite3
    from datetime import UTC, datetime

    db = str(tmp_path / "c.db")
    run_cycle(db, cycle_key="held", probe=lambda owner, repo: _access())
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO controller_lock(id, holder, acquired_at) VALUES (1, ?, ?)",
            ("other", datetime.now(tz=UTC).isoformat()),
        )
        conn.commit()
    blocked = run_cycle(db, cycle_key="other-cycle", probe=lambda owner, repo: _access())
    assert blocked["decision"]["action"] == "wait_for_active_cycle"
    assert blocked["changes_applied"] is False


def test_unauthorised_change_is_refused():
    with pytest.raises(ControllerError):
        authorise_change("place_supplier_order", approved=True)
    assert authorise_change("run_tests", approved=False)["applied"] is False
