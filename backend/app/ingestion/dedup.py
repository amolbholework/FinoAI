from datetime import date

from sqlalchemy.orm import Session

from app.ingestion.csv_parser import NormalizedRow
from app.models.transaction import Transaction


def existing_keys(db: Session, dates: list[date], user_id: str) -> set[tuple[date, int, str]]:
    """Fetches (date, amount_minor, raw_description) for this user's existing
    rows in the given date range, so re-uploading an overlapping statement
    doesn't duplicate transactions already committed."""
    if not dates:
        return set()

    rows = (
        db.query(Transaction.date, Transaction.amount_minor, Transaction.raw_description)
        .filter(Transaction.date.in_(dates), Transaction.user_id == user_id)
        .all()
    )
    return {(d, amt, desc) for d, amt, desc in rows}


def dedupe(db: Session, rows: list[NormalizedRow], user_id: str) -> tuple[list[NormalizedRow], int]:
    """Returns (rows_to_insert, duplicate_count). Also drops duplicates
    within the same upload batch."""
    dates = [date.fromisoformat(r.date) for r in rows]
    existing = existing_keys(db, dates, user_id)

    seen_in_batch: set[tuple[str, int, str]] = set()
    kept: list[NormalizedRow] = []
    duplicates = 0

    for row in rows:
        key = (date.fromisoformat(row.date), row.amount_minor, row.description)
        batch_key = (row.date, row.amount_minor, row.description)
        if key in existing or batch_key in seen_in_batch:
            duplicates += 1
            continue
        seen_in_batch.add(batch_key)
        kept.append(row)

    return kept, duplicates
