"""TraceLogger for emitting structured trace events."""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any

from macr.tracing.base import TraceStore
from macr.tracing.jsonl_store import JsonlTraceStore
from macr.tracing.models import TraceEvent, TraceRun


class TraceLogger:
    """Lightweight logger that emits trace events to a TraceStore."""

    def __init__(
        self,
        run_id: str,
        bug_id: str,
        configuration: str,
        model: str,
        store: TraceStore | None = None,
    ) -> None:
        self._run_id = run_id
        self._bug_id = bug_id
        self._configuration = configuration
        self._model = model
        self._store = store or JsonlTraceStore("outputs/traces")
        self._start_time = time.perf_counter()

    @property
    def run_id(self) -> str:
        return self._run_id

    @property
    def store(self) -> TraceStore:
        return self._store

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _uuid() -> str:
        return uuid.uuid4().hex

    def _emit(
        self,
        event_type: str,
        payload: dict[str, Any],
        *,
        step_number: int | None = None,
        tool_name: str | None = None,
        latency_ms: float | None = None,
    ) -> None:
        event = TraceEvent(
            event_id=self._uuid(),
            run_id=self._run_id,
            timestamp=self._now(),
            event_type=event_type,
            step_number=step_number,
            tool_name=tool_name,
            latency_ms=latency_ms,
            payload=payload,
        )
        self._store.append_event(event)

    def log_run_start(self) -> None:
        self._emit(
            "run_start",
            {
                "bug_id": self._bug_id,
                "configuration": self._configuration,
                "model": self._model,
            },
        )

    def log_run_end(self, status: str, metrics: dict[str, Any] | None = None) -> None:
        elapsed_ms = (time.perf_counter() - self._start_time) * 1000
        run = TraceRun(
            run_id=self._run_id,
            bug_id=self._bug_id,
            configuration=self._configuration,
            model=self._model,
            started_at=self._now(),  # approximate; run_start event has exact start
            ended_at=self._now(),
            status=status,
            metrics=metrics,
        )
        self._store.save_run(run)
        self._emit(
            "run_end",
            {"status": status, "metrics": metrics or {}},
            latency_ms=elapsed_ms,
        )

    def log_react_step(
        self,
        step_number: int,
        thought: str,
        tool_name: str,
        tool_input: dict[str, Any],
        observation: dict[str, Any],
    ) -> None:
        self._emit(
            "react_step",
            {
                "thought": thought,
                "tool_input": tool_input,
                "observation": observation,
            },
            step_number=step_number,
            tool_name=tool_name,
        )

    def log_tool_call(self, tool_name: str, tool_input: dict[str, Any]) -> None:
        self._emit(
            "tool_call",
            {"tool_input": tool_input},
            tool_name=tool_name,
        )

    def log_tool_result(
        self,
        tool_name: str,
        observation: dict[str, Any],
        latency_ms: float,
    ) -> None:
        self._emit(
            "tool_result",
            {"observation": observation},
            tool_name=tool_name,
            latency_ms=latency_ms,
        )

    def log_llm_request(self, messages: list[dict[str, Any]]) -> None:
        self._emit(
            "llm_request",
            {
                "message_count": len(messages),
                "messages": messages,
            },
        )

    def log_llm_response(
        self,
        content: Any,
        usage: Any,
        latency_ms: float,
    ) -> None:
        usage_dict: dict[str, Any] = {}
        if usage is not None:
            usage_dict = {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            }
        self._emit(
            "llm_response",
            {
                "content": content,
                "usage": usage_dict,
            },
            latency_ms=latency_ms,
        )

    def log_subagent_spawn(
        self,
        subagent_name: str,
        instructions: str,
        result: dict[str, Any],
    ) -> None:
        self._emit(
            "subagent_spawn",
            {
                "subagent_name": subagent_name,
                "instructions": instructions[:2000],
                "result": result,
            },
            tool_name=subagent_name,
        )

    def log_error(self, message: str, exception: Exception | None = None) -> None:
        payload: dict[str, Any] = {"message": message}
        if exception is not None:
            payload["exception"] = repr(exception)
        self._emit("error", payload)
