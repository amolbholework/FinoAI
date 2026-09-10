import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import get_current_user
from app.models.user import User
from app.mutualfunds.curated import CATEGORIES, CURATED_SCHEMES, FINO_BUDDY_MATCHES
from app.mutualfunds.schema import (
    CuratedListResponse,
    CuratedSchemeSummary,
    FinoBuddyRequest,
    FinoBuddyResponse,
    SchemeDetail,
    SchemeSearchResult,
)
from app.mutualfunds.service import MutualFundDataUnavailableError, get_scheme_detail, search_schemes

router = APIRouter(prefix="/api/mutual-funds", tags=["mutual-funds"])
logger = logging.getLogger("finpilot.mutualfunds")


def _curated_summaries() -> list[CuratedSchemeSummary]:
    """Resolves each curated scheme independently — one provider hiccup
    shouldn't drop the whole list, matching the markets router's pattern."""
    summaries = []
    for entry in CURATED_SCHEMES:
        try:
            detail = get_scheme_detail(entry["scheme_code"])
            summaries.append(
                CuratedSchemeSummary(
                    scheme_code=detail.scheme_code,
                    scheme_name=detail.scheme_name,
                    category=entry["category"],
                    category_label=CATEGORIES[entry["category"]],
                    latest_nav=detail.latest_nav,
                    change_pct_30d=detail.change_pct_30d,
                    is_stale=detail.is_stale,
                )
            )
        except MutualFundDataUnavailableError as exc:
            logger.warning("Dropping scheme %s from curated list: %s", entry["scheme_code"], exc)
    return summaries


@router.get("/curated", response_model=CuratedListResponse)
def list_curated(current_user: User = Depends(get_current_user)):
    return CuratedListResponse(schemes=_curated_summaries())


@router.get("/search", response_model=list[SchemeSearchResult])
def search(q: str = Query(min_length=2), current_user: User = Depends(get_current_user)):
    try:
        return search_schemes(q)
    except Exception as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Mutual fund search is temporarily unavailable.") from exc


@router.get("/{scheme_code}", response_model=SchemeDetail)
def get_scheme(scheme_code: int, current_user: User = Depends(get_current_user)):
    try:
        return get_scheme_detail(scheme_code)
    except MutualFundDataUnavailableError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc


@router.post("/fino-buddy", response_model=FinoBuddyResponse)
def fino_buddy(payload: FinoBuddyRequest, current_user: User = Depends(get_current_user)):
    """Deterministic category matching, not a model call — 'Fino Buddy' is
    an educational filter over the curated list keyed by risk comfort and
    time horizon, same spirit as the Financial Health score: transparent
    and explainable rather than a black box, and never a specific buy
    recommendation."""
    key = (payload.risk_comfort, payload.horizon)
    matched_categories = FINO_BUDDY_MATCHES.get(key)
    if matched_categories is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unrecognized risk_comfort/horizon combination.")

    all_schemes = {s.category: s for s in _curated_summaries()}
    matched_schemes = [all_schemes[cat] for cat in matched_categories if cat in all_schemes]

    return FinoBuddyResponse(matched_categories=matched_categories, schemes=matched_schemes)
