from datetime import date, datetime, timedelta, timezone

from app.forecasting.series import month_str_to_date
from app.models.category import Category
from app.models.forecast import Forecast
from app.models.transaction import Transaction


def _last_completed_month():
    today = datetime.now(timezone.utc).date()
    month = today.month - 1 or 12
    year = today.year if today.month > 1 else today.year - 1
    return year, month


def test_horizon_rejects_invalid_months(auth_client):
    response = auth_client.get("/forecasts/horizon", params={"months": 2})
    assert response.status_code == 400


def test_horizon_cold_start_with_no_transactions(auth_client):
    response = auth_client.get("/forecasts/horizon", params={"months": 3})
    assert response.status_code == 200
    body = response.json()
    assert len(body["months"]) == 3
    assert body["history_months"] == 0
    assert body["is_low_confidence"] is True
    assert body["accuracy"] is None
    assert body["category_drivers"] == []


def test_horizon_includes_accuracy_panel_when_a_past_forecast_exists(auth_client, test_user, db_session):
    year, month = _last_completed_month()
    horizon_first = month_str_to_date(f"{year:04d}-{month:02d}")

    category = db_session.query(Category).filter(Category.name == "Food", Category.is_system.is_(True)).one()
    db_session.add(
        Transaction(
            user_id=test_user.id,
            date=date(year, month, 5),
            description="Groceries",
            raw_description="Groceries",
            amount_minor=-5000,
            category_id=category.id,
        )
    )
    db_session.add(
        Forecast(
            user_id=test_user.id,
            horizon_month=horizon_first,
            predicted_total_minor=6000,
            confidence_low_minor=4000,
            confidence_high_minor=8000,
            per_category_breakdown={},
            model_used="average_fallback",
        )
    )
    db_session.commit()

    response = auth_client.get("/forecasts/horizon", params={"months": 1})
    assert response.status_code == 200
    accuracy = response.json()["accuracy"]
    assert accuracy is not None
    assert accuracy["predicted_minor"] == 6000
    assert accuracy["actual_minor"] == 5000
    assert accuracy["error_minor"] == 1000
