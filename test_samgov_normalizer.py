#!/usr/bin/env python3
"""
Simple test script to verify the SAM.gov normalizer can handle dictionary fields for country and city.
"""
import json
from pynormalizer.normalizers.samgov_normalizer import normalize_samgov
from pprint import pprint

# Test data with dictionary fields for country and city
test_data_with_dict = {
    "opportunity_id": "test1234",
    "opportunity_title": "Test Opportunity",
    "place_of_performance": {
        "country": {"code": "LBR"},
        "city": {"name": "Monrovia"}
    },
    "opportunity_type": "Test Type",
    "opportunity_status": "Open",
    "description": "This is a test opportunity.",
    "org_key": 123  # Adding required field
}

# Test with another format
test_data_with_dict2 = {
    "opportunity_id": "test5678",
    "opportunity_title": "Another Test",
    "place_of_performance": {
        "country": {"name": "United States", "code": "USA"},
        "city": {"code": "DC", "name": "Washington"}
    },
    "opportunity_type": "Contract",
    "opportunity_status": "Active",
    "description": "Another test opportunity.",
    "org_key": 456  # Adding required field
}

print("Testing with dictionary country and city fields...")
try:
    # Test first example
    print("\nTest 1:")
    result1 = normalize_samgov(test_data_with_dict)
    print(f"Country: {result1.country}")
    print(f"City: {result1.city}")
    
    # Test second example
    print("\nTest 2:")
    result2 = normalize_samgov(test_data_with_dict2)
    print(f"Country: {result2.country}")
    print(f"City: {result2.city}")
    
    print("\nSuccessfully normalized data with dictionary fields!")
except Exception as e:
    print(f"ERROR: {e}") 