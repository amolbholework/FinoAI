from datetime import datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    picture_url: str | None
    created_at: datetime
    onboarding_status: str
    # True for an anonymous "Try demo" guest account — there's no real
    # account behind it, so the frontend shouldn't offer a demo toggle.
    is_demo: bool
    # True when a real account currently has test mode switched on and is
    # viewing its shadow demo data instead of its own.
    test_mode_enabled: bool

    model_config = {"from_attributes": True}


class GoogleSignInRequest(BaseModel):
    id_token: str
