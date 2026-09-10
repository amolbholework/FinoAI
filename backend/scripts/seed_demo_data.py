"""Seeds ~12 months of realistic synthetic transactions so the dashboard is
never empty in a demo. Deterministic (fixed seed) so forecasting/analysis
screenshots in the report stay reproducible.

Run from backend/ with the venv active:
    python -m scripts.seed_demo_data [--reset]
"""
import argparse
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.seed_categories import ensure_system_categories  # noqa: E402
from app.models.category import Category  # noqa: E402
from app.models.transaction import Transaction  # noqa: E402

RNG_SEED = 42
MONTHS_OF_HISTORY = 12


def _rupees(amount: float) -> int:
    return round(amount * 100)


def _add_txn(db, cat_ids: dict[str, str], d: date, description: str, amount_rupees: float, category: str):
    # Signed, smallest-unit convention: income is positive, every other
    # category is a spend and must be negative.
    signed_amount = amount_rupees if category == "Income" else -amount_rupees
    db.add(
        Transaction(
            date=d,
            description=description,
            raw_description=description,
            amount_minor=_rupees(signed_amount),
            category_id=cat_ids[category],
            category_confirmed=True,
            source="csv",
        )
    )


def generate(db, rng: random.Random) -> None:
    cat_ids = {c.name: c.id for c in db.query(Category).all()}

    today = date.today()
    first_month = date(today.year, today.month, 1)
    months = []
    y, m = first_month.year, first_month.month
    for _ in range(MONTHS_OF_HISTORY):
        months.append(date(y, m, 1))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    months.reverse()  # oldest first

    food_vendors = ["Swiggy", "Zomato", "Local Cafe", "Grocery Mart", "Bakery Corner", "Supermarket"]
    transport_vendors = ["Uber", "Ola", "Metro Card Recharge", "Petrol Pump", "IRCTC"]
    shopping_vendors = ["Amazon", "Flipkart", "Myntra", "Local Store"]
    entertainment_vendors = ["Netflix", "Spotify", "BookMyShow", "Cinema Hall", "Prime Video"]
    health_vendors = ["Apollo Pharmacy", "City Clinic", "Diagnostic Lab"]

    for i, month_start in enumerate(months):
        next_month = date(month_start.year + (1 if month_start.month == 12 else 0), (month_start.month % 12) + 1, 1)
        is_current_month = month_start.year == today.year and month_start.month == today.month
        # Don't fabricate transactions dated after today for the in-progress month.
        days_in_month = today.day if is_current_month else (next_month - month_start).days

        # Income: salary on the 1st, with a small raise partway through the year.
        salary = 55000 + (3000 if i >= 6 else 0) + rng.randint(-500, 500)
        _add_txn(db, cat_ids, month_start, "Salary credit", salary, "Income")

        # Rent: fixed, on the 3rd (or the last available day, for a not-yet-3-days-old current month).
        rent_day = min(2, days_in_month - 1)
        _add_txn(db, cat_ids, month_start + timedelta(days=rent_day), "Monthly rent", 15000, "Rent")

        # Utilities: 2-3 bills early in the month.
        for _ in range(rng.randint(2, 3)):
            day = min(rng.randint(1, 10), days_in_month - 1)
            amount = rng.uniform(400, 1500)
            _add_txn(db, cat_ids, month_start + timedelta(days=day), "Utility bill payment", amount, "Utilities")

        # Food: several a week, with a gentle upward drift in the last 3 months
        # (gives the trend detector something real to flag).
        food_multiplier = 1.35 if i >= MONTHS_OF_HISTORY - 3 else 1.0
        for _ in range(rng.randint(14, 20)):
            day = rng.randint(0, days_in_month - 1)
            amount = rng.uniform(150, 900) * food_multiplier
            vendor = rng.choice(food_vendors)
            _add_txn(db, cat_ids, month_start + timedelta(days=day), vendor, amount, "Food")

        # Transport: several a week.
        for _ in range(rng.randint(10, 16)):
            day = rng.randint(0, days_in_month - 1)
            amount = rng.uniform(50, 450)
            vendor = rng.choice(transport_vendors)
            _add_txn(db, cat_ids, month_start + timedelta(days=day), vendor, amount, "Transport")

        # Shopping: a handful a month.
        for _ in range(rng.randint(2, 5)):
            day = rng.randint(0, days_in_month - 1)
            amount = rng.uniform(500, 4000)
            vendor = rng.choice(shopping_vendors)
            _add_txn(db, cat_ids, month_start + timedelta(days=day), vendor, amount, "Shopping")

        # Entertainment: subscriptions plus occasional outings.
        for _ in range(rng.randint(2, 4)):
            day = rng.randint(0, days_in_month - 1)
            amount = rng.uniform(200, 1800)
            vendor = rng.choice(entertainment_vendors)
            _add_txn(db, cat_ids, month_start + timedelta(days=day), vendor, amount, "Entertainment")

        # Health: occasional.
        if rng.random() < 0.6:
            day = rng.randint(0, days_in_month - 1)
            amount = rng.uniform(300, 2500)
            vendor = rng.choice(health_vendors)
            _add_txn(db, cat_ids, month_start + timedelta(days=day), vendor, amount, "Health")

        # A couple of deliberate anomalies for the anomaly detector to catch.
        if i == MONTHS_OF_HISTORY - 4:
            _add_txn(db, cat_ids, month_start + timedelta(days=15), "Emergency dental treatment", 9500, "Health")
        if i == MONTHS_OF_HISTORY - 2:
            _add_txn(db, cat_ids, month_start + timedelta(days=8), "Laptop purchase", 62000, "Shopping")

    db.commit()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="delete existing transactions before seeding")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ensure_system_categories(db)

        if args.reset:
            db.query(Transaction).delete()
            db.commit()
        elif db.query(Transaction).count() > 0:
            print("Transactions already exist — pass --reset to wipe and reseed.")
            return

        generate(db, random.Random(RNG_SEED))
        count = db.query(Transaction).count()
        print(f"Seeded {count} transactions across {MONTHS_OF_HISTORY} months.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
