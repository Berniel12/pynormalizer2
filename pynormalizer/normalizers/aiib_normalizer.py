import json
import re
from datetime import datetime
from typing import Dict, Any, Optional

from pynormalizer.models.source_models import AIIBTender
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
    ensure_country,
)

def normalize_aiib(row: Dict[str, Any]) -> UnifiedTender:
    """
    Normalize an AIIB (Asian Infrastructure Investment Bank) tender record.
    
    Args:
        row: Dictionary containing AIIB tender data
        
    Returns:
        Normalized UnifiedTender instance
    """
    # Validate with Pydantic
    try:
        aiib_obj = AIIBTender(**row)
    except Exception as e:
        raise ValueError(f"Failed to validate AIIB tender: {e}")

    # Parse date string if present
    publication_dt = None
    if aiib_obj.date:
        try:
            # Try different date formats
            date_formats = [
                "%Y-%m-%d",
                "%d/%m/%Y",
                "%m/%d/%Y",
                "%B %d, %Y",  # e.g. "January 15, 2023"
                "%d %B %Y",   # e.g. "15 January 2023"
            ]
            
            for fmt in date_formats:
                try:
                    publication_dt = datetime.strptime(aiib_obj.date, fmt)
                    break
                except ValueError:
                    continue
        except Exception:
            # If all parsing attempts fail, leave as None
            pass

    # Use project_notice as the title if available, otherwise use a placeholder
    title = aiib_obj.project_notice or f"AIIB Tender - {aiib_obj.id}"
    
    # Extract status from text or dates
    status = None
    if aiib_obj.type:
        status = extract_status(status_text=aiib_obj.type)
    
    # Try to extract status from description if not found
    if not status and aiib_obj.pdf_content:
        status = extract_status(description=aiib_obj.pdf_content)
    
    # Try to extract organization name from description
    organization_name = None
    if aiib_obj.pdf_content:
        organization_name = extract_organization(aiib_obj.pdf_content)
    
    # Try to extract financial information
    estimated_value = None
    currency = None
    if aiib_obj.pdf_content:
        estimated_value, currency = extract_financial_info(aiib_obj.pdf_content)
    
    # Detect language - MOVED UP before country extraction
    language = "en"  # Default for AIIB
    if aiib_obj.pdf_content:
        detected = detect_language(aiib_obj.pdf_content)
        if detected:
            language = detected
    
    # Try to extract country and city
    country_value = aiib_obj.member if aiib_obj.member else None
    city = None
    
    if aiib_obj.pdf_content:
        # Instead of directly assigning the result of extract_location_info
        # We'll handle the extraction more carefully
        location_info = extract_location_info(aiib_obj.pdf_content)
        if location_info and isinstance(location_info, tuple) and len(location_info) > 1:
            extracted_country, extracted_city = location_info
            if extracted_city:
                city = extracted_city
            # We'll use ensure_country to handle the country value
    
    # Ensure we have a country value using our fallback mechanisms
    country = ensure_country(
        country=country_value,
        text=aiib_obj.pdf_content,
        organization=organization_name,
        language=language
    )
    
    # Extract procurement method
    procurement_method = None
    if aiib_obj.type:
        procurement_method = extract_procurement_method(aiib_obj.type)
    
    if not procurement_method and aiib_obj.pdf_content:
        procurement_method = extract_procurement_method(aiib_obj.pdf_content)
        
    # Extract document links if available
    document_links = []
    if "pdf" in row and row["pdf"]:
        pdf_url = row["pdf"]
        document_links = normalize_document_links(pdf_url)
    
    # Construct the UnifiedTender
    unified = UnifiedTender(
        # Required fields
        title=title,
        source_table="aiib",
        source_id=str(aiib_obj.id),
        
        # Additional fields
        description=aiib_obj.pdf_content,  # Using PDF content as description
        tender_type=aiib_obj.type,
        status=status,
        publication_date=publication_dt,
        country=country,
        city=city,
        organization_name=organization_name,
        sector=aiib_obj.sector,
        estimated_value=estimated_value,
        currency=currency,
        document_links=document_links,
        procurement_method=procurement_method,
        language=language,
        original_data=row,
        normalized_method="offline-dictionary",
    )

    # Use the common apply_translations function for all fields
    unified = apply_translations(unified, language)

    return unified 