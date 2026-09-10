"""Screenshot intake for the "scan a transaction" feature.

Two things matter here more than anywhere else in the app:
1. We validate the *actual* file content, not the extension or the
   client-supplied Content-Type header — either of those can lie.
2. Nothing here ever touches disk or the database. Callers get bytes back
   in memory; it's on them to discard it after use.
"""
import io

from PIL import Image, ImageOps

import pillow_heif

pillow_heif.register_heif_opener()  # lets Pillow.open() read HEIC/HEIF too

MAX_UPLOAD_BYTES = 8 * 1024 * 1024  # 8MB, per spec

# Pillow's detected format (read from the file's actual header, i.e. magic
# bytes) mapped to what we accept. HEIC/HEIF get normalized to JPEG below
# since Claude's vision API doesn't take HEIC directly.
_ALLOWED_FORMATS = {"PNG", "JPEG", "WEBP", "HEIF"}

JPEG_QUALITY = 90


class UnsupportedImageError(ValueError):
    pass


def process_screenshot(raw: bytes) -> tuple[bytes, str]:
    """Validates, strips EXIF, and normalizes an uploaded screenshot.

    Returns (jpeg_bytes, media_type). Raises UnsupportedImageError if the
    bytes aren't a real, recognizable image in an allowed format — this is
    determined by asking Pillow to decode the actual header, never by
    trusting the filename or the upload's declared content-type.
    """
    if len(raw) > MAX_UPLOAD_BYTES:
        raise UnsupportedImageError(f"Image exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)}MB limit.")
    if not raw:
        raise UnsupportedImageError("Empty file.")

    try:
        img = Image.open(io.BytesIO(raw))
        img.load()  # force a full decode now, while we still control the error path
    except Exception as exc:
        raise UnsupportedImageError("File is not a readable image.") from exc

    detected_format = (img.format or "").upper()
    if detected_format not in _ALLOWED_FORMATS:
        raise UnsupportedImageError(f"Unsupported image format: {detected_format or 'unknown'}.")

    # Apply EXIF orientation (phones commonly rely on this tag rather than
    # storing the pixels already rotated) before we drop the EXIF block
    # entirely — otherwise a portrait screenshot could come out sideways.
    img = ImageOps.exif_transpose(img)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    buffer = io.BytesIO()
    # Re-encoding without an `exif=` argument is what actually strips the
    # metadata — Pillow only embeds EXIF on save if you hand it back in.
    img.save(buffer, format="JPEG", quality=JPEG_QUALITY)
    return buffer.getvalue(), "image/jpeg"
