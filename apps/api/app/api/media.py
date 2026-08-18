"""Media upload API — listing images and proof photos/videos (B6)."""

from __future__ import annotations

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict

from app.api.deps import CurrentUser, require_role
from app.domain_enums import UserRole
from app.services import media_service
from app.services.media_service import MediaServiceError

router = APIRouter(prefix="/api/media", tags=["media"])

# Read this many bytes at a time while enforcing the size cap in-stream.
_READ_CHUNK = 64 * 1024
_HARD_CAP = media_service.VIDEO_MAX_BYTES


class MediaUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    url: str
    mime_type: str
    size_bytes: int
    purpose: str
    thumbnail_url: str | None = None


def _http_for_media_error(exc: MediaServiceError) -> HTTPException:
    detail = str(exc)
    if "not found" in detail.lower():
        return HTTPException(status_code=404, detail=detail)
    if "exceeds size cap" in detail.lower():
        return HTTPException(status_code=413, detail=detail)
    if "unsupported media type" in detail.lower():
        return HTTPException(status_code=415, detail=detail)
    return HTTPException(status_code=400, detail=detail)


@router.post(
    "/upload",
    response_model=MediaUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload listing or proof media",
    description=(
        "Single upload for listing images (`purpose=listing_image`) and "
        "proof-of-play photos/videos (`purpose=proof`). MIME is sniffed from "
        "file bytes (not the client filename/header). Size caps: 10 MiB images, "
        "50 MiB videos. Thumbnail generation is queued as a background stub."
    ),
)
async def upload_media(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    purpose: str = Query(
        default=media_service.PURPOSE_LISTING_IMAGE,
        description="listing_image | proof",
    ),
    _user: CurrentUser = Depends(
        require_role(UserRole.SELLER, UserRole.BUYER, UserRole.ADMIN)
    ),
) -> MediaUploadResponse:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(_READ_CHUNK)
        if not chunk:
            break
        total += len(chunk)
        if total > _HARD_CAP:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds size cap of {_HARD_CAP} bytes",
            )
        chunks.append(chunk)
    data = b"".join(chunks)

    try:
        record = media_service.save_upload(
            data,
            original_filename=file.filename or "",
            purpose=purpose,
        )
    except MediaServiceError as exc:
        raise _http_for_media_error(exc) from exc

    background_tasks.add_task(
        media_service.generate_thumbnail_stub, record.id
    )
    return MediaUploadResponse(
        id=record.id,
        url=record.url,
        mime_type=record.mime_type,
        size_bytes=record.size_bytes,
        purpose=record.purpose,
        thumbnail_url=record.thumbnail_url,
    )


@router.get(
    "/{media_id}",
    summary="Download uploaded media",
    description="Serves a previously uploaded listing image or proof file by id.",
)
async def get_media(media_id: str) -> FileResponse:
    try:
        record, path = media_service.get_media(media_id)
    except MediaServiceError as exc:
        raise _http_for_media_error(exc) from exc
    return FileResponse(
        path,
        media_type=record.mime_type,
        filename=record.original_filename or path.name,
    )
