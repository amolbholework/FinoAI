from datetime import datetime

from pydantic import BaseModel


class QuestionOption(BaseModel):
    value: str
    label: str


class Question(BaseModel):
    id: str
    prompt: str
    help_text: str | None = None
    type: str  # single_choice | multi_choice | knowledge_check
    max_selections: int | None = None
    options: list[QuestionOption]
    skippable: bool = True


class AnswerRequest(BaseModel):
    question_id: str
    value: str | list[str] | None = None


class ProfileResponse(BaseModel):
    status: str
    current_step: int
    total_steps: int
    answers: dict
    risk_band: str | None
    literacy_level: str | None
    life_stage: str | None
    income_stability: str | None
    investment_experience: str | None
    goals: list
    completed_at: datetime | None

    model_config = {"from_attributes": True}
