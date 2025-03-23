"""
Helper functions for normalizers.
"""
import json
import logging
import re
from typing import Any, Dict, Optional, Tuple, List, Union
from datetime import datetime, date, timezone
import traceback
from decimal import Decimal, InvalidOperation
import pytz
from dateutil import parser as date_parser

from .standardization import (
    standardize_title,
    structure_description,
    normalize_country,
    validate_translation_quality,
    calculate_data_quality_score,
    validate_cpv_code,
    validate_nuts_code,
    validate_currency_value,
    CURRENCY_CONFIG,
    CPV_PATTERN,
    NUTS_PATTERN,
    CURRENCY_PATTERN,
    extract_organization_name,
    extract_contact_info
)

# Initialize logger
logger = logging.getLogger(__name__)

# Export all helper functions
__all__ = [
    'normalize_document_links',
    'extract_financial_info',
    'determine_currency',
    'format_for_logging',
    'ensure_country',
    'log_tender_normalization',
    'clean_price',
    'extract_status',
    'parse_date_string',
    'extract_sector_info',
    'standardize_status',
    'normalize_title',
    'normalize_description',
    'standardize_procurement_method',
    'normalize_value',
    'extract_organization_and_buyer',
    'log_before_after',
    'determine_normalized_method',
    'clean_date',
    'extract_location_info',
    'extract_organization',
    'extract_procurement_method',
    'parse_date_from_text',
    'extract_country_from_text',
    'extract_deadline',
    'determine_status',
    'extract_organization_info',
    'safe_get_value',
    'log_normalization_error',
    'validate_extracted_data'
]

# Common countries for fallback
COMMON_COUNTRIES = [
    "United States", "China", "India", "Brazil", "Russia", "Germany", "United Kingdom", 
    "France", "Japan", "Italy", "Canada", "Australia", "Spain", "Mexico", "South Korea",
    "Indonesia", "Netherlands", "Saudi Arabia", "Turkey", "Switzerland", "South Africa"
]

# Mapping of TLDs to countries
COUNTRY_TLD_MAPPING = {
    "us": "United States",
    "uk": "United Kingdom",
    "fr": "France",
    "de": "Germany",
    "cn": "China",
    "jp": "Japan",
    "ca": "Canada",
    "au": "Australia",
    "in": "India",
    "br": "Brazil",
    "ru": "Russia",
    "za": "South Africa",
    "mx": "Mexico",
    "es": "Spain",
    "it": "Italy",
    "nl": "Netherlands",
    "ch": "Switzerland",
    "se": "Sweden",
    "no": "Norway",
    "dk": "Denmark",
    "fi": "Finland"
}

# Mapping of languages to common countries
LANGUAGE_COUNTRY_MAPPING = {
    "en": "United States",
    "fr": "France",
    "de": "Germany",
    "es": "Spain",
    "it": "Italy",
    "pt": "Portugal", 
    "ru": "Russia",
    "zh": "China",
    "ja": "Japan",
    "ar": "Saudi Arabia",
    "hi": "India",
    "ko": "South Korea",
    "nl": "Netherlands",
    "sv": "Sweden",
    "no": "Norway",
    "da": "Denmark",
    "fi": "Finland",
    "el": "Greece",
    "tr": "Turkey"
}

# Precompile regex patterns
PRICE_PATTERN = re.compile(r'(?:[\$€£])\s*([0-9,]+(?:\.[0-9]+)?)|([0-9,]+(?:\.[0-9]+)?)\s*(?:USD|EUR|GBP)')
LOCATION_PATTERN = re.compile(r'(?:in|at|from)\s+([A-Za-z\s,]+)')
DEADLINE_PATTERN = re.compile(r'(?:deadline|closing date|submission date|due date|due by)[\s:]+(\d{1,2}[\s./\-]\d{1,2}[\s./\-]\d{2,4}|\d{1,2}[\s./\-][A-Za-z]{3,9}[\s./\-]\d{2,4})')
STATUS_PATTERN = re.compile(r'(?:status|state)[\s:]+([A-Za-z\s]+)', re.IGNORECASE)

