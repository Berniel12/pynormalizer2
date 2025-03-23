"""
Normalizer for African Development Bank tenders.
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import uuid
import re

from pynormalizer.models.source_models import AFDBTender
from pynormalizer.models.unified_model import UnifiedTender
from pynormalizer.utils.translation import (
    translate_to_english,
    detect_language,
    apply_translations
)
from pynormalizer.utils.normalizer_helpers import (
    normalize_document_links, 
    extract_financial_info,
    extract_location_info,
    extract_organization,
    extract_organization_and_buyer,
    extract_procurement_method,
    extract_status,
    extract_deadline,
    normalize_title,
    normalize_description,
    ensure_country,
    clean_price,
    log_tender_normalization
)
from pynormalizer.utils.standardization import (
    validate_cpv_code,
    validate_currency_value,
    calculate_data_quality_score
)

# Import custom helper functions
try:
    from pynormalizer.utils.normalizer_helpers_custom import validate_extracted_data
except ImportError:
    # Define a fallback function if the import fails
    def validate_extracted_data(data):
        return {'is_valid': True, 'issues': []}

logger = logging.getLogger(__name__)

# Common African cities and their countries for better city extraction
AFRICAN_CITIES = {
    'abidjan': 'Ivory Coast',
    'accra': 'Ghana',
    'addis ababa': 'Ethiopia',
    'cairo': 'Egypt',
    'cape town': 'South Africa',
    'casablanca': 'Morocco',
    'dakar': 'Senegal',
    'dar es salaam': 'Tanzania',
    'johannesburg': 'South Africa',
    'kampala': 'Uganda',
    'khartoum': 'Sudan',
    'kinshasa': 'DR Congo',
    'lagos': 'Nigeria',
    'luanda': 'Angola',
    'lusaka': 'Zambia',
    'maputo': 'Mozambique',
    'nairobi': 'Kenya',
    'tunis': 'Tunisia',
    'windhoek': 'Namibia'
}

# Enhanced sector patterns for African context
SECTOR_PATTERNS = {
    'agriculture': [
        r'agricultur(?:e|al)',
        r'farming',
        r'irrigation',
        r'food security',
        r'rural development',
        r'agribusiness'
    ],
    'energy': [
        r'energy',
        r'electricity',
        r'power generation',
        r'renewable',
        r'solar',
        r'wind',
        r'hydropower'
    ],
    'transport': [
        r'transport',
        r'road[s]?',
        r'highway[s]?',
        r'railway[s]?',
        r'aviation',
        r'port[s]?',
        r'infrastructure'
    ],
    'water': [
        r'water',
        r'sanitation',
        r'sewage',
        r'drainage',
        r'wastewater',
        r'water resources'
    ],
    'health': [
        r'health',
        r'medical',
        r'hospital[s]?',
        r'clinic[s]?',
        r'pharmaceutical',
        r'healthcare'
    ],
    'education': [
        r'education',
        r'school[s]?',
        r'university',
        r'training',
        r'vocational',
        r'skills development'
    ],
    'urban': [
        r'urban',
        r'city development',
        r'municipal',
        r'housing',
        r'settlement[s]?',
        r'urban planning'
    ],
    'finance': [
        r'finance',
        r'banking',
        r'microfinance',
        r'insurance',
        r'credit',
        r'financial services'
    ],
    'environment': [
        r'environment',
        r'climate',
        r'conservation',
        r'biodiversity',
        r'sustainability',
        r'green energy'
    ],
    'ict': [
        r'ict',
        r'information technology',
        r'digital',
        r'telecommunications',
        r'internet',
        r'broadband'
    ]
}

def extract_city_info(tender: AFDBTender, country: Optional[str] = None) -> Optional[str]:
    """Extract city information with improved accuracy for African context."""
    # Initialize potential sources of city information
    text_sources = []
    
    # Add description if available
    if tender.description:
        text_sources.append(tender.description)
    
    # Add title if available
    if tender.title:
        text_sources.append(tender.title)
    
    # Combine text sources
    combined_text = ' '.join(text_sources).lower()
    
    # First try location extraction helper
    _, city = extract_location_info(combined_text)
    if city:
        return city.title()
    
    # Look for common African cities
    for city, city_country in AFRICAN_CITIES.items():
        if city in combined_text:
            # If we have country info, verify it matches
            if country and city_country.lower() != country.lower():
                continue
            return city.title()
    
    # Try to find city after location indicators
    city_patterns = [
        r'in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        r'at\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        r'location:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        r'city\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
    ]
    
    for pattern in city_patterns:
        matches = re.finditer(pattern, ' '.join(text_sources))
        for match in matches:
            potential_city = match.group(1)
            # Verify it's not a country name
            if potential_city.lower() not in [c.lower() for c in AFRICAN_CITIES.values()]:
                return potential_city
    
            return None
        
def extract_enhanced_financial_info(tender: AFDBTender) -> Tuple[Optional[float], Optional[str]]:
    """Extract financial information with improved pattern matching for African context."""
    amount, currency = None, None
    
    # Try to extract from various fields
    fields_to_check = []
    
    if tender.description:
        fields_to_check.append(tender.description)
    if tender.title:
        fields_to_check.append(tender.title)
    
    # Common African currencies
    currency_patterns = {
        'USD': [r'USD', r'US\$', r'\$'],
        'EUR': [r'EUR', r'€'],
        'XOF': [r'XOF', r'CFA'],  # West African CFA franc
        'XAF': [r'XAF', r'CFA'],  # Central African CFA franc
        'ZAR': [r'ZAR', r'R'],    # South African Rand
        'NGN': [r'NGN', r'₦'],    # Nigerian Naira
        'KES': [r'KES', r'KSh'],  # Kenyan Shilling
        'EGP': [r'EGP', r'E£'],   # Egyptian Pound
        'MAD': [r'MAD', r'DH']    # Moroccan Dirham
    }
    
    # Try each field
    for field in fields_to_check:
        # First try general financial extraction
        extracted_amount, extracted_currency = extract_financial_info(field)
        if extracted_amount and extracted_currency:
            amount, currency = extracted_amount, extracted_currency
            break
        
        # Then try specific currency patterns
        for curr, patterns in currency_patterns.items():
            for pattern in patterns:
                matches = re.finditer(
                    f"{pattern}\\s*(\\d+(?:,\\d{{3}})*(?:\\.\\d+)?(?:\\s*[mM]illion|\\s*[bB]illion)?)",
                    field
                )
                for match in matches:
                    try:
                        value_str = match.group(1)
                        
                        # Handle million/billion
                        multiplier = 1
                        if 'million' in value_str.lower():
                            multiplier = 1_000_000
                            value_str = value_str.lower().replace('million', '').strip()
                        elif 'billion' in value_str.lower():
                            multiplier = 1_000_000_000
                            value_str = value_str.lower().replace('billion', '').strip()
                        
                        # Clean and convert to float
                        value_str = re.sub(r'[^\d.]', '', value_str)
                        amount = float(value_str) * multiplier
                        currency = curr
                        
                        # Validate the extracted amount
                        if validate_currency_value(amount):
                            return amount, currency
                    except (ValueError, IndexError) as e:
                        logger.debug(f"Failed to parse amount from {value_str}: {e}")
                continue
        
    return amount, currency

def extract_sectors(tender: AFDBTender) -> List[str]:
    """Extract and categorize sectors with improved accuracy for African context."""
    sectors = set()
    
    # Combine available text
    text_sources = []
    if tender.description:
        text_sources.append(tender.description)
    if tender.title:
        text_sources.append(tender.title)
    
    combined_text = ' '.join(text_sources).lower()
    
    # Check each sector's patterns
    for sector, patterns in SECTOR_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, combined_text, re.IGNORECASE):
                sectors.add(sector)
                break
    
    return list(sectors)

def normalize_afdb(tender: AFDBTender) -> UnifiedTender:
    """
    Normalize African Development Bank tender to unified format with improved extraction and validation.
    
    Args:
        tender: AFDBTender object containing source data
        
    Returns:
        UnifiedTender object with normalized data
    """
    try:
        # Generate unique ID for the tender
        tender_id = str(uuid.uuid4())
        
        # Initialize unified tender
        unified = UnifiedTender(
            id=tender_id,
            source="afdb",
            source_id=tender.id,
            source_url=tender.url
        )
        
        # Normalize title
        unified.title = normalize_title(tender.title)
        log_tender_normalization(tender_id, "title", tender.title, unified.title)
        
        # Normalize description
        unified.description = normalize_description(tender.description)
        log_tender_normalization(tender_id, "description", tender.description, unified.description)
        
        # Detect language and translate if needed
        language = detect_language(tender.title)
        unified.language = language or 'en'
        
        if language and language != 'en':
            logger.info(f"Detected non-English language: {language}")
            # Apply translations for key fields
            
            # Title translation
            if unified.title:
                title_english, quality = translate_to_english(unified.title, language)
                unified.title_english = title_english
                log_tender_normalization(tender_id, "title_translation", unified.title, unified.title_english)
            
            # Description translation
            if unified.description:
                desc_english, quality = translate_to_english(unified.description, language)
                unified.description_english = desc_english
                log_tender_normalization(tender_id, "description_translation", unified.description, unified.description_english)
        else:
            # For English content, copy the fields directly
            unified.title_english = unified.title
            unified.description_english = unified.description
        
        # Extract and normalize country with improved validation
        country_name = ensure_country(tender.country)
        unified.country = country_name
        log_tender_normalization(tender_id, "country", tender.country, unified.country)
        
        # Extract city information with improved accuracy
        city = extract_city_info(tender, country_name)
        if city:
            unified.city = city
            log_tender_normalization(tender_id, "city", None, city)
        
        # Extract organization and buyer information
        org_name, buyer_info = extract_organization_and_buyer(unified.description)
        if org_name:
            unified.organization_name = org_name
            log_tender_normalization(tender_id, "organization", None, org_name)
            
            # Also set in English if language is not English
            if language and language != 'en':
                org_english = translate_to_english(org_name, language)
                unified.organization_name_english = org_english
        
        if buyer_info:
            unified.buyer = buyer_info
            log_tender_normalization(tender_id, "buyer", None, buyer_info)
        
        # Extract financial information with improved accuracy
        amount, currency = extract_enhanced_financial_info(tender)
        if amount and currency:
            unified.estimated_value = amount
            unified.currency = currency
            log_tender_normalization(tender_id, "financial_info", None, f"{amount} {currency}")
        
        # Extract and categorize sectors
        sectors = extract_sectors(tender)
        if sectors:
            unified.sector = sectors[0]  # Primary sector
            unified.original_data = json.dumps({
                **(json.loads(unified.original_data) if unified.original_data else {}),
                "all_sectors": sectors
            })
            log_tender_normalization(tender_id, "sectors", None, sectors)
        
        # Extract procurement method
        method = extract_procurement_method(unified.description)
        if method:
            unified.procurement_method = method
            log_tender_normalization(tender_id, "procurement_method", None, method)
        
        # Extract and normalize status
        status = extract_status(unified.description)
        if status:
            unified.status = status
            log_tender_normalization(tender_id, "status", None, status)
        
        # Extract deadline with improved validation
        deadline = extract_deadline(unified.description)
        if deadline:
            unified.deadline_date = deadline
            log_tender_normalization(tender_id, "deadline", None, deadline.isoformat())
        elif tender.closing_date:  # Use the closing_date field if available
            unified.deadline_date = tender.closing_date
        
        # Set publication date
        if tender.publication_date:
            unified.publication_date = tender.publication_date
        
        # Normalize document links
        if tender.document_links:
            unified.documents = normalize_document_links(tender.document_links)
        
        # AFDB specific fields - store in original_data
        original_data = json.loads(unified.original_data) if unified.original_data else {}
        if hasattr(tender, 'tender_type'):
            unified.tender_type = tender.tender_type
            original_data["tender_type"] = tender.tender_type
        
        # Store original data
        if original_data:
            unified.original_data = json.dumps(original_data)
        
        # Validate extracted fields
        try:
            validation_results = validate_extracted_data(unified.dict())
            if not validation_results['is_valid']:
                logger.warning(f"Validation issues for tender {tender_id}: {validation_results['issues']}")
                unified.data_quality_issues = json.dumps(validation_results['issues'])
        except (NameError, ImportError) as e:
            # Function may not be available, log and continue
            logger.warning(f"Could not validate extracted data: {str(e)}")
        
        # Calculate data quality score
        quality_scores = calculate_data_quality_score(unified.dict())
        unified.data_quality_score = quality_scores['overall_score']
        
        # Add normalized timestamp
        unified.normalized_at = datetime.utcnow()
        unified.normalized_method = "enhanced_afdb_normalizer"
        
        return unified

    except Exception as e:
        logger.error(f"Error normalizing AFDB tender {tender.id}: {str(e)}")
        # Return a minimal unified tender for error cases
        error_tender = UnifiedTender(
            id=str(uuid.uuid4()),
            source="afdb",
            source_id=tender.id if hasattr(tender, 'id') else "unknown",
            title=tender.title if hasattr(tender, 'title') else "Error in normalization",
            fallback_reason=f"Error: {str(e)}",
            normalized_method="error_fallback"
        )
        return error_tender 