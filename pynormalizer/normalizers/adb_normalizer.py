import json
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
import re
import logging

from pynormalizer.models.source_models import ADBTender
from pynormalizer.models.unified_model import UnifiedTender
from pynormalizer.utils.translation import (
    translate_to_english, detect_language, apply_translations
)
from pynormalizer.utils.normalizer_helpers import (
    normalize_document_links, 
    extract_financial_info,
    extract_location_info,
    extract_organization,
    extract_organization_and_buyer,
    log_before_after,
    ensure_country,
    clean_price,
    log_tender_normalization
)

logger = logging.getLogger(__name__)

# Common Asian cities and their countries for better city extraction
ASIAN_CITIES = {
    'manila': 'Philippines',
    'bangkok': 'Thailand',
    'jakarta': 'Indonesia',
    'hanoi': 'Vietnam',
    'beijing': 'China',
    'tokyo': 'Japan',
    'seoul': 'South Korea',
    'dhaka': 'Bangladesh',
    'colombo': 'Sri Lanka',
    'new delhi': 'India'
}

# Enhanced sector patterns for better categorization
SECTOR_PATTERNS = {
    'agriculture': [
        r'agricultur(?:e|al)',
        r'farming',
        r'irrigation',
        r'crop',
        r'food security'
    ],
    'energy': [
        r'energy',
        r'electricity',
        r'power',
        r'renewable',
        r'solar',
        r'wind'
    ],
    'transport': [
        r'transport',
        r'road',
        r'highway',
        r'railway',
        r'aviation',
        r'port'
    ],
    'water': [
        r'water',
        r'sanitation',
        r'sewage',
        r'drainage',
        r'wastewater'
    ],
    'health': [
        r'health',
        r'medical',
        r'hospital',
        r'clinic',
        r'pharmaceutical'
    ],
    'education': [
        r'education',
        r'school',
        r'university',
        r'training',
        r'vocational'
    ],
    'urban': [
        r'urban',
        r'city development',
        r'municipal',
        r'housing',
        r'settlement'
    ],
    'finance': [
        r'finance',
        r'banking',
        r'microfinance',
        r'insurance',
        r'credit'
    ]
}

def extract_city_info(tender: ADBTender) -> Optional[str]:
    """Extract city information from tender data with improved accuracy."""
    # Try to find city in the description
    if tender.description:
        # First try location extraction helper
        _, city = extract_location_info(tender.description)
        if city:
            return city
            
        # Look for common Asian cities
        desc_lower = tender.description.lower()
        for city, country in ASIAN_CITIES.items():
            if city in desc_lower:
                # Verify if the country matches (if we have country info)
                if not tender.country or country.lower() in tender.country.lower():
                    return city.title()
        
        # Try to find city after location indicators
        city_patterns = [
            r'in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'at\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'location:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'city\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
        ]
        
        for pattern in city_patterns:
            match = re.search(pattern, tender.description)
            if match:
                return match.group(1)
    
    # Try project name if no city found in description
    if tender.project_name:
        for city in ASIAN_CITIES:
            if city in tender.project_name.lower():
                return city.title()
    
    return None

def extract_enhanced_financial_info(tender: ADBTender) -> Tuple[Optional[float], Optional[str]]:
    """Extract financial information with improved pattern matching and validation."""
    amount, currency = None, None
    
    # Try to extract from various fields
    fields_to_check = [
        tender.description,
        tender.project_name,
        getattr(tender, 'contract_amount', None),
        getattr(tender, 'estimated_value', None)
    ]
    
    # Filter out None values
    fields_to_check = [f for f in fields_to_check if f]
    
    for field in fields_to_check:
        # Try to extract amount and currency
        # extract_financial_info returns (min_amount, max_amount, currency)
        extracted_tuple = extract_financial_info(str(field))
        
        # Check if a non-None tuple was returned
        if extracted_tuple and extracted_tuple[0] and extracted_tuple[2]:
            # Use the minimum amount if available
            amount = extracted_tuple[0]
            currency = extracted_tuple[2]
            break
    
    # Clean and validate the amount
    if amount:
        try:
            amount = clean_price(str(amount))
        except (ValueError, TypeError):
            amount = None
    
    # Normalize currency codes
    if currency:
        currency = currency.upper()
        # Map common variations
        currency_map = {
            'USD': 'USD',
            'US$': 'USD',
            '$': 'USD',  # Assume USD for plain $ in ADB context
            'PHP': 'PHP',
            'CNY': 'CNY',
            'JPY': 'JPY',
            'INR': 'INR'
        }
        currency = currency_map.get(currency, currency)
    
    return amount, currency

def extract_enhanced_sector_info(tender: ADBTender) -> List[str]:
    """Extract and categorize sector information with improved accuracy."""
    sectors = set()
    
    # Use existing sector field if available
    if tender.sector:
        sectors.add(tender.sector)
    
    # Extract from description and project name
    text_to_check = []
    if tender.description:
        text_to_check.append(tender.description)
    if tender.project_name:
        text_to_check.append(tender.project_name)
    
    combined_text = ' '.join(text_to_check).lower()
    
    # Check each sector's patterns
    for sector, patterns in SECTOR_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, combined_text, re.IGNORECASE):
                sectors.add(sector)
                break
    
    return list(sectors)

