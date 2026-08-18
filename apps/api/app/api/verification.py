"""B7 — seller business verification + buyer account-type capture."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, require_role
from app.domain_enums import UserRole
from app.repositories.memory_store import (
    AuditLogRecord,
    BuyerProfileRecord,
    PlatformUserRecord,
    SellerProfile,
    SellerVerificationRecord,
    new_id,
    store,
)

router = APIRouter(prefix="/api/verification", tags=["verification"])

VerificationStatus = Literal["pending", "verified", "rejected"]
AccountType = Literal["sme", "agency", "enterprise"]


class VerificationReviewAction(str, Enum):
    VERIFIED = "verified"
    REJECTED = "rejected"


class SellerVerificationSubmit(BaseModel):
    business_name: str = Field(min_length=1, max_length=255)
    company_number: str | None = Field(default=None, max_length=64)
    notes: str | None = Field(default=None, max_length=2000)
    document_urls: list[str] = Field(default_factory=list)


class SellerVerificationResponse(BaseModel):
    seller_id: str
    status: str
    business_name: str | None = None
    company_number: str | None = None
    notes: str | None = None
    document_urls: list[str] = Field(default_factory=list)
    review_reason: str | None = None
    is_verified: bool = False


class SellerVerificationListResponse(BaseModel):
    items: list[SellerVerificationResponse]


class VerificationReviewRequest(BaseModel):
    status: VerificationReviewAction
    reason: str = Field(min_length=1, max_length=2000)


class BuyerAccountTypeRequest(BaseModel):
    account_type: AccountType


class BuyerAccountTypeResponse(BaseModel):
    account_type: AccountType | None = None


def _to_verification_response(
    rec: SellerVerificationRecord,
) -> SellerVerificationResponse:
    return SellerVerificationResponse(
        seller_id=rec.seller_id,
        status=rec.status,
        business_name=rec.business_name,
        company_number=rec.company_number,
        notes=rec.notes,
        document_urls=list(rec.document_urls),
        review_reason=rec.review_reason,
        is_verified=rec.status == "verified",
    )


def _write_audit(
    user: CurrentUser,
    action: str,
    entity_type: str,
    entity_id: str,
    details: dict,
) -> None:
    store.add_audit_log(
        AuditLogRecord(
            id=new_id(),
            actor_id=user.id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        )
    )


@router.post(
    "/seller",
    response_model=SellerVerificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit seller business verification",
    description=(
        "Seller submits business details for admin review. Status becomes "
        "`pending`. Display `is_verified` only when status is `verified`."
    ),
)
async def submit_seller_verification(
    body: SellerVerificationSubmit,
    user: CurrentUser = Depends(require_role(UserRole.SELLER)),
) -> SellerVerificationResponse:
    existing = store.get_verification(user.id)
    if existing and existing.status == "verified":
        raise HTTPException(
            status_code=400,
            detail="Seller is already verified",
        )
    if store.get_seller(user.id) is None:
        store.upsert_seller(SellerProfile(user_id=user.id))
    store.upsert_user(PlatformUserRecord(id=user.id, role="seller"))
    record = SellerVerificationRecord(
        id=existing.id if existing else new_id(),
        seller_id=user.id,
        status="pending",
        business_name=body.business_name,
        company_number=body.company_number,
        notes=body.notes,
        document_urls=list(body.document_urls),
    )
    stored = store.upsert_verification(record)
    return _to_verification_response(stored)


@router.get(
    "/seller",
    response_model=SellerVerificationResponse,
    summary="Get own seller verification status",
    description="Seller-only. Returns unsubmitted when no application exists.",
)
async def get_seller_verification(
    user: CurrentUser = Depends(require_role(UserRole.SELLER)),
) -> SellerVerificationResponse:
    rec = store.get_verification(user.id)
    if not rec:
        return SellerVerificationResponse(
            seller_id=user.id,
            status="unsubmitted",
            is_verified=False,
        )
    return _to_verification_response(rec)


@router.get(
    "/admin/pending",
    response_model=SellerVerificationListResponse,
    summary="List pending seller verifications",
    description="Admin review queue. Only `pending` applications are returned.",
)
async def list_pending_verifications(
    user: CurrentUser = Depends(require_role(UserRole.ADMIN)),
) -> SellerVerificationListResponse:
    del user
    items = store.list_verifications(status="pending")
    return SellerVerificationListResponse(
        items=[_to_verification_response(r) for r in items]
    )


@router.post(
    "/admin/{seller_id}/review",
    response_model=SellerVerificationResponse,
    summary="Approve or reject seller verification",
    description=(
        "Admin sets status to `verified` or `rejected`. Writes an audit_logs "
        "row. `is_verified` is true only for `verified`."
    ),
)
async def review_seller_verification(
    seller_id: str,
    body: VerificationReviewRequest,
    user: CurrentUser = Depends(require_role(UserRole.ADMIN)),
) -> SellerVerificationResponse:
    rec = store.get_verification(seller_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Verification not found")
    if rec.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Verification is {rec.status}, not pending",
        )
    rec.status = body.status.value
    rec.review_reason = body.reason
    rec.reviewed_by = user.id
    stored = store.upsert_verification(rec)
    _write_audit(
        user,
        action="review_seller_verification",
        entity_type="seller_verification",
        entity_id=seller_id,
        details={"status": stored.status, "reason": body.reason},
    )
    return _to_verification_response(stored)


@router.put(
    "/buyer/account-type",
    response_model=BuyerAccountTypeResponse,
    summary="Set buyer account type",
    description="Additive capture of SME / agency / enterprise. Buyer-only.",
)
async def set_buyer_account_type(
    body: BuyerAccountTypeRequest,
    user: CurrentUser = Depends(require_role(UserRole.BUYER)),
) -> BuyerAccountTypeResponse:
    store.upsert_user(PlatformUserRecord(id=user.id, role="buyer"))
    store.upsert_buyer_profile(
        BuyerProfileRecord(user_id=user.id, account_type=body.account_type)
    )
    return BuyerAccountTypeResponse(account_type=body.account_type)


@router.get(
    "/buyer/account-type",
    response_model=BuyerAccountTypeResponse,
    summary="Get buyer account type",
    description="Returns null account_type when the buyer has not set one.",
)
async def get_buyer_account_type(
    user: CurrentUser = Depends(require_role(UserRole.BUYER)),
) -> BuyerAccountTypeResponse:
    profile = store.get_buyer_profile(user.id)
    account_type: AccountType | None = None
    if profile and profile.account_type in ("sme", "agency", "enterprise"):
        account_type = profile.account_type  # type: ignore[assignment]
    return BuyerAccountTypeResponse(account_type=account_type)
