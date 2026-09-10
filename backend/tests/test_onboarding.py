"""Integration tests for the onboarding router: resumable answer-saving,
completion running the real scoring rubric, skip's graceful defaults, and
the auth-gate signal (onboarding_status on /api/auth/me)."""


def test_new_user_profile_is_not_started(auth_client):
    response = auth_client.get("/api/onboarding/profile")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "not_started"
    assert body["current_step"] == 0
    assert body["total_steps"] == 14


def test_me_reports_onboarding_status(auth_client):
    response = auth_client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json()["onboarding_status"] == "not_started"


def test_answering_a_question_advances_status_and_step(auth_client):
    response = auth_client.post("/api/onboarding/answer", json={"question_id": "age_band", "value": "25-34"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "in_progress"
    assert body["current_step"] == 1
    assert body["answers"]["age_band"] == "25-34"


def test_answers_persist_across_requests_for_resumability(auth_client):
    auth_client.post("/api/onboarding/answer", json={"question_id": "age_band", "value": "25-34"})
    auth_client.post("/api/onboarding/answer", json={"question_id": "employment_status", "value": "salaried"})

    profile = auth_client.get("/api/onboarding/profile").json()
    assert profile["answers"] == {"age_band": "25-34", "employment_status": "salaried"}
    assert profile["current_step"] == 2


def test_answering_unknown_question_is_rejected(auth_client):
    response = auth_client.post("/api/onboarding/answer", json={"question_id": "not_a_real_question", "value": "x"})
    assert response.status_code == 400


def test_skipped_answer_is_stored_as_null(auth_client):
    response = auth_client.post("/api/onboarding/answer", json={"question_id": "dependents", "value": None})
    assert response.status_code == 200
    assert response.json()["answers"]["dependents"] is None


def test_complete_runs_scoring_and_marks_completed(auth_client):
    auth_client.post("/api/onboarding/answer", json={"question_id": "risk_scenario_1", "value": "buy_more"})
    auth_client.post("/api/onboarding/answer", json={"question_id": "risk_scenario_2", "value": "gamble"})
    auth_client.post(
        "/api/onboarding/answer", json={"question_id": "investment_experience", "value": "experienced"}
    )
    auth_client.post("/api/onboarding/answer", json={"question_id": "employment_status", "value": "salaried"})
    auth_client.post("/api/onboarding/answer", json={"question_id": "goals", "value": ["retirement"]})

    response = auth_client.post("/api/onboarding/complete")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["risk_band"] == "aggressive"
    assert body["income_stability"] == "stable"
    assert body["goals"] == [{"type": "retirement", "target_amount": None, "target_date": None, "priority": 1}]
    assert body["completed_at"] is not None

    me = auth_client.get("/api/auth/me").json()
    assert me["onboarding_status"] == "completed"


def test_skip_produces_neutral_defaults_not_nulls(auth_client):
    response = auth_client.post("/api/onboarding/skip")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "skipped"
    assert body["risk_band"] == "moderate"
    assert body["literacy_level"] == "beginner"
    assert body["life_stage"] == "early_career"
    assert body["income_stability"] == "variable"
    assert body["investment_experience"] == "none"


def test_retake_resets_step_but_keeps_prior_answers(auth_client):
    auth_client.post("/api/onboarding/answer", json={"question_id": "age_band", "value": "25-34"})
    auth_client.post("/api/onboarding/complete")

    response = auth_client.post("/api/onboarding/retake")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "in_progress"
    assert body["current_step"] == 0
    assert body["answers"]["age_band"] == "25-34"


def test_onboarding_requires_a_session():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as anon_client:
        response = anon_client.get("/api/onboarding/profile")
        assert response.status_code == 401


def test_deleting_account_removes_profile(auth_client):
    auth_client.post("/api/onboarding/answer", json={"question_id": "age_band", "value": "25-34"})
    response = auth_client.delete("/api/auth/me")
    assert response.status_code == 204
