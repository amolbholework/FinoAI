from pydantic import BaseModel, Field


class RecommendationItem(BaseModel):
    title: str
    rationale: str
    projected_impact: str
    category: str
    priority: str = Field(pattern="^(high|medium|low)$")


class RecommendationOutput(BaseModel):
    summary: str
    insights: list[str]
    recommendations: list[RecommendationItem]
    risks: list[str]
