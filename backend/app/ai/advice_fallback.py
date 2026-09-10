"""Deterministic, non-AI fallback for POST /api/advice — used when the LLM
call fails or returns malformed output twice in a row, so the advice page
is never blank. Built entirely from the same summary dict the AI would
have received, using simple rules rather than any model call."""
from datetime import date

from app.ai.advice_schema import AdviceOutput, EvidenceOut, InsightOut, RecommendationOut


def _months_until(target_date_str: str, reference_month_str: str | None) -> int:
    target = date.fromisoformat(target_date_str)
    if reference_month_str:
        ref_year, ref_month = (int(x) for x in reference_month_str.split("-"))
        reference = date(ref_year, ref_month, 1)
    else:
        reference = date.today().replace(day=1)
    return max(0, (target.year - reference.year) * 12 + (target.month - reference.month))


def _horizon_for_months(months: int) -> str:
    if months <= 1:
        return "this_month"
    if months <= 3:
        return "next_3_months"
    return "long_term"


def generate_fallback_advice(summary: dict) -> AdviceOutput:
    health = summary.get("deterministic_health_score") or {}
    score = health.get("score")
    band = health.get("band")

    headline = (
        f"Your financial health is scored {band.lower()} — see the breakdown below for specifics."
        if score is not None and band
        else "Add a bit more transaction history to unlock personalized advice."
    )

    insights: list[InsightOut] = []
    for t in summary.get("trends", []):
        if t.get("direction") == "rising" and t.get("pct_change") is not None:
            insights.append(
                InsightOut(
                    title=f"{t['category']} spending is rising",
                    detail=f"{t['category']} spend is {t['pct_change']}% above its 3-month average.",
                    evidence=EvidenceOut(metric=f"{t['category']} spend", value=f"₹{t['latest_spend']}", period=summary.get("latest_month") or ""),
                    severity="watch",
                )
            )

    for a in summary.get("category_month_anomalies", [])[:2]:
        insights.append(
            InsightOut(
                title=f"Unusual {a['category']} spend in {a['month']}",
                detail=f"{a['category']} spend in {a['month']} was well outside its usual range.",
                evidence=EvidenceOut(metric=f"{a['category']} spend", value=f"₹{a['spend']}", period=a["month"]),
                severity="urgent" if a.get("z_score", 0) >= 3 else "watch",
            )
        )

    latest_month = summary.get("latest_month")

    recommendations: list[RecommendationOut] = []
    for b in summary.get("budget_adherence", []):
        if b.get("is_over"):
            over_by = round(b["spent"] - b["limit"], 2)
            recommendations.append(
                RecommendationOut(
                    action=f"Bring {b['category']} spend back within budget",
                    why=f"You've spent ₹{b['spent']} against a ₹{b['limit']} budget this month, ₹{over_by} over.",
                    impact_inr_per_month=over_by,
                    effort="medium",
                    category="budget",
                    horizon="this_month",
                )
            )

    for g in summary.get("goals", []):
        if g.get("progress_pct", 100) < 50:
            months_left = _months_until(g["target_date"], latest_month)
            recommendations.append(
                RecommendationOut(
                    action=f"Increase contributions toward '{g['name']}'",
                    why=f"'{g['name']}' is {g['progress_pct']}% funded (₹{g['saved_amount']} of ₹{g['target_amount']}) with a target date of {g['target_date']}.",
                    impact_inr_per_month=round((g["target_amount"] - g["saved_amount"]) / 6, 2),
                    effort="medium",
                    category="save",
                    horizon=_horizon_for_months(months_left),
                    linked_goal=g["name"],
                    goal_impact=f"{g['progress_pct']}% funded, {months_left} months to target date",
                )
            )

    return AdviceOutput(
        headline=headline,
        health_score=score if score is not None else 50,
        insights=insights[:5],
        recommendations=recommendations[:5],
        questions_to_consider=[
            "Which of your budgeted categories tends to run over most months?",
            "Is your current savings rate enough to reach your stated goals on time?",
        ],
    )
