import json
from datetime import datetime
from typing import Dict, Any, Optional

from pynormalizer.models.source_models import AFDBTender
from pynormalizer.models.unified_model import UnifiedTender
from pynormalizer.utils.translation import translate_to_english, detect_language
from pynormalizer.utils.normalizer_helpers import (
    normalize_document_links, 
    extract_financial_info,
    extract_location_info,
    extract_organization,
    extract_procurement_method,
    apply_translations
)

def normalize_afdb(row: Dict[str, Any]) -> UnifiedTender:
    """
    Normalize an African Development Bank tender record.
    
    Args:
        row: Dictionary containing AFDB tender data
        
    Returns:
        Normalized UnifiedTender instance
    """
    # Validate with Pydantic
    try:
        afdb_obj = AFDBTender(**row)
    except Exception as e:
        raise ValueError(f"Failed to validate AFDB tender: {e}")

    # Extract city and country from country field if it contains format "Country - City"
    country = afdb_obj.country
    city = None
    
    if country and " - " in country:
        parts = country.split(" - ", 1)
        country = parts[0].strip()
        city = parts[1].strip() if len(parts) > 1 else None
    
    # If country or city still not found, try to extract from description
    if not country or not city:
        if afdb_obj.description:
            extracted_country, extracted_city = extract_location_info(afdb_obj.description)
            if not country and extracted_country:
                country = extracted_country
            if not city and extracted_city:
                city = extracted_city
    
    # Try to extract organization name from description
    organization_name = None
    if afdb_obj.description:
        organization_name = extract_organization(afdb_obj.description)
    
    # Extract financial information
    estimated_value = afdb_obj.estimated_value
    currency = afdb_obj.currency
    
    # Try to extract from description if not available
    if not estimated_value and afdb_obj.description:
        value, curr = extract_financial_info(afdb_obj.description)
        if value and curr:
            estimated_value = value
            currency = curr
    
    # Try to extract procurement method
    procurement_method = None
    if afdb_obj.tender_type:
        procurement_method = extract_procurement_method(afdb_obj.tender_type)
    
    if not procurement_method and afdb_obj.description:
        procurement_method = extract_procurement_method(afdb_obj.description)
    
    # Convert date objects to datetime if needed
    publication_dt = None
    if afdb_obj.publication_date:
        if isinstance(afdb_obj.publication_date, datetime):
            publication_dt = afdb_obj.publication_date
        elif isinstance(afdb_obj.publication_date, str):
            try:
                # Try parsing common date formats
                if "/" in afdb_obj.publication_date:
                    publication_dt = datetime.strptime(afdb_obj.publication_date, "%d/%m/%Y")
                elif "-" in afdb_obj.publication_date:
                    publication_dt = datetime.strptime(afdb_obj.publication_date, "%Y-%m-%d")
            except ValueError:
                pass
    
    # Convert closing date to deadline_date
    deadline_dt = None
    if afdb_obj.closing_date:
        if isinstance(afdb_obj.closing_date, datetime):
            deadline_dt = afdb_obj.closing_date
        elif hasattr(afdb_obj.closing_date, 'strftime'):  # Check if it has date methods
            deadline_dt = datetime.combine(afdb_obj.closing_date, datetime.min.time())
                
    # Normalize document links to standardized format
    document_links = normalize_document_links(afdb_obj.document_links)
    
    # Determine status based on closing date
    status = None
    if afdb_obj.status:
        status = afdb_obj.status
    elif afdb_obj.closing_date:
        # Check if it's a datetime or date object
        closing_date = None
        if isinstance(afdb_obj.closing_date, datetime):
            closing_date = afdb_obj.closing_date
        elif hasattr(afdb_obj.closing_date, 'strftime'):  # Check if it's a date object
            closing_date = datetime.combine(afdb_obj.closing_date, datetime.min.time())
            
        if closing_date and closing_date < datetime.now():
            status = "Closed"
        else:
            status = "Open"

    # Detect language from title and description
    language = "en"  # Default for AFDB
    
    if afdb_obj.title:
        detected = detect_language(afdb_obj.title)
        if detected:
            language = detected
    elif afdb_obj.description and language == "en":
        detected = detect_language(afdb_obj.description)
        if detected:
            language = detected

    # Construct the UnifiedTender
    unified = UnifiedTender(
        # Required fields
        title=afdb_obj.title or f"AFDB Tender - {afdb_obj.id}",
        source_table="afdb",
        source_id=str(afdb_obj.id),
        
        # Additional fields
        description=afdb_obj.description,
        tender_type=afdb_obj.tender_type,
        status=status,
        publication_date=publication_dt,
        deadline_date=deadline_dt,
        country=country,
        city=city,
        organization_name=organization_name,
        project_name=afdb_obj.project_name,
        project_id=afdb_obj.project_id,
        estimated_value=estimated_value,
        currency=currency,
        url=afdb_obj.url,
        document_links=document_links,
        procurement_method=procurement_method,
        language=language,
        original_data=row,
        normalized_method="offline-dictionary",
    )

    # Use the common apply_translations function for all fields
    unified = apply_translations(unified, language)

    return unified 