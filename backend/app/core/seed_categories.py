from sqlalchemy.orm import Session

from app.models.category import SYSTEM_CATEGORIES, Category


def ensure_system_categories(db: Session) -> None:
    existing = {c.name for c in db.query(Category.name).all()}
    for name in SYSTEM_CATEGORIES:
        if name not in existing:
            db.add(Category(name=name, is_system=True))
    db.commit()
