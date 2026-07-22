"""
Domain API router aggregator.

Auth agent: include auth routers alongside this module — do not replace it.
  app.include_router(domain_router)   # from app.api.router
  app.include_router(auth_router)     # Auth-owned
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api import admin, availability, bookings, cis, listings, payments

domain_router = APIRouter()
domain_router.include_router(listings.router)
domain_router.include_router(bookings.router)
domain_router.include_router(availability.router)
domain_router.include_router(payments.router)
domain_router.include_router(admin.router)
domain_router.include_router(cis.router)
