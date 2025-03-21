"""
Standardization functions for tender data normalization.
"""
import re
import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
import difflib

logger = logging.getLogger(__name__)

# Try to import pycountry, but make it optional with a fallback
PYCOUNTRY_AVAILABLE = False
try:
    import pycountry
    PYCOUNTRY_AVAILABLE = True
    logger.info("pycountry module loaded successfully")
except ImportError:
    logger.warning("pycountry module not available, using simplified country normalization")

# Precompile regex patterns for performance
WHITESPACE_PATTERN = re.compile(r'\s+')
HTML_TAG_PATTERN = re.compile(r'<[^>]+>')
CURRENCY_PATTERN = re.compile(r'([A-Z]{3})\s*(\d+(?:,\d{3})*(?:\.\d+)?)|(\d+(?:,\d{3})*(?:\.\d+)?)\s*([A-Z]{3})')
EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
PHONE_PATTERN = re.compile(r'(?:\+\d{1,3}[- ]?)?\(?\d{2,4}\)?[- ]?\d{3,4}[- ]?\d{3,4}')
URL_PATTERN = re.compile(r'https?://(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?')

# Title standardization
TITLE_CONFIG = {
    'min_length': 25,
    'max_length': 300,
    'remove_prefixes': [
        r'^tender\s+for\s+',
        r'^request\s+for\s+',
        r'^invitation\s+to\s+',
        r'^notice\s+of\s+',
        r'^procurement\s+of\s+',
        r'^supply\s+of\s+',
        r'^provision\s+of\s+',
        r'^contract\s+for\s+',
        r'^bid\s+for\s+',
        r'^proposal\s+for\s+'
    ],
    'remove_suffixes': [
        r'\s+\d{4}$',  # Year at end
        r'\s+-\s*ref\s*\d+$',  # Reference numbers
        r'\s+\([^)]+\)$'  # Parenthetical notes
    ]
}

# Description standardization
DESCRIPTION_CONFIG = {
    'min_length': 50,
    'max_length': 5000,
    'sections': [
        'Background',
        'Scope of Work',
        'Requirements',
        'Eligibility',
        'Submission Details',
        'Contact Information',
        'Technical Specifications',
        'Evaluation Criteria',
        'Timeline',
        'Terms and Conditions'
    ],
    'required_sections': [
        'Scope of Work',
        'Requirements',
        'Submission Details'
    ]
}

# Country standardization with expanded mappings
COUNTRY_MAPPING = {
    # French to English mappings (expanded)
    'Algérie': 'Algeria',
    'Allemagne': 'Germany',
    'Bénin': 'Benin',
    'Burkina Faso': 'Burkina Faso',
    'Cameroun': 'Cameroon',
    'Comores': 'Comoros',
    'Congo': 'Congo',
    'Côte d\'Ivoire': 'Ivory Coast',
    'Egypte': 'Egypt',
    'Éthiopie': 'Ethiopia',
    'Guinée': 'Guinea',
    'Guinée-Bissau': 'Guinea-Bissau',
    'Guinée Équatoriale': 'Equatorial Guinea',
    'Maroc': 'Morocco',
    'Maurice': 'Mauritius',
    'Mauritanie': 'Mauritania',
    'Mozambique': 'Mozambique',
    'Niger': 'Niger',
    'République centrafricaine': 'Central African Republic',
    'République du Sénégal': 'Senegal',
    'République du Bénin': 'Benin',
    'République du Cameroun': 'Cameroon',
    'République de Côte d\'Ivoire': 'Ivory Coast',
    'République démocratique du Congo': 'Democratic Republic of the Congo',
    'Sénégal': 'Senegal',
    'Seychelles': 'Seychelles',
    'Tanzanie': 'Tanzania',
    'Tchad': 'Chad',
    'Togo': 'Togo',
    'Tunisie': 'Tunisia',
    
    # Spanish to English mappings
    'Argentina': 'Argentina',
    'Bolivia': 'Bolivia',
    'Brasil': 'Brazil',
    'Chile': 'Chile',
    'Colombia': 'Colombia',
    'Costa Rica': 'Costa Rica',
    'Cuba': 'Cuba',
    'Ecuador': 'Ecuador',
    'El Salvador': 'El Salvador',
    'España': 'Spain',
    'Guatemala': 'Guatemala',
    'Honduras': 'Honduras',
    'México': 'Mexico',
    'Nicaragua': 'Nicaragua',
    'Panamá': 'Panama',
    'Paraguay': 'Paraguay',
    'Perú': 'Peru',
    'República del Perú': 'Peru',
    'República de Chile': 'Chile',
    'República de Colombia': 'Colombia',
    'República Dominicana': 'Dominican Republic',
    'Uruguay': 'Uruguay',
    'Venezuela': 'Venezuela',
    
    # Portuguese to English mappings
    'Angola': 'Angola',
    'Brasil': 'Brazil',
    'Cabo Verde': 'Cape Verde',
    'Guiné-Bissau': 'Guinea-Bissau',
    'Moçambique': 'Mozambique',
    'Portugal': 'Portugal',
    'São Tomé e Príncipe': 'Sao Tome and Principe',
    'Timor-Leste': 'East Timor',
    'República de Angola': 'Angola',
    'República de Moçambique': 'Mozambique',
    
    # Common abbreviations
    'USA': 'United States',
    'U.S.A.': 'United States',
    'US': 'United States',
    'U.S.': 'United States',
    'UK': 'United Kingdom',
    'U.K.': 'United Kingdom',
    'UAE': 'United Arab Emirates',
    'U.A.E.': 'United Arab Emirates',
    
    # Regional groupings
    'EU': 'European Union',
    'MENA': 'Middle East and North Africa',
    'APAC': 'Asia Pacific',
    'LAC': 'Latin America and Caribbean',
    
    # Special cases with mixed case formats
    'ARGENTINA': 'Argentina',
    'BOLIVIA': 'Bolivia',
    'BRAZIL': 'Brazil',
    'BARBADOS': 'Barbados',
    'BAHAMAS': 'Bahamas',
    'BELIZE': 'Belize',
    'Unknown': 'Unknown'
}

