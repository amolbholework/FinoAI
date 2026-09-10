import pytest
from pydantic import ValidationError

from app.ai.recommendations import FALLBACK_OUTPUT, _call_with_retry
from app.ai.schema import RecommendationOutput
from app.llm.base import LLMUnavailableError, LLMValidationError
from app.llm.providers.claude import _extract_json

VALID_PAYLOAD = {
    "summary": "You spent 20% more on dining this month.",
    "insights": ["Dining is up 20% vs your 3-month average."],
    "recommendations": [
        {
            "title": "Cut dining spend",
            "rationale": "Dining is 20% above your rolling average.",
            "projected_impact": "Save ~2000/month",
            "category": "Food",
            "priority": "high",
        }
    ],
    "risks": ["Savings rate could dip below 10% if this continues."],
}


def test_recommendation_output_accepts_valid_payload():
    output = RecommendationOutput.model_validate(VALID_PAYLOAD)
    assert output.recommendations[0].priority == "high"


def test_recommendation_output_rejects_invalid_priority():
    bad = {**VALID_PAYLOAD, "recommendations": [{**VALID_PAYLOAD["recommendations"][0], "priority": "urgent"}]}
    with pytest.raises(ValidationError):
        RecommendationOutput.model_validate(bad)


def test_recommendation_output_rejects_missing_field():
    bad = {k: v for k, v in VALID_PAYLOAD.items() if k != "risks"}
    with pytest.raises(ValidationError):
        RecommendationOutput.model_validate(bad)


def test_extract_json_handles_markdown_fences():
    import json

    text = f"```json\n{json.dumps(VALID_PAYLOAD)}\n```"
    parsed = _extract_json(text)
    assert parsed["summary"] == VALID_PAYLOAD["summary"]


def test_extract_json_handles_bare_json():
    import json

    parsed = _extract_json(json.dumps(VALID_PAYLOAD))
    assert parsed["summary"] == VALID_PAYLOAD["summary"]


def test_call_with_retry_degrades_to_fallback_after_repeated_failure(monkeypatch):
    def always_fails(summary):
        raise LLMUnavailableError("simulated outage")

    monkeypatch.setattr("app.ai.recommendations._generate", always_fails)
    result = _call_with_retry({"some": "summary"})
    assert result is FALLBACK_OUTPUT


def test_call_with_retry_recovers_on_second_attempt(monkeypatch):
    calls = {"count": 0}

    def fails_once_then_succeeds(summary):
        calls["count"] += 1
        if calls["count"] == 1:
            raise LLMUnavailableError("transient")
        return RecommendationOutput.model_validate(VALID_PAYLOAD)

    monkeypatch.setattr("app.ai.recommendations._generate", fails_once_then_succeeds)
    result = _call_with_retry({"some": "summary"})
    assert result is not FALLBACK_OUTPUT
    assert result.summary == VALID_PAYLOAD["summary"]


def test_call_with_retry_retries_once_on_schema_validation_failure(monkeypatch):
    calls = {"count": 0}

    def bad_then_good(summary):
        calls["count"] += 1
        if calls["count"] == 1:
            raise LLMValidationError("missing required fields")
        return RecommendationOutput.model_validate(VALID_PAYLOAD)

    monkeypatch.setattr("app.ai.recommendations._generate", bad_then_good)
    result = _call_with_retry({"some": "summary"})
    assert calls["count"] == 2
    assert result.summary == VALID_PAYLOAD["summary"]
