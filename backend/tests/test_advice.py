from datetime import date

import pytest
from pydantic import ValidationError

from app.ai.advice import _call_with_retry
from app.ai.advice_fallback import generate_fallback_advice
from app.ai.advice_schema import AdviceOutput
from app.ai.advice_summary import advice_data_version
from app.llm.base import LLMUnavailableError, LLMValidationError
from app.models.category import Category
from app.models.transaction import Transaction

VALID_PAYLOAD = {
    "headline": "You're saving a healthy share of income this month.",
    "health_score": 72,
    "insights": [
        {
            "title": "Food spending is rising",
            "detail": "Food spend is 20% above your 3-month average.",
            "evidence": {"metric": "Food spend", "value": "₹6000", "period": "2026-03"},
            "severity": "watch",
        }
    ],
    "recommendations": [
        {
            "action": "Cap discretionary Shopping spend",
            "why": "Shopping is 15% above budget this month.",
            "impact_inr_per_month": 1500,
            "effort": "low",
            "category": "budget",
            "horizon": "this_month",
            "linked_goal": None,
            "goal_impact": None,
        }
    ],
    "questions_to_consider": ["Is your emergency fund on track?"],
}


def test_advice_output_accepts_valid_payload():
    output = AdviceOutput.model_validate(VALID_PAYLOAD)
    assert output.health_score == 72
    assert output.recommendations[0].category == "budget"


def test_advice_output_rejects_invalid_severity():
    bad = {**VALID_PAYLOAD, "insights": [{**VALID_PAYLOAD["insights"][0], "severity": "critical"}]}
    with pytest.raises(ValidationError):
        AdviceOutput.model_validate(bad)


def test_advice_output_rejects_out_of_range_health_score():
    bad = {**VALID_PAYLOAD, "health_score": 150}
    with pytest.raises(ValidationError):
        AdviceOutput.model_validate(bad)


def test_call_with_retry_returns_none_after_repeated_failure(monkeypatch):
    def always_fails(summary):
        raise LLMUnavailableError("simulated outage")

    monkeypatch.setattr("app.ai.advice._generate", always_fails)
    assert _call_with_retry({"some": "summary"}) is None


def test_call_with_retry_recovers_on_second_attempt(monkeypatch):
    calls = {"count": 0}

    def fails_once_then_succeeds(summary):
        calls["count"] += 1
        if calls["count"] == 1:
            raise LLMValidationError("missing fields")
        return AdviceOutput.model_validate(VALID_PAYLOAD)

    monkeypatch.setattr("app.ai.advice._generate", fails_once_then_succeeds)
    result = _call_with_retry({"some": "summary"})
    assert result is not None
    assert result.headline == VALID_PAYLOAD["headline"]


def test_data_version_is_stable_across_non_deterministic_forecast_noise():
    # Prophet's fit can differ by a paisa between calls on identical input —
    # data_version must not flip just because next_month_forecast wobbled,
    # or caching (and dismiss/done persistence, which is keyed off it) breaks.
    base = {"latest_month": "2026-03", "trends": [], "goals": []}
    version_a = advice_data_version({**base, "next_month_forecast": {"predicted_total": 100.0, "low": 90.0, "high": 110.0}})
    version_b = advice_data_version({**base, "next_month_forecast": {"predicted_total": 100.01, "low": 89.99, "high": 110.02}})
    assert version_a == version_b


def test_data_version_changes_when_real_data_changes():
    version_a = advice_data_version({"latest_month": "2026-03", "trends": []})
    version_b = advice_data_version({"latest_month": "2026-04", "trends": []})
    assert version_a != version_b


def test_fallback_advice_echoes_deterministic_score_and_flags_over_budget():
    summary = {
        "deterministic_health_score": {"score": 55, "band": "Getting there", "is_provisional": False},
        "trends": [],
        "category_month_anomalies": [],
        "budget_adherence": [{"category": "Food", "limit": 5000, "spent": 6000, "pct_used": 120.0, "is_over": True}],
        "goals": [],
        "latest_month": "2026-03",
    }
    output = generate_fallback_advice(summary)
    assert output.health_score == 55
    assert any("Food" in r.action for r in output.recommendations)
    food_rec = next(r for r in output.recommendations if "Food" in r.action)
    assert food_rec.horizon == "this_month"
    assert food_rec.linked_goal is None


def test_fallback_advice_links_goal_and_sets_horizon_by_distance():
    summary = {
        "deterministic_health_score": {"score": 60, "band": "Stable", "is_provisional": False},
        "trends": [],
        "category_month_anomalies": [],
        "budget_adherence": [],
        "goals": [
            {"name": "Goa trip", "target_amount": 60000, "saved_amount": 15000, "target_date": "2026-05-01", "progress_pct": 25.0}
        ],
        "latest_month": "2026-03",
    }
    output = generate_fallback_advice(summary)
    goal_rec = next(r for r in output.recommendations if r.linked_goal == "Goa trip")
    assert goal_rec.horizon == "next_3_months"  # 2 months from 2026-03 to 2026-05
    assert goal_rec.goal_impact is not None


