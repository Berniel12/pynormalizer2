from pynormalizer.utils.normalizer_helpers import ensure_country

def test_country_extraction():
    """
    Test the country extraction functionality to ensure it works for various scenarios.
    """
    print("Testing country extraction functionality...\n")
    
    # Test cases
    test_cases = [
        # Direct country value
        {
            "name": "Direct country value",
            "country": "Kenya",
            "text": None,
            "organization": None,
            "email": None,
            "language": None,
            "expected": "Kenya"
        },
        # Country from text
        {
            "name": "Country from text",
            "country": None,
            "text": "This project is located in Rwanda and will be implemented by the Ministry of Infrastructure.",
            "organization": None,
            "email": None,
            "language": None,
            "expected": "Rwanda"
        },
        # Country from organization
        {
            "name": "Country from organization name",
            "country": None,
            "text": None,
            "organization": "KENYA - Ministry of Transport",
            "email": None,
            "language": None,
            "expected": "KENYA"
        },
        # Country from email domain
        {
            "name": "Country from email domain",
            "country": None,
            "text": None,
            "organization": None,
            "email": "contact@mininfra.gov.rw",
            "language": None,
            "expected": "Rwanda"
        },
        # Country from language
        {
            "name": "Country from language",
            "country": None,
            "text": None,
            "organization": None,
            "email": None,
            "language": "fr",
            "expected": "France"
        },
        # Fallback to Unknown
        {
            "name": "Fallback to Unknown",
            "country": None,
            "text": None,
            "organization": None,
            "email": None,
            "language": None,
            "expected": "Unknown"
        },
        # Complex case with multiple possible sources
        {
            "name": "Multiple sources - should use direct country",
            "country": "Tanzania",
            "text": "This project is in Kenya",
            "organization": "UGANDA - Ministry of Health",
            "email": "info@mininfra.gov.rw",
            "language": "fr",
            "expected": "Tanzania"
        }
    ]
    
    # Run tests
    for i, test_case in enumerate(test_cases):
        result = ensure_country(
            country=test_case["country"],
            text=test_case["text"],
            organization=test_case["organization"],
            email=test_case["email"],
            language=test_case["language"]
        )
        
        success = result == test_case["expected"]
        print(f"Test {i+1}: {test_case['name']}")
        print(f"  Input: country={test_case['country']}, text_sample={test_case['text'][:20] + '...' if test_case['text'] else None}")
        print(f"  Expected: {test_case['expected']}")
        print(f"  Result: {result}")
        print(f"  Status: {'✅ PASS' if success else '❌ FAIL'}")
        print()
    
    print("Testing complete!")

if __name__ == "__main__":
    test_country_extraction() 