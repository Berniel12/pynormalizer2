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

    # Extract title
    title = tedeu_obj.title if hasattr(tedeu_obj, 'title') and tedeu_obj.title else None
    
    # Use summary as description since TED EU model doesn't have a description field
    description = None
    if hasattr(tedeu_obj, 'summary') and tedeu_obj.summary:
        description = tedeu_obj.summary
    
    # Extract procurement method
    procurement_method = None
    if hasattr(tedeu_obj, 'procedure_type') and tedeu_obj.procedure_type:
        procurement_method = tedeu_obj.procedure_type.capitalize()
    
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
            extracted_country, extracted_city = extract_location_info(tedeu_obj.contact_address)
            if extracted_country:
                country = extracted_country
            if not city and extracted_city:
                city = extracted_city
        
        # Try from the description as a last resort
        if not country and hasattr(tedeu_obj, 'summary') and tedeu_obj.summary:
            extracted_country, extracted_city = extract_location_info(tedeu_obj.summary)
            if extracted_country:
                country = extracted_country
            if not city and extracted_city:
                city = extracted_city
    
    # Safe attribute access for city
    if hasattr(tedeu_obj, 'city') and tedeu_obj.city:
        city = tedeu_obj.city
    elif hasattr(tedeu_obj, 'place') and tedeu_obj.place:
        city = tedeu_obj.place
    
    # If still no city, try to extract from address or contact information
    if not city:
        if hasattr(tedeu_obj, 'contact_address') and tedeu_obj.contact_address:
            # Extract city from contact address using helper function
            extracted_country, extracted_city = extract_location_info(tedeu_obj.contact_address)
            if extracted_city:
                city = extracted_city
                
        # Try from the description as a last resort
        if not city and hasattr(tedeu_obj, 'summary') and tedeu_obj.summary:
            extracted_country, extracted_city = extract_location_info(tedeu_obj.summary)
            if extracted_city:
                city = extracted_city
    
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
    
    # Extract reference numbers
    reference_number = None
    if hasattr(tedeu_obj, 'reference_number') and tedeu_obj.reference_number:
        reference_number = tedeu_obj.reference_number
    elif hasattr(tedeu_obj, 'doc_id') and tedeu_obj.doc_id:
        reference_number = tedeu_obj.doc_id
    
    # Translate title and description to English if not in English
    title_english = None
    description_english = None
    
    # Detect language - check all text fields for better accuracy
    language_sample = ""
    
    # Create a combined sample using title + summary + other relevant text
    if hasattr(tedeu_obj, 'title') and tedeu_obj.title:
        language_sample += tedeu_obj.title + " "
    
    if hasattr(tedeu_obj, 'summary') and tedeu_obj.summary:
        # Add a truncated version of the summary (first 300 chars)
        language_sample += tedeu_obj.summary[:300] + " "
    
    if hasattr(tedeu_obj, 'buyer') and tedeu_obj.buyer:
        language_sample += tedeu_obj.buyer + " "
    
    # Add organization name if available and different from buyer
    buyer_value = tedeu_obj.buyer if hasattr(tedeu_obj, 'buyer') else None
    if organization_name and hasattr(tedeu_obj, 'buyer') and organization_name != buyer_value:
        language_sample += organization_name + " "
    
    # Detect language from combined sample
    detected_language = detect_language(language_sample.strip())
    
    # Validate language code - TED_EU often has invalid language codes
    valid_languages = ['en', 'fr', 'de', 'es', 'it', 'pt', 'nl', 'da', 'sv', 'fi', 'el', 'cs', 'et', 'hu', 'lt', 'lv', 'mt', 'pl', 'sk', 'sl', 'bg', 'ro', 'ga', 'hr']
    
    if detected_language and detected_language in valid_languages:
        language = detected_language
    else:
        # Try to get language from the documents or original data
        if tedeu_obj.language:
            lang_code = tedeu_obj.language.lower()[:2]  # Extract first 2 chars of language code
            if lang_code in valid_languages:
                language = lang_code
            else:
                language = 'en'  # Default to English if invalid
        else:
            language = 'en'  # Default to English if detection fails
    
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
        source_id=str(tedeu_obj.id) if hasattr(tedeu_obj, 'id') and tedeu_obj.id is not None else None,
        normalized_by="pynormalizer",
        title_english=title_english,
        description_english=description_english,
        organization_name_english=organization_name_english,
        buyer_english=buyer_english,
        project_name_english=None,  # Not directly available
    )
    
    return normalized_tender 