# Shared regex patterns for financial information
AMOUNT_PATTERNS = {
    'standard': [
        r'(?:USD|US\$|\$|EUR|€|GBP|£)\s*([\d,]+(?:\.\d{2})?)',
        r'([\d,]+(?:\.\d{2})?)\s*(?:USD|US\$|\$|EUR|€|GBP|£)',
    ],
    'with_scale': [
        r'(?:USD|US\$|\$|EUR|€|GBP|£)?\s*([\d,]+(?:\.\d{2})?)\s*(?:million|billion|M|B)',
        r'([\d,]+(?:\.\d{2})?)\s*(?:million|billion|M|B)\s*(?:USD|US\$|\$|EUR|€|GBP|£)?'
    ],
    'range': [
        r'(?:between|from)?\s*(?:USD|US\$|\$|EUR|€|GBP|£)\s*([\d,]+(?:\.\d{2})?)\s*(?:to|-)\s*(?:USD|US\$|\$|EUR|€|GBP|£)?\s*([\d,]+(?:\.\d{2})?)',
    ]
}

# Shared procurement method patterns
PROCUREMENT_PATTERNS = {
    'open': [
        r'(?i)(?:open|international)\s+(?:tender|competition|bidding)',
        r'(?i)request\s+for\s+(?:proposal|tender|bid)',
        r'(?i)invitation\s+to\s+bid'
    ],
    'restricted': [
        r'(?i)restricted\s+(?:tender|bidding)',
        r'(?i)limited\s+competition',
        r'(?i)pre[-\s]qualified\s+(?:suppliers|bidders)'
    ],
    'direct': [
        r'(?i)direct\s+(?:procurement|contracting|award)',
        r'(?i)single\s+source',
        r'(?i)sole\s+source'
    ],
    'framework': [
        r'(?i)framework\s+agreement',
        r'(?i)long[-\s]term\s+agreement',
        r'(?i)master\s+agreement'
    ]
}

# Status determination patterns
STATUS_PATTERNS = {
    'active': [
        r'(?i)active',
        r'(?i)open',
        r'(?i)published',
        r'(?i)current'
    ],
    'closed': [
        r'(?i)closed',
        r'(?i)completed',
        r'(?i)awarded',
        r'(?i)expired'
    ],
    'cancelled': [
        r'(?i)cancel(?:l)?ed',
        r'(?i)withdrawn',
        r'(?i)terminated'
    ],
    'draft': [
        r'(?i)draft',
        r'(?i)pending',
        r'(?i)upcoming'
    ]
}

def normalize_document_links(links_data):
    """Normalize document links to a standardized format."""
    if not links_data:
        return []
        
    # Basic implementation that extracts URLs
    normalized_links = []
    
    # Define pattern to identify URLs
    url_pattern = re.compile(
        r'(https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*)'
    )
    
    # Handle string (single URL)
    if isinstance(links_data, str):
        urls = url_pattern.findall(links_data)
        for url in urls:
                normalized_links.append({
                'url': url,
                'type': 'unknown',
                'language': 'en',
                'description': None
            })
        return normalized_links
    
    # Handle list
    if isinstance(links_data, list):
        for item in links_data:
            if isinstance(item, str):
                urls = url_pattern.findall(item)
                for url in urls:
                    normalized_links.append({
                        'url': url,
                        'type': 'unknown',
                        'language': 'en',
                        'description': None
                    })
    
    # Remove duplicates
    seen = set()
    unique_links = []
    for link in normalized_links:
        if link['url'] not in seen:
            seen.add(link['url'])
            unique_links.append(link)
    
    return unique_links

def extract_financial_info(text: str, currency_hint: Optional[str] = None) -> Tuple[Optional[Decimal], Optional[Decimal], Optional[str]]:
    """
    Extract financial information from text with improved pattern matching.
    
    Args:
        text: Text to extract financial information from
        currency_hint: Optional hint about the expected currency
        
    Returns:
        Tuple of (min_value, max_value, currency)
    """
    if not text:
        return None, None, None

    # Try range patterns first
    for pattern in AMOUNT_PATTERNS['range']:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                min_amount = Decimal(match.group(1).replace(',', ''))
                max_amount = Decimal(match.group(2).replace(',', ''))
                currency = determine_currency(match.group(0), currency_hint)
                return min_amount, max_amount, currency
            except (ValueError, InvalidOperation):
                continue

    # Try standard and scale patterns
    amounts = []
    detected_currency = None
    
    for pattern_type in ['standard', 'with_scale']:
        for pattern in AMOUNT_PATTERNS[pattern_type]:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                try:
                    amount_str = match.group(1).replace(',', '')
                    amount = Decimal(amount_str)
                    
                    # Handle scale
                    if pattern_type == 'with_scale':
                        scale_text = match.group(0).lower()
                        if 'billion' in scale_text or 'B' in scale_text:
                            amount *= 1000000000
                        elif 'million' in scale_text or 'M' in scale_text:
                            amount *= 1000000
                    
                    amounts.append(amount)
                    
                    # Determine currency if not already found
                    if not detected_currency:
                        detected_currency = determine_currency(match.group(0), currency_hint)
                        
                except (ValueError, InvalidOperation):
                    continue

    if not amounts:
        return None, None, None

    return min(amounts), max(amounts), detected_currency or currency_hint or 'USD'

