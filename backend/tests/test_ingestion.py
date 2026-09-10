from app.ingestion.csv_parser import ColumnMapping, build_preview, normalize_rows, suggest_mapping
from app.ingestion.dedup import dedupe
from app.ingestion.service import commit_rows

TEST_USER_ID = "11111111-1111-1111-1111-111111111111"


def test_suggest_mapping_recognizes_signed_amount_headers():
    mapping = suggest_mapping(["Date", "Description", "Amount"])
    assert mapping.date == "Date"
    assert mapping.description == "Description"
    assert mapping.amount == "Amount"
    assert mapping.is_complete()


def test_suggest_mapping_recognizes_debit_credit_headers():
    mapping = suggest_mapping(["Transaction Date", "Narration", "Withdrawal Amt", "Deposit Amt"])
    assert mapping.date == "Transaction Date"
    assert mapping.description == "Narration"
    assert mapping.debit == "Withdrawal Amt"
    assert mapping.credit == "Deposit Amt"
    assert mapping.is_complete()


def test_suggest_mapping_leaves_unrecognized_headers_unmapped():
    mapping = suggest_mapping(["Col1", "Col2", "Col3"])
    assert not mapping.is_complete()
    assert mapping.date is None


def test_normalize_rows_signed_amount_format():
    csv_bytes = b"Date,Description,Amount\n01/08/2026,Coffee,-250.00\n02/08/2026,Salary,55000.00\n"
    mapping = ColumnMapping(date="Date", description="Description", amount="Amount")
    rows, skipped = normalize_rows(csv_bytes, mapping)

    assert skipped == 0
    assert len(rows) == 2
    assert rows[0].date == "2026-08-01"  # dd/mm/yyyy, INR-locale default
    assert rows[0].amount_minor == -25000
    assert rows[1].amount_minor == 5500000


def test_normalize_rows_debit_credit_format():
    csv_bytes = b"Date,Narration,Debit,Credit\n03/08/2026,Uber,180.50,\n04/08/2026,Refund,,100.00\n"
    mapping = ColumnMapping(date="Date", description="Narration", debit="Debit", credit="Credit")
    rows, skipped = normalize_rows(csv_bytes, mapping)

    assert skipped == 0
    assert rows[0].amount_minor == -18050  # debit -> negative (spend)
    assert rows[1].amount_minor == 10000  # credit -> positive (income)


def test_normalize_rows_skips_unparseable_rows():
    csv_bytes = b"Date,Description,Amount\nnot-a-date,Coffee,-250.00\n01/08/2026,,100.00\n01/08/2026,Ok,not-a-number\n"
    mapping = ColumnMapping(date="Date", description="Description", amount="Amount")
    rows, skipped = normalize_rows(csv_bytes, mapping)

    assert rows == []
    assert skipped == 3


def test_build_preview_returns_sample_and_total_count():
    csv_bytes = b"Date,Description,Amount\n01/08/2026,Coffee,-250.00\n02/08/2026,Salary,55000.00\n"
    preview = build_preview(csv_bytes)

    assert preview.total_rows == 2
    assert preview.columns == ["Date", "Description", "Amount"]
    assert len(preview.sample_rows) == 2


def test_dedup_drops_rows_already_in_db(db_session):
    from datetime import date as date_cls

    from app.models.category import Category
    from app.models.transaction import Transaction

    category = Category(name="TestFood", is_system=False)
    db_session.add(category)
    db_session.commit()

    db_session.add(
        Transaction(
            user_id=TEST_USER_ID,
            date=date_cls(2026, 8, 1),
            description="Coffee",
            raw_description="Coffee",
            amount_minor=-25000,
            category_id=category.id,
            category_confirmed=True,
            source="csv",
        )
    )
    db_session.commit()

    csv_bytes = b"Date,Description,Amount\n01/08/2026,Coffee,-250.00\n02/08/2026,New one,-100.00\n"
    mapping = ColumnMapping(date="Date", description="Description", amount="Amount")
    rows, _ = normalize_rows(csv_bytes, mapping)

    kept, duplicate_count = dedupe(db_session, rows, TEST_USER_ID)

    assert duplicate_count == 1
    assert len(kept) == 1
    assert kept[0].description == "New one"


def test_dedup_drops_duplicates_within_same_batch(db_session):
    # A description unused by any other test — tests share one on-disk test DB
    # (see conftest), so a name collision here would false-fail against leftover rows.
    csv_bytes = b"Date,Description,Amount\n05/08/2026,BatchDupCoffee,-250.00\n05/08/2026,BatchDupCoffee,-250.00\n"
    mapping = ColumnMapping(date="Date", description="Description", amount="Amount")
    rows, _ = normalize_rows(csv_bytes, mapping)

    kept, duplicate_count = dedupe(db_session, rows, TEST_USER_ID)

    assert len(kept) == 1
    assert duplicate_count == 1


def test_commit_rows_applies_category_override_by_source_row_index(db_session):
    from app.models.category import Category
    from app.models.transaction import Transaction

    category = Category(name="OverrideTestTravel", is_system=False)
    db_session.add(category)
    db_session.commit()

    # Row 0 has a description no keyword rule matches, so without an
    # override it would land uncategorized.
    csv_bytes = (
        b"Date,Description,Amount\n"
        b"06/08/2026,ZzzUnrecognizedMerchant,-500.00\n"
        b"06/08/2026,AnotherUnrecognizedOne,-700.00\n"
    )
    mapping = ColumnMapping(date="Date", description="Description", amount="Amount")

    inserted, duplicates, unparseable = commit_rows(
        db_session, csv_bytes, mapping, TEST_USER_ID, category_overrides={0: "OverrideTestTravel"}
    )

    assert inserted == 2
    assert duplicates == 0
    assert unparseable == 0

    overridden = db_session.query(Transaction).filter(Transaction.description == "ZzzUnrecognizedMerchant").first()
    untouched = db_session.query(Transaction).filter(Transaction.description == "AnotherUnrecognizedOne").first()

    assert overridden.category_id == category.id
    assert overridden.category_confirmed is True
    assert untouched.category_id is None
    assert untouched.category_confirmed is False