# ISO Code Mappings (fallback for when pycountry is not available)
ISO_CODE_MAPPING = {
    'United States': {'alpha_2': 'US', 'alpha_3': 'USA'},
    'United Kingdom': {'alpha_2': 'GB', 'alpha_3': 'GBR'},
    'Canada': {'alpha_2': 'CA', 'alpha_3': 'CAN'},
    'Australia': {'alpha_2': 'AU', 'alpha_3': 'AUS'},
    'Germany': {'alpha_2': 'DE', 'alpha_3': 'DEU'},
    'France': {'alpha_2': 'FR', 'alpha_3': 'FRA'},
    'Italy': {'alpha_2': 'IT', 'alpha_3': 'ITA'},
    'Spain': {'alpha_2': 'ES', 'alpha_3': 'ESP'},
    'China': {'alpha_2': 'CN', 'alpha_3': 'CHN'},
    'Japan': {'alpha_2': 'JP', 'alpha_3': 'JPN'},
    'Brazil': {'alpha_2': 'BR', 'alpha_3': 'BRA'},
    'India': {'alpha_2': 'IN', 'alpha_3': 'IND'},
    'Russia': {'alpha_2': 'RU', 'alpha_3': 'RUS'},
    'South Africa': {'alpha_2': 'ZA', 'alpha_3': 'ZAF'},
    'Mexico': {'alpha_2': 'MX', 'alpha_3': 'MEX'},
    'Argentina': {'alpha_2': 'AR', 'alpha_3': 'ARG'},
    'Chile': {'alpha_2': 'CL', 'alpha_3': 'CHL'},
    'Colombia': {'alpha_2': 'CO', 'alpha_3': 'COL'},
    'Peru': {'alpha_2': 'PE', 'alpha_3': 'PER'},
    'Nigeria': {'alpha_2': 'NG', 'alpha_3': 'NGA'},
    'Kenya': {'alpha_2': 'KE', 'alpha_3': 'KEN'},
    'Egypt': {'alpha_2': 'EG', 'alpha_3': 'EGY'},
    'Morocco': {'alpha_2': 'MA', 'alpha_3': 'MAR'},
    'Tanzania': {'alpha_2': 'TZ', 'alpha_3': 'TZA'},
    'Ethiopia': {'alpha_2': 'ET', 'alpha_3': 'ETH'},
    'Ghana': {'alpha_2': 'GH', 'alpha_3': 'GHA'},
    'Ivory Coast': {'alpha_2': 'CI', 'alpha_3': 'CIV'},
    'Senegal': {'alpha_2': 'SN', 'alpha_3': 'SEN'},
    'Algeria': {'alpha_2': 'DZ', 'alpha_3': 'DZA'},
    'Tunisia': {'alpha_2': 'TN', 'alpha_3': 'TUN'}
}

