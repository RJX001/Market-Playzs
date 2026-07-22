"""CIS API — per-listing nullable score + admin override."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import CurrentUser, require_role
from app.domain_enums import UserRole
from app.schemas.cis import CisOverrideRequest, CisScoreResponse
from app.services import cis_service
from app.services.cis_service import CisServiceError

router = APIRouter(prefix="/api/cis", tags=["cis"])


@router.get("/listings/{listing_id}", response_model=CisScoreResponse)
async def get_listing_cis(listing_id: str) -> CisScoreResponse:
    try:
        score, overridden, counted = cis_service.get_listing_cis(listing_id)
    except CisServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return CisScoreResponse(
        listing_id=listing_id,
        cis_score=score,
        is_cis_overridden=overridden,
        completed_bookings_counted=counted,
    )


@router.post(
    "/listings/{listing_id}/override", response_model=CisScoreResponse
)
async def override_listing_cis(
    listing_id: str,
    body: CisOverrideRequest,
    user: CurrentUser = Depends(require_role(UserRole.ADMIN)),
) -> CisScoreResponse:
    try:
        score = cis_service.apply_admin_override(
            listing_id=listing_id,
            cis_score=body.cis_score,
            admin_id=user.id,
            reason=body.reason,
        )
    except CisServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return CisScoreResponse(
        listing_id=listing_id,
        cis_score=score,
        is_cis_overridden=True,
        completed_bookings_counted=0,
    )
