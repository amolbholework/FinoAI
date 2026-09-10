"""Unit tests for the LLM provider abstraction itself — ClaudeProvider's
response normalization, structured-output validation, and the factory's
per-purpose resolution. The Anthropic SDK is mocked; no live calls."""
from unittest.mock import MagicMock

import anthropic
import pytest
from pydantic import BaseModel

from app.llm.base import LLMResponse, LLMUnavailableError, LLMValidationError
from app.llm.factory import get_provider
from app.llm.providers.claude import ClaudeProvider


class _Schema(BaseModel):
    value: str


def _fake_anthropic_client(monkeypatch, text: str, stop_reason="end_turn", input_tokens=10, output_tokens=5):
    fake_content_block = MagicMock(type="text", text=text)
    fake_response = MagicMock(
        content=[fake_content_block],
        stop_reason=stop_reason,
        usage=MagicMock(input_tokens=input_tokens, output_tokens=output_tokens),
    )
    fake_client = MagicMock()
    fake_client.messages.create.return_value = fake_response
    monkeypatch.setattr("app.llm.providers.claude.anthropic.Anthropic", lambda api_key: fake_client)
    return fake_client


def test_generate_returns_normalized_response_shape(monkeypatch):
    _fake_anthropic_client(monkeypatch, "hello there")
    provider = ClaudeProvider(model="claude-test", api_key="fake-key")

    response = provider.generate(messages=[{"role": "user", "content": "hi"}], system_prompt="sys")

    assert isinstance(response, LLMResponse)
    assert response.text == "hello there"
    assert response.usage == {"input_tokens": 10, "output_tokens": 5}
    assert response.finish_reason == "end_turn"


def test_generate_raises_llm_unavailable_without_api_key():
    provider = ClaudeProvider(model="claude-test", api_key="")
    with pytest.raises(LLMUnavailableError):
        provider.generate(messages=[{"role": "user", "content": "hi"}], system_prompt="sys")


def test_generate_structured_returns_validated_schema_instance(monkeypatch):
    _fake_anthropic_client(monkeypatch, '{"value": "ok"}')
    provider = ClaudeProvider(model="claude-test", api_key="fake-key")

    result = provider.generate_structured(
        messages=[{"role": "user", "content": "hi"}], system_prompt="sys", schema=_Schema
    )

    assert isinstance(result, _Schema)
    assert result.value == "ok"


def test_generate_structured_strips_markdown_fences(monkeypatch):
    _fake_anthropic_client(monkeypatch, '```json\n{"value": "fenced"}\n```')
    provider = ClaudeProvider(model="claude-test", api_key="fake-key")

    result = provider.generate_structured(
        messages=[{"role": "user", "content": "hi"}], system_prompt="sys", schema=_Schema
    )
    assert result.value == "fenced"


def test_generate_structured_raises_validation_error_on_schema_mismatch(monkeypatch):
    _fake_anthropic_client(monkeypatch, '{"wrong_field": "oops"}')
    provider = ClaudeProvider(model="claude-test", api_key="fake-key")

    with pytest.raises(LLMValidationError):
        provider.generate_structured(messages=[{"role": "user", "content": "hi"}], system_prompt="sys", schema=_Schema)


def test_generate_structured_raises_unavailable_on_unparseable_json(monkeypatch):
    _fake_anthropic_client(monkeypatch, "not json at all")
    provider = ClaudeProvider(model="claude-test", api_key="fake-key")

    with pytest.raises(LLMUnavailableError):
        provider.generate_structured(messages=[{"role": "user", "content": "hi"}], system_prompt="sys", schema=_Schema)


def test_generate_wraps_anthropic_api_error(monkeypatch):
    fake_client = MagicMock()
    fake_client.messages.create.side_effect = anthropic.APIError(
        message="boom", request=MagicMock(), body=None
    )
    monkeypatch.setattr("app.llm.providers.claude.anthropic.Anthropic", lambda api_key: fake_client)
    provider = ClaudeProvider(model="claude-test", api_key="fake-key")

    with pytest.raises(LLMUnavailableError):
        provider.generate(messages=[{"role": "user", "content": "hi"}], system_prompt="sys")


def test_analyze_image_returns_validated_schema(monkeypatch):
    _fake_anthropic_client(monkeypatch, '{"value": "from-image"}')
    provider = ClaudeProvider(model="claude-test", api_key="fake-key")

    result = provider.analyze_image(b"fake-bytes", "image/jpeg", "sys", "describe it", _Schema)
    assert result.value == "from-image"


def test_provider_exposes_model_name():
    provider = ClaudeProvider(model="claude-test-model", api_key="fake-key")
    assert provider.model == "claude-test-model"
    assert provider.name == "claude"


# --- factory ---


def test_get_provider_defaults_to_claude_for_every_purpose():
    for purpose in ("fino", "advice", "vision"):
        provider = get_provider(purpose)
        assert isinstance(provider, ClaudeProvider)


def test_get_provider_raises_clear_error_for_unregistered_provider(monkeypatch):
    # get_settings() is process-wide cached (@lru_cache), so patch the
    # attribute on that shared instance rather than trying to swap it out.
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "llm_provider_fino", "gemini")

    with pytest.raises(ValueError, match="gemini"):
        get_provider("fino")
