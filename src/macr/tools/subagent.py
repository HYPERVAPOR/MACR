"""Tool wrapper that delegates to a MACR subagent."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from macr.agents.protocol import RepairContext

if TYPE_CHECKING:
    from macr.tracing.trace_logger import TraceLogger
from macr.agents.subagent import Subagent
from macr.tools.base import Observation, Tool


class SubagentTool(Tool):
    """Spawn an isolated subagent and return its summary result."""

    def __init__(
        self,
        subagent: Subagent,
        trace_logger: TraceLogger | None = None,
    ) -> None:
        self._subagent = subagent
        self._trace_logger = trace_logger

    @property
    def name(self) -> str:
        return self._subagent.config.name

    @property
    def description(self) -> str:
        return self._subagent.config.description

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "context": "RepairContext: isolated repair context for the subagent",
            "instructions": "str (optional): extra instructions, e.g. previous results or the patch to validate",
            "previous_results": "list[dict] (optional): previous subagent/tool results to include as context",
        }

    def run(self, inputs: dict[str, Any]) -> Observation:
        raw_context = inputs.get("context")
        if not isinstance(raw_context, RepairContext):
            return Observation(
                success=False,
                error_message="Missing or invalid RepairContext in subagent input.",
            )

        instructions = inputs.get("instructions", "")
        previous_results = inputs.get("previous_results", []) or []

        # Build an isolated context: same task info, but no main ReAct memory.
        isolated_context = RepairContext(
            bug_id=raw_context.bug_id,
            language=raw_context.language,
            buggy_code=raw_context.buggy_code,
            test_code=raw_context.test_code,
            issue_description=raw_context.issue_description,
            file_path=raw_context.file_path,
            kg_context=raw_context.kg_context,
        )

        full_instructions = self._format_instructions(instructions, previous_results)

        try:
            result = self._subagent.run(isolated_context, instructions=full_instructions)
            if self._trace_logger is not None:
                self._trace_logger.log_subagent_spawn(
                    subagent_name=self.name,
                    instructions=full_instructions,
                    result=result.model_dump(),
                )
            return Observation(
                success=True,
                output=result.summary,
                structured_output=result.structured_output,
                reasoning=result.reasoning,
            )
        except Exception as exc:  # pragma: no cover
            return Observation(
                success=False,
                output=str(exc),
                error_message=f"Subagent '{self.name}' failed: {exc}",
            )

    @staticmethod
    def _format_instructions(instructions: str, previous_results: list[Any]) -> str:
        parts = []
        if instructions:
            parts.append(instructions)
        if previous_results:
            parts.append("Previous results:")
            for idx, item in enumerate(previous_results, 1):
                summary = item.get("output", "") if isinstance(item, dict) else str(item)
                parts.append(f"  [{idx}] {summary[:500]}")
        return "\n\n".join(parts)
