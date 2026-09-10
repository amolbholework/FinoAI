"""Deterministic scoring rubric for the onboarding quiz.

No AI call — every UserProfile field below is a documented, pure function of
the raw answers dict, so the result is explainable to the user ("why am I
marked conservative?") and stable/testable across runs. Missing or skipped
answers fall back to a neutral midpoint rather than crashing or defaulting
to an extreme.
"""

# --- risk_band -------------------------------------------------------------
# Points sum to a 0-7 scale from three independent signals, each capturing a
# different facet of risk tolerance: actual behavior under a loss scenario,
# a classic gain/loss-framing gamble, and self-reported experience (more
# experience raises the ceiling of risk someone can knowingly take on).

RISK_SCENARIO_1_POINTS = {"sell_all": 0, "sell_some": 1, "hold": 2, "buy_more": 3}
RISK_SCENARIO_2_POINTS = {"guaranteed": 0, "gamble": 2}
INVESTMENT_EXPERIENCE_POINTS = {"none": 0, "some": 1, "experienced": 2}

RISK_BAND_THRESHOLDS = (
    (2, "conservative"),  # 0-2 points
    (5, "moderate"),  # 3-5 points
)  # 6-7 points -> aggressive


def score_risk_band(answers: dict) -> str:
    points = (
        RISK_SCENARIO_1_POINTS.get(answers.get("risk_scenario_1"), 1.5)
        + RISK_SCENARIO_2_POINTS.get(answers.get("risk_scenario_2"), 1)
        + INVESTMENT_EXPERIENCE_POINTS.get(answers.get("investment_experience"), 1)
    )
    for ceiling, band in RISK_BAND_THRESHOLDS:
        if points <= ceiling:
            return band
    return "aggressive"


# --- literacy_level ----------------------------------------------------------
# Objective knowledge-check score (0-3 correct) plus self-rating (0-2), so a
# confident-but-wrong self-rating alone can't inflate the result.

KNOWLEDGE_CHECK_ANSWERS = {
    "knowledge_check_1": "b",  # diversification
    "knowledge_check_2": "b",  # inflation erodes real value
    "knowledge_check_3": "c",  # emergency fund covers 3-6 months expenses
}
SELF_RATING_POINTS = {"beginner": 0, "intermediate": 1, "advanced": 2}

LITERACY_LEVEL_THRESHOLDS = (
    (1, "beginner"),  # 0-1 points
    (3, "intermediate"),  # 2-3 points
)  # 4-5 points -> advanced


def knowledge_check_score(answers: dict) -> int:
    return sum(1 for key, correct in KNOWLEDGE_CHECK_ANSWERS.items() if answers.get(key) == correct)


def score_literacy_level(answers: dict) -> str:
    points = knowledge_check_score(answers) + SELF_RATING_POINTS.get(answers.get("literacy_self_rating"), 0)
    for ceiling, level in LITERACY_LEVEL_THRESHOLDS:
        if points <= ceiling:
            return level
    return "advanced"


# --- life_stage --------------------------------------------------------------
# Priority order: student status is definitive; then age brackets nearing
# retirement; then whether anyone depends on the user's income; everyone
# else defaults to early_career.

def derive_life_stage(answers: dict) -> str:
    if answers.get("employment_status") == "student":
        return "student"
    if answers.get("age_band") in ("55-64", "65+"):
        return "pre_retirement"
    if answers.get("dependents") in ("1_2", "3_plus"):
        return "family"
    return "early_career"


# --- income_stability --------------------------------------------------------
# Derived from employment_status rather than asked separately — salaried
# income is the stable case, business/freelance income varies month to
# month, and no current income is irregular by definition.

_INCOME_STABILITY_BY_EMPLOYMENT = {
    "salaried": "stable",
    "business_owner": "variable",
    "self_employed": "variable",
    "student": "irregular",
    "not_working": "irregular",
}


def derive_income_stability(answers: dict) -> str:
    return _INCOME_STABILITY_BY_EMPLOYMENT.get(answers.get("employment_status"), "variable")


# --- goals ---------------------------------------------------------------
# The quiz captures interest + priority order only; target_amount/target_date
# are filled in for real when the user creates the matching Goal on the
# Goals page, so this stays a light-weight personalization signal rather
# than a second, shadow goal-tracking system.

def extract_goals(answers: dict) -> list[dict]:
    selected = answers.get("goals")
    if not isinstance(selected, list):
        return []
    return [
        {"type": goal_type, "target_amount": None, "target_date": None, "priority": index + 1}
        for index, goal_type in enumerate(selected)
        if isinstance(goal_type, str)
    ]


def build_profile_fields(answers: dict) -> dict:
    """The full derived-fields bundle written onto UserProfile at
    completion time. Callable independently of the HTTP layer for testing."""
    return {
        "risk_band": score_risk_band(answers),
        "literacy_level": score_literacy_level(answers),
        "life_stage": derive_life_stage(answers),
        "income_stability": derive_income_stability(answers),
        "investment_experience": answers.get("investment_experience") or "none",
        "goals": extract_goals(answers),
    }
