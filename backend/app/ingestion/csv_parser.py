"""Parses uploaded bank-statement CSVs into a normalized shape.

Bank export formats vary a lot: some use a single signed `amount` column,
others split `debit`/`credit`. We recognize common header spellings and
propose a column mapping; if we can't confidently guess a column, the caller
(the /preview endpoint) surfaces it to the user to map by hand instead of
silently guessing wrong.
"""
import io
from dataclasses import dataclass, field

import pandas as pd

REQUIRED_FIELDS = ["date", "description", "amount"]

# Alternative shape: separate debit/credit columns instead of one signed amount.
DEBIT_CREDIT_FIELDS = ["date", "description", "debit", "credit"]

HEADER_SYNONYMS: dict[str, list[str]] = {
    "date": ["date", "transaction date", "txn date", "value date", "posting date"],
    "description": ["description", "narration", "particulars", "details", "memo", "transaction details"],
    "amount": ["amount", "amount (inr)", "transaction amount", "value"],
    "debit": ["debit", "withdrawal", "withdrawal amt", "debit amount", "dr"],
    "credit": ["credit", "deposit", "deposit amt", "credit amount", "cr"],
}


@dataclass
class ColumnMapping:
    date: str | None = None
    description: str | None = None
    amount: str | None = None
    debit: str | None = None
    credit: str | None = None

    def is_complete(self) -> bool:
        has_signed_amount = bool(self.date and self.description and self.amount)
        has_debit_credit = bool(self.date and self.description and (self.debit or self.credit))
        return has_signed_amount or has_debit_credit


@dataclass
class ParsedPreview:
    columns: list[str]
    suggested_mapping: ColumnMapping
    sample_rows: list[dict] = field(default_factory=list)
    total_rows: int = 0


MAX_PREVIEW_ROWS = 20


def read_csv_bytes(raw: bytes) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(raw), dtype=str, keep_default_na=False)


def suggest_mapping(columns: list[str]) -> ColumnMapping:
    normalized = {c: c.strip().lower() for c in columns}
    mapping = ColumnMapping()

    for field_name, synonyms in HEADER_SYNONYMS.items():
        for original, lowered in normalized.items():
            if lowered in synonyms:
                setattr(mapping, field_name, original)
                break

    return mapping


def build_preview(raw: bytes) -> ParsedPreview:
    df = read_csv_bytes(raw)
    mapping = suggest_mapping(list(df.columns))
    sample = df.head(MAX_PREVIEW_ROWS).to_dict(orient="records")
    return ParsedPreview(
        columns=list(df.columns),
        suggested_mapping=mapping,
        sample_rows=sample,
        total_rows=len(df),
    )


@dataclass
class NormalizedRow:
    date: str  # ISO yyyy-mm-dd
    description: str
    amount_minor: int  # signed
    source_row_index: int  # position in the original CSV — lets a category
    # override picked in the preview (which only shows the first N rows)
    # survive rows being skipped as unparseable in between.


def normalize_rows(raw: bytes, mapping: ColumnMapping) -> tuple[list[NormalizedRow], int]:
    """Returns (rows, skipped_count) — skipped rows had an unparseable date or amount."""
    if not mapping.is_complete():
        raise ValueError("Column mapping is incomplete.")

    df = read_csv_bytes(raw)
    rows: list[NormalizedRow] = []
    skipped = 0

    for row_index, record in df.iterrows():
        raw_date = str(record[mapping.date]).strip()
        # Default currency/locale is INR, where bank exports are overwhelmingly
        # DD/MM/YYYY — try that first so an unambiguous "01/08" reads as 1 Aug,
        # not (US-style) 8 Jan. Only fall back to MM/DD if DD/MM can't parse.
        parsed_date = pd.to_datetime(raw_date, dayfirst=True, errors="coerce")
        if pd.isna(parsed_date):
            parsed_date = pd.to_datetime(raw_date, dayfirst=False, errors="coerce")
        if pd.isna(parsed_date):
            skipped += 1
            continue  # unparseable row — skipped rather than guessed at

        description = str(record[mapping.description]).strip()
        if not description:
            skipped += 1
            continue

        if mapping.amount:
            amount_str = str(record[mapping.amount]).replace(",", "").strip()
            try:
                amount_minor = round(float(amount_str) * 100)
            except ValueError:
                skipped += 1
                continue
        else:
            debit_str = str(record.get(mapping.debit, "") or "0").replace(",", "").strip()
            credit_str = str(record.get(mapping.credit, "") or "0").replace(",", "").strip()
            try:
                debit = float(debit_str) if debit_str else 0.0
                credit = float(credit_str) if credit_str else 0.0
            except ValueError:
                skipped += 1
                continue
            amount_minor = round((credit - debit) * 100)

        rows.append(
            NormalizedRow(
                date=parsed_date.date().isoformat(),
                description=description,
                amount_minor=int(amount_minor),
                source_row_index=int(row_index),
            )
        )

    return rows, skipped
