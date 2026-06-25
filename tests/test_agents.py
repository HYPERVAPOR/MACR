"""Tests for the agent orchestration."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from macr.agents.coordinator import CoordinatorAgent
from macr.agents.protocol import ReActAction, RepairContext
from macr.agents.subagent import Subagent, SubagentConfig, SubagentRegistry
from macr.llm.base import LLMBackend
from macr.tools.base import ToolRegistry
from macr.tools.direct_patch import DirectPatchTool
from macr.tools.subagent import SubagentTool


class FakeLLMBackend(LLMBackend):
    """In-memory LLM backend for testing."""

    def __init__(self, responses: list[str | BaseModel]) -> None:
        self._responses = list(responses)
        self._index = 0

    @property
    def model_name(self) -> str:
        return "fake"

    def with_model(self, model: str | None) -> FakeLLMBackend:
        return self

    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        response_format: type[Any] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        **kwargs: Any,
    ) -> str | Any:
        if self._index >= len(self._responses):
            raise RuntimeError("No more fake responses")
        response = self._responses[self._index]
        self._index += 1
        return response


def test_subagent_extracts_patch() -> None:
    backend = FakeLLMBackend([
        "The bug is in the recursive call.\n"
        "```python\n"
        "def fib(n):\n"
        "    if n <= 1:\n"
        "        return n\n"
        "    return fib(n - 1) + fib(n - 2)\n"
        "```"
    ])
    config = SubagentConfig(
        name="generate_patch",
        description="Generate a patch",
        system_prompt="You are a repair expert.",
        tools=[],
    )
    subagent = Subagent(config, backend, ToolRegistry())
    context = RepairContext(
        bug_id="fib",
        language="python",
        buggy_code="def fib(n): return fib(n-1)\n",
        test_code="assert fib(5) == 5",
    )
    result = subagent.run(context)
    assert "fib(n - 2)" in result.structured_output["patched_code"]


def test_subagent_tool_isolates_context() -> None:
    backend = FakeLLMBackend([
        "```python\ndef add(a, b):\n    return a + b\n```"
    ])
    config = SubagentConfig(
        name="generate_patch",
        description="Generate a patch",
        system_prompt="You are a repair expert.",
        tools=[],
    )
    subagent = Subagent(config, backend, ToolRegistry())
    tool = SubagentTool(subagent)

    context = RepairContext(
        bug_id="add",
        language="python",
        buggy_code="def add(a, b): return a - b\n",
        test_code="assert add(1, 2) == 3",
    )
    observation = tool.run({"context": context})
    assert observation.success
    assert "a + b" in observation.structured_output["patched_code"]


def test_subagent_registry_builds_tools() -> None:
    backend = FakeLLMBackend([])
    base_tools = ToolRegistry()
    registry = SubagentRegistry(backend, base_tools)
    tools = registry.build_tools()
    names = {tool.name for tool in tools}
    assert names >= {"localize", "generate_patch", "validate_patch"}


def test_coordinator_baseline_mode() -> None:
    backend = FakeLLMBackend([
        ReActAction(
            thought="Generate a patch directly.",
            tool_name="direct_patch",
            tool_input={"buggy_code": "def add(a, b): return a - b\n"},
        ),
        "```python\n"
        "def add(a, b):\n"
        "    return a + b\n"
        "```",
    ])

    registry = ToolRegistry()
    registry.register(DirectPatchTool(backend))

    coordinator = CoordinatorAgent(backend, registry)
    context = RepairContext(
        bug_id="add",
        language="python",
        buggy_code="def add(a, b): return a - b\n",
        test_code="assert add(1, 2) == 3",
    )
    result = coordinator.repair(context)
    assert result.status == "success"
    assert result.patch is not None
    assert "a + b" in result.patch.patched_code