# Currency validation
CURRENCY_CONFIG = {
    'major_currencies': ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'CAD', 'CNY', 'INR', 'BRL', 'ZAR', 'RUB'],
    'min_value': 100,  # Minimum reasonable tender value
    'max_value': 1000000000000  # Maximum reasonable tender value (1 trillion)
}

# CPV code validation
CPV_PATTERN = re.compile(r'^\d{8}-\d$')

# NUTS code validation
NUTS_PATTERN = re.compile(r'^[A-Z]{2}[A-Z0-9]{0,3}$')

# Organization name extraction patterns
ORGANIZATION_PATTERNS = [
    r'(?:client|buyer|contracting authority|organization|entity):\s*([A-Za-z0-9\s\.,&\-\'()]+)',
    r'(?:for|by)\s+(?:the)?\s*([A-Za-z0-9\s\.,&\-\'()]{5,50})',
    r'([A-Za-z0-9\s\.,&\-\'()]{5,50})(?:\s+is\s+seeking|\s+invites|\s+requests)'
]

def validate_cpv_code(cpv_code: str) -> Tuple[bool, List[str]]:
    """Validate CPV (Common Procurement Vocabulary) code."""
    if not cpv_code:
        return False, ["Empty CPV code"]
    
    issues = []
    if not CPV_PATTERN.match(cpv_code):
        issues.append(f"Invalid CPV code format: {cpv_code}")
        return False, issues
    
    # Additional validation could be added here for valid CPV ranges
    return len(issues) == 0, issues

def validate_nuts_code(nuts_code: str) -> Tuple[bool, List[str]]:
    """Validate NUTS (Nomenclature of Territorial Units for Statistics) code."""
    if not nuts_code:
        return False, ["Empty NUTS code"]
    
    issues = []
    if not NUTS_PATTERN.match(nuts_code):
        issues.append(f"Invalid NUTS code format: {nuts_code}")
        return False, issues
    
    # Additional validation could be added here for valid NUTS regions
    return len(issues) == 0, issues

def validate_currency_value(value: float, currency: str) -> Tuple[bool, List[str]]:
    """Validate currency value is within reasonable range."""
    if not value or not currency:
        return False, ["Missing value or currency"]
    
    issues = []
    if value < CURRENCY_CONFIG['min_value']:
        issues.append(f"Value {value} {currency} is below minimum threshold")
    if value > CURRENCY_CONFIG['max_value']:
        issues.append(f"Value {value} {currency} exceeds maximum threshold")
    
    if currency not in CURRENCY_CONFIG['major_currencies']:
        issues.append(f"Non-major currency: {currency}")
    
    return len(issues) == 0, issues

def standardize_title(title: str) -> Tuple[str, Dict[str, Any]]:
    """
    Standardize the title of a tender.
    
    Args:
        title: Original title string
        
    Returns:
        Tuple of (standardized_title, validation_info)
    """
    if not title:
        return "", {"valid": False, "issues": ["Empty title"]}
    
    # Remove HTML tags if present
    title = re.sub(HTML_TAG_PATTERN, '', title)
    
    # Normalize whitespace
    title = re.sub(WHITESPACE_PATTERN, ' ', title).strip()
    
    # Remove common prefixes
    for prefix in TITLE_CONFIG['remove_prefixes']:
        title = re.sub(prefix, '', title, flags=re.IGNORECASE)
    
    # Remove common suffixes
    for suffix in TITLE_CONFIG['remove_suffixes']:
        title = re.sub(suffix, '', title, flags=re.IGNORECASE)
    
    # Strip again after removing prefixes/suffixes
    title = title.strip()
    
    # Validate length constraints
    issues = []
    if len(title) < TITLE_CONFIG['min_length']:
        issues.append(f"Title length {len(title)} below minimum {TITLE_CONFIG['min_length']}")
    elif len(title) > TITLE_CONFIG['max_length']:
        issues.append(f"Title length {len(title)} exceeds maximum {TITLE_CONFIG['max_length']}")
        # Truncate if too long
        title = title[:TITLE_CONFIG['max_length']]
    
    # Capitalize first letter of each sentence
    title = '. '.join(s.capitalize() for s in title.split('. '))
    
    # First letter should always be capitalized 
    if title and len(title) > 0:
        title = title[0].upper() + title[1:]
    
    return title, {"valid": len(issues) == 0, "issues": issues}

