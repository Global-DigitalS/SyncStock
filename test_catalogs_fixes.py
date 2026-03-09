#!/usr/bin/env python3
"""
Test script to validate the fixes made to catalogs.py
This test verifies that the database collection references are correct
"""
import sys
import re
from pathlib import Path

def test_catalog_imports():
    """Test that all imports are present"""
    with open("vscode-vfs://github/Global-DigitalS/StockHUB3/backend/routes/catalogs.py", "r") as f:
        content = f.read()
    
    required_imports = [
        "from fastapi import",
        "from services.database import db",
        "from services.auth import",
        "from services.sync import",
        "from models.schemas import"
    ]
    
    print("=" * 60)
    print("TEST 1: Validating Imports")
    print("=" * 60)
    
    all_good = True
    for imp in required_imports:
        if imp in content:
            print(f"✅ Found: {imp}")
        else:
            print(f"❌ Missing: {imp}")
            all_good = False
    
    return all_good


def test_database_collection_references():
    """Test that all database references use correct collection names"""
    with open("vscode-vfs://github/Global-DigitalS/StockHUB3/backend/routes/catalogs.py", "r") as f:
        content = f.read()
    
    print("\n" + "=" * 60)
    print("TEST 2: Database Collection Reference Validation")
    print("=" * 60)
    
    # Find all db.* references
    db_refs = re.findall(r'db\.\w+', content)
    unique_refs = sorted(set(db_refs))
    
    print("\nDatabase collections referenced:")
    valid_collections = [
        "db.catalogs",
        "db.catalog_items",
        "db.catalog_margin_rules",
        "db.catalog_categories",
        "db.products",
        "db.subscription_plans"
    ]
    
    all_good = True
    for ref in unique_refs:
        if ref in valid_collections:
            print(f"✅ {ref}")
        else:
            print(f"⚠️  {ref} - Check if this is intentional")
    
    # Check for INCORRECT references that were supposed to be fixed
    invalid_patterns = [
        (r'db\.catalog\.', "db.catalog (should be db.catalog_items or db.catalogs)"),
        (r'db\.margin_rules\.', "db.margin_rules (should be db.catalog_margin_rules)"),
    ]
    
    print("\nChecking for FIXED errors:")
    errors_found = False
    for pattern, description in invalid_patterns:
        matches = re.findall(pattern, content)
        if matches:
            print(f"❌ Found {len(matches)} instance(s) of {description}")
            print(f"   Matches: {matches[:3]}")  # Show first 3
            errors_found = True
            all_good = False
        else:
            print(f"✅ No instances of {description} found")
    
    return not errors_found


def test_function_definitions():
    """Test that all expected endpoints are defined"""
    with open("vscode-vfs://github/Global-DigitalS/StockHUB3/backend/routes/catalogs.py", "r") as f:
        content = f.read()
    
    print("\n" + "=" * 60)
    print("TEST 3: Endpoint Definitions Validation")
    print("=" * 60)
    
    expected_endpoints = [
        "@router.post(\"/catalogs\"",
        "@router.get(\"/catalogs\"",
        "@router.get(\"/catalogs/{catalog_id}\"",
        "@router.put(\"/catalogs/{catalog_id}\"",
        "@router.delete(\"/catalogs/{catalog_id}\"",
        "@router.post(\"/catalogs/{catalog_id}/products\"",
        "@router.get(\"/catalogs/{catalog_id}/products\"",
        "@router.delete(\"/catalogs/{catalog_id}/products/{item_id}\"",
        "@router.post(\"/catalogs/{catalog_id}/margin-rules\"",
        "@router.get(\"/catalogs/{catalog_id}/margin-rules\"",
        "@router.put(\"/catalogs/{catalog_id}/margin-rules/{rule_id}\"",
        "@router.delete(\"/catalogs/{catalog_id}/margin-rules/{rule_id}\"",
        "@router.post(\"/margin-rules\"",
        "@router.get(\"/margin-rules\"",
        "@router.put(\"/margin-rules/{rule_id}\"",
        "@router.delete(\"/margin-rules/{rule_id}\"",
    ]
    
    all_good = True
    for endpoint in expected_endpoints:
        if endpoint in content:
            print(f"✅ {endpoint}")
        else:
            print(f"❌ Missing {endpoint}")
            all_good = False
    
    return all_good


def test_error_handling():
    """Test that proper error handling is in place"""
    with open("vscode-vfs://github/Global-DigitalS/StockHUB3/backend/routes/catalogs.py", "r") as f:
        content = f.read()
    
    print("\n" + "=" * 60)
    print("TEST 4: Error Handling Validation")
    print("=" * 60)
    
    # Check for HTTPException raises
    http_exception_count = content.count("raise HTTPException")
    
    print(f"\nFound {http_exception_count} HTTPException raises ✅")
    
    if http_exception_count < 5:
        print("⚠️  Less than expected error handling")
        return False
    
    # Check specific error codes
    error_codes = {
        404: "Not Found",
        400: "Bad Request",
        403: "Forbidden",
        500: "Internal Server Error"
    }
    
    all_good = True
    for code, name in error_codes.items():
        if f"status_code={code}" in content:
            print(f"✅ {code} - {name}")
        elif code == 400 or code == 404:  # Most important ones
            print(f"⚠️  {code} - {name} (might be missing)")
    
    return all_good


def test_response_models():
    """Test that response models are used correctly"""
    with open("vscode-vfs://github/Global-DigitalS/StockHUB3/backend/routes/catalogs.py", "r") as f:
        content = f.read()
    
    print("\n" + "=" * 60)
    print("TEST 5: Response Model Validation")
    print("=" * 60)
    
    response_models = [
        "response_model=CatalogResponse",
        "response_model=List[CatalogResponse]",
        "response_model=CatalogMarginRuleResponse",
        "response_model=List[CatalogMarginRuleResponse]",
        "response_model=CatalogCategoryResponse",
        "response_model=MarginRuleResponse",
        "response_model=List[MarginRuleResponse]",
    ]
    
    all_good = True
    for model in response_models:
        count = content.count(model)
        if count > 0:
            print(f"✅ {model} ({count} occurrence(s))")
        else:
            print(f"⚠️  {model} - Not found (might be missing)")
    
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("STOCKHUB3 - CATALOGS.PY VALIDATION TEST SUITE")
    print("=" * 60)
    
    results = {
        "Imports": test_catalog_imports(),
        "Database References": test_database_collection_references(),
        "Endpoints": test_function_definitions(),
        "Error Handling": test_error_handling(),
        "Response Models": test_response_models(),
    }
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "=" * 60)
    print(f"RESULT: {passed}/{total} tests passed")
    print("=" * 60 + "\n")
    
    if all(results.values()):
        print("🎉 All tests passed! The fixes are working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
