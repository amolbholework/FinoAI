from datetime import date

from sqlalchemy.orm import Session

from app.categorization import classifier
from app.categorization.service import categorize
from app.ingestion.csv_parser import ColumnMapping, normalize_rows
from app.ingestion.dedup import dedupe
from app.models.category import Category, owned_or_system
from app.models.transaction import Transaction


def commit_rows(
    db: Session,
    raw: bytes,
    mapping: ColumnMapping,
    user_id: str,
    category_overrides: dict[int, str] | None = None,
) -> tuple[int, int, int]:
    """Returns (inserted, duplicates_skipped, unparseable_skipped).

    category_overrides maps a row's original CSV position (NormalizedRow.
    source_row_index) to a category name — this is how a user's edit in the
    preview table actually gets applied, rather than being cosmetic."""
    category_overrides = category_overrides or {}
    all_rows, unparseable = normalize_rows(raw, mapping)
    to_insert, duplicates = dedupe(db, all_rows, user_id)

    any_override_applied = False

    for row in to_insert:
        override_name = category_overrides.get(row.source_row_index)
        if override_name:
            override_category = (
                db.query(Category)
                .filter(Category.name == override_name, owned_or_system(user_id))
                .first()
            )
        else:
            override_category = None

        if override_category:
            category_id = override_category.id
            category_confirmed = True  # the user picked this, not a guess
            any_override_applied = True
        else:
            category_id, _confident = categorize(db, row.description, user_id)
            category_confirmed = False

        db.add(
            Transaction(
                user_id=user_id,
                date=date.fromisoformat(row.date),
                description=row.description,
                raw_description=row.description,
                amount_minor=row.amount_minor,
                category_id=category_id,
                category_confirmed=category_confirmed,
                source="csv",
            )
        )

    db.commit()

    if any_override_applied:
        classifier.train(db, user_id)

    return len(to_insert), duplicates, unparseable
