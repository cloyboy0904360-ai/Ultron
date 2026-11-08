"""One-shot GitHub Actions worker entry point for one ULTRON agent."""
from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from ultron.agents import execute_task
from ultron.github_queue import GitHubAPIError, GitHubQueue

FENCE = chr(96) * 3
TASK_BLOCK = re.compile(re.escape(FENCE + "ultron-task") + r"\s*(\{.*?\})\s*" + re.escape(FENCE), re.DOTALL)
MAX_ATTEMPTS = 3
STALE_LEASE_MINUTES = 30

def utc_now() -> datetime:
    return datetime.now(tz=UTC)

def parse_task(body: str) -> tuple[str, dict[str, Any]]:
    match = TASK_BLOCK.search(body or "")
    if not match:
        raise ValueError("issue body must contain a fenced ultron-task JSON block")
    try:
        task = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid ultron-task JSON: {exc.msg}") from exc
    if not isinstance(task, dict) or set(task) != {"operation", "input"}:
        raise ValueError("task JSON must contain exactly operation and input")
    if not isinstance(task["operation"], str) or not isinstance(task["input"], dict):
        raise TypeError("operation must be a string and input must be an object")
    return task["operation"], task["input"]

def _marker(comment: dict[str, Any], prefix: str) -> dict[str, Any] | None:
    for line in comment.get("body", "").splitlines():
        if line.startswith(prefix):
            try:
                payload = line[len(prefix):].strip()
                if payload.endswith("-->"):
                    payload = payload[:-3].strip()
                return json.loads(payload)
            except json.JSONDecodeError:
                return None
    return None

class AgentWorker:
    def __init__(self, agent: str, queue: GitHubQueue):
        self.agent = agent.upper()
        self.queue = queue
        if self.agent not in {"NOVA", "FORGE", "SALES", "OPS", "FINANCE", "PIXEL"}:
            raise ValueError("unknown ULTRON agent")

    def _recover_stale_leases(self) -> None:
        for issue in self.queue.list_issues(self.agent, "running"):
            comments = self.queue.comments(issue["number"])
            leases = [(c, _marker(c, "<!-- ULTRON_LEASE ")) for c in comments]
            leases = [(c, data) for c, data in leases if data]
            if not leases:
                continue
            lease_comment, lease = leases[-1]
            run_id = lease.get("run_id")
            completed = any(
                (_marker(c, "<!-- ULTRON_RESULT ") or {}).get("run_id") == run_id
                for c in comments
            )
            if completed:
                continue
            issued = datetime.fromisoformat(lease_comment["created_at"])
            if utc_now() - issued > timedelta(minutes=STALE_LEASE_MINUTES):
                self.queue.set_status(issue, "ready")
                self.queue.add_comment(issue["number"],
                    f"<!-- ULTRON_RECOVERY -->\nExpired {self.agent} lease reclaimed after {STALE_LEASE_MINUTES} minutes. No completion evidence was found.")

    def run_once(self) -> dict[str, Any]:
        self._recover_stale_leases()
        issues = self.queue.list_issues(self.agent, "ready")
        if not issues:
            return {"agent": self.agent, "status": "IDLE", "processed": 0}
        issue = issues[0]
        number = issue["number"]
        comments = self.queue.comments(number)
        attempts = sum(1 for c in comments if "<!-- ULTRON_ATTEMPT " in c.get("body", ""))
        attempt = attempts + 1
        if attempt > MAX_ATTEMPTS:
            self.queue.set_status(issue, "failed")
            self.queue.add_comment(number, "ULTRON failed: maximum manual attempts exceeded.")
            return {"agent": self.agent, "status": "FAILED", "issue": number, "processed": 0}

        run_id = str(uuid.uuid4())
        lease = {"agent": self.agent, "run_id": run_id, "attempt": attempt, "issued_at": utc_now().isoformat()}
        self.queue.set_status(issue, "running")
        self.queue.add_comment(number,
            f"<!-- ULTRON_ATTEMPT {attempt} -->\n<!-- ULTRON_LEASE {json.dumps(lease, separators=(',', ':'))} -->\nULTRON {self.agent} acquired this task. Run: {run_id}.")

        try:
            operation, task_input = parse_task(issue.get("body", ""))
            result = execute_task(self.agent, operation, task_input)
            evidence = {
                "agent": self.agent, "issue": number, "run_id": run_id, "attempt": attempt,
                "operation": result.operation, "status": result.status, "output": result.output,
                "completed_at": utc_now().isoformat(),
            }
            encoded = json.dumps(evidence, ensure_ascii=False, separators=(",", ":"))
            if len(encoded) > 6000:
                raise ValueError("task output exceeds the 6000-character evidence limit")
            self.queue.add_comment(number,
                f"<!-- ULTRON_RESULT {json.dumps({'run_id': run_id, 'status': result.status})} -->\n"
                f"**ULTRON {self.agent} evidence**\n\n{FENCE}json\n{json.dumps(evidence, ensure_ascii=False, indent=2)}\n{FENCE}")
            self.queue.set_status(issue, "verified" if result.status == "COMPLETED" else "blocked")
            return {"agent": self.agent, "status": result.status, "issue": number, "run_id": run_id}
        except (ValueError, TypeError, PermissionError, GitHubAPIError) as exc:
            failure = {
                "agent": self.agent, "issue": number, "run_id": run_id, "attempt": attempt,
                "status": "FAILED", "error_type": type(exc).__name__, "error": str(exc)[:1000],
                "failed_at": utc_now().isoformat(),
            }
            self.queue.add_comment(number,
                f"<!-- ULTRON_RESULT {json.dumps({'run_id': run_id, 'status': 'FAILED'})} -->\n"
                f"**ULTRON {self.agent} failure report**\n\n{FENCE}json\n{json.dumps(failure, indent=2)}\n{FENCE}")
            self.queue.set_status(issue, "failed")
            return {"agent": self.agent, "status": "FAILED", "issue": number, "run_id": run_id}

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", required=True)
    args = parser.parse_args()
    try:
        result = AgentWorker(args.agent, GitHubQueue.from_environment()).run_once()
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["status"] != "FAILED" else 1
    except (GitHubAPIError, ValueError, TypeError, PermissionError) as exc:
        print(json.dumps({"agent": args.agent.upper(), "status": "FAILED", "error": str(exc)[:1000]}))
        return 1

if __name__ == "__main__":
    sys.exit(main())
