"""OpenAI-compatible LLM backend implementation."""

from __future__ import annotations

import json
import logging
import time
from typing import TYPE_CHECKING, Any, TypeVar, cast

from openai import OpenAI
from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from macr.config import get_settings
from macr.llm.base import LLMBackend

if TYPE_CHECKING:
    from macr.tracing.trace_logger import TraceLogger

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class OpenAIBackend(LLMBackend):
    """LLM backend using OpenAI-compatible APIs.

    Supports both native OpenAI (beta parse endpoint) and third-party
    OpenAI-compatible providers by falling back to standard chat completions.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        use_beta_parse: bool | None = None,
        trace_logger: TraceLogger | None = None,
    ) -> None:
        settings = get_settings()
        self._api_key = api_key or settings.openai_api_key
        self._model = model or settings.openai_model
        self._base_url = base_url or settings.openai_base_url
        self._use_beta_parse = (
            use_beta_parse
            if use_beta_parse is not None
            else settings.openai_use_beta_parse
        )
        self._trace_logger = trace_logger

        client_kwargs: dict[str, Any] = {"api_key": self._api_key}
        if self._base_url:
            client_kwargs["base_url"] = self._base_url

        self._client = OpenAI(**client_kwargs)

    @property
    def trace_logger(self) -> TraceLogger | None:
        return self._trace_logger

    @trace_logger.setter
    def trace_logger(self, value: TraceLogger | None) -> None:
        self._trace_logger = value

    @property
    def model_name(self) -> str:
        return self._model

    def with_model(self, model: str | None) -> OpenAIBackend:
        if model is None or model == self._model:
            return self
        return OpenAIBackend(
            api_key=self._api_key,
            base_url=self._base_url,
            model=model,
            use_beta_parse=self._use_beta_parse,
            trace_logger=self._trace_logger,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        response_format: type[T] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        **kwargs: Any,
    ) -> str | T:
        request_params: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
        }

        if max_tokens is not None:
            request_params["max_completion_tokens"] = max_tokens
        else:
            request_params["max_completion_tokens"] = get_settings().max_tokens

        if temperature is not None:
            request_params["temperature"] = temperature
        elif get_settings().temperature is not None:
            request_params["temperature"] = get_settings().temperature

        request_params.update(kwargs)

        logger.debug(
            "Sending chat request to %s with %d messages (beta_parse=%s)",
            self._model,
            len(messages),
            self._use_beta_parse,
        )

        if self._trace_logger is not None:
            self._trace_logger.log_llm_request(messages)

        if response_format is not None and self._use_beta_parse:
            return self._chat_beta_parse(request_params, response_format)

        return self._chat_standard(request_params, response_format)

    def _chat_beta_parse(
        self,
        request_params: dict[str, Any],
        response_format: type[T],
    ) -> T:
        request_params["response_format"] = response_format
        try:
            start = time.perf_counter()
            response = self._client.beta.chat.completions.parse(**request_params)
            latency_ms = (time.perf_counter() - start) * 1000
        except Exception as exc:  # pragma: no cover - provider-specific errors
            logger.warning(
                "Beta parse endpoint failed (%s). Consider setting OPENAI_USE_BETA_PARSE=false.",
                exc,
            )
            raise

        self._log_usage(response.usage)

        parsed = response.choices[0].message.parsed
        if parsed is not None:
            if self._trace_logger is not None:
                self._trace_logger.log_llm_response(parsed, response.usage, latency_ms)
            return cast(T, parsed)

        structured_content = response.choices[0].message.content
        if isinstance(structured_content, str):
            if self._trace_logger is not None:
                self._trace_logger.log_llm_response(
                    structured_content, response.usage, latency_ms
                )
            return response_format.model_validate_json(structured_content)
        raise ValueError("Structured response returned empty content")

    def _chat_standard(
        self,
        request_params: dict[str, Any],
        response_format: type[T] | None,
    ) -> str | T:
        messages = list(request_params.get("messages", []))

        if response_format is not None:
            # Ask the model to output valid JSON matching the schema.
            schema = response_format.model_json_schema()
            system_json_instruction = (
                "You must respond with a single JSON object matching this schema:\n"
                f"{json.dumps(schema, indent=2)}\n"
                "Do not include markdown formatting or explanations outside the JSON."
            )
            messages = self._inject_system_message(messages, system_json_instruction)
            request_params["messages"] = messages

        start = time.perf_counter()
        response = self._client.chat.completions.create(**request_params)
        latency_ms = (time.perf_counter() - start) * 1000
        self._log_usage(response.usage)

        raw_content = response.choices[0].message.content
        if not isinstance(raw_content, str):
            raise ValueError("LLM returned empty content")

        if self._trace_logger is not None:
            self._trace_logger.log_llm_response(raw_content, response.usage, latency_ms)

        if response_format is None:
            return raw_content

        return self._parse_structured(raw_content, response_format)

    @staticmethod
    def _inject_system_message(
        messages: list[dict[str, Any]], content: str
    ) -> list[dict[str, Any]]:
        """Prepend or extend the system message."""
        new_messages: list[dict[str, Any]] = []
        system_found = False
        for message in messages:
            if message.get("role") == "system":
                original = message.get("content", "")
                new_messages.append(
                    {"role": "system", "content": f"{original}\n\n{content}"}
                )
                system_found = True
            else:
                new_messages.append(message)
        if not system_found:
            new_messages.insert(0, {"role": "system", "content": content})
        return new_messages

    @staticmethod
    def _parse_structured(content: str, response_format: type[T]) -> T:
        """Parse JSON content into a Pydantic model, with simple cleanup."""
        cleaned = content.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        return response_format.model_validate_json(cleaned)

    def _log_usage(self, usage: Any) -> None:
        if usage:
            logger.debug(
                "Tokens used: prompt=%d, completion=%d, total=%d",
                usage.prompt_tokens,
                usage.completion_tokens,
                usage.total_tokens,
            )

    def __repr__(self) -> str:  # pragma: no cover
        return f"OpenAIBackend(model={self._model}, beta_parse={self._use_beta_parse})"
