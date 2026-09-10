from pydantic import BaseModel


class HealthPillarOut(BaseModel):
    key: str
    label: str
    score: float | None
    weight: float
    value_label: str
    note: str


class HealthLeverOut(BaseModel):
    pillar_key: str
    pillar_label: str
    current_score: float
    estimated_point_gain: float
    note: str


class HealthTrendPoint(BaseModel):
    month: str
    score: int


class HealthScoreOut(BaseModel):
    score: int | None
    band: str | None
    is_provisional: bool
    pillars: list[HealthPillarOut]
    top_levers: list[HealthLeverOut]
    trend: list[HealthTrendPoint]
