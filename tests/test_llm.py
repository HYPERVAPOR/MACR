"""Tests for the LLM backend."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from pydantic import BaseModel

from macr.llm.openai_backend import OpenAIBackend


class _SampleOutput(BaseModel):
    answer: str


def _make_fake_response(content: str, parsed: BaseModel | None = None) -> MagicMock:
    fake_message = MagicMock()
    fake_message.content = content
    fake_message.parsed = parsed

    fake_choice = MagicMock()
    fake_choice.message = fake_message

    fake_response = MagicMock()
    fake_response.choices = [fake_choice]
    fake_response.usage = None
    return fake_response


def test_openai_backend_chat_string() -> None:
    backend = OpenAIBackend(api_key="test-key", model="gpt-4o-mini")

    fake_response = _make_fake_response("hello")
    with patch.object(backend._client.chat.completions, "create", return_value=fake_response):
        result = backend.chat([{"role": "user", "content": "hi"}])

    assert result == "hello"


def test_openai_backend_chat_structured_beta_parse() -> None:
    backend = OpenAIBackend(api_key="test-key", model="gpt-4o-mini", use_beta_parse=True)

    parsed = _SampleOutput(answer="42")
    fake_response = _make_fake_response('{"answer": "42"}', parsed=parsed)

    with patch.object(backend._client.beta.chat.completions, "parse", return_value=fake_response):
        result = backend.chat(
            [{"role": "user", "content": "what is the answer?"}],
            response_format=_SampleOutput,
        )

    assert isinstance(result, _SampleOutput)
    assert result.answer == "42"


def test_openai_backend_chat_structured_standard_mode() -> None:
    backend = OpenAIBackend(api_key="test-key", model="gpt-4o-mini", use_beta_parse=False)

    fake_response = _make_fake_response('{"answer": "99"}')

    with patch.object(backend._client.chat.completions, "create", return_value=fake_response):
        result = backend.chat(
            [{"role": "user", "content": "what is the answer?"}],
            response_format=_SampleOutput,
        )

    assert isinstance(result, _SampleOutput)
    assert result.answer == "99"


def test_openai_backend_standard_mode_with_markdown_json() -> None:
    backend = OpenAIBackend(api_key="test-key", model="gpt-4o-mini", use_beta_parse=False)

    fake_response = _make_fake_response('```json\n{"answer": "markdown"}\n```')

    with patch.object(backend._client.chat.completions, "create", return_value=fake_response):
        result = backend.chat(
            [{"role": "user", "content": "what is the answer?"}],
            response_format=_SampleOutput,
        )

    assert isinstance(result, _SampleOutput)
    assert result.answer == "markdown"
