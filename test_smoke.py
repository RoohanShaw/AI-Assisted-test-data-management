# -*- coding: utf-8 -*-
"""
test_smoke.py - Quick smoke test (no pytest needed).

Can be run directly:
    python test_smoke.py

Or imported as a module and called programmatically:
    from test_smoke import run_smoke_tests
    run_smoke_tests()
"""

import json
import sys
import os

# Force UTF-8 output on Windows so Unicode in generated names prints fine
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Make sure we can import the app modules from project root
sys.path.insert(0, os.path.dirname(__file__))


def run_smoke_tests() -> bool:
    """
    Run all smoke tests programmatically.

    Prints a checkmark (✓) for each passing test and a cross (✗) for failures.
    Raises SystemExit (with a non-zero code) if any test fails so that
    callers (e.g. start.py) can detect failure without catching a generic
    Exception.

    Returns True when every test passes.
    """
    failed_tests = []

    def _ok(label: str) -> None:
        print(f"  \u2713 {label}")

    def _fail(label: str, exc: Exception) -> None:
        print(f"  \u2717 {label} Failed")
        print(f"      Error: {exc}")
        failed_tests.append((label, exc))

    print("\nRunning Smoke Tests...")

    # ------------------------------------------------------------------
    # Test 1: Config loads
    # ------------------------------------------------------------------
    try:
        from app.config import SIMILARITY_THRESHOLD, EMBEDDING_MODEL, FAISS_INDEX_PATH  # noqa: F401
        _ok(f"Config  (model={EMBEDDING_MODEL}, threshold={SIMILARITY_THRESHOLD})")
    except Exception as exc:
        _fail("Config", exc)

    # ------------------------------------------------------------------
    # Test 2: Embedding engine
    # ------------------------------------------------------------------
    try:
        from app.embedding_engine import encode, warm_up
        warm_up()
        vec = encode("Patient Name")
        assert vec.shape == (384,), f"Expected (384,), got {vec.shape}"
        _ok(f"Embedding Engine  (vector shape: {vec.shape})")
    except Exception as exc:
        _fail("Embedding Engine", exc)

    # ------------------------------------------------------------------
    # Test 3 + 4: FAISS store + similarity search
    # ------------------------------------------------------------------
    store = None
    try:
        from app.faiss_store import get_store
        store = get_store()
        store.initialize()
        _ok(f"FAISS  ({store.size} vectors in index)")
    except Exception as exc:
        _fail("FAISS", exc)

    if store is not None:
        try:
            test_cases = [
                ("Patient Name", "Full Name",       0.82),
                ("Age",          "Human Age",       0.82),
                ("Salary",       "Employee Salary", 0.82),
                ("Email",        "Email Address",   0.82),
                ("Phone Number", "Phone Number",    0.82),
            ]
            all_pass = True
            for query, _expected_cat, threshold in test_cases:
                meta, score = store.best_match(query)
                passed = meta is not None and score >= threshold
                if not passed:
                    all_pass = False
            if not all_pass:
                raise AssertionError("One or more similarity searches did not meet the threshold")
            _ok("Similarity Search")
        except Exception as exc:
            _fail("Similarity Search", exc)

    # ------------------------------------------------------------------
    # Test 5: Rule engine
    # ------------------------------------------------------------------
    try:
        from app.rule_engine import get_rules
        age_rules = get_rules("age")
        assert age_rules["min"] == 18 and age_rules["max"] == 80
        salary_rules = get_rules("salary")
        assert salary_rules["min"] == 300000
        _ok("Rule Engine")
    except Exception as exc:
        _fail("Rule Engine", exc)

    # ------------------------------------------------------------------
    # Test 6: Generator
    # ------------------------------------------------------------------
    gen = None
    try:
        from app.generator import DataGenerator
        gen = DataGenerator(seed=42)
        name   = gen.generate("full_name")   # noqa: F841
        age    = gen.generate("age")
        salary = gen.generate("salary")
        email  = gen.generate("email")
        phone  = gen.generate("phone")       # noqa: F841
        mrn    = gen.generate("mrn")         # noqa: F841
        pan    = gen.generate("pan")
        aadhar = gen.generate("aadhar")      # noqa: F841
        assert isinstance(age, int) and 18 <= age <= 80, f"Age out of range: {age}"
        assert isinstance(salary, int) and 300000 <= salary <= 3000000, f"Salary out of range: {salary}"
        assert "@" in email, f"Invalid email: {email}"
        assert pan[-1].isalpha() and len(pan) == 10, f"Invalid PAN: {pan}"
        _ok("Generator")
    except Exception as exc:
        _fail("Generator", exc)

    # ------------------------------------------------------------------
    # Test 7: Semantic classifier
    # ------------------------------------------------------------------
    results = None
    try:
        from app.models import FieldDefinition
        from app.semantic_classifier import classify_fields

        fields = [
            FieldDefinition(field_name="Patient Name", field_type="String"),
            FieldDefinition(field_name="Age",          field_type="Number"),
            FieldDefinition(field_name="Salary",       field_type="Number"),
            FieldDefinition(field_name="MRN",          field_type="String"),
        ]
        results = classify_fields(fields, module="Registration")
        assert results, "classify_fields returned empty result"
        _ok("Semantic Classifier")
    except Exception as exc:
        _fail("Semantic Classifier", exc)

    # ------------------------------------------------------------------
    # Test 8: Full pipeline simulation
    # ------------------------------------------------------------------
    if gen is not None and results is not None:
        try:
            records = []
            for _ in range(3):
                record = {}
                for clf in results:
                    record[clf.field_name] = gen.generate(clf.generator, clf.rules)
                records.append(record)
            assert len(records) == 3, "Expected 3 records"
            _ok("Pipeline  (3 records generated)")
        except Exception as exc:
            _fail("Pipeline", exc)

    # ------------------------------------------------------------------
    # Test 9: Excel/JSON Parser
    # ------------------------------------------------------------------
    normalized = None
    try:
        from app.excel_parser import parse_json_input

        sample_input = {
            "PackageName": "TP_Smoke",
            "TestSuites": [
                {
                    "TestSuiteName": "TS_01",
                    "SelectedTestSuite": [
                        {
                            "IterationCount": "2",
                            "SeleniumExecutionFlow": [
                                {
                                    "Name": "Patient Registration - Search",
                                    "Fields": [
                                        {"Name": "NavBtn",  "DisplayName": ["Navigate"],      "Type": 24, "IsNavigation": True,  "IsLookupon": False},
                                        {"Name": "reg_no",  "DisplayName": ["Reg No"],        "Type": 6,  "IsNavigation": False, "IsLookupon": False},
                                        {"Name": "dob",     "DisplayName": ["Date of Birth"], "Type": 9,  "IsNavigation": False, "IsLookupon": False},
                                        {"Name": "dept",    "DisplayName": ["Department"],    "Type": 11, "IsNavigation": False, "IsLookupon": False},
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        normalized = parse_json_input(sample_input)
        assert normalized["test_package_name"] == "TP_Smoke", "Package name mismatch"
        assert "TS_01" in normalized["test_suites"], "Suite not found"
        obj = normalized["test_suites"]["TS_01"]["objects"]["Patient Registration - Search"]
        assert obj["iteration_count"] == 2, f"Expected 2 iterations, got {obj['iteration_count']}"
        assert "Reg No"        in obj["fields"], "Reg No field missing"
        assert "Date of Birth" in obj["fields"], "DOB field missing"
        assert "Navigate"  not in obj["fields"], "Navigation field should be excluded"
        _ok("JSON Parser (excel_parser)")
    except Exception as exc:
        _fail("JSON Parser (excel_parser)", exc)

    # ------------------------------------------------------------------
    # Test 10: Template builder
    # ------------------------------------------------------------------
    template = None
    if normalized is not None:
        try:
            from app.template_builder import build_template, collect_all_field_names

            template = build_template(normalized)
            assert template["TestPackageName"] == "TP_Smoke"
            assert "TS_01" in template["TestSuites"]
            obj_template = template["TestSuites"]["TS_01"]["Objects"]["Patient Registration - Search"]
            assert "Login"      in obj_template, "Login block missing"
            assert "Iterations" in obj_template, "Iterations block missing"
            assert "1" in obj_template["Iterations"] and "2" in obj_template["Iterations"], "Expected 2 iterations"
            assert "Reg No" in obj_template["Iterations"]["1"]["Fields"], "Field missing in iteration"
            assert obj_template["Iterations"]["1"]["Fields"]["Reg No"] == "", "Field should be empty before generation"
            all_fields = collect_all_field_names(template)
            assert "Reg No" in all_fields and "Date of Birth" in all_fields
            _ok("Template Builder")
        except Exception as exc:
            _fail("Template Builder", exc)

    # ------------------------------------------------------------------
    # Test 11: Full pipeline from SampleInput.json
    # ------------------------------------------------------------------
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(__file__)
    sample_input_path = os.path.join(base_dir, "SampleInput.json")
    if os.path.exists(sample_input_path):
        try:
            from app.pipeline import run_pipeline
            from app.excel_parser import load_json_file

            normalized_full = load_json_file(sample_input_path)
            result = run_pipeline(
                normalized=normalized_full,
                module="Appointment",
                locale="en_IN",
                seed=42,
            )
            output   = result["output"]
            metadata = result["metadata"]
            assert "TestPackageName" in output, "TestPackageName missing from output"
            assert "TestSuites"      in output, "TestSuites missing from output"
            assert output["TestPackageName"] == normalized_full["test_package_name"]

            populated_count = sum(
                1
                for suite_data in output["TestSuites"].values()
                for obj_data   in suite_data["Objects"].values()
                for iter_data  in obj_data["Iterations"].values()
                for v          in iter_data["Fields"].values()
                if v != "" and v is not None
            )
            assert populated_count > 0, "No fields were populated — check AI pipeline"
            _ok(f"Full Pipeline from SampleInput.json  ({populated_count} fields populated, {len(metadata)} classified)")
        except Exception as exc:
            _fail("Full Pipeline from SampleInput.json", exc)
    else:
        print(f"  [SKIP] Full Pipeline — SampleInput.json not found at {sample_input_path}")

    # ------------------------------------------------------------------
    # Test 12: Zero-based FIELD_TYPE_MAP enum mapping
    # ------------------------------------------------------------------
    try:
        from app.field_types import FIELD_TYPE_MAP, get_type_name

        expected = {
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
        # Verify every entry in the map
        for type_int, type_name in expected.items():
            actual = FIELD_TYPE_MAP.get(type_int)
            assert actual == type_name, (
                f"FIELD_TYPE_MAP[{type_int}] = {actual!r}, expected {type_name!r}"
            )
        # Spot-check the get_type_name helper
        assert get_type_name(6)  == "String",   f"Type 6 should be String, got {get_type_name(6)!r}"
        assert get_type_name(9)  == "DateTime", f"Type 9 should be DateTime, got {get_type_name(9)!r}"
        assert get_type_name(11) == "Picklist", f"Type 11 should be Picklist, got {get_type_name(11)!r}"
        assert get_type_name(15) == "Dropdown", f"Type 15 should be Dropdown, got {get_type_name(15)!r}"
        assert get_type_name(20) == "Boolean",  f"Type 20 should be Boolean, got {get_type_name(20)!r}"
        assert get_type_name(24) == "Button",   f"Type 24 should be Button, got {get_type_name(24)!r}"
        _ok("Zero-based FIELD_TYPE_MAP  (all 26 entries verified, spot-checks passed)")
    except Exception as exc:
        _fail("Zero-based FIELD_TYPE_MAP", exc)

    # ------------------------------------------------------------------
    # Test 13: Type-based routing correctness
    # ------------------------------------------------------------------
    try:
        from app.field_type_router import route_by_type, should_skip, should_empty

        # Rule 1: IsNavigation=True → always skip regardless of type
        clf_nav = route_by_type(field_type=6, is_navigation=True, field_name="NavField")
        assert clf_nav is not None and should_skip(clf_nav), \
            "IsNavigation=True field should be skipped"

        # Rule 2: Type=24 (Button) + IsNavigation=False → still skip
        clf_btn = route_by_type(field_type=24, is_navigation=False, field_name="SaveBtn")
        assert clf_btn is not None and should_skip(clf_btn), \
            "Type=24 Button field should be skipped even if IsNavigation=False"

        # Rule 2 variant: Type=24 + IsNavigation=True → skip (most common case)
        clf_navbtn = route_by_type(field_type=24, is_navigation=True, field_name="NavBtn")
        assert clf_navbtn is not None and should_skip(clf_navbtn), \
            "Type=24 IsNavigation=True field should be skipped"

        # Rule 2.5: Type=11 (Picklist) → empty (no Faker value)
        clf_pk = route_by_type(field_type=11, is_navigation=False, field_name="Title")
        assert clf_pk is not None and should_empty(clf_pk), \
            "Type=11 Picklist field should have empty value"

        # Rule 2.5: Type=15 (Dropdown) → empty (no Faker value)
        clf_dd = route_by_type(field_type=15, is_navigation=False, field_name="Department")
        assert clf_dd is not None and should_empty(clf_dd), \
            "Type=15 Dropdown field should have empty value"

        # Rule 3: Type=6 (String) → returns None → goes to FAISS AI pipeline
        clf_str = route_by_type(field_type=6, is_navigation=False, field_name="Patient Name")
        assert clf_str is None, \
            "Type=6 String field should return None (sent to FAISS)"

        _ok("Type-based routing  (Button/Nav skip, Picklist/Dropdown empty, String→FAISS)")
    except Exception as exc:
        _fail("Type-based routing", exc)

    # ------------------------------------------------------------------
    # Test 14: Phone number format — exactly 10 digits, no country code
    # ------------------------------------------------------------------
    try:
        from app.generator import DataGenerator

        gen_phone = DataGenerator(seed=99)
        phone_errors = []
        for i in range(50):   # generate 50 phone numbers and validate all
            phone = gen_phone.generate("phone")
            phone_str = str(phone)
            if len(phone_str) != 10:
                phone_errors.append(f"[{i}] len={len(phone_str)}: {phone_str!r}")
            elif not phone_str.isdigit():
                phone_errors.append(f"[{i}] not all digits: {phone_str!r}")
            elif phone_str[0] not in "6789":
                phone_errors.append(f"[{i}] invalid prefix {phone_str[0]!r}: {phone_str!r}")
            elif "+91" in phone_str:
                phone_errors.append(f"[{i}] contains +91: {phone_str!r}")

        assert not phone_errors, (
            f"Phone format violations ({len(phone_errors)}/50):\n  "
            + "\n  ".join(phone_errors)
        )
        sample = gen_phone.generate("phone")
        _ok(
            f"Phone format  (50 generated, all exactly 10 digits, no country code, "
            f"sample={sample!r})"
        )
    except Exception as exc:
        _fail("Phone format", exc)

    # ------------------------------------------------------------------
    # Test 15: IntegrationPackage.json — end-to-end pipeline
    # ------------------------------------------------------------------
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(__file__)
    integration_pkg_path = os.path.join(base_dir, "IntegrationPackage.json")
    if os.path.exists(integration_pkg_path):
        try:
            from app.pipeline import run_pipeline
            from app.excel_parser import load_json_file

            normalized_ip = load_json_file(integration_pkg_path)

            # Structural assertions
            assert normalized_ip["test_package_name"] == "IntegrationPackage", \
                f"PackageName mismatch: {normalized_ip['test_package_name']!r}"
            assert normalized_ip["test_suites"], "No test suites parsed from IntegrationPackage"

            # Run the full pipeline
            result_ip = run_pipeline(
                normalized=normalized_ip,
                module="Registration",
                locale="en_IN",
                seed=42,
            )
            output_ip = result_ip["output"]

            assert "TestPackageName" in output_ip, "TestPackageName missing from output"
            assert output_ip["TestPackageName"] == "IntegrationPackage", \
                f"Wrong package name: {output_ip['TestPackageName']!r}"
            assert "TestSuites" in output_ip, "TestSuites missing from output"

            # Walk every iteration and collect generated field values
            populated_fields = {}
            for suite_data in output_ip["TestSuites"].values():
                for obj_data in suite_data.get("Objects", {}).values():
                    for iter_data in obj_data.get("Iterations", {}).values():
                        for fname, fval in iter_data.get("Fields", {}).items():
                            populated_fields[fname] = fval

            # Verify Button/Navigation fields (Type=24 + IsNavigation) were removed
            nav_button_names = {
                "Registration", "New Registration",  # Type=24 + IsNavigation=True in pkg
            }
            for nav_name in nav_button_names:
                assert nav_name not in populated_fields, \
                    f"Navigation/Button field '{nav_name}' should be absent from output"

            # Verify String fields (Type=6) got real values generated
            string_fields_found = {
                k: v for k, v in populated_fields.items()
                if v is not None and v != ""
            }
            assert string_fields_found, \
                "No String fields were populated — check FAISS/heuristic pipeline"

            # Verify mobile fields: field whose Name contains 'mobile' (not 'office' or 'landline')
            # should be exactly 10 digits.
            # Note: 'Office Phone' and 'Landline' fields intentionally use STD format, not 10 digits.
            phone_violations = []
            for fname, fval in populated_fields.items():
                fname_lower = fname.lower().replace(" ", "")
                is_mobile = "mobile" in fname_lower and "office" not in fname_lower
                is_landline = any(kw in fname_lower for kw in ("landline", "officefax", "officephone"))
                if is_mobile and not is_landline:
                    if fval and fval != "":
                        fval_str = str(fval)
                        if len(fval_str) != 10 or not fval_str.isdigit():
                            phone_violations.append(f"{fname!r}={fval_str!r}")
            assert not phone_violations, (
                f"Mobile fields with invalid format (expected 10 digits): {phone_violations}"
            )

            populated_count = sum(
                1 for v in populated_fields.values() if v != "" and v is not None
            )
            _ok(
                f"IntegrationPackage.json pipeline  "
                f"({populated_count} fields populated, "
                f"{len(result_ip['metadata'])} classified, "
                f"package={output_ip['TestPackageName']!r})"
            )
        except Exception as exc:
            _fail("IntegrationPackage.json pipeline", exc)
    else:
        print(
            f"  [SKIP] IntegrationPackage.json pipeline — "
            f"file not found at {integration_pkg_path}"
        )

    # ------------------------------------------------------------------
    # Final verdict
    # ------------------------------------------------------------------

    if failed_tests:
        print(f"\nApplication startup aborted. ({len(failed_tests)} test(s) failed)\n")
        sys.exit(1)

    print("\nAll smoke tests passed.\n")
    return True


# ---------------------------------------------------------------------------
# Allow running directly:  python test_smoke.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    print("=" * 60)
    print("  AI Test Data Generator - Smoke Test")
    print("=" * 60)

    run_smoke_tests()

    print("=" * 60)
    print("  ALL TESTS PASSED \u2713")
    print("=" * 60)
    print("\nNew endpoints available after starting server:")
    print("  POST /api/v1/generate/from-json   (send SampleInput.json as body)")
    print("  POST /api/v1/generate/from-excel  (upload .xlsx TDM file)")
    print("\nTo start the API server, run:")
    print("  python start.py")
    print("\nAPI docs: http://localhost:8000/docs")
