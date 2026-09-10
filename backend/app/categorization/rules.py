"""Keyword rules — the first categorization pass, before the ML classifier has
enough confirmed history to be trusted. Cheap, transparent, and gives the
classifier something better than random guesses to bootstrap from."""
import re

KEYWORD_RULES: dict[str, list[str]] = {
    "Food": ["restaurant", "cafe", "coffee", "swiggy", "zomato", "grocery", "supermarket", "bakery", "diner"],
    "Rent": ["rent", "landlord", "lease"],
    "Transport": ["uber", "ola", "taxi", "fuel", "petrol", "diesel", "metro", "parking", "irctc", "flight", "airlines"],
    "Utilities": ["electricity", "water bill", "gas bill", "broadband", "internet", "mobile recharge", "dth"],
    "Shopping": ["amazon", "flipkart", "myntra", "mall", "store", "retail"],
    "Health": ["pharmacy", "hospital", "clinic", "doctor", "medical", "diagnostic"],
    "Entertainment": ["netflix", "spotify", "prime video", "hotstar", "cinema", "movie", "concert", "bookmyshow"],
    "Income": ["salary", "payroll", "interest credit", "dividend", "refund"],
}

_COMPILED = {
    category: re.compile("|".join(re.escape(kw) for kw in keywords), re.IGNORECASE)
    for category, keywords in KEYWORD_RULES.items()
}


def match_keyword_rule(description: str) -> str | None:
    for category, pattern in _COMPILED.items():
        if pattern.search(description):
            return category
    return None
