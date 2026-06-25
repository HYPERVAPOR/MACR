"""Analyze trace files to produce debugging and cost statistics."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))



def _load_runs(trace_dir: Path) -> list[dict]:
    runs_path = trace_dir / "runs.jsonl"
    if not runs_path.exists():
        return []
    runs: list[dict] = []
    with runs_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                runs.append(json.loads(line))
    return runs


def _load_events(trace_dir: Path) -> list[dict]:
    events_path = trace_dir / "events.jsonl"
    if not events_path.exists():
        return []
    events: list[dict] = []
    with events_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze MACR traces")
    parser.add_argument("--trace-dir", type=str, default="outputs/traces", help="Trace directory")
    parser.add_argument("--run-id", type=str, default=None, help="Focus on a single run")
    args = parser.parse_args()

    trace_dir = Path(args.trace_dir)
    runs = _load_runs(trace_dir)
    events = _load_events(trace_dir)

    if args.run_id:
        events = [e for e in events if e["run_id"] == args.run_id]

    # Aggregate by configuration
    by_config: dict[str, dict] = defaultdict(
        lambda: {
            "runs": 0,
            "success": 0,
            "llm_calls": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "tools_used": defaultdict(int),
            "subagents_used": defaultdict(int),
        }
    )

    run_config: dict[str, str] = {}
    for run in runs:
        run_config[run["run_id"]] = run.get("configuration", "unknown")
        cfg = run_config[run["run_id"]]
        by_config[cfg]["runs"] += 1
        if run.get("status") == "success":
            by_config[cfg]["success"] += 1

    for event in events:
        cfg = run_config.get(event["run_id"], "unknown")
        if event["event_type"] == "llm_response":
            by_config[cfg]["llm_calls"] += 1
            usage = event.get("payload", {}).get("usage") or {}
            by_config[cfg]["prompt_tokens"] += usage.get("prompt_tokens") or 0
            by_config[cfg]["completion_tokens"] += usage.get("completion_tokens") or 0
            by_config[cfg]["total_tokens"] += usage.get("total_tokens") or 0
        elif event["event_type"] == "react_step":
            tool_name = event.get("tool_name")
            if tool_name:
                by_config[cfg]["tools_used"][tool_name] += 1
        elif event["event_type"] == "subagent_spawn":
            subagent = event.get("payload", {}).get("subagent_name", "unknown")
            by_config[cfg]["subagents_used"][subagent] += 1

    print(f"\nTrace analysis from {trace_dir}")
    print(f"Total runs: {len(runs)}, total events: {len(events)}")
    print("-" * 90)
    print(
        f"{'Config':<30} {'Runs':>6} {'Success':>8} {'LLM calls':>10} "
        f"{'Tokens':>10} {'Tools / Subagents'}")
    print("-" * 90)
    for cfg, stats in sorted(by_config.items()):
        tools = ", ".join(f"{k}={v}" for k, v in stats["tools_used"].items())
        subagents = ", ".join(f"{k}={v}" for k, v in stats["subagents_used"].items())
        print(
            f"{cfg:<30} {stats['runs']:>6} {stats['success']:>8} {stats['llm_calls']:>10} "
            f"{stats['total_tokens']:>10} {tools or '-'} | {subagents or '-'}"
        )


if __name__ == "__main__":
    main()
