"""Query interface for the code knowledge graph."""

from __future__ import annotations

from typing import Any, cast

import networkx as nx

from macr.knowledge_graph.entities import EntityType, RelationType


class KnowledgeGraphQuery:
    """High-level queries over a code knowledge graph."""

    def __init__(self, graph: nx.DiGraph) -> None:
        self._graph = graph

    def get_entity(self, entity_id: str) -> dict[str, Any] | None:
        """Return node data for a given entity id."""
        return cast(dict[str, Any] | None, self._graph.nodes.get(entity_id))

    def find_functions(self, name: str | None = None, file_path: str | None = None) -> list[dict[str, Any]]:
        """Find functions by optional name and file path filters."""
        results = []
        for node_id, data in self._graph.nodes(data=True):
            if data.get("type") != EntityType.FUNCTION.value:
                continue
            if name is not None and data.get("name") != name:
                continue
            if file_path is not None and data.get("file_path") != file_path:
                continue
            results.append(dict(data, id=node_id))
        return results

    def find_callers(self, function_id: str) -> list[dict[str, Any]]:
        """Return functions that call the given function."""
        callers = []
        for source, _, edge_data in self._graph.in_edges(function_id, data=True):
            if edge_data.get("type") == RelationType.CALLS.value:
                data = self._graph.nodes[source]
                if data.get("type") == EntityType.FUNCTION.value:
                    callers.append(dict(data, id=source))
        return callers

    def find_callees(self, function_id: str) -> list[dict[str, Any]]:
        """Return functions called by the given function."""
        callees = []
        for _, target, edge_data in self._graph.out_edges(function_id, data=True):
            if edge_data.get("type") == RelationType.CALLS.value:
                data = self._graph.nodes[target]
                if data.get("type") == EntityType.FUNCTION.value:
                    callees.append(dict(data, id=target))
        return callees

    def get_related_functions(self, function_id: str, depth: int = 1) -> list[dict[str, Any]]:
        """Return functions within `depth` hops of the given function via calls."""
        related: set[str] = set()
        visited: set[str] = {function_id}
        frontier = {function_id}

        for _ in range(depth):
            next_frontier: set[str] = set()
            for node in frontier:
                for neighbor in nx.all_neighbors(self._graph, node):
                    edge_data = self._graph.get_edge_data(node, neighbor) or self._graph.get_edge_data(neighbor, node)
                    if edge_data and edge_data.get("type") == RelationType.CALLS.value:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            next_frontier.add(neighbor)
                            data = self._graph.nodes[neighbor]
                            if data.get("type") == EntityType.FUNCTION.value:
                                related.add(neighbor)
            frontier = next_frontier

        return [dict(self._graph.nodes[n], id=n) for n in related]

    def summarize_for_function(self, function_id: str) -> str:
        """Create a textual summary of a function and its immediate neighbors."""
        data = self._graph.nodes.get(function_id)
        if data is None:
            return ""

        lines = [
            f"Function: {data.get('name')} ({data.get('file_path')}:{data.get('line_start')})",
        ]

        callees = self.find_callees(function_id)
        if callees:
            lines.append("Calls:")
            for callee in callees:
                lines.append(f"  - {callee['name']} ({callee['file_path']}:{callee['line_start']})")

        callers = self.find_callers(function_id)
        if callers:
            lines.append("Called by:")
            for caller in callers:
                lines.append(f"  - {caller['name']} ({caller['file_path']}:{caller['line_start']})")

        return "\n".join(lines)

    def to_context(self, function_id: str, depth: int = 1) -> dict[str, Any]:
        """Export a function-centric context bundle for an Agent."""
        data = self.get_entity(function_id)
        if data is None:
            return {}
        return {
            "target": dict(data, id=function_id),
            "related_functions": self.get_related_functions(function_id, depth=depth),
            "callers": self.find_callers(function_id),
            "callees": self.find_callees(function_id),
        }
