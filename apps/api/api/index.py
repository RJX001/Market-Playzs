"""Vercel-discoverable entry — re-exports FastAPI `app` from app.main."""

from app.main import app

__all__ = ["app"]
