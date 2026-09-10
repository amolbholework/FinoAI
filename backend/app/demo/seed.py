"""Builds one complete, reproducible synthetic account: ~14 months of
transactions with believable seasonality, three goals at different
progress levels, a completed onboarding profile, and a short canned Fino
conversation. Everything is driven by `random.Random(seed)` — same seed,
byte-identical output, every run — which is the whole point of a demo you
might present more than once.

Market Academy progress and scam-trainer attempts are deliberately not
seeded: neither feature exists yet in this codebase. Seeding data for a
screen that doesn't exist would just be dead weight to delete later.
"""
import random
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.base import utcnow
from app.models.category import Category
from app.models.fino_message import FinoMessage
from app.models.goal import Goal
from app.models.recommendation import Recommendation
from app.models.transaction import Transaction
from app.models.user_profile import UserProfile
from app.onboarding.scoring import build_profile_fields

DEFAULT_SEED = 42
MONTHS_OF_HISTORY = 14

# Festival/shopping-season months (1-indexed) see a spending bump, matching
# the Diwali/wedding-season pattern called out in the spec.
FESTIVAL_MONTHS = {10, 11}

_MERCHANTS = {
    "Food": ["Swiggy", "Zomato", "Big Bazaar", "Local Kirana Store", "Dominos", "Cafe Coffee Day"],
    "Transport": ["Uber", "Ola", "IndianOil Petrol Pump", "Metro Card Recharge"],
    "Utilities": ["Electricity Board", "Airtel Broadband", "Jio Recharge", "Water Board"],
    "Shopping": ["Amazon", "Flipkart", "Myntra", "Local Market"],
    "Entertainment": ["BookMyShow", "Netflix", "Spotify"],
    "Health": ["Apollo Pharmacy", "Practo Consultation", "Local Clinic"],
    "Other": ["ATM Withdrawal", "UPI Transfer", "Misc Payment"],
}


def _month_range(today: date, months_back: int) -> list[date]:
    months = []
    y, m = today.year, today.month
    for _ in range(months_back):
        months.append(date(y, m, 1))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return list(reversed(months))


def _category_ids(db: Session) -> dict[str, str]:
    rows = db.query(Category).filter(Category.is_system.is_(True)).all()
    return {c.name: c.id for c in rows}


def _add_txn(db: Session, user_id: str, rng: random.Random, d: date, amount_minor: int, category_id: str | None, merchant: str) -> None:
    db.add(
        Transaction(
            user_id=user_id,
            date=d,
            description=merchant,
            raw_description=merchant,
            amount_minor=amount_minor,
            category_id=category_id,
            category_confirmed=True,
            source="manual",
        )
    )


