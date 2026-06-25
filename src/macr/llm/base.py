"""Abstract LLM backend interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, TypeVar

from pydantic import BaseModel

if TYPE_CHECKING:
    from macr.tracing.trace_logger import TraceLogger

T = TypeVar("T", bound=BaseModel)


class LLMBackend(ABC):
    """Abstract interface for LLM inference backends."""

    @abstractmethod
    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        response_format: type[T] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        **kwargs: Any,
    ) -> str | T:
        """Send a chat completion request to the LLM.

        Args:
            messages: OpenAI-style conversation messages.
            response_format: Optional Pydantic model for structured JSON output.
            max_tokens: Maximum tokens in the response.
            temperature: Sampling temperature.
            **kwargs: Additional provider-specific parameters.

        Returns:
            Raw response string, or a parsed Pydantic model if response_format is given.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model identifier used by this backend."""
        raise NotImplementedError

    @property
    def trace_logger(self) -> TraceLogger | None:
        """Return the optional trace logger attached to this backend."""
        return None

    @trace_logger.setter
    def trace_logger(self, value: TraceLogger | None) -> None:
        """Attach a trace logger. Default no-op."""
        return None

    def with_model(self, model: str | None) -> LLMBackend:
        """Return a backend configured for the given model, or self if unchanged."""
        if model is None or model == self.model_name:
            return self
        raise NotImplementedError
