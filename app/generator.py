"""
generator.py — Realistic test data generator.

Dispatches on the generator key from the rule engine and uses:
  - Faker (with en_IN locale by default)
  - Python random + regex
  - Custom lookup tables
"""

import random
import re
import string
import uuid
from datetime import date, timedelta
from typing import Any, Dict

from faker import Faker

from app.config import DEFAULT_LOCALE
from app.rule_engine import get_rules

# ──────────────────────────────────────────────
# Indian city / state lookup tables
# ──────────────────────────────────────────────

INDIAN_CITIES = [
    "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Ahmedabad", "Chennai",
    "Kolkata", "Pune", "Jaipur", "Lucknow", "Kanpur", "Nagpur", "Indore",
    "Thane", "Bhopal", "Visakhapatnam", "Patna", "Vadodara", "Coimbatore",
    "Surat", "Agra", "Meerut", "Nashik", "Faridabad", "Kochi", "Chandigarh",
    "Ghaziabad", "Ludhiana", "Noida", "Gurgaon", "Mysore", "Amritsar",
    "Mangalore", "Rajkot", "Raipur", "Bhubaneswar", "Jodhpur", "Guwahati",
]

INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Delhi", "Chandigarh",
]

# ──────────────────────────────────────────────
# Main Generator
# ──────────────────────────────────────────────

