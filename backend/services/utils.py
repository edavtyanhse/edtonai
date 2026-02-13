"""Utility functions for text normalization and hashing."""

import hashlib
import json
import re
from typing import Any


def normalize_text(text: str) -> str:
    """Normalize text for consistent hashing.

    - Trim whitespace
    - Unify spaces (collapse multiple spaces/tabs to single space)
    - Remove repeated empty lines
    """
    # Trim
    text = text.strip()

    # Replace tabs with spaces
    text = text.replace("\t", " ")

    # Collapse multiple spaces to single
    text = re.sub(r" +", " ", text)

    # Collapse multiple newlines to single
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    # Trim each line
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    return text


def compute_hash(text: str) -> str:
    """Compute SHA256 hash of normalized text."""
    normalized = normalize_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def prompt_template_sha256(prompt_template: str) -> str:
    """Hash prompt template to invalidate caches when prompts change."""
    return hashlib.sha256(
        prompt_template.encode("utf-8", errors="replace")
    ).hexdigest()


def get_provider_name(provider: Any) -> str:
    name = getattr(provider, "provider_name", None)
    return str(name) if name else "unknown"


def get_model_name(provider: Any, fallback: str = "unknown") -> str:
    model = getattr(provider, "model", None) or getattr(provider, "model_name", None)
    return str(model) if model else fallback


def compute_ai_cache_key(operation: str, payload: dict[str, Any]) -> str:
    """Stable cache key for AIResult keyed by inputs + provider/model + prompt hash.

    The caller is responsible for including only the needed inputs (e.g. hashes instead of raw texts).
    """
    data = {"operation": operation, **payload}
    dumped = json.dumps(data, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()
