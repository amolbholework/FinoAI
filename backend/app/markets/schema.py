from pydantic import BaseModel


class IntradayPoint(BaseModel):
    timestamp: int  # unix seconds
    value: float


class IndexData(BaseModel):
    name: str
    symbol: str
    current: float
    change: float
    change_pct: float
    previous_close: float
    points: list[IntradayPoint]
    timestamp: int  # unix seconds — when `current` was last actually valid
    is_open: bool
    is_stale: bool = False


class MarketIndicesResponse(BaseModel):
    indices: list[IndexData]
    source: str = "Yahoo Finance"
    delayed_minutes: int = 15
