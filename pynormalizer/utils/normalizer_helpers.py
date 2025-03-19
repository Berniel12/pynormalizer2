"""
Helper functions for normalizers.
"""
import json
import logging
import re
from typing import Any, Dict, Optional, Tuple, List, Union
from datetime import datetime, date, timezone
import traceback

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

def extract_financial_info(text: str) -> Tuple[Optional[float], Optional[str]]:
    """Extract financial information from text."""
    if not text:
        return None, None
    
    # Try currency pattern
    matches = CURRENCY_PATTERN.findall(text)
    if matches:
        for match in matches:
            if match[0] and match[1]:  # Currency code then amount
                currency, amount_str = match[0], match[1]
                amount = clean_price(amount_str)
                if amount:
                    return amount, currency
            elif match[2] and match[3]:  # Amount then currency code
                amount_str, currency = match[2], match[3]
                amount = clean_price(amount_str)
                if amount:
                    return amount, currency
    
    # Try special currency symbols
    match = re.search(r'([$€£])\s*([\d,]+(?:\.\d+)?)', text)
    if match:
        currency_map = {'$': 'USD', '€': 'EUR', '£': 'GBP'}
        amount = clean_price(match.group(2))
        currency = currency_map.get(match.group(1))
        
        if amount and currency:
            return amount, currency
    
    return None, None

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
        Tuple of (normalized_name, iso_code, iso_code_3)
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
            return "Unknown", None, None
    
    normalized_name, iso_code, iso_code_3, info = normalize_country(country_value)
    
    if not info["valid"]:
        logger.warning(f"Country validation issues: {info['issues']}")
        return normalized_name or "Unknown", iso_code, iso_code_3
    
    return normalized_name, iso_code, iso_code_3

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

def extract_location_info(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract country and city information from text.
    
    Args:
        text: Text to extract from
        
    Returns:
        Tuple of (country, city)
    """
    if not text:
        return None, None
    
    # Try to find location after prepositions
    match = LOCATION_PATTERN.search(text)
    if match:
        location = match.group(1).strip()
        # Clean up the location string
        location = re.sub(r'[^\w\s,]', '', location)
        location = re.sub(r'\s+', ' ', location).strip()
        
        # Split into city and country if comma present
        parts = [p.strip() for p in location.split(',')]
        if len(parts) >= 2:
            city, country = parts[0], parts[-1]
            normalized_country, _, _ = ensure_country(country)
            return normalized_country, city
        
        # If only one part, try to identify if it's a country
        normalized_country, _, _ = ensure_country(location)
        if normalized_country != "Unknown":
            return normalized_country, None
        
        # If not identified as country, assume it's a city
        return None, location
    
    return None, None

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