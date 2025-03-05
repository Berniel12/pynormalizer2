import json
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from pynormalizer.models.source_models import WBTender
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

def normalize_wb(row: Dict[str, Any]) -> UnifiedTender:
    """
    Normalize a World Bank tender record.
    
    Args:
        row: Dictionary containing World Bank tender data
        
    Returns:
        Normalized UnifiedTender instance
    """
    # Handle document_links if it's a string (sometimes it is)
    if "document_links" in row and isinstance(row["document_links"], str):
        # Try to parse as JSON if it starts with [ or {
        if row["document_links"].strip().startswith(("[", "{")):
            try:
                row["document_links"] = json.loads(row["document_links"])
            except json.JSONDecodeError:
                # If it fails to parse, just keep it as a string
                pass
        # If it's a URL string that starts with http or www, make it a list with a dict
        elif row["document_links"].strip().startswith(("http", "www")):
            row["document_links"] = [{"link": row["document_links"]}]
    
    # Validate with Pydantic
    try:
        wb_obj = WBTender(**row)
    except Exception as e:
        raise ValueError(f"Failed to validate World Bank tender: {e}")
    
    # Detect language
    language = "en"  # Default for World Bank
    
    if wb_obj.title:
        detected = detect_language(wb_obj.title)
        if detected:
            language = detected
    elif wb_obj.description and language == "en":
        detected = detect_language(wb_obj.description)
        if detected:
            language = detected
    
    # Extract procurement method - first from procurement_method field, then from description
    procurement_method = None
    
    # Check direct field first
    if hasattr(wb_obj, 'procurement_method') and wb_obj.procurement_method:
        procurement_method = wb_obj.procurement_method
    elif hasattr(wb_obj, 'procurement_method_name') and wb_obj.procurement_method_name:
        procurement_method = wb_obj.procurement_method_name
    
    # Try to extract from description if not found directly
    if not procurement_method and wb_obj.description:
        procurement_method = extract_procurement_method(wb_obj.description)
    
    # Extract status
    status = None
    
    # Check if notice_status attribute exists
    if hasattr(wb_obj, 'notice_status') and wb_obj.notice_status:
        status = wb_obj.notice_status
    # Check if tender_type attribute exists (sometimes contains status)
    elif hasattr(wb_obj, 'tender_type') and wb_obj.tender_type:
        status = wb_obj.tender_type
    
    # Try to determine based on deadline_date
    if not status and hasattr(wb_obj, 'deadline_date') and wb_obj.deadline_date:
        # If deadline has passed, mark as closed
        if isinstance(wb_obj.deadline_date, datetime) and wb_obj.deadline_date < datetime.now():
            status = "Closed"
        else:
            status = "Open"
    
    # Extract country and city
    country = None
    city = None
    
    # Check direct fields
    if hasattr(wb_obj, 'country') and wb_obj.country:
        country = wb_obj.country
    
    if hasattr(wb_obj, 'city') and wb_obj.city:
        city = wb_obj.city
    
    # Try project_ctry_name if country is not set
    if not country and hasattr(wb_obj, 'project_ctry_name') and wb_obj.project_ctry_name:
        country = wb_obj.project_ctry_name
    
    # Try contact_ctry_name if still not set
    if not country and hasattr(wb_obj, 'contact_ctry_name') and wb_obj.contact_ctry_name:
        country = wb_obj.contact_ctry_name
    
    # If no country/city found, try to extract from contact address
    if (not country or not city) and hasattr(wb_obj, 'contact_address') and wb_obj.contact_address:
        country_from_addr, city_from_addr = extract_location_info(wb_obj.contact_address)
        if not country and country_from_addr:
            country = country_from_addr
        if not city and city_from_addr:
            city = city_from_addr
    
    # If still not found, try to extract from description
    if (not country or not city) and wb_obj.description:
        country_from_desc, city_from_desc = extract_location_info(wb_obj.description)
        if not country and country_from_desc:
            country = country_from_desc
        if not city and city_from_desc:
            city = city_from_desc
    
    # Extract organization name
    organization_name = None
    
    # Check direct contact_organization field
    if hasattr(wb_obj, 'contact_organization') and wb_obj.contact_organization:
        organization_name = wb_obj.contact_organization
    # If not found, try buyer field
    elif hasattr(wb_obj, 'buyer') and wb_obj.buyer:
        organization_name = wb_obj.buyer
    # If still not found, try to extract from description
    elif wb_obj.description:
        organization_name = extract_organization(wb_obj.description)
    
    # Extract financial information
    estimated_value = None
    currency = None
    
    if hasattr(wb_obj, 'estimated_value') and wb_obj.estimated_value:
        estimated_value = wb_obj.estimated_value
    
    if hasattr(wb_obj, 'currency') and wb_obj.currency:
        currency = wb_obj.currency
    
    # If not found directly, try to extract from description
    if (not estimated_value or not currency) and wb_obj.description:
        value, curr = extract_financial_info(wb_obj.description)
        if value and curr:
            if not estimated_value:
                estimated_value = value
            if not currency:
                currency = curr
    
    # Normalize document links
    document_links = []
    if hasattr(wb_obj, 'document_links') and wb_obj.document_links:
        document_links = normalize_document_links(wb_obj.document_links)
    
    # Convert dates
    publication_date = None
    if hasattr(wb_obj, 'publication_date') and wb_obj.publication_date:
        if isinstance(wb_obj.publication_date, datetime):
            publication_date = wb_obj.publication_date
        elif isinstance(wb_obj.publication_date, str):
            try:
                publication_date = datetime.fromisoformat(wb_obj.publication_date.replace('Z', '+00:00'))
            except ValueError:
                pass
    
    deadline_date = None
    if hasattr(wb_obj, 'deadline_date') and wb_obj.deadline_date:
        if isinstance(wb_obj.deadline_date, datetime):
            deadline_date = wb_obj.deadline_date
        elif isinstance(wb_obj.deadline_date, str):
            try:
                deadline_date = datetime.fromisoformat(wb_obj.deadline_date.replace('Z', '+00:00'))
            except ValueError:
                pass
    
    # Construct the UnifiedTender
    unified = UnifiedTender(
        # Required fields
        title=wb_obj.title,
        source_table="wb",
        source_id=str(wb_obj.id),
        
        # Additional fields
        description=wb_obj.description,
        tender_type=getattr(wb_obj, 'tender_type', None),
        status=status,
        publication_date=publication_date,
        deadline_date=deadline_date,
        country=country,
        city=city,
        organization_name=organization_name,
        project_name=getattr(wb_obj, 'project_name', None),
        estimated_value=estimated_value,
        currency=currency,
        url=getattr(wb_obj, 'url', None),
        document_links=document_links,
        procurement_method=procurement_method,
        language=language,
        original_data=row,
        normalized_method="offline-dictionary",
    )
    
    # Apply translations
    unified = apply_translations(unified, language)
    
    return unified 