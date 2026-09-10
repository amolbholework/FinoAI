"""Claude provider — this is the pre-existing app/ai/client.py logic moved
behind the LLMProvider interface, byte-for-byte unchanged in behavior:
same models, same max_tokens defaults, same JSON-fence-stripping, same
streaming approach. Nothing about how Claude is called changes here, only
where the calling code lives."""
import base64
import json
import re
from collections.abc import Generator, Iterable

import anthropic
from pydantic import BaseModel, ValidationError

from app.llm.base import LLMProvider, LLMResponse, LLMUnavailableError, LLMValidationError

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _extract_json(text: str) -> dict:
    cleaned = _FENCE_RE.sub("", text.strip())
    return json.loads(cleaned)


def _usage_dict(usage: object) -> dict[str, int]:
    return {"input_tokens": getattr(usage, "input_tokens", 0), "output_tokens": getattr(usage, "output_tokens", 0)}


class ClaudeProvider(LLMProvider):
    name = "claude"

    def __init__(self, model: str, api_key: str):
        self.model = model
        self._model = model
        self._api_key = api_key

    def _client(self) -> anthropic.Anthropic:
        if not self._api_key:
            raise LLMUnavailableError("ANTHROPIC_API_KEY is not configured.")
        return anthropic.Anthropic(api_key=self._api_key)

    def generate(
        self,
        messages: Iterable[dict],
        system_prompt: str,
        tools: list[dict] | None = None,
        stream: bool = False,
        max_tokens: int = 1024,
    ) -> LLMResponse | Generator[str, None, None]:
        if stream:
            return self._stream(messages, system_prompt, max_tokens)

        client = self._client()
        try:
            response = client.messages.create(
                model=self._model, max_tokens=max_tokens, system=system_prompt, messages=list(messages)
            )
            text = "".join(block.text for block in response.content if block.type == "text")
            return LLMResponse(
                text=text,
                usage=_usage_dict(response.usage),
                finish_reason=response.stop_reason,
                raw=response,
            )
        except anthropic.APIError as exc:
            raise LLMUnavailableError(str(exc)) from exc

    def _stream(
        self, messages: Iterable[dict], system_prompt: str, max_tokens: int
    ) -> Generator[str, None, None]:
        client = self._client()
        try:
            with client.messages.stream(
                model=self._model, max_tokens=max_tokens, system=system_prompt, messages=list(messages)
            ) as stream:
                yield from stream.text_stream
        except anthropic.APIError as exc:
            raise LLMUnavailableError(str(exc)) from exc

    def generate_structured(
        self, messages: Iterable[dict], system_prompt: str, schema: type[BaseModel]
    ) -> BaseModel:
        response = self.generate(messages, system_prompt, stream=False)
        assert isinstance(response, LLMResponse)  # stream=False always returns this
        try:
            data = _extract_json(response.text)
        except json.JSONDecodeError as exc:
            raise LLMUnavailableError(str(exc)) from exc
        try:
            return schema.model_validate(data)
        except ValidationError as exc:
            raise LLMValidationError(str(exc)) from exc

    def analyze_image(
        self,
        image_bytes: bytes,
        media_type: str,
        system_prompt: str,
        user_text: str,
        schema: type[BaseModel],
    ) -> BaseModel:
        client = self._client()
        image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

        try:
            response = client.messages.create(
                model=self._model,
                max_tokens=1024,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {"type": "base64", "media_type": media_type, "data": image_b64},
                            },
                            {"type": "text", "text": user_text},
                        ],
                    }
                ],
            )
            text = "".join(block.text for block in response.content if block.type == "text")
        except anthropic.APIError as exc:
            raise LLMUnavailableError(str(exc)) from exc

        try:
            data = _extract_json(text)
        except json.JSONDecodeError as exc:
            raise LLMUnavailableError(str(exc)) from exc
        try:
            return schema.model_validate(data)
        except ValidationError as exc:
            raise LLMValidationError(str(exc)) from exc
