"""The Market Education curriculum — the single source of truth for both
`GET /api/education/curriculum` and progress tracking (which stores
completed lesson ids from here). Videos are curated from established Indian
financial educators and embedded via YouTube's standard embed player, never
linked out to. Edit this file to add, remove, or reorder lessons — nothing
else needs to change.
"""

MODULES = [
    {
        "id": "money-basics",
        "title": "Money basics",
        "level": "beginner",
        "description": "Start here if investing and personal finance are new to you.",
        "lessons": [
            {
                "id": "why-invest",
                "title": "Why should you invest?",
                "description": "Why letting money sit idle loses value over time, and what investing actually solves for.",
                "youtube_id": "YGh8C6C4yDQ",
                "source": "Varsity by Zerodha",
            },
            {
                "id": "emergency-fund",
                "title": "Emergency funds, explained",
                "description": "What an emergency fund is, how big it should be, and how to build one before you invest anything else.",
                "youtube_id": "3hikDqf9GW4",
                "source": "CA Rachana Ranade",
            },
            {
                "id": "what-is-mutual-fund",
                "title": "What is a mutual fund?",
                "description": "The basic mechanics of a mutual fund — pooled money, a fund manager, and units — explained from scratch.",
                "youtube_id": "PbldLCsspgE",
                "source": "CA Rachana Ranade",
            },
        ],
    },
    {
        "id": "markets-investing",
        "title": "Markets & investing",
        "level": "intermediate",
        "description": "How markets actually work once you're past the basics.",
        "lessons": [
            {
                "id": "regulators-intermediaries",
                "title": "Regulators & financial intermediaries",
                "description": "Who SEBI, exchanges, brokers, and depositories are, and what role each one plays when you invest.",
                "youtube_id": "RIp16TH2fjs",
                "source": "Varsity by Zerodha",
            },
            {
                "id": "what-is-ipo",
                "title": "What is an IPO?",
                "description": "How a company goes from private to publicly listed, and what that means for an investor buying in.",
                "youtube_id": "OMEIrakP2yY",
                "source": "Varsity by Zerodha",
            },
            {
                "id": "stock-market-index",
                "title": "The stock market index",
                "description": "What an index like the Nifty 50 or Sensex actually measures, and why it moves the way it does.",
                "youtube_id": "s2-Qdpxynx8",
                "source": "Varsity by Zerodha",
            },
        ],
    },
    {
        "id": "going-further",
        "title": "Going further",
        "level": "advanced",
        "description": "For once the fundamentals feel comfortable.",
        "lessons": [
            {
                "id": "maximize-mutual-fund-returns",
                "title": "Getting more out of your mutual funds",
                "description": "Practical habits — reviewing costs, staying invested, and avoiding common timing mistakes — that compound over years.",
                "youtube_id": "SykubriJVHE",
                "source": "CA Rachana Ranade",
            },
        ],
    },
]

LESSON_IDS = [lesson["id"] for module in MODULES for lesson in module["lessons"]]
TOTAL_LESSON_COUNT = len(LESSON_IDS)
