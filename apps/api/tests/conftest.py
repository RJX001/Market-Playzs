"""Pytest fixtures."""

from __future__ import annotations

import pytest

from app.repositories.memory_store import store


@pytest.fixture(autouse=True)
def _reset_store() -> None:
    store.reset()
    yield
    store.reset()