def structure_description(description: str) -> Tuple[str, Dict[str, Any]]:
    """
    Structure and standardize a tender description.
    
    Args:
        description: Original description string
        
    Returns:
        Tuple of (structured_description, validation_info)
    """
    if not description:
        return "", {"valid": False, "issues": ["Empty description"]}
    
    # Remove HTML tags if present
    description = re.sub(HTML_TAG_PATTERN, '', description)
    
    # Normalize whitespace
    description = re.sub(WHITESPACE_PATTERN, ' ', description).strip()
    
    # Validate length constraints
    issues = []
    if len(description) < DESCRIPTION_CONFIG['min_length']:
        issues.append(f"Description length {len(description)} below minimum {DESCRIPTION_CONFIG['min_length']}")
    elif len(description) > DESCRIPTION_CONFIG['max_length']:
        issues.append(f"Description length {len(description)} exceeds maximum {DESCRIPTION_CONFIG['max_length']}")
        # Truncate if too long
        description = description[:DESCRIPTION_CONFIG['max_length']]
    
    # Check for section headers
    identified_sections = []
    for section in DESCRIPTION_CONFIG['sections']:
        pattern = re.compile(rf'\b{re.escape(section)}\b[:\s-]', re.IGNORECASE)
        if pattern.search(description):
            identified_sections.append(section)
    
    # Check for missing required sections
    missing_sections = []
    for required in DESCRIPTION_CONFIG['required_sections']:
        if required not in identified_sections:
            missing_sections.append(required)
    
    if missing_sections:
        issues.append(f"Missing required sections: {', '.join(missing_sections)}")
    
    return description, {
        "valid": len(issues) == 0, 
        "issues": issues,
        "identified_sections": identified_sections,
        "missing_sections": missing_sections
    }

def normalize_country(country: Optional[str]) -> Tuple[Optional[str], Optional[str], Optional[str], Dict[str, Any]]:
    """
    Normalize country name to standard English name with ISO codes.
    Handles direct mappings and fuzzy searches.
    
    Args:
        country: Country name in any format or language
        
    Returns:
        Tuple of (normalized_name, iso_code_2, iso_code_3, info_dict)
    """
    if not country:
        return None, None, None, {"valid": False, "issues": ["Empty country value"]}
    
    # Normalize whitespace and capitalization
    country = re.sub(WHITESPACE_PATTERN, ' ', str(country)).strip()
    
    # Direct mapping for known variations
    if country in COUNTRY_MAPPING:
        normalized = COUNTRY_MAPPING[country]
        if normalized == "Unknown":
            return None, None, None, {"valid": False, "issues": ["Country mapped to Unknown"]}
    else:
        # Try case-insensitive mapping
        country_lower = country.lower()
        for known_country, mapped_country in COUNTRY_MAPPING.items():
            if known_country.lower() == country_lower:
                normalized = mapped_country
                break
        else:
            # If not found in mapping, keep as is for now
            normalized = country
    
    # Get ISO codes using pycountry if available
    iso_code_2 = None
    iso_code_3 = None
    issues = []
    
    if PYCOUNTRY_AVAILABLE:
        # Try exact match first
        try:
            country_obj = pycountry.countries.get(name=normalized)
            if not country_obj:
                # Try fuzzy search if exact match fails
                try:
                    matches = pycountry.countries.search_fuzzy(normalized)
                    if matches:
                        country_obj = matches[0]
                    else:
                        issues.append(f"No country match found for: {normalized}")
                        country_obj = None
                except (LookupError, AttributeError) as e:
                    issues.append(f"Fuzzy search error: {str(e)}")
                    country_obj = None
                
            if country_obj:
                normalized = country_obj.name
                iso_code_2 = country_obj.alpha_2
                iso_code_3 = country_obj.alpha_3
        except (LookupError, AttributeError) as e:
            issues.append(f"pycountry lookup error: {str(e)}")
    else:
        # Fallback to ISO mapping dictionary if pycountry not available
        if normalized in ISO_CODE_MAPPING:
            iso_code_2 = ISO_CODE_MAPPING[normalized]['alpha_2']
            iso_code_3 = ISO_CODE_MAPPING[normalized]['alpha_3']
        else:
            # Try fuzzy matching with difflib
            matches = difflib.get_close_matches(normalized, ISO_CODE_MAPPING.keys(), n=1, cutoff=0.8)
            if matches:
                best_match = matches[0]
                normalized = best_match
                iso_code_2 = ISO_CODE_MAPPING[best_match]['alpha_2']
                iso_code_3 = ISO_CODE_MAPPING[best_match]['alpha_3']
            else:
                issues.append(f"No country match found for: {normalized} (using fallback ISO mapping)")
    
    # Final validation
    valid = bool(normalized and iso_code_2 and iso_code_3 and not issues)
    
    return normalized, iso_code_2, iso_code_3, {
        "valid": valid,
        "issues": issues,
        "original": country,
        "normalized": normalized,
        "iso_code_2": iso_code_2,
        "iso_code_3": iso_code_3
    }

