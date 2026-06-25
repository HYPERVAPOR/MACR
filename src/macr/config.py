"""Global configuration for MACR."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class Settings(BaseModel):
    """MACR runtime settings loaded from environment variables."""

    openai_api_key: str | None = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY"),
        description="OpenAI API key",
    )
    openai_model: str = Field(
        default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o"),
        description="OpenAI model name",
    )
    openai_base_url: str | None = Field(
        default_factory=lambda: os.getenv("OPENAI_BASE_URL"),
        description="Optional OpenAI-compatible base URL",
    )
    openai_use_beta_parse: bool = Field(
        default_factory=lambda: os.getenv("OPENAI_USE_BETA_PARSE", "true").lower() in ("1", "true", "yes"),
        description="Use OpenAI beta chat.completions.parse for structured output",
    )

    max_repair_attempts: int = Field(
        default_factory=lambda: int(os.getenv("MACR_MAX_REPAIR_ATTEMPTS", "3")),
        description="Maximum repair attempts per bug",
    )
    max_tokens: int = Field(
        default_factory=lambda: int(os.getenv("MACR_MAX_TOKENS", "4096")),
        description="Maximum tokens for LLM responses",
    )
    temperature: float = Field(
        default_factory=lambda: float(os.getenv("MACR_TEMPERATURE", "0.2")),
        description="Sampling temperature",
    )

    log_level: str = Field(
        default_factory=lambda: os.getenv("MACR_LOG_LEVEL", "INFO"),
        description="Logging level",
    )

    project_root: Path = Field(
        default=Path(__file__).resolve().parents[3],
        description="Project root directory",
    )

    trace_store: str = Field(
        default_factory=lambda: os.getenv("MACR_TRACE_STORE", "jsonl"),
        description="Trace storage backend: jsonl or sqlite",
    )

    trace_dir: Path = Field(
        default_factory=lambda: Path(os.getenv("MACR_TRACE_DIR", "outputs/traces")),
        description="Directory for trace storage",
    )


@lru_cache
def get_settings() -> Settings:
    """Return the cached global settings instance."""
    return Settings()


# Backward-compatible module-level accessor
settings = get_settings()
