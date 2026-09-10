from datetime import datetime

from pydantic import BaseModel


class FinoMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FinoSendRequest(BaseModel):
    message: str
    # Which screen the user is on right now — lets Fino's suggested prompts
    # (frontend-side) and its "how do I..." answers stay screen-aware.
    current_route: str | None = None
