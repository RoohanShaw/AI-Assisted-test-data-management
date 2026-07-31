"""
openai_client.py — Calls OpenAI to classify unknown fields.

Uses the Chat Completions API with a structured prompt that forces a
JSON response. Result is parsed and returned as a plain dict.
"""

import json
import logging
from typing import Optional

from openai import OpenAI, OpenAIError

from app.config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_MAX_TOKENS,
    OPENAI_TEMPERATURE,
)

logger = logging.getLogger(__name__)

# Lazy singleton
_client: OpenAI | None = None


def _get_client() -> Optional[OpenAI]:
    global _client
    if _client is None:
        if not OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not set — OpenAI fallback disabled.")
            return None
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


# ──────────────────────────────────────────────
# Prompt template
# ──────────────────────────────────────────────

SYSTEM_PROMPT = """You are a data classification expert. 
Your task is to identify the semantic meaning of a database field and assign:
1. A human-readable category name (e.g. "Medical Record Number", "Employee Salary")
2. A generator key — one of the following ONLY:
   full_name, first_name, last_name, middle_name, age, dob, gender, email, phone,
   salary, monthly_salary, net_salary, address, city, state, country, pin_code,
   employee_id, patient_id, mrn, aadhar, pan, department, job_title, joining_date,
   start_date, end_date, generic_date, blood_group, bank_account, ifsc_code,
   credit_card, ip_address, mac_address, url, company, username, password,
   experience, nationality, religion, marital_status, education, diagnosis,
   prescription, medication, height, weight, transaction_id, order_id,
   invoice_number, amount, gst_number, remarks, description, status, boolean, uuid

Respond ONLY with a valid JSON object in this exact format:
{"category": "...", "generator": "..."}

Do NOT add any explanation or extra text."""

USER_PROMPT_TEMPLATE = """Module: {module}
Field Name: {field_name}
Field Type: {field_type}

What is the semantic meaning of this field?"""


def classify_field(
    field_name: str,
    field_type: str = "String",
    module: str = "Generic",
) -> Optional[dict]:
    """
    Ask OpenAI to classify an unknown field.

    Returns dict with keys: category, generator
    Returns None if OpenAI is unavailable or returns invalid JSON.
    """
    client = _get_client()
    if client is None:
        return None

    prompt = USER_PROMPT_TEMPLATE.format(
        module=module,
        field_name=field_name,
        field_type=field_type,
    )

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            max_tokens=OPENAI_MAX_TOKENS,
            temperature=OPENAI_TEMPERATURE,
            response_format={"type": "json_object"},   # force JSON mode
        )

        raw = response.choices[0].message.content.strip()
        result = json.loads(raw)

        # Validate required keys
        if "category" not in result or "generator" not in result:
            logger.error(f"OpenAI returned incomplete JSON for '{field_name}': {raw}")
            return None

        logger.info(
            f"OpenAI classified '{field_name}' → {result['category']} "
            f"(generator={result['generator']})"
        )
        return result

    except json.JSONDecodeError as exc:
        logger.error(f"OpenAI returned non-JSON for '{field_name}': {exc}")
        return None
    except OpenAIError as exc:
        logger.error(f"OpenAI API error for '{field_name}': {exc}")
        return None
    except Exception as exc:
        logger.error(f"Unexpected error calling OpenAI for '{field_name}': {exc}")
        return None


def is_available() -> bool:
    """Return True if OpenAI is configured and the client can be created."""
    return bool(OPENAI_API_KEY)
