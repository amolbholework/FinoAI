import io

import pytest
from PIL import Image
from pydantic import ValidationError

from app.ai.extraction import ExtractionFailedError, extract_transaction
from app.ai.vision_schema import TransactionExtraction
from app.core.rate_limit import enforce_ip_rate_limit
from app.ingestion.image_processing import UnsupportedImageError, process_screenshot
from app.llm.base import LLMUnavailableError, LLMValidationError

TEST_USER_ID = "11111111-1111-1111-1111-111111111111"

VALID_EXTRACTION = {
    "is_transaction": True,
    "amount": 450.0,
    "currency": "INR",
    "direction": "debit",
    "merchant": "Blue Bottle Coffee",
    "datetime": "2026-08-08T10:15:00",
    "reference": "UPI123456",
    "category": "Food",
    "confidence": {"amount": 0.95, "merchant": 0.9, "category": 0.8},
    "unreadable_fields": [],
    "notes": None,
}

NOT_A_TRANSACTION = {
    "is_transaction": False,
    "amount": None,
    "currency": None,
    "direction": None,
    "merchant": None,
    "datetime": None,
    "reference": None,
    "category": None,
    "confidence": {"amount": 0, "merchant": 0, "category": 0},
    "unreadable_fields": [],
    "notes": "no transaction detected",
}


def _png_bytes(size=(40, 40), color=(200, 50, 50)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color=color).save(buf, format="PNG")
    return buf.getvalue()


# --- schema validation ---


def test_extraction_schema_accepts_valid_payload():
    result = TransactionExtraction.model_validate(VALID_EXTRACTION)
    assert result.amount == 450.0
    assert result.direction == "debit"


def test_extraction_schema_accepts_not_a_transaction():
    result = TransactionExtraction.model_validate(NOT_A_TRANSACTION)
    assert result.is_transaction is False
    assert result.amount is None


def test_extraction_schema_rejects_negative_amount():
    bad = {**VALID_EXTRACTION, "amount": -50}
    with pytest.raises(ValidationError):
        TransactionExtraction.model_validate(bad)


def test_extraction_schema_rejects_zero_amount():
    bad = {**VALID_EXTRACTION, "amount": 0}
    with pytest.raises(ValidationError):
        TransactionExtraction.model_validate(bad)


def test_extraction_schema_rejects_invalid_direction():
    bad = {**VALID_EXTRACTION, "direction": "sideways"}
    with pytest.raises(ValidationError):
        TransactionExtraction.model_validate(bad)


def test_extraction_schema_rejects_unparseable_datetime():
    bad = {**VALID_EXTRACTION, "datetime": "not a date"}
    with pytest.raises(ValidationError):
        TransactionExtraction.model_validate(bad)


def test_extraction_schema_datetime_alias_round_trips():
    result = TransactionExtraction.model_validate(VALID_EXTRACTION)
    dumped = result.model_dump(by_alias=True)
    assert dumped["datetime"] == VALID_EXTRACTION["datetime"]
    assert "datetime_" not in dumped


# --- image processing: magic bytes, not extension ---


def test_process_screenshot_accepts_real_png():
    jpeg_bytes, media_type = process_screenshot(_png_bytes())
    assert media_type == "image/jpeg"
    assert jpeg_bytes[:2] == b"\xff\xd8"  # JPEG magic bytes


def test_process_screenshot_rejects_non_image_bytes_regardless_of_intent():
    fake = b"this is just plain text pretending to be an image, not real image bytes at all"
    with pytest.raises(UnsupportedImageError):
        process_screenshot(fake)


def test_process_screenshot_rejects_empty_bytes():
    with pytest.raises(UnsupportedImageError):
        process_screenshot(b"")


def test_process_screenshot_rejects_oversized_upload():
    from app.ingestion import image_processing

    oversized = b"\x00" * (image_processing.MAX_UPLOAD_BYTES + 1)
    with pytest.raises(UnsupportedImageError):
        process_screenshot(oversized)


def test_process_screenshot_strips_exif():
    buf = io.BytesIO()
    img = Image.new("RGB", (30, 30), color=(10, 20, 30))
    exif = img.getexif()
    exif[0x0112] = 3  # orientation tag — something that would prove EXIF survived if it did
    img.save(buf, format="JPEG", exif=exif)

    jpeg_bytes, _ = process_screenshot(buf.getvalue())
    result_img = Image.open(io.BytesIO(jpeg_bytes))
    assert not result_img.getexif()  # stripped, not carried through


# --- extraction orchestration ---


def test_extract_transaction_returns_validated_model(db_session, monkeypatch):
    monkeypatch.setattr(
        "app.ai.extraction._extract", lambda *a, **k: TransactionExtraction.model_validate(VALID_EXTRACTION)
    )
    result = extract_transaction(db_session, _png_bytes(), TEST_USER_ID)
    assert result.is_transaction is True
    assert result.merchant == "Blue Bottle Coffee"


def test_extract_transaction_nulls_out_category_not_in_db(db_session, monkeypatch):
    bogus_category = {**VALID_EXTRACTION, "category": "TotallyMadeUpCategory"}
    monkeypatch.setattr(
        "app.ai.extraction._extract", lambda *a, **k: TransactionExtraction.model_validate(bogus_category)
    )
    result = extract_transaction(db_session, _png_bytes(), TEST_USER_ID)
    assert result.category is None
    assert "category" in result.unreadable_fields


def test_extract_transaction_handles_non_transaction_image(db_session, monkeypatch):
    monkeypatch.setattr(
        "app.ai.extraction._extract", lambda *a, **k: TransactionExtraction.model_validate(NOT_A_TRANSACTION)
    )
    result = extract_transaction(db_session, _png_bytes(), TEST_USER_ID)
    assert result.is_transaction is False
    assert result.amount is None


def test_extract_transaction_rejects_bad_upload_before_calling_claude(db_session, monkeypatch):
    called = {"hit": False}
    monkeypatch.setattr("app.ai.extraction._extract", lambda *a, **k: called.update(hit=True))
    with pytest.raises(ExtractionFailedError):
        extract_transaction(db_session, b"not an image", TEST_USER_ID)
    assert called["hit"] is False  # never spent an API call on an invalid upload


def test_extract_transaction_raises_clean_error_on_provider_unavailable(db_session, monkeypatch):
    def _raise(*a, **k):
        raise LLMUnavailableError("simulated outage")

    monkeypatch.setattr("app.ai.extraction._extract", _raise)
    with pytest.raises(ExtractionFailedError):
        extract_transaction(db_session, _png_bytes(), TEST_USER_ID)


def test_extract_transaction_raises_clean_error_on_malformed_model_response(db_session, monkeypatch):
    def _raise(*a, **k):
        raise LLMValidationError("bad shape")

    monkeypatch.setattr("app.ai.extraction._extract", _raise)
    with pytest.raises(ExtractionFailedError):
        extract_transaction(db_session, _png_bytes(), TEST_USER_ID)


# --- rate limiting ---


def test_rate_limit_blocks_after_threshold():
    from fastapi import HTTPException

    class FakeClient:
        host = "1.2.3.4"

    class FakeRequest:
        client = FakeClient()

    req = FakeRequest()
    for _ in range(3):
        enforce_ip_rate_limit(req, "test-extract", max_per_minute=3)

    with pytest.raises(HTTPException) as exc_info:
        enforce_ip_rate_limit(req, "test-extract", max_per_minute=3)
    assert exc_info.value.status_code == 429
