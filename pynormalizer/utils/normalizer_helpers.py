"""
Helper functions for normalizers.
"""
import json
import logging
import re
from typing import Any, Dict, Optional, Tuple, List
from datetime import datetime
from pynormalizer.models.unified_model import UnifiedTender
from pynormalizer.utils.translation import translate_to_english

logger = logging.getLogger(__name__)

def normalize_document_links(links: Any) -> List[Dict[str, str]]:
    """
    Normalize document links to a consistent format.
    
    Args:
        links: Document links in various formats
        
    Returns:
        List of dictionaries with standardized format
    """
    if not links:
        return []
        
    normalized_links = []
    
    # Handle string format (single URL)
    if isinstance(links, str):
        try:
            # Check if it's a JSON string
            parsed = json.loads(links)
            if isinstance(parsed, list):
                links = parsed
            else:
                # Single URL string
                normalized_links.append({
                    "url": links,
                    "type": "unknown"
                })
                return normalized_links
        except (json.JSONDecodeError, ValueError):
            # Single URL string
            normalized_links.append({
                "url": links,
                "type": "unknown"
            })
            return normalized_links
    
    # Handle list format
    if isinstance(links, list):
        for item in links:
            # List of strings (URLs)
            if isinstance(item, str):
                normalized_links.append({
                    "url": item,
                    "type": "unknown"
                })
            # List of dictionaries
            elif isinstance(item, dict) and "link" in item:
                normalized_links.append({
                    "url": item["link"],
                    "type": item.get("type", "unknown"),
                    "description": item.get("description", None)
                })
            # Other dictionary format
            elif isinstance(item, dict) and "url" in item:
                normalized_links.append({
                    "url": item["url"],
                    "type": item.get("type", "unknown"),
                    "description": item.get("description", None)
                })
            # Other dictionary without standard keys
            elif isinstance(item, dict):
                for key, value in item.items():
                    if isinstance(value, str) and (value.startswith("http") or ".pdf" in value.lower()):
                        normalized_links.append({
                            "url": value,
                            "type": key
                        })
    
    # Handle dictionary format
    elif isinstance(links, dict):
        # TED EU format with language-specific URLs
        pdf_extensions = [".pdf", ".PDF"]
        xml_extensions = [".xml", ".XML"]
        html_extensions = [".html", ".htm", ".HTML", ".HTM"]
        
        # Process different sections
        for section, content in links.items():
            if isinstance(content, dict):
                for lang, url in content.items():
                    link_type = "unknown"
                    if section.lower() == "pdf" or any(url.endswith(ext) for ext in pdf_extensions):
                        link_type = "pdf"
                    elif section.lower() == "xml" or any(url.endswith(ext) for ext in xml_extensions):
                        link_type = "xml"
                    elif section.lower() == "html" or any(url.endswith(ext) for ext in html_extensions):
                        link_type = "html"
                    
                    normalized_links.append({
                        "url": url,
                        "type": link_type,
                        "language": lang
                    })
            elif isinstance(content, str):
                link_type = "unknown"
                if any(content.endswith(ext) for ext in pdf_extensions):
                    link_type = "pdf"
                elif any(content.endswith(ext) for ext in xml_extensions):
                    link_type = "xml"
                elif any(content.endswith(ext) for ext in html_extensions):
                    link_type = "html"
                
                normalized_links.append({
                    "url": content,
                    "type": link_type
                })
    
    return normalized_links

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
    already_english_fields = []
    
    # Translate title
    if unified.title:
        unified.title_english, method = translate_to_english(unified.title, detected_language)
        if method:
            translation_methods["title"] = method
            if method == "already_english":
                already_english_fields.append("title")
    
    # Translate description
    if unified.description:
        unified.description_english, method = translate_to_english(unified.description, detected_language)
        if method:
            translation_methods["description"] = method
            if method == "already_english":
                already_english_fields.append("description")
    
    # Translate organization name
    if unified.organization_name:
        unified.organization_name_english, method = translate_to_english(unified.organization_name, detected_language)
        if method:
            translation_methods["organization_name"] = method
            if method == "already_english":
                already_english_fields.append("organization_name")
    
    # Translate project name
    if unified.project_name:
        unified.project_name_english, method = translate_to_english(unified.project_name, detected_language)
        if method:
            translation_methods["project_name"] = method
            if method == "already_english":
                already_english_fields.append("project_name")
    
    # Translate buyer
    if unified.buyer:
        unified.buyer_english, method = translate_to_english(unified.buyer, detected_language)
        if method:
            translation_methods["buyer"] = method
            if method == "already_english":
                already_english_fields.append("buyer")
    
    # Store translation methods used in normalized_method field
    if translation_methods:
        unified.normalized_method = json.dumps(translation_methods)
    
    # Set fallback_reason field if fields were already in English
    if already_english_fields:
        unified.fallback_reason = json.dumps({field: "already_english" for field in already_english_fields})
    
    return unified

def extract_financial_info(text: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Extract estimated value and currency from text.
    
    Args:
        text: Text to extract from
        
    Returns:
        Tuple of (estimated_value, currency)
    """
    if not text:
        return None, None
        
    # Look for currency symbols and amounts
    currency_patterns = {
        'USD': r'US\$\s*([\d,]+(?:\.\d+)?)|USD\s*([\d,]+(?:\.\d+)?)|(\$\s*[\d,]+(?:\.\d+)?)',
        'EUR': r'EUR\s*([\d,]+(?:\.\d+)?)|€\s*([\d,]+(?:\.\d+)?)',
        'GBP': r'GBP\s*([\d,]+(?:\.\d+)?)|£\s*([\d,]+(?:\.\d+)?)',
        'CAD': r'CAD\s*([\d,]+(?:\.\d+)?)',
        'AUD': r'AUD\s*([\d,]+(?:\.\d+)?)',
        'INR': r'INR\s*([\d,]+(?:\.\d+)?)|Rs\.\s*([\d,]+(?:\.\d+)?)'
    }
    
    for currency, pattern in currency_patterns.items():
        matches = re.findall(pattern, text)
        if matches:
            # Flatten matches and find first non-empty group
            for match in matches:
                if isinstance(match, tuple):
                    for group in match:
                        if group:
                            # Remove commas and convert to float
                            try:
                                value = float(group.replace(',', ''))
                                return value, currency
                            except (ValueError, TypeError):
                                pass
    
    # Look for patterns like "1.5 million USD" or "USD 1.5 million"
    million_patterns = [
        r'(\d+(?:\.\d+)?)\s*million\s*(USD|EUR|GBP|CAD|AUD|INR|\$|€|£)',
        r'(USD|EUR|GBP|CAD|AUD|INR|\$|€|£)\s*(\d+(?:\.\d+)?)\s*million'
    ]
    
    for pattern in million_patterns:
        matches = re.findall(pattern, text)
        if matches:
            for match in matches:
                try:
                    value = float(match[0]) * 1000000
                    currency = match[1]
                    # Map symbols to currency codes
                    if currency == "$":
                        currency = "USD"
                    elif currency == "€":
                        currency = "EUR"
                    elif currency == "£":
                        currency = "GBP"
                    return value, currency
                except (ValueError, TypeError, IndexError):
                    pass
                    
    return None, None

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