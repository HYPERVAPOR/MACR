"""Patch generation and application utilities."""

from __future__ import annotations

import logging
from pathlib import Path

from tree_sitter import Language, Parser
from tree_sitter_python import language as python_language

from macr.agents.protocol import PatchCandidate

logger = logging.getLogger(__name__)

PYTHON_LANGUAGE = Language(python_language())

__all__ = ["apply_patch", "extract_first_code_block", "PatchCandidate", "write_and_apply"]


def apply_patch(buggy_code: str, patch: PatchCandidate) -> str:
    """Apply a patch candidate to the original buggy code.

    Heuristic:
    - If the patched code looks like a complete runnable file, use it directly.
    - Otherwise, try to replace the matching function definition in the buggy code.
    """
    patched_code = patch.patched_code

    # If patched code is much shorter and looks like a single function, attempt replacement
    if _looks_like_function_only(patched_code):
        replaced = _replace_function(buggy_code, patched_code)
        if replaced is not None:
            return replaced

    # Fallback: use the patched code as-is
    return patched_code


def _looks_like_function_only(code: str) -> bool:
    lines = code.strip().splitlines()
    if not lines:
        return False
    first_line = lines[0].strip()
    return first_line.startswith("def ") or first_line.startswith("class ")


def _replace_function(buggy_code: str, patched_function: str) -> str | None:
    """Replace a function definition in buggy_code with patched_function."""
    parser = Parser(PYTHON_LANGUAGE)
    source_bytes = buggy_code.encode("utf-8")
    tree = parser.parse(source_bytes)

    target_name = _extract_function_name(patched_function)
    if target_name is None:
        return None

    for node in tree.root_node.children:
        if node.type == "function_definition":
            name_node = next((c for c in node.children if c.type == "identifier"), None)
            if name_node and source_bytes[name_node.start_byte : name_node.end_byte].decode("utf-8") == target_name:
                prefix = buggy_code[: node.start_byte]
                suffix = buggy_code[node.end_byte :]
                return prefix + patched_function + suffix

    return None


def _extract_function_name(code: str) -> str | None:
    parser = Parser(PYTHON_LANGUAGE)
    tree = parser.parse(code.encode("utf-8"))
    for node in tree.root_node.children:
        if node.type == "function_definition":
            for child in node.children:
                if child.type == "identifier":
                    return child.text.decode("utf-8") if child.text else None
    return None


def extract_first_code_block(text: str) -> str | None:
    """Extract the first fenced code block from a Markdown-style response."""
    if "```" not in text:
        return None
    parts = text.split("```")
    for i, part in enumerate(parts):
        if i == 0:
            continue
        candidate = part.strip()
        lines = candidate.splitlines()
        if lines and not any(c in lines[0] for c in "(){}=:"):
            candidate = "\n".join(lines[1:]).strip()
        if candidate:
            return candidate
    return None


def write_and_apply(buggy_file: str | Path, patch: PatchCandidate, output_dir: str | Path) -> Path:
    """Write a patched version of a file to the output directory."""
    buggy_file = Path(buggy_file)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    original_code = buggy_file.read_text(encoding="utf-8")
    patched_code = apply_patch(original_code, patch)

    output_path = output_dir / buggy_file.name
    output_path.write_text(patched_code, encoding="utf-8")
    return output_path
