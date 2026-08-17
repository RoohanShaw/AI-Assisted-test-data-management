"""
main.py — Application entry point.

Startup sequence:
  1. Configure logging
  2. Warm up the embedding model
  3. Initialise the FAISS index (load from disk or rebuild from KB)
  4. Mount the API router
"""

import logging
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.config import API_DESCRIPTION, API_TITLE, API_VERSION
from app.embedding_engine import warm_up
from app.faiss_store import get_store

# ──────────────────────────────────────────────
# Logging Setup
# ──────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Lifespan (startup / shutdown)
# ──────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ────────────────────────────────
    logger.info("=" * 60)
    logger.info(f"  Starting {API_TITLE} v{API_VERSION}")
    logger.info("=" * 60)

    logger.info("Step 1/2 — Warming up embedding model …")
    warm_up()

    logger.info("Step 2/2 — Initialising FAISS index …")
    store = get_store()
    store.initialize()
    logger.info(f"  FAISS ready: {store.size} vectors indexed.")

    logger.info("Server ready. 🚀")
    logger.info("  Swagger UI: http://127.0.0.1:9090/docs")
    logger.info("  ReDoc:      http://127.0.0.1:9090/redoc")
    logger.info("=" * 60)

    yield  # hand over to the application

    # ── Shutdown ───────────────────────────────
    logger.info("Shutting down …")


# ──────────────────────────────────────────────
# FastAPI App
# ──────────────────────────────────────────────

app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Allow all origins in dev (restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API routes under /api/v1
app.include_router(router, prefix="/api/v1")


# ──────────────────────────────────────────────
# Root redirect
# ──────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": API_TITLE,
        "version": API_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
    }


# ──────────────────────────────────────────────
# Direct execution
# ──────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=9090,
        reload=True,
        log_level="info",
    )
