"""
start.py — Application entry point.

Startup sequence:
  1. Load .env
  2. Run smoke tests  (exits with code 1 on any failure — FastAPI never starts)
  3. Configure logging
  4. Warm up the embedding model
  5. Initialise the FAISS index (load from disk or rebuild from KB)
  6. Mount the API router
  7. Start FastAPI server on localhost:8000
  8. Automatically open default browser to http://127.0.0.1:8000/docs
"""
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed; rely on shell environment

import logging
import sys
import threading
import time
import webbrowser
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.config import API_DESCRIPTION, API_TITLE, API_VERSION
from app.embedding_engine import warm_up
from app.faiss_store import get_store
from test_smoke import run_smoke_tests

# ──────────────────────────────────────────────────────────────────────────────
# Smoke Tests  (run before FastAPI initialises; exits with code 1 on failure)
# ──────────────────────────────────────────────────────────────────────────────

run_smoke_tests()

# ──────────────────────────────────────────────────────────────────────────────
# Logging Setup
# ──────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Browser Helper  (opens Swagger UI automatically once server is ready)
# ──────────────────────────────────────────────────────────────────────────────

_browser_opened = False

def open_browser_once(url: str = "http://127.0.0.1:9090/docs") -> None:
    """Launch the user's default browser exactly once after server is ready."""
    global _browser_opened
    if not _browser_opened:
        _browser_opened = True
        def _open():
            time.sleep(1.5)  # brief wait for socket to begin accepting requests
            logger.info(f"Opening browser to {url} ...")
            webbrowser.open(url)
        threading.Thread(target=_open, daemon=True).start()


# ──────────────────────────────────────────────────────────────────────────────
# Lifespan (startup / shutdown)
# ──────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ────────────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info(f"  Starting {API_TITLE} v{API_VERSION}")
    logger.info("=" * 60)

    logger.info("Step 1/2 – Warming up embedding model …")
    warm_up()

    logger.info("Step 2/2 – Initialising FAISS index …")
    store = get_store()
    store.initialize()
    logger.info(f"  FAISS ready: {store.size} vectors indexed.")

    logger.info("Server ready. 🚀  (smoke tests already passed)")
    logger.info("  Swagger UI: http://127.0.0.1:9090/docs")
    logger.info("  ReDoc:      http://127.0.0.1:9090/redoc")
    logger.info("=" * 60)

    # Launch browser automatically once server is ready
    open_browser_once("http://127.0.0.1:9090/docs")

    yield  # hand over to the application

    # ── Shutdown ───────────────────────────────────────────────────────────────
    logger.info("Shutting down …")


# ──────────────────────────────────────────────────────────────────────────────
# FastAPI App
# ──────────────────────────────────────────────────────────────────────────────

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


# ──────────────────────────────────────────────────────────────────────────────
# Root redirect
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": API_TITLE,
        "version": API_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
    }


# ──────────────────────────────────────────────────────────────────────────────
# Direct execution
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    is_frozen = getattr(sys, "frozen", False)
    uvicorn.run(
        app if is_frozen else "start:app",
        host="127.0.0.1",
        port=9090,
        reload=not is_frozen,
        log_level="info",
    )
