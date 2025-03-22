"""
Validation utilities for normalizer outputs.
"""
import re
import logging
from typing import Dict, Any, Optional, Tuple
from unidecode import unidecode

logger = logging.getLogger(__name__)

def validate_field(field_name: str, value: Any, field_type: type) -> Tuple[bool, str]:
    """Validate a single field value."""
    if value is None:
        return True, ""
    
    try:
        if not isinstance(value, field_type):
            return False, f"Invalid type for {field_name}: expected {field_type.__name__}, got {type(value).__name__}"
        return True, ""
    except Exception as e:
        return False, f"Validation error for {field_name}: {str(e)}"

def calculate_field_quality(field_name: str, value: Any) -> float:
    """Calculate quality score for a single field."""
    if value is None:
        return 0.0
        
    if isinstance(value, str):
        if not value.strip():
            return 0.0
        # Check for minimum length
        if len(value) < 3:
            return 0.3
        # Check for all caps or all lowercase
        if value.isupper() or value.islower():
            return 0.7
        return 1.0
        
    return 1.0 if value is not None else 0.0

def calculate_tender_quality(tender: Dict[str, Any]) -> float:
    """Calculate overall quality score for a tender."""
    weights = {
        'title': 1.0,
        'description': 0.8,
        'organization_name': 0.7,
        'deadline_date': 0.6,
        'estimated_value': 0.5,
        'country': 0.4,
        'document_links': 0.4,
        'contact_info': 0.3
    }
    
    total_weight = sum(weights.values())
    weighted_sum = 0.0
    
    for field, weight in weights.items():
        value = tender.get(field)
        quality = calculate_field_quality(field, value)
        weighted_sum += quality * weight
    
    return weighted_sum / total_weight

def normalize_text(text: str) -> str:
    """Normalize text by handling accents and special characters."""
    if not text:
        return ""
    
    # Convert accented characters to ASCII
    normalized = unidecode(text)
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    # Handle common special characters
    normalized = normalized.replace('&amp;', '&')
    normalized = normalized.replace('&quot;', '"')
    normalized = normalized.replace('&apos;', "'")
    
    return normalized

def detect_encoding_issues(text: str) -> Tuple[bool, str]:
    """Detect potential encoding issues in text."""
    if not text:
        return False, ""
    
    issues = []
    
    # Check for common encoding issue patterns
    if '�' in text:
        issues.append("Contains replacement character")
    if re.search(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', text):
        issues.append("Contains control characters")
    if re.search(r'â€™|â€œ|â€|Â', text):
        issues.append("Contains common UTF-8 mojibake patterns")
    
    return bool(issues), "; ".join(issues)

def validate_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
    """Validate data against a schema."""
    errors = {}
    
    for field, field_info in schema.items():
        required = field_info.get('required', False)
        field_type = field_info.get('type')
        
        value = data.get(field)
        
        if required and value is None:
            errors[field] = "Required field is missing"
            continue
            
        if value is not None and field_type:
            try:
                if not isinstance(value, field_type):
                    errors[field] = f"Invalid type: expected {field_type.__name__}, got {type(value).__name__}"
            except Exception as e:
                errors[field] = f"Validation error: {str(e)}"
    
    return len(errors) == 0, errors 