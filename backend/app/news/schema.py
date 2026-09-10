from pydantic import BaseModel


class NewsArticle(BaseModel):
    uuid: str
    title: str
    description: str
    url: str
    image_url: str | None
    source: str
    published_at: str


class NewsResponse(BaseModel):
    articles: list[NewsArticle]
    is_available: bool
    is_stale: bool = False
    source: str = "Marketaux"
