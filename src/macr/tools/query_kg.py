"""Knowledge graph query tool."""

from __future__ import annotations

from typing import Any, cast

from macr.knowledge_graph.builder import KnowledgeGraphBuilder
from macr.knowledge_graph.query import KnowledgeGraphQuery
from macr.tools.base import Observation, Tool


class QueryKGTool(Tool):
    """Query the code knowledge graph for structural information."""

    def __init__(self, file_paths: list[str]) -> None:
        self._file_paths = file_paths
        self._query = self._build_query()

    def _build_query(self) -> KnowledgeGraphQuery | None:
        try:
            builder = KnowledgeGraphBuilder()
            graph = builder.build_from_files(cast(list[str | Any], self._file_paths))
            return KnowledgeGraphQuery(graph)
        except Exception:  # pragma: no cover
            return None

    @property
    def name(self) -> str:
        return "query_kg"

    @property
    def description(self) -> str:
        return (
            "Query the code knowledge graph. You can ask about functions, callers, callees, "
            "or related functions in the codebase."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "query_type": "str: one of [find_function, callers, callees, related, summary]",
            "function_name": "str: target function name",
            "file_path": "str (optional): restrict search to a file",
            "depth": "int (optional): depth for related functions",
        }

    def run(self, inputs: dict[str, Any]) -> Observation:
        if self._query is None:
            return Observation(
                success=False,
                error_message="Failed to build knowledge graph.",
            )

        query_type = inputs.get("query_type", "")
        function_name = inputs.get("function_name", "")
        file_path = inputs.get("file_path")
        depth = inputs.get("depth", 1)

        if not function_name:
            return Observation(
                success=False,
                error_message="Missing function_name in query.",
            )

        try:
            functions = self._query.find_functions(name=function_name, file_path=file_path)
            if not functions:
                return Observation(
                    success=False,
                    output=f"No function named '{function_name}' found.",
                )

            target_id = functions[0]["id"]
            result: dict[str, Any] = {}

            if query_type == "find_function":
                result = {"functions": functions}
            elif query_type == "callers":
                result = {"callers": self._query.find_callers(target_id)}
            elif query_type == "callees":
                result = {"callees": self._query.find_callees(target_id)}
            elif query_type == "related":
                result = {"related_functions": self._query.get_related_functions(target_id, depth=depth)}
            elif query_type == "summary":
                result = {"summary": self._query.summarize_for_function(target_id)}
            else:
                return Observation(
                    success=False,
                    error_message=f"Unknown query_type: {query_type}",
                )

            return Observation(
                success=True,
                output=str(result),
                structured_output=result,
            )
        except Exception as exc:  # pragma: no cover
            return Observation(
                success=False,
                error_message=f"KG query failed: {exc}",
            )
