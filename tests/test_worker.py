from datetime import UTC, datetime, timedelta

import pytest

from ultron.worker import AgentWorker, parse_task

FENCE = chr(96) * 3


class FakeQueue:
    def __init__(self, issue=None, comments=None):
        self.issue = issue or {
            "number": 42,
            "body": FENCE + "ultron-task\n" + '{"operation":"calculate_margin","input":{"revenue_pence":900,"cost_pence":300,"fees_pence":50}}' + "\n" + FENCE,
            "labels": [{"name": "agent:finance"}, {"name": "status:ready"}],
        }
        self.issue_status = "ready"
        self._comments = comments or []

    def list_issues(self, agent, status):
        return [self.issue] if agent == "FINANCE" and status == self.issue_status else []

    def comments(self, issue_number):
        return list(self._comments)

    def add_comment(self, issue_number, body):
        self._comments.append({"body": body, "created_at": datetime.now(tz=UTC).isoformat()})

    def set_status(self, issue, status):
        self.issue_status = status


def test_parse_task_accepts_structured_json():
    operation, data = parse_task(FENCE + "ultron-task\n" + '{"operation":"x","input":{"a":1}}' + "\n" + FENCE)
    assert operation == "x"
    assert data == {"a": 1}


def test_parse_task_rejects_extra_fields():
    with pytest.raises(ValueError, match="exactly operation and input"):
        parse_task(FENCE + "ultron-task\n" + '{"operation":"x","input":{},"unsafe":true}' + "\n" + FENCE)


def test_worker_records_evidence_and_marks_verified():
    queue = FakeQueue()
    result = AgentWorker("FINANCE", queue).run_once()
    assert result["status"] == "COMPLETED"
    assert queue.issue_status == "verified"
    assert any("ULTRON_RESULT" in item["body"] and "gross_profit_pence" in item["body"] for item in queue._comments)


def test_worker_rejects_cross_agent_operation_and_reports_failure():
    queue = FakeQueue()
    queue.issue["body"] = FENCE + "ultron-task\n" + '{"operation":"draft_reply","input":{"lead_context":"x","offer":"y","next_step":"z"}}' + "\n" + FENCE
    result = AgentWorker("FINANCE", queue).run_once()
    assert result["status"] == "FAILED"
    assert queue.issue_status == "failed"
    assert any("failure report" in item["body"] for item in queue._comments)


def test_worker_is_idle_when_no_task_is_ready():
    queue = FakeQueue()
    queue.issue_status = "running"
    result = AgentWorker("FINANCE", queue).run_once()
    assert result == {"agent": "FINANCE", "status": "IDLE", "processed": 0}


def test_worker_reclaims_stale_lease():
    old = (datetime.now(tz=UTC) - timedelta(minutes=45)).isoformat()
    queue = FakeQueue()
    queue.issue_status = "running"
    queue._comments.append({
        "body": "<!-- ULTRON_LEASE " + '{"run_id":"old-run"}' + " -->",
        "created_at": old,
    })
    worker = AgentWorker("FINANCE", queue)
    worker._recover_stale_leases()
    assert queue.issue_status == "ready"
    assert any("Expired FINANCE lease reclaimed" in item["body"] for item in queue._comments)
