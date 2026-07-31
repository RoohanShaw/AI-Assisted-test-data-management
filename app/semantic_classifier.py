"""
semantic_classifier.py — Orchestrates field classification.

Pipeline per field (local-only, no external API):
  1. Check persistent cache (learned_fields.json)
  2. Check FAISS similarity search → if score >= threshold, accept
  3. Heuristic rule-based fallback (token matching)
"""

import logging
from typing import List

from app.cache import get_cache
from app.config import SIMILARITY_THRESHOLD
from app.faiss_store import get_store
from app.models import FieldClassification, FieldDefinition
from app.rule_engine import get_rules

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Heuristic fallback (when neither cache nor FAISS can help)
# Maps partial field-name tokens → (category, generator)
# ──────────────────────────────────────────────
HEURISTIC_RULES = [
    (["name"],                 "Full Name",              "full_name"),
    (["age"],                  "Human Age",              "age"),
    (["email"],                "Email Address",          "email"),
    (["phone", "mobile", "cell", "contact"], "Phone Number", "phone"),
    (["salary", "ctc", "income"], "Employee Salary",     "salary"),
    (["address", "addr"],      "Street Address",         "address"),
    (["city", "town"],         "City",                   "city"),
    (["state", "province"],    "State",                  "state"),
    (["country", "nation"],    "Country",                "country"),
    (["zip", "pin", "postal"], "Postal Code",            "pin_code"),
    (["dob", "birth", "birthday"], "Date of Birth",      "dob"),
    (["gender", "sex"],        "Gender",                 "gender"),
    (["date", "period"],       "Generic Date",           "generic_date"),
    (["id", "uid", "uuid"],    "Unique Identifier",      "uuid"),
    (["reg id", "registration id", "reg. no", "regnum", "reg_id"], "Registration ID", "reg_id"),
    (["reg", "registration"],  "Patient ID",             "patient_id"),
    (["token number", "token no", "tokenno", "tokennumber"], "Token Number", "token_number"),
    (["token"],                "Token Number",           "token_number"),
    (["department", "dept"],   "Department",             "department"),
    (["doctor", "physician", "docselect"], "Full Name",  "full_name"),
    (["designation", "title", "position", "role"], "Job Title", "job_title"),
    (["salary", "pay", "wage"], "Employee Salary",       "salary"),
    (["account", "acc"],       "Bank Account Number",    "bank_account"),
    (["pan"],                  "PAN Number",             "pan"),
    (["aadhar", "aadhaar"],    "Aadhar Number",          "aadhar"),
    (["mrn", "medical record"], "Medical Record Number", "mrn"),
    (["diagnosis", "disease"], "Medical Diagnosis",      "diagnosis"),
    (["company", "org"],       "Company Name",           "company"),
    (["status"],               "Status",                 "status"),
    (["type", "visit", "patient type"], "Status",        "status"),
    (["priority"],             "Status",                 "status"),
    (["bool", "flag", "active", "enabled"], "Boolean Flag", "boolean"),
    (["amount", "price", "cost", "total"], "Transaction Amount", "amount"),
    (["password", "pwd"],      "Password",               "password"),
    (["username", "login"],    "Username",               "username"),
    (["url", "website", "link"], "Website URL",          "url"),
    (["ip"],                   "IP Address",             "ip_address"),
    (["blood"],                "Blood Group",            "blood_group"),
    (["height"],               "Height",                 "height"),
    (["weight"],               "Weight",                 "weight"),
    (["experience", "exp"],    "Work Experience",        "experience"),
    (["education", "degree", "qualification"], "Education", "education"),
    (["description", "desc"],  "Description",            "description"),
    (["remarks", "notes", "comments"], "Comment",        "remarks"),
    (["reason", "select reason"], "Status",              "status"),
    (["search"],               "Generic Text",           "description"),
    (["download", "print"],    "Generic Text",           "description"),
]


def _heuristic_classify(field_name: str) -> tuple[str, str]:
    """
    Token-matching fallback used when cache and FAISS cannot classify.
    Returns (category, generator).
    """
    normalized = field_name.lower().replace("_", " ").replace("-", " ").replace("/", " ")
    tokens = normalized.split()

    for keywords, category, generator in HEURISTIC_RULES:
        for kw in keywords:
            for token in tokens:
                if kw in token:
                    return category, generator

    return "Generic Text", "description"