def normalize_document_links_enhanced(tender: ADBTender) -> List[Dict[str, str]]:
    """Enhanced document link normalization for ADB tenders."""
    normalized_docs = []
    
    # Collect all potential document sources
    doc_sources = []
    
    # Add PDF URL if available
    if tender.pdf_url:
        doc_sources.append({
            'url': tender.pdf_url,
            'type': 'pdf',
            'description': 'Tender Notice PDF'
        })
    
    # Add any additional documents
    if hasattr(tender, 'documents') and tender.documents:
        if isinstance(tender.documents, list):
            doc_sources.extend(tender.documents)
        elif isinstance(tender.documents, str):
            doc_sources.append({'url': tender.documents, 'type': 'document'})
    
    # Process each document source
    for doc in doc_sources:
        try:
            if isinstance(doc, str):
                # Handle string URLs
                normalized = normalize_document_links(doc)
                if normalized:
                    normalized_docs.extend(normalized)
            elif isinstance(doc, dict):
                # Handle dictionary format
                normalized_doc = {
                    'url': doc.get('url', ''),
                    'type': doc.get('type', 'document'),
                    'language': doc.get('language', 'en'),
                    'description': doc.get('description', 'ADB tender document')
                }
                if normalized_doc['url']:
                    normalized_docs.append(normalized_doc)
        except Exception as e:
            logger.warning(f"Error normalizing document link: {e}")
            continue
    
    # Remove duplicates while preserving order
    seen_urls = set()
    unique_docs = []
    for doc in normalized_docs:
        if doc['url'] not in seen_urls:
            seen_urls.add(doc['url'])
            unique_docs.append(doc)
    
    return unique_docs

def normalize_adb(row: Dict[str, Any]) -> UnifiedTender:
    """
    Normalize an ADB tender record with improved extraction and validation.
    
    Args:
        row: Dictionary containing ADB tender data
        
    Returns:
        Normalized UnifiedTender instance
    """
    # Validate with Pydantic
    try:
        adb_obj = ADBTender(**row)
    except Exception as e:
        logger.error(f"Failed to validate ADB tender: {e}")
        # Return minimal tender with error info
        return UnifiedTender(
            title="Validation Error",
            source_table="adb",
            source_id=str(row.get('id', 'unknown')),
            fallback_reason=f"Validation error: {str(e)}",
            original_data=row
        )

    try:
        # Convert date -> datetime for publication_date/deadline
        publication_dt = datetime.combine(adb_obj.publication_date, datetime.min.time()) if adb_obj.publication_date else None
        deadline_dt = datetime.combine(adb_obj.due_date, datetime.min.time()) if adb_obj.due_date else None

        # Detect language from title and description
        language = "en"  # Default for ADB
        if adb_obj.notice_title:
            lang = detect_language(adb_obj.notice_title)
            if lang:
                language = lang
        elif adb_obj.description:
            lang = detect_language(adb_obj.description)
            if lang:
                language = lang
        
        logger.debug(f"Detected language for ADB tender {adb_obj.id}: {language}")

        # Enhanced country detection with fallbacks
        country = ensure_country(
            country_value=adb_obj.country,
            text=adb_obj.description,
            organization=adb_obj.project_name,
            language=language
        )
        
        # Use Philippines as fallback if no country detected (ADB HQ)
        if not country:
            country = "Philippines"
            logger.info(f"Using default country (Philippines) for ADB tender {adb_obj.id}")
        
        # Extract city information
        city = extract_city_info(adb_obj)
        
        # Extract organization and buyer information
        organization_name, buyer_info = extract_organization_and_buyer(adb_obj.description)
        
        # Use project name as organization if none found
        if not organization_name and adb_obj.project_name:
            organization_name = adb_obj.project_name
        
        # Extract financial information
        estimated_value, currency = extract_enhanced_financial_info(adb_obj)
        
        # Extract and categorize sectors
        sectors = extract_enhanced_sector_info(adb_obj)
        
        # Process document links
        document_links = normalize_document_links_enhanced(adb_obj)
        
        # Construct the UnifiedTender with improved data
        unified = UnifiedTender(
            # Required fields
            title=adb_obj.notice_title or "Untitled ADB Tender",
            source_table="adb",
            source_id=str(adb_obj.id),
            
            # Additional fields with enhanced data
            description=adb_obj.description,
            tender_type=adb_obj.type,
            publication_date=publication_dt,
            deadline_date=deadline_dt,
            country=country,
            city=city,
            organization_name=organization_name,
            buyer=buyer_info,
            project_name=adb_obj.project_name,
            project_id=adb_obj.project_id,
            project_number=adb_obj.project_number,
            sector=sectors[0] if sectors else adb_obj.sector,  # Use first detected sector or original
            url=adb_obj.pdf_url,
            reference_number=adb_obj.borrower_bid_no,
            document_links=document_links,
            estimated_value=estimated_value,
            currency=currency,
            original_data={
                **row,
                'detected_sectors': sectors,
                'normalized_method': 'enhanced_adb_normalizer'
            },
            language=language,
        )

        # Apply translations if needed
        if language != 'en':
            unified = apply_translations(unified, language)
        
        # Log normalization results
        log_tender_normalization(
            source="adb",
            tender_id=str(adb_obj.id),
            data={
                "detected_city": city,
                "detected_sectors": sectors,
                "extracted_organization": organization_name,
                "extracted_buyer": buyer_info,
                "financial_info": f"{estimated_value} {currency}" if estimated_value and currency else None
            }
        )

        return unified
        
    except Exception as e:
        logger.error(f"Error normalizing ADB tender: {e}")
        # Return minimal tender with error info
        return UnifiedTender(
            title="Normalization Error",
            source_table="adb",
            source_id=str(row.get('id', 'unknown')),
            fallback_reason=f"Normalization error: {str(e)}",
            original_data=row
        ) 