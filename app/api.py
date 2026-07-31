"""
api.py — FastAPI router with all endpoints.

Endpoints:
  POST /generate   — main data-generation endpoint
  GET  /health     — readiness/health check
  GET  /knowledge  — inspect the knowledge base + learned cache
  POST /feedback   — submit a manual correction for a misclassified field
  POST /rebuild    — force-rebuild the FAISS index from scratch
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.cache import get_cache
from app.config import DEFAULT_LOCALE, FIELD_MAPPING_PATH, EMBEDDING_MODEL
from app.excel_parser import parse_json_input, parse_excel_input
from app.faiss_store import get_store
from app.generator import DataGenerator
from app.models import (
    FeedbackRequest,
    FeedbackResponse,
    FieldClassificationMeta,
    FieldMetadata,
    FromJsonRequest,
    GenerateRequest,
    GenerateResponse,
    HealthResponse,
    KnowledgeEntry,
    KnowledgeResponse,
    TemplateGenerateResponse,
)
from app.field_type_router import should_empty
from app.pipeline import run_pipeline
from app.semantic_classifier import classify_fields
from app.template_builder import build_template

logger = logging.getLogger(__name__)

router = APIRouter()


# ══════════════════════════════════════════════
# POST /generate
# ══════════════════════════════════════════════

@router.post(
    "/generate",
    response_model=GenerateResponse,
    summary="Generate test data",
    description=(
        "Accepts a JSON payload with field definitions and returns "
        "realistic synthetic test records."
    ),
    tags=["Data Generation"],
)
async def generate(request: GenerateRequest) -> GenerateResponse:
    """
    Main endpoint: classify fields → apply rules → generate N records.
    """
    logger.info(
        f"POST /generate | module={request.module} | "
        f"fields={[f.field_name for f in request.fields]} | "
        f"record_count={request.record_count}"
    )

    warnings: List[str] = []

    # ── 1. Classify all fields ──────────────────────────────────────────
    classifications = classify_fields(request.fields, module=request.module)

    # Warn about heuristic / fallback sources
    for clf in classifications:
        if clf.source == "fallback":
            warnings.append(
                f"Field '{clf.field_name}' could not be confidently classified "
                f"(score={clf.confidence:.2f}). Used heuristic fallback → '{clf.category}'."
            )

    # ── 2. Build generator ──────────────────────────────────────────────
    locale = request.locale or DEFAULT_LOCALE
    gen = DataGenerator(locale=locale, seed=request.seed)

    # ── 3. Generate records ─────────────────────────────────────────────
    records = []
    for _ in range(request.record_count):
        record = {}
        for clf in classifications:
            if should_empty(clf):
                value = ""
            else:
                try:
                    value = gen.generate(clf.generator, clf.rules)
                except Exception as exc:
                    logger.error(
                        f"Generator error for '{clf.field_name}' "
                        f"(generator={clf.generator}): {exc}"
                    )
                    value = None
                    warnings.append(
                        f"Generator failed for '{clf.field_name}': {exc}"
                    )
            record[clf.field_name] = value
        records.append(record)

    # ── 4. Build metadata ───────────────────────────────────────────────
    field_metadata = [
        FieldMetadata(
            field_name=clf.field_name,
            category=clf.category,
            generator=clf.generator,
            confidence=clf.confidence,
            source=clf.source,
        )
        for clf in classifications
    ]

    logger.info(
        f"Generated {len(records)} record(s) for module '{request.module}'. "
        f"Warnings: {len(warnings)}"
    )

    return GenerateResponse(
        module=request.module,
        record_count=len(records),
        records=records,
        field_metadata=field_metadata,
        warnings=warnings,
    )


# ══════════════════════════════════════════════
# GET /health
# ══════════════════════════════════════════════

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    tags=["System"],
)
async def health() -> HealthResponse:
    """Returns system readiness status."""
    import json
    from app.config import FIELD_MAPPING_PATH, EMBEDDING_MODEL

    # Count KB entries
    kb_size = 0
    try:
        with open(FIELD_MAPPING_PATH) as f:
            kb_size = len(json.load(f).get("fields", []))
    except Exception:
        pass

    store = get_store()
    cache = get_cache()

    return HealthResponse(
        status="ok",
        knowledge_base_size=kb_size,
        learned_cache_size=cache.size,
        faiss_index_size=store.size,
        embedding_model=EMBEDDING_MODEL,
    )


# ══════════════════════════════════════════════
# GET /knowledge
# ══════════════════════════════════════════════

@router.get(
    "/knowledge",
    response_model=KnowledgeResponse,
    summary="Inspect knowledge base",
    tags=["System"],
)
async def knowledge(
    source: str = Query(
        default="all",
        description="Filter by source: 'kb' (knowledge base), 'cache' (learned), 'all'"
    )
) -> KnowledgeResponse:
    """
    Returns all known field→category mappings.
    Combines the static knowledge base and the dynamically-learned cache.
    """
    import json
    from app.config import FIELD_MAPPING_PATH

    entries: List[KnowledgeEntry] = []

    if source in ("kb", "all"):
        try:
            with open(FIELD_MAPPING_PATH) as f:
                for e in json.load(f).get("fields", []):
                    entries.append(KnowledgeEntry(
                        field_name=e["field_name"],
                        category=e["category"],
                        generator=e["generator"],
                        source="knowledge_base",
                    ))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Cannot read knowledge base: {exc}")

    if source in ("cache", "all"):
        cache = get_cache()
        for e in cache.all_entries():
            entries.append(KnowledgeEntry(
                field_name=e["field_name"],
                category=e["category"],
                generator=e["generator"],
                source=e.get("source", "learned"),
            ))

    return KnowledgeResponse(total=len(entries), entries=entries)


# ══════════════════════════════════════════════
# POST /feedback
# ══════════════════════════════════════════════

@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    summary="Correct a field classification",
    tags=["System"],
)
async def feedback(req: FeedbackRequest) -> FeedbackResponse:
    """
    Allows callers to manually correct a misclassified field.
    The correction is stored in the cache and added to the FAISS index
    so future requests benefit immediately.
    """
    cache = get_cache()
    store = get_store()

    # Remove stale cache entry if present
    cache.delete(req.field_name)

    # Store correction
    cache.set(req.field_name, req.correct_category, req.correct_generator, source="feedback")

    # Update FAISS
    store.add_entry(req.field_name, req.correct_category, req.correct_generator, save_after=True)

    logger.info(
        f"Feedback applied: '{req.field_name}' → '{req.correct_category}' "
        f"(generator={req.correct_generator})"
    )

    return FeedbackResponse(
        message=f"Correction applied for '{req.field_name}'.",
        field_name=req.field_name,
        category=req.correct_category,
        generator=req.correct_generator,
    )


# ══════════════════════════════════════════════
# POST /rebuild
# ══════════════════════════════════════════════

@router.post(
    "/rebuild",
    summary="Rebuild FAISS index",
    tags=["System"],
)
async def rebuild() -> dict:
    """
    Force-rebuilds the FAISS index from field_mapping.json.
    Useful after manually editing the knowledge base file.
    """
    store = get_store()
    store.build_from_knowledge_base()
    store.save()
    return {"message": f"FAISS index rebuilt. Total vectors: {store.size}"}


# ══════════════════════════════════════════════
# POST /generate/from-json
# ══════════════════════════════════════════════

@router.post(
    "/generate/from-json",
    response_model=TemplateGenerateResponse,
    summary="Generate test data from SampleInput.json structure",
    description=(
        "Accepts a raw SampleInput.json payload (TestSuites, SeleniumExecutionFlow, Fields). "
        "Step 1: Deterministic parser extracts structure (zero AI). "
        "Step 2: AI pipeline classifies each field via FAISS → learns new mappings. "
        "Step 3: Business rule engine + Faker generates realistic values. "
        "Step 4: Returns populated JSON in SampleOutput.json format."
    ),
    tags=["Data Generation"],
)
async def generate_from_json(
    request_body: Dict[str, Any],
    module: str = Query(
        default="Generic",
        description="Business module hint for AI classification (e.g. 'Appointment')"
    ),
    locale: str = Query(
        default=DEFAULT_LOCALE,
        description="Faker locale override (default: en_IN)"
    ),
    seed: int = Query(
        default=None,
        description="Optional random seed for reproducible output"
    ),
) -> TemplateGenerateResponse:
    """
    Full pipeline endpoint: SampleInput.json → deterministic parse → AI classify → generate → output.

    Workflow:
      Client sends SampleInput.json
        ↓
      Excel/JSON Parser (openpyxl/json) — deterministic extraction
        ↓
      Normalize Structure (TestSuites, Objects, Iterations, Fields)
        ↓
      AI Pipeline (Embedding → FAISS → learn)
        ↓
      Business Rule Engine + Faker
        ↓
      Populate JSON Template
        ↓
      Return populated JSON
    """
    logger.info(
        f"POST /generate/from-json | module={module} | locale={locale}"
    )

    # ── Step 1: Deterministic extraction (zero AI) ───────────────────
    try:
        normalized = parse_json_input(request_body)
    except Exception as exc:
        logger.error(f"JSON parsing failed: {exc}")
        raise HTTPException(
            status_code=422,
            detail=f"Failed to parse input JSON structure: {exc}"
        )

    if not normalized.get("test_suites"):
        raise HTTPException(
            status_code=422,
            detail="No TestSuites found in the provided JSON."
        )

    # ── Step 2–5: AI pipeline → generate → populate ────────────────
    try:
        result = run_pipeline(
            normalized=normalized,
            module=module,
            locale=locale,
            seed=seed,
        )
    except Exception as exc:
        logger.error(f"Pipeline error: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline error: {exc}"
        )

    # Build typed metadata for the response
    metadata = {
        name: FieldClassificationMeta(**meta)
        for name, meta in result["metadata"].items()
    }

    logger.info(
        f"POST /generate/from-json complete | "
        f"package='{result['output'].get('TestPackageName')}' | "
        f"warnings={len(result['warnings'])}"
    )

    return TemplateGenerateResponse(
        output=result["output"],
        metadata=metadata,
        warnings=result["warnings"],
    )


# ══════════════════════════════════════════════
# POST /generate/from-excel
# ══════════════════════════════════════════════

@router.post(
    "/generate/from-excel",
    response_model=TemplateGenerateResponse,
    summary="Generate test data from Excel TDM file",
    description=(
        "Upload a .xlsx TDM Excel file. "
        "Deterministically extracts test structure (sheets → suites, rows → fields). "
        "AI pipeline then classifies fields and generates realistic test data."
    ),
    tags=["Data Generation"],
)
async def generate_from_excel(
    file: UploadFile = File(..., description=".xlsx TDM Excel file to parse"),
    module: str = Query(
        default="Generic",
        description="Business module hint for AI classification (e.g. 'Appointment')"
    ),
    locale: str = Query(
        default=DEFAULT_LOCALE,
        description="Faker locale override (default: en_IN)"
    ),
    seed: int = Query(
        default=None,
        description="Optional random seed for reproducible output"
    ),
) -> TemplateGenerateResponse:
    """
    Upload Excel → deterministic parse → AI classify → generate → output.
    """
    import tempfile, os

    logger.info(
        f"POST /generate/from-excel | file={file.filename} | module={module}"
    )

    if not file.filename.endswith((".xlsx", ".xlsm")):
        raise HTTPException(
            status_code=422,
            detail="Only .xlsx / .xlsm Excel files are supported."
        )

    # Save upload to a temp file (openpyxl requires a file path)
    try:
        content = await file.read()
        with tempfile.NamedTemporaryFile(
            suffix=".xlsx", delete=False
        ) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read uploaded file: {exc}"
        )

    try:
        # ── Step 1: Deterministic Excel extraction (zero AI) ──────
        normalized = parse_excel_input(tmp_path)
    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )
    except Exception as exc:
        logger.error(f"Excel parsing failed: {exc}")
        raise HTTPException(
            status_code=422,
            detail=f"Failed to parse Excel file: {exc}"
        )
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    if not normalized.get("test_suites"):
        raise HTTPException(
            status_code=422,
            detail="No test suites / sheets with field data found in the Excel file."
        )

    # ── Step 2–5: AI pipeline → generate → populate ───────────
    try:
        result = run_pipeline(
            normalized=normalized,
            module=module,
            locale=locale,
            seed=seed,
        )
    except Exception as exc:
        logger.error(f"Pipeline error: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline error: {exc}"
        )

    metadata = {
        name: FieldClassificationMeta(**meta)
        for name, meta in result["metadata"].items()
    }

    logger.info(
        f"POST /generate/from-excel complete | "
        f"package='{result['output'].get('TestPackageName')}' | "
        f"warnings={len(result['warnings'])}"
    )

    return TemplateGenerateResponse(
        output=result["output"],
        metadata=metadata,
        warnings=result["warnings"],
    )
