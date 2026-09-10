from dataclasses import replace
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.analysis.anomalies import detect_category_month_anomalies, detect_transaction_anomalies
from app.analysis.budgets import budget_adherence
from app.analysis.dashboard import (
    daily_burn_series,
    projected_month_end_spend,
    remaining_budget,
    spend_to_date_comparison,
    top_categories,
)
from app.analysis.monthly import category_breakdown, monthly_category_breakdown, monthly_spend_totals
from app.analysis.savings import monthly_savings_rate
from app.analysis.trends import detect_trends
from app.core.database import get_db
from app.core.security import get_effective_user
from app.forecasting.generate import load_records
from app.models.budget import Budget
from app.models.category import Category
from app.models.user import User

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/monthly-totals")
def get_monthly_totals(db: Session = Depends(get_db), current_user: User = Depends(get_effective_user)):
    return monthly_spend_totals(load_records(db, current_user.id))


@router.get("/category-breakdown")
def get_category_breakdown(
    month: str | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_effective_user)
):
    return category_breakdown(load_records(db, current_user.id), month=month)


@router.get("/monthly-category-breakdown")
def get_monthly_category_breakdown(db: Session = Depends(get_db), current_user: User = Depends(get_effective_user)):
    return monthly_category_breakdown(load_records(db, current_user.id))


@router.get("/trends")
def get_trends(db: Session = Depends(get_db), current_user: User = Depends(get_effective_user)):
    return detect_trends(load_records(db, current_user.id))


@router.get("/anomalies")
def get_anomalies(db: Session = Depends(get_db), current_user: User = Depends(get_effective_user)):
    records = load_records(db, current_user.id)
    return {
        "transactions": detect_transaction_anomalies(records),
        "category_months": detect_category_month_anomalies(records),
    }


@router.get("/savings-rate")
def get_savings_rate(db: Session = Depends(get_db), current_user: User = Depends(get_effective_user)):
    return monthly_savings_rate(load_records(db, current_user.id))


@router.get("/balance")
def get_balance(db: Session = Depends(get_db), current_user: User = Depends(get_effective_user)):
    """All-time net balance (income minus spend). Not a real bank balance —
    there's no starting-balance concept in this model — but the closest
    honest proxy for the dashboard's hero figure."""
    records = load_records(db, current_user.id)
    return {"balance_minor": sum(r.amount_minor for r in records)}


@router.get("/budget-adherence")
def get_budget_adherence(
    month: str | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_effective_user)
):
    records = load_records(db, current_user.id)
    budget_rows = (
        db.query(Budget, Category)
        .join(Category, Budget.category_id == Category.id)
        .filter(Budget.user_id == current_user.id)
        .all()
    )
    budgets_minor = {cat.name: b.monthly_limit_minor for b, cat in budget_rows}
    return budget_adherence(records, budgets_minor, month=month)


@router.get("/dashboard-summary")
def get_dashboard_summary(db: Session = Depends(get_db), current_user: User = Depends(get_effective_user)):
    """Everything the dashboard's above-the-fold "four questions" need in one
    call: pace vs. last month, the daily burn-rate series, remaining budget
    (with a naive month-end projection for the on-track read), and the
    top-3-plus-Other category split."""
    records = load_records(db, current_user.id)
    as_of = datetime.now(timezone.utc).date()

    budget_rows = (
        db.query(Budget, Category)
        .join(Category, Budget.category_id == Category.id)
        .filter(Budget.user_id == current_user.id)
        .all()
    )
    budgets_minor = {cat.name: b.monthly_limit_minor for b, cat in budget_rows}

    spend_to_date = spend_to_date_comparison(records, as_of)
    if spend_to_date.pct_change == float("inf"):
        # json.dumps renders inf as the bare token `Infinity`, which is not
        # valid JSON and breaks response.json() in the browser — same
        # sanitization ai/summary.py already does at its API boundary.
        spend_to_date = replace(spend_to_date, pct_change=None)

    return {
        "as_of": as_of.isoformat(),
        "spend_to_date": spend_to_date,
        "daily_burn": daily_burn_series(records, as_of),
        "projected_month_end_spend_minor": projected_month_end_spend(records, as_of),
        "remaining_budget": remaining_budget(records, budgets_minor),
        "top_categories": top_categories(records, top_n=3),
    }
