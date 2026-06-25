"""End-to-end repair pipeline."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any, cast

from macr.agents.coordinator import CoordinatorAgent
from macr.agents.protocol import RepairContext
from macr.agents.subagent import SubagentRegistry
from macr.config import get_settings
from macr.datasets.base import BugDataset, BugSample
from macr.knowledge_graph.builder import KnowledgeGraphBuilder
from macr.knowledge_graph.query import KnowledgeGraphQuery
from macr.llm.base import LLMBackend
from macr.tools.base import ToolRegistry
from macr.tools.direct_patch import DirectPatchTool
from macr.tools.query_kg import QueryKGTool
from macr.tools.run_tests import RunTestsTool
from macr.tracing.sqlite_store import SQLiteTraceStore
from macr.tracing.trace_logger import TraceLogger

logger = logging.getLogger(__name__)


class RepairPipeline:
    """Orchestrates repair and evaluation for a single bug sample."""

    def __init__(
        self,
        backend: LLMBackend,
        dataset: BugDataset | None = None,
        *,
        use_knowledge_graph: bool = True,
        use_sub_agents: bool = True,
        max_steps: int = 5,
        configuration: str = "",
    ) -> None:
        self._backend = backend
        self._dataset = dataset
        self._use_kg = use_knowledge_graph
        self._use_sub_agents = use_sub_agents
        self._max_steps = max_steps
        self._configuration = configuration

    def run(self, sample: BugSample) -> dict[str, Any]:
        """Run the full repair-evaluation loop for one bug."""
        run_id = uuid.uuid4().hex
        trace_logger = self._create_trace_logger(run_id, sample)
        self._backend.trace_logger = trace_logger

        kg_context = self._build_kg_context(sample) if self._use_kg else None

        context = RepairContext(
            bug_id=sample.bug_id,
            language=sample.language,
            buggy_code=sample.buggy_code,
            test_code=sample.test_code,
            issue_description=sample.metadata.get("issue_description") if sample.metadata else None,
            file_path=sample.file_path,
            kg_context=kg_context,
        )

        tool_registry = self._build_tool_registry(context, trace_logger)
        coordinator = CoordinatorAgent(
            self._backend,
            tool_registry,
            max_steps=self._max_steps,
            trace_logger=trace_logger,
        )

        trace_logger.log_run_start()
        repair_result = coordinator.repair(context)

        result = {
            "bug_id": sample.bug_id,
            "status": repair_result.status,
            "patch_generated": repair_result.patch is not None,
            "patch": repair_result.patch.model_dump() if repair_result.patch else None,
            "attempts": repair_result.attempts,
            "steps": repair_result.steps,
            "evaluation": None,
            "trace_run_id": run_id,
        }

        metrics = {
            "status": repair_result.status,
            "attempts": repair_result.attempts,
            "patch_generated": repair_result.patch is not None,
        }
        trace_logger.log_run_end(repair_result.status, metrics)
        return result

    def _create_trace_logger(self, run_id: str, sample: BugSample) -> TraceLogger:
        from macr.tracing.base import TraceStore
        from macr.tracing.jsonl_store import JsonlTraceStore

        settings = get_settings()
        trace_store_setting = settings.trace_store.lower()
        store: TraceStore
        if trace_store_setting == "sqlite":
            store = SQLiteTraceStore(settings.trace_dir)
        else:
            store = JsonlTraceStore(settings.trace_dir)

        return TraceLogger(
            run_id=run_id,
            bug_id=sample.bug_id,
            configuration=self._configuration,
            model=self._backend.model_name,
            store=store,
        )

    def _build_tool_registry(
        self,
        context: RepairContext,
        trace_logger: TraceLogger | None,
    ) -> ToolRegistry:
        """Build the tool registry based on configuration."""
        registry = ToolRegistry()
        kg_files = self._kg_source_files(context.file_path)

        # Always available: direct patch generation.
        registry.register(DirectPatchTool(self._backend))

        # Knowledge graph tool.
        if self._use_kg and kg_files:
            registry.register(QueryKGTool(kg_files))

        # Test execution tool (requires dataset).
        if self._dataset is not None:
            sample = self._dataset.get(context.bug_id)
            if sample is not None:
                registry.register(RunTestsTool(self._dataset, sample))

        # Subagent tools.
        if self._use_sub_agents:
            subagent_registry = SubagentRegistry(self._backend, registry)
            for tool in subagent_registry.build_tools(trace_logger=trace_logger):
                registry.register(tool)

        return registry

    def _kg_source_files(self, file_path: str | None) -> list[str]:
        """Return all Python source files in the same directory as the buggy file."""
        if not file_path:
            return []
        directory = Path(file_path).parent
        return [str(p) for p in sorted(directory.glob("*.py"))]

    def _build_kg_context(self, sample: BugSample) -> dict[str, Any] | None:
        """Build a knowledge graph for the sample and return target context."""
        kg_files = self._kg_source_files(sample.file_path)
        if not kg_files:
            return None

        try:
            builder = KnowledgeGraphBuilder()
            graph = builder.build_from_files(cast(list[str | Path], kg_files))
            query = KnowledgeGraphQuery(graph)
            functions = query.find_functions(file_path=sample.file_path)
            if not functions:
                return None

            target_id = functions[0]["id"]
            return query.to_context(target_id, depth=1)
        except Exception as exc:
            logger.warning("Failed to build KG context for %s: %s", sample.bug_id, exc)
            return None
