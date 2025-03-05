from datetime import datetime
from typing import Dict, Any, Optional
import json
import re

from pynormalizer.models.source_models import TEDEuTender
from pynormalizer.models.unified_model import UnifiedTender
from pynormalizer.utils.translation import translate_to_english, detect_language
from pynormalizer.utils.normalizer_helpers import (
    normalize_document_links, 
    extract_financial_info, 
    extract_location_info,
    extract_procurement_method,
    extract_organization,
    apply_translations
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
    if tedeu_obj.publication_date:
        if isinstance(tedeu_obj.publication_date, datetime):
            publication_dt = tedeu_obj.publication_date
        else:
            publication_dt = datetime.combine(tedeu_obj.publication_date, datetime.min.time())
    
    deadline_dt = None
    if tedeu_obj.deadline_date:
        if isinstance(tedeu_obj.deadline_date, datetime):
            deadline_dt = tedeu_obj.deadline_date
        else:
            deadline_dt = datetime.combine(tedeu_obj.deadline_date, datetime.min.time())

    # Determine procurement method from procedure_type or description
    procurement_method = None
    if tedeu_obj.procedure_type:
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
        if tedeu_obj.summary:
            description_text += tedeu_obj.summary + " "
        if tedeu_obj.additional_information:
            description_text += tedeu_obj.additional_information
            
        if description_text:
            extracted_method = extract_procurement_method(description_text)
            if extracted_method:
                procurement_method = extracted_method

    # Extract estimated value and currency from various fields
    estimated_value = None
    currency = None
    
    # Try to extract from description or additional_information
    if tedeu_obj.summary:
        estimated_value, currency = extract_financial_info(tedeu_obj.summary)
    
    if not estimated_value and tedeu_obj.additional_information:
        estimated_value, currency = extract_financial_info(tedeu_obj.additional_information)
    
    # Extract location information - first try direct fields, then use helper function
    country = None
    city = None
    
    # Try direct attribute access first
    if hasattr(tedeu_obj, 'country') and tedeu_obj.country:
        country = tedeu_obj.country
    
    if hasattr(tedeu_obj, 'city') and tedeu_obj.city:
        city = tedeu_obj.city
    
    # Try to extract from lots if available
    if hasattr(tedeu_obj, 'lots') and tedeu_obj.lots and isinstance(tedeu_obj.lots, list) and len(tedeu_obj.lots) > 0:
        for lot in tedeu_obj.lots:
            if isinstance(lot, dict):
                # Extract country
                if not country and 'country' in lot:
                    country = lot.get('country')
                    
                # Extract city
                if not city and 'city' in lot:
                    city = lot.get('city')
                    
                # Extract value information if not already extracted
                if not estimated_value and 'value' in lot:
                    lot_value = lot.get('value')
                    if isinstance(lot_value, dict):
                        if 'amount' in lot_value:
                            try:
                                estimated_value = float(lot_value.get('amount'))
                            except (ValueError, TypeError):
                                pass
                        if 'currency' in lot_value:
                            currency = lot_value.get('currency')
    
    # If country or city still not found, try to extract from description
    if not country or not city:
        description_text = ""
        if tedeu_obj.summary:
            description_text += tedeu_obj.summary + " "
        if tedeu_obj.additional_information:
            description_text += tedeu_obj.additional_information
            
        extracted_country, extracted_city = extract_location_info(description_text)
        if not country and extracted_country:
            country = extracted_country
        if not city and extracted_city:
            city = extracted_city
    
    # Use the normalize_document_links helper to standardize links
    document_links = normalize_document_links(tedeu_obj.links)
    
    # Detect language and default to English if not specified
    language = tedeu_obj.language or "en"
    if not language or language == "None":
        # Try to detect from title or summary
        if tedeu_obj.title:
            detected = detect_language(tedeu_obj.title)
            if detected:
                language = detected
        elif tedeu_obj.summary and not language:
            detected = detect_language(tedeu_obj.summary)
            if detected:
                language = detected
        else:
            # Default to English as a fallback
            language = "en"

    # Construct the UnifiedTender
    unified = UnifiedTender(
        # Required fields
        title=getattr(tedeu_obj, 'title', None) or f"TED Notice - {tedeu_obj.publication_number}",
        source_table="ted_eu",
        source_id=tedeu_obj.publication_number,  # Using publication_number as the ID
        
        # Additional fields
        description=getattr(tedeu_obj, 'summary', None) or getattr(tedeu_obj, 'additional_information', None),
        tender_type=getattr(tedeu_obj, 'notice_type', None),
        status=getattr(tedeu_obj, 'notice_status', None),
        publication_date=publication_dt,
        deadline_date=deadline_dt,
        country=country,
        city=city,
        organization_name=getattr(tedeu_obj, 'organisation_name', None),
        organization_id=getattr(tedeu_obj, 'organisation_id', None),
        contact_email=getattr(tedeu_obj, 'contact_email', None),
        contact_phone=getattr(tedeu_obj, 'contact_phone', None),
        url=getattr(tedeu_obj, 'contact_url', None),
        language=language,
        notice_id=getattr(tedeu_obj, 'notice_identifier', None) or tedeu_obj.publication_number,
        document_links=document_links,
        procurement_method=procurement_method,
        estimated_value=estimated_value,
        currency=currency,
        original_data=row,
        normalized_method="offline-dictionary",
    )

    # Use the common apply_translations function for all fields
    unified = apply_translations(unified, language)

    return unified 