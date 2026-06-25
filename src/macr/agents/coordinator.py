"""ReAct-style coordinator agent for MACR."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from macr.agents.protocol import (
    PatchCandidate,
    ReActAction,
    RepairContext,
    RepairResult,
    Step,
)
from macr.llm.base import LLMBackend
from macr.tools.base import Observation, ToolRegistry

if TYPE_CHECKING:
    from macr.tracing.trace_logger import TraceLogger

logger = logging.getLogger(__name__)


class CoordinatorAgent:
    """ReAct coordinator that selects tools to repair a bug."""

    def __init__(
        self,
        backend: LLMBackend,
        tool_registry: ToolRegistry,
        *,
        max_steps: int = 5,
        trace_logger: TraceLogger | None = None,
    ) -> None:
        self._backend = backend
        self._tools = tool_registry
        self._max_steps = max_steps
        self._trace_logger = trace_logger

    def repair(self, context: RepairContext) -> RepairResult:
        """Run the ReAct repair loop for a single bug."""
        steps: list[Step] = []

        for step_number in range(1, self._max_steps + 1):
            action = self._choose_action(context, steps)
            observation = self._execute_action(action)

            step = Step(
                step_number=step_number,
                thought=action.thought,
                tool_name=action.tool_name,
                tool_input=action.tool_input,
                observation=observation.to_dict(),
            )
            steps.append(step)

            if self._trace_logger is not None:
                self._trace_logger.log_react_step(
                    step_number=step.step_number,
                    thought=step.thought,
                    tool_name=step.tool_name,
                    tool_input=step.tool_input,
                    observation=step.observation,
                )

            if observation.terminal:
                patch = self._extract_best_patch(steps)
                return RepairResult(
                    bug_id=context.bug_id,
                    status="success",
                    patch=patch,
                    attempts=step_number,
                    steps=[s.model_dump() for s in steps],
                )

        # Max steps reached: return the best patch found so far.
        patch = self._extract_best_patch(steps)
        return RepairResult(
            bug_id=context.bug_id,
            status="success" if patch else "failure",
            patch=patch,
            attempts=len(steps),
            steps=[s.model_dump() for s in steps],
            error_message=None if patch else "Max steps reached without a valid patch",
        )

    def _choose_action(self, context: RepairContext, steps: list[Step]) -> ReActAction:
        """Ask the LLM to choose the next tool action."""
        system = self._build_system_prompt()
        user = self._build_user_prompt(context, steps)

        try:
            response = self._backend.chat(
                [{"role": "system", "content": system}, {"role": "user", "content": user}],
                response_format=ReActAction,
            )
            if isinstance(response, ReActAction):
                return response
        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to parse ReActAction: %s", exc)

        # Fallback: if structured parsing fails, default to direct_patch.
        return ReActAction(
            thought="Falling back to direct patch generation.",
            tool_name="direct_patch",
            tool_input={
                "buggy_code": context.buggy_code,
                "test_code": context.test_code or "",
                "issue_description": context.issue_description or "",
            },
        )

    def _execute_action(self, action: ReActAction) -> Observation:
        """Execute the selected tool and return its observation."""
        tool = self._tools.get(action.tool_name)
        if tool is None:
            return Observation(
                success=False,
                error_message=f"Tool '{action.tool_name}' is not available.",
            )
        return tool.run(action.tool_input)

    def _build_system_prompt(self) -> str:
        """Build the system prompt describing the ReAct protocol and tools."""
        return (
            "You are an autonomous automated program repair agent. "
            "You solve bugs by iterating through a loop of Thought, Action, and Observation.\n\n"
            "At each step:\n"
            "1. Think: reason about the bug, available information, and what to do next.\n"
            "2. Action: choose exactly one tool from the available tools and provide its inputs.\n"
            "3. Observation: you will receive the result of the tool.\n\n"
            "Your goal is to produce a patch that passes the test suite. "
            "For complex bugs, first explore the code or query the knowledge graph; "
            "then generate a patch and run the tests to verify it. "
            "Always run run_tests after generating a candidate patch. "
            "When a patch passes tests, the run_tests tool will mark the process as finished.\n\n"
            + self._tools.to_prompt_section()
            + "\n\n"
            "Respond with a JSON object containing:\n"
            "- thought: your reasoning\n"
            "- tool_name: the exact name of the tool to call\n"
            "- tool_input: a JSON object of inputs for that tool\n"
        )

    def _build_user_prompt(self, context: RepairContext, steps: list[Step]) -> str:
        """Build the user prompt with context and history."""
        lines = [
            f"Bug ID: {context.bug_id}",
            f"Language: {context.language}",
            f"Issue description: {context.issue_description or 'N/A'}",
            f"Buggy code:\n```\n{context.buggy_code}\n```",
        ]
        if context.kg_context:
            lines.append(
                f"Knowledge graph context: {json.dumps(context.kg_context, ensure_ascii=False)}"
            )

        if steps:
            lines.append("\nPrevious steps:")
            for step in steps:
                lines.append(f"\nStep {step.step_number}:")
                lines.append(f"Thought: {step.thought}")
                lines.append(
                    f"Action: {step.tool_name}({json.dumps(step.tool_input, ensure_ascii=False)})"
                )
                obs = step.observation
                output = obs.get("output", "")
                lines.append(f"Observation: success={obs.get('success')}, output={output[:500]}")

        lines.append("\nNow decide the next action.")
        return "\n".join(lines)

    @staticmethod
    def _extract_best_patch(steps: list[Step]) -> PatchCandidate | None:
        """Extract the most recent successful patch from the step history."""
        for step in reversed(steps):
            obs = step.observation
            if not obs.get("success"):
                continue
            structured = obs.get("structured_output") or {}
            if not isinstance(structured, dict):
                continue
            patched_code = structured.get("patched_code")
            if patched_code:
                return PatchCandidate(
                    buggy_code=structured.get("buggy_code", ""),
                    patched_code=patched_code,
                )
        return None
