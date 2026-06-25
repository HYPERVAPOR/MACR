"""Data models for MACR tracing."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TraceRun(BaseModel):
    """Summary of a single repair run."""

    run_id: str
    bug_id: str
    configuration: str = ""
    model: str = ""
    started_at: str
    ended_at: str | None = None
    status: str | None = None
    metrics: dict[str, Any] | None = None


class TraceEvent(BaseModel):
    """A single trace event within a repair run."""

    event_id: str
    run_id: str
    parent_span_id: str | None = None
    timestamp: str
    event_type: str = Field(
        ...,
        description="One of: run_start, run_end, react_step, tool_call, tool_result, "
        "llm_request, llm_response, subagent_spawn, error",
    )
    step_number: int | None = None
    tool_name: str | None = None
    latency_ms: float | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
