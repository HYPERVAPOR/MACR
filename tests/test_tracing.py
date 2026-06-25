"""Tests for the tracing layer."""

from __future__ import annotations

from macr.tracing.jsonl_store import JsonlTraceStore
from macr.tracing.models import TraceEvent, TraceRun
from macr.tracing.sqlite_store import SQLiteTraceStore
from macr.tracing.trace_logger import TraceLogger


def test_jsonl_store_round_trip(tmp_path) -> None:
    store = JsonlTraceStore(tmp_path)
    run = TraceRun(
        run_id="r1",
        bug_id="bug1",
        configuration="Baseline",
        model="fake",
        started_at="2026-01-01T00:00:00Z",
        ended_at="2026-01-01T00:01:00Z",
        status="success",
        metrics={"plausible": True},
    )
    store.save_run(run)

    event = TraceEvent(
        event_id="e1",
        run_id="r1",
        timestamp="2026-01-01T00:00:30Z",
        event_type="react_step",
        step_number=1,
        tool_name="direct_patch",
        payload={"thought": "test"},
    )
    store.append_event(event)

    retrieved_run = store.get_run("r1")
    assert retrieved_run is not None
    assert retrieved_run.bug_id == "bug1"

    events = store.get_events("r1")
    assert len(events) == 1
    assert events[0].event_type == "react_step"
    assert events[0].payload["thought"] == "test"


def test_sqlite_store_round_trip(tmp_path) -> None:
    store = SQLiteTraceStore(tmp_path)
    run = TraceRun(
        run_id="r2",
        bug_id="bug2",
        configuration="MACR",
        model="fake",
        started_at="2026-01-01T00:00:00Z",
        ended_at="2026-01-01T00:01:00Z",
        status="success",
        metrics={"plausible": True},
    )
    store.save_run(run)

    logger = TraceLogger(
        run_id="r2",
        bug_id="bug2",
        configuration="MACR",
        model="fake",
        store=store,
    )
    logger.log_run_start()
    logger.log_react_step(
        step_number=1,
        thought="Generate patch",
        tool_name="direct_patch",
        tool_input={"buggy_code": "code"},
        observation={"success": True},
    )
    logger.log_run_end("success", {"attempts": 1})

    retrieved_run = store.get_run("r2")
    assert retrieved_run is not None
    assert retrieved_run.status == "success"

    events = store.get_events("r2")
    event_types = [e.event_type for e in events]
    assert "run_start" in event_types
    assert "react_step" in event_types
    assert "run_end" in event_types

    store.close()


def test_trace_logger_emits_events(tmp_path) -> None:
    store = JsonlTraceStore(tmp_path)
    logger = TraceLogger(
        run_id="r3",
        bug_id="bug3",
        configuration="Test",
        model="fake",
        store=store,
    )
    logger.log_run_start()
    logger.log_llm_request([{"role": "user", "content": "hi"}])
    logger.log_llm_response("hello", None, 123.0)
    logger.log_subagent_spawn(
        subagent_name="explore",
        instructions="find bug",
        result={"summary": "found"},
    )
    logger.log_run_end("success", {"attempts": 2})

    events = store.get_events("r3")
    event_types = {e.event_type for e in events}
    assert event_types >= {"run_start", "llm_request", "llm_response", "subagent_spawn", "run_end"}
