from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.ai.prompt import SYSTEM_PROMPT, build_user_message
from app.ai.recommendations import get_recommendations
from app.ai.schema import RecommendationOutput
from app.ai.summary import build_summary
from app.core.config import get_settings
from app.core.database import get_db
from app.core.rate_limit import enforce_ip_rate_limit
from app.core.security import get_effective_user
from app.llm.factory import get_provider
from app.models.user import User

router = APIRouter(prefix="/ai", tags=["ai"])
settings = get_settings()


@router.get("/recommendations")
def recommendations(
    request: Request,
    force_refresh: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_effective_user),
):
    # Demo accounts get a tighter per-minute cap than real usage — a demo
    # session is far more likely to be someone rapid-clicking "Refresh" to
    # see what happens than a real user genuinely needing many regenerations.
    if current_user.is_demo:
        enforce_ip_rate_limit(request, f"ai-demo-{current_user.id}", max_per_minute=settings.ai_demo_rate_limit_per_minute)

    output, was_cached = get_recommendations(
        db, current_user.id, force_refresh=force_refresh, is_demo=current_user.is_demo
    )
    return {"cached": was_cached, **output.model_dump()}


@router.post("/whatif-commentary")
def whatif_commentary(
    scenario: dict, db: Session = Depends(get_db), current_user: User = Depends(get_effective_user)
):
    """AI commentary on a what-if scenario the user has already computed
    client-side. Grounded the same way as the main recommendations — built
    from the real summary plus the hypothetical adjustments the client sends."""
    base_summary = build_summary(db, current_user.id)
    combined = {**base_summary, "whatif_scenario": scenario}

    try:
        provider = get_provider("advice")
        output = provider.generate_structured(
            messages=[{"role": "user", "content": build_user_message(combined)}],
            system_prompt=SYSTEM_PROMPT,
            schema=RecommendationOutput,
        )
        assert isinstance(output, RecommendationOutput)
        return output.model_dump()
    except Exception:
        return {
            "summary": "AI commentary is temporarily unavailable — your projected numbers above are unaffected.",
            "insights": [],
            "recommendations": [],
            "risks": [],
        }