def _seed_transactions(db: Session, user_id: str, rng: random.Random, today: date) -> None:
    categories = _category_ids(db)

    for month_start in _month_range(today, MONTHS_OF_HISTORY):
        month_end = date(month_start.year + (1 if month_start.month == 12 else 0), (month_start.month % 12) + 1, 1) - timedelta(days=1)
        if month_end > today:
            month_end = today
        if month_start > today:
            break

        is_festival = month_start.month in FESTIVAL_MONTHS

        # Salary — 1st of the month, income.
        salary_day = min(1, (month_end - month_start).days)
        salary_minor = rng.randint(58_000, 65_000) * 100
        _add_txn(db, user_id, rng, month_start + timedelta(days=salary_day), salary_minor, categories.get("Income"), "Salary Credit")

        # Rent — 1st-3rd, fixed-ish.
        rent_day = min(rng.randint(1, 3), (month_end - month_start).days)
        rent_minor = -rng.randint(14_500, 15_500) * 100
        _add_txn(db, user_id, rng, month_start + timedelta(days=rent_day), rent_minor, categories.get("Rent"), "Rent Payment")

        # Utilities — a few bills across the month.
        for _ in range(rng.randint(2, 3)):
            day_offset = rng.randint(3, min(25, (month_end - month_start).days))
            amount = -rng.randint(400, 2200) * 100
            merchant = rng.choice(_MERCHANTS["Utilities"])
            _add_txn(db, user_id, rng, month_start + timedelta(days=day_offset), amount, categories.get("Utilities"), merchant)

        # Food — frequent, small.
        for _ in range(rng.randint(8, 14)):
            day_offset = rng.randint(0, (month_end - month_start).days)
            amount = -rng.randint(120, 900) * 100
            merchant = rng.choice(_MERCHANTS["Food"])
            _add_txn(db, user_id, rng, month_start + timedelta(days=day_offset), amount, categories.get("Food"), merchant)

        # Transport
        for _ in range(rng.randint(4, 9)):
            day_offset = rng.randint(0, (month_end - month_start).days)
            amount = -rng.randint(80, 600) * 100
            merchant = rng.choice(_MERCHANTS["Transport"])
            _add_txn(db, user_id, rng, month_start + timedelta(days=day_offset), amount, categories.get("Transport"), merchant)

        # Shopping — bigger and more frequent in festival months.
        shopping_count = rng.randint(4, 7) if is_festival else rng.randint(1, 3)
        for _ in range(shopping_count):
            day_offset = rng.randint(0, (month_end - month_start).days)
            base = rng.randint(1500, 6000) if is_festival else rng.randint(400, 2500)
            merchant = rng.choice(_MERCHANTS["Shopping"])
            _add_txn(db, user_id, rng, month_start + timedelta(days=day_offset), -base * 100, categories.get("Shopping"), merchant)

        # Entertainment
        for _ in range(rng.randint(1, 3)):
            day_offset = rng.randint(0, (month_end - month_start).days)
            amount = -rng.randint(150, 900) * 100
            merchant = rng.choice(_MERCHANTS["Entertainment"])
            _add_txn(db, user_id, rng, month_start + timedelta(days=day_offset), amount, categories.get("Entertainment"), merchant)

        # Health — occasional
        if rng.random() < 0.4:
            day_offset = rng.randint(0, (month_end - month_start).days)
            amount = -rng.randint(200, 3000) * 100
            merchant = rng.choice(_MERCHANTS["Health"])
            _add_txn(db, user_id, rng, month_start + timedelta(days=day_offset), amount, categories.get("Health"), merchant)

        # One genuine anomaly roughly every 4 months — a real one-off spike
        # for anomaly detection and Fino/advice grounding to have something
        # to notice.
        if rng.random() < 0.28:
            day_offset = rng.randint(0, (month_end - month_start).days)
            amount = -rng.randint(8000, 18000) * 100
            _add_txn(db, user_id, rng, month_start + timedelta(days=day_offset), amount, categories.get("Other"), "Unplanned Large Purchase")

    db.commit()


def _seed_goals(db: Session, user_id: str, today: date) -> None:
    db.add_all(
        [
            Goal(
                user_id=user_id,
                name="Emergency fund",
                target_amount_minor=300_000 * 100,
                saved_amount_minor=180_000 * 100,
                target_date=today + timedelta(days=200),
            ),
            Goal(
                user_id=user_id,
                name="Goa trip",
                target_amount_minor=60_000 * 100,
                saved_amount_minor=15_000 * 100,
                target_date=today + timedelta(days=100),
            ),
            Goal(
                user_id=user_id,
                name="New laptop",
                target_amount_minor=90_000 * 100,
                saved_amount_minor=81_000 * 100,
                target_date=today + timedelta(days=45),
            ),
        ]
    )
    db.commit()


_DEMO_QUIZ_ANSWERS = {
    "age_band": "25-34",
    "employment_status": "salaried",
    "income_range": "50k_1l",
    "dependents": "none",
    "existing_debt_type": ["credit_card"],
    "savings_habit": "automatic",
    "investment_experience": "some",
    "risk_scenario_1": "hold",
    "risk_scenario_2": "gamble",
    "goals": ["emergency_fund", "travel", "wealth_building"],
    "literacy_self_rating": "intermediate",
    "knowledge_check_1": "b",
    "knowledge_check_2": "b",
    "knowledge_check_3": "a",
}


