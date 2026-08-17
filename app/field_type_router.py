"""
field_type_router.py — Deterministic type-based routing layer.

Mirrors the C# FieldTypes enum (0-indexed):

    None=0, Undefined=1, Text=2, Number=3, Date=4, Hierarchy=5,
    String=6, Integer=7, BigInt=8, DateTime=9, Reference=10,
    Picklist=11, Virtual=12, Customer=13, State=14, Dropdown=15,
    Lookup=16, EntityName=17, Uniqueidentifier=18, Memo=19,
    Boolean=20, Double=21, Status=22, Decimal=23, Button=24, Meta=25

The canonical zero-based integer → name mapping lives in:
    app/field_types.py  (FIELD_TYPE_MAP)

Decision priority (checked in this order for every field):
  1. IsNavigation == True  →  skip
  2. Type == Button (24)   →  skip
  3. Name heuristics (Picklist/Dropdown keywords) → empty
  4. Type == Picklist (11) / Dropdown (15) → empty
  5. Type has deterministic generator  →  use it
  6. Type == String (6) / Text (2) / unknown  →  AI pipeline (return None)

Usage:
    from app.field_type_router import route_by_type

    result = route_by_type(field_type=24, is_navigation=True, field_name="Appointment")
    # result → FieldClassification(generator="__skip__", source="type_router")

    result = route_by_type(field_type=6, is_navigation=False, field_name="Patient Name")
    # result → None   (caller should use FAISS)
"""

import logging
from enum import IntEnum
from typing import Optional

from app.models import FieldClassification
from app.rule_engine import get_rules

# Import the canonical FIELD_TYPE_MAP so it is available via this module.
# The dict is the human-readable companion to the FieldType IntEnum below.
try:
    from app.field_types import FIELD_TYPE_MAP  # noqa: F401 — re-exported for consumers
except ImportError:
    FIELD_TYPE_MAP = {}

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# FieldTypes enum (mirrors C# enum, 0-indexed)
# ──────────────────────────────────────────────

class FieldType(IntEnum):
    NONE             = 0
    UNDEFINED        = 1
    TEXT             = 2   # treat like String → AI
    NUMBER           = 3
    DATE             = 4
    HIERARCHY        = 5
    STRING           = 6   # only type that uses AI
    INTEGER          = 7
    BIG_INT          = 8
    DATE_TIME        = 9
    REFERENCE        = 10
    PICKLIST         = 11
    VIRTUAL          = 12
    CUSTOMER         = 13
    STATE            = 14
    DROPDOWN         = 15
    LOOKUP           = 16
    ENTITY_NAME      = 17
    UNIQUE_IDENTIFIER= 18
    MEMO             = 19
    BOOLEAN          = 20
    DOUBLE           = 21
    STATUS           = 22
    DECIMAL          = 23
    BUTTON           = 24
    META             = 25


# ──────────────────────────────────────────────
# Sentinel generator key: "skip this field" or "empty this field"
# ──────────────────────────────────────────────
SKIP_GENERATOR = "__skip__"
EMPTY_GENERATOR = "__empty__"


# ──────────────────────────────────────────────
# Type → (category, generator) deterministic map
# ──────────────────────────────────────────────
_TYPE_GENERATOR_MAP: dict[int, tuple[str, str]] = {
    FieldType.NUMBER          : ("Integer Number",      "integer"),
    FieldType.DATE            : ("Date",                "date_only"),
    FieldType.INTEGER         : ("Integer Number",      "integer"),
    FieldType.BIG_INT         : ("Big Integer",         "big_integer"),
    FieldType.DATE_TIME       : ("DateTime",            "date_only"),
    FieldType.REFERENCE       : ("Reference ID",        "reference_id"),
    FieldType.STATE           : ("Status",              "status"),
    FieldType.LOOKUP          : ("Lookup Value",        "lookup_value"),
    FieldType.ENTITY_NAME     : ("Entity Name",         "full_name"),
    FieldType.UNIQUE_IDENTIFIER: ("UUID",              "uuid"),
    FieldType.MEMO            : ("Memo / Remarks",      "remarks"),
    FieldType.BOOLEAN         : ("Boolean",             "boolean"),
    FieldType.DOUBLE          : ("Decimal Amount",      "amount"),
    FieldType.STATUS          : ("Status",              "status"),
    FieldType.DECIMAL         : ("Decimal Amount",      "amount"),
    FieldType.CUSTOMER        : ("Customer Name",       "full_name"),
    FieldType.HIERARCHY       : ("Generic Text",        "description"),
    FieldType.VIRTUAL         : ("Generic Text",        "description"),
    FieldType.META            : ("Generic Text",        "description"),
}

# Types that must use the AI (FAISS) pipeline
_AI_TYPES: set[int] = {
    FieldType.STRING,
    FieldType.TEXT,
    FieldType.NONE,
    FieldType.UNDEFINED,
}

# Types that must be skipped entirely (no output value)
_SKIP_TYPES: set[int] = {
    FieldType.BUTTON,
}


# ──────────────────────────────────────────────
# Public router
# ──────────────────────────────────────────────

def route_by_type(
    field_type: int,
    is_navigation: bool,
    field_name: str,
) -> Optional[FieldClassification]:
    """
    Determine how to handle a field based on its declared integer Type.

    Returns:
        FieldClassification with generator="__skip__"  → field must be omitted from output
        FieldClassification with generator="__empty__" → field must be empty string
        FieldClassification with a real generator key  → use deterministic generator
        None                                           → send to FAISS AI pipeline
    """

    # ── Rule 1: Navigation fields — always skip ──────────────────────────
    if is_navigation:
        logger.debug(f"[type_router] '{field_name}' IsNavigation=True → skip")
        return _make_skip(field_name, field_type, reason="IsNavigation")

    # ── Rule 2: Button type — always skip ───────────────────────────────
    if field_type == FieldType.BUTTON:
        logger.debug(f"[type_router] '{field_name}' Type=Button(24) → skip")
        return _make_skip(field_name, field_type, reason="Button")

    # ── Rule 2.3: Name-based heuristics for Picklist / Dropdown ──────────
    name_lower = field_name.lower()
    if any(kw in name_lower for kw in ("select", "dropdown", "picklist", "list")):
        logger.debug(f"[type_router] '{field_name}' Name matches picklist/dropdown heuristics → empty")
        return _make_empty(field_name, field_type, reason="Name Heuristic (Picklist/Dropdown)")

    # ── Rule 2.5: Picklist & Dropdown types — always return empty ───────
    if field_type in (FieldType.PICKLIST, FieldType.DROPDOWN):
        logger.debug(f"[type_router] '{field_name}' Type={field_type} → empty")
        return _make_empty(field_name, field_type, reason="Picklist/Dropdown")

    # ── Rule 3: Types that need AI ───────────────────────────────────────
    if field_type in _AI_TYPES:
        logger.debug(
            f"[type_router] '{field_name}' Type={field_type} → AI pipeline"
        )
        return None  # caller will use FAISS

    # ── Rule 4: Deterministic type mapping ───────────────────────────────
    mapping = _TYPE_GENERATOR_MAP.get(field_type)
    if mapping:
        category, generator = mapping
        logger.debug(
            f"[type_router] '{field_name}' Type={field_type} → "
            f"deterministic: category='{category}', generator='{generator}'"
        )
        return _make_clf(field_name, field_type, category, generator)

    # ── Fallback: unknown type → AI pipeline ─────────────────────────────
    logger.debug(
        f"[type_router] '{field_name}' Type={field_type} unknown → AI pipeline"
    )
    return None


def should_skip(clf: FieldClassification) -> bool:
    """Return True if this classification means the field must be omitted."""
    return clf.generator == SKIP_GENERATOR


def should_empty(clf: FieldClassification) -> bool:
    """Return True if this classification means the field must be empty string."""
    return clf.generator == EMPTY_GENERATOR


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _make_skip(field_name: str, field_type: int, reason: str) -> FieldClassification:
    return FieldClassification(
        field_name=field_name,
        field_type=str(field_type),
        category="Skip",
        generator=SKIP_GENERATOR,
        confidence=1.0,
        source="type_router",
        rules={"reason": reason},
    )


def _make_empty(field_name: str, field_type: int, reason: str) -> FieldClassification:
    return FieldClassification(
        field_name=field_name,
        field_type=str(field_type),
        category="Empty",
        generator=EMPTY_GENERATOR,
        confidence=1.0,
        source="type_router",
        rules={"reason": reason},
    )


def _make_clf(
    field_name: str,
    field_type: int,
    category: str,
    generator: str,
) -> FieldClassification:
    return FieldClassification(
        field_name=field_name,
        field_type=str(field_type),
        category=category,
        generator=generator,
        confidence=1.0,
        source="type_router",
        rules=get_rules(generator),
    )
