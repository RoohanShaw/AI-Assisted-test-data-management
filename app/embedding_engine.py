"""
embedding_engine.py — Wraps SentenceTransformer for consistent vector encoding.

Singleton pattern: the model is loaded once at startup and reused.
"""

import logging
import numpy as np
from typing import List, Union
from sentence_transformers import SentenceTransformer

from app.config import EMBEDDING_MODEL, EMBEDDING_DIM

logger = logging.getLogger(__name__)

# Module-level singleton
_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Return the (lazily loaded) SentenceTransformer model."""
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL} …")
        _model = SentenceTransformer(EMBEDDING_MODEL)
        logger.info("Embedding model loaded.")
    return _model


def encode(text: Union[str, List[str]], normalize: bool = True) -> np.ndarray:
    """
    Encode one or more texts into L2-normalised float32 vectors.

    Args:
        text:      A single string or a list of strings.
        normalize: If True, L2-normalise so that dot-product == cosine similarity.

    Returns:
        np.ndarray of shape (embedding_dim,) for a single string,
        or (N, embedding_dim) for a list.
    """
    model = get_model()
    is_single = isinstance(text, str)
    texts = [text] if is_single else text

    # Clean and lowercase for better matching
    texts = [t.strip().lower() for t in texts]

    vectors = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=normalize,
        show_progress_bar=False,
    ).astype(np.float32)

    return vectors[0] if is_single else vectors


def batch_encode(texts: List[str], batch_size: int = 64) -> np.ndarray:
    """
    Encode a large list of texts in mini-batches (memory-friendly).

    Returns: np.ndarray of shape (N, EMBEDDING_DIM)
    """
    model = get_model()
    cleaned = [t.strip().lower() for t in texts]
    return model.encode(
        cleaned,
        convert_to_numpy=True,
        normalize_embeddings=True,
        batch_size=batch_size,
        show_progress_bar=False,
    ).astype(np.float32)


def warm_up() -> None:
    """Pre-load the model at application startup so the first request is fast."""
    get_model()
    # Dummy encode to trigger JIT compilation
    encode("warm up", normalize=True)
    logger.info("Embedding engine warmed up.")