def _seed_profile(db: Session, user_id: str) -> None:
    fields = build_profile_fields(_DEMO_QUIZ_ANSWERS)
    db.add(
        UserProfile(
            user_id=user_id,
            status="completed",
            current_step=len(_DEMO_QUIZ_ANSWERS),
            answers=_DEMO_QUIZ_ANSWERS,
            risk_band=fields["risk_band"],
            literacy_level=fields["literacy_level"],
            life_stage=fields["life_stage"],
            income_stability=fields["income_stability"],
            investment_experience=fields["investment_experience"],
            goals=fields["goals"],
            completed_at=utcnow(),
        )
    )
    db.commit()


_DEMO_CONVERSATION = [
    ("user", "How am I doing with my spending this month?"),
    (
        "assistant",
        "You're broadly on track. Food is your biggest category most months, and there's usually a shopping bump "
        "around festival season — nothing that looks out of line with your usual pattern. Want me to walk through "
        "any category in more detail?",
    ),
    ("user", "What's the fastest way to hit my Goa trip goal?"),
    (
        "assistant",
        "Your Goa trip goal is at ₹15,000 of ₹60,000 with about 3 months left. At your recent average savings rate "
        "you'd need to put aside a bit more each month to get there on time — check the Goals page for the exact "
        "monthly number and a projected completion date based on your real numbers.",
    ),
]


def _seed_fino_history(db: Session, user_id: str) -> None:
    for role, content in _DEMO_CONVERSATION:
        db.add(FinoMessage(user_id=user_id, role=role, content=content))
    db.commit()


_CANNED_RECOMMENDATION_OUTPUT = {
    "summary": "Spending is steady month to month, with a predictable rent and salary rhythm and a seasonal bump "
    "in Shopping around festival season.",
    "insights": [
        "Food is consistently the largest discretionary category most months.",
        "Shopping spend rises noticeably in October and November compared to the rest of the year.",
    ],
    "recommendations": [
        {
            "title": "Automate a fixed transfer toward your Goa trip goal",
            "rationale": "The goal is short-horizon and currently behind the pace needed to hit its target date.",
            "projected_impact": "Reaching the goal on schedule without needing a large lump sum later.",
            "category": "Goals",
            "priority": "high",
        },
        {
            "title": "Set a Shopping budget ahead of festival season",
            "rationale": "Shopping spend spikes predictably in Oct/Nov — a budget set in advance is easier to stick to than one set mid-spike.",
            "projected_impact": "A smoother month-to-month spending pattern through the festival period.",
            "category": "Shopping",
            "priority": "medium",
        },
    ],
    "risks": ["No emergency fund shortfall detected, but continue monitoring after any large one-off expense."],
}


def _seed_recommendation(db: Session, user_id: str) -> None:
    # Imported lazily to avoid a circular import (ai.summary eventually
    # touches models that touch this package during app startup in some
    # import orders); cheap enough to pay once per seed call.
    from app.ai.summary import build_summary, data_version

    summary = build_summary(db, user_id)
    db.add(
        Recommendation(
            user_id=user_id,
            data_version=data_version(summary),
            input_summary=summary,
            output=_CANNED_RECOMMENDATION_OUTPUT,
            model_version="demo-seed",
        )
    )
    db.commit()


def seed_demo_dataset(db: Session, user_id: str, seed: int = DEFAULT_SEED, today: date | None = None) -> None:
    """Populates a (freshly created, empty) demo user's account. Idempotent
    guard is the caller's job — this always inserts, so only call it once
    per user_id (see the demo router, which only calls this the first time
    a shadow account is created)."""
    rng = random.Random(seed)
    resolved_today = today or date.today()

    _seed_transactions(db, user_id, rng, resolved_today)
    _seed_goals(db, user_id, resolved_today)
    _seed_profile(db, user_id)
    _seed_fino_history(db, user_id)
    _seed_recommendation(db, user_id)
