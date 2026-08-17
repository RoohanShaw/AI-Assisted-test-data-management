"""
config.py — Central configuration for AI Test Data Generator
All tuneable knobs are here so nothing is hardcoded elsewhere.
"""

import os
import sys
from pathlib import Path

# ──────────────────────────────────────────────
# Project Paths (Supports Dev & PyInstaller)
# ──────────────────────────────────────────────
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file if present
try:
    from dotenv import load_dotenv
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()
except ImportError:
    pass  # python-dotenv not installed; use shell environment variables

KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
OUTPUT_DIR = BASE_DIR / "output"

FIELD_MAPPING_PATH   = KNOWLEDGE_BASE_DIR / "field_mapping.json"
FAISS_INDEX_PATH     = KNOWLEDGE_BASE_DIR / "faiss_index.bin"
FAISS_META_PATH      = KNOWLEDGE_BASE_DIR / "faiss_meta.json"   # label ↔ index mapping
LEARNED_CACHE_PATH   = KNOWLEDGE_BASE_DIR / "learned_fields.json"

# Path to the bundled Excel TDM template (used as a reference for uploads)
EXCEL_TEMPLATE_PATH  = BASE_DIR / "TP_AppointmentList_TDM.xlsx"

# ──────────────────────────────────────────────
# Embedding Model
# ──────────────────────────────────────────────
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM   = 384          # dimension for all-MiniLM-L6-v2

# ──────────────────────────────────────────────
# FAISS / Similarity
# ──────────────────────────────────────────────
# Cosine similarity threshold (0–1).
# If best match score >= this → use FAISS result directly.

SIMILARITY_THRESHOLD = 0.82    # tuned: 0.82 gives good balance

# How many nearest neighbours to retrieve from FAISS
FAISS_TOP_K = 3


# ──────────────────────────────────────────────
# Generation
# ──────────────────────────────────────────────
DEFAULT_LOCALE = "en_IN"      # Faker locale — Indian names by default
MAX_RECORDS    = 1000         # hard cap on record_count per request

# ──────────────────────────────────────────────
# API
# ──────────────────────────────────────────────
API_TITLE   = "AI Test Data Generator"
API_VERSION = "1.0.0"
API_DESCRIPTION = (
    "Generates realistic test data from JSON / Excel field definitions using "
    "semantic classification (SentenceTransformer embeddings + FAISS similarity search + "
    "heuristic fallback) and business-rule-aware Faker generation. "
    "Fully local — no external API calls required."
)
