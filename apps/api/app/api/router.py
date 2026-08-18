"""
Domain API router aggregator.

Auth agent: include auth routers alongside this module — do not replace it.
  app.include_router(domain_router)   # from app.api.router
  app.include_router(auth_router)     # Auth-owned
"""

from __future__ import annotations

import importlib
import logging

from fastapi import APIRouter

from app.api import admin, availability, bookings, cis, listings, payments

logger = logging.getLogger(__name__)

domain_router = APIRouter()
domain_router.include_router(listings.router)
domain_router.include_router(bookings.router)
domain_router.include_router(availability.router)
domain_router.include_router(payments.router)
domain_router.include_router(admin.router)
domain_router.include_router(cis.router)

# New workstream-B routers — include only when the module exists so missing
# parallel agents cannot crash the API. Do not rewrite the includes above.
_OPTIONAL_MODULES = (
    "reviews",
    "conversations",
    "notifications",
    "favourites",
    "saved_searches",
    "media",
    "verification",
    "analytics",
    "public_stats",
    "attribution",
)


def _include_optional(module_name: str) -> None:
    try:
        module = importlib.import_module(f"app.api.{module_name}")
    except ImportError:
        logger.debug("optional router app.api.%s not present yet", module_name)
        return
    router = getattr(module, "router", None)
    if router is None:
        logger.warning("optional module app.api.%s has no `router`", module_name)
        return
    domain_router.include_router(router)


for _name in _OPTIONAL_MODULES:
    _include_optional(_name)
