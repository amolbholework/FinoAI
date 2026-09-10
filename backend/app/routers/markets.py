import logging

from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.markets.schema import MarketIndicesResponse
from app.markets.service import INDICES, MarketDataUnavailableError, get_index
from app.models.user import User

router = APIRouter(prefix="/markets", tags=["markets"])
logger = logging.getLogger("finpilot.markets")


@router.get("/indices", response_model=MarketIndicesResponse)
def list_indices(current_user: User = Depends(get_current_user)):
    """Each index is resolved independently — one provider hiccup shouldn't
    take down the other, and if both fail with nothing cached yet, this
    still returns 200 with an empty list rather than a 5xx, so the rest of
    the dashboard renders untouched and the frontend shows one clean
    "unavailable" state for this section."""
    results = []
    for entry in INDICES:
        try:
            results.append(get_index(entry["symbol"], entry["name"]))
        except MarketDataUnavailableError as exc:
            logger.warning("Dropping %s from this response: %s", entry["name"], exc)

    return MarketIndicesResponse(indices=results)
