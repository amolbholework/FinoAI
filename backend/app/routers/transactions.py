from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.ai.extraction import ExtractionFailedError, extract_transaction
from app.ai.vision_schema import TransactionExtraction
from app.categorization import classifier
from app.categorization.service import categorize, categorize_with_confidence
from app.core.config import get_settings
from app.core.database import get_db
from app.core.rate_limit import enforce_ip_rate_limit
from app.core.security import get_effective_user
from app.ingestion import staging
from app.ingestion.csv_parser import ColumnMapping, build_preview
from app.ingestion.service import commit_rows
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import (
    CategoryGuess,
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
    UploadCommitRequest,
    UploadCommitResponse,
    UploadPreviewResponse,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])
settings = get_settings()


def _to_response(txn: Transaction) -> TransactionResponse:
    resp = TransactionResponse.model_validate(txn)
    resp.category_name = txn.category.name if txn.category_id and txn.category else None
    return resp


@router.get("", response_model=list[TransactionResponse])
def list_transactions(
    date_from: date | None = None,
    date_to: date | None = None,
    category_id: str | None = None,
    amount_min_minor: int | None = None,
    amount_max_minor: int | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_effective_user),
):
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)
    if date_from:
        query = query.filter(Transaction.date >= date_from)
    if date_to:
        query = query.filter(Transaction.date <= date_to)
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    if amount_min_minor is not None:
        query = query.filter(Transaction.amount_minor >= amount_min_minor)
    if amount_max_minor is not None:
        query = query.filter(Transaction.amount_minor <= amount_max_minor)
    if search:
        like = f"%{search}%"
        query = query.filter(or_(Transaction.description.ilike(like), Transaction.raw_description.ilike(like)))

    txns = query.order_by(Transaction.date.desc(), Transaction.created_at.desc()).all()
    return [_to_response(t) for t in txns]


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_effective_user)
):
    category_id = payload.category_id
    category_confirmed = category_id is not None

    if category_id is None:
        guessed_id, confident = categorize(db, payload.description, current_user.id)
        category_id = guessed_id
        category_confirmed = False  # a guess, even a confident one, isn't user-confirmed

    txn = Transaction(
        user_id=current_user.id,
        date=payload.date,
        description=payload.description,
        raw_description=payload.description,
        amount_minor=payload.amount_minor,
        category_id=category_id,
        category_confirmed=category_confirmed,
        source="manual",
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)

    if category_confirmed:
        classifier.train(db, current_user.id)

    return _to_response(txn)


@router.patch("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: str,
    payload: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_effective_user),
):
    txn = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id, Transaction.user_id == current_user.id)
        .first()
    )
    if not txn:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaction not found.")

    category_changed = payload.category_id is not None and payload.category_id != txn.category_id

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(txn, field, value)

    if category_changed:
        # A user picking a category is exactly the override signal the
        # classifier should learn from next time it retrains.
        txn.category_confirmed = True

    db.commit()
    db.refresh(txn)

    if category_changed:
        classifier.train(db, current_user.id)

    return _to_response(txn)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_effective_user)
):
    txn = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id, Transaction.user_id == current_user.id)
        .first()
    )
    if not txn:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaction not found.")
    db.delete(txn)
    db.commit()


@router.post("/upload/preview", response_model=UploadPreviewResponse)
async def upload_preview(
    file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_effective_user)
):
    raw = await file.read()
    if len(raw) > settings.max_csv_upload_mb * 1024 * 1024:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"File exceeds {settings.max_csv_upload_mb}MB limit.")
    if not raw:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty file.")

    try:
        preview = build_preview(raw)
    except Exception as exc:  # malformed CSV, bad encoding, etc.
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Could not parse CSV: {exc}") from exc

    # Best-effort category guess per previewed row, shown next to the sample
    # data so the user can correct it before committing — not persisted here.
    desc_col = preview.suggested_mapping.description
    guesses: list[CategoryGuess] = []
    if desc_col:
        for row in preview.sample_rows:
            category_name, confidence = categorize_with_confidence(
                db, str(row.get(desc_col, "")), current_user.id
            )
            guesses.append(CategoryGuess(category=category_name, confidence=confidence))
    else:
        guesses = [CategoryGuess(category=None, confidence=None) for _ in preview.sample_rows]

    token = staging.stage(raw)
    return UploadPreviewResponse(
        columns=preview.columns,
        suggested_mapping=preview.suggested_mapping.__dict__,
        sample_rows=preview.sample_rows,
        category_guesses=guesses,
        total_rows=preview.total_rows,
        upload_token=token,
    )


@router.post("/upload/commit", response_model=UploadCommitResponse)
def upload_commit(
    payload: UploadCommitRequest, db: Session = Depends(get_db), current_user: User = Depends(get_effective_user)
):
    raw = staging.retrieve(payload.upload_token)
    if raw is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Upload session expired — please re-upload the file.")

    mapping = ColumnMapping(**payload.mapping.model_dump())
    if not mapping.is_complete():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Column mapping is incomplete.")

    try:
        inserted, duplicates, unparseable = commit_rows(
            db, raw, mapping, current_user.id, payload.category_overrides
        )
    except Exception as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Could not import CSV: {exc}") from exc

    return UploadCommitResponse(inserted=inserted, duplicates_skipped=duplicates, unparseable_skipped=unparseable)


@router.post("/extract", response_model=TransactionExtraction)
async def extract_from_screenshot(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_effective_user),
):
    """Reads a transaction out of a screenshot via Claude vision. Extract and
    save are deliberately two separate calls — this endpoint writes nothing
    to the database and the image is never persisted, only held in memory
    for the duration of the request."""
    enforce_ip_rate_limit(request, "extract", max_per_minute=settings.screenshot_extract_rate_limit_per_minute)

    raw = await file.read()
    if len(raw) > settings.max_screenshot_upload_mb * 1024 * 1024:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Image exceeds {settings.max_screenshot_upload_mb}MB limit.")

    try:
        return extract_transaction(db, raw, current_user.id)
    except ExtractionFailedError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
