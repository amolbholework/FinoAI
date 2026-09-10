"""The onboarding quiz's questions — the single source of truth consumed by
both `GET /api/onboarding/questions` (so the frontend renders generically,
no copy duplicated client-side) and scoring.py (which reads answers back out
by these same ids). 14 questions, each on its own screen, all skippable.

`employment_status` doubles as the income-stability signal (see
scoring.derive_income_stability) rather than asking a separate question —
one fewer screen without losing the field the UserProfile output requires.
Likewise, "time horizon" is captured implicitly via each selected goal's
target_date once the user creates it on the Goals page, rather than as its
own top-level quiz question.
"""

QUESTIONS = [
    {
        "id": "age_band",
        "prompt": "What's your age range?",
        "type": "single_choice",
        "options": [
            {"value": "18-24", "label": "18–24"},
            {"value": "25-34", "label": "25–34"},
            {"value": "35-44", "label": "35–44"},
            {"value": "45-54", "label": "45–54"},
            {"value": "55-64", "label": "55–64"},
            {"value": "65+", "label": "65 and above"},
        ],
    },
    {
        "id": "employment_status",
        "prompt": "Which best describes your current work situation?",
        "type": "single_choice",
        "options": [
            {"value": "student", "label": "Student"},
            {"value": "salaried", "label": "Salaried employee"},
            {"value": "self_employed", "label": "Self-employed / freelance"},
            {"value": "business_owner", "label": "Business owner"},
            {"value": "not_working", "label": "Not currently working"},
        ],
    },
    {
        "id": "income_range",
        "prompt": "What's your approximate monthly income?",
        "type": "single_choice",
        "options": [
            {"value": "under_25k", "label": "Under ₹25,000"},
            {"value": "25k_50k", "label": "₹25,000 – ₹50,000"},
            {"value": "50k_1l", "label": "₹50,000 – ₹1,00,000"},
            {"value": "1l_2l", "label": "₹1,00,000 – ₹2,00,000"},
            {"value": "2l_plus", "label": "Above ₹2,00,000"},
        ],
    },
    {
        "id": "dependents",
        "prompt": "How many people depend on your income?",
        "type": "single_choice",
        "options": [
            {"value": "none", "label": "No one but myself"},
            {"value": "1_2", "label": "1–2 people"},
            {"value": "3_plus", "label": "3 or more people"},
        ],
    },
    {
        "id": "existing_debt_type",
        "prompt": "Do you currently have any of these? Select all that apply.",
        "help_text": "We only ask the type, never the amount.",
        "type": "multi_choice",
        "options": [
            {"value": "none", "label": "No debt"},
            {"value": "credit_card", "label": "Credit card balance"},
            {"value": "personal_loan", "label": "Personal loan"},
            {"value": "education_loan", "label": "Education loan"},
            {"value": "home_loan", "label": "Home loan"},
            {"value": "vehicle_loan", "label": "Vehicle loan"},
            {"value": "other", "label": "Other"},
        ],
    },
    {
        "id": "savings_habit",
        "prompt": "How would you describe your savings habit today?",
        "type": "single_choice",
        "options": [
            {"value": "none", "label": "I don't save regularly"},
            {"value": "occasional", "label": "I save occasionally, whatever's left over"},
            {"value": "automatic", "label": "I save a fixed amount every month"},
        ],
    },
    {
        "id": "investment_experience",
        "prompt": "How much investing experience do you have?",
        "type": "single_choice",
        "options": [
            {"value": "none", "label": "None — I haven't invested yet"},
            {"value": "some", "label": "Some — mutual funds, FDs, or similar"},
            {"value": "experienced", "label": "Experienced — stocks, derivatives, or active trading"},
        ],
    },
    {
        "id": "risk_scenario_1",
        "prompt": "An investment you hold drops 20% in a month with no bad news about the company. What do you do?",
        "type": "single_choice",
        "options": [
            {"value": "sell_all", "label": "Sell everything to stop further loss"},
            {"value": "sell_some", "label": "Sell part of it to reduce risk"},
            {"value": "hold", "label": "Hold and wait it out"},
            {"value": "buy_more", "label": "Buy more while it's cheaper"},
        ],
    },
    {
        "id": "risk_scenario_2",
        "prompt": "Which would you choose?",
        "type": "single_choice",
        "options": [
            {"value": "guaranteed", "label": "A guaranteed ₹1,000"},
            {"value": "gamble", "label": "A 50% chance of ₹2,500 and a 50% chance of ₹0"},
        ],
    },
    {
        "id": "goals",
        "prompt": "What are you working toward? Select up to 3, in order of priority.",
        "type": "multi_choice",
        "max_selections": 3,
        "options": [
            {"value": "emergency_fund", "label": "Building an emergency fund"},
            {"value": "debt_payoff", "label": "Paying off debt"},
            {"value": "home_purchase", "label": "Buying a home"},
            {"value": "education", "label": "Education (yours or a dependent's)"},
            {"value": "retirement", "label": "Retirement"},
            {"value": "travel", "label": "Travel or a big purchase"},
            {"value": "wealth_building", "label": "General wealth building"},
        ],
    },
    {
        "id": "literacy_self_rating",
        "prompt": "How would you rate your own financial knowledge?",
        "type": "single_choice",
        "options": [
            {"value": "beginner", "label": "Beginner — still learning the basics"},
            {"value": "intermediate", "label": "Intermediate — comfortable with the fundamentals"},
            {"value": "advanced", "label": "Advanced — I actively manage a portfolio"},
        ],
    },
    {
        "id": "knowledge_check_1",
        "prompt": 'What does "diversification" mean?',
        "type": "knowledge_check",
        "options": [
            {"value": "a", "label": "Investing all your money in one high-performing stock"},
            {"value": "b", "label": "Spreading money across different assets to reduce risk"},
            {"value": "c", "label": "Moving all your money to a savings account"},
            {"value": "d", "label": "Timing the market to buy low and sell high"},
        ],
    },
    {
        "id": "knowledge_check_2",
        "prompt": "Inflation is 6% a year and your savings account pays 3% interest. What's happening to your money's real value?",
        "type": "knowledge_check",
        "options": [
            {"value": "a", "label": "It's growing faster than prices"},
            {"value": "b", "label": "It's losing purchasing power over time"},
            {"value": "c", "label": "It's unaffected by inflation"},
            {"value": "d", "label": "It doubles every year"},
        ],
    },
    {
        "id": "knowledge_check_3",
        "prompt": "What is an emergency fund typically meant to cover?",
        "type": "knowledge_check",
        "options": [
            {"value": "a", "label": "A down payment on a house"},
            {"value": "b", "label": "Stock market investments during a dip"},
            {"value": "c", "label": "3–6 months of essential living expenses"},
            {"value": "d", "label": "Annual vacation spending"},
        ],
    },
]

QUESTION_IDS = [q["id"] for q in QUESTIONS]
