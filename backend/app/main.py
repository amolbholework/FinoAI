from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.seed_categories import ensure_system_categories
from app.routers import (
    advice,
    ai,
    analysis,
    auth,
    budgets,
    categories,
    demo,
    education,
    fino,
    forecasts,
    goals,
    health,
    markets,
    mutualfunds,
    news,
    onboarding,
    reports,
    transactions,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        ensure_system_categories(db)
    finally:
        db.close()
    yield


app = FastAPI(title="FinPilot AI", lifespan=lifespan)

# allow_credentials is required for the httpOnly session cookies to flow
# cross-origin (frontend on :5173, backend on :8000); it's incompatible
# with a wildcard allow_origins, so cors_origins must stay an explicit list.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(budgets.router)
app.include_router(goals.router)
app.include_router(reports.router)
app.include_router(ai.router)
app.include_router(analysis.router)
app.include_router(forecasts.router)
app.include_router(markets.router)
app.include_router(onboarding.router)
app.include_router(fino.router)
app.include_router(demo.router)
app.include_router(health.router)
app.include_router(advice.router)
app.include_router(education.router)
app.include_router(mutualfunds.router)
app.include_router(news.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/settings")
def get_app_settings():
    return {"currency": settings.default_currency}
