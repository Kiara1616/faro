"""Local audit storage for Faro's simulation.

The store records decisions and simulator events, never raw audio. It can
migrate the original ``decisions`` table used by the first prototype.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any
from uuid import uuid4


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class AuditRecord:
    timestamp: str
    command_id: str
    session_id: str | None
    operator_label: str | None
    source: str
    transcript: str
    intent: str
    hole_id: str | None
    state_before: str
    state_after: str
    accepted: bool
    decision: str
    reason: str
    event_status: str | None = None


class AuditStore:
    """SQLite repository with an idempotent migration from legacy decisions."""

    def __init__(self, path: str | Path):
        self.path = str(path)
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS schema_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            db.execute(
                """CREATE TABLE IF NOT EXISTS audit_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    command_id TEXT NOT NULL,
                    session_id TEXT,
                    operator_label TEXT,
                    source TEXT NOT NULL,
                    transcript TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    hole_id TEXT,
                    state_before TEXT NOT NULL,
                    state_after TEXT NOT NULL,
                    accepted INTEGER NOT NULL,
                    decision TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    event_status TEXT
                )"""
            )
            db.execute("CREATE INDEX IF NOT EXISTS idx_audit_command ON audit_records(command_id, id)")
            self._migrate_legacy(db)
            db.execute("INSERT OR REPLACE INTO schema_meta(key,value) VALUES('audit_schema','3')")

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    @staticmethod
    def _migrate_legacy(db: sqlite3.Connection) -> None:
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "decisions" not in tables:
            return
        already = db.execute("SELECT 1 FROM schema_meta WHERE key='legacy_decisions_migrated'").fetchone()
        if already:
            return
        columns = {row[1] for row in db.execute("PRAGMA table_info(decisions)")}
        required = {"timestamp", "transcript", "intent", "accepted", "decision", "step", "source"}
        if not required.issubset(columns):
            raise ValueError("Legacy decisions table has an unsupported schema")
        rows = db.execute("SELECT timestamp, transcript, intent, accepted, decision, step, source FROM decisions ORDER BY id").fetchall()
        for row in rows:
            db.execute(
                """INSERT INTO audit_records
                (timestamp,command_id,session_id,operator_label,source,transcript,intent,hole_id,
                 state_before,state_after,accepted,decision,reason,event_status)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (row[0], f"legacy-{row[2]}-{row[0]}", None, None, row[6], row[1], row[2], None,
                 f"legacy_step_{row[5]}", f"legacy_step_{row[5]}", int(row[3]), row[4], row[4], None),
            )
        db.execute("INSERT INTO schema_meta(key,value) VALUES('legacy_decisions_migrated','1')")

    def record_decision(self, *, command_id: str | None, session_id: str | None,
                        operator_label: str | None, source: str, transcript: str,
                        intent: str, hole_id: str | None, state_before: str,
                        state_after: str, accepted: bool, decision: str,
                        reason: str, timestamp: str | None = None) -> str:
        command_id = command_id or uuid4().hex
        with self._connect() as db:
            db.execute(
                """INSERT INTO audit_records
                (timestamp,command_id,session_id,operator_label,source,transcript,intent,hole_id,
                 state_before,state_after,accepted,decision,reason,event_status)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,NULL)""",
                (timestamp or _now(), command_id, session_id, operator_label, source, transcript,
                 intent, hole_id, state_before, state_after, int(accepted), decision, reason),
            )
        return command_id

    def record_event(self, command_id: str, status: str, reason: str = "", timestamp: str | None = None) -> int:
        with self._connect() as db:
            source = db.execute(
                """SELECT session_id, operator_label, source, transcript, intent, hole_id,
                          state_before, state_after, accepted, decision
                   FROM audit_records WHERE command_id=? ORDER BY id DESC LIMIT 1""",
                (command_id,),
            ).fetchone()
            if source is None:
                raise KeyError(f"Unknown command_id: {command_id}")
            db.execute(
                """INSERT INTO audit_records
                   (timestamp,command_id,session_id,operator_label,source,transcript,intent,hole_id,
                    state_before,state_after,accepted,decision,reason,event_status)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (timestamp or _now(), command_id, source[0], source[1], source[2], source[3],
                 source[4], source[5], source[6], source[7], source[8], source[9], reason, status),
            )
            return 1

    def list_records(self, command_id: str | None = None) -> list[dict[str, Any]]:
        with self._connect() as db:
            if command_id is None:
                rows = db.execute("SELECT * FROM audit_records ORDER BY id").fetchall()
            else:
                rows = db.execute("SELECT * FROM audit_records WHERE command_id=? ORDER BY id", (command_id,)).fetchall()
        return [dict(row) for row in rows]
