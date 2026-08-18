"""Saved search filter combinations — per-user in-memory store (B5)."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import uuid4


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SavedSearchServiceError(ValueError):
    """Domain validation error for saved-search operations."""


@dataclass
class SavedSearchRecord:
    id: str
    user_id: str
    name: str
    filters: dict[str, Any]
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "filters": deepcopy(self.filters),
            "created_at": self.created_at,
        }


class SavedSearchStore:
    """Thread-safe per-user saved searches."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._items: dict[str, SavedSearchRecord] = {}

    def reset(self) -> None:
        with self._lock:
            self._items.clear()

    def add(self, record: SavedSearchRecord) -> SavedSearchRecord:
        with self._lock:
            self._items[record.id] = record
            return deepcopy(record)

    def get(self, search_id: str) -> SavedSearchRecord | None:
        with self._lock:
            rec = self._items.get(search_id)
            return deepcopy(rec) if rec else None

    def delete_owned(self, user_id: str, search_id: str) -> bool:
        with self._lock:
            rec = self._items.get(search_id)
            if rec is None or rec.user_id != user_id:
                return False
            del self._items[search_id]
            return True

    def list_for_user(self, user_id: str) -> list[SavedSearchRecord]:
        with self._lock:
            rows = [
                deepcopy(r) for r in self._items.values() if r.user_id == user_id
            ]
        return sorted(rows, key=lambda r: r.created_at, reverse=True)

    def count_for_user(self, user_id: str) -> int:
        with self._lock:
            return sum(1 for r in self._items.values() if r.user_id == user_id)


_store = SavedSearchStore()
MAX_SAVED_SEARCHES_PER_USER = 25
DEFAULT_NAME = "Saved search"


def reset_store() -> None:
    _store.reset()


def create_saved_search(
    user_id: str,
    *,
    name: str | None,
    filters: dict[str, Any],
) -> SavedSearchRecord:
    if _store.count_for_user(user_id) >= MAX_SAVED_SEARCHES_PER_USER:
        raise SavedSearchServiceError("Saved search limit reached")
    label = (name or "").strip() or DEFAULT_NAME
    record = SavedSearchRecord(
        id=str(uuid4()),
        user_id=user_id,
        name=label,
        filters=deepcopy(filters),
    )
    return _store.add(record)


def list_saved_searches(user_id: str) -> list[SavedSearchRecord]:
    return _store.list_for_user(user_id)


def delete_saved_search(user_id: str, search_id: str) -> None:
    if not _store.delete_owned(user_id, search_id):
        raise SavedSearchServiceError("Saved search not found")