# ──────────────────────────────────────────────
# Main Classifier
# ──────────────────────────────────────────────

def classify_fields(
    fields: List[FieldDefinition],
    module: str = "Generic",
) -> List[FieldClassification]:
    """
    Classify a list of field definitions using local-only pipeline:
      Cache → FAISS → Heuristic fallback
    """
    cache = get_cache()
    store = get_store()
    results: List[FieldClassification] = []

    for field in fields:
        classification = _classify_single(field, module, cache, store)
        results.append(classification)

    return results


def _classify_single(
    field: FieldDefinition,
    module: str,
    cache,
    store,
) -> FieldClassification:
    """Classify a single field using the 3-step local pipeline."""

    name = field.field_name
    ftype = field.field_type

    # ── Override: Force Reg ID and Token Number to numeric generators ────
    name_lower = name.lower()
    name_clean = name_lower.replace(" ", "").replace("_", "").replace("-", "").replace(".", "")
    if name_clean in ("regid", "regnum", "regno", "registrationid"):
        logger.info(f"[{name}] Overriding to reg_id generator")
        return FieldClassification(
            field_name=name,
            field_type=ftype,
            category="Registration ID",
            generator="reg_id",
            confidence=1.0,
            source="override",
            rules=get_rules("reg_id"),
        )
    if name_clean in ("tokennumber", "tokenno", "token"):
        logger.info(f"[{name}] Overriding to token_number generator")
        return FieldClassification(
            field_name=name,
            field_type=ftype,
            category="Token Number",
            generator="token_number",
            confidence=1.0,
            source="override",
            rules=get_rules("token_number"),
        )

    # ── Step 0: Category override ──────────────────────────────────────
    if field.category_override:
        gen = "description"
        from app.rule_engine import list_generators
        for g in list_generators():
            if g.replace("_", " ") in field.category_override.lower():
                gen = g
                break
        logger.info(f"[{name}] Override → {field.category_override}")
        return FieldClassification(
            field_name=name,
            field_type=ftype,
            category=field.category_override,
            generator=gen,
            confidence=1.0,
            source="override",
            rules=get_rules(gen),
        )

    # ── Step 1: Persistent cache ────────────────────────────────────────
    cached = cache.get(name)
    if cached:
        cat = cached["category"]
        gen = cached["generator"]
        logger.info(f"[{name}] Cache hit → {cat}")
        return FieldClassification(
            field_name=name,
            field_type=ftype,
            category=cat,
            generator=gen,
            confidence=0.99,
            source="cache",
            rules=get_rules(gen),
        )

    # ── Step 2: FAISS similarity search ────────────────────────────────
    best_meta, score = store.best_match(name)
    if best_meta and score >= SIMILARITY_THRESHOLD:
        cat = best_meta["category"]
        gen = best_meta["generator"]
        # Learn this result so next identical query hits the cache
        cache.set(name, cat, gen, source="faiss")
        logger.info(f"[{name}] FAISS hit (score={score:.3f}) → {cat}")
        return FieldClassification(
            field_name=name,
            field_type=ftype,
            category=cat,
            generator=gen,
            confidence=round(float(score), 4),
            source="faiss",
            rules=get_rules(gen),
        )

    logger.info(
        f"[{name}] FAISS score={score:.3f} < threshold={SIMILARITY_THRESHOLD} "
        f"→ using heuristic fallback"
    )

    # ── Step 3: Heuristic fallback ──────────────────────────────────────
    cat, gen = _heuristic_classify(name)
    # Cache the heuristic result so repeated calls are faster
    cache.set(name, cat, gen, source="fallback")
    logger.warning(f"[{name}] Heuristic fallback → {cat} (generator={gen})")
    return FieldClassification(
        field_name=name,
        field_type=ftype,
        category=cat,
        generator=gen,
        confidence=round(float(score), 4) if best_meta else 0.0,
        source="fallback",
        rules=get_rules(gen),
    )