def extract_contact_info(text: str) -> Optional[Dict[str, Any]]:
    """Extract contact information from text."""
    if not text:
        return None
    
    contact_info = {}
    
    # Extract email addresses
    emails = EMAIL_PATTERN.findall(text)
    if emails:
        contact_info['email'] = emails[0]  # Take the first email
    
    # Extract phone numbers
    phones = PHONE_PATTERN.findall(text)
    if phones:
        contact_info['phone'] = phones[0]  # Take the first phone
    
    # Extract URLs
    urls = URL_PATTERN.findall(text)
    if urls:
        contact_info['url'] = urls[0]  # Take the first URL
    
    return contact_info if contact_info else None

def extract_organization_name(text: str) -> Optional[str]:
    """Extract organization name from text using advanced patterns."""
    if not text:
        return None
    
    for pattern in ORGANIZATION_PATTERNS:
        matches = re.search(pattern, text, re.IGNORECASE)
        if matches:
            org_name = matches.group(1).strip()
            # Clean up the organization name
            org_name = re.sub(r'\s+', ' ', org_name)
            if len(org_name) > 5:  # Ensure minimum length
                return org_name
    
    return None

def validate_translation_quality(original: str, translated: str, language: str) -> Dict[str, Any]:
    """
    Validate the quality of translation.
    
    Args:
        original: Original text
        translated: Translated text
        language: Source language code
        
    Returns:
        Dictionary with validation info
    """
    if not original or not translated:
        return {
            "valid": False,
            "confidence": 0.0,
            "issues": ["Missing original or translated text"]
        }
    
    issues = []
    
    # Check for unchanged text (indicating failed translation)
    if original.lower() == translated.lower():
        issues.append("Translation is identical to original")
        return {
            "valid": False,
            "confidence": 0.0,
            "issues": issues
        }
    
    # Check for reasonable length ratio
    # Different languages have different typical expansion/contraction ratios
    expansion_ratios = {
        'fr': (0.8, 1.3),  # French typically expands 10-30% from English
        'es': (0.8, 1.4),  # Spanish can expand up to 30-40%
        'de': (0.7, 1.5),  # German can expand up to 40-50%
        'it': (0.9, 1.3),  # Italian typically expands 15-30%
        'pt': (0.8, 1.3),  # Portuguese similar to Spanish
        'ru': (0.7, 1.3),  # Russian can be shorter or longer
        'zh': (0.6, 0.8),  # Chinese is typically 30-40% shorter
        'ja': (0.6, 0.8),  # Japanese is typically 30-40% shorter
        'ar': (0.6, 1.2)   # Arabic can vary widely
    }
    
    # Default ratio if language not specified
    min_ratio, max_ratio = expansion_ratios.get(language, (0.5, 2.0))
    
    length_ratio = len(translated) / len(original) if len(original) > 0 else 0
    
    if length_ratio < min_ratio:
        issues.append(f"Translation is too short ({length_ratio:.2f}x)")
    elif length_ratio > max_ratio:
        issues.append(f"Translation is too long ({length_ratio:.2f}x)")
    
    # Check for untranslated fragments (for non-Latin script languages)
    if language in ['zh', 'ja', 'ko', 'ru', 'ar', 'th']:
        latin_char_ratio_original = sum(1 for c in original if ord('a') <= ord(c.lower()) <= ord('z')) / len(original) if len(original) > 0 else 0
        latin_char_ratio_translated = sum(1 for c in translated if ord('a') <= ord(c.lower()) <= ord('z')) / len(translated) if len(translated) > 0 else 0
        
        if latin_char_ratio_original > 0.7 and latin_char_ratio_translated < 0.3:
            issues.append("Possible mistranslation: script change from Latin to non-Latin")
        elif latin_char_ratio_original < 0.3 and latin_char_ratio_translated < 0.7:
            issues.append("Possible untranslated content: non-Latin script not converted")
    
    # Calculate confidence score
    confidence = 1.0
    
    # Deduct for each issue
    confidence -= len(issues) * 0.2
    
    # Adjust for length ratio
    if min_ratio <= length_ratio <= max_ratio:
        # Ideal ratio is around 1.0 for most language pairs
        confidence += 0.2 * (1.0 - abs(1.0 - length_ratio))
    
    # Ensure bounds
    confidence = max(0.0, min(1.0, confidence))
    
    return {
        "valid": len(issues) == 0,
        "confidence": confidence,
        "issues": issues
    }

