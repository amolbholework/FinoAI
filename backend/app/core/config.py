"""Central app settings, loaded from environment variables (.env in dev)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"

    # SQLite fallback keeps local dev zero-config; set DATABASE_URL for Postgres.
    database_url: str = "sqlite:///./finpilot.db"

    cors_origins: list[str] = ["http://localhost:5173"]

    default_currency: str = "INR"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    # Per-purpose LLM provider selection (app/llm/factory.py). All default
    # to "claude" — the only provider actually implemented so far. Fino's
    # default is documented to flip to "gemini" once GeminiProvider ships;
    # until then, setting any of these to "gemini" raises a clear config
    # error rather than silently doing something wrong.
    llm_provider_fino: str = "claude"
    llm_provider_advice: str = "claude"
    llm_provider_vision: str = "claude"

    max_csv_upload_mb: int = 5
    max_screenshot_upload_mb: int = 8
    screenshot_extract_rate_limit_per_minute: int = 6
    fino_rate_limit_per_minute: int = 15
    fino_demo_rate_limit_per_minute: int = 6
    ai_demo_rate_limit_per_minute: int = 4

    # Google Identity Services — verifies ID tokens from the frontend against
    # this client id; never trust the aud claim without checking it.
    google_client_id: str = ""
    # Not used by the current flow: verifying a client-obtained ID token needs
    # no secret (no code exchange happens). Kept for parity with the Google
    # Cloud Console credential pair and in case a code-exchange flow is added later.
    google_client_secret: str = ""
    # Signs/verifies our own access + refresh JWTs.
    jwt_secret: str = ""
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 30
    frontend_url: str = "http://localhost:5173"

    # Feature flag for the (optional) Financial Health Checker. Purely
    # additive: the router 404s when this is off, and nothing else in the
    # app reads this flag — see tests/test_health_endpoint.py for the
    # inertness proof.
    health_checker_enabled: bool = True

    # Free tier at https://www.marketaux.com/ — 100 requests/day. The news
    # feed degrades to a clean "unavailable" state (never a 5xx) when this
    # is unset, same as ANTHROPIC_API_KEY's graceful degradation.
    marketaux_api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