def determine_currency(text: str, hint: Optional[str] = None) -> str:
    """
    Determine currency from text with fallback to hint.
    """
    text = text.upper()
    if '€' in text or 'EUR' in text:
        return 'EUR'
    elif '£' in text or 'GBP' in text:
        return 'GBP'
    elif '¥' in text or 'JPY' in text:
        return 'JPY'
    elif 'CHF' in text:
        return 'CHF'
    elif '$' in text or 'USD' in text:
        return 'USD'
    return hint or 'USD'

def format_for_logging(data: Any) -> str:
    """Format data for logging, handling special types."""
    if isinstance(data, (str, int, float)):
        return str(data)
    elif isinstance(data, datetime):
        return data.isoformat()
    elif isinstance(data, dict):
        try:
            return json.dumps(data, default=str)[:500]  # Truncate long JSON
        except (TypeError, ValueError):
            return str(data)[:500]  # Fallback to string representation
    elif isinstance(data, (list, tuple)):
        try:
            return json.dumps(data, default=str)[:500]
        except (TypeError, ValueError):
            return str(data)[:500]
    return str(data)[:500]  # Default truncated string representation

def ensure_country(country_value=None, text=None, organization=None, email=None, language=None):
    """
    Ensure a valid country name and get associated ISO codes.
    
    Args:
        country_value: Country name in any format
        text: Text to extract country from if country_value is None
        organization: Organization name that might contain country info
        email: Email that might contain country info in domain
        language: Language code that might give a clue about country
        
    Returns:
        Normalized country name as a string (not a tuple)
    """
    if not country_value:
        logger.warning("Empty country value provided")
        
        # Try to extract from text
        if text:
            extracted_country, _ = extract_location_info(text)
            if extracted_country:
                country_value = extracted_country
                logger.info(f"Extracted country '{country_value}' from text")
        
        # Try to extract from organization name
        if not country_value and organization:
            # Check for common country patterns in organization names
            org_lower = organization.lower()
            for country_name in COMMON_COUNTRIES:
                if country_name.lower() in org_lower:
                    country_value = country_name
                    logger.info(f"Extracted country '{country_value}' from organization name")
                    break
        
        # Try to extract from email domain
        if not country_value and email and '@' in email:
            domain = email.split('@')[-1]
            tld = domain.split('.')[-1].lower()
            
            # Check if TLD is a country code
            if tld in COUNTRY_TLD_MAPPING:
                country_value = COUNTRY_TLD_MAPPING[tld]
                logger.info(f"Extracted country '{country_value}' from email TLD: {tld}")
        
        # Use language as a hint for country
        if not country_value and language:
            if language in LANGUAGE_COUNTRY_MAPPING:
                country_value = LANGUAGE_COUNTRY_MAPPING[language]
                logger.info(f"Using country '{country_value}' based on language: {language}")
        
        if not country_value:
            return "Unknown"
    
    normalized_name, iso_code, iso_code_3, info = normalize_country(country_value)
    
    if not info["valid"]:
        logger.warning(f"Country validation issues: {info['issues']}")
        return normalized_name or "Unknown"
    
    return normalized_name

def log_tender_normalization(source_table, source_id, log_data):
    """Log tender normalization process."""
    try:
        if not isinstance(log_data, dict):
            log_data = {"data": str(log_data)}
            
        formatted_data = format_for_logging(log_data)
        logger.info(f"Normalizing tender from {source_table} (ID: {source_id}): {formatted_data}")
    except Exception as e:
        logger.error(f"Error logging tender normalization: {str(e)}")

def clean_price(price_str: str) -> Optional[float]:
    """Clean and convert price string to float."""
    if not price_str:
        return None
    
    try:
        # Remove non-numeric characters except decimal point
        cleaned = re.sub(r'[^\d.]', '', price_str.replace(',', ''))
        value = float(cleaned)
        
        # Basic sanity check
        if value <= 0 or value > CURRENCY_CONFIG['max_value']:
            logger.warning(f"Price value out of reasonable range: {value}")
            return None
            
        return value
    except (ValueError, TypeError) as e:
        logger.warning(f"Could not convert price: {price_str}. Error: {str(e)}")
        return None

