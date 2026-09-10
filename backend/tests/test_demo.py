"""Test/demo mode — the critical property is isolation: toggling test mode
on for a real account must never expose, mutate, or delete that account's
real data, and turning it back off must restore exactly what was there
before. These tests exist specifically to prove that."""
from app.models.transaction import Transaction
from app.models.user import User


def test_try_demo_requires_no_prior_session(client):
    response = client.post("/api/demo/try")
    assert response.status_code == 200
    body = response.json()
    assert body["is_demo"] is True
    assert body["onboarding_status"] == "completed"


def test_try_demo_seeds_a_full_usable_account(client):
    client.post("/api/demo/try")

    transactions = client.get("/transactions").json()
    goals = client.get("/goals").json()
    fino_history = client.get("/api/fino/messages").json()

    assert len(transactions) > 50  # ~14 months of realistic activity
    assert len(goals) == 3
    assert len(fino_history) > 0


def test_demo_seed_is_reproducible_across_separate_sessions(client):
    """Same seed -> same shape of data every time, even though each guest
    gets its own user_id — this is what makes a demo re-presentable."""
    client.post("/api/demo/try")
    transactions_a = client.get("/transactions").json()
    goals_a = client.get("/goals").json()
    client.post("/api/auth/logout")

    client.post("/api/demo/try")
    transactions_b = client.get("/transactions").json()
    goals_b = client.get("/goals").json()

    assert len(transactions_a) == len(transactions_b)
    assert sorted(t["amount_minor"] for t in transactions_a) == sorted(t["amount_minor"] for t in transactions_b)
    assert [g["name"] for g in goals_a] == [g["name"] for g in goals_b]
    assert [g["saved_amount_minor"] for g in goals_a] == [g["saved_amount_minor"] for g in goals_b]


def test_enabling_test_mode_hides_real_data_and_shows_demo_data(auth_client):
    real = auth_client.post("/transactions", json={"date": "2026-01-15", "description": "Real paycheck", "amount_minor": 500000}).json()
    assert real["description"] == "Real paycheck"

    response = auth_client.post("/api/demo/enable")
    assert response.status_code == 200
    assert response.json()["test_mode_enabled"] is True

    transactions = auth_client.get("/transactions").json()
    descriptions = [t["description"] for t in transactions]
    assert "Real paycheck" not in descriptions
    assert len(transactions) > 50


def test_disabling_test_mode_restores_the_real_account_untouched(auth_client):
    created = auth_client.post(
        "/transactions", json={"date": "2026-01-15", "description": "Real paycheck", "amount_minor": 500000}
    ).json()
    real_id, real_amount = created["id"], created["amount_minor"]

    auth_client.post("/api/demo/enable")
    auth_client.get("/transactions")  # exercise the demo view
    auth_client.post("/api/demo/disable")

    transactions = auth_client.get("/transactions").json()
    assert len(transactions) == 1
    assert transactions[0]["description"] == "Real paycheck"
    assert transactions[0]["id"] == real_id
    assert transactions[0]["amount_minor"] == real_amount


def test_writes_made_while_in_test_mode_never_touch_the_real_account(auth_client, db_session, test_user):
    auth_client.post("/transactions", json={"date": "2026-01-15", "description": "Real paycheck", "amount_minor": 500000})
    auth_client.post("/api/demo/enable")

    auth_client.post("/transactions", json={"date": "2026-02-01", "description": "Demo-only purchase", "amount_minor": -1000})

    real_transactions = db_session.query(Transaction).filter(Transaction.user_id == test_user.id).all()
    real_descriptions = [t.description for t in real_transactions]
    assert "Demo-only purchase" not in real_descriptions
    assert "Real paycheck" in real_descriptions
    assert len(real_transactions) == 1  # only the one real transaction, never touched


def test_enabling_test_mode_twice_reuses_the_same_shadow_account(auth_client, db_session, test_user):
    auth_client.post("/api/demo/enable")
    db_session.refresh(test_user)
    shadow_id_first = test_user.demo_shadow_user_id

    auth_client.post("/api/demo/disable")
    auth_client.post("/api/demo/enable")
    db_session.refresh(test_user)

    assert test_user.demo_shadow_user_id == shadow_id_first


def test_cannot_enable_test_mode_on_a_demo_account(client):
    client.post("/api/demo/try")
    response = client.post("/api/demo/enable")
    assert response.status_code == 400


def test_deleting_account_removes_the_linked_shadow_demo_account_too(auth_client, db_session, test_user):
    auth_client.post("/api/demo/enable")
    db_session.refresh(test_user)
    shadow_id = test_user.demo_shadow_user_id
    assert shadow_id is not None

    response = auth_client.delete("/api/auth/me")
    assert response.status_code == 204

    assert db_session.query(User).filter(User.id == shadow_id).first() is None
    assert db_session.query(Transaction).filter(Transaction.user_id == shadow_id).count() == 0


def test_me_reflects_test_mode_state(auth_client):
    assert auth_client.get("/api/auth/me").json()["test_mode_enabled"] is False
    auth_client.post("/api/demo/enable")
    assert auth_client.get("/api/auth/me").json()["test_mode_enabled"] is True
    auth_client.post("/api/demo/disable")
    assert auth_client.get("/api/auth/me").json()["test_mode_enabled"] is False
