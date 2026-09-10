from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class TxnRecord:
    """The minimal shape analysis functions need — decoupled from the ORM
    model so this whole package can be unit tested without a database."""

    date: date
    amount_minor: int  # signed: negative = spend, positive = income
    category: str
