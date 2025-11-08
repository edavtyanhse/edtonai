from __future__ import annotations

from pathlib import Path
from typing import Generator

# Ensure the backend package is importable when tests run from the repo root.
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from sqlalchemy import create_engine

from backend.app import db
from backend.app.models import Base


@pytest.fixture(autouse=True)
def _configure_test_database(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Initialise an in-memory SQLite database for repository tests."""

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    monkeypatch.setattr(db, "_engine", engine)
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")

    yield

    Base.metadata.drop_all(engine)
    monkeypatch.setattr(db, "_engine", None)