def calculate_data_quality_score(tender: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate overall data quality score with enhanced validation."""
    scores = {
        "overall": 0.0,
        "completeness": 0.0,
        "consistency": 0.0,
        "translation": 0.0,
        "validation": 0.0,
        "issues": []
    }
    
    # Check required fields
    required_fields = [
        'title', 'description', 'status', 'publication_date',
        'country', 'organization_name'
    ]
    
    present_fields = sum(1 for field in required_fields if tender.get(field))
    scores["completeness"] = present_fields / len(required_fields)
    
    # Validate CPV and NUTS codes if present
    if tender.get('cpv_codes'):
        for cpv in tender.get('cpv_codes', []):
            valid, issues = validate_cpv_code(cpv)
            if not valid:
                scores["issues"].extend(issues)
    
    if tender.get('nuts_code'):
        valid, issues = validate_nuts_code(tender.get('nuts_code'))
        if not valid:
            scores["issues"].extend(issues)
    
    # Validate currency values
    if tender.get('estimated_value') and tender.get('currency'):
        valid, issues = validate_currency_value(
            tender['estimated_value'],
            tender['currency']
        )
        if not valid:
            scores["issues"].extend(issues)
    
    # Check translation quality if applicable
    if tender.get('language') and tender['language'] != 'en':
        translation_fields = [
            ('title', 'title_english'),
            ('description', 'description_english'),
            ('organization_name', 'organization_name_english')
        ]
        
        translation_scores = []
        for orig_field, trans_field in translation_fields:
            if tender.get(orig_field) and tender.get(trans_field):
                validation = validate_translation_quality(
                    tender[orig_field],
                    tender[trans_field],
                    tender['language']
                )
                translation_scores.append(validation["confidence"])
        
        scores["translation"] = sum(translation_scores) / len(translation_scores) if translation_scores else 0.0
    else:
        scores["translation"] = 1.0  # Perfect score for English content
    
    # Enhanced consistency checks
    consistency_checks = [
        lambda t: bool(t.get('status') and t.get('deadline_date')),
        lambda t: bool(t.get('estimated_value') and t.get('currency')),
        lambda t: bool(t.get('country') and t.get('city')),
        lambda t: bool(t.get('organization_name') and t.get('contact_email')),
        lambda t: bool(t.get('procurement_method') and t.get('tender_type')),
        lambda t: bool(t.get('publication_date') and t.get('deadline_date') and 
                      isinstance(t.get('publication_date'), datetime) and
                      isinstance(t.get('deadline_date'), datetime) and
                      t['publication_date'] < t['deadline_date'])
    ]
    
    passed_checks = sum(1 for check in consistency_checks if check(tender))
    scores["consistency"] = passed_checks / len(consistency_checks) if consistency_checks else 0.0
    
    # Calculate validation score
    validation_score = 1.0
    if scores["issues"]:
        validation_score -= len(scores["issues"]) * 0.1  # Deduct 0.1 for each issue
        validation_score = max(0.0, validation_score)  # Don't go below 0
    scores["validation"] = validation_score
    
    # Calculate overall score with updated weights
    weights = {
        "completeness": 0.3,
        "consistency": 0.3,
        "translation": 0.2,
        "validation": 0.2
    }
    
    scores["overall"] = sum(
        scores[key] * weight
        for key, weight in weights.items()
    )
    
    return scores 