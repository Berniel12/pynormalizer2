#!/usr/bin/env python3
"""
Test script to verify the fixes to country normalization in the ensure_country function.
This script tests various country inputs to ensure they are normalized correctly and
do not result in None values inappropriately.
"""
import sys
import os
import logging
from pprint import pprint

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the ensure_country function
from pynormalizer.utils.normalizer_helpers import ensure_country

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_ensure_country():
    """Test the ensure_country function with various inputs."""
    test_cases = [
        # Empty or None values
        (None, "Empty value"),
        ("", "Empty string"),
        
        # Valid standard country names
        ("Philippines", "Standard country name"),
        ("United States", "Standard country name"),
        ("China", "Standard country name"),
        
        # Country codes
        ("USA", "Country code"),
        ("PHL", "Philippines code"),
        ("REG", "Regional code used by ADB"),
        
        # Special cases
        ("Multinational", "Special case"),
        ("Kyrgyz", "Special case - should normalize to Kyrgyz Republic"),
        
        # Alternate spellings
        ("Vietnam", "Alternate spelling"),
        ("Viet Nam", "Alternate spelling"),
        
        # Misspellings
        ("Philipines", "Misspelling"),
        ("Bostwana", "Misspelling - should correct to Botswana"),
        
        # Project titles that contain country names
        ("Program for Integrated Rural Sanitation In Upper Egypt", "Project title"),
        
        # Text with other information
        ("Project in the Philippines for water supply", "Text with country mention"),
        
        # Values that should not be normalized to None
        ("Some Random Place", "Non-standard location"),
        ("Project Location", "Generic location"),
        
        # ADB common countries
        ("Mongolia", "ADB common country"),
        ("Papua New Guinea", "ADB common country"),
        ("Fiji", "ADB common country")
    ]
    
    # Test with just the country_value parameter
    logger.info("Testing with country_value parameter only:")
    for value, description in test_cases:
        result = ensure_country(country_value=value)
        logger.info(f"{description}: '{value}' -> '{result}'")
    
    # Test with text parameter
    logger.info("\nTesting with text parameter:")
    text_test_cases = [
        ("This project is located in the Philippines", "Text with country mention"),
        ("Water supply project in rural India", "Text with country mention"),
        ("Climate resilience in Pacific Island nations", "Text without specific country"),
        ("Infrastructure development", "Generic text")
    ]
    
    for text, description in text_test_cases:
        result = ensure_country(country_value=None, text=text)
        logger.info(f"{description}: '{text}' -> '{result}'")
    
    # Test with organization parameter
    logger.info("\nTesting with organization parameter:")
    org_test_cases = [
        ("Department of Transportation Philippines", "Organization with country mention"),
        ("National Bank of Pakistan", "Organization with country mention"),
        ("Ministry of Water Resources", "Generic organization")
    ]
    
    for org, description in org_test_cases:
        result = ensure_country(country_value=None, organization=org)
        logger.info(f"{description}: '{org}' -> '{result}'")
    
    # Test combinations of parameters
    logger.info("\nTesting combinations of parameters:")
    combo_test_cases = [
        (None, "Project in Vietnam", "Vietnamese Ministry", "Fallback to text"),
        ("", "Water project in China", "Asian Development Bank", "Empty string with fallbacks"),
        ("Philippines", "Project in Indonesia", "Department of Energy", "Valid country with contradicting fallbacks")
    ]
    
    for country, text, org, description in combo_test_cases:
        result = ensure_country(country_value=country, text=text, organization=org)
        logger.info(f"{description}: country='{country}', text='{text}', org='{org}' -> '{result}'")

def main():
    """Run the country normalization tests."""
    logger.info("Starting country normalization tests")
    test_ensure_country()
    logger.info("Tests completed")

if __name__ == "__main__":
    main()
