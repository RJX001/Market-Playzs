"""Database engine and session factory.

Mode: SQLAlchemy 2.x **sync** with psycopg2 (see requirements.txt).
Async migration path: swap to create_async_engine + async_sessionmaker
and asyncpg when Vercel/worker workloads require it; models already use
2.0 DeclarativeBase / Mapped style and are async-compatible.
"""

from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/marketplays",
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yield a sync Session, always close."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


__all__ = ["Base", "DATABASE_URL", "SessionLocal", "engine", "get_db"]
