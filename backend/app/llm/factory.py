"""Resolves which LLMProvider a given purpose should use, from config —
LLM_PROVIDER_FINO / LLM_PROVIDER_ADVICE / LLM_PROVIDER_VISION. All three
default to "claude" for now; only ClaudeProvider is registered until
GeminiProvider ships. Setting a purpose to an unregistered provider name
raises a clear error at call time rather than silently falling back —
config mistakes should be loud in dev, not a quiet wrong-model surprise.

Deliberately not cached: provider construction is cheap (just wraps an
api key + model string), and caching would let a config change go
unnoticed for the lifetime of the process — not worth the tradeoff.
"""
from typing import Literal

from app.core.config import get_settings
from app.llm.base import LLMProvider
from app.llm.providers.claude import ClaudeProvider

Purpose = Literal["fino", "advice", "vision"]

_SETTINGS_FIELD_BY_PURPOSE: dict[Purpose, str] = {
    "fino": "llm_provider_fino",
    "advice": "llm_provider_advice",
    "vision": "llm_provider_vision",
}


def get_provider(purpose: Purpose) -> LLMProvider:
    settings = get_settings()
    field_name = _SETTINGS_FIELD_BY_PURPOSE[purpose]
    provider_name = getattr(settings, field_name)

    if provider_name == "claude":
        return ClaudeProvider(model=settings.anthropic_model, api_key=settings.anthropic_api_key)

    # GeminiProvider registers here once it ships.
    raise ValueError(
        f"Unknown LLM provider '{provider_name}' configured for '{purpose}' "
        f"(set via {field_name.upper()}). Available: claude."
    )
