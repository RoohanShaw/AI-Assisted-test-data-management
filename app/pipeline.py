"""
pipeline.py — End-to-end orchestrator.

Pipeline (updated to use type-based routing):

  1. Receive normalized template (from excel_parser + template_builder)
  2. Collect all unique field names + their declared Type metadata
  3. For each field, route by Type:
       a. IsNavigation == True  → skip (omit from output)
       b. Type == Button (24)   → skip (omit from output)
       c. Type has deterministic generator → use it directly
       d. Type == String (6) / Text (2) / unknown → FAISS AI pipeline
  4. Apply Business Rules via rule_engine  (already in FieldClassification.rules)
  5. Run DataGenerator.generate() per field per iteration
  6. Populate the empty template with generated values
  7. Strip internal keys (_FieldMetadata) from output
  8. Return populated JSON + metadata about each field's classification

This module is the bridge between:
  - Deterministic layer (excel_parser + template_builder) — no AI
  - Type-routing layer (field_type_router) — deterministic, no AI
  - Classification layer (semantic_classifier) — local FAISS model only
  - Generation layer (generator + rule_engine) — Faker + custom generators
"""

import logging
from typing import Any, Dict, List, Optional

from app.config import DEFAULT_LOCALE
from app.field_type_router import route_by_type, should_skip, should_empty, SKIP_GENERATOR
from app.generator import DataGenerator
from app.models import FieldDefinition, FieldClassification
from app.semantic_classifier import classify_fields
from app.template_builder import (
    build_template,
    collect_all_field_names,
    collect_field_metadata,
    strip_internal_keys,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Main pipeline entry point
# ──────────────────────────────────────────────

def run_pipeline(
    normalized: Dict[str, Any],
    module: str = "Generic",
    locale: str = DEFAULT_LOCALE,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Full end-to-end pipeline: normalized structure → populated JSON.

    Args:
        normalized: Output of excel_parser.parse_json_input() / parse_excel_input()
        module:     Business module hint for AI classification (e.g. "Appointment")
        locale:     Faker locale for generation (default: en_IN)
        seed:       Optional random seed for reproducible output

    Returns:
        Dict with keys:
          - "output"    : populated JSON matching SampleOutput.json shape
          - "metadata"  : per-field classification details (source, category, confidence)
          - "warnings"  : list of non-fatal warning messages
    """
    warnings: List[str] = []

    # ── Step 1: Build the empty output template (deterministic) ───────────
    template = build_template(normalized)

    # ── Step 2: Collect field names + their Type metadata ─────────────────
    unique_field_names: List[str] = collect_all_field_names(template)
    field_metadata_map: Dict[str, Dict] = collect_field_metadata(template)

    logger.info(
        f"[pipeline] Collected {len(unique_field_names)} unique field(s) "
        f"from template. Type-routing before FAISS."
    )

    if not unique_field_names:
        logger.warning("[pipeline] No fields found in template. Returning empty template.")
        return {
            "output": strip_internal_keys(template),
            "metadata": {},
            "warnings": ["No data fields found in the input template."],
        }

    # ── Step 3: Type-based routing + AI classification ─────────────────────
    clf_map: Dict[str, FieldClassification] = {}
    ai_fields: List[FieldDefinition] = []          # fields needing FAISS

    skipped_fields: List[str] = []

    for field_name in unique_field_names:
        meta = field_metadata_map.get(field_name, {})
        field_type_int: int = meta.get("type", 0)
        is_nav: bool = meta.get("is_navigation", False)

        # Try deterministic routing first
        clf = route_by_type(
            field_type=field_type_int,
            is_navigation=is_nav,
            field_name=field_name,
        )

        if clf is not None:
            if should_skip(clf):
                # Navigation / Button — omit from output entirely
                skipped_fields.append(field_name)
                logger.info(
                    f"[pipeline] '{field_name}' Type={field_type_int} "
                    f"IsNav={is_nav} → SKIPPED"
                )
            else:
                clf_map[field_name] = clf
                logger.info(
                    f"[pipeline] '{field_name}' Type={field_type_int} "
                    f"→ deterministic: {clf.generator}"
                )
        else:
            # Needs FAISS / heuristic (String or unknown type)
            ai_fields.append(
                FieldDefinition(field_name=field_name, field_type="Auto")
            )
            logger.info(
                f"[pipeline] '{field_name}' Type={field_type_int} → AI pipeline"
            )

    # ── Step 4: AI classification (FAISS) for String/unknown fields ────────
    if ai_fields:
        logger.info(
            f"[pipeline] Sending {len(ai_fields)} field(s) to FAISS AI pipeline."
        )
        ai_classifications: List[FieldClassification] = classify_fields(
            ai_fields, module=module
        )
        for clf in ai_classifications:
            clf_map[clf.field_name] = clf
            if clf.source == "fallback":
                warnings.append(
                    f"Field '{clf.field_name}' could not be confidently classified "
                    f"(score={clf.confidence:.2f}). Used heuristic fallback → '{clf.category}'."
                )

    logger.info(
        f"[pipeline] Classification complete. "
        f"Deterministic: {len(clf_map) - len(ai_fields)}, "
        f"AI: {len(ai_fields)}, "
        f"Skipped: {len(skipped_fields)}"
    )

    # ── Step 5: Generate values & populate the template ─────────────────
    gen = DataGenerator(locale=locale, seed=seed)
    populated = _populate_template(
        template, clf_map, skipped_fields, gen, warnings
    )

    # ── Step 6: Strip internal keys before returning ─────────────────────
    populated = strip_internal_keys(populated)

    # ── Step 7: Build metadata summary ───────────────────────────────────
    all_classifications = list(clf_map.values())
    metadata: Dict[str, Any] = {
        clf.field_name: {
            "category":   clf.category,
            "generator":  clf.generator,
            "confidence": round(clf.confidence, 4),
            "source":     clf.source,
        }
        for clf in all_classifications
        if clf.generator != SKIP_GENERATOR
    }
    # Add skipped-field entries to metadata (for transparency)
    for fname in skipped_fields:
        metadata[fname] = {
            "category":   "Skip",
            "generator":  SKIP_GENERATOR,
            "confidence": 1.0,
            "source":     "type_router",
        }

    logger.info(
        f"[pipeline] Pipeline complete. "
        f"Package='{populated.get('TestPackageName')}', "
        f"suites={list(populated.get('TestSuites', {}).keys())}, "
        f"warnings={len(warnings)}"
    )

    return {
        "output": populated,
        "metadata": metadata,
        "warnings": warnings,
    }


# ──────────────────────────────────────────────
# Template population
# ──────────────────────────────────────────────

def _populate_template(
    template: Dict[str, Any],
    clf_map: Dict[str, FieldClassification],
    skipped_fields: List[str],
    gen: DataGenerator,
    warnings: List[str],
) -> Dict[str, Any]:
    """
    Walk the empty template and fill in each field value using the
    generator selected by type routing or AI classification.

    - Navigation/Button fields are removed from the iteration output entirely.
    - Each iteration gets independently generated values (not copies).
    - Login.Values remain "" — they are environment-specific credentials.
    """
    import copy
    populated = copy.deepcopy(template)

    skipped_set = set(skipped_fields)

    for suite_name, suite_data in populated.get("TestSuites", {}).items():
        for obj_name, obj_data in suite_data.get("Objects", {}).items():
            iterations = obj_data.get("Iterations", {})

            for iter_key, iter_data in iterations.items():
                fields = iter_data.get("Fields", {})

                for field_name in list(fields.keys()):
                    # Remove skipped (navigation / button) fields from output
                    if field_name in skipped_set:
                        del fields[field_name]
                        continue

                    clf = clf_map.get(field_name)
                    if clf is None:
                        # No classification found — leave blank with warning
                        fields[field_name] = ""
                        warnings.append(
                            f"No classification found for field '{field_name}' "
                            f"in {suite_name}/{obj_name}/iteration {iter_key}. Left blank."
                        )
                        continue

                    if should_empty(clf):
                        fields[field_name] = ""
                        continue

                    try:
                        value = gen.generate(clf.generator, clf.rules)
                        fields[field_name] = value
                    except Exception as exc:
                        logger.error(
                            f"[pipeline] Generator error for '{field_name}' "
                            f"(generator={clf.generator}): {exc}"
                        )
                        fields[field_name] = ""
                        warnings.append(
                            f"Generator failed for '{field_name}' "
                            f"(generator={clf.generator}): {exc}"
                        )

    return populated


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _count_sources(classifications: List[FieldClassification]) -> Dict[str, int]:
    """Count how many fields were classified by each source."""
    counts: Dict[str, int] = {}
    for clf in classifications:
        counts[clf.source] = counts.get(clf.source, 0) + 1
    return counts
