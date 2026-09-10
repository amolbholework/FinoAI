from datetime import datetime, timezone

from app.ai.fino_history import KEEP_RECENT_TURNS, split_history, to_anthropic_messages
from app.models.fino_message import FinoMessage


def _msg(role: str, content: str) -> FinoMessage:
    return FinoMessage(id="x", user_id="u", role=role, content=content, created_at=datetime.now(timezone.utc))


def test_short_history_is_returned_unchanged_with_no_summary():
    history = [_msg("user", "hi"), _msg("assistant", "hello")]
    recent, summary = split_history(history)
    assert recent == history
    assert summary is None


def test_long_history_is_truncated_and_summarized():
    history = []
    for i in range(20):
        history.append(_msg("user", f"question number {i}"))
        history.append(_msg("assistant", f"answer number {i}"))

    recent, summary = split_history(history)

    assert len(recent) == KEEP_RECENT_TURNS
    assert recent == history[-KEEP_RECENT_TURNS:]
    assert summary is not None
    assert "question number 0" in summary


def test_to_anthropic_messages_maps_role_and_content():
    history = [_msg("user", "hi"), _msg("assistant", "hello")]
    messages = to_anthropic_messages(history)
    assert messages == [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]