class DataGenerator:
    """
    Generates one value per call given a generator key + rules.
    A single instance is shared across all records in one request.
    """

    def __init__(self, locale: str = DEFAULT_LOCALE, seed: int | None = None) -> None:
        self.faker = Faker(locale)
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)

    # ── Dispatch ────────────────────────────────────────────────────────
    def generate(self, generator: str, rules: Dict[str, Any] | None = None) -> Any:
        if generator == "__empty__":
            return ""
        if rules is None:
            rules = get_rules(generator)

        dispatch = {
            "full_name":       self._full_name,
            "first_name":      self._first_name,
            "last_name":       self._last_name,
            "middle_name":     self._middle_name,
            "age":             self._age,
            "dob":             self._dob,
            "gender":          self._gender,
            "height":          self._height,
            "weight":          self._weight,
            "blood_group":     self._blood_group,
            "marital_status":  self._marital_status,
            "nationality":     self._nationality,
            "religion":        self._religion,
            "email":           self._email,
            "phone":           self._phone,
            "address":         self._address,
            "city":            self._city,
            "state":           self._state,
            "country":         self._country,
            "pin_code":        self._pin_code,
            "url":             self._url,
            "ip_address":      self._ip_address,
            "mac_address":     self._mac_address,
            "salary":          self._salary,
            "monthly_salary":  self._monthly_salary,
            "net_salary":      self._net_salary,
            "employee_id":     self._employee_id,
            "department":      self._department,
            "job_title":       self._job_title,
            "experience":      self._experience,
            "education":       self._education,
            "joining_date":    self._joining_date,
            "start_date":      self._start_date,
            "end_date":        self._end_date,
            "generic_date":    self._generic_date,
            "patient_id":      self._patient_id,
            "mrn":             self._mrn,
            "diagnosis":       self._diagnosis,
            "prescription":    self._prescription,
            "medication":      self._medication,
            "aadhar":          self._aadhar,
            "pan":             self._pan,
            "gst_number":      self._gst_number,
            "bank_account":    self._bank_account,
            "ifsc_code":       self._ifsc_code,
            "credit_card":     self._credit_card,
            "amount":          self._amount,
            "transaction_id":  self._transaction_id,
            "order_id":        self._order_id,
            "invoice_number":  self._invoice_number,
            "username":        self._username,
            "password":        self._password,
            "company":         self._company,
            "status":          self._status,
            "boolean":         self._boolean,
            "uuid":            self._uuid,
            "remarks":         self._remarks,
            "description":     self._description,
            # ── Deterministic type-router generators ─────────────────────
            "integer":         self._integer,
            "big_integer":     self._big_integer,
            "date_only":       self._date_only,
            "datetime_value":  self._datetime_value,
            "reference_id":    self._reference_id,
            "picklist_value":  self._picklist_value,
            "lookup_value":    self._lookup_value,
            "reg_id":          self._reg_id,
            "token_number":    self._token_number,
            # ── IntegrationPackage-specific generators ────────────────────
            "dob_mdy":         self._dob_mdy,
            "age_years":       self._age_years,
            "age_months":      self._age_months,
            "age_days":        self._age_days,
            "birth_time":      self._birth_time,
            "landline":        self._landline,
            "passport_number": self._passport_number,
            "driving_license": self._driving_license,
            "refugee_number":  self._refugee_number,
            "frro_number":     self._frro_number,
            "abha_number":     self._abha_number,
            "port_of_entry":   self._port_of_entry,
            "policy_source":   self._policy_source,
            "policy_number":   self._policy_number,
            "valid_date":      self._valid_date,
            "valid_from_date": self._valid_from_date,
            "valid_to_date":   self._valid_to_date,
        }

        fn = dispatch.get(generator)
        if fn is None:
            return self._fallback(generator, rules)
        return fn(rules)

    # ── Names ────────────────────────────────────────────────────────────
    def _full_name(self, r): return self.faker.name()
    def _first_name(self, r): return self.faker.first_name()
    def _last_name(self, r):  return self.faker.last_name()
    def _middle_name(self, r): return self.faker.first_name()  # reuse first name pool

    # ── Demographics ─────────────────────────────────────────────────────
    def _age(self, r):
        return random.randint(r.get("min", 18), r.get("max", 80))

    def _dob(self, r):
        min_age = r.get("min_age", 18)
        max_age = r.get("max_age", 80)
        today = date.today()
        start = today - timedelta(days=max_age * 365)
        end   = today - timedelta(days=min_age * 365)
        birth = start + timedelta(days=random.randint(0, (end - start).days))
        fmt = r.get("format", "%Y-%m-%d")
        return birth.strftime(fmt)

    def _gender(self, r):
        values  = r.get("values",  ["Male", "Female", "Other"])
        weights = r.get("weights", None)
        return random.choices(values, weights=weights, k=1)[0]

    def _height(self, r):
        return random.randint(r.get("min_cm", 150), r.get("max_cm", 195))

    def _weight(self, r):
        val = round(random.uniform(r.get("min_kg", 45), r.get("max_kg", 110)), 1)
        return val

    def _blood_group(self, r):
        values  = r.get("values",  ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
        weights = r.get("weights", None)
        return random.choices(values, weights=weights, k=1)[0]

    def _marital_status(self, r):
        values  = r.get("values",  ["Single", "Married", "Divorced", "Widowed"])
        weights = r.get("weights", None)
        return random.choices(values, weights=weights, k=1)[0]

    def _nationality(self, r):
        return random.choice(r.get("values", ["Indian"]))

    def _religion(self, r):
        return random.choice(r.get("values", ["Hindu", "Muslim", "Christian", "Other"]))

    # ── Contact ──────────────────────────────────────────────────────────
    def _email(self, r):
        domains = r.get("domain_pool", ["gmail.com", "yahoo.com", "outlook.com"])
        name = self.faker.user_name().replace(".", "").replace("-", "").lower()
        return f"{name}@{random.choice(domains)}"

    def _phone(self, r):
        # Generate exactly 10 numeric digits — no country code, no spaces, no hyphens.
        # Valid Indian mobile numbers start with 6, 7, 8, or 9.
        prefixes = ["6", "7", "8", "9"]
        rest = "".join(str(random.randint(0, 9)) for _ in range(9))
        number = random.choice(prefixes) + rest
        # Invariant: must be exactly 10 digits
        assert len(number) == 10 and number.isdigit(), f"Phone invariant violated: {number!r}"
        return number

    def _address(self, r):
        return self.faker.address().replace("\n", ", ")

    def _city(self, r):
        if r.get("indian_cities", True):
            return random.choice(INDIAN_CITIES)
        return self.faker.city()

    def _state(self, r):
        if r.get("indian_states", True):
            return random.choice(INDIAN_STATES)
        return self.faker.state()

    def _country(self, r):
        values = r.get("values", None)
        if values:
            return random.choice(values)
        return self.faker.country()

    def _pin_code(self, r):
        # Valid Indian 6-digit PIN code (starts 1-9, no 0s in first digit)
        first = random.randint(1, 9)
        rest  = "".join(str(random.randint(0, 9)) for _ in range(5))
        return f"{first}{rest}"

    def _url(self, r):
        return self.faker.url()

    def _ip_address(self, r):
        return self.faker.ipv4()

    def _mac_address(self, r):
        return self.faker.mac_address()

    # ── Finance / Employment ─────────────────────────────────────────────
    def _salary(self, r):
        lo   = r.get("min",  300000)
        hi   = r.get("max",  3000000)
        step = r.get("step", 10000)
        return random.randrange(lo, hi + step, step)

    def _monthly_salary(self, r):
        lo   = r.get("min",  25000)
        hi   = r.get("max",  250000)
        step = r.get("step", 1000)
        return random.randrange(lo, hi + step, step)

    def _net_salary(self, r):
        lo   = r.get("min",  20000)
        hi   = r.get("max",  200000)
        step = r.get("step", 1000)
        return random.randrange(lo, hi + step, step)

    def _employee_id(self, r):
        prefix = r.get("prefix", "EMP")
        digits = r.get("digits", 5)
        num = random.randint(10 ** (digits - 1), 10 ** digits - 1)
        return f"{prefix}{num}"

    def _department(self, r):
        return random.choice(r.get("values", ["Engineering", "HR", "Finance", "Sales"]))

    def _job_title(self, r):
        return random.choice(r.get("values", ["Software Engineer", "Manager"]))

    def _experience(self, r):
        return random.randint(r.get("min", 0), r.get("max", 35))

    def _education(self, r):
        return random.choice(r.get("values", ["B.Tech", "MBA", "B.Sc"]))

    # ── Dates ────────────────────────────────────────────────────────────
    def _joining_date(self, r):
        return self._date_in_range(r.get("min_year", 2010), r.get("max_year", 2025), r)

    def _start_date(self, r):
        return self._date_in_range(r.get("min_year", 2020), r.get("max_year", 2026), r)

    def _end_date(self, r):
        return self._date_in_range(r.get("min_year", 2025), r.get("max_year", 2027), r)

    def _generic_date(self, r):
        return self._date_in_range(r.get("min_year", 2020), r.get("max_year", 2026), r)

    def _date_in_range(self, min_year: int, max_year: int, r: dict) -> str:
        start = date(min_year, 1, 1)
        end   = date(max_year, 12, 31)
        delta = (end - start).days
        chosen = start + timedelta(days=random.randint(0, delta))
        return chosen.strftime(r.get("format", "%Y-%m-%d"))

    # ── Healthcare ───────────────────────────────────────────────────────
    def _patient_id(self, r):
        prefix = r.get("prefix", "PAT")
        digits = r.get("digits", 6)
        num = random.randint(10 ** (digits - 1), 10 ** digits - 1)
        return f"{prefix}{num}"

    def _mrn(self, r):
        prefix = r.get("prefix", "MRN")
        digits = r.get("digits", 7)
        num = random.randint(10 ** (digits - 1), 10 ** digits - 1)
        return f"{prefix}{num}"

    def _diagnosis(self, r):
        return random.choice(r.get("values", ["Hypertension", "Diabetes"]))

    def _prescription(self, r):
        return random.choice(r.get("values", ["Paracetamol 500mg as needed"]))

    def _medication(self, r):
        return random.choice(r.get("values", ["Paracetamol", "Metformin"]))

    # ── Identity Documents ───────────────────────────────────────────────
    def _aadhar(self, r):
        # Format: XXXX XXXX XXXX (first digit 2-9)
        first = str(random.randint(2, 9)) + "".join(str(random.randint(0,9)) for _ in range(3))
        mid   = "".join(str(random.randint(0, 9)) for _ in range(4))
        last  = "".join(str(random.randint(0, 9)) for _ in range(4))
        return f"{first} {mid} {last}"

    def _pan(self, r):
        # AAAAA0000A
        letters = "".join(random.choices(string.ascii_uppercase, k=5))
        digits  = "".join(str(random.randint(0, 9)) for _ in range(4))
        last    = random.choice(string.ascii_uppercase)
        return f"{letters}{digits}{last}"

    def _gst_number(self, r):
        state_code = str(random.randint(1, 37)).zfill(2)
        pan = self._pan({})
        entity = str(random.randint(1, 9))
        return f"{state_code}{pan}{entity}Z{random.choice(string.digits + string.ascii_uppercase)}"

    # ── Finance ──────────────────────────────────────────────────────────
    def _bank_account(self, r):
        length = random.randint(r.get("min_digits", 10), r.get("max_digits", 16))
        return "".join(str(random.randint(0, 9)) for _ in range(length))

    def _ifsc_code(self, r):
        bank_codes = ["HDFC", "ICIC", "SBIN", "AXIS", "KOTK", "PUNB", "BKID", "CNRB"]
        bank  = random.choice(bank_codes)
        rest  = "0" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"{bank}{rest}"

    def _credit_card(self, r):
        return self.faker.credit_card_number()

    def _amount(self, r):
        lo  = r.get("min",      100)
        hi  = r.get("max",    100000)
        dec = r.get("decimals",   2)
        val = round(random.uniform(lo, hi), dec)
        return val

    def _transaction_id(self, r):
        prefix = r.get("prefix", "TXN")
        digits = r.get("digits", 10)
        num = random.randint(10 ** (digits - 1), 10 ** digits - 1)
        return f"{prefix}{num}"

    def _order_id(self, r):
        prefix = r.get("prefix", "ORD")
        digits = r.get("digits", 8)
        num = random.randint(10 ** (digits - 1), 10 ** digits - 1)
        return f"{prefix}{num}"

    def _invoice_number(self, r):
        prefix = r.get("prefix", "INV")
        digits = r.get("digits", 6)
        num = random.randint(10 ** (digits - 1), 10 ** digits - 1)
        return f"{prefix}{num}"

    # ── System / Misc ─────────────────────────────────────────────────────
    def _username(self, r):
        min_len = r.get("min_length", 6)
        max_len = r.get("max_length", 15)
        base = self.faker.user_name().lower().replace(".", "").replace("-", "")
        base = base[:max_len]
        if len(base) < min_len:
            base = base + "".join(random.choices(string.digits, k=min_len - len(base)))
        return base

    def _password(self, r):
        length = r.get("length", 12)
        chars  = string.ascii_letters + string.digits
        if r.get("special_chars", True):
            chars += "!@#$%^&*"
        return "".join(random.choices(chars, k=length))

    def _company(self, r):
        return self.faker.company()

    def _status(self, r):
        return random.choice(r.get("values", ["Active", "Inactive"]))

    def _boolean(self, r):
        return random.choice([True, False])

    def _uuid(self, r):
        return str(uuid.uuid4())

    def _remarks(self, r):
        words = [
            "pending", "verified", "approved", "reviewed", "submitted",
            "processed", "confirmed", "completed", "follow-up required",
            "document uploaded", "waiting for approval", "in progress"
        ]
        max_words = r.get("max_words", 5)
        sample = random.sample(words, min(max_words, len(words)))
        return " ".join(sample[:random.randint(2, max_words)]).capitalize()

    def _description(self, r):
        return self.faker.sentence(nb_words=r.get("max_words", 10))

    # ── Fallback ─────────────────────────────────────────────────────────
    def _fallback(self, generator: str, r: dict) -> Any:
        """Last resort: return a plausible value based on generator name."""
        g = generator.lower()
        if "name" in g:
            return self.faker.name()
        if "date" in g:
            return self.faker.date()
        if "email" in g:
            return self.faker.email()
        if "phone" in g or "mobile" in g:
            return self._phone(r)
        if "id" in g or "number" in g or "no" in g:
            return str(random.randint(100000, 999999))
        if "amount" in g or "salary" in g or "price" in g:
            return random.randint(1000, 100000)
        return self.faker.word()


    # ── Deterministic type-router generators ───────────────────────────
    # These are invoked when the field has a declared integer Type that maps
    # deterministically to a generator (no FAISS needed).
    # ─────────────────────────────────────────────────────────────

    def _integer(self, r: dict) -> int:
        """Type 3 (Number) / Type 7 (Integer) — generate a realistic integer."""
        return random.randint(r.get("min", 1), r.get("max", 999))

    def _big_integer(self, r: dict) -> int:
        """Type 8 (BigInt) — generate a large integer."""
        return random.randint(r.get("min", 100_000), r.get("max", 999_999_999))

    def _date_only(self, r: dict) -> str:
        """Type 4 (Date) / Type 9 (DateTime) — generate a valid date string YYYY-MM-DD."""
        return self._date_in_range(
            r.get("min_year", 1970),
            r.get("max_year", 2025),
            r,
        )

    def _datetime_value(self, r: dict) -> str:
        """Type 9 (DateTime) with time component — generate YYYY-MM-DD HH:MM."""
        date_str = self._date_only(r)
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        return f"{date_str} {hour:02d}:{minute:02d}"

    def _reference_id(self, r: dict) -> str:
        """Type 10 (reference) — generate a realistic reference ID."""
        prefix = r.get("prefix", "REF")
        digits = r.get("digits", 5)
        num = random.randint(10 ** (digits - 1), 10 ** digits - 1)
        return f"{prefix}-{num}"

    def _picklist_value(self, r: dict) -> str:
        """Type 11 (Picklist) / Type 15 (Dropdown) — return a business status value.

        The rules dict may carry a 'values' list supplied by business context.
        Falls back to a general clinical/business picklist.
        """
        default_values = [
            "Open", "Closed", "Pending", "Cancelled", "Active", "Inactive",
            "Approved", "Rejected", "On Hold", "Completed", "Processing",
            "Reviewed", "Submitted", "In Progress",
        ]
        return random.choice(r.get("values", default_values))

    def _lookup_value(self, r: dict) -> str:
        """Type 16 (Lookup) — return a realistic lookup-style value.

        Lookup fields represent typeahead / dropdown selections pointing to
        another entity (Doctor Name, Department, Branch, Hospital, etc.).
        The rules dict may carry 'entity' or 'values' to narrow the pool.
        """
        entity = r.get("entity", "").lower()

        if "doctor" in entity or "physician" in entity:
            titles = ["Dr.", "Dr."]
            return f"{random.choice(titles)} {self.faker.name()}"

        if "department" in entity or "dept" in entity:
            departments = [
                "Cardiology", "Neurology", "Orthopedics", "Pediatrics",
                "Radiology", "Dermatology", "General Medicine", "Oncology",
                "Ophthalmology", "ENT", "Psychiatry", "Nephrology",
            ]
            return random.choice(departments)

        if "branch" in entity or "hospital" in entity:
            return f"{random.choice(INDIAN_CITIES)} Branch"

        # Generic lookup: realistic name from the Faker pool
        return self.faker.name()

    def _reg_id(self, r: dict) -> int:
        """Registration ID (Reg ID) — generate numeric values only (e.g., 100245, 999876)."""
        lo = r.get("min", 100000)
        hi = r.get("max", 999999)
        return random.randint(lo, hi)

    def _token_number(self, r: dict) -> int:
        """Token Number — generate numeric values only (e.g., 1, 25, 102, 999)."""
        lo = r.get("min", 1)
        hi = r.get("max", 999)
        return random.randint(lo, hi)

    # ── IntegrationPackage-specific generators ─────────────────────────
    # These handle the rich field variety found in clinical registration
    # forms: date components, identity documents, insurance, etc.
    # ─────────────────────────────────────────────────────────────────

    def _dob_mdy(self, r: dict) -> str:
        """Date of Birth in MM/DD/YYYY format (DisplayName='MM/DD/YYYY')."""
        min_age = r.get("min_age", 1)
        max_age = r.get("max_age", 90)
        today = date.today()
        start = today - timedelta(days=max_age * 365)
        end   = today - timedelta(days=min_age * 365)
        birth = start + timedelta(days=random.randint(0, (end - start).days))
        return birth.strftime("%m/%d/%Y")

    def _age_years(self, r: dict) -> int:
        """Age in years (DisplayName='Years'). Range 0-110."""
        return random.randint(r.get("min", 0), r.get("max", 110))

    def _age_months(self, r: dict) -> int:
        """Age months component (DisplayName='Months'). Range 0-11."""
        return random.randint(r.get("min", 0), r.get("max", 11))

    def _age_days(self, r: dict) -> int:
        """Age days component (DisplayName='Days'). Range 0-30."""
        return random.randint(r.get("min", 0), r.get("max", 30))

    def _birth_time(self, r: dict) -> str:
        """Time of birth in HH:MM AM/PM format (e.g. '10:30 AM')."""
        hour24 = random.randint(0, 23)
        minute = random.randint(0, 59)
        period = "AM" if hour24 < 12 else "PM"
        hour12 = hour24 % 12
        if hour12 == 0:
            hour12 = 12
        return f"{hour12:02d}:{minute:02d} {period}"

    def _landline(self, r: dict) -> str:
        """Indian landline number in STD format (e.g. '044-23456789').
        Covers major city STD codes: 011=Delhi, 022=Mumbai, 033=Kolkata,
        044=Chennai, 080=Bangalore, etc."""
        std_codes = [
            "011", "022", "033", "044", "040", "020", "079",
            "080", "0484", "0471", "0361", "0172", "0141",
        ]
        std = random.choice(std_codes)
        # Subscriber number length varies: 8 digits for 3-digit STD, 7 for 4-digit
        sub_len = 7 if len(std) == 4 else 8
        sub = "".join(str(random.randint(0, 9)) for _ in range(sub_len))
        # Ensure subscriber doesn't start with 0
        sub = str(random.randint(2, 9)) + sub[1:]
        return f"{std}-{sub}"

    def _passport_number(self, r: dict) -> str:
        """Indian passport number: 1 uppercase letter + 7 digits (e.g. 'P1234567')."""
        letter = random.choice(string.ascii_uppercase)
        digits = "".join(str(random.randint(0, 9)) for _ in range(7))
        return f"{letter}{digits}"

    def _driving_license(self, r: dict) -> str:
        """Indian driving licence number in format: ST-YYYY########### (e.g. 'TN-2026001234567').
        Format: 2-letter state code + hyphen + 4-digit year + 9-13 digits."""
        state_codes = [
            "TN", "MH", "DL", "KA", "AP", "TS", "KL", "GJ",
            "RJ", "UP", "WB", "MP", "PB", "HR", "OR",
        ]
        state = random.choice(state_codes)
        year = random.randint(2015, 2026)
        serial = "".join(str(random.randint(0, 9)) for _ in range(9))
        return f"{state}-{year}{serial}"

    def _refugee_number(self, r: dict) -> str:
        """UNHCR / refugee registration number (e.g. 'REF-2026-001234')."""
        year = random.randint(2015, 2026)
        serial = str(random.randint(1, 999999)).zfill(6)
        return f"REF-{year}-{serial}"

    def _frro_number(self, r: dict) -> str:
        """Foreigners Regional Registration Office number (e.g. 'FRRO-2026-001234')."""
        year = random.randint(2015, 2026)
        serial = str(random.randint(1, 999999)).zfill(6)
        return f"FRRO-{year}-{serial}"

    def _abha_number(self, r: dict) -> str:
        """ABHA (Ayushman Bharat Health Account) number in format ##-####-####-#### (14 digits)."""
        parts = [
            "".join(str(random.randint(0, 9)) for _ in range(2)),
            "".join(str(random.randint(0, 9)) for _ in range(4)),
            "".join(str(random.randint(0, 9)) for _ in range(4)),
            "".join(str(random.randint(0, 9)) for _ in range(4)),
        ]
        return "-".join(parts)

    def _port_of_entry(self, r: dict) -> str:
        """Realistic Indian international port / airport of entry name."""
        ports = r.get("values", [
            "Chennai International Airport",
            "Indira Gandhi International Airport, Delhi",
            "Chhatrapati Shivaji Maharaj International Airport, Mumbai",
            "Kempegowda International Airport, Bangalore",
            "Rajiv Gandhi International Airport, Hyderabad",
            "Netaji Subhas Chandra Bose International Airport, Kolkata",
            "Cochin International Airport",
            "Coimbatore International Airport",
            "Calicut International Airport",
            "Tiruchirappalli International Airport",
            "Madurai Airport",
            "Visakhapatnam Airport",
            "Goa International Airport (Mopa)",
            "Amritsar Sri Guru Ram Dass Jee International Airport",
            "Port of Chennai (Seaport)",
            "Jawaharlal Nehru Port, Mumbai (Seaport)",
            "Kolkata Port (Seaport)",
        ])
        return random.choice(ports)

    def _policy_source(self, r: dict) -> str:
        """Realistic insurance / policy source / scheme name."""
        sources = r.get("values", [
            "Government Insurance Scheme",
            "Ayushman Bharat - PMJAY",
            "ESIC (Employees State Insurance Corporation)",
            "CGHS (Central Government Health Scheme)",
            "Star Health Insurance",
            "New India Assurance",
            "HDFC Ergo Health Insurance",
            "Bajaj Allianz Health Insurance",
            "United India Insurance",
            "National Insurance Company",
            "ICICI Lombard Health Insurance",
            "Max Bupa Health Insurance",
            "Oriental Insurance",
            "Reliance Health Insurance",
            "SBI Health Insurance",
            "Niva Bupa Health Insurance",
            "Care Health Insurance",
            "Manipal Cigna Health Insurance",
            "Aditya Birla Health Insurance",
            "Royal Sundaram Health Insurance",
        ])
        return random.choice(sources)

    def _policy_number(self, r: dict) -> str:
        """Insurance policy number in format POL-YYYY-######## (e.g. 'POL-2026-00123456')."""
        year = random.randint(2020, 2026)
        serial = str(random.randint(1, 99999999)).zfill(8)
        prefix = r.get("prefix", "POL")
        return f"{prefix}-{year}-{serial}"

    def _valid_date(self, r: dict) -> str:
        """Date in DD-MM-YYYY format for validity / insurance dates (e.g. '01-01-2026')."""
        return self._date_in_range(
            r.get("min_year", 2020),
            r.get("max_year", 2030),
            {**r, "format": "%d-%m-%Y"},
        )

    def _valid_from_date(self, r: dict) -> str:
        """Start/from date in DD-MM-YYYY — always in the past/current window (2020-2025)."""
        return self._date_in_range(
            r.get("min_year", 2020),
            r.get("max_year", 2025),
            {**r, "format": "%d-%m-%Y"},
        )

    def _valid_to_date(self, r: dict) -> str:
        """End/to/upto date in DD-MM-YYYY — always future (2026-2030), so From < To."""
        return self._date_in_range(
            r.get("min_year", 2026),
            r.get("max_year", 2030),
            {**r, "format": "%d-%m-%Y"},
        )

