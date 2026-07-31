"""
rule_engine.py — Maps semantic categories to business generation rules.

Rules are applied by generator.py to produce realistic, constrained values.
"""

from typing import Any, Dict

# ──────────────────────────────────────────────
# Rule Definitions
# Each entry: generator_key → dict of rule parameters
# ──────────────────────────────────────────────

RULES: Dict[str, Dict[str, Any]] = {

    # ── Names ──────────────────────────────────
    "full_name":       {"locale": "en_IN"},
    "first_name":      {"locale": "en_IN"},
    "last_name":       {"locale": "en_IN"},
    "middle_name":     {"locale": "en_IN"},

    # ── Demographics ───────────────────────────
    "age": {
        "min": 18,
        "max": 80,
        "description": "Adult human age in years"
    },
    "dob": {
        "min_age": 18,
        "max_age": 80,
        "format": "%Y-%m-%d",
        "description": "Date of birth (YYYY-MM-DD)"
    },
    "gender": {
        "values": ["Male", "Female", "Other"],
        "weights": [0.49, 0.49, 0.02]
    },
    "height": {
        "min_cm": 150,
        "max_cm": 195,
        "unit": "cm"
    },
    "weight": {
        "min_kg": 45,
        "max_kg": 110,
        "unit": "kg"
    },
    "blood_group": {
        "values": ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
        "weights": [0.27, 0.06, 0.22, 0.02, 0.05, 0.01, 0.38, 0.07]
    },
    "marital_status": {
        "values": ["Single", "Married", "Divorced", "Widowed"],
        "weights": [0.35, 0.55, 0.07, 0.03]
    },
    "nationality": {
        "values": ["Indian", "American", "British", "Canadian", "Australian",
                   "German", "French", "Japanese", "Chinese", "Brazilian"]
    },
    "religion": {
        "values": ["Hindu", "Muslim", "Christian", "Sikh", "Buddhist",
                   "Jain", "Other"]
    },

    # ── Contact ────────────────────────────────
    "email":  {"domain_pool": ["gmail.com", "yahoo.com", "outlook.com",
                                "hotmail.com", "company.com"]},
    "phone":  {"format": "91##########", "pattern": r"9[0-9]{9}"},
    "address": {"locale": "en_IN"},
    "city":   {"indian_cities": True},
    "state":  {"indian_states": True},
    "country": {"values": ["India"]},    # default India; override via locale
    "pin_code": {"pattern": r"[1-9][0-9]{5}"},
    "url":    {},
    "ip_address": {"version": 4},
    "mac_address": {},

    # ── Employment ─────────────────────────────
    "salary": {
        "min": 300000,
        "max": 3000000,
        "step": 10000,
        "currency": "INR",
        "description": "Annual CTC in INR"
    },
    "monthly_salary": {
        "min": 25000,
        "max": 250000,
        "step": 1000,
        "currency": "INR"
    },
    "net_salary": {
        "min": 20000,
        "max": 200000,
        "step": 1000,
        "currency": "INR"
    },
    "employee_id": {
        "prefix": "EMP",
        "digits": 5
    },
    "department": {
        "values": [
            "Engineering", "Sales", "Marketing", "Finance", "HR",
            "Operations", "IT", "Legal", "Admin", "R&D",
            "Customer Support", "Product", "Design", "Data Science"
        ]
    },
    "job_title": {
        "values": [
            "Software Engineer", "Senior Software Engineer", "Tech Lead",
            "Product Manager", "Business Analyst", "Data Scientist",
            "HR Manager", "Finance Executive", "Marketing Manager",
            "Operations Manager", "QA Engineer", "DevOps Engineer",
            "UI/UX Designer", "Project Manager", "Sales Executive",
            "Customer Support Executive", "Team Lead", "Architect"
        ]
    },
    "experience": {
        "min": 0,
        "max": 35,
        "unit": "years"
    },
    "education": {
        "values": [
            "B.Tech", "M.Tech", "B.Sc", "M.Sc", "MBA", "BBA",
            "B.Com", "M.Com", "B.E", "M.E", "MBBS", "MD",
            "PhD", "Diploma", "B.A", "M.A", "BCA", "MCA"
        ]
    },

    # ── Dates ──────────────────────────────────
    "joining_date": {
        "min_year": 2010,
        "max_year": 2025,
        "format": "%Y-%m-%d"
    },
    "start_date": {
        "min_year": 2020,
        "max_year": 2026,
        "format": "%Y-%m-%d"
    },
    "end_date": {
        "min_year": 2025,
        "max_year": 2027,
        "format": "%Y-%m-%d"
    },
    "generic_date": {
        "min_year": 2020,
        "max_year": 2026,
        "format": "%Y-%m-%d"
    },

    # ── Healthcare ─────────────────────────────
    "patient_id": {
        "prefix": "PAT",
        "digits": 6
    },
    "mrn": {
        "prefix": "MRN",
        "digits": 7,
        "description": "Medical Record Number"
    },
    "diagnosis": {
        "values": [
            "Hypertension", "Type 2 Diabetes", "Asthma", "Migraine",
            "Arthritis", "Hypothyroidism", "GERD", "Anxiety Disorder",
            "Iron Deficiency Anemia", "Chronic Back Pain", "Obesity",
            "Viral Fever", "Dengue", "Malaria", "COVID-19 (Recovered)"
        ]
    },
    "prescription": {
        "values": [
            "Metformin 500mg twice daily",
            "Amlodipine 5mg once daily",
            "Paracetamol 500mg as needed",
            "Omeprazole 20mg before meals",
            "Atorvastatin 10mg at bedtime",
            "Levothyroxine 50mcg in morning",
            "Salbutamol inhaler as needed",
            "Aspirin 75mg once daily"
        ]
    },
    "medication": {
        "values": [
            "Metformin", "Amlodipine", "Paracetamol", "Omeprazole",
            "Atorvastatin", "Levothyroxine", "Salbutamol", "Aspirin",
            "Ibuprofen", "Amoxicillin", "Cetirizine", "Pantoprazole"
        ]
    },

    # ── Identity Documents ──────────────────────
    "aadhar":   {"pattern": r"[2-9][0-9]{3} [0-9]{4} [0-9]{4}"},
    "pan":      {"pattern": r"[A-Z]{5}[0-9]{4}[A-Z]"},
    "gst_number": {"pattern": r"[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]"},

    # ── Finance ────────────────────────────────
    "bank_account": {"min_digits": 10, "max_digits": 16},
    "ifsc_code":    {"pattern": r"[A-Z]{4}0[A-Z0-9]{6}"},
    "credit_card":  {},
    "amount": {
        "min": 100,
        "max": 100000,
        "decimals": 2,
        "currency": "INR"
    },
    "transaction_id": {"prefix": "TXN", "digits": 10},
    "order_id":       {"prefix": "ORD", "digits": 8},
    "invoice_number": {"prefix": "INV", "digits": 6},

    # ── System / Misc ──────────────────────────
    "username":    {"min_length": 6, "max_length": 15},
    "password":    {"length": 12, "special_chars": True},
    "company":     {"locale": "en_IN"},
    "status": {
        "values": ["Active", "Inactive", "Pending", "Approved", "Rejected",
                   "On Hold", "Completed", "Processing"]
    },
    "boolean":  {"values": [True, False]},
    "uuid":     {},
    "remarks":  {"max_words": 10},
    "description": {"max_words": 20},

    # ── Deterministic type-router generators ───────────────────────────
    "integer": {
        "min": 1,
        "max": 999,
        "description": "Whole integer (Type=Number/Integer)"
    },
    "big_integer": {
        "min": 100_000,
        "max": 999_999_999,
        "description": "Large integer (Type=BigInt)"
    },
    "date_only": {
        "min_year": 1970,
        "max_year": 2025,
        "format": "%Y-%m-%d",
        "description": "Date only YYYY-MM-DD (Type=Date/DateTime)"
    },
    "datetime_value": {
        "min_year": 1970,
        "max_year": 2025,
        "format": "%Y-%m-%d",
        "description": "DateTime YYYY-MM-DD HH:MM (Type=DateTime)"
    },
    "reference_id": {
        "prefix": "REF",
        "digits": 5,
        "description": "Reference identifier REF-XXXXX (Type=reference)"
    },
    "picklist_value": {
        "values": [
            "Open", "Closed", "Pending", "Cancelled", "Active", "Inactive",
            "Approved", "Rejected", "On Hold", "Completed", "Processing",
            "Reviewed", "Submitted", "In Progress",
        ],
        "description": "Business picklist value (Type=Picklist/Dropdown)"
    },
    "lookup_value": {
        "entity": "",
        "description": "Lookup entity name (Type=Lookup)"
    },
    "reg_id": {
        "min": 100000,
        "max": 999999,
        "description": "Registration ID numeric only"
    },
    "token_number": {
        "min": 1,
        "max": 999,
        "description": "Token Number numeric only"
    },
}


def get_rules(generator: str) -> Dict[str, Any]:
    """Return business rules for the given generator key. Empty dict if unknown."""
    return RULES.get(generator, {})


def list_generators() -> list:
    """Return all known generator keys."""
    return list(RULES.keys())
