"""Helpers for storing bearer-style secrets safely."""

from __future__ import annotations

import hashlib


def hash_secret(secret: str) -> str:
    """Return a stable SHA-256 hash for tokens stored in the database."""
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()
