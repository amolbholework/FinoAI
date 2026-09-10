"""Unit tests for the deterministic quiz scoring rubric — no DB, no HTTP,
just answers dict in, UserProfile fields out."""
from app.onboarding.scoring import (
    build_profile_fields,
    derive_income_stability,
    derive_life_stage,
    extract_goals,
    knowledge_check_score,
    score_literacy_level,
    score_risk_band,
)


def test_risk_band_conservative_for_loss_averse_novice():
    answers = {
        "risk_scenario_1": "sell_all",
        "risk_scenario_2": "guaranteed",
        "investment_experience": "none",
    }
    assert score_risk_band(answers) == "conservative"


def test_risk_band_aggressive_for_experienced_risk_seeker():
    answers = {
        "risk_scenario_1": "buy_more",
        "risk_scenario_2": "gamble",
        "investment_experience": "experienced",
    }
    assert score_risk_band(answers) == "aggressive"


def test_risk_band_moderate_for_mixed_signals():
    answers = {
        "risk_scenario_1": "hold",
        "risk_scenario_2": "guaranteed",
        "investment_experience": "some",
    }
    assert score_risk_band(answers) == "moderate"


def test_risk_band_defaults_to_moderate_when_all_questions_skipped():
    assert score_risk_band({}) == "moderate"


def test_knowledge_check_score_counts_only_correct_answers():
    answers = {
        "knowledge_check_1": "b",  # correct
        "knowledge_check_2": "a",  # wrong
        "knowledge_check_3": "c",  # correct
    }
    assert knowledge_check_score(answers) == 2


def test_literacy_level_beginner_when_nothing_answered():
    assert score_literacy_level({}) == "beginner"


def test_literacy_level_advanced_for_high_knowledge_and_self_rating():
    answers = {
        "knowledge_check_1": "b",
        "knowledge_check_2": "b",
        "knowledge_check_3": "c",
        "literacy_self_rating": "advanced",
    }
    assert score_literacy_level(answers) == "advanced"


def test_literacy_level_intermediate_for_partial_knowledge():
    answers = {"knowledge_check_1": "b", "literacy_self_rating": "intermediate"}
    assert score_literacy_level(answers) == "intermediate"


def test_life_stage_student_overrides_age():
    answers = {"employment_status": "student", "age_band": "55-64"}
    assert derive_life_stage(answers) == "student"


def test_life_stage_pre_retirement_from_age_band():
    answers = {"employment_status": "salaried", "age_band": "55-64", "dependents": "none"}
    assert derive_life_stage(answers) == "pre_retirement"


def test_life_stage_family_from_dependents():
    answers = {"employment_status": "salaried", "age_band": "35-44", "dependents": "1_2"}
    assert derive_life_stage(answers) == "family"


def test_life_stage_defaults_to_early_career():
    assert derive_life_stage({}) == "early_career"


def test_income_stability_salaried_is_stable():
    assert derive_income_stability({"employment_status": "salaried"}) == "stable"


def test_income_stability_self_employed_is_variable():
    assert derive_income_stability({"employment_status": "self_employed"}) == "variable"


def test_income_stability_student_is_irregular():
    assert derive_income_stability({"employment_status": "student"}) == "irregular"


def test_extract_goals_preserves_selection_order_as_priority():
    answers = {"goals": ["retirement", "emergency_fund"]}
    goals = extract_goals(answers)
    assert goals == [
        {"type": "retirement", "target_amount": None, "target_date": None, "priority": 1},
        {"type": "emergency_fund", "target_amount": None, "target_date": None, "priority": 2},
    ]


def test_extract_goals_handles_missing_or_malformed_answer():
    assert extract_goals({}) == []
    assert extract_goals({"goals": "not_a_list"}) == []


def test_build_profile_fields_returns_every_required_field():
    fields = build_profile_fields({})
    assert set(fields.keys()) == {
        "risk_band",
        "literacy_level",
        "life_stage",
        "income_stability",
        "investment_experience",
        "goals",
    }
