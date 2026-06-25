"""JSONL-based trace store."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from macr.tracing.base import TraceStore
from macr.tracing.models import TraceEvent, TraceRun

logger = logging.getLogger(__name__)


class JsonlTraceStore(TraceStore):
    """Append-only JSONL trace store.

    Events are written to `<trace_dir>/events.jsonl`.
    Run summaries are written to `<trace_dir>/runs.jsonl`.
    """

    def __init__(self, trace_dir: str | Path) -> None:
        self._trace_dir = Path(trace_dir)
        self._trace_dir.mkdir(parents=True, exist_ok=True)
        self._events_path = self._trace_dir / "events.jsonl"
        self._runs_path = self._trace_dir / "runs.jsonl"

    def save_run(self, run: TraceRun) -> None:
        self._append_jsonl(self._runs_path, run.model_dump())

    def append_event(self, event: TraceEvent) -> None:
        self._append_jsonl(self._events_path, event.model_dump())

    def get_run(self, run_id: str) -> TraceRun | None:
        if not self._runs_path.exists():
            return None
        for line in self._read_lines_reverse(self._runs_path):
            data = json.loads(line)
            if data.get("run_id") == run_id:
                return TraceRun.model_validate(data)
        return None

    def get_events(self, run_id: str) -> list[TraceEvent]:
        events: list[TraceEvent] = []
        if not self._events_path.exists():
            return events
        with self._events_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                if data.get("run_id") == run_id:
                    events.append(TraceEvent.model_validate(data))
        return events

    @staticmethod
    def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

    @staticmethod
    def _read_lines_reverse(path: Path) -> Iterator[str]:
        """Yield lines from a file in reverse order."""
        with path.open("r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in reversed(lines):
            line = line.strip()
            if line:
                yield line
