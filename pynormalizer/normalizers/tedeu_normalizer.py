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
    extract_status,
    extract_organization_and_buyer,
    ensure_country,
    extract_country_from_text
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

    # Extract and normalize title and description
    raw_title = tedeu_obj.title if hasattr(tedeu_obj, 'title') and tedeu_obj.title else None
    raw_description = tedeu_obj.summary if hasattr(tedeu_obj, 'summary') and tedeu_obj.summary else None
    
    title = normalize_title(raw_title)
    description = normalize_description(raw_description)
    
    # Detect language with improved accuracy using multiple fields
    language_sample = ""
    if title:
        language_sample += title + " "
    if description:
        language_sample += description[:500] + " "
    if hasattr(tedeu_obj, 'organisation_name') and tedeu_obj.organisation_name:
        language_sample += tedeu_obj.organisation_name + " "
    if hasattr(tedeu_obj, 'buyer_name') and tedeu_obj.buyer_name:
        language_sample += tedeu_obj.buyer_name + " "
    
    language = detect_language(language_sample.strip())
    if not language and hasattr(tedeu_obj, 'language') and tedeu_obj.language:
        language = tedeu_obj.language.lower()[:2]
    if not language:
        language = 'en'  # Default to English if detection fails
    
    # Translate with improved chunking and retry logic
    title_english = None
    description_english = None
    
    if title and language != 'en':
        title_english, _ = translate_to_english(title, language, max_retries=3)
        # Normalize translated title
        if title_english:
            title_english = normalize_title(title_english)
    else:
        title_english = title
        
    if description and language != 'en':
        # Split long descriptions into smaller chunks for better translation
        chunks = [description[i:i+500] for i in range(0, len(description), 500)]
        translated_chunks = []
        for chunk in chunks:
            trans_chunk, _ = translate_to_english(chunk, language, max_retries=3)
            if trans_chunk:
                translated_chunks.append(trans_chunk)
        description_english = " ".join(translated_chunks) if translated_chunks else None
        # Normalize translated description
        if description_english:
            description_english = normalize_description(description_english)
    else:
        description_english = description

    # Extract and normalize estimated value and currency
    estimated_value = None
    currency = None
    
    # Try multiple sources for value extraction
    if hasattr(tedeu_obj, 'value_magnitude') and tedeu_obj.value_magnitude:
        try:
            estimated_value = float(tedeu_obj.value_magnitude)
            if hasattr(tedeu_obj, 'currency') and tedeu_obj.currency:
                currency = tedeu_obj.currency
        except (ValueError, TypeError):
            pass
    
    # Try to extract from description if not found
    if not estimated_value and description:
        estimated_value, extracted_currency = extract_financial_info(description)
        if not currency and extracted_currency:
            currency = extracted_currency
    
    # Try to extract from title if still not found
    if not estimated_value and title:
        estimated_value, extracted_currency = extract_financial_info(title)
        if not currency and extracted_currency:
            currency = extracted_currency
            
    # Normalize value and currency
    estimated_value, currency = normalize_value(estimated_value, currency)
    
    # Extract organization name and buyer with improved logic
    organization_name = None
    buyer = None
    
    if hasattr(tedeu_obj, 'organisation_name') and tedeu_obj.organisation_name:
        organization_name = tedeu_obj.organisation_name
    
    if hasattr(tedeu_obj, 'buyer_name') and tedeu_obj.buyer_name:
        buyer = tedeu_obj.buyer_name
    
    # If organization is missing, try to extract from text
    if not organization_name:
        organization_name, extracted_buyer = extract_organization_and_buyer(description, title)
        if not buyer:
            buyer = extracted_buyer
    
    # Translate organization and buyer names if needed
    organization_name_english = None
    buyer_english = None
    
    if organization_name and language != 'en':
        organization_name_english, _ = translate_to_english(organization_name, language, max_retries=3)
    else:
        organization_name_english = organization_name
        
    if buyer and language != 'en':
        buyer_english, _ = translate_to_english(buyer, language, max_retries=3)
    else:
        buyer_english = buyer

    # Extract country with enhanced fallback mechanisms
    country = None
    if hasattr(tedeu_obj, 'country') and tedeu_obj.country:
        country = tedeu_obj.country
    elif hasattr(tedeu_obj, 'country_code') and tedeu_obj.country_code:
        country = tedeu_obj.country_code
    elif hasattr(tedeu_obj, 'nuts_code') and tedeu_obj.nuts_code:
        # Extract country from NUTS code (first 2 characters)
        country = tedeu_obj.nuts_code[:2] if len(tedeu_obj.nuts_code) >= 2 else None
    
    # Try to extract country from address or organization data if still missing
    if not country:
        if hasattr(tedeu_obj, 'address') and tedeu_obj.address:
            country = extract_country_from_text(tedeu_obj.address)
        elif hasattr(tedeu_obj, 'organisation_country') and tedeu_obj.organisation_country:
            country = tedeu_obj.organisation_country
    
    # Ensure country is populated using fallback mechanisms
    country = ensure_country(
        country_value=country,
        text=description,
        organization=organization_name,
        email=tedeu_obj.contact_email if hasattr(tedeu_obj, 'contact_email') and tedeu_obj.contact_email else None,
        language=language
    )

    # Extract document links with improved validation
    document_links = []
    if hasattr(tedeu_obj, 'links') and tedeu_obj.links:
        document_links = normalize_document_links(tedeu_obj.links)
    
    # Add contact_url to document_links if available and valid
    if hasattr(tedeu_obj, 'contact_url') and tedeu_obj.contact_url:
        if tedeu_obj.contact_url.startswith(('http://', 'https://')):
            url_already_included = False
            if document_links:
                for link in document_links:
                    if isinstance(link, dict) and link.get('url') == tedeu_obj.contact_url:
                        url_already_included = True
                        break
            
            if not url_already_included:
                document_links.append({
                    "url": tedeu_obj.contact_url,
                    "type": "contact",
                    "language": language,
                    "description": "Contact URL"
                })
    
    # Extract and standardize procurement method
    procurement_method = None
    if hasattr(tedeu_obj, 'procedure_type') and tedeu_obj.procedure_type:
        procurement_method = standardize_procurement_method(tedeu_obj.procedure_type)
    
    # Convert date objects to datetime
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
    
    # Extract and standardize status
    raw_status = None
    if hasattr(tedeu_obj, 'notice_status') and tedeu_obj.notice_status:
        raw_status = tedeu_obj.notice_status
    
    # Use the improved extract_status function and standardize
    status = extract_status(
        text=raw_status,
        deadline=deadline_dt,
        publication_date=publication_dt,
        description=description
    )
    status = standardize_status(status)
    
    # Extract sector information
    sector = None
    if description:
        sectors = extract_sector_info(description)
        if sectors:
            sector = sectors[0]  # Use the first identified sector
    
    # Create the UnifiedTender object
    normalized_tender = UnifiedTender(
        id=str(uuid.uuid4()),
        title=title,
        description=description,
        tender_type=None,
        status=status,
        publication_date=publication_dt,
        deadline_date=deadline_dt,
        country=country,
        city=None,  # Not reliably available in TED EU data
        organization_name=organization_name,
        organization_id=None,
        buyer=buyer,
        project_name=None,
        project_id=None,
        project_number=None,
        sector=sector,
        estimated_value=estimated_value,
        currency=currency,
        contact_name=tedeu_obj.contact_name if hasattr(tedeu_obj, 'contact_name') and tedeu_obj.contact_name else None,
        contact_email=tedeu_obj.contact_email if hasattr(tedeu_obj, 'contact_email') and tedeu_obj.contact_email else None,
        contact_phone=tedeu_obj.contact_phone if hasattr(tedeu_obj, 'contact_phone') and tedeu_obj.contact_phone else None,
        contact_address=tedeu_obj.contact_address if hasattr(tedeu_obj, 'contact_address') and tedeu_obj.contact_address else None,
        url=tedeu_obj.url if hasattr(tedeu_obj, 'url') and tedeu_obj.url else None,
        document_links=document_links,
        language=language,
        notice_id=tedeu_obj.notice_id if hasattr(tedeu_obj, 'notice_id') and tedeu_obj.notice_id else None,
        reference_number=tedeu_obj.reference_number if hasattr(tedeu_obj, 'reference_number') and tedeu_obj.reference_number else None,
        procurement_method=procurement_method,
        original_data=row,  # Store the original data for reference
        source_table="tedeu",
        source_id=str(tedeu_obj.id) if hasattr(tedeu_obj, 'id') and tedeu_obj.id is not None else None,
        normalized_by="pynormalizer",
        title_english=title_english,
        description_english=description_english,
        organization_name_english=organization_name_english,
        buyer_english=buyer_english,
        project_name_english=None
    )
    
    return normalized_tender 