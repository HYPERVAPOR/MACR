"""Load subagent configurations from Markdown files with YAML frontmatter."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SubagentConfig(BaseModel):
    """Configuration for a single subagent."""

    name: str = Field(description="Unique subagent identifier")
    description: str = Field(description="Used by the coordinator to decide when to delegate")
    system_prompt: str = Field(description="System prompt for the subagent")
    model: str | None = Field(default=None, description="Optional per-subagent model override")
    tools: list[str] = Field(default_factory=list, description="Allowed tool names for this subagent")
    max_steps: int = Field(default=3, description="Max ReAct steps when tools are enabled")
    file_path: str | None = Field(default=None, description="Source config file path")


def load_subagent_configs() -> dict[str, SubagentConfig]:
    """Load subagent configs from built-in, user, and project directories.

    Precedence (later overrides earlier):
        built-ins < user ~/.macr/agents < project ./.macr/agents
    """
    configs: dict[str, SubagentConfig] = {}
    for directory in _search_paths():
        if not directory.exists():
            continue
        for file_path in sorted(directory.glob("*.md")):
            try:
                cfg = _parse_agent_file(file_path)
                configs[cfg.name] = cfg
                logger.debug("Loaded subagent config: %s from %s", cfg.name, file_path)
            except Exception as exc:
                logger.warning("Failed to parse subagent config %s: %s", file_path, exc)
    return configs


def _search_paths() -> list[Path]:
    """Return config directories in increasing precedence order."""
    builtin = Path(__file__).resolve().parent / "builtins"
    user = Path.home() / ".macr" / "agents"
    project = Path.cwd() / ".macr" / "agents"
    return [builtin, user, project]


def _parse_agent_file(file_path: Path) -> SubagentConfig:
    """Parse a Markdown file with YAML frontmatter into a SubagentConfig."""
    text = file_path.read_text(encoding="utf-8")
    if not text.strip().startswith("---"):
        raise ValueError("Subagent config must start with YAML frontmatter delimiters")

    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError("Subagent config frontmatter is not closed")

    frontmatter_text = parts[1]
    body = parts[2].strip()

    data: dict[str, Any] = yaml.safe_load(frontmatter_text) or {}
    if not isinstance(data, dict):
        raise ValueError("YAML frontmatter must be a mapping")

    # If system_prompt is also in frontmatter, append the Markdown body as extra guidance.
    if "system_prompt" in data:
        if body:
            data["system_prompt"] = f"{data['system_prompt'].strip()}\n\n{body}"
    else:
        if not body:
            raise ValueError("Subagent config must contain either a system_prompt in frontmatter or a Markdown body")
        data["system_prompt"] = body

    data["file_path"] = str(file_path)
    return SubagentConfig(**data)
