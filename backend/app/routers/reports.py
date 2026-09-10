from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_effective_user
from app.forecasting.generate import load_records
from app.models.transaction import Transaction
from app.models.user import User
from app.reports.csv_export import transactions_to_csv
from app.reports.monthly_summary import build_monthly_summary
from app.reports.pdf import build_monthly_summary_pdf

router = APIRouter(prefix="/reports", tags=["reports"])


def _latest_month(db: Session, user_id: str) -> str | None:
    records = load_records(db, user_id)
    months = sorted({f"{r.date.year:04d}-{r.date.month:02d}" for r in records})
    return months[-1] if months else None


@router.get("/monthly-summary")
def monthly_summary(
    month: str | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_effective_user)
):
    month = month or _latest_month(db, current_user.id)
    if not month:
        return {"month": None, "total_spend_minor": 0, "category_breakdown_minor": {}, "income_minor": 0, "net_minor": 0, "savings_rate_pct": 0.0}
    return build_monthly_summary(load_records(db, current_user.id), month)


@router.get("/monthly-summary/export.pdf")
def export_monthly_summary_pdf(
    month: str | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_effective_user)
):
    month = month or _latest_month(db, current_user.id)
    summary = (
        build_monthly_summary(load_records(db, current_user.id), month)
        if month
        else {"month": "—", "total_spend_minor": 0, "category_breakdown_minor": {}, "income_minor": 0, "net_minor": 0, "savings_rate_pct": 0.0}
    )
    pdf_bytes = build_monthly_summary_pdf(summary)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="finpilot-summary-{month or "empty"}.pdf"'},
    )


@router.get("/transactions/export.csv")
def export_transactions_csv(db: Session = Depends(get_db), current_user: User = Depends(get_effective_user)):
    transactions = (
        db.query(Transaction).filter(Transaction.user_id == current_user.id).order_by(Transaction.date).all()
    )
    csv_text = transactions_to_csv(transactions)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="finpilot-transactions.csv"'},
    )
