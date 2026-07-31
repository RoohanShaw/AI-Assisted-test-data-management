"""
cache.py — Persistent JSON cache for FAISS classification results.

Any field classified by FAISS is stored here so subsequent identical
(or near-identical) requests don't incur API cost.
"""

import json
import logging
import os
from typing import Optional

from app.config import LEARNED_CACHE_PATH

logger = logging.getLogger(__name__)


class FieldCache:
    """
    Simple key-value store: field_name (lowercase) → {category, generator}.

    Backed by a JSON file so it survives server restarts.
    """

    def __init__(self) -> None:
        self._cache: dict = {}
        self._load()

    # ──────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────

    def get(self, field_name: str) -> Optional[dict]:
        """Return cached classification or None."""
        return self._cache.get(self._key(field_name))

    def set(self, field_name: str, category: str, generator: str, source: str = "openai") -> None:
        """Store a classification and flush to disk."""
        key = self._key(field_name)
        self._cache[key] = {
            "field_name": field_name,
            "category":   category,
            "generator":  generator,
            "source":     source,
        }
        self._save()
        logger.info(f"Cache: stored '{field_name}' → '{category}' (source={source})")

    def delete(self, field_name: str) -> bool:
        """Remove an entry (useful for feedback corrections). Returns True if found."""
        key = self._key(field_name)
        if key in self._cache:
            del self._cache[key]
            self._save()
            return True
        return False

    def all_entries(self) -> list:
        return list(self._cache.values())

    @property
    def size(self) -> int:
        return len(self._cache)

    # ──────────────────────────────────────────────
    # Internals
    # ──────────────────────────────────────────────

    def _key(self, field_name: str) -> str:
        """Normalised cache key: lowercase, stripped."""
        return field_name.strip().lower()

    def _load(self) -> None:
        try:
            if LEARNED_CACHE_PATH.exists():
                with open(LEARNED_CACHE_PATH, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                logger.info(f"Cache loaded: {len(self._cache)} entries.")
        except Exception as exc:
            logger.warning(f"Cache load failed ({exc}); starting fresh.")
            self._cache = {}

    def _save(self) -> None:
        os.makedirs(str(LEARNED_CACHE_PATH.parent), exist_ok=True)
        with open(LEARNED_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(self._cache, f, indent=2, ensure_ascii=False)


# Module-level singleton
_cache: FieldCache | None = None


def get_cache() -> FieldCache:
    global _cache
    if _cache is None:
        _cache = FieldCache()
    return _cache
