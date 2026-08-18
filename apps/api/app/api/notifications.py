"""Notifications API — list + bulk mark-read (B3)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import CurrentUser, get_current_user
from app.schemas.notifications import (
    MarkReadRequest,
    MarkReadResponse,
    NotificationListResponse,
    NotificationResponse,
)
from app.services import notification_service

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


def _to_response(record) -> NotificationResponse:
    return NotificationResponse(
        id=record.id,
        user_id=record.user_id,
        event_type=record.event_type,
        title=record.title,
        body=record.body,
        booking_id=record.booking_id,
        listing_id=record.listing_id,
        read=record.read,
        created_at=record.created_at,
    )


@router.get(
    "",
    response_model=NotificationListResponse,
    summary="List in-app notifications",
    description=(
        "Paginated notifications for the authenticated user only, newest first. "
        "unread_count is the caller's total unread (not just this page)."
    ),
)
async def list_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    user: CurrentUser = Depends(get_current_user),
) -> NotificationListResponse:
    items, total, unread = notification_service.list_notifications(
        user.id, page=page, page_size=page_size
    )
    return NotificationListResponse(
        items=[_to_response(row) for row in items],
        total=total,
        page=page,
        page_size=page_size,
        unread_count=unread,
    )


@router.post(
    "/mark-read",
    response_model=MarkReadResponse,
    summary="Mark notifications as read",
    description=(
        "Bulk-mark the authenticated user's notifications as read. "
        "Pass ids for a subset, or mark_all=true (e.g. opening the bell dropdown). "
        "Ids that are not owned by the caller are ignored."
    ),
)
async def mark_notifications_read(
    body: MarkReadRequest,
    user: CurrentUser = Depends(get_current_user),
) -> MarkReadResponse:
    if not body.mark_all and not body.ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide ids or set mark_all=true",
        )
    marked, unread = notification_service.mark_read(
        user.id, body.ids, mark_all=body.mark_all
    )
    return MarkReadResponse(marked_count=marked, unread_count=unread)


def register_engagement_routers(parent) -> None:
    """Mount B3/B4/B5 routers. Call from the domain aggregator when wiring."""
    from app.api.favourites import router as favourites_router
    from app.api.saved_searches import router as saved_searches_router

    parent.include_router(router)
    parent.include_router(favourites_router)
    parent.include_router(saved_searches_router)
