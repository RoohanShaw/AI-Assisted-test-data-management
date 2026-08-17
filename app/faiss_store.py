"""
faiss_store.py — FAISS-backed similarity search over the knowledge base.

Index type: IndexFlatIP (inner-product / cosine similarity on L2-normalised vectors).
The meta list keeps label → (category, generator) mappings in the same order as
the FAISS index rows so a row id can be instantly resolved.
"""

import json
import logging
import os
import numpy as np
import faiss
from typing import List, Optional, Tuple

from app.config import (
    FAISS_INDEX_PATH,
    FAISS_META_PATH,
    FIELD_MAPPING_PATH,
    EMBEDDING_DIM,
    FAISS_TOP_K,
)
from app.embedding_engine import batch_encode, encode

logger = logging.getLogger(__name__)


class FAISSStore:
    """Thread-safe FAISS store for field-name → (category, generator) lookup."""

    def __init__(self) -> None:
        self.index: faiss.IndexFlatIP = faiss.IndexFlatIP(EMBEDDING_DIM)
        # Parallel list: meta[i] = {"field_name": ..., "category": ..., "generator": ...}
        self.meta: List[dict] = []

    # ──────────────────────────────────────────────
    # Build / Persist
    # ──────────────────────────────────────────────

    def build_from_knowledge_base(self) -> None:
        """
        Load field_mapping.json, encode all field names, and populate the index.
        Called once at startup (or when the index file is missing).
        """
        with open(FIELD_MAPPING_PATH, "r", encoding="utf-8") as f:
            kb = json.load(f)

        entries = kb["fields"]
        field_names = [e["field_name"] for e in entries]
        logger.info(f"Building FAISS index from {len(field_names)} knowledge-base entries …")

        vectors = batch_encode(field_names)          # (N, DIM) float32, L2-normalised
        self.index.add(vectors)
        self.meta = [
            {
                "field_name": e["field_name"],
                "category":   e["category"],
                "generator":  e["generator"],
            }
            for e in entries
        ]
        logger.info("FAISS index built.")

    def save(self) -> None:
        """Persist index + metadata to disk."""
        os.makedirs(str(FAISS_INDEX_PATH.parent), exist_ok=True)
        faiss.write_index(self.index, str(FAISS_INDEX_PATH))
        with open(FAISS_META_PATH, "w", encoding="utf-8") as f:
            json.dump(self.meta, f, indent=2, ensure_ascii=False)
        logger.info(f"FAISS index saved ({self.index.ntotal} vectors).")

    def load(self) -> bool:
        """
        Try to load a persisted index. Returns True on success.
        If files are missing or corrupt, returns False (caller should rebuild).
        """
        try:
            self.index = faiss.read_index(str(FAISS_INDEX_PATH))
            with open(FAISS_META_PATH, "r", encoding="utf-8") as f:
                self.meta = json.load(f)
            logger.info(f"FAISS index loaded ({self.index.ntotal} vectors).")
            return True
        except Exception as exc:
            logger.warning(f"Could not load FAISS index: {exc}")
            return False

    def initialize(self) -> None:
        """
        Load from disk if possible; rebuild + save otherwise.
        Called at application startup.
        """
        if not self.load():
            self.build_from_knowledge_base()
            self.save()

    # ──────────────────────────────────────────────
    # Search
    # ──────────────────────────────────────────────

    def search(
        self, query: str, top_k: int = FAISS_TOP_K
    ) -> List[Tuple[dict, float]]:
        """
        Find the top-k most similar entries to `query`.

        Returns: list of (meta_dict, cosine_similarity_score)  — sorted descending.
        """
        if self.index.ntotal == 0:
            return []

        vec = encode(query, normalize=True).reshape(1, -1)
        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(vec, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            results.append((self.meta[idx], float(score)))
        return results  # already sorted best-first by FAISS

    def best_match(self, query: str) -> Tuple[Optional[dict], float]:
        """
        Return the single best match and its score.
        If the index is empty, returns (None, 0.0).
        """
        results = self.search(query, top_k=1)
        if not results:
            return None, 0.0
        return results[0]

    # ──────────────────────────────────────────────
    # Dynamic Insert (Learned Fields)
    # ──────────────────────────────────────────────

    def add_entry(
        self, field_name: str, category: str, generator: str, save_after: bool = True
    ) -> None:
        """
        Add a new field→category mapping to the live index.
        """
        vec = encode(field_name, normalize=True).reshape(1, -1)
        self.index.add(vec)
        self.meta.append(
            {"field_name": field_name, "category": category, "generator": generator}
        )
        if save_after:
            self.save()
        logger.info(f"Added '{field_name}' → '{category}' to FAISS index.")

    @property
    def size(self) -> int:
        return self.index.ntotal


# ──────────────────────────────────────────────
# Module-level singleton
# ──────────────────────────────────────────────
_store: FAISSStore | None = None


def get_store() -> FAISSStore:
    global _store
    if _store is None:
        _store = FAISSStore()
    return _store
