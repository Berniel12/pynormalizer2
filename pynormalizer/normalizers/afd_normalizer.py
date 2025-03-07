import json
from datetime import datetime
from typing import Dict, Any, Optional
import re

from pynormalizer.models.source_models import AFDTender
from pynormalizer.models.unified_model import UnifiedTender
from pynormalizer.utils.translation import (
    translate_to_english, detect_language, apply_translations
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
    ensure_country
)

def normalize_afd(row: Dict[str, Any]) -> UnifiedTender:
    """
    Normalize an AFD tender record.
    
    Args:
        row: Dictionary containing AFD tender data
        
    Returns:
        Normalized UnifiedTender instance
    """
    # Validate with Pydantic
    try:
        afd_obj = AFDTender(**row)
    except Exception as e:
        raise ValueError(f"Failed to validate AFD tender: {e}")

    # Parse string dates if provided
    publication_dt = None
    deadline_dt = None
    
    # Try to extract publication date from various fields
    if afd_obj.publication_date:
        publication_dt = parse_date_string(afd_obj.publication_date)
    
    # If still no publication date, try to extract from notice content
    if not publication_dt and afd_obj.notice_content and afd_obj.notice_content != "NO CONTENT":
        publication_dt = parse_date_from_text(afd_obj.notice_content)
    
    # Try to extract deadline date from deadline field
    if afd_obj.deadline:
        deadline_dt = parse_date_string(afd_obj.deadline)
    
    # If no deadline found, try to extract from notice content
    if not deadline_dt and afd_obj.notice_content and afd_obj.notice_content != "NO CONTENT":
        # Look for deadline patterns in the content
        deadline_dt = parse_date_from_text(afd_obj.notice_content)
    
    # Detect language using combined text from title and description
    language_sample = ""
    if afd_obj.notice_title:
        language_sample += afd_obj.notice_title + " "
    if afd_obj.notice_content and afd_obj.notice_content != "NO CONTENT":
        language_sample += afd_obj.notice_content[:200]  # Use first 200 chars
    
    language = detect_language(language_sample.strip()) or "fr"  # Default to French for AFD
    
    # Use the improved extract_status function
    status = extract_status(
        deadline=deadline_dt,
        description=afd_obj.notice_content if afd_obj.notice_content != "NO CONTENT" else None,
        publication_date=publication_dt
    )
    
    # Use the improved organization extraction
    organization_name, buyer_info = extract_organization_and_buyer(
        afd_obj.notice_content if afd_obj.notice_content != "NO CONTENT" else None
    )
    
    # If no organization from extraction, use the agency field
    if not organization_name and afd_obj.agency:
        organization_name = afd_obj.agency
    
    # If no buyer from extraction, use the buyer field
    if not buyer_info and afd_obj.buyer:
        buyer_info = afd_obj.buyer
        
    # If still no organization but we have buyer, use that
    if not organization_name and buyer_info:
        organization_name = buyer_info
    
    # Extract tender_type from notice title or content
    tender_type = None
    if afd_obj.notice_title:
        if any(term in afd_obj.notice_title.lower() for term in ['request for proposal', 'rfp']):
            tender_type = "Request for Proposal"
        elif any(term in afd_obj.notice_title.lower() for term in ['request for quotation', 'rfq']):
            tender_type = "Request for Quotation"
        elif any(term in afd_obj.notice_title.lower() for term in ['invitation for bid', 'ifb', 'invitation to bid', 'itb']):
            tender_type = "Invitation for Bid"
        elif any(term in afd_obj.notice_title.lower() for term in ['expression of interest', 'eoi']):
            tender_type = "Expression of Interest"
    
    # Extract procurement_method from content
    procurement_method = None
    if afd_obj.notice_content and afd_obj.notice_content != "NO CONTENT":
        procurement_method = extract_procurement_method(afd_obj.notice_content)
    
    # Extract financial information from notice content if available
    estimated_value = None
    currency = None
    
    # Try to get financial information from contract_amount/value fields
    if hasattr(afd_obj, 'contract_amount') and afd_obj.contract_amount and isinstance(afd_obj.contract_amount, str):
        estimated_value, currency = extract_financial_info(afd_obj.contract_amount)
    
    # If no financial info found, try to extract from description
    if (not estimated_value or not currency) and afd_obj.notice_content:
        # Look for specific Rwandan Franc pattern first
        rwf_pattern = r'(?:Rwf|RWF)\s*([\d,\.]+(?:\s*million|\s*m|\s*billion|\s*b)?)'
        rwf_matches = re.findall(rwf_pattern, afd_obj.notice_content, re.IGNORECASE)
        
        if rwf_matches:
            try:
                # Process the value
                value_str = rwf_matches[0].replace(',', '')
                multiplier = 1
                
                if 'million' in value_str.lower() or ' m' in value_str.lower():
                    multiplier = 1000000
                    value_str = re.sub(r'million|m', '', value_str, flags=re.IGNORECASE).strip()
                elif 'billion' in value_str.lower() or ' b' in value_str.lower():
                    multiplier = 1000000000
                    value_str = re.sub(r'billion|b', '', value_str, flags=re.IGNORECASE).strip()
                    
                estimated_value = float(value_str) * multiplier
                currency = 'RWF'
            except (ValueError, IndexError):
                # If parsing fails, try the general method
                estimated_value, currency = extract_financial_info(afd_obj.notice_content)
        else:
            # If no specific RWF pattern found, use general extraction
            estimated_value, currency = extract_financial_info(afd_obj.notice_content)
    
    # If still no currency but value exists, check for context clues
    if estimated_value and not currency:
        # Check for common currency mentions in the content
        if afd_obj.notice_content:
            if 'rwanda' in afd_obj.notice_content.lower() and re.search(r'\bRwf\b|\bRWF\b', afd_obj.notice_content, re.IGNORECASE):
                currency = 'RWF'
            elif 'france' in afd_obj.notice_content.lower() or 'euro' in afd_obj.notice_content.lower():
                currency = 'EUR'
            elif re.search(r'\bUSD\b|\$', afd_obj.notice_content):
                currency = 'USD'
    
    # Correct common currency code mistakes
    if currency == 'ZAR' and 'rwanda' in (afd_obj.country or '').lower():
        currency = 'RWF'
    
    # Ensure proper organization name
    organization_name = afd_obj.agency
    if not organization_name and afd_obj.notice_content and afd_obj.notice_content != "NO CONTENT":
        organization_name = extract_organization(afd_obj.notice_content)
    
    # Process document links
    document_links = []
    if afd_obj.services:
        document_links = normalize_document_links(afd_obj.services)

    # Make sure country is never empty
    country = afd_obj.country if afd_obj.country else None
    
    # Use our fallback mechanisms to ensure country is populated
    normalized_country = ensure_country(
        country_value=country,
        text=afd_obj.notice_content if afd_obj.notice_content and afd_obj.notice_content != "NO CONTENT" else None,
        organization=organization_name,
        email=afd_obj.email,
        language=language
    )
    
    # Never use None as a country value - keep the original value if normalization returns None
    if normalized_country is not None:
        country = normalized_country
    elif not country and organization_name and 'france' in organization_name.lower():
        country = 'France'  # Default country for AFD is France when no other information is available

    # Construct the UnifiedTender
    unified = UnifiedTender(
        # Required fields
        title=afd_obj.notice_title or "No title",  # Placeholder if missing
        source_table="afd",
        source_id=str(afd_obj.id),
        
        # Additional fields
        description=afd_obj.notice_content if afd_obj.notice_content and afd_obj.notice_content != "NO CONTENT" else None,
        tender_type=tender_type,
        status=status,
        publication_date=publication_dt,
        deadline_date=deadline_dt,
        country=country,  # Using our guaranteed non-empty country
        city=afd_obj.city_locality,
        buyer=buyer_info,
        organization_name=organization_name,
        language=language,
        contact_email=afd_obj.email,
        contact_address=afd_obj.address,
        url=afd_obj.url,
        notice_id=afd_obj.notice_id,
        document_links=document_links,
        estimated_value=estimated_value,
        currency=currency,
        procurement_method=procurement_method,
        original_data=row,
        normalized_method="offline-dictionary",
    )

    # Use the common apply_translations function
    unified = apply_translations(unified, language)

    return unified 