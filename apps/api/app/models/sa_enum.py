"""SQLAlchemy Enum column helpers — PostgreSQL native enums."""

from __future__ import annotations

from enum import Enum as PyEnum
from typing import TypeVar

from sqlalchemy import Enum as SAEnum

E = TypeVar("E", bound=PyEnum)


def pg_enum(enum_cls: type[E], name: str) -> SAEnum:
    """Persist Python str enums as PostgreSQL ENUM types."""
    return SAEnum(
        enum_cls,
        name=name,
        native_enum=True,
        values_callable=lambda x: [e.value for e in x],
        validate_strings=True,
    )
