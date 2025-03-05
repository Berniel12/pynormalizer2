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
    # Handle document_links if it's a string
    if isinstance(row.get('document_links'), str):
        try:
            if row['document_links'].strip():
                row['document_links'] = json.loads(row['document_links'])
            else:
                row['document_links'] = None
        except (json.JSONDecodeError, ValueError):
            # If not valid JSON, it could be a URL
            if row['document_links'].startswith(('http', 'www')):
                row['document_links'] = [{'url': row['document_links']}]
            else:
                row['document_links'] = None
            
    # Validate with Pydantic
    try:
        wb_obj = WBTender(**row)
    except Exception as e:
        raise ValueError(f"Failed to validate World Bank tender: {e}")

    # Detect language from title and/or description
    language = "en"  # Default to English for World Bank
    
    if wb_obj.title:
        detected = detect_language(wb_obj.title)
        if detected:
            language = detected
    elif wb_obj.description and not language:
        detected = detect_language(wb_obj.description)
        if detected:
            language = detected

    # Extract procurement method using helper function
    procurement_method = None
    
    # Try direct fields first
    if wb_obj.procurement_method_name:
        procurement_method = wb_obj.procurement_method_name
    elif wb_obj.procurement_method:
        procurement_method = wb_obj.procurement_method
        
    # Try to extract from description if needed
    if not procurement_method and wb_obj.description:
        extracted_method = extract_procurement_method(wb_obj.description)
        if extracted_method:
            procurement_method = extracted_method
                
    # Extract procurement method from procurement_method_code if available
    if not procurement_method and wb_obj.procurement_method_code:
        # Common procurement method codes
        proc_code_map = {
            'ICB': 'International Competitive Bidding',
            'NCB': 'National Competitive Bidding',
            'RFP': 'Request for Proposals',
            'QCBS': 'Quality and Cost-Based Selection',
            'QBS': 'Quality-Based Selection',
            'FBS': 'Fixed Budget Selection',
            'LCS': 'Least Cost Selection',
            'CQS': 'Consultant\'s Qualification Selection',
            'SSS': 'Single Source Selection',
            'DC': 'Direct Contracting',
            'FA': 'Framework Agreement',
            'EOI': 'Expression of Interest',
            'IQ': 'Invitation for Quotations',
            'RFQ': 'Request for Quotations'
        }
        
        if wb_obj.procurement_method_code in proc_code_map:
            procurement_method = proc_code_map[wb_obj.procurement_method_code]

    # Extract status information if not already available
    status = wb_obj.notice_status or wb_obj.status
    
    # Determine status based on dates if not already available
    if not status:
        if wb_obj.submission_deadline_time:
            if isinstance(wb_obj.submission_deadline_time, datetime):
                deadline = wb_obj.submission_deadline_time
                # If deadline is in the past, mark as closed
                if deadline < datetime.now():
                    status = "Closed"
                else:
                    status = "Open"
            elif isinstance(wb_obj.submission_deadline_time, str):
                try:
                    deadline = datetime.fromisoformat(wb_obj.submission_deadline_time.replace('Z', '+00:00'))
                    if deadline < datetime.now():
                        status = "Closed"
                    else:
                        status = "Open"
                except (ValueError, TypeError):
                    pass

    # Extract location information 
    country = wb_obj.country
    city = None
    
    # Try to extract country and city from project_ctry_name
    if wb_obj.project_ctry_name and not country:
        country = wb_obj.project_ctry_name
    
    # Extract from description if not available
    if (not country or not city) and wb_obj.description:
        extracted_country, extracted_city = extract_location_info(wb_obj.description)
        if not country and extracted_country:
            country = extracted_country
        if not city and extracted_city:
            city = extracted_city
    
    # Extract organization information
    organization_name = None
    if wb_obj.contact_organization:
        organization_name = wb_obj.contact_organization
    elif wb_obj.description:
        organization_name = extract_organization(wb_obj.description)
    
    # Extract financial information if not already available
    estimated_value, currency = None, None
    
    # Extract from description
    if wb_obj.description:
        estimated_value, currency = extract_financial_info(wb_obj.description)
        
    # Normalize document links to standardized format
    document_links = normalize_document_links(wb_obj.document_links)
    
    # Convert dates to datetime objects
    publication_date = None
    deadline_date = None
    
    if wb_obj.publication_date:
        if isinstance(wb_obj.publication_date, datetime):
            publication_date = wb_obj.publication_date
        elif isinstance(wb_obj.publication_date, str):
            try:
                publication_date = datetime.fromisoformat(wb_obj.publication_date.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                pass
    
    if wb_obj.submission_date:
        if isinstance(wb_obj.submission_date, datetime):
            deadline_date = wb_obj.submission_date
        elif isinstance(wb_obj.submission_date, str):
            try:
                deadline_date = datetime.fromisoformat(wb_obj.submission_date.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                pass
    
    # Determine tender type from notice_type
    tender_type = None
    if wb_obj.tender_type:
        tender_type = wb_obj.tender_type
    elif wb_obj.notice_type:
        # Mapping of notice types to tender types
        notice_type_map = {
            'Invitation for Bids': 'Goods/Works',
            'Request for Expressions of Interest': 'Consulting Services',
            'Request for Proposals': 'Consulting Services',
            'General Procurement Notice': 'Planning',
            'Contract Award': 'Award',
            'Shortlist': 'Shortlisting Results'
        }
        tender_type = notice_type_map.get(wb_obj.notice_type, wb_obj.notice_type)

    # Construct the UnifiedTender
    unified = UnifiedTender(
        # Required fields
        title=wb_obj.title or f"World Bank Tender - {wb_obj.id}",
        source_table="wb",
        source_id=str(wb_obj.id),
        
        # Additional fields
        description=wb_obj.description,
        tender_type=tender_type,
        status=status,
        publication_date=publication_date or wb_obj.publication_date,
        deadline_date=deadline_date or wb_obj.submission_date or wb_obj.submission_deadline_time,
        country=country,
        city=city,
        organization_name=organization_name,
        organization_id=wb_obj.project_id,
        project_name=wb_obj.project_name,
        project_id=wb_obj.project_id,
        reference_number=wb_obj.bid_reference_no,
        notice_id=wb_obj.bid_reference_no or wb_obj.id,
        contact_name=wb_obj.contact_name,
        contact_email=wb_obj.contact_email,
        contact_phone=wb_obj.contact_phone,
        contact_address=wb_obj.contact_address,
        url=wb_obj.url,
        document_links=document_links,
        procurement_method=procurement_method,
        estimated_value=estimated_value,
        currency=currency,
        original_data=row,
        normalized_method="offline-dictionary",
        language=language,
    )

    # Apply translations using the common helper
    unified = apply_translations(unified, language)

    return unified 