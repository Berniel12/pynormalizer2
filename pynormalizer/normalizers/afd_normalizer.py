import json
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
import re
import logging

from pynormalizer.models.source_models import AFDTender
from pynormalizer.models.unified_model import UnifiedTender
from pynormalizer.utils.translation import (
    translate_to_english, detect_language, apply_translations, detect_language_with_fallback
)
from pynormalizer.utils.normalizer_helpers import (
    normalize_document_links,
    extract_financial_info,
    extract_location_info,
    extract_organization,
    extract_procurement_method,
    extract_status,
    extract_organization_and_buyer,
    parse_date_string,
    parse_date_from_text,
    ensure_country,
    clean_price,
    log_tender_normalization
)

logger = logging.getLogger(__name__)

# Improved regex patterns for financial information
AMOUNT_PATTERNS = [
    r'(?:montant|amount|value|budget|cost|estimate).*?(?:EUR|USD|€|\$|RWF)?\s*([\d,.]+(?:\s*[mM](?:illion)?|\s*[bB](?:illion)?)?)',
    r'(?:EUR|USD|€|\$|RWF)\s*([\d,.]+(?:\s*[mM](?:illion)?|\s*[bB](?:illion)?)?)',
    r'([\d,.]+(?:\s*[mM](?:illion)?|\s*[bB](?:illion)?))\s*(?:EUR|USD|€|\$|RWF)'
]

# Enhanced procurement method patterns
PROCUREMENT_PATTERNS = {
    'open': [
        r'(?:appel|call)\s+(?:d\'offres?|for\s+tenders?)\s+(?:ouvert|open)',
        r'open\s+(?:tender|bidding|competition)',
        r'competitive\s+bidding'
    ],
    'restricted': [
        r'(?:appel|call)\s+(?:d\'offres?|for\s+tenders?)\s+restreint',
        r'restricted\s+(?:tender|bidding)',
        r'pre[-\s]qualified\s+bidders'
    ],
    'direct': [
        r'(?:marché|contract)\s+(?:de\s+gré\s+à\s+gré|direct)',
        r'direct\s+(?:contract|award|procurement)',
        r'single[-\s]source'
    ],
    'framework': [
        r'accord[-\s]cadre',
        r'framework\s+agreement',
        r'multiple[-\s]supplier'
    ]
}

