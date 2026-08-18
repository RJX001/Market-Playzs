"""Media upload — listing images and proof photos/videos (B6).

Local disk store at apps/api/uploads/ (gitignored). Thumbnail generation is a
BackgroundTasks stub; malware scanning is deferred to a worker (Section 2.3).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"

PURPOSE_LISTING_IMAGE = "listing_image"
PURPOSE_PROOF = "proof"
ALLOWED_PURPOSES = frozenset({PURPOSE_LISTING_IMAGE, PURPOSE_PROOF})

IMAGE_MIMES = frozenset(
    {"image/jpeg", "image/png", "image/webp", "image/gif"}
)
VIDEO_MIMES = frozenset({"video/mp4", "video/webm"})
LISTING_MIMES = IMAGE_MIMES
PROOF_MIMES = IMAGE_MIMES | VIDEO_MIMES

IMAGE_MAX_BYTES = 10 * 1024 * 1024  # 10 MiB
VIDEO_MAX_BYTES = 50 * 1024 * 1024  # 50 MiB

EXT_FOR_MIME = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
}


class MediaServiceError(ValueError):
    pass


@dataclass
class MediaRecord:
    id: str
    mime_type: str
    size_bytes: int
    purpose: str
    original_filename: str
    url: str
    thumbnail_url: str | None = None


def _ensure_upload_dir() -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOAD_DIR


def sniff_mime(data: bytes) -> str | None:
    """Server-side MIME from magic bytes — never trust client extension/header."""
    if len(data) < 12:
        return None
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return "image/gif"
    if data[4:8] == b"ftyp":
        return "video/mp4"
    if data.startswith(b"\x1a\x45\xdf\xa3"):
        return "video/webm"
    return None


def _max_bytes(mime_type: str) -> int:
    if mime_type in VIDEO_MIMES:
        return VIDEO_MAX_BYTES
    return IMAGE_MAX_BYTES


def _allowed_mimes(purpose: str) -> frozenset[str]:
    if purpose == PURPOSE_PROOF:
        return PROOF_MIMES
    return LISTING_MIMES


def _meta_path(media_id: str) -> Path:
    return UPLOAD_DIR / f"{media_id}.json"


def _file_path(media_id: str, mime_type: str) -> Path:
    ext = EXT_FOR_MIME.get(mime_type, ".bin")
    return UPLOAD_DIR / f"{media_id}{ext}"


def _public_url(media_id: str) -> str:
    return f"/api/media/{media_id}"


def save_upload(
    data: bytes,
    *,
    original_filename: str,
    purpose: str,
) -> MediaRecord:
    purpose_key = (purpose or PURPOSE_LISTING_IMAGE).strip().lower()
    if purpose_key not in ALLOWED_PURPOSES:
        raise MediaServiceError(
            f"Invalid purpose: {purpose}. Use listing_image or proof"
        )

    mime_type = sniff_mime(data)
    if mime_type is None or mime_type not in _allowed_mimes(purpose_key):
        allowed = ", ".join(sorted(_allowed_mimes(purpose_key)))
        raise MediaServiceError(f"Unsupported media type. Allowed: {allowed}")

    max_bytes = _max_bytes(mime_type)
    if len(data) > max_bytes:
        raise MediaServiceError(
            f"File exceeds size cap of {max_bytes} bytes"
        )

    media_id = str(uuid4())
    _ensure_upload_dir()
    dest = _file_path(media_id, mime_type)
    dest.write_bytes(data)

    record = MediaRecord(
        id=media_id,
        mime_type=mime_type,
        size_bytes=len(data),
        purpose=purpose_key,
        original_filename=original_filename or dest.name,
        url=_public_url(media_id),
        thumbnail_url=None,
    )
    _meta_path(media_id).write_text(
        json.dumps(
            {
                "id": record.id,
                "mime_type": record.mime_type,
                "size_bytes": record.size_bytes,
                "purpose": record.purpose,
                "original_filename": record.original_filename,
                "url": record.url,
                "thumbnail_url": record.thumbnail_url,
            }
        ),
        encoding="utf-8",
    )
    return record


def get_media(media_id: str) -> tuple[MediaRecord, Path]:
    try:
        parsed = str(UUID(media_id))
    except ValueError as exc:
        raise MediaServiceError("Media not found") from exc

    meta_file = _meta_path(parsed)
    if not meta_file.is_file():
        raise MediaServiceError("Media not found")
    payload = json.loads(meta_file.read_text(encoding="utf-8"))
    record = MediaRecord(
        id=payload["id"],
        mime_type=payload["mime_type"],
        size_bytes=payload["size_bytes"],
        purpose=payload["purpose"],
        original_filename=payload.get("original_filename", ""),
        url=payload.get("url", _public_url(parsed)),
        thumbnail_url=payload.get("thumbnail_url"),
    )
    path = _file_path(record.id, record.mime_type)
    if not path.is_file():
        raise MediaServiceError("Media not found")
    return record, path


def generate_thumbnail_stub(media_id: str) -> None:
    """BackgroundTasks stub — real thumbnails / malware scan belong on a worker."""
    logger.info("media:thumbnail_stub media_id=%s", media_id)
