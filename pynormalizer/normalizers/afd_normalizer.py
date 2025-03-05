import json
from datetime import datetime
from typing import Dict, Any, Optional

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
    extract_status
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
    
    try:
        if afd_obj.publication_date:
            publication_dt = datetime.fromisoformat(afd_obj.publication_date.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        # Just leave as None if we can't parse
        pass
        
    try:
        if afd_obj.deadline:
            deadline_dt = datetime.fromisoformat(afd_obj.deadline.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        # Just leave as None if we can't parse
        pass

    # Detect language from original_language field or content
    language = afd_obj.original_language or 'auto'
    if language == 'auto' and afd_obj.notice_content:
        detected = detect_language(afd_obj.notice_content)
        if detected:
            language = detected
    
    # Extract status based on deadline
    status = extract_status(
        deadline=deadline_dt,
        description=afd_obj.notice_content if afd_obj.notice_content != "NO CONTENT" else None
    )
    
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
    
    # Try to extract financial information from content
    estimated_value = None
    currency = None
    if afd_obj.notice_content and afd_obj.notice_content != "NO CONTENT":
        estimated_value, currency = extract_financial_info(afd_obj.notice_content)
    
    # Ensure proper organization name
    organization_name = afd_obj.agency
    if not organization_name and afd_obj.notice_content and afd_obj.notice_content != "NO CONTENT":
        organization_name = extract_organization(afd_obj.notice_content)
    
    # Process document links
    document_links = []
    if afd_obj.services:
        document_links = normalize_document_links(afd_obj.services)

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
        country=afd_obj.country,
        city=afd_obj.city_locality,
        buyer=afd_obj.buyer,
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