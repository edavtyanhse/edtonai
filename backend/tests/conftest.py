"""Root conftest — shared across unit & integration test suites."""

import pytest


@pytest.fixture
def anyio_backend():
    """Use asyncio as the async backend for all tests."""
    return "asyncio"
