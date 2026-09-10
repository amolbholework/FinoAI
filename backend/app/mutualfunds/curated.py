"""Curated mutual fund schemes for the browse list — one well-established,
long-running direct-plan-growth scheme per broad category, verified against
api.mfapi.in. This keeps the default list small and comprehensible rather
than surfacing all ~40k schemes MFAPI knows about; `/api/mutual-funds/search`
still reaches the full catalog for anything not in this list. Edit this file
to add, remove, or recategorize schemes — nothing else needs to change.
"""

CATEGORIES = {
    "equity_large_cap": "Large cap",
    "equity_flexi_cap": "Flexi cap",
    "equity_mid_cap": "Mid cap",
    "equity_small_cap": "Small cap",
    "elss": "Tax saver (ELSS)",
    "hybrid": "Hybrid / balanced",
    "debt": "Debt",
    "index": "Index fund",
}

CURATED_SCHEMES = [
    {"scheme_code": 118825, "category": "equity_large_cap"},
    {"scheme_code": 122639, "category": "equity_flexi_cap"},
    {"scheme_code": 119071, "category": "equity_mid_cap"},
    {"scheme_code": 125354, "category": "equity_small_cap"},
    {"scheme_code": 135781, "category": "elss"},
    {"scheme_code": 118968, "category": "hybrid"},
    {"scheme_code": 119016, "category": "debt"},
    {"scheme_code": 119063, "category": "index"},
]

# Fino Buddy: maps a (risk_comfort, horizon) profile to the category ids
# above, ordered by fit. Deterministic and inert on its own — Fino Buddy is
# an educational filter over this table, not investment advice.
FINO_BUDDY_MATCHES = {
    ("low", "short"): ["debt", "hybrid"],
    ("low", "medium"): ["hybrid", "debt", "index"],
    ("low", "long"): ["hybrid", "index", "equity_large_cap"],
    ("medium", "short"): ["debt", "hybrid"],
    ("medium", "medium"): ["equity_large_cap", "index", "hybrid"],
    ("medium", "long"): ["equity_flexi_cap", "equity_large_cap", "elss", "index"],
    ("high", "short"): ["hybrid", "debt"],
    ("high", "medium"): ["equity_flexi_cap", "equity_large_cap", "elss"],
    ("high", "long"): ["equity_small_cap", "equity_mid_cap", "equity_flexi_cap", "elss"],
}
