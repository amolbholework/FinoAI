"""Integration tests for the Fino router. _stream_reply is monkeypatched
(same pattern as the recommendations tests) so these never hit a real
LLM provider."""
from app.llm.base import LLMUnavailableError


def _mock_stream(chunks):
    def _stream(system_prompt, messages, max_tokens=1024):
        yield from chunks

    return _stream


def test_messages_requires_a_session(client):
    response = client.get("/api/fino/messages")
    assert response.status_code == 401


def test_empty_history_for_new_user(auth_client):
    response = auth_client.get("/api/fino/messages")
    assert response.status_code == 200
    assert response.json() == []


def test_sending_a_message_persists_user_and_assistant_turns(auth_client, monkeypatch):
    monkeypatch.setattr("app.routers.fino._stream_reply", _mock_stream(["Hello", " there!"]))

    response = auth_client.post("/api/fino/messages", json={"message": "How am I doing this month?"})
    assert response.status_code == 200
    assert response.text == "Hello there!"

    history = auth_client.get("/api/fino/messages").json()
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "How am I doing this month?"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "Hello there!"


def test_stream_failure_falls_back_to_a_useful_message(auth_client, monkeypatch):
    def _always_fails(system_prompt, messages, max_tokens=1024):
        raise LLMUnavailableError("boom")
        yield  # pragma: no cover - makes this a generator

    monkeypatch.setattr("app.routers.fino._stream_reply", _always_fails)

    response = auth_client.post("/api/fino/messages", json={"message": "hi"})
    assert response.status_code == 200
    assert "having trouble connecting" in response.text

    history = auth_client.get("/api/fino/messages").json()
    assert history[1]["content"] == response.text


def test_rate_limit_returns_429_after_too_many_requests(auth_client, monkeypatch):
    monkeypatch.setattr("app.routers.fino._stream_reply", _mock_stream(["ok"]))
    monkeypatch.setattr("app.routers.fino.settings.fino_rate_limit_per_minute", 2)

    for _ in range(2):
        assert auth_client.post("/api/fino/messages", json={"message": "hi"}).status_code == 200

    response = auth_client.post("/api/fino/messages", json={"message": "hi"})
    assert response.status_code == 429


def test_a_second_user_never_sees_the_first_users_fino_history(client, monkeypatch):
    from app.core.security import GoogleIdentity

    monkeypatch.setattr(
        "app.routers.auth.verify_google_id_token",
        lambda token: GoogleIdentity(sub="fino-user-a", email="a@example.com", name="A", picture=None),
    )
    client.post("/api/auth/google", json={"id_token": "ta"})
    monkeypatch.setattr("app.routers.fino._stream_reply", _mock_stream(["hi from A"]))
    client.post("/api/fino/messages", json={"message": "hello"})

    monkeypatch.setattr(
        "app.routers.auth.verify_google_id_token",
        lambda token: GoogleIdentity(sub="fino-user-b", email="b@example.com", name="B", picture=None),
    )
    client.post("/api/auth/google", json={"id_token": "tb"})
    history_b = client.get("/api/fino/messages").json()

    assert history_b == []
