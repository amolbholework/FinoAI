"""Health Checker endpoint tests. The critical property here (per the spec)
is inertness: disabling the feature flag must not change any other
endpoint's behavior, and the endpoint itself must simply stop existing
(404) rather than degrade."""
from datetime import date

from app.core.config import Settings
from app.models.category import Category
from app.models.transaction import Transaction


def _seed_transactions(db_session, user_id):
    category = db_session.query(Category).filter(Category.name == "Food", Category.is_system.is_(True)).one()
    for month in (1, 2, 3):
        db_session.add(
            Transaction(
                user_id=user_id,
                date=date(2026, month, 1),
                description="Salary",
                raw_description="Salary",
                amount_minor=50_000,
                category_id=None,
            )
        )
        db_session.add(
            Transaction(
                user_id=user_id,
                date=date(2026, month, 15),
                description="Groceries",
                raw_description="Groceries",
                amount_minor=-10_000,
                category_id=category.id,
            )
        )
    db_session.commit()


def test_health_score_endpoint_returns_valid_shape(auth_client, test_user, db_session):
    _seed_transactions(db_session, test_user.id)
    response = auth_client.get("/api/health/score")
    assert response.status_code == 200
    body = response.json()
    assert body["score"] is not None
    assert body["band"] in ("Needs attention", "Getting there", "Stable", "Strong")
    assert len(body["pillars"]) == 5
    assert isinstance(body["top_levers"], list)
    assert isinstance(body["trend"], list)


def test_disabling_flag_returns_404(auth_client, monkeypatch):
    disabled = Settings(health_checker_enabled=False)
    monkeypatch.setattr("app.routers.health.get_settings", lambda: disabled)
    response = auth_client.get("/api/health/score")
    assert response.status_code == 404


def test_disabling_flag_does_not_affect_other_endpoints(auth_client, test_user, db_session, monkeypatch):
    _seed_transactions(db_session, test_user.id)

    before = {
        "balance": auth_client.get("/analysis/balance").json(),
        "categories": auth_client.get("/categories").json(),
        "transactions": auth_client.get("/transactions").json(),
        "budget_adherence": auth_client.get("/analysis/budget-adherence").json(),
    }

    disabled = Settings(health_checker_enabled=False)
    monkeypatch.setattr("app.routers.health.get_settings", lambda: disabled)

    after = {
        "balance": auth_client.get("/analysis/balance").json(),
        "categories": auth_client.get("/categories").json(),
        "transactions": auth_client.get("/transactions").json(),
        "budget_adherence": auth_client.get("/analysis/budget-adherence").json(),
    }

    assert before == after
