"""Subagent runtime for MACR."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from macr.agents.coordinator import CoordinatorAgent
from macr.agents.protocol import RepairContext, RepairResult, SubagentResult
from macr.agents.subagent_loader import SubagentConfig, load_subagent_configs
from macr.llm.base import LLMBackend
from macr.repair.patch import PatchCandidate, extract_first_code_block
from macr.tools.base import Tool, ToolRegistry

if TYPE_CHECKING:
    from macr.tracing.trace_logger import TraceLogger

logger = logging.getLogger(__name__)


class Subagent:
    """A configurable subagent that can be delegated to by the main coordinator."""

    def __init__(
        self,
        config: SubagentConfig,
        base_backend: LLMBackend,
        base_tools: ToolRegistry,
    ) -> None:
        self._config = config
        self._backend = base_backend.with_model(config.model)
        self._tools = self._build_filtered_registry(base_tools)

    @property
    def config(self) -> SubagentConfig:
        return self._config

    def _build_filtered_registry(self, base_tools: ToolRegistry) -> ToolRegistry:
        """Create a tool registry containing only the subagent's allowed tools."""
        registry = ToolRegistry()
        allowed = set(self._config.tools)
        if not allowed:
            return registry
        for tool in base_tools.list_tools():
            if tool.name in allowed:
                registry.register(tool)
        return registry

    def run(self, context: RepairContext, instructions: str = "") -> SubagentResult:
        """Run the subagent on an isolated task and return a summary."""
        if not self._config.tools:
            return self._run_single_turn(context, instructions)
        return self._run_with_tools(context, instructions)

    def _run_single_turn(self, context: RepairContext, instructions: str) -> SubagentResult:
        """Run a single LLM call without tool use."""
        messages = [
            {"role": "system", "content": self._config.system_prompt},
            {"role": "user", "content": self._build_user_prompt(context, instructions)},
        ]
        try:
            output = self._backend.chat(messages)
            text = output if isinstance(output, str) else str(output)
            structured = self._extract_structured(text, context)
            return SubagentResult(
                summary=text[:2000],
                structured_output=structured,
                reasoning=f"Completed by single-turn subagent '{self._config.name}'",
                confidence=None,
            )
        except Exception as exc:  # pragma: no cover
            logger.exception("Single-turn subagent %s failed", self._config.name)
            return SubagentResult(
                summary=f"Subagent failed: {exc}",
                reasoning="Unhandled error",
                confidence="low",
            )

    def _run_with_tools(self, context: RepairContext, instructions: str) -> SubagentResult:
        """Run a short internal ReAct loop with the subagent's allowed tools."""
        coordinator = CoordinatorAgent(
            self._backend,
            self._tools,
            max_steps=self._config.max_steps,
        )
        try:
            result = coordinator.repair(context)
        except Exception as exc:  # pragma: no cover
            logger.exception("Subagent %s ReAct loop failed", self._config.name)
            return SubagentResult(
                summary=f"Subagent ReAct loop failed: {exc}",
                reasoning="Unhandled error",
                confidence="low",
            )

        structured: dict[str, Any] = {}
        if result.patch:
            structured = result.patch.model_dump()

        summary = self._synthesize_summary(result)
        confidence = self._infer_confidence(result)

        return SubagentResult(
            summary=summary,
            structured_output=structured,
            reasoning=f"Completed by subagent '{self._config.name}' in {result.attempts} step(s)",
            confidence=confidence,
        )

    def _build_user_prompt(self, context: RepairContext, instructions: str) -> str:
        """Build the isolated user prompt for the subagent."""
        lines = [
            f"Bug ID: {context.bug_id}",
            f"Language: {context.language}",
            f"Issue description: {context.issue_description or 'N/A'}",
            f"Buggy code:\n```\n{context.buggy_code}\n```",
        ]
        if context.test_code:
            lines.append(f"Test code:\n```\n{context.test_code}\n```")
        if context.kg_context:
            lines.append(
                f"Knowledge graph context: {json.dumps(context.kg_context, ensure_ascii=False)}"
            )
        if instructions:
            lines.append(f"Instructions:\n{instructions}")
        return "\n\n".join(lines)

    def _extract_structured(self, text: str, context: RepairContext) -> dict[str, Any]:
        """Try to extract a patch or verdict from raw text."""
        patched_code = extract_first_code_block(text)
        if patched_code:
            return PatchCandidate(buggy_code=context.buggy_code, patched_code=patched_code).model_dump()

        upper = text.upper()
        if "VALID" in upper or "INVALID" in upper or "UNCERTAIN" in upper:
            verdict = "UNCERTAIN"
            if "VALID" in upper:
                verdict = "VALID"
            elif "INVALID" in upper:
                verdict = "INVALID"
            return {"verdict": verdict}

        return {}

    def _synthesize_summary(self, result: RepairResult) -> str:
        """Create a concise summary from a subagent RepairResult."""
        if result.error_message:
            return f"Subagent finished with error: {result.error_message}"
        if result.patch and result.patch.explanation:
            return result.patch.explanation[:2000]
        if result.steps:
            last_obs = result.steps[-1].get("observation", {})
            output = last_obs.get("output", "")
            if output:
                return str(output)[:2000]
        return "Subagent completed without detailed output."

    def _infer_confidence(self, result: RepairResult) -> str | None:
        """Infer confidence from the subagent result."""
        if result.status != "success":
            return "low"
        if result.patch:
            return "high"
        return "medium"


class SubagentRegistry:
    """Registry that loads subagent configs and exposes them as tools."""

    def __init__(
        self,
        base_backend: LLMBackend,
        base_tools: ToolRegistry,
        configs: dict[str, SubagentConfig] | None = None,
    ) -> None:
        self._base_backend = base_backend
        self._base_tools = base_tools
        self._configs = configs if configs is not None else load_subagent_configs()
        self._subagents: dict[str, Subagent] = {
            name: Subagent(cfg, base_backend, base_tools)
            for name, cfg in self._configs.items()
        }

    def list_subagents(self) -> list[SubagentConfig]:
        return list(self._configs.values())

    def get(self, name: str) -> Subagent | None:
        return self._subagents.get(name)

    def build_tools(
        self,
        trace_logger: TraceLogger | None = None,
    ) -> list[Tool]:
        """Build a SubagentTool wrapper for each loaded subagent."""
        from macr.tools.subagent import SubagentTool

        return [
            SubagentTool(subagent, trace_logger=trace_logger)
            for subagent in self._subagents.values()
        ]
