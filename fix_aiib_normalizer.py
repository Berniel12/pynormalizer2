#!/usr/bin/env python3
"""
Script to fix issues in the AIIB normalizer:
1. Incorrect parameter name in ensure_country() call ('country' instead of 'country_value')
2. determine_normalized_method() being called with a list instead of a dictionary

This script modifies the aiib_normalizer.py file in place.
"""

import os
import re
import sys
import logging
import shutil
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_aiib_normalizer.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("fix_aiib_normalizer")

def fix_aiib_normalizer_file():
    """
    Fix issues in the AIIB normalizer file.
    """
    # Define file paths
    normalizer_dir = os.path.join("pynormalizer", "normalizers")
    aiib_file_path = os.path.join(normalizer_dir, "aiib_normalizer.py")
    backup_file_path = os.path.join(normalizer_dir, "aiib_normalizer.py.bak")
    
    # Ensure the file exists
    if not os.path.exists(aiib_file_path):
        logger.error(f"Could not find file: {aiib_file_path}")
        return False
    
    # Create a backup of the original file
    logger.info(f"Creating backup of {aiib_file_path} to {backup_file_path}")
    shutil.copy2(aiib_file_path, backup_file_path)
    
    # Read the file content
    with open(aiib_file_path, 'r') as f:
        content = f.read()
    
    # Fix 1: Replace 'country=' with 'country_value=' in ensure_country() call
    logger.info("Fixing ensure_country() parameter name...")
    ensure_country_pattern = r'(country\s*=\s*ensure_country\(\s*country\s*=)'
    replacement = r'\1'.replace('country=', 'country_value=')
    content_fixed1 = re.sub(ensure_country_pattern, replacement, content)
    
    # Count replacements for ensure_country
    replacements_count1 = content.count("ensure_country(\n                country=") - content_fixed1.count("ensure_country(\n                country=")
    logger.info(f"Made {replacements_count1} replacements for ensure_country parameter")
    
    # Fix 2: Modify determine_normalized_method() call to use a dictionary
    logger.info("Fixing determine_normalized_method() call...")
    method_pattern = r'normalized_method\s*=\s*determine_normalized_method\(extraction_methods\)'
    method_replacement = r'''# Convert extraction_methods list to a dictionary format that determine_normalized_method expects
        normalized_method_data = {
            "source_table": "aiib",
            "extraction_methods": extraction_methods
        }
        normalized_method = determine_normalized_method(normalized_method_data)'''
    content_fixed2 = re.sub(method_pattern, method_replacement, content_fixed1)
    
    # Count replacements for determine_normalized_method
    replacements_count2 = content_fixed1.count("normalized_method = determine_normalized_method(extraction_methods)") - content_fixed2.count("normalized_method = determine_normalized_method(extraction_methods)")
    logger.info(f"Made {replacements_count2} replacements for determine_normalized_method call")
    
    # Manual approach if regex approach doesn't work well
    if replacements_count1 == 0 or replacements_count2 == 0:
        logger.warning("Regex replacements not effective, attempting manual string replacements...")
        
        # Manual fix for ensure_country
        content_fixed2 = content_fixed2.replace(
            "country = ensure_country(\n                country=country_string,", 
            "country = ensure_country(\n                country_value=country_string,"
        )
        
        # Manual fix for determine_normalized_method
        content_fixed2 = content_fixed2.replace(
            "normalized_method = determine_normalized_method(extraction_methods)",
            """# Convert extraction_methods list to a dictionary format that determine_normalized_method expects
        normalized_method_data = {
            "source_table": "aiib",
            "extraction_methods": extraction_methods
        }
        normalized_method = determine_normalized_method(normalized_method_data)"""
        )
    
    # Write the fixed content back to the file
    with open(aiib_file_path, 'w') as f:
        f.write(content_fixed2)
    
    logger.info(f"Successfully updated {aiib_file_path}")
    return True

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Fix issues in the AIIB normalizer")
    args = parser.parse_args()
    
    try:
        if fix_aiib_normalizer_file():
            logger.info("Successfully fixed AIIB normalizer file")
        else:
            logger.error("Failed to fix AIIB normalizer file")
            sys.exit(1)
    except Exception as e:
        logger.exception(f"Error fixing AIIB normalizer: {e}")
        sys.exit(1)
    
    logger.info("Fix completed successfully")

if __name__ == "__main__":
    main() 