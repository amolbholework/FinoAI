"""ML categorization layer, sitting behind the keyword rules.

Trained on transactions the user has confirmed (manually entered, or an
auto-categorization they didn't override) — see Transaction.category_confirmed.
Kept as a lazily-rebuilt in-process singleton *per user*: for a demo-scale
few-thousand-rows-per-user dataset, retraining on every ingest is cheap and
avoids the complexity of a model registry / persistence format. State is
keyed by user_id so one user's transaction history never trains (or leaks
into predictions for) another user's model.
"""
from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.transaction import Transaction

MIN_SAMPLES_PER_CLASS = 3
MIN_CLASSES = 2
CONFIDENCE_THRESHOLD = 0.55


@dataclass
class ClassifierState:
    pipeline: Pipeline | None = None
    trained_on_count: int = 0


_state_by_user: dict[str, ClassifierState] = {}


def _training_rows(db: Session, user_id: str) -> list[tuple[str, str]]:
    rows = (
        db.query(Transaction.raw_description, Category.name)
        .join(Category, Transaction.category_id == Category.id)
        .filter(Transaction.category_confirmed.is_(True), Transaction.user_id == user_id)
        .all()
    )
    return [(desc, cat) for desc, cat in rows]


def train(db: Session, user_id: str) -> bool:
    """Rebuilds this user's classifier from their confirmed history. Returns
    False (and leaves the classifier unset) if there isn't enough labeled
    data yet — callers should fall back to keyword rules in that case."""
    state = _state_by_user.setdefault(user_id, ClassifierState())

    rows = _training_rows(db, user_id)
    state.trained_on_count = len(rows)

    class_counts: dict[str, int] = {}
    for _, category in rows:
        class_counts[category] = class_counts.get(category, 0) + 1

    eligible_classes = {c for c, n in class_counts.items() if n >= MIN_SAMPLES_PER_CLASS}
    if len(eligible_classes) < MIN_CLASSES:
        state.pipeline = None
        return False

    descriptions, labels = zip(*[(d, c) for d, c in rows if c in eligible_classes])

    pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer(lowercase=True, ngram_range=(1, 2), min_df=1)),
            ("clf", LogisticRegression(max_iter=1000)),
        ]
    )
    pipeline.fit(list(descriptions), list(labels))
    state.pipeline = pipeline
    return True


def predict(description: str, user_id: str) -> tuple[str, float] | None:
    state = _state_by_user.get(user_id)
    if state is None or state.pipeline is None:
        return None
    proba = state.pipeline.predict_proba([description])[0]
    classes = state.pipeline.classes_
    best_idx = proba.argmax()
    confidence = float(proba[best_idx])
    if confidence < CONFIDENCE_THRESHOLD:
        return None
    return classes[best_idx], confidence


def is_trained(user_id: str) -> bool:
    state = _state_by_user.get(user_id)
    return state is not None and state.pipeline is not None
