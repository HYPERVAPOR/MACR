"""Entity and relation definitions for the code knowledge graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EntityType(str, Enum):
    """Types of nodes in the code knowledge graph."""

    FILE = "file"
    CLASS = "class"
    FUNCTION = "function"
    VARIABLE = "variable"
    IMPORT = "import"


class RelationType(str, Enum):
    """Types of edges in the code knowledge graph."""

    CONTAINS = "contains"
    DEFINES = "defines"
    CALLS = "calls"
    INHERITS = "inherits"
    IMPORTS = "imports"
    USES = "uses"


@dataclass
class Entity:
    """A node in the code knowledge graph."""

    id: str
    type: EntityType
    name: str
    file_path: str
    line_start: int = 0
    line_end: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        return self.id == other.id


@dataclass
class Relation:
    """An edge between two entities in the code knowledge graph."""

    source: str
    target: str
    type: RelationType
    metadata: dict[str, Any] = field(default_factory=dict)
