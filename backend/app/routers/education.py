from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.education.curriculum import LESSON_IDS, MODULES, TOTAL_LESSON_COUNT
from app.models.education_progress import EducationProgress
from app.models.user import User
from app.schemas.education import Module, ProgressResponse, ToggleLessonRequest

router = APIRouter(prefix="/api/education", tags=["education"])


def get_or_create_progress(db: Session, user_id: str) -> EducationProgress:
    progress = db.query(EducationProgress).filter(EducationProgress.user_id == user_id).first()
    if progress is None:
        progress = EducationProgress(user_id=user_id)
        db.add(progress)
        db.commit()
        db.refresh(progress)
    return progress


def _to_response(progress: EducationProgress) -> ProgressResponse:
    return ProgressResponse(completed_lesson_ids=progress.completed_lesson_ids, total_lesson_count=TOTAL_LESSON_COUNT)


@router.get("/curriculum", response_model=list[Module])
def get_curriculum():
    return MODULES


@router.get("/progress", response_model=ProgressResponse)
def get_progress(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _to_response(get_or_create_progress(db, current_user.id))


@router.post("/progress/toggle", response_model=ProgressResponse)
def toggle_lesson(
    payload: ToggleLessonRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if payload.lesson_id not in LESSON_IDS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown lesson.")

    progress = get_or_create_progress(db, current_user.id)
    # Reassigning (not mutating in place) so SQLAlchemy's change-tracking on
    # the JSON column actually notices the update.
    completed = list(progress.completed_lesson_ids)
    if payload.lesson_id in completed:
        completed.remove(payload.lesson_id)
    else:
        completed.append(payload.lesson_id)
    progress.completed_lesson_ids = completed

    db.commit()
    db.refresh(progress)
    return _to_response(progress)
