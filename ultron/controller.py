"""Single ULTRON master controller.

Subordinate modules report here. This process does not spend money, publish, place supplier
orders, or treat a recorded cycle as a live business result.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta

from ultron.assets import ensure_registry
from ultron.events import validate_registry
from ultron.github_access import GitHubAccess, probe_github_write
from ultron.modules import ModuleReport, collect_reports
from ultron.pathway import initialize_db

ALLOWED_CHANGES = frozenset({"run_tests", "validate_repository"})


class ControllerError(RuntimeError):
    pass


class ManageableFailure(ControllerError):
    pass


@dataclass(frozen=True)
class Decision:
    agent: str
    action: str
    status: str
    reason: str


def _now() -> str:
    return datetime.now(tz=UTC).isoformat()


def ensure_schema(db_path: str) -> None:
    initialize_db(db_path)
    ensure_registry(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS controller_lock (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                holder TEXT NOT NULL,
                acquired_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS controller_cycles (
                id INTEGER PRIMARY KEY,
                cycle_key TEXT UNIQUE,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT NOT NULL,
                github_status TEXT NOT NULL,
                agent TEXT,
                action TEXT,
                attempts INTEGER NOT NULL,
                report_json TEXT NOT NULL
            )
            """
        )


def measure(db_path: str) -> dict:
    """Actual stored cents only. Missing tables and open orders contribute nothing."""
    with sqlite3.connect(db_path) as conn:
        try:
            row = conn.execute(
                """
                SELECT COUNT(*),
                       COALESCE(SUM(o.total_cents), 0),
                       COALESCE(SUM(o.total_cents - f.fees_cents - f.supplier_cost_cents
                                    - f.delivery_cost_cents), 0)
                FROM fulfilment f
                JOIN orders o ON o.id = f.order_id
                WHERE f.state = 'CLOSED'
                """
            ).fetchone()
        except sqlite3.OperationalError:
            row = (0, 0, 0)
    return {
        "closed_orders": int(row[0]),
        "revenue_cents": int(row[1]),
        "reconciled_profit_cents": int(row[2]),
        "forecast_cents": None,
    }


def decide(access: GitHubAccess, reports: tuple[ModuleReport, ...], registry_problems: list[str]) -> Decision:
    if access.status != "VERIFIED":
        return Decision(
            "GUARDIAN",
            "recover_github_write_access",
            "BLOCKED",
            access.evidence,
        )
    if registry_problems:
        return Decision("FORGE", "repair_agent_registry", "FAILED", "; ".join(registry_problems))
    failed = next((item for item in reports if item.status == "FAILED"), None)
    if failed:
        return Decision(failed.agent, f"recover_{failed.name}", "FAILED", failed.summary)
    return Decision(
        "FORGE",
        "await_verified_payment_provider",
        "AWAITING APPROVAL",
        "No closed reconciled order and no authority to connect a payment provider",
    )


def authorise_change(name: str, *, approved: bool) -> dict:
    if name not in ALLOWED_CHANGES:
        raise ControllerError("change is not authorised")
    if not approved:
        return {"change": name, "applied": False, "status": "AWAITING APPROVAL"}
    return {"change": name, "applied": False, "status": "READY"}


