import os
import json
from typing import Dict, Any, Optional
from pynormalizer.utils.logger import logger

def get_apify_input() -> Optional[Dict[str, Any]]:
    """
    Get input data from Apify, either from the APIFY_INPUT_PATH environment variable
    or the default INPUT_PATH.
    
    Returns:
        Dictionary with Apify input data, or None if not found or unable to parse
    """
    try:
        # Try to get input path from environment, or use default
        input_path = os.environ.get('APIFY_INPUT_PATH', './input.json')
        
        # Check if file exists
        if not os.path.exists(input_path):
            logger.warning(f"Apify input file not found at {input_path}")
            return None
        
        # Read and parse input
        with open(input_path, 'r') as f:
            input_data = json.load(f)
            return input_data
            
    except Exception as e:
        logger.error(f"Error reading Apify input: {str(e)}")
        return None 