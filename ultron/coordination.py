"""Shared opportunity board for coordinated ULTRON agent work.

Records are append-only evidence and handoffs; this module does not call external
services, spend money, contact customers, publish listings, or dispatch orders.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from typing import Any

AGENTS = frozenset({"NOVA", "FORGE", "SALES", "OPS", "FINANCE", "PIXEL"})


def _now() -> str:
    return datetime.now(tz=UTC).isoformat()


def _agent(value: str) -> str:
    agent = value.upper() if isinstance(value, str) else ""
    if agent not in AGENTS:
        raise ValueError("unknown agent")
    return agent


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_coordination_db(db_path: str) -> None:
    with _connect(db_path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS opportunities (
                opportunity_key TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                created_by TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'OPEN',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS agent_tasks (
                task_key TEXT PRIMARY KEY,
                opportunity_key TEXT NOT NULL REFERENCES opportunities(opportunity_key),
                assigned_by TEXT NOT NULL,
                assigned_to TEXT NOT NULL,
                instruction TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'READY',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS opportunity_evidence (
                evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_key TEXT NOT NULL REFERENCES opportunities(opportunity_key),
                agent TEXT NOT NULL,
                evidence_type TEXT NOT NULL,
                status TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS agent_lessons (
                lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_key TEXT NOT NULL REFERENCES opportunities(opportunity_key),
                agent TEXT NOT NULL,
                lesson TEXT NOT NULL,
                evidence_id INTEGER REFERENCES opportunity_evidence(evidence_id),
                created_at TEXT NOT NULL
            );
        """)


def create_opportunity(
    db_path: str, *, opportunity_key: str, title: str, created_by: str, description: str
) -> str:
    agent = _agent(created_by)
    if not all(isinstance(v, str) and v.strip() for v in (opportunity_key, title, description)):
        raise ValueError("opportunity key, title and description are required")
    initialize_coordination_db(db_path)
    with _connect(db_path) as conn:
        conn.execute(
            """INSERT INTO opportunities
               (opportunity_key, title, description, created_by, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (opportunity_key.strip(), title.strip(), description.strip(), agent, _now()),
        )
    return opportunity_key.strip()


def add_evidence(
    db_path: str, *, opportunity_key: str, agent: str, evidence_type: str,
    status: str, payload: dict[str, Any]
) -> int:
    owner = _agent(agent)
    if not isinstance(payload, dict):
        raise TypeError("evidence payload must be an object")
    if not all(isinstance(v, str) and v.strip() for v in (evidence_type, status)):
        raise ValueError("evidence type and status are required")
    initialize_coordination_db(db_path)
    with _connect(db_path) as conn:
        if not conn.execute(
            "SELECT 1 FROM opportunities WHERE opportunity_key = ?", (opportunity_key,)
        ).fetchone():
            raise ValueError("opportunity not found")
        cursor = conn.execute(
            """INSERT INTO opportunity_evidence
               (opportunity_key, agent, evidence_type, status, payload_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (opportunity_key, owner, evidence_type, status.upper(),
             json.dumps(payload, sort_keys=True, ensure_ascii=False), _now()),
        )
        return int(cursor.lastrowid)


def record_lesson(
    db_path: str, *, opportunity_key: str, agent: str, lesson: str,
    evidence_id: int | None = None
) -> int:
    owner = _agent(agent)
    if not isinstance(lesson, str) or not lesson.strip():
        raise ValueError("lesson is required")
    initialize_coordination_db(db_path)
    with _connect(db_path) as conn:
        if not conn.execute(
            "SELECT 1 FROM opportunities WHERE opportunity_key = ?", (opportunity_key,)
        ).fetchone():
            raise ValueError("opportunity not found")
        cursor = conn.execute(
            """INSERT INTO agent_lessons
               (opportunity_key, agent, lesson, evidence_id, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (opportunity_key, owner, lesson.strip(), evidence_id, _now()),
        )
        return int(cursor.lastrowid)


def handoff_task(
    db_path: str, *, opportunity_key: str, task_key: str, from_agent: str,
    to_agent: str, instruction: str
) -> str:
    sender, recipient = _agent(from_agent), _agent(to_agent)
    if sender == recipient:
        raise ValueError("handoff must target a different agent")
    if not all(isinstance(v, str) and v.strip() for v in (task_key, instruction)):
        raise ValueError("task key and instruction are required")
    initialize_coordination_db(db_path)
    with _connect(db_path) as conn:
        if not conn.execute(
            "SELECT 1 FROM opportunities WHERE opportunity_key = ?", (opportunity_key,)
        ).fetchone():
            raise ValueError("opportunity not found")
        conn.execute(
            """INSERT OR IGNORE INTO agent_tasks
               (task_key, opportunity_key, assigned_by, assigned_to, instruction, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (task_key, opportunity_key, sender, recipient, instruction.strip(), _now()),
        )
        row = conn.execute(
            "SELECT opportunity_key, assigned_by, assigned_to, instruction "
            "FROM agent_tasks WHERE task_key = ?", (task_key,)
        ).fetchone()
        if (row["opportunity_key"], row["assigned_by"], row["assigned_to"], row["instruction"]) != (
            opportunity_key, sender, recipient, instruction.strip()
        ):
            raise ValueError("task key already exists with conflicting handoff")
    return task_key


def get_opportunity_context(db_path: str, opportunity_key: str) -> dict[str, Any]:
    initialize_coordination_db(db_path)
    with _connect(db_path) as conn:
        opportunity = conn.execute(
            "SELECT * FROM opportunities WHERE opportunity_key = ?", (opportunity_key,)
        ).fetchone()
        if opportunity is None:
            raise ValueError("opportunity not found")
        evidence = conn.execute(
            "SELECT * FROM opportunity_evidence WHERE opportunity_key = ? ORDER BY evidence_id",
            (opportunity_key,),
        ).fetchall()
        tasks = conn.execute(
            "SELECT * FROM agent_tasks WHERE opportunity_key = ? ORDER BY created_at, task_key",
            (opportunity_key,),
        ).fetchall()
        lessons = conn.execute(
            "SELECT * FROM agent_lessons WHERE opportunity_key = ? ORDER BY lesson_id",
            (opportunity_key,),
        ).fetchall()
    return {
        "opportunity": dict(opportunity),
        "evidence": [
            {**dict(row), "payload": json.loads(row["payload_json"])} for row in evidence
        ],
        "tasks": [dict(row) for row in tasks],
        "lessons": [dict(row) for row in lessons],
    }
