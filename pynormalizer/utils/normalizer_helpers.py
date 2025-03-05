"""
Helper functions for normalizers.
"""
import json
import logging
from typing import Any, Dict, Optional, Tuple
from datetime import datetime
from pynormalizer.models.unified_model import UnifiedTender
from pynormalizer.utils.translation import translate_to_english

logger = logging.getLogger(__name__)

def apply_translations(unified: UnifiedTender, detected_language: Optional[str] = "auto") -> UnifiedTender:
    """
    Apply translations to a unified tender record.
    
    Args:
        unified: The unified tender record
        detected_language: Detected language code or "auto" for auto-detection
        
    Returns:
        Updated unified tender with translations
    """
    # Track translation methods used
    translation_methods = {}
    
    # Translate title
    if unified.title:
        unified.title_english, method = translate_to_english(unified.title, detected_language)
        if method:
            translation_methods["title"] = method
    
    # Translate description
    if unified.description:
        unified.description_english, method = translate_to_english(unified.description, detected_language)
        if method:
            translation_methods["description"] = method
    
    # Translate organization name
    if unified.organization_name:
        unified.organization_name_english, method = translate_to_english(unified.organization_name, detected_language)
        if method:
            translation_methods["organization_name"] = method
    
    # Translate project name
    if unified.project_name:
        unified.project_name_english, method = translate_to_english(unified.project_name, detected_language)
        if method:
            translation_methods["project_name"] = method
    
    # Translate buyer
    if unified.buyer:
        unified.buyer_english, method = translate_to_english(unified.buyer, detected_language)
        if method:
            translation_methods["buyer"] = method
    
    # Store translation methods used in normalized_method field
    if translation_methods:
        unified.normalized_method = json.dumps(translation_methods)
    
    return unified

def format_for_logging(data: Dict[str, Any]) -> str:
    """
    Format data for logging, handling special types and truncating long values.
    
    Args:
        data: Dictionary of data to format
        
    Returns:
        Formatted string
    """
    result = {}
    
    # Process each field
    for key, value in data.items():
        # Skip None values
        if value is None:
            continue
            
        # Handle datetime objects
        if isinstance(value, datetime):
            result[key] = value.isoformat()
        
        # Handle dictionaries and lists
        elif isinstance(value, (dict, list)):
            try:
                # Try to serialize to JSON
                json_str = json.dumps(value, default=str)
                # Truncate if too long
                if len(json_str) > 500:
                    result[key] = json_str[:497] + "..."
                else:
                    result[key] = json_str
            except:
                result[key] = str(value)[:100]
        
        # Handle long strings
        elif isinstance(value, str) and len(value) > 300:
            result[key] = value[:297] + "..."
        
        # Regular values
        else:
            result[key] = value
    
    return json.dumps(result, indent=2, default=str)

def log_before_after(source_type: str, source_id: str, before: Dict[str, Any], after: UnifiedTender):
    """
    Log before and after data for a tender.
    
    Args:
        source_type: Source table name
        source_id: Source ID
        before: Original source data
        after: Normalized unified tender
    """
    logger.info(f"NORMALIZING {source_type.upper()} - {source_id}")
    logger.info(f"BEFORE:\n{format_for_logging(before)}")
    logger.info(f"AFTER:\n{format_for_logging(after.model_dump())}")
    logger.info(f"TRANSLATION: {after.normalized_method}")
    logger.info("-" * 80) 