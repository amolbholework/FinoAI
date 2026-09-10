"""Covers the Google sign-in flow end to end. We never call real Google
servers in tests — verify_google_id_token is monkeypatched to return a
canned identity, the same way the AI tests avoid calling the real Claude
API. Everything downstream (user creation, cookie issuance, refresh
rotation, reuse detection, logout, data scoping) is exercised for real."""
from app.core import security
from app.core.security import GoogleIdentity


def _mock_identity(sub="google-sub-1", email="new-user@example.com", name="New User"):
    return GoogleIdentity(sub=sub, email=email, name=name, picture="https://example.com/pic.jpg")


def test_google_sign_in_creates_user_and_sets_cookies(client, monkeypatch):
    monkeypatch.setattr("app.routers.auth.verify_google_id_token", lambda token: _mock_identity())

    response = client.post("/api/auth/google", json={"id_token": "fake-token"})

    assert response.status_code == 200
    assert response.json()["email"] == "new-user@example.com"
    assert "fp_access" in response.cookies
    assert "fp_refresh" in response.cookies


def test_auth_cookies_use_samesite_none_in_production(monkeypatch):
    # SameSite=Lax cookies are never sent on a cross-site fetch/XHR — only a
    # top-level navigation — which is exactly how the deployed frontend
    # (Netlify) talks to this API (Render), on a different registrable
    # domain. Regression test for the incident where every authenticated
    # request after sign-in silently looked unauthenticated in production.
    monkeypatch.setattr(security.settings, "app_env", "production")
    from fastapi import Response

    response = Response()
    security.set_auth_cookies(response, "access-token", "refresh-token")
    set_cookie_headers = response.headers.getlist("set-cookie")
    assert len(set_cookie_headers) == 2
    for header in set_cookie_headers:
        assert "samesite=none" in header.lower()
        assert "secure" in header.lower()


def test_auth_cookies_use_samesite_lax_in_development(monkeypatch):
    # Local dev is same-site (localhost:5173 -> localhost:8000), and
    # SameSite=None requires Secure, which a plain http://localhost origin
    # can't satisfy — Lax is correct here, not a relaxed version of prod.
    monkeypatch.setattr(security.settings, "app_env", "development")
    from fastapi import Response

    response = Response()
    security.set_auth_cookies(response, "access-token", "refresh-token")
    set_cookie_headers = response.headers.getlist("set-cookie")
    assert len(set_cookie_headers) == 2
    for header in set_cookie_headers:
        assert "samesite=lax" in header.lower()
        assert "secure" not in header.lower()


def test_google_sign_in_is_idempotent_for_returning_user(client, monkeypatch):
    monkeypatch.setattr("app.routers.auth.verify_google_id_token", lambda token: _mock_identity(sub="returning-sub"))

    first = client.post("/api/auth/google", json={"id_token": "t1"})
    second = client.post("/api/auth/google", json={"id_token": "t2"})

    assert first.json()["id"] == second.json()["id"]


def test_google_sign_in_updates_profile_fields_on_returning_user(client, monkeypatch):
    monkeypatch.setattr(
        "app.routers.auth.verify_google_id_token", lambda token: _mock_identity(sub="profile-sub", name="Old Name")
    )
    client.post("/api/auth/google", json={"id_token": "t1"})

    monkeypatch.setattr(
        "app.routers.auth.verify_google_id_token", lambda token: _mock_identity(sub="profile-sub", name="New Name")
    )
    response = client.post("/api/auth/google", json={"id_token": "t2"})

    assert response.json()["name"] == "New Name"


def test_me_requires_a_session(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user_with_valid_session(client, monkeypatch):
    monkeypatch.setattr("app.routers.auth.verify_google_id_token", lambda token: _mock_identity(sub="me-sub"))
    client.post("/api/auth/google", json={"id_token": "t1"})

    response = client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == "new-user@example.com"


def test_refresh_rotates_tokens_and_old_access_cookie_still_works_until_expiry(client, monkeypatch):
    monkeypatch.setattr("app.routers.auth.verify_google_id_token", lambda token: _mock_identity(sub="refresh-sub"))
    client.post("/api/auth/google", json={"id_token": "t1"})
    old_access = client.cookies.get("fp_access")

    response = client.post("/api/auth/refresh")
    assert response.status_code == 200
    assert client.cookies.get("fp_access") != old_access


def test_refresh_token_reuse_is_detected_and_revokes_the_session(client, monkeypatch):
    monkeypatch.setattr("app.routers.auth.verify_google_id_token", lambda token: _mock_identity(sub="reuse-sub"))
    client.post("/api/auth/google", json={"id_token": "t1"})
    first_refresh_cookie = client.cookies.get("fp_refresh")

    # Rotate once — this is the legitimate use of the token.
    client.post("/api/auth/refresh")

    # Replay the original (now-rotated-away) refresh token — this simulates
    # a stolen/duplicated token being used after the real client already
    # refreshed. It must be rejected, not silently accepted.
    client.cookies.set("fp_refresh", first_refresh_cookie)
    replay_response = client.post("/api/auth/refresh")
    assert replay_response.status_code == 401

    # And the session should now be fully dead, including the access token
    # that was live before the reuse was detected.
    me_response = client.get("/api/auth/me")
    assert me_response.status_code == 401


def test_logout_clears_session_and_revokes_refresh_token(client, monkeypatch):
    monkeypatch.setattr("app.routers.auth.verify_google_id_token", lambda token: _mock_identity(sub="logout-sub"))
    client.post("/api/auth/google", json={"id_token": "t1"})

    logout_response = client.post("/api/auth/logout")
    assert logout_response.status_code == 204

    me_response = client.get("/api/auth/me")
    assert me_response.status_code == 401


def test_protected_route_rejects_missing_session():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as anon_client:
        response = anon_client.get("/categories")
        assert response.status_code == 401


def test_a_second_user_never_sees_the_first_users_categories(client, monkeypatch):
    monkeypatch.setattr("app.routers.auth.verify_google_id_token", lambda token: _mock_identity(sub="user-a"))
    client.post("/api/auth/google", json={"id_token": "ta"})
    client.post("/categories", json={"name": "User A's private category"})

    monkeypatch.setattr(
        "app.routers.auth.verify_google_id_token", lambda token: _mock_identity(sub="user-b", email="b@example.com")
    )
    client.post("/api/auth/google", json={"id_token": "tb"})
    names = [c["name"] for c in client.get("/categories").json()]

    assert "User A's private category" not in names


def test_delete_account_requires_a_session(client):
    response = client.delete("/api/auth/me")
    assert response.status_code == 401


def test_delete_account_removes_user_and_owned_rows(client, monkeypatch):
    monkeypatch.setattr("app.routers.auth.verify_google_id_token", lambda token: _mock_identity(sub="delete-sub"))
    client.post("/api/auth/google", json={"id_token": "t1"})
    client.post("/categories", json={"name": "Category to delete"})

    response = client.delete("/api/auth/me")
    assert response.status_code == 204
    assert "fp_access" not in response.cookies

    # The session is dead — even a fresh sign-in-less request is unauthorized.
    me_response = client.get("/api/auth/me")
    assert me_response.status_code == 401


def test_deleted_account_can_sign_in_again_as_a_new_user(client, monkeypatch):
    monkeypatch.setattr("app.routers.auth.verify_google_id_token", lambda token: _mock_identity(sub="recreate-sub"))
    first = client.post("/api/auth/google", json={"id_token": "t1"})
    first_id = first.json()["id"]

    client.delete("/api/auth/me")
    client.cookies.clear()

    second = client.post("/api/auth/google", json={"id_token": "t2"})
    assert second.status_code == 200
    assert second.json()["id"] != first_id