def extract_status(text=None, deadline=None, publication_date=None, description=None):
    """Extract tender status information."""
    # Use description as text if text is None
    if text is None and description is not None:
        text = description
    
    # Default status
    status = 'active'
    
    if text and isinstance(text, str):
        text_lower = text.lower()
        
        if any(term in text_lower for term in ['complete', 'completed', 'closed', 'awarded']):
            status = 'complete'
        elif any(term in text_lower for term in ['cancelled', 'canceled', 'terminated']):
            status = 'cancelled'
        
        # Additional status patterns from the other implementation
        status_patterns = {
            r'\b(?:open|active|ongoing|current)\b': 'active',
            r'\b(?:closed|completed|finished|past|archived)\b': 'complete',
            r'\b(?:awarded|contract awarded|awarded contract)\b': 'awarded',
            r'\b(?:cancelled|canceled|terminated|abandoned)\b': 'cancelled',
            r'\b(?:draft|preparation|not published|upcoming)\b': 'draft',
            r'\b(?:under evaluation|evaluating|evaluation stage)\b': 'under_evaluation'
        }
        
        # Check for explicit status mentions
        if STATUS_PATTERN:
            status_match = STATUS_PATTERN.search(text_lower)
            if status_match:
                status_text = status_match.group(1).lower().strip()
                for pattern, normalized in status_patterns.items():
                    if re.search(pattern, status_text, re.IGNORECASE):
                        status = normalized
                        break
        
        # If no explicit status found, try to infer from the whole text
        for pattern, normalized in status_patterns.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                status = normalized
                break
    
    # Check dates if available
    if deadline or publication_date:
        try:
            current_date = datetime.now().date()
            
            if deadline and isinstance(deadline, datetime):
                deadline_date = deadline.date()
                if deadline_date < current_date:
                    status = 'complete'
        except Exception:
            pass
    
    return status

