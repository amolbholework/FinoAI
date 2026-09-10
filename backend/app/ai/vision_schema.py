from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ExtractionConfidence(BaseModel):
    amount: float = Field(ge=0, le=1)
    merchant: float = Field(ge=0, le=1)
    category: float = Field(ge=0, le=1)


class TransactionExtraction(BaseModel):
    is_transaction: bool
    amount: float | None = None
    currency: str | None = None
    direction: str | None = None  # "debit" | "credit" | None
    merchant: str | None = None
    datetime_: str | None = Field(default=None, alias="datetime")
    reference: str | None = None
    category: str | None = None
    confidence: ExtractionConfidence
    unreadable_fields: list[str] = Field(default_factory=list)
    notes: str | None = None

    model_config = {"populate_by_name": True}

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: float | None) -> float | None:
        if v is not None and v <= 0:
            raise ValueError("amount must be positive")
        return v

    @field_validator("direction")
    @classmethod
    def direction_must_be_valid(cls, v: str | None) -> str | None:
        if v is not None and v not in ("debit", "credit"):
            raise ValueError("direction must be 'debit', 'credit', or null")
        return v

    @field_validator("datetime_")
    @classmethod
    def datetime_must_parse(cls, v: str | None) -> str | None:
        if v is None:
            return None
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"datetime is not valid ISO 8601: {v}") from exc
        return v
