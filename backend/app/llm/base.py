"""Provider-agnostic LLM abstraction. Every AI surface in the app — Fino,
the advice panel, screenshot extraction — goes through an LLMProvider
rather than calling a vendor SDK directly, so the provider behind any of
them is swappable by config (see factory.py) and callers never branch on
which model actually answered.

Note on the package location: the brief said `services/llm/`; this
codebase's convention is every domain living under `app/<name>/` (app/ai,
app/onboarding, app/demo, ...), so this lives at `app/llm/` instead to
match. Same contents, different parent path.
"""
from __future__ import annotations

import abc
from collections.abc import Generator, Iterable
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel


class LLMUnavailableError(Exception):
    """The provider couldn't produce a usable response at all — missing
    API key, network/timeout/API error, or output that wasn't parseable
    as JSON at all when JSON was required. Callers treat this as
    "degrade gracefully", never as a reason to break a page."""


class LLMValidationError(Exception):
    """The provider returned something parseable that didn't match the
    requested schema. Kept distinct from LLMUnavailableError because
    callers often want a different message for "the model said something
    oddly-shaped" versus "the model didn't respond at all" — screenshot
    extraction's two different failure messages depend on this split."""


@dataclass
class LLMResponse:
    """The one shape every provider's non-streaming call returns.
    `usage` is normalized to {"input_tokens": int, "output_tokens": int}
    regardless of what the vendor SDK calls those fields. `raw` is the
    provider-native response object, kept only for logging/debugging —
    no caller may depend on its shape."""

    text: str
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: str | None = None
    raw: Any = None


class LLMProvider(abc.ABC):
    """One instance per (provider, model, purpose) — see
    factory.get_provider(). `name` is a short lowercase identifier
    ("claude", "gemini") used only for logging/dev-mode indicators, never
    surfaced to end users and never branched on by callers."""

    name: str
    model: str

    @abc.abstractmethod
    def generate(
        self,
        messages: Iterable[dict],
        system_prompt: str,
        tools: list[dict] | None = None,
        stream: bool = False,
        max_tokens: int = 1024,
    ) -> LLMResponse | Generator[str, None, None]:
        """Non-streaming (stream=False): returns a complete LLMResponse.
        Streaming (stream=True): returns a generator yielding text
        deltas — the caller accumulates them if it needs the full text
        afterward (see routers/fino.py, which persists the accumulated
        text once the stream ends)."""

    @abc.abstractmethod
    def generate_structured(
        self, messages: Iterable[dict], system_prompt: str, schema: type[BaseModel]
    ) -> BaseModel:
        """Returns a validated instance of `schema`. Raises
        LLMUnavailableError if the provider couldn't be reached or its
        output wasn't parseable as JSON at all; LLMValidationError if it
        parsed but didn't match `schema`."""

    @abc.abstractmethod
    def analyze_image(
        self,
        image_bytes: bytes,
        media_type: str,
        system_prompt: str,
        user_text: str,
        schema: type[BaseModel],
    ) -> BaseModel:
        """Vision variant of generate_structured. `media_type` and
        `user_text` aren't in the brief's one-line signature
        (`analyze_image(image_bytes, prompt, schema)`) but are required
        for a real vision call — the image's MIME type, and the
        instruction text accompanying it — so they're explicit params
        here rather than folded into `system_prompt`."""
