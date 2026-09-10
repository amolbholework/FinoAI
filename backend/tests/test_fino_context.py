from datetime import date

from app.ai.fino_context import build_fino_context
from app.models.goal import Goal


def test_context_includes_active_goals_with_progress(db_session, test_user):
    goal = Goal(
        user_id=test_user.id,
        name="Emergency fund",
        target_amount_minor=100_000,
        saved_amount_minor=25_000,
        target_date=date(2027, 1, 1),
    )
    db_session.add(goal)
    db_session.commit()

    context = build_fino_context(db_session, test_user.id)

    assert len(context["active_goals"]) == 1
    goal_ctx = context["active_goals"][0]
    assert goal_ctx["name"] == "Emergency fund"
    assert goal_ctx["target_amount"] == 1000.0
    assert goal_ctx["saved_amount"] == 250.0
    assert goal_ctx["progress_pct"] == 25.0


def test_context_has_no_goals_for_a_fresh_user(db_session, test_user):
    context = build_fino_context(db_session, test_user.id)
    assert context["active_goals"] == []


def test_context_reuses_the_same_user_profile_block_as_the_advice_panel(db_session, test_user):
    context = build_fino_context(db_session, test_user.id)
    assert "user_profile" in context
    assert context["user_profile"]["risk_band"] == "moderate"
