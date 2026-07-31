"""
Sample requests for testing the AI Test Data Generator API.
Run the server first:  python start.py
Then use these with curl, Postman, or the Swagger UI at http://localhost:8000/docs
"""

SAMPLES = {
    "registration": {
        "description": "Hospital registration module",
        "request": {
            "module": "Registration",
            "record_count": 3,
            "fields": [
                {"field_name": "Patient Name",  "field_type": "String"},
                {"field_name": "Age",           "field_type": "Number"},
                {"field_name": "DOB",           "field_type": "Date"},
                {"field_name": "Gender",        "field_type": "String"},
                {"field_name": "Blood Group",   "field_type": "String"},
                {"field_name": "MRN",           "field_type": "String"},
                {"field_name": "Phone Number",  "field_type": "String"},
                {"field_name": "Email",         "field_type": "Email"},
                {"field_name": "Address",       "field_type": "String"},
            ]
        }
    },
    "payroll": {
        "description": "HR/Payroll module",
        "request": {
            "module": "Payroll",
            "record_count": 5,
            "fields": [
                {"field_name": "Employee Name", "field_type": "String"},
                {"field_name": "Employee ID",   "field_type": "String"},
                {"field_name": "Department",    "field_type": "String"},
                {"field_name": "Designation",   "field_type": "String"},
                {"field_name": "Salary",        "field_type": "Number"},
                {"field_name": "Joining Date",  "field_type": "Date"},
                {"field_name": "PAN",           "field_type": "String"},
                {"field_name": "Aadhar",        "field_type": "String"},
            ]
        }
    },
    "banking": {
        "description": "Banking/Finance module",
        "request": {
            "module": "Banking",
            "record_count": 4,
            "fields": [
                {"field_name": "Customer Name",  "field_type": "String"},
                {"field_name": "Account Number", "field_type": "String"},
                {"field_name": "IFSC Code",      "field_type": "String"},
                {"field_name": "Transaction ID", "field_type": "String"},
                {"field_name": "Amount",         "field_type": "Number"},
                {"field_name": "Credit Card",    "field_type": "String"},
            ]
        }
    },
    "ecommerce": {
        "description": "E-Commerce order module",
        "request": {
            "module": "E-Commerce",
            "record_count": 3,
            "fields": [
                {"field_name": "Customer Name", "field_type": "String"},
                {"field_name": "Email",         "field_type": "Email"},
                {"field_name": "Phone",         "field_type": "Phone"},
                {"field_name": "Order ID",      "field_type": "String"},
                {"field_name": "Amount",        "field_type": "Number"},
                {"field_name": "Status",        "field_type": "String"},
                {"field_name": "City",          "field_type": "String"},
            ]
        }
    }
}

if __name__ == "__main__":
    import json
    import urllib.request
    import urllib.error

    BASE_URL = "http://localhost:8000/api/v1"

    for name, sample in SAMPLES.items():
        print(f"\n{'='*60}")
        print(f"  Module: {sample['description']}")
        print(f"{'='*60}")
        print("Request:")
        print(json.dumps(sample["request"], indent=2))

        try:
            data = json.dumps(sample["request"]).encode()
            req = urllib.request.Request(
                f"{BASE_URL}/generate",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())
                print("\nResponse (records):")
                print(json.dumps(result["records"], indent=2, ensure_ascii=False))
                if result.get("warnings"):
                    print("\nWarnings:", result["warnings"])
        except urllib.error.URLError as e:
            print(f"\nERROR: Could not connect to server at {BASE_URL}")
            print("Make sure the server is running: python start.py")
            break