def test_fallback_advice_uses_neutral_score_when_none_computed():
    summary = {"deterministic_health_score": {"score": None, "band": None, "is_provisional": True}, "trends": [], "category_month_anomalies": [], "budget_adherence": [], "goals": []}
    output = generate_fallback_advice(summary)
    assert output.health_score == 50


def _seed(db_session, user_id):
    category = db_session.query(Category).filter(Category.name == "Shopping", Category.is_system.is_(True)).one()
    for month in (1, 2, 3):
        db_session.add(
            Transaction(
                user_id=user_id, date=date(2026, month, 1), description="Salary", raw_description="Salary",
                amount_minor=60_000, category_id=None,
            )
        )
        db_session.add(
            Transaction(
                user_id=user_id, date=date(2026, month, 15), description="Shopping", raw_description="Shopping",
                amount_minor=-10_000, category_id=category.id,
            )
        )
    db_session.commit()


def test_post_advice_endpoint_caches_and_serves_from_cache(auth_client, test_user, db_session, monkeypatch):
    _seed(db_session, test_user.id)

    calls = {"count": 0}

    def fake_generate(summary):
        calls["count"] += 1
        return AdviceOutput.model_validate(VALID_PAYLOAD)

    monkeypatch.setattr("app.ai.advice._generate", fake_generate)

    first = auth_client.post("/api/advice")
    assert first.status_code == 200
    body = first.json()
    assert body["cached"] is False
    assert body["is_fallback"] is False
    assert body["headline"] == VALID_PAYLOAD["headline"]
    assert len(body["recommendations"]) == 1
    assert body["recommendations"][0]["status"] == "pending"
    assert calls["count"] == 1

    second = auth_client.post("/api/advice")
    assert second.status_code == 200
    assert second.json()["cached"] is True
    assert calls["count"] == 1  # served from cache, no second LLM call

    third = auth_client.post("/api/advice", params={"force_refresh": True})
    assert third.status_code == 200
    assert third.json()["cached"] is False
    assert calls["count"] == 2


def test_post_advice_falls_back_when_llm_unavailable(auth_client, test_user, db_session, monkeypatch):
    _seed(db_session, test_user.id)

    def always_fails(summary):
        raise LLMUnavailableError("simulated outage")

    monkeypatch.setattr("app.ai.advice._generate", always_fails)

    response = auth_client.post("/api/advice")
    assert response.status_code == 200
    body = response.json()
    assert body["is_fallback"] is True
    assert body["health_score"] is not None


def test_recommendation_status_persists_across_cached_fetch(auth_client, test_user, db_session, monkeypatch):
    _seed(db_session, test_user.id)
    monkeypatch.setattr("app.ai.advice._generate", lambda summary: AdviceOutput.model_validate(VALID_PAYLOAD))

    first = auth_client.post("/api/advice").json()
    rec_id = first["recommendations"][0]["id"]

    patch_response = auth_client.patch(f"/api/advice/recommendations/{rec_id}/status", json={"status": "done"})
    assert patch_response.status_code == 200
    assert patch_response.json()["status"] == "done"

    second = auth_client.post("/api/advice").json()
    assert second["cached"] is True
    assert second["recommendations"][0]["status"] == "done"


def test_recommendation_status_rejects_unknown_status(auth_client, test_user, db_session, monkeypatch):
    _seed(db_session, test_user.id)
    monkeypatch.setattr("app.ai.advice._generate", lambda summary: AdviceOutput.model_validate(VALID_PAYLOAD))

    first = auth_client.post("/api/advice").json()
    rec_id = first["recommendations"][0]["id"]

    response = auth_client.patch(f"/api/advice/recommendations/{rec_id}/status", json={"status": "archived"})
    assert response.status_code == 400


def test_recommendation_includes_horizon_and_goal_fields(auth_client, test_user, db_session, monkeypatch):
    _seed(db_session, test_user.id)
    monkeypatch.setattr("app.ai.advice._generate", lambda summary: AdviceOutput.model_validate(VALID_PAYLOAD))

    body = auth_client.post("/api/advice").json()
    rec = body["recommendations"][0]
    assert rec["horizon"] == "this_month"
    assert rec["linked_goal"] is None
    assert rec["goal_impact"] is None


def test_advice_history_returns_most_recent_first(auth_client, test_user, db_session, monkeypatch):
    _seed(db_session, test_user.id)
    monkeypatch.setattr("app.ai.advice._generate", lambda summary: AdviceOutput.model_validate(VALID_PAYLOAD))

    first_id = auth_client.post("/api/advice").json()["advice_id"]
    second_id = auth_client.post("/api/advice", params={"force_refresh": True}).json()["advice_id"]
    assert first_id != second_id

    history = auth_client.get("/api/advice/history").json()
    assert history[0]["advice_id"] == second_id
    assert any(h["advice_id"] == first_id for h in history)
