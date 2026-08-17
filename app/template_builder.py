"""
template_builder.py — Builds the empty output template (skeleton).

Takes the normalized internal structure from excel_parser and produces
the exact JSON skeleton matching SampleOutput.json — all field values
are "" (empty string) at this stage.

Still ZERO AI — pure deterministic template construction.
AI fills in the values in pipeline.py.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Standard login fields (always blank — env-specific credentials)
# ──────────────────────────────────────────────
LOGIN_VALUE_KEYS: List[str] = [
    "url",
    "userid",
    "password",
    "mobile no",
    "branch name",
    "dashboard url",
]


def build_template(normalized: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert the normalized internal JSON into an empty output skeleton.

    Args:
        normalized: Output of excel_parser.parse_json_input() or parse_excel_input()

    Returns:
        Output skeleton matching SampleOutput.json shape:
        {
          "TestPackageName": str,
          "TestSuites": {
            "TS_01": {
              "Objects": {
                "Object Name": {
                  "Login": { "Values": { "url": "", ... } },
                  "Iterations": {
                    "1": { "Fields": { "field_name": "" } },
                    "2": { "Fields": { "field_name": "" } },
                    ...
                  },
                  "Lookups": {},
                  "_FieldMetadata": {   # internal — stripped before final output
                    "field_name": { "type": 6, "is_navigation": False, ... }
                  }
                }
              }
            }
          }
        }
    """
    package_name: str = normalized.get("test_package_name", "UnknownPackage")
    suites_raw: Dict[str, Any] = normalized.get("test_suites", {})

    template: Dict[str, Any] = {
        "TestPackageName": package_name,
        "TestSuites": {},
    }

    for suite_name, suite_data in suites_raw.items():
        objects_raw: Dict[str, Any] = suite_data.get("objects", {})
        suite_node: Dict[str, Any] = {"Objects": {}}

        for obj_name, obj_data in objects_raw.items():
            iteration_count: int = obj_data.get("iteration_count", 1)
            field_names: List[str] = obj_data.get("fields", [])
            lookup_fields: List[str] = obj_data.get("lookup_fields", [])
            field_metadata: Dict[str, Any] = obj_data.get("field_metadata", {})

            obj_node: Dict[str, Any] = {
                "Login": _build_login_block(),
                "Iterations": _build_iterations_block(field_names, iteration_count),
                "Lookups": _build_lookups_block(lookup_fields),
                "_FieldMetadata": field_metadata,  # consumed by pipeline, stripped from output
            }

            suite_node["Objects"][obj_name] = obj_node

        template["TestSuites"][suite_name] = suite_node

    logger.info(
        f"[template_builder] Built template: package='{package_name}', "
        f"suites={list(template['TestSuites'].keys())}"
    )
    return template


def _build_login_block() -> Dict[str, Any]:
    """
    Build the Login block with all standard credential keys set to "".
    These are environment-specific values; AI does NOT fill them.
    """
    return {
        "Values": {key: "" for key in LOGIN_VALUE_KEYS}
    }


def _build_iterations_block(
    field_names: List[str],
    iteration_count: int,
) -> Dict[str, Any]:
    """
    Build the Iterations block — one entry per iteration, each with
    the same set of field names all set to "".
    """
    iterations: Dict[str, Any] = {}
    for i in range(1, iteration_count + 1):
        iterations[str(i)] = {
            "Fields": {name: "" for name in field_names}
        }
    return iterations


def _build_lookups_block(lookup_fields: List[str]) -> Dict[str, Any]:
    """
    Build the Lookups block. Currently returns {} (empty) for all objects
    unless lookup fields were identified in parsing.
    Each lookup field gets an empty dict as placeholder.
    """
    if not lookup_fields:
        return {}
    return {name: {} for name in lookup_fields}


# ──────────────────────────────────────────────
# Utility: flatten all field names from template
# (used by pipeline.py to collect unique fields for AI classification)
# ──────────────────────────────────────────────

def collect_all_field_names(template: Dict[str, Any]) -> List[str]:
    """
    Walk the output template and collect every unique field name
    across all suites, objects, and iterations.

    Used by pipeline.py to batch all fields for AI classification in one call.
    """
    seen = set()
    result = []

    for suite_data in template.get("TestSuites", {}).values():
        for obj_data in suite_data.get("Objects", {}).values():
            for iter_data in obj_data.get("Iterations", {}).values():
                for field_name in iter_data.get("Fields", {}).keys():
                    if field_name not in seen:
                        seen.add(field_name)
                        result.append(field_name)

    return result


def collect_field_metadata(template: Dict[str, Any]) -> Dict[str, Dict]:
    """
    Flatten the _FieldMetadata dicts from all objects in the template
    into a single dict: field_name → {type, is_navigation, is_lookup, is_mandatory}.

    Used by pipeline.py to route fields by type before AI classification.
    First occurrence wins (same field may appear in multiple objects).
    """
    merged: Dict[str, Dict] = {}
    for suite_data in template.get("TestSuites", {}).values():
        for obj_data in suite_data.get("Objects", {}).values():
            for field_name, meta in obj_data.get("_FieldMetadata", {}).items():
                if field_name not in merged:
                    merged[field_name] = meta
    return merged


def strip_internal_keys(template: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove internal pipeline keys (prefixed with '_') from the template
    before returning to the caller. Returns a cleaned copy.
    """
    import copy
    cleaned = copy.deepcopy(template)
    for suite_data in cleaned.get("TestSuites", {}).values():
        for obj_data in suite_data.get("Objects", {}).values():
            obj_data.pop("_FieldMetadata", None)
    return cleaned
