"""Endpoint-level test for /analysis/dashboard-summary — specifically that
its response is always valid JSON. spend_to_date.pct_change is float('inf')
whenever there's no prior-month spend to compare against (e.g. a brand new
account's first transactions), and json.dumps renders that as the bare
token `Infinity`, which response.json() in the browser cannot parse."""
from datetime import date, timedelta

from app.models.category import Category
from app.models.transaction import Transaction


def test_dashboard_summary_is_valid_json_with_no_prior_month_spend(auth_client, test_user, db_session):
    category = db_session.query(Category).filter(Category.name == "Food", Category.is_system.is_(True)).one()

    today = date.today()
    db_session.add(
        Transaction(
            user_id=test_user.id,
            date=today - timedelta(days=1),
            description="Groceries",
            raw_description="Groceries",
            amount_minor=-1500,
            category_id=category.id,
        )
    )
    db_session.commit()

    response = auth_client.get("/analysis/dashboard-summary")
    assert response.status_code == 200
    body = response.json()  # raises if the body isn't valid JSON
    assert body["spend_to_date"]["pct_change"] is None
