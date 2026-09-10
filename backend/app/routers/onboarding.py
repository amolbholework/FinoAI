from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.base import utcnow
from app.models.user import User
from app.models.user_profile import UserProfile
from app.onboarding.questions import QUESTION_IDS, QUESTIONS
from app.onboarding.scoring import build_profile_fields
from app.schemas.onboarding import AnswerRequest, ProfileResponse, Question

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


def get_or_create_profile(db: Session, user_id: str) -> UserProfile:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if profile is None:
        profile = UserProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def _to_response(profile: UserProfile) -> ProfileResponse:
    return ProfileResponse(
        status=profile.status,
        current_step=profile.current_step,
        total_steps=len(QUESTIONS),
        answers=profile.answers,
        risk_band=profile.risk_band,
        literacy_level=profile.literacy_level,
        life_stage=profile.life_stage,
        income_stability=profile.income_stability,
        investment_experience=profile.investment_experience,
        goals=profile.goals,
        completed_at=profile.completed_at,
    )


@router.get("/questions", response_model=list[Question])
def list_questions():
    return QUESTIONS


@router.get("/profile", response_model=ProfileResponse)
def get_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _to_response(get_or_create_profile(db, current_user.id))


@router.post("/answer", response_model=ProfileResponse)
def submit_answer(
    payload: AnswerRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if payload.question_id not in QUESTION_IDS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown question.")

    profile = get_or_create_profile(db, current_user.id)
    if profile.status == "not_started":
        profile.status = "in_progress"

    # Reassigning (not mutating in place) so SQLAlchemy's change-tracking on
    # the JSON column actually notices the update.
    answers = dict(profile.answers)
    answers[payload.question_id] = payload.value
    profile.answers = answers
    profile.current_step = max(profile.current_step, QUESTION_IDS.index(payload.question_id) + 1)

    db.commit()
    db.refresh(profile)
    return _to_response(profile)


@router.post("/complete", response_model=ProfileResponse)
def complete_quiz(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = get_or_create_profile(db, current_user.id)
    fields = build_profile_fields(profile.answers)
    profile.risk_band = fields["risk_band"]
    profile.literacy_level = fields["literacy_level"]
    profile.life_stage = fields["life_stage"]
    profile.income_stability = fields["income_stability"]
    profile.investment_experience = fields["investment_experience"]
    profile.goals = fields["goals"]
    profile.status = "completed"
    profile.completed_at = utcnow()

    db.commit()
    db.refresh(profile)
    return _to_response(profile)


@router.post("/skip", response_model=ProfileResponse)
def skip_quiz(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """A skipped quiz still needs a usable, neutral profile — every
    personalization surface reads risk_band/literacy_level unconditionally
    rather than null-checking, so skipping degrades to a defined middle
    ground instead of leaving those fields empty."""
    profile = get_or_create_profile(db, current_user.id)
    profile.risk_band = profile.risk_band or "moderate"
    profile.literacy_level = profile.literacy_level or "beginner"
    profile.life_stage = profile.life_stage or "early_career"
    profile.income_stability = profile.income_stability or "variable"
    profile.investment_experience = profile.investment_experience or "none"
    profile.status = "skipped"
    profile.completed_at = utcnow()

    db.commit()
    db.refresh(profile)
    return _to_response(profile)


@router.post("/retake", response_model=ProfileResponse)
def retake_quiz(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Re-enters the quiz flow from the top with prior answers pre-filled
    (the frontend reads `answers` back into the form) — this is also how
    "adjust my profile" works: edit an answer, complete again, scoring
    recomputes from scratch."""
    profile = get_or_create_profile(db, current_user.id)
    profile.status = "in_progress"
    profile.current_step = 0

    db.commit()
    db.refresh(profile)
    return _to_response(profile)
