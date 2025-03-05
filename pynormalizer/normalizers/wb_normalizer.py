import json
import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import uuid

from pynormalizer.models.source_models import WBTender
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

# Initialize logger
logger = logging.getLogger(__name__)

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
    
    # Detect language - default for World Bank is English
    language = "en"
    
    # Safely check for title and description
    if hasattr(wb_obj, 'title') and wb_obj.title:
        detected = detect_language(wb_obj.title)
        if detected and detected != "en":
            language = detected
    
    if language == "en" and hasattr(wb_obj, 'description') and wb_obj.description:
        detected = detect_language(wb_obj.description)
        if detected and detected != "en":
            language = detected
    
    # Extract procurement method
    procurement_method = None
    
    # Try from tender_type first
    if hasattr(wb_obj, 'tender_type') and wb_obj.tender_type:
        procurement_method = extract_procurement_method(wb_obj.tender_type)
    
    # Try from procurement_method_code if available
    if not procurement_method and hasattr(wb_obj, 'procurement_method_code') and wb_obj.procurement_method_code:
        # Map World Bank procurement method codes to descriptions
        procurement_map = {
            "CQS": "Consultant's Qualifications Based Selection",
            "QCBS": "Quality and Cost-Based Selection",
            "LCS": "Least-Cost Selection",
            "FBS": "Fixed Budget Selection",
            "SSS": "Single-Source Selection",
            "ICB": "International Competitive Bidding",
            "NCB": "National Competitive Bidding",
            "DC": "Direct Contracting",
            "SHOP": "Shopping",
            "QBS": "Quality-Based Selection",
            "OPN": "Open Tender",
            "LIB": "Limited International Bidding",
            "IC": "Individual Consultants"
        }
        proc_code = wb_obj.procurement_method_code.upper()
        procurement_method = procurement_map.get(proc_code, proc_code)
    
    # Try from description if still not found
    if not procurement_method and hasattr(wb_obj, 'description') and wb_obj.description:
        procurement_method = extract_procurement_method(wb_obj.description)
    
    # Determine status with enhanced logic
    status = None
    
    # First check if status is explicitly set
    if hasattr(wb_obj, 'status') and wb_obj.status:
        status = wb_obj.status
    # Check tender_type/notice_type for clues about status
    elif hasattr(wb_obj, 'notice_type') and wb_obj.notice_type:
        notice_type_lower = wb_obj.notice_type.lower()
        
        if "award" in notice_type_lower or "awarded" in notice_type_lower:
            status = "Awarded"
        elif "contract" in notice_type_lower:
            status = "Contract Award"
    
    # Use deadline_date to determine if tender is open or closed
    deadline_dt = None
    if hasattr(wb_obj, 'deadline_date') and wb_obj.deadline_date:
        if isinstance(wb_obj.deadline_date, datetime):
            deadline_dt = wb_obj.deadline_date
        elif isinstance(wb_obj.deadline_date, str):
            try:
                # Try parsing common date formats
                deadline_dt = datetime.fromisoformat(wb_obj.deadline_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                try:
                    # Try with different format
                    deadline_dt = datetime.strptime(wb_obj.deadline_date, "%Y-%m-%d")
                except ValueError:
                    pass
    
    # Set status based on deadline if available and status still not determined
    if not status and deadline_dt:
        current_dt = datetime.now()
        if current_dt > deadline_dt:
            status = "Closed"
        else:
            status = "Open"
    
    # If still no status, try to extract from description
    if not status and hasattr(wb_obj, 'description') and wb_obj.description:
        extracted_status = extract_status(description=wb_obj.description)
        if extracted_status:
            status = extracted_status
    
    # Default to "Active" if we have a publication date
    if not status and hasattr(wb_obj, 'publication_date') and wb_obj.publication_date:
        status = "Active"
    
    # Extract country and city - try direct attributes first
    country = None
    city = None
    
    if hasattr(wb_obj, 'country') and wb_obj.country:
        country = wb_obj.country
    
    if hasattr(wb_obj, 'city') and wb_obj.city:
        city = wb_obj.city
    
    # Try to extract from contact_address if available
    if (not country or not city) and hasattr(wb_obj, 'contact_address') and wb_obj.contact_address:
        extracted_location = extract_location_info(wb_obj.contact_address)
        if extracted_location:
            if not country and extracted_location.get('country'):
                country = extracted_location['country']
            if not city and extracted_location.get('city'):
                city = extracted_location['city']
    
    # Try to extract from description as a last resort
    if (not country or not city) and hasattr(wb_obj, 'description') and wb_obj.description:
        extracted_location = extract_location_info(wb_obj.description)
        if extracted_location:
            if not country and extracted_location.get('country'):
                country = extracted_location['country']
            if not city and extracted_location.get('city'):
                city = extracted_location['city']
    
    # Extract organization name
    organization_name = None
    
    if hasattr(wb_obj, 'organization_name') and wb_obj.organization_name:
        organization_name = wb_obj.organization_name
    elif hasattr(wb_obj, 'buyer') and wb_obj.buyer:
        organization_name = wb_obj.buyer
    
    # Try to extract from description if still not found
    if not organization_name and hasattr(wb_obj, 'description') and wb_obj.description:
        extracted_org = extract_organization(wb_obj.description)
        if extracted_org:
            organization_name = extracted_org
    
    # Extract financial information
    estimated_value = None
    currency = None
    
    # Try direct fields first
    if hasattr(wb_obj, 'estimated_value') and wb_obj.estimated_value:
        if isinstance(wb_obj.estimated_value, (int, float)):
            estimated_value = float(wb_obj.estimated_value)
        elif isinstance(wb_obj.estimated_value, str):
            try:
                # Remove commas and convert to float
                estimated_value = float(wb_obj.estimated_value.replace(',', ''))
            except (ValueError, TypeError):
                pass
    
    if hasattr(wb_obj, 'currency') and wb_obj.currency:
        currency = wb_obj.currency
    
    # Try to extract from description if not found directly
    if (not estimated_value or not currency) and hasattr(wb_obj, 'description') and wb_obj.description:
        extracted_financial = extract_financial_info(wb_obj.description)
        if extracted_financial:
            if not estimated_value and extracted_financial.get('value'):
                estimated_value = extracted_financial['value']
            if not currency and extracted_financial.get('currency'):
                currency = extracted_financial['currency']
    
    # Extract document links
    document_links = []
    
    # Process document_links if available
    if hasattr(wb_obj, 'document_links') and wb_obj.document_links:
        document_links = normalize_document_links(wb_obj.document_links)
    
    # Add URL as a document link if available and not already in document_links
    if hasattr(wb_obj, 'url') and wb_obj.url:
        url_already_included = False
        for link in document_links:
            if isinstance(link, dict) and link.get('url') == wb_obj.url:
                url_already_included = True
                break
        
        if not url_already_included:
            document_links.append({"url": wb_obj.url, "description": "Main tender notice"})
    
    # Convert publication date to datetime
    publication_dt = None
    if hasattr(wb_obj, 'publication_date') and wb_obj.publication_date:
        if isinstance(wb_obj.publication_date, datetime):
            publication_dt = wb_obj.publication_date
        elif isinstance(wb_obj.publication_date, str):
            try:
                # Try parsing common date formats
                publication_dt = datetime.fromisoformat(wb_obj.publication_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                try:
                    # Try with different format
                    publication_dt = datetime.strptime(wb_obj.publication_date, "%Y-%m-%d")
                except ValueError:
                    pass
    
    # Extract title and description
    title = getattr(wb_obj, 'title', None)
    description = getattr(wb_obj, 'description', None)
    
    # Translate fields if needed
    title_english = None
    description_english = None
    organization_name_english = None
    buyer_english = None
    project_name_english = None
    
    # Translate title to English if not already in English
    if title:
        title_english, title_method = translate_to_english(title, language)
    
    # Translate description to English if not already in English
    if description:
        description_english, desc_method = translate_to_english(description, language)
    
    # Translate organization name to English if not already in English
    if organization_name:
        organization_name_english, org_method = translate_to_english(organization_name, language)
    
    # Translate buyer to English if not already in English and different from organization_name
    buyer = getattr(wb_obj, 'buyer', None)
    if buyer and buyer != organization_name:
        buyer_english, buyer_method = translate_to_english(buyer, language)
    
    # Translate project name to English if not already in English
    project_name = getattr(wb_obj, 'project_name', None)
    if project_name:
        project_name_english, project_method = translate_to_english(project_name, language)
    
    # Create UnifiedTender object
    normalized_tender = UnifiedTender(
        id=str(uuid.uuid4()),  # Generate a new UUID for the unified record
        title=title,
        description=description,
        tender_type=getattr(wb_obj, 'tender_type', None),
        status=status,
        publication_date=publication_dt,
        deadline_date=deadline_dt,
        country=country,
        city=city,
        organization_name=organization_name,
        organization_id=getattr(wb_obj, 'organization_id', None),
        buyer=buyer,
        project_name=project_name,
        project_id=getattr(wb_obj, 'project_id', None),
        project_number=getattr(wb_obj, 'project_number', None),
        sector=getattr(wb_obj, 'sector', None),
        estimated_value=estimated_value,
        currency=currency,
        contact_name=getattr(wb_obj, 'contact_name', None),
        contact_email=getattr(wb_obj, 'contact_email', None),
        contact_phone=getattr(wb_obj, 'contact_phone', None),
        contact_address=getattr(wb_obj, 'contact_address', None),
        url=getattr(wb_obj, 'url', None),
        document_links=document_links,
        language=language,
        notice_id=getattr(wb_obj, 'notice_id', None),
        reference_number=getattr(wb_obj, 'reference_number', None),
        procurement_method=procurement_method,
        original_data=row,
        source_table="wb",
        source_id=getattr(wb_obj, 'id', None),
        normalized_by="pynormalizer",
        title_english=title_english,
        description_english=description_english,
        organization_name_english=organization_name_english,
        buyer_english=buyer_english,
        project_name_english=project_name_english,
    )
    
    return normalized_tender 