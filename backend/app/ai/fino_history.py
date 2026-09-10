"""Splits a user's persisted Fino history into (recent turns to send
verbatim, a cheap summary of anything older) so a long-running conversation
doesn't grow the prompt without bound. The summary is a deterministic
one-liner rather than an extra paid Claude call per message — good enough
to give Fino a sense of what's already been covered."""

from app.models.fino_message import FinoMessage

KEEP_RECENT_TURNS = 12  # messages, not turns — 6 user/assistant exchanges


def split_history(history: list[FinoMessage]) -> tuple[list[FinoMessage], str | None]:
    if len(history) <= KEEP_RECENT_TURNS:
        return history, None

    older = history[: -KEEP_RECENT_TURNS]
    recent = history[-KEEP_RECENT_TURNS:]

    topics = [m.content[:60].strip() for m in older if m.role == "user"]
    summary = "the user asked about " + "; ".join(topics[:8]) if topics else None
    return recent, summary


def to_anthropic_messages(history: list[FinoMessage]) -> list[dict]:
    return [{"role": m.role, "content": m.content} for m in history]
