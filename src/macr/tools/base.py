"""Tool abstraction for MACR ReAct agent."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Observation:
    """Result returned by a tool execution."""

    success: bool = True
    output: str = ""
    structured_output: dict[str, Any] = field(default_factory=dict)
    terminal: bool = False
    reasoning: str | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "structured_output": self.structured_output,
            "terminal": self.terminal,
            "error_message": self.error_message,
        }


class Tool(ABC):
    """Abstract base class for tools available to the ReAct coordinator."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name used by the LLM to select it."""
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what the tool does."""
        raise NotImplementedError

    @property
    @abstractmethod
    def input_schema(self) -> dict[str, Any]:
        """JSON-schema-like description of expected input parameters."""
        raise NotImplementedError

    @abstractmethod
    def run(self, inputs: dict[str, Any]) -> Observation:
        """Execute the tool with the given inputs and return an observation."""
        raise NotImplementedError

    def to_tool_definition(self) -> dict[str, Any]:
        """Return a definition suitable for inclusion in the ReAct prompt."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


class ToolRegistry:
    """Registry of available tools."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def register_many(self, tools: list[Tool]) -> None:
        for tool in tools:
            self.register(tool)

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[Tool]:
        return list(self._tools.values())

    def to_prompt_section(self) -> str:
        """Render all registered tools as a prompt section."""
        lines = ["Available tools:"]
        for tool in self.list_tools():
            lines.append(f"\n### {tool.name}")
            lines.append(tool.description)
            lines.append(f"Input schema: {tool.input_schema}")
        return "\n".join(lines)
