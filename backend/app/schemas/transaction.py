import datetime as dt

from pydantic import BaseModel, Field

# A field literally named `date` on these models shadows the bare name `date`
# inside Pydantic's forward-ref resolution namespace, breaking sibling fields'
# `date | None` annotations — importing the module and spelling `dt.date`
# sidesteps the collision entirely.


class TransactionResponse(BaseModel):
    id: str
    date: dt.date
    description: str
    amount_minor: int
    category_id: str | None
    category_name: str | None = None
    category_confirmed: bool
    source: str

    model_config = {"from_attributes": True}


class TransactionCreate(BaseModel):
    date: dt.date
    description: str = Field(min_length=1, max_length=255)
    amount_minor: int
    category_id: str | None = None


class TransactionUpdate(BaseModel):
    date: dt.date | None = None
    description: str | None = Field(default=None, min_length=1, max_length=255)
    amount_minor: int | None = None
    category_id: str | None = None


class TransactionFilter(BaseModel):
    date_from: dt.date | None = None
    date_to: dt.date | None = None
    category_id: str | None = None
    amount_min_minor: int | None = None
    amount_max_minor: int | None = None
    search: str | None = None


# --- CSV upload ---


class ColumnMappingSchema(BaseModel):
    date: str | None = None
    description: str | None = None
    amount: str | None = None
    debit: str | None = None
    credit: str | None = None


class CategoryGuess(BaseModel):
    category: str | None
    # Only set when the ML classifier produced a real probability — a
    # keyword-rule match has no numeric confidence to show, so this stays
    # null rather than a made-up number.
    confidence: float | None = None


class UploadPreviewResponse(BaseModel):
    columns: list[str]
    suggested_mapping: ColumnMappingSchema
    sample_rows: list[dict]
    category_guesses: list[CategoryGuess]
    total_rows: int
    upload_token: str


class UploadCommitRequest(BaseModel):
    upload_token: str
    mapping: ColumnMappingSchema
    # Keyed by the row's original CSV position (0-based), only for rows the
    # user edited the category pill on in the preview table.
    category_overrides: dict[int, str] = Field(default_factory=dict)


class UploadCommitResponse(BaseModel):
    inserted: int
    duplicates_skipped: int
    unparseable_skipped: int
