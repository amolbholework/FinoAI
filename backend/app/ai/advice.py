"""Orchestrates POST /api/advice: build the grounded summary, check the
cache, call the configured provider with one retry, and degrade to the
deterministic rule-based fallback (never the AI, never blank) if both
attempts fail. Mirrors ai/recommendations.py's shape deliberately — same
proven pattern, separate cache table (Advice, not Recommendation) so the
two features never collide."""
import logging

from sqlalchemy.orm import Session

from app.ai.advice_fallback import generate_fallback_advice
from app.ai.advice_prompt import ADVICE_SYSTEM_PROMPT, build_advice_user_message
from app.ai.advice_schema import AdviceOutput
from app.ai.advice_summary import advice_data_version, build_advice_summary
from app.llm.base import LLMUnavailableError, LLMValidationError
from app.llm.factory import get_provider
from app.models.advice import Advice

logger = logging.getLogger("finpilot.ai")


def _generate(summary: dict) -> AdviceOutput:
    provider = get_provider("advice")
    result = provider.generate_structured(
        messages=[{"role": "user", "content": build_advice_user_message(summary)}],
        system_prompt=ADVICE_SYSTEM_PROMPT,
        schema=AdviceOutput,
    )
    assert isinstance(result, AdviceOutput)
    return result


def _call_with_retry(summary: dict) -> AdviceOutput | None:
    """Returns None (not a fallback) if both attempts failed — the caller
    decides whether to use the rule-based fallback, so this function stays
    a pure "try the AI" concern."""
    for attempt in range(2):
        try:
            return _generate(summary)
        except LLMUnavailableError as exc:
            logger.warning("Advice LLM call failed (attempt %d): %s", attempt + 1, exc)
        except LLMValidationError as exc:
            logger.warning("Advice LLM response failed schema validation (attempt %d): %s", attempt + 1, exc)
    return None


def get_advice(db: Session, user_id: str, force_refresh: bool = False) -> tuple[Advice, bool]:
    """Returns (Advice row, was_cached)."""
    summary = build_advice_summary(db, user_id)
    version = advice_data_version(summary)

    if not force_refresh:
        cached = (
            db.query(Advice)
            .filter(Advice.data_version == version, Advice.user_id == user_id)
            .order_by(Advice.generated_at.desc())
            .first()
        )
        if cached:
            return cached, True

    output = _call_with_retry(summary)
    is_fallback = output is None
    if output is None:
        logger.error("Advice unavailable after retry — degrading to deterministic fallback.")
        output = generate_fallback_advice(summary)

    record = Advice(
        user_id=user_id,
        data_version=version,
        input_summary=summary,
        output=output.model_dump(),
        model_version=get_provider("advice").model if not is_fallback else "fallback-rule-based",
        is_fallback=is_fallback,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record, False
