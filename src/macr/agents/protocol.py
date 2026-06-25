"""Communication protocol between MACR agents."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RepairContext(BaseModel):
    """Context describing a bug to be repaired."""

    bug_id: str = Field(description="Unique bug identifier")
    language: str = Field(description="Programming language of the buggy code")
    buggy_code: str = Field(description="The buggy source code")
    test_code: str | None = Field(default=None, description="Test case(s) for the bug")
    issue_description: str | None = Field(default=None, description="Natural language bug description")
    file_path: str | None = Field(default=None, description="Path to the buggy file")
    kg_context: dict[str, Any] | None = Field(default=None, description="Optional knowledge graph context")


class TaskRequest(BaseModel):
    """A task dispatched by the coordinator to a worker agent."""

    task_id: str = Field(description="Unique task identifier")
    task_type: str = Field(description="Task type, e.g. localize, generate, validate")
    context: RepairContext = Field(description="Repair context for this task")
    instructions: str = Field(description="Specific instructions for the worker")
    previous_results: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Results from previously completed subtasks",
    )


class TaskResult(BaseModel):
    """Result returned by a worker agent."""

    task_id: str = Field(description="Task identifier matching the request")
    success: bool = Field(description="Whether the worker completed the task")
    output: str = Field(description="Primary text output from the worker")
    structured_output: dict[str, Any] | None = Field(
        default=None,
        description="Optional structured data extracted by the worker",
    )
    reasoning: str | None = Field(default=None, description="Explanation of the result")


class PatchCandidate(BaseModel):
    """A generated patch candidate."""

    buggy_code: str = Field(description="Original buggy code snippet")
    patched_code: str = Field(description="Repaired code snippet")
    explanation: str | None = Field(default=None, description="Why this patch fixes the bug")


class RepairResult(BaseModel):
    """Final output of the repair pipeline."""

    bug_id: str
    status: str = Field(description="success | failure | timeout")
    patch: PatchCandidate | None = None
    attempts: int = 0
    steps: list[dict[str, Any]] = Field(default_factory=list)
    error_message: str | None = None


class ReActAction(BaseModel):
    """A single action chosen by the ReAct coordinator."""

    thought: str = Field(description="Step-by-step reasoning about what to do next")
    tool_name: str = Field(description="Name of the tool to invoke")
    tool_input: dict[str, Any] = Field(description="Input parameters for the tool")


class Step(BaseModel):
    """One iteration of the ReAct loop."""

    step_number: int
    thought: str
    tool_name: str
    tool_input: dict[str, Any]
    observation: dict[str, Any]


class SubagentResult(BaseModel):
    """Result returned by a subagent to the main coordinator."""

    summary: str = Field(description="Concise summary of what the subagent did/found")
    structured_output: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured data extracted from the subagent output, e.g. patched_code",
    )
    reasoning: str | None = Field(default=None, description="Explanation of the result")
    confidence: str | None = Field(default=None, description="Confidence level: high/medium/low")


class SubagentTask(BaseModel):
    """Lightweight task passed to a subagent."""

    context: RepairContext = Field(description="Isolated repair context")
    instructions: str = Field(default="", description="Specific instructions for this subagent")
