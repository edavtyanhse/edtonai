"""Root conftest — shared across unit & integration test suites."""

import os

import pytest

os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_DB", "edtonai_test")
os.environ.setdefault("LOG_LEVEL", "INFO")


@pytest.fixture
def anyio_backend():
    """Use asyncio as the async backend for all tests."""
    return "asyncio"