def safe_get_value(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get a value from a dictionary with type checking."""
    try:
        value = data.get(key, default)
        return value if value not in (None, "", "null", "undefined") else default
    except (KeyError, AttributeError):
        return default

def extract_enhanced_financial_info(tender: AFDTender) -> Tuple[Optional[float], Optional[str]]:
    """Extract financial information with improved pattern matching and validation."""
    amount, currency = None, None
    
    # Try contract_amount first if it exists
    if hasattr(tender, 'contract_amount'):
        try:
            contract_amount = str(tender.contract_amount)
            if contract_amount and contract_amount.strip():
                # Try to extract amount and currency
                amount, currency = extract_financial_info(contract_amount)
        except (AttributeError, ValueError) as e:
            logger.warning(f"Error processing contract_amount: {e}")
    
    # If no amount/currency found, try notice_content
    if (not amount or not currency) and tender.notice_content and tender.notice_content != "NO CONTENT":
        content = tender.notice_content
        
        # Try each pattern in order
        for pattern in AMOUNT_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    value_str = match.group(1).strip()
                    
                    # Handle million/billion abbreviations
                    multiplier = 1
                    if any(x in value_str.lower() for x in ['m', 'million']):
                        multiplier = 1_000_000
                        value_str = re.sub(r'[mM](?:illion)?', '', value_str)
                    elif any(x in value_str.lower() for x in ['b', 'billion']):
                        multiplier = 1_000_000_000
                        value_str = re.sub(r'[bB](?:illion)?', '', value_str)
                    
                    # Clean and convert to float
                    value_str = re.sub(r'[^\d.]', '', value_str)
                    amount = float(value_str) * multiplier
                    
                    # Try to determine currency from context
                    if not currency:
                        if '€' in content or 'EUR' in content:
                            currency = 'EUR'
                        elif '$' in content or 'USD' in content:
                            currency = 'USD'
                        elif 'RWF' in content.upper() or 'FRW' in content.upper():
                            currency = 'RWF'
                    
                    if amount and currency:
                        break
                except (ValueError, IndexError) as e:
                    logger.debug(f"Failed to parse amount from {value_str}: {e}")
                    continue
            
            if amount and currency:
                break
    
    # Validate and clean the amount
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
            'EURO': 'EUR',
            'EUROS': 'EUR',
            'FRW': 'RWF',
            'RWFR': 'RWF'
        }
        currency = currency_map.get(currency, currency)
    
    return amount, currency

def detect_languages(tender: AFDTender) -> List[str]:
    """Detect languages from multiple fields with improved accuracy."""
    languages = set()
    
    # Check title
    if tender.notice_title:
        lang = detect_language_with_fallback(tender.notice_title)
        if lang:
            languages.add(lang)
    
    # Check content in chunks to improve accuracy
    if tender.notice_content and tender.notice_content != "NO CONTENT":
        # Split content into chunks of ~500 characters at word boundaries
        chunks = re.findall(r'.{1,500}(?:\s|$)', tender.notice_content)
        for chunk in chunks:
            lang = detect_language_with_fallback(chunk)
            if lang:
                languages.add(lang)
    
    # Always include French for AFD tenders if no language detected
    if not languages:
        languages.add('fr')
    
    return list(languages)

def extract_enhanced_procurement_method(tender: AFDTender) -> Optional[str]:
    """Extract procurement method with improved pattern matching."""
    if not tender.notice_content or tender.notice_content == "NO CONTENT":
        return None
        
    content = tender.notice_content.lower()
    
    # Check each procurement type
    for method, patterns in PROCUREMENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return method
    
    # Try the general extraction as fallback
    return extract_procurement_method(tender.notice_content)

def normalize_afd(row: Dict[str, Any]) -> UnifiedTender:
    """
    Normalize an AFD tender record with improved validation and fallbacks.
    
    Args:
        row: Dictionary containing AFD tender data
        
    Returns:
        Normalized UnifiedTender instance
    """
    # Validate with Pydantic
    try:
        afd_obj = AFDTender(**row)
    except Exception as e:
        logger.error(f"Failed to validate AFD tender: {e}")
        # Create minimal tender with error info
        return UnifiedTender(
            title="Validation Error",
            source_table="afd",
            source_id=str(safe_get_value(row, 'id', 'unknown')),
            fallback_reason=f"Validation error: {str(e)}",
            original_data=row
        )

    try:
        # Parse string dates with improved error handling
        publication_dt = None
        deadline_dt = None
        
        # Try to extract publication date from various fields
        if afd_obj.publication_date:
            publication_dt = parse_date_string(afd_obj.publication_date)
        
        # If still no publication date, try to extract from notice content
        if not publication_dt and afd_obj.notice_content and afd_obj.notice_content != "NO CONTENT":
            publication_dt = parse_date_from_text(afd_obj.notice_content)
        
        # Try to extract deadline date with fallbacks
        if afd_obj.deadline:
            deadline_dt = parse_date_string(afd_obj.deadline)
        
        if not deadline_dt and afd_obj.notice_content and afd_obj.notice_content != "NO CONTENT":
            deadline_dt = parse_date_from_text(afd_obj.notice_content)
        
        # Detect multiple languages
        languages = detect_languages(afd_obj)
        primary_language = languages[0] if languages else 'fr'
        
        # Extract status with fallback
        status = extract_status(
            afd_obj.notice_content if afd_obj.notice_content != "NO CONTENT" else None
        ) or 'unknown'
        
        # Enhanced organization extraction
        organization_name, buyer_info = extract_organization_and_buyer(
            afd_obj.notice_content if afd_obj.notice_content != "NO CONTENT" else None
        )
        
        # Fallback chain for organization name
        organization_name = (
            organization_name or
            afd_obj.agency or
            afd_obj.buyer or
            buyer_info or
            "Agence Française de Développement"  # Ultimate fallback
        )
        
        # Enhanced tender type extraction
        tender_type = None
        if afd_obj.notice_title:
            title_lower = afd_obj.notice_title.lower()
            type_patterns = {
                'Request for Proposal': ['request for proposal', 'rfp', 'demande de proposition'],
                'Request for Quotation': ['request for quotation', 'rfq', 'demande de devis'],
                'Invitation for Bid': ['invitation for bid', 'ifb', 'invitation to bid', 'itb', 'appel d\'offres'],
                'Expression of Interest': ['expression of interest', 'eoi', 'manifestation d\'intérêt']
            }
            
            for type_name, patterns in type_patterns.items():
                if any(pattern in title_lower for pattern in patterns):
                    tender_type = type_name
                    break
        
        # Enhanced procurement method extraction
        procurement_method = extract_enhanced_procurement_method(afd_obj)
        
        # Improved financial information extraction
        estimated_value, currency = extract_enhanced_financial_info(afd_obj)
        
        # Process document links with validation
        document_links = []
        if afd_obj.services:
            try:
                document_links = normalize_document_links(afd_obj.services)
            except Exception as e:
                logger.warning(f"Error normalizing document links: {e}")
        
        # Enhanced country detection with multiple fallbacks
        country = ensure_country(
            country_value=afd_obj.country,
            text=afd_obj.notice_content if afd_obj.notice_content != "NO CONTENT" else None,
            organization=organization_name,
            email=afd_obj.email,
            language=primary_language
        )
        
        # Fallback to France if no country detected (AFD is French)
        if not country:
            country = "France"
        
        # Construct the UnifiedTender with improved fallbacks
        unified = UnifiedTender(
            # Required fields
            title=afd_obj.notice_title or "Untitled AFD Tender",
            source_table="afd",
            source_id=str(afd_obj.id),
            
            # Additional fields with fallbacks
            description=afd_obj.notice_content if afd_obj.notice_content != "NO CONTENT" else None,
            tender_type=tender_type,
            status=status,
            publication_date=publication_dt,
            deadline_date=deadline_dt,
            country=country,
            city=afd_obj.city_locality,
            buyer=buyer_info,
            organization_name=organization_name,
            language=primary_language,
            contact_email=afd_obj.email,
            contact_address=afd_obj.address,
            url=afd_obj.url,
            notice_id=afd_obj.notice_id,
            document_links=document_links,
            estimated_value=estimated_value,
            currency=currency,
            procurement_method=procurement_method,
            original_data=row,
            normalized_method="pynormalizer",
            translations=json.dumps({"detected_languages": languages}) if len(languages) > 1 else None
        )
        
        # Apply translations for multi-language content
        if len(languages) > 1:
            unified = apply_translations(unified, primary_language)
        
        return unified
        
    except Exception as e:
        logger.error(f"Error normalizing AFD tender: {e}")
        # Return minimal tender with error info
        return UnifiedTender(
            title="Normalization Error",
            source_table="afd",
            source_id=str(safe_get_value(row, 'id', 'unknown')),
            fallback_reason=f"Normalization error: {str(e)}",
            original_data=row
        ) 