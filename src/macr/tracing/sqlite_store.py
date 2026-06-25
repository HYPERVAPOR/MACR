"""SQLite-based trace store."""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path

from macr.tracing.base import TraceStore
from macr.tracing.models import TraceEvent, TraceRun

logger = logging.getLogger(__name__)


class SQLiteTraceStore(TraceStore):
    """SQLite trace store for structured querying."""

    def __init__(self, trace_dir: str | Path, db_name: str = "traces.db") -> None:
        self._trace_dir = Path(trace_dir)
        self._trace_dir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._trace_dir / db_name
        self._conn = sqlite3.connect(str(self._db_path))
        self._conn.row_factory = sqlite3.Row
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                bug_id TEXT NOT NULL,
                configuration TEXT,
                model TEXT,
                started_at TEXT,
                ended_at TEXT,
                status TEXT,
                metrics_json TEXT
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                parent_span_id TEXT,
                timestamp TEXT,
                event_type TEXT,
                step_number INTEGER,
                tool_name TEXT,
                latency_ms REAL,
                payload_json TEXT
            )
            """
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_run_id ON events(run_id)"
        )
        self._conn.commit()

    def save_run(self, run: TraceRun) -> None:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO runs
            (run_id, bug_id, configuration, model, started_at, ended_at, status, metrics_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run.run_id,
                run.bug_id,
                run.configuration,
                run.model,
                run.started_at,
                run.ended_at,
                run.status,
                json.dumps(run.metrics or {}, ensure_ascii=False, default=str),
            ),
        )
        self._conn.commit()

    def append_event(self, event: TraceEvent) -> None:
        self._conn.execute(
            """
            INSERT INTO events
            (event_id, run_id, parent_span_id, timestamp, event_type, step_number, tool_name, latency_ms, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.event_id,
                event.run_id,
                event.parent_span_id,
                event.timestamp,
                event.event_type,
                event.step_number,
                event.tool_name,
                event.latency_ms,
                json.dumps(event.payload, ensure_ascii=False, default=str),
            ),
        )
        self._conn.commit()

    def get_run(self, run_id: str) -> TraceRun | None:
        row = self._conn.execute(
            "SELECT * FROM runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        if row is None:
            return None
        return TraceRun(
            run_id=row["run_id"],
            bug_id=row["bug_id"],
            configuration=row["configuration"] or "",
            model=row["model"] or "",
            started_at=row["started_at"] or "",
            ended_at=row["ended_at"],
            status=row["status"],
            metrics=json.loads(row["metrics_json"] or "{}"),
        )

    def get_events(self, run_id: str) -> list[TraceEvent]:
        rows = self._conn.execute(
            "SELECT * FROM events WHERE run_id = ? ORDER BY timestamp",
            (run_id,),
        ).fetchall()
        return [
            TraceEvent(
                event_id=row["event_id"],
                run_id=row["run_id"],
                parent_span_id=row["parent_span_id"],
                timestamp=row["timestamp"],
                event_type=row["event_type"],
                step_number=row["step_number"],
                tool_name=row["tool_name"],
                latency_ms=row["latency_ms"],
                payload=json.loads(row["payload_json"] or "{}"),
            )
            for row in rows
        ]

    def close(self) -> None:
        self._conn.close()
