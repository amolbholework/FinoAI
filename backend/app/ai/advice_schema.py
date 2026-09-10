from pydantic import BaseModel, Field


class EvidenceOut(BaseModel):
    metric: str
    value: str
    period: str


class InsightOut(BaseModel):
    title: str
    detail: str
    evidence: EvidenceOut
    severity: str = Field(pattern="^(info|watch|urgent)$")


class RecommendationOut(BaseModel):
    action: str
    why: str
    impact_inr_per_month: float
    effort: str = Field(pattern="^(low|medium|high)$")
    category: str = Field(pattern="^(budget|save|invest|debt)$")
    # "this_month" / "next_3_months" / "long_term" — powers the Advice page's
    # horizon grouping.
    horizon: str = Field(pattern="^(this_month|next_3_months|long_term)$")
    # Name of a goal from the input's `goals` list this recommendation moves,
    # or null if it doesn't affect any stated goal.
    linked_goal: str | None = None
    # One short phrase quantifying that effect, e.g. "reaches target ~2 months
    # sooner" or "+8% progress this year" — null whenever linked_goal is null.
    goal_impact: str | None = None


class AdviceOutput(BaseModel):
    headline: str
    health_score: int = Field(ge=0, le=100)
    insights: list[InsightOut]
    recommendations: list[RecommendationOut]
    questions_to_consider: list[str]
