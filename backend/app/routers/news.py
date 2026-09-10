from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models.user import User
from app.news.schema import NewsResponse
from app.news.service import NewsUnavailableError, get_news

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("", response_model=NewsResponse)
def list_news(current_user: User = Depends(get_current_user)):
    """Always 200s — an unconfigured key or a provider outage renders as a
    clean 'unavailable' card on the frontend, never a broken page."""
    try:
        articles, is_stale = get_news()
        return NewsResponse(articles=articles, is_available=True, is_stale=is_stale)
    except NewsUnavailableError:
        return NewsResponse(articles=[], is_available=False)
