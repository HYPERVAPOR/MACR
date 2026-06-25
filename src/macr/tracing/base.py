"""Abstract trace store interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from macr.tracing.models import TraceEvent, TraceRun


class TraceStore(ABC):
    """Backend responsible for persisting trace runs and events."""

    @abstractmethod
    def save_run(self, run: TraceRun) -> None:
        """Persist or update a run summary."""

    @abstractmethod
    def append_event(self, event: TraceEvent) -> None:
        """Persist a single trace event."""

    @abstractmethod
    def get_run(self, run_id: str) -> TraceRun | None:
        """Retrieve a run summary by id."""

    @abstractmethod
    def get_events(self, run_id: str) -> list[TraceEvent]:
        """Retrieve all events for a given run, ordered by timestamp."""

    def close(self) -> None:
        """Release any resources. Default no-op."""
        return None
