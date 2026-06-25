"""Build a code knowledge graph from source files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import networkx as nx
from tree_sitter import Language, Parser, Tree
from tree_sitter_java import language as java_language
from tree_sitter_python import language as python_language

from macr.knowledge_graph.entities import Entity, EntityType, Relation, RelationType

logger = logging.getLogger(__name__)

LANGUAGE_MAP: dict[str, Language] = {
    ".py": Language(python_language()),
    ".java": Language(java_language()),
}


def _get_text(node: Any, source: bytes) -> str:
    """Extract source text covered by a tree-sitter node."""
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _node_id(file_path: str, entity_type: EntityType, name: str, line: int) -> str:
    return f"{file_path}::{entity_type.value}::{name}::{line}"


class KnowledgeGraphBuilder:
    """Build a knowledge graph from a codebase."""

    def __init__(self) -> None:
        self._graph: nx.DiGraph = nx.DiGraph()
        self._parsers: dict[str, Parser] = {}

    def _get_parser(self, extension: str) -> Parser | None:
        if extension not in LANGUAGE_MAP:
            return None
        if extension not in self._parsers:
            self._parsers[extension] = Parser(LANGUAGE_MAP[extension])
        return self._parsers[extension]

    def build_from_directory(self, directory: str | Path) -> nx.DiGraph:
        """Build a knowledge graph from all supported files in a directory."""
        self._graph = nx.DiGraph()
        directory = Path(directory)

        for ext in LANGUAGE_MAP:
            for file_path in directory.rglob(f"*{ext}"):
                try:
                    self._add_file(file_path)
                except Exception:
                    logger.exception("Failed to parse %s", file_path)

        return self._graph

    def build_from_files(self, files: list[str | Path]) -> nx.DiGraph:
        """Build a knowledge graph from an explicit list of source files."""
        self._graph = nx.DiGraph()
        for file_path in files:
            try:
                self._add_file(Path(file_path))
            except Exception:
                logger.exception("Failed to parse %s", file_path)
        return self._graph

    def _add_file(self, file_path: Path) -> None:
        extension = file_path.suffix
        parser = self._get_parser(extension)
        if parser is None:
            return

        source = file_path.read_bytes()
        tree = parser.parse(source)

        file_entity = Entity(
            id=str(file_path),
            type=EntityType.FILE,
            name=file_path.name,
            file_path=str(file_path),
            line_start=1,
            line_end=source.count(b"\n") + 1,
            metadata={"language": extension.lstrip(".")},
        )
        self._add_entity(file_entity)

        if extension == ".py":
            self._walk_python(file_entity, tree, source)
        elif extension == ".java":
            self._walk_java(file_entity, tree, source)

    def _add_entity(self, entity: Entity) -> None:
        self._graph.add_node(
            entity.id,
            type=entity.type.value,
            name=entity.name,
            file_path=entity.file_path,
            line_start=entity.line_start,
            line_end=entity.line_end,
            metadata=entity.metadata,
        )

    def _add_relation(self, relation: Relation) -> None:
        if relation.source not in self._graph or relation.target not in self._graph:
            return
        self._graph.add_edge(
            relation.source,
            relation.target,
            type=relation.type.value,
            metadata=relation.metadata,
        )

    # ------------------------------------------------------------------
    # Python walker
    # ------------------------------------------------------------------
    def _walk_python(self, file_entity: Entity, tree: Tree, source: bytes) -> None:
        function_nodes: list[tuple[Any, Entity]] = []
        class_nodes: list[tuple[Any, Entity]] = []

        def visit(node: Any) -> None:
            if node.type == "function_definition":
                name_node = next((c for c in node.children if c.type == "identifier"), None)
                if name_node:
                    name = _get_text(name_node, source)
                    entity = Entity(
                        id=_node_id(file_entity.file_path, EntityType.FUNCTION, name, name_node.start_point[0] + 1),
                        type=EntityType.FUNCTION,
                        name=name,
                        file_path=file_entity.file_path,
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1,
                        metadata={"signature": _get_text(node.child_by_field_name("parameters"), source)},
                    )
                    self._add_entity(entity)
                    self._add_relation(Relation(file_entity.id, entity.id, RelationType.CONTAINS))
                    function_nodes.append((node, entity))

            elif node.type == "class_definition":
                name_node = next((c for c in node.children if c.type == "identifier"), None)
                if name_node:
                    name = _get_text(name_node, source)
                    entity = Entity(
                        id=_node_id(file_entity.file_path, EntityType.CLASS, name, name_node.start_point[0] + 1),
                        type=EntityType.CLASS,
                        name=name,
                        file_path=file_entity.file_path,
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1,
                    )
                    self._add_entity(entity)
                    self._add_relation(Relation(file_entity.id, entity.id, RelationType.CONTAINS))
                    class_nodes.append((node, entity))

            elif node.type == "import_statement":
                text = _get_text(node, source).strip()
                entity = Entity(
                    id=_node_id(file_entity.file_path, EntityType.IMPORT, text, node.start_point[0] + 1),
                    type=EntityType.IMPORT,
                    name=text,
                    file_path=file_entity.file_path,
                    line_start=node.start_point[0] + 1,
                    line_end=node.end_point[0] + 1,
                )
                self._add_entity(entity)
                self._add_relation(Relation(file_entity.id, entity.id, RelationType.IMPORTS))

            for child in node.children:
                visit(child)

        visit(tree.root_node)

        # Resolve calls and class-method ownership
        for func_node, func_entity in function_nodes:
            self._collect_python_calls(func_node, func_entity, function_nodes, class_nodes, source)

        for class_node, class_entity in class_nodes:
            for child in class_node.children:
                if child.type == "block":
                    for member in child.children:
                        if member.type == "function_definition":
                            for fn_node, fn_entity in function_nodes:
                                if fn_node is member:
                                    self._add_relation(Relation(class_entity.id, fn_entity.id, RelationType.DEFINES))

    def _collect_python_calls(
        self,
        func_node: Any,
        func_entity: Entity,
        all_functions: list[tuple[Any, Entity]],
        all_classes: list[tuple[Any, Entity]],
        source: bytes,
    ) -> None:
        def visit(node: Any) -> None:
            if node.type == "call":
                called_name = self._resolve_python_called_name(node, source)
                if called_name:
                    # Try to find an exact match in the same file
                    for _, target_entity in all_functions:
                        if target_entity.name == called_name:
                            self._add_relation(
                                Relation(func_entity.id, target_entity.id, RelationType.CALLS)
                            )
                            break
            for child in node.children:
                visit(child)

        visit(func_node)

    @staticmethod
    def _resolve_python_called_name(call_node: Any, source: bytes) -> str | None:
        func_node = call_node.child_by_field_name("function")
        if func_node is None:
            return None
        if func_node.type == "identifier":
            return _get_text(func_node, source)
        if func_node.type == "attribute":
            # Take the last attribute identifier as a best-effort name
            last = func_node.children[-1]
            if last.type == "identifier":
                return _get_text(last, source)
        return None

    # ------------------------------------------------------------------
    # Java walker (simplified)
    # ------------------------------------------------------------------
    def _walk_java(self, file_entity: Entity, tree: Tree, source: bytes) -> None:
        function_nodes: list[tuple[Any, Entity]] = []
        class_nodes: list[tuple[Any, Entity]] = []

        def visit(node: Any) -> None:
            if node.type == "method_declaration":
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = _get_text(name_node, source)
                    entity = Entity(
                        id=_node_id(file_entity.file_path, EntityType.FUNCTION, name, name_node.start_point[0] + 1),
                        type=EntityType.FUNCTION,
                        name=name,
                        file_path=file_entity.file_path,
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1,
                    )
                    self._add_entity(entity)
                    self._add_relation(Relation(file_entity.id, entity.id, RelationType.CONTAINS))
                    function_nodes.append((node, entity))

            elif node.type == "class_declaration":
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = _get_text(name_node, source)
                    entity = Entity(
                        id=_node_id(file_entity.file_path, EntityType.CLASS, name, name_node.start_point[0] + 1),
                        type=EntityType.CLASS,
                        name=name,
                        file_path=file_entity.file_path,
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1,
                    )
                    self._add_entity(entity)
                    self._add_relation(Relation(file_entity.id, entity.id, RelationType.CONTAINS))
                    class_nodes.append((node, entity))

            for child in node.children:
                visit(child)

        visit(tree.root_node)

        for func_node, func_entity in function_nodes:
            self._collect_java_calls(func_node, func_entity, function_nodes, source)

    def _collect_java_calls(
        self,
        func_node: Any,
        func_entity: Entity,
        all_functions: list[tuple[Any, Entity]],
        source: bytes,
    ) -> None:
        def visit(node: Any) -> None:
            if node.type == "method_invocation":
                name_node = node.child_by_field_name("name")
                if name_node:
                    called_name = _get_text(name_node, source)
                    for _, target_entity in all_functions:
                        if target_entity.name == called_name:
                            self._add_relation(
                                Relation(func_entity.id, target_entity.id, RelationType.CALLS)
                            )
                            break
            for child in node.children:
                visit(child)

        visit(func_node)