def _persist(db_path: str, cycle_key: str | None, started: str, payload: dict, attempts: int) -> dict:
    finished = _now()
    payload["finished_at"] = finished
    payload["attempts"] = attempts
    with sqlite3.connect(db_path) as conn:
        if cycle_key:
            prior = conn.execute(
                "SELECT report_json FROM controller_cycles WHERE cycle_key = ?",
                (cycle_key,),
            ).fetchone()
            if prior:
                stored = json.loads(prior[0])
                stored["duplicate"] = True
                return stored
        conn.execute(
            """
            INSERT INTO controller_cycles(
                cycle_key, started_at, finished_at, status, github_status, agent, action,
                attempts, report_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cycle_key,
                started,
                finished,
                payload["status"],
                payload["github"]["status"],
                payload["decision"]["agent"],
                payload["decision"]["action"],
                attempts,
                json.dumps(payload),
            ),
        )
        conn.commit()
    return payload


def _acquire_lock(db_path: str, holder: str, stale_after: timedelta = timedelta(minutes=20)) -> bool:
    with sqlite3.connect(db_path) as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT holder, acquired_at FROM controller_lock WHERE id = 1").fetchone()
        if row and row[0] != holder:
            acquired = datetime.fromisoformat(row[1])
            if datetime.now(tz=UTC) - acquired < stale_after:
                conn.commit()
                return False
        conn.execute(
            """
            INSERT INTO controller_lock(id, holder, acquired_at) VALUES (1, ?, ?)
            ON CONFLICT(id) DO UPDATE SET holder = excluded.holder, acquired_at = excluded.acquired_at
            """,
            (holder, _now()),
        )
        conn.commit()
    return True


def _release_lock(db_path: str, holder: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM controller_lock WHERE id = 1 AND holder = ?", (holder,))
        conn.commit()


def run_cycle(
    db_path: str,
    *,
    cycle_key: str | None = None,
    owner: str | None = None,
    repo: str | None = None,
    probe=probe_github_write,
    reports_fn=collect_reports,
    max_attempts: int = 2,
) -> dict:
    ensure_schema(db_path)
    holder = cycle_key or "cycle"
    if not _acquire_lock(db_path, holder):
        return {
            "status": "BLOCKED",
            "deployed": False,
            "changes_applied": False,
            "duplicate": True,
            "github": asdict(GitHubAccess("BLOCKED", None, False, "cycle lock held", ())),
            "modules": [],
            "decision": asdict(Decision("ULTRON", "wait_for_active_cycle", "BLOCKED", "lock held")),
            "measurements": measure(db_path),
            "started_at": _now(),
            "finished_at": _now(),
            "attempts": 0,
        }
    owner = owner or os.environ.get("ULTRON_GITHUB_OWNER", "cloyboy0904360-ai")
    repo = repo or os.environ.get("ULTRON_GITHUB_REPO", "Ultron")
    last_error = "unknown"
    try:
        for attempt in range(1, max_attempts + 1):
            started = _now()
            try:
                access = probe(owner, repo)
                reports = reports_fn(db_path)
                problems = validate_registry()
                decision = decide(access, reports, problems)
                payload = {
                    "status": decision.status,
                    "deployed": False,
                    "changes_applied": False,
                    "duplicate": False,
                    "github": asdict(access),
                    "modules": [asdict(item) for item in reports],
                    "decision": asdict(decision),
                    "measurements": measure(db_path),
                    "started_at": started,
                }
                return _persist(db_path, cycle_key, started, payload, attempt)
            except ManageableFailure as exc:
                last_error = str(exc)
                continue
    finally:
        _release_lock(db_path, holder)
    failed = {
        "status": "FAILED",
        "deployed": False,
        "changes_applied": False,
        "duplicate": False,
        "github": asdict(GitHubAccess("FAILED", None, False, last_error, ())),
        "modules": [],
        "decision": asdict(Decision("ULTRON", "retry_cycle", "FAILED", last_error)),
        "measurements": {"closed_orders": 0, "revenue_cents": 0, "reconciled_profit_cents": 0, "forecast_cents": None},
        "started_at": _now(),
    }
    return _persist(db_path, cycle_key, failed["started_at"], failed, max_attempts)


def main() -> int:
    db_path = os.environ.get("ULTRON_DB", "data/controller.db")
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    report = run_cycle(db_path)
    text = json.dumps(report, indent=2)
    print(text)
    out = os.environ.get("ULTRON_CYCLE_REPORT", "data/controller-cycle.json")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as handle:
        handle.write(text + "\n")
    if report["status"] == "FAILED":
        return 1
    if report["github"]["status"] != "VERIFIED":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