def parse_date_string(date_str):
    """Parse a date string into a datetime object."""
    if not date_str or not isinstance(date_str, str):
        return None

    # Clean the string
    date_str = date_str.strip()
    
    # Common date formats to try
    date_formats = [
        '%Y-%m-%d',      
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%d %H:%M:%S',
        '%d/%m/%Y',
        '%m/%d/%Y',
        '%d-%m-%Y',
        '%m-%d-%Y'
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None

def extract_sector_info(text):
    """Extract sector information from text."""
    if not text:
        return None
        
    # Common sector keywords
    sectors = {
        'agriculture': ['agriculture', 'farming', 'crops', 'livestock'],
        'construction': ['construction', 'building', 'infrastructure'],
        'education': ['education', 'school', 'university', 'training'],
        'energy': ['energy', 'power', 'electricity', 'renewable'],
        'healthcare': ['health', 'medical', 'hospital', 'pharmaceutical'],
        'technology': ['technology', 'software', 'IT', 'digital'],
        'transport': ['transport', 'logistics', 'shipping']
    }
    
    text_lower = text.lower()
    matched_sectors = []
    
    for sector, keywords in sectors.items():
        if any(keyword in text_lower for keyword in keywords):
            matched_sectors.append(sector)
    
    return matched_sectors[0] if matched_sectors else None

def standardize_status(status_text):
    """Standardize status values."""
    if not status_text:
        return None
        
    status_text = str(status_text).lower().strip()
    
    # Status mapping
    status_mapping = {
        'active': ['active', 'open', 'ongoing', 'in progress'],
        'complete': ['complete', 'completed', 'closed', 'awarded', 'finished'],
        'cancelled': ['cancelled', 'canceled', 'terminated', 'withdrawn'],
        'draft': ['draft', 'pending', 'not published'],
        'expired': ['expired', 'deadline passed']
    }
    
    for standard_status, variations in status_mapping.items():
        if any(var in status_text for var in variations):
            return standard_status
    
    return 'unknown'

def normalize_title(title: str) -> str:
    """Normalize and standardize a tender title."""
    if not title:
        return ""
    
    # Use the standardization function
    result, info = standardize_title(title)
    
    if not info["valid"]:
        logger.warning(f"Title validation issues: {info['issues']}")
    
    return result

def normalize_description(description: str) -> str:
    """Normalize and structure a tender description."""
    if not description:
        return ""
    
    # Use the standardization function
    result, info = structure_description(description)
    
    if not info["valid"]:
        logger.warning(f"Description validation issues: {info['issues']}")
    
    return result

def standardize_procurement_method(method: str) -> str:
    """Standardize procurement method values."""
    if not method:
        return None
    
    method = str(method).lower().strip()
    
    # Method mapping
    method_mapping = {
        'open': [
            'open', 'open tender', 'open bidding', 'competitive',
            'international competitive bidding', 'icb',
            'national competitive bidding', 'ncb'
        ],
        'limited': [
            'limited', 'restricted', 'selective', 'invitation only',
            'prequalification', 'pre-qualification'
        ],
        'direct': [
            'direct', 'single source', 'sole source', 'proprietary',
            'direct contracting', 'direct award'
        ],
        'framework': [
            'framework', 'framework agreement', 'multiple suppliers'
        ],
        'negotiated': [
            'negotiated', 'negotiation', 'competitive dialogue',
            'competitive negotiation'
        ]
    }
    
    for standard_method, variations in method_mapping.items():
        if any(var in method for var in variations):
            return standard_method
    
    return 'other'

def normalize_value(value: float, currency: str = None) -> Tuple[float, str]:
    """Normalize tender value and currency."""
    if value is None:
        return None, currency
    
    try:
        value = float(value)
    except (ValueError, TypeError):
        return None, currency
    
    # Standardize currency codes
    currency_mapping = {
        'USD': ['usd', 'us', 'dollar', 'dollars'],
        'EUR': ['eur', 'euro', 'euros'],
        'GBP': ['gbp', 'pound', 'pounds'],
        'JPY': ['jpy', 'yen']
    }
    
    if currency:
        currency = str(currency).strip().upper()
        for standard_code, variations in currency_mapping.items():
            if currency.lower() in variations:
                currency = standard_code
                break
    
    return value, currency

def extract_organization_and_buyer(text: str, title: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """Extract organization and buyer information from text."""
    if not text and not title:
        return None, None
    
    # Combine text sources
    full_text = ' '.join(filter(None, [text, title]))
    
    # Common organization indicators
    org_indicators = [
        r'(?:issued|published|posted)\s+by\s+([^\.]+)',
        r'(?:organization|organisation|agency|authority):\s*([^\.]+)',
        r'(?:client|owner|employer):\s*([^\.]+)'
    ]
    
    # Common buyer indicators
    buyer_indicators = [
        r'(?:buyer|purchaser|contracting authority):\s*([^\.]+)',
        r'(?:on behalf of|for)\s+([^\.]+)',
        r'(?:procurement for|purchase for)\s+([^\.]+)'
    ]
    
    organization = None
    buyer = None
    
    # Extract organization
    for pattern in org_indicators:
        matches = re.search(pattern, full_text, re.IGNORECASE)
        if matches:
            organization = matches.group(1).strip()
            break
    
    # Extract buyer
    for pattern in buyer_indicators:
        matches = re.search(pattern, full_text, re.IGNORECASE)
        if matches:
            buyer = matches.group(1).strip()
            break
    
    # Clean extracted values
    if organization:
        organization = re.sub(r'\s+', ' ', organization)
        organization = re.sub(r'[^\w\s\-\.,]', '', organization)
        
    if buyer:
        buyer = re.sub(r'\s+', ' ', buyer)
        buyer = re.sub(r'[^\w\s\-\.,]', '', buyer)
    
    return organization, buyer

def log_before_after(field, before, after):
    """Log field changes during normalization."""
    if before != after:
        logger.debug(f"Field '{field}' changed:")
        logger.debug(f"  Before: {before}")
        logger.debug(f"  After:  {after}")

def determine_normalized_method(row, default=None):
    """Determine the normalization method based on row data."""
    if not row:
        return default or "unknown"
    
    # Initialize score tracking
    method_scores = {
        "full": 0,
        "partial": 0,
        "minimal": 0
    }
    
    # Check required fields
    required_fields = ['title', 'description', 'status']
    for field in required_fields:
        if field in row and row[field]:
            method_scores['full'] += 1
        else:
            method_scores['minimal'] += 1
    
    # Check important fields
    important_fields = [
        'publication_date', 'deadline_date', 'country',
        'organization_name', 'estimated_value'
    ]
    for field in important_fields:
        if field in row and row[field]:
            method_scores['full'] += 1
        else:
            method_scores['partial'] += 1
    
    # Check additional fields
    additional_fields = [
        'city', 'buyer', 'project_name', 'sector',
        'currency', 'contact_email', 'document_links'
    ]
    for field in additional_fields:
        if field in row and row[field]:
            method_scores['partial'] += 1
        else:
            method_scores['minimal'] += 1
    
    # Determine method based on scores
    if method_scores['full'] >= 5:
        return "full"
    elif method_scores['partial'] >= 5:
        return "partial"
    elif method_scores['minimal'] >= 5:
        return "minimal"
    else:
        return default or "unknown"

def clean_date(date_value):
    """Clean and normalize a date value."""
    if not date_value:
        return None
    
    # If already a datetime object
    if isinstance(date_value, datetime):
        return date_value
    
    # If a date object
    if isinstance(date_value, date):
        return datetime.combine(date_value, datetime.min.time())
    
    # If a string, try parsing
    if isinstance(date_value, str):
        # Remove any surrounding whitespace
        date_str = date_value.strip()
        
        # Try common date formats
        formats = [
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%d-%m-%Y',
            '%m-%d-%Y',
            '%b %d %Y',
            '%B %d %Y',
            '%d %b %Y',
            '%d %B %Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Try parsing with dateutil as a fallback
        try:
            from dateutil import parser
            return parser.parse(date_str)
        except:
            pass
    
    return None

def extract_location_info(text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extract country, state/region, and city information from text.
    
    Args:
        text: Text to extract from
        
    Returns:
        Tuple of (country, state, city)
    """
    if not text:
        return None, None, None
    
    # Try to find location after prepositions
    match = LOCATION_PATTERN.search(text)
    if match:
        location = match.group(1).strip()
        # Clean up the location string
        location = re.sub(r'[^\w\s,]', '', location)
        location = re.sub(r'\s+', ' ', location).strip()
        
        # Split into city, state, and country if multiple commas present
        parts = [p.strip() for p in location.split(',')]
        if len(parts) >= 3:
            city, state, country = parts[0], parts[1], parts[-1]
            normalized_country = ensure_country(country)
            return normalized_country, state, city
        elif len(parts) == 2:
            city, country = parts[0], parts[-1]
            normalized_country = ensure_country(country)
            return normalized_country, None, city
        
        # If only one part, try to identify if it's a country
        normalized_country = ensure_country(location)
        if normalized_country != "Unknown":
            return normalized_country, None, None
        
        # If not identified as country, assume it's a city
        return None, None, location
    
    return None, None, None

def extract_organization(text: str) -> Optional[str]:
    """
    Extract organization name from text.
    
    Args:
        text: Text to extract from
        
    Returns:
        Organization name if found, None otherwise
    """
    if not text:
        return None
    
    # Use the standardization function
    org_name = extract_organization_name(text)
    
    if org_name:
        # Clean up the name
        org_name = re.sub(r'\s+', ' ', org_name).strip()
        # Remove common suffixes
        org_name = re.sub(r'\s+(?:ltd|llc|inc|corp|sa|gmbh|co)\.?$', '', org_name, flags=re.IGNORECASE)
        
        return org_name
    
    return None

def extract_procurement_method(text: str) -> Optional[str]:
    """
    Extract and normalize procurement method.
    
    Args:
        text: Text to extract from
        
    Returns:
        Normalized procurement method if found, None otherwise
    """
    if not text:
        return None
    
    # Common procurement method patterns
    methods = {
        r'\b(?:open|public)\s+(?:tender|bidding)\b': 'Open',
        r'\b(?:restricted|limited)\s+(?:tender|bidding)\b': 'Restricted',
        r'\b(?:competitive|negotiated)\s+dialogue\b': 'Competitive Dialogue',
        r'\b(?:direct|single-source)\s+award\b': 'Direct Award',
        r'\b(?:framework|blanket)\s+agreement\b': 'Framework Agreement',
        r'\b(?:request|call)\s+for\s+proposal(?:s)?\b': 'RFP',
        r'\b(?:request|call)\s+for\s+qualification(?:s)?\b': 'RFQ',
        r'\b(?:request|call)\s+for\s+tender(?:s)?\b': 'RFT',
        r'\b(?:request|call)\s+for\s+bid(?:s)?\b': 'RFB',
        r'\b(?:expression|statement)\s+of\s+interest\b': 'EOI',
        r'\bICB\b': 'International Competitive Bidding',
        r'\bNCB\b': 'National Competitive Bidding',
        r'\bLIB\b': 'Limited International Bidding'
    }
    
    normalized = None
    for pattern, method in methods.items():
        if re.search(pattern, text, re.IGNORECASE):
            normalized = method
            logger.info(f"Matched procurement method: {method} from: {pattern}")
            break
    
    if normalized:
        return normalized
    else:
        logger.warning(f"Could not normalize procurement method from: {text[:100]}")
        return None

def parse_date_from_text(text):
    """Extract and parse dates from free-form text."""
    if not text:
        return None
    
    # Common date patterns
    date_patterns = [
        r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
        r'(\d{2}/\d{2}/\d{4})',  # DD/MM/YYYY or MM/DD/YYYY
        r'(\d{2}-\d{2}-\d{4})',  # DD-MM-YYYY or MM-DD-YYYY
        r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',  # DD Month YYYY
        r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})'  # Month DD, YYYY
    ]
    
    for pattern in date_patterns:
        matches = re.findall(pattern, text)
        if matches:
            for match in matches:
                try:
                    return parse_date_string(match)
                except ValueError:
                    continue
    
    return None

def extract_country_from_text(text: str) -> Optional[str]:
    """Extract country name from text."""
    if not text:
        return None
    
    # Common country patterns
    country_patterns = [
        r'(?:country|location):\s*([A-Za-z\s]+)',
        r'in\s+([A-Za-z]+)(?:\s+and|,|\.|$)',
        r'(?:from|to)\s+([A-Za-z]+)(?:\s+and|,|\.|$)'
    ]
    
    # Common country names and their variations
    country_mapping = {
        'United States': ['usa', 'us', 'united states', 'america'],
        'United Kingdom': ['uk', 'britain', 'great britain'],
        'European Union': ['eu', 'europe'],
        'United Arab Emirates': ['uae', 'emirates'],
        'Russian Federation': ['russia', 'russian'],
        'People\'s Republic of China': ['china', 'prc'],
        'Republic of Korea': ['korea', 'south korea'],
        'Democratic People\'s Republic of Korea': ['north korea', 'dprk']
    }
    
    # Try to extract country using patterns
    for pattern in country_patterns:
        matches = re.search(pattern, text, re.IGNORECASE)
        if matches:
            country = matches.group(1).strip().lower()
            
            # Check against country mapping
            for standard_name, variations in country_mapping.items():
                if country in variations:
                    return standard_name
            
            # If no mapping found, capitalize words
            return country.title()
    
    return None

def extract_deadline(text: str) -> Optional[datetime]:
    """
    Extract deadline date from text.
    
    Args:
        text: Text to extract from
        
    Returns:
        Deadline date if found, None otherwise
    """
    if not text:
        return None
    
    # Look for deadline patterns
    match = DEADLINE_PATTERN.search(text)
    if match:
        date_str = match.group(1).strip()
        # Try various date formats
        formats = [
            '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y',
            '%m/%d/%Y', '%m-%d-%Y', '%m.%d.%Y',
            '%d/%m/%y', '%d-%m-%y', '%d.%m.%y',
            '%m/%d/%y', '%m-%d-%y', '%m.%d.%y',
            '%d %b %Y', '%d %B %Y',
            '%b %d %Y', '%B %d %Y'
        ]
        
        for fmt in formats:
            try:
                date = datetime.strptime(date_str, fmt)
                # Add timezone information if missing
                if date.tzinfo is None:
                    date = date.replace(tzinfo=timezone.utc)
                return date
            except ValueError:
                continue
    
    return None

def determine_status(status_text: Optional[str], publication_date: Optional[datetime] = None, 
                    deadline_date: Optional[datetime] = None) -> str:
    """
    Determine tender status based on text and dates.
    """
    if not status_text and not publication_date and not deadline_date:
        return 'unknown'

    # Check explicit status first
    if status_text:
        status_text = status_text.lower()
        for status, patterns in STATUS_PATTERNS.items():
            if any(re.search(pattern, status_text) for pattern in patterns):
                return status

    # Determine from dates if no explicit status match
    now = datetime.now(pytz.UTC)
    
    if deadline_date and deadline_date < now:
        return 'closed'
    elif publication_date:
        if publication_date > now:
            return 'draft'
        elif deadline_date and publication_date <= now <= deadline_date:
            return 'active'
            
    return 'unknown'

def normalize_document_links(links: List[Dict[str, Any]], base_url: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Normalize document links with consistent structure.
    """
    normalized_links = []
    seen_urls = set()
    
    for link in links:
        if not isinstance(link, dict):
            continue
            
        url = link.get('url') or link.get('href')
        if not url:
            continue
            
        # Add base URL if relative
        if base_url and not url.startswith(('http://', 'https://')):
            url = f"{base_url.rstrip('/')}/{url.lstrip('/')}"
            
        # Skip if already processed
        if url in seen_urls:
            continue
            
        seen_urls.add(url)
        
        normalized_links.append({
            'url': url,
            'type': link.get('type', 'attachment'),
            'language': link.get('language', 'en'),
            'description': link.get('description') or link.get('title', 'Document')
        })
        
    return normalized_links

def extract_organization_info(text: str, contact_info: Optional[Dict] = None, 
                           org_field: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract organization name and buyer information.
    """
    organization_name = None
    buyer = None
    
    # Try explicit organization field first
    if org_field:
        organization_name = org_field
        
    # Try contact info
    elif contact_info:
        if isinstance(contact_info, dict):
            organization_name = (
                contact_info.get('organization') or
                contact_info.get('org') or
                contact_info.get('company') or
                contact_info.get('department')
            )
            
    # Try extracting from text
    if not organization_name and text:
        org_patterns = [
            r'(?:by|from|for)\s+([A-Za-z0-9\s\(\)&,\.\-]+?)(?:\s+in|\s+for|\s+at|$)',
            r'([A-Za-z0-9\s\(\)&,\.\-]+?)\s+(?:is seeking|requests|invites)',
            r'(?:organization|department|agency|ministry):\s*([A-Za-z0-9\s\(\)&,\.\-]+?)(?:\s|$)'
        ]
        
        for pattern in org_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                potential_org = match.group(1).strip()
                if len(potential_org) > 3 and potential_org.lower() not in ['the', 'and', 'for', 'of']:
                    organization_name = potential_org
                    break
                    
    # Use organization name as buyer if not set
    if organization_name and not buyer:
        buyer = organization_name
        
    return organization_name, buyer

def safe_get_value(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Safely get value from dictionary with dot notation support.
    """
    try:
        current = data
        for part in key.split('.'):
            if isinstance(current, dict):
                current = current.get(part, default)
            else:
                return default
        return current
    except Exception:
        return default

def log_normalization_error(source: str, tender_id: str, error: Exception, context: Optional[Dict] = None) -> None:
    """Log errors that occur during normalization with structured context."""
    error_data = {
        'source': source,
        'tender_id': tender_id,
        'error': str(error),
        'traceback': traceback.format_exc(),
        'context': context or {},
        'timestamp': datetime.now().isoformat()
    }
    logger.error(f"Normalization error: {error} (source={source}, id={tender_id})")
    logger.debug(f"Error details: {json.dumps(error_data, default=str)}")

def validate_extracted_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate the extracted data for completeness and quality.
    
    Args:
        data: Dictionary containing normalized data
        
    Returns:
        Dictionary with validation results including:
        - is_valid: Boolean indicating if the data meets minimum requirements
        - issues: List of identified issues or missing fields
        - quality_score: Numerical score of data quality (0-100)
    """
    issues = []
    required_fields = ['title', 'description', 'publication_date', 'deadline_date', 'status']
    
    # Check for missing required fields
    for field in required_fields:
        if field not in data or not data[field]:
            issues.append(f"Missing required field: {field}")
    
    # Check financial information
    if 'estimated_value' in data and data['estimated_value']:
        if 'amount' not in data['estimated_value'] or not data['estimated_value']['amount']:
            issues.append("Missing amount in estimated value")
        if 'currency' not in data['estimated_value'] or not data['estimated_value']['currency']:
            issues.append("Missing currency in estimated value")
    else:
        issues.append("Missing estimated value information")
    
    # Check buyer information
    if 'buyer' not in data or not data['buyer']:
        issues.append("Missing buyer information")
    elif 'name' not in data['buyer'] or not data['buyer']['name']:
        issues.append("Missing buyer name")
    
    # Calculate quality score (0-100)
    total_fields = len(data.keys())
    filled_fields = sum(1 for k, v in data.items() if v is not None and v != "")
    quality_score = min(100, int((filled_fields / max(1, total_fields)) * 100))
    
    # Adjust score based on issues
    quality_score = max(0, quality_score - (5 * len(issues)))
    
    return {
        'is_valid': len(issues) == 0,
        'issues': issues,
        'quality_score': quality_score
    }