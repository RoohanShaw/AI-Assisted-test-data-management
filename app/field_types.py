"""
field_types.py — Centralized, zero-based FieldTypes enum mapping.

This is the SINGLE source of truth for the company FieldTypes enum.
All other modules that need to look up a type integer → type name
should import from here.

The enum is ZERO-BASED (matches the C# FieldTypes enum exactly):

    0  = None
    1  = Undefined
    2  = Text
    3  = Number
    4  = Date
    5  = Hierarchy
    6  = String
    7  = Integer
    8  = BigInt
    9  = DateTime
    10 = Reference
    11 = Picklist
    12 = Virtual
    13 = Customer
    14 = State
    15 = Dropdown
    16 = Lookup
    17 = EntityName
    18 = Uniqueidentifier
    19 = Memo
    20 = Boolean
    21 = Double
    22 = Status
    23 = Decimal
    24 = Button
    25 = Meta

IMPORTANT:
  - The enum starts from ZERO. Do NOT shift values.
  - Type 6  = String   (NOT the 7th value in a 1-based list)
  - Type 9  = DateTime
  - Type 11 = Picklist
  - Type 15 = Dropdown
  - Type 20 = Boolean
  - Type 24 = Button
"""

from typing import Dict

# ──────────────────────────────────────────────
# Canonical zero-based FieldTypes mapping
# ──────────────────────────────────────────────

FIELD_TYPE_MAP: Dict[int, str] = {
    0:  "None",
    1:  "Undefined",
    2:  "Text",
    3:  "Number",
    4:  "Date",
    5:  "Hierarchy",
    6:  "String",
    7:  "Integer",
    8:  "BigInt",
    9:  "DateTime",
    10: "Reference",
    11: "Picklist",
    12: "Virtual",
    13: "Customer",
    14: "State",
    15: "Dropdown",
    16: "Lookup",
    17: "EntityName",
    18: "Uniqueidentifier",
    19: "Memo",
    20: "Boolean",
    21: "Double",
    22: "Status",
    23: "Decimal",
    24: "Button",
    25: "Meta",
}


def get_type_name(type_int: int) -> str:
    """
    Return the human-readable type name for a given integer type value.

    Args:
        type_int: The integer field type from the JSON input (zero-based).

    Returns:
        The type name string (e.g. "String", "Picklist", "Button").
        Returns "Unknown" if the integer is not in the map.

    Examples:
        >>> get_type_name(6)
        'String'
        >>> get_type_name(24)
        'Button'
        >>> get_type_name(11)
        'Picklist'
    """
    return FIELD_TYPE_MAP.get(type_int, "Unknown")


def is_skip_type(type_int: int, is_navigation: bool = False) -> bool:
    """
    Return True if the field should be completely skipped (no output value).

    Skip conditions (highest priority, checked before generation):
      - IsNavigation == True (Selenium click-action, no data value)
      - Type == 24 (Button — UI action element)

    Args:
        type_int:      The integer field type.
        is_navigation: Whether the field has IsNavigation=true in the input.

    Returns:
        True if the field must be omitted from generated output.
    """
    if is_navigation:
        return True
    return type_int == 24  # Button


def is_empty_type(type_int: int) -> bool:
    """
    Return True if the field should be included in output with an empty value.

    Empty conditions:
      - Type == 11 (Picklist)  — do NOT generate synthetic values
      - Type == 15 (Dropdown)  — do NOT generate synthetic values

    Args:
        type_int: The integer field type.

    Returns:
        True if the field must appear in output as an empty string "".
    """
    return type_int in (11, 15)  # Picklist, Dropdown


# ──────────────────────────────────────────────
# Re-export the FieldType IntEnum from field_type_router
# so callers only need to import from one place.
# ──────────────────────────────────────────────

def _lazy_field_type_enum():
    """Lazy import to avoid circular dependency."""
    from app.field_type_router import FieldType
    return FieldType


# Convenience: expose FieldType at module level
# Usage:  from app.field_types import FieldType
try:
    from app.field_type_router import FieldType  # noqa: F401
except ImportError:
    pass  # will not happen in normal runtime; only during isolated unit tests
