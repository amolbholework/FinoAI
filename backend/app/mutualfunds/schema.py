from pydantic import BaseModel


class NavPoint(BaseModel):
    date: str  # DD-MM-YYYY, as returned by the provider
    nav: float


class SchemeSearchResult(BaseModel):
    scheme_code: int
    scheme_name: str


class SchemeDetail(BaseModel):
    scheme_code: int
    scheme_name: str
    fund_house: str
    scheme_category: str
    latest_nav: float
    latest_date: str
    change_pct_30d: float | None
    history: list[NavPoint]
    is_stale: bool = False


class CuratedSchemeSummary(BaseModel):
    scheme_code: int
    scheme_name: str
    category: str
    category_label: str
    latest_nav: float
    change_pct_30d: float | None
    is_stale: bool = False


class CuratedListResponse(BaseModel):
    schemes: list[CuratedSchemeSummary]
    source: str = "MFAPI.in (AMFI data)"


class FinoBuddyRequest(BaseModel):
    risk_comfort: str  # low | medium | high
    horizon: str  # short | medium | long


class FinoBuddyResponse(BaseModel):
    matched_categories: list[str]
    schemes: list[CuratedSchemeSummary]
