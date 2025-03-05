from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import json
import re
import uuid

from pynormalizer.models.source_models import TEDEuTender
from pynormalizer.models.unified_model import UnifiedTender
from pynormalizer.utils.translation import (
    translate_to_english, detect_language, apply_translations
)
from pynormalizer.utils.normalizer_helpers import (
    normalize_document_links, 
    extract_financial_info, 
    extract_location_info,
    extract_procurement_method,
    extract_organization,
    extract_status
)

def normalize_tedeu(row: Dict[str, Any]) -> UnifiedTender:
    """
    Normalize a TED.eu (Tenders Electronic Daily) tender record.
    
    Args:
        row: Dictionary containing TED.eu tender data
        
    Returns:
        Normalized UnifiedTender instance
    """
    # Validate with Pydantic
    try:
        tedeu_obj = TEDEuTender(**row)
    except Exception as e:
        raise ValueError(f"Failed to validate TED.eu tender: {e}")

    # Convert date objects to datetime if needed
    publication_dt = None
    if hasattr(tedeu_obj, 'publication_date') and tedeu_obj.publication_date:
        if isinstance(tedeu_obj.publication_date, datetime):
            publication_dt = tedeu_obj.publication_date
        else:
            publication_dt = datetime.combine(tedeu_obj.publication_date, datetime.min.time())
    
    deadline_dt = None
    if hasattr(tedeu_obj, 'deadline_date') and tedeu_obj.deadline_date:
        if isinstance(tedeu_obj.deadline_date, datetime):
            deadline_dt = tedeu_obj.deadline_date
        else:
            deadline_dt = datetime.combine(tedeu_obj.deadline_date, datetime.min.time())

    # Determine procurement method from procedure_type or description
    procurement_method = None
    if hasattr(tedeu_obj, 'procedure_type') and tedeu_obj.procedure_type:
        # Map TED procedure types to general procurement methods
        procurement_map = {
            "OPEN": "Open Procedure",
            "RESTRICTED": "Restricted Procedure",
            "COMPETITIVE_NEGOTIATION": "Competitive Procedure with Negotiation",
            "COMPETITIVE_DIALOGUE": "Competitive Dialogue",
            "INNOVATION_PARTNERSHIP": "Innovation Partnership",
            "DESIGN_CONTEST": "Design Contest",
            "NEGOTIATED_WITH_PRIOR_CALL": "Negotiated Procedure with Prior Call for Competition",
            "NEGOTIATED_WITHOUT_PRIOR_CALL": "Negotiated Procedure without Prior Call for Competition",
        }
        procurement_method = procurement_map.get(tedeu_obj.procedure_type.upper(), tedeu_obj.procedure_type)
    
    # If not found in procedure_type, try to extract from description or additional_information
    if not procurement_method:
        description_text = ""
        if hasattr(tedeu_obj, 'summary') and tedeu_obj.summary:
            description_text += tedeu_obj.summary + " "
        if hasattr(tedeu_obj, 'additional_information') and tedeu_obj.additional_information:
            description_text += tedeu_obj.additional_information + " "
            
        # Try to identify procurement method from description
        procurement_keywords = {
            "open procedure": "Open Procedure",
            "restricted procedure": "Restricted Procedure",
            "competitive dialogue": "Competitive Dialogue",
            "negotiated procedure": "Negotiated Procedure",
            "innovation partnership": "Innovation Partnership",
            "design contest": "Design Contest"
        }
        
        desc_lower = description_text.lower()
        for keyword, method in procurement_keywords.items():
            if keyword in desc_lower:
                procurement_method = method
                break
    
    # Extract country and city information safely
    country = None
    city = None
    
    # Safe attribute access for country
    if hasattr(tedeu_obj, 'country') and tedeu_obj.country:
        country = tedeu_obj.country
    elif hasattr(tedeu_obj, 'country_code') and tedeu_obj.country_code:
        # Map country codes to country names if needed
        country = tedeu_obj.country_code
    
    # If still no country, try to extract from address or contact information
    if not country:
        if hasattr(tedeu_obj, 'contact_address') and tedeu_obj.contact_address:
            # Extract country from contact address using helper function
            extracted_location = extract_location_info(tedeu_obj.contact_address)
            if extracted_location and extracted_location.get('country'):
                country = extracted_location['country']
        
        # Try from the description as a last resort
        if not country and hasattr(tedeu_obj, 'description') and tedeu_obj.description:
            extracted_location = extract_location_info(tedeu_obj.description)
            if extracted_location and extracted_location.get('country'):
                country = extracted_location['country']
    
    # Safe attribute access for city
    if hasattr(tedeu_obj, 'city') and tedeu_obj.city:
        city = tedeu_obj.city
    elif hasattr(tedeu_obj, 'place') and tedeu_obj.place:
        city = tedeu_obj.place
    
    # If still no city, try to extract from address or contact information
    if not city:
        if hasattr(tedeu_obj, 'contact_address') and tedeu_obj.contact_address:
            # Extract city from contact address using helper function
            extracted_location = extract_location_info(tedeu_obj.contact_address)
            if extracted_location and extracted_location.get('city'):
                city = extracted_location['city']
                
        # Try from the description as a last resort
        if not city and hasattr(tedeu_obj, 'description') and tedeu_obj.description:
            extracted_location = extract_location_info(tedeu_obj.description)
            if extracted_location and extracted_location.get('city'):
                city = extracted_location['city']
    
    # Extract estimated value and currency from various fields
    estimated_value = None
    currency = None
    
    # Try to extract from specific financial fields if available
    if hasattr(tedeu_obj, 'estimated_value') and tedeu_obj.estimated_value:
        if isinstance(tedeu_obj.estimated_value, (int, float)):
            estimated_value = float(tedeu_obj.estimated_value)
        elif isinstance(tedeu_obj.estimated_value, str):
            try:
                estimated_value = float(tedeu_obj.estimated_value.replace(',', ''))
            except (ValueError, TypeError):
                pass
    
    if hasattr(tedeu_obj, 'currency') and tedeu_obj.currency:
        currency = tedeu_obj.currency
    
    # Try to extract from description or additional_information
    if hasattr(tedeu_obj, 'summary') and tedeu_obj.summary:
        extracted_value, extracted_currency = extract_financial_info(tedeu_obj.summary)
        if not estimated_value and extracted_value:
            estimated_value = extracted_value
        if not currency and extracted_currency:
            currency = extracted_currency
    
    if not estimated_value and hasattr(tedeu_obj, 'additional_information') and tedeu_obj.additional_information:
        extracted_value, extracted_currency = extract_financial_info(tedeu_obj.additional_information)
        if not estimated_value and extracted_value:
            estimated_value = extracted_value
        if not currency and extracted_currency:
            currency = extracted_currency
    
    # Use the normalize_document_links helper to standardize links
    document_links = []
    if hasattr(tedeu_obj, 'links') and tedeu_obj.links:
        document_links = normalize_document_links(tedeu_obj.links)
    
    # Extract or determine the language
    language = None
    if hasattr(tedeu_obj, 'language') and tedeu_obj.language:
        language = tedeu_obj.language
    
    if not language or language == "None":
        # Try to detect from title or summary
        if hasattr(tedeu_obj, 'title') and tedeu_obj.title:
            detected = detect_language(tedeu_obj.title)
            if detected:
                language = detected
        elif hasattr(tedeu_obj, 'summary') and tedeu_obj.summary and not language:
            detected = detect_language(tedeu_obj.summary)
            if detected:
                language = detected
    
    # Extract organization information
    organization_name = None
    buyer = None
    
    if hasattr(tedeu_obj, 'authority_name') and tedeu_obj.authority_name:
        organization_name = tedeu_obj.authority_name
    
    if hasattr(tedeu_obj, 'buyer_name') and tedeu_obj.buyer_name:
        buyer = tedeu_obj.buyer_name
    
    # Determine status based on dates and explicit status field
    status = None
    if hasattr(tedeu_obj, 'status') and tedeu_obj.status:
        status = tedeu_obj.status
    else:
        # Derive status from dates if not explicitly set
        current_dt = datetime.now()
        
        if deadline_dt and current_dt > deadline_dt:
            status = "Closed"
        elif publication_dt and current_dt >= publication_dt:
            status = "Open"
        elif publication_dt and current_dt < publication_dt:
            status = "Planned"
        else:
            # Default to Active if we have any dates
            if publication_dt or deadline_dt:
                status = "Active"
    
    # Extract contact information
    contact_name = None
    contact_email = None
    contact_phone = None
    contact_address = None
    
    if hasattr(tedeu_obj, 'contact_name') and tedeu_obj.contact_name:
        contact_name = tedeu_obj.contact_name
    
    if hasattr(tedeu_obj, 'contact_email') and tedeu_obj.contact_email:
        contact_email = tedeu_obj.contact_email
    
    if hasattr(tedeu_obj, 'contact_phone') and tedeu_obj.contact_phone:
        contact_phone = tedeu_obj.contact_phone
    
    if hasattr(tedeu_obj, 'contact_address') and tedeu_obj.contact_address:
        contact_address = tedeu_obj.contact_address
    
    # Extract title and description information
    title = None
    description = None
    
    if hasattr(tedeu_obj, 'title') and tedeu_obj.title:
        title = tedeu_obj.title
    
    if hasattr(tedeu_obj, 'summary') and tedeu_obj.summary:
        description = tedeu_obj.summary
        
        # Add additional information to description if available
        if hasattr(tedeu_obj, 'additional_information') and tedeu_obj.additional_information:
            description += "\n\n" + tedeu_obj.additional_information
    
    # Extract reference numbers
    reference_number = None
    if hasattr(tedeu_obj, 'reference_number') and tedeu_obj.reference_number:
        reference_number = tedeu_obj.reference_number
    elif hasattr(tedeu_obj, 'doc_id') and tedeu_obj.doc_id:
        reference_number = tedeu_obj.doc_id
    
    # Translate title and description to English if not in English
    title_english = None
    description_english = None
    
    if title:
        title_english, title_method = translate_to_english(title, language)
    
    if description:
        description_english, desc_method = translate_to_english(description, language)
    
    # Translate organization name and buyer to English
    organization_name_english = None
    buyer_english = None
    
    if organization_name:
        organization_name_english, org_method = translate_to_english(organization_name, language)
    
    if buyer:
        buyer_english, buyer_method = translate_to_english(buyer, language)
    
    # Create the UnifiedTender object
    normalized_tender = UnifiedTender(
        id=str(uuid.uuid4()),  # Generate a new UUID for the unified record
        title=title,
        description=description,
        tender_type=None,  # Not directly available in TED.eu data
        status=status,
        publication_date=publication_dt,
        deadline_date=deadline_dt,
        country=country,
        city=city,
        organization_name=organization_name,
        organization_id=None,  # Not directly available
        buyer=buyer,
        project_name=None,  # Not directly available
        project_id=None,  # Not directly available
        project_number=None,  # Not directly available
        sector=None,  # Not directly available
        estimated_value=estimated_value,
        currency=currency,
        contact_name=contact_name,
        contact_email=contact_email,
        contact_phone=contact_phone,
        contact_address=contact_address,
        url=tedeu_obj.url if hasattr(tedeu_obj, 'url') and tedeu_obj.url else None,
        document_links=document_links,
        language=language,
        notice_id=tedeu_obj.notice_id if hasattr(tedeu_obj, 'notice_id') and tedeu_obj.notice_id else None,
        reference_number=reference_number,
        procurement_method=procurement_method,
        original_data=tedeu_obj.original_data if hasattr(tedeu_obj, 'original_data') and tedeu_obj.original_data else None,
        source_table="tedeu",
        source_id=tedeu_obj.id if hasattr(tedeu_obj, 'id') and tedeu_obj.id else None,
        normalized_by="pynormalizer",
        title_english=title_english,
        description_english=description_english,
        organization_name_english=organization_name_english,
        buyer_english=buyer_english,
        project_name_english=None,  # Not directly available
    )
    
    return normalized_tender 