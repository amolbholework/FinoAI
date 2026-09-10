import csv
import io

from app.models.transaction import Transaction


def transactions_to_csv(transactions: list[Transaction]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["date", "description", "amount", "category", "source"])
    for t in transactions:
        writer.writerow(
            [
                t.date.isoformat(),
                t.description,
                f"{t.amount_minor / 100:.2f}",
                t.category.name if t.category else "",
                t.source,
            ]
        )
    return buffer.getvalue()
