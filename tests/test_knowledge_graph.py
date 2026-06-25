"""Tests for the knowledge graph builder and query interface."""

from __future__ import annotations

from pathlib import Path

import pytest

from macr.knowledge_graph.builder import KnowledgeGraphBuilder
from macr.knowledge_graph.query import KnowledgeGraphQuery

SAMPLE_PYTHON = """
def add(a, b):
    return a + b

def multiply(x, y):
    return add(x, y) + add(x, y)

class Calculator:
    def compute(self, a, b):
        return multiply(a, b)
"""


@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "calc.py").write_text(SAMPLE_PYTHON)
    return repo


def test_builder_extracts_functions_and_calls(sample_repo: Path) -> None:
    builder = KnowledgeGraphBuilder()
    graph = builder.build_from_directory(sample_repo)
    query = KnowledgeGraphQuery(graph)

    functions = query.find_functions(file_path=str(sample_repo / "calc.py"))
    names = {f["name"] for f in functions}
    assert names >= {"add", "multiply", "compute"}

    multiply = next(f for f in functions if f["name"] == "multiply")
    callees = query.find_callees(multiply["id"])
    assert {c["name"] for c in callees} == {"add"}

    add = next(f for f in functions if f["name"] == "add")
    callers = query.find_callers(add["id"])
    assert {c["name"] for c in callers} == {"multiply"}


def test_query_related_functions(sample_repo: Path) -> None:
    builder = KnowledgeGraphBuilder()
    graph = builder.build_from_directory(sample_repo)
    query = KnowledgeGraphQuery(graph)

    functions = query.find_functions(file_path=str(sample_repo / "calc.py"))
    add = next(f for f in functions if f["name"] == "add")
    related = query.get_related_functions(add["id"], depth=2)
    names = {r["name"] for r in related}
    assert "multiply" in names


def test_summarize_for_function(sample_repo: Path) -> None:
    builder = KnowledgeGraphBuilder()
    graph = builder.build_from_directory(sample_repo)
    query = KnowledgeGraphQuery(graph)

    functions = query.find_functions(name="multiply")
    summary = query.summarize_for_function(functions[0]["id"])
    assert "Function: multiply" in summary
    assert "Calls:" in summary
    assert "add" in summary
