"""Saved listings / favourites — per-user in-memory store (B4)."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import uuid4

from app.repositories.memory_store import store as listing_store


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class FavouriteServiceError(ValueError):
    """Domain validation error for favourite operations."""


@dataclass
class FavouriteRecord:
    id: str
    user_id: str
    listing_id: str
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "listing_id": self.listing_id,
            "created_at": self.created_at,
        }


class FavouriteStore:
    """Thread-safe per-user favourites. Unique on (user_id, listing_id)."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._items: dict[str, FavouriteRecord] = {}

    def reset(self) -> None:
        with self._lock:
            self._items.clear()

    def get(self, favourite_id: str) -> FavouriteRecord | None:
        with self._lock:
            rec = self._items.get(favourite_id)
            return deepcopy(rec) if rec else None

    def find_for_user_listing(
        self, user_id: str, listing_id: str
    ) -> FavouriteRecord | None:
        with self._lock:
            for rec in self._items.values():
                if rec.user_id == user_id and rec.listing_id == listing_id:
                    return deepcopy(rec)
            return None

    def add(self, record: FavouriteRecord) -> FavouriteRecord:
        with self._lock:
            self._items[record.id] = record
            return deepcopy(record)

    def delete_for_user(self, user_id: str, listing_id: str) -> bool:
        with self._lock:
            for fid, rec in list(self._items.items()):
                if rec.user_id == user_id and rec.listing_id == listing_id:
                    del self._items[fid]
                    return True
            return False

    def list_for_user(self, user_id: str) -> list[FavouriteRecord]:
        with self._lock:
            rows = [
                deepcopy(r) for r in self._items.values() if r.user_id == user_id
            ]
        return sorted(rows, key=lambda r: r.created_at, reverse=True)


_store = FavouriteStore()
MAX_FAVOURITES_PER_USER = 200


def reset_store() -> None:
    _store.reset()


def add_favourite(user_id: str, listing_id: str) -> tuple[FavouriteRecord, bool]:
    """
    Add listing to the caller's favourites.

    Returns (record, created). created=False when the pair already existed.
    """
    listing = listing_store.get_listing(listing_id)
    if listing is None:
        raise FavouriteServiceError("Listing not found")

    existing = _store.find_for_user_listing(user_id, listing_id)
    if existing is not None:
        return existing, False

    if len(_store.list_for_user(user_id)) >= MAX_FAVOURITES_PER_USER:
        raise FavouriteServiceError("Favourite limit reached")

    record = FavouriteRecord(
        id=str(uuid4()),
        user_id=user_id,
        listing_id=listing_id,
    )
    return _store.add(record), True


def remove_favourite(user_id: str, listing_id: str) -> None:
    if not _store.delete_for_user(user_id, listing_id):
        raise FavouriteServiceError("Favourite not found")


def list_favourites(user_id: str) -> list[FavouriteRecord]:
    return _store.list_for_user(user_id)
