import json
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import re
import logging
import uuid

from pynormalizer.models.source_models import AFDBTender
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

# Initialize logger
logger = logging.getLogger(__name__)

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
    country = getattr(afdb_obj, 'country', None)
    city = None
    
    if country and " - " in country:
        parts = country.split(" - ", 1)
        country = parts[0].strip()
        city = parts[1].strip() if len(parts) > 1 else None
    
    # If country or city still not found, try to extract from description
    if not country or not city:
        description = getattr(afdb_obj, 'description', '')
        if description:
            extracted_country, extracted_city = extract_location_info(description)
            if not country and extracted_country:
                country = extracted_country
            if not city and extracted_city:
                city = extracted_city
    
    # Try to extract organization name from description
    organization_name = getattr(afdb_obj, 'organization_name', None)
    if not organization_name and hasattr(afdb_obj, 'description') and afdb_obj.description:
        extracted_org = extract_organization(afdb_obj.description)
        if extracted_org:
            organization_name = extracted_org
    
    # Extract financial information
    estimated_value = getattr(afdb_obj, 'estimated_value', None)
    currency = getattr(afdb_obj, 'currency', None)
    
    # Try to extract from description if not available
    if not estimated_value and hasattr(afdb_obj, 'description') and afdb_obj.description:
        extracted_value, extracted_curr = extract_financial_info(afdb_obj.description)
        if extracted_value:
            estimated_value = extracted_value
        if not currency and extracted_curr:
            currency = extracted_curr
    
    # Try to extract procurement method
    procurement_method = None
    if hasattr(afdb_obj, 'tender_type') and afdb_obj.tender_type:
        procurement_method = extract_procurement_method(afdb_obj.tender_type)
    
    if not procurement_method and hasattr(afdb_obj, 'description') and afdb_obj.description:
        extracted_method = extract_procurement_method(afdb_obj.description)
        if extracted_method:
            procurement_method = extracted_method
    
    # Enhanced date extraction
    def parse_date_string(date_str):
        """Parse date string to datetime object with support for multiple formats"""
        if not date_str:
            return None
        
        # Clean the date string
        date_str = date_str.strip()
        
        # Try various datetime formats
        date_formats = [
            '%Y-%m-%d',           # YYYY-MM-DD
            '%d/%m/%Y',           # DD/MM/YYYY
            '%B %d, %Y',          # January 31, 2022
            '%d %B %Y',           # 31 January 2022
            '%b %d, %Y',          # Jan 31, 2022
            '%d %b %Y',           # 31 Jan 2022
            '%d-%m-%Y',           # DD-MM-YYYY
            '%Y/%m/%d',           # YYYY/MM/DD
        ]
        
        for date_format in date_formats:
            try:
                return datetime.strptime(date_str, date_format)
            except ValueError:
                continue
        
        # Try to extract date from text format like "Feb-2025"
        month_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[- ](\d{4})', date_str, re.IGNORECASE)
        if month_match:
            month_abbr = month_match.group(1).capitalize()
            year = month_match.group(2)
            try:
                # Default to 1st of the month if only month and year are provided
                return datetime.strptime(f"1 {month_abbr} {year}", "%d %b %Y")
            except ValueError:
                pass
                
        return None
    
    # Extract publication date with enhanced support
    publication_dt = None
    if hasattr(afdb_obj, 'publication_date') and afdb_obj.publication_date:
        if isinstance(afdb_obj.publication_date, datetime):
            publication_dt = afdb_obj.publication_date
        else:
            publication_dt = parse_date_string(str(afdb_obj.publication_date))
    
    # If publication date not found, try to extract from description
    if not publication_dt and hasattr(afdb_obj, 'description') and afdb_obj.description:
        # Look for date patterns in the text
        description = afdb_obj.description
        date_patterns = [
            r'published on (\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'published on (\d{4}[/-]\d{1,2}[/-]\d{1,2})',
            r'publication date:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'publication date:?\s*(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
            r'date of publication:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'date of publication:?\s*(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
            r'published:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'published:?\s*(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
            r'date:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'date:?\s*(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
            r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',
            r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})',
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})',
            r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                try:
                    publication_dt = parse_date_string(date_str)
                    if publication_dt:
                        break
                except:
                    continue
    
    # Extract closing/deadline date
    closing_date = None
    if hasattr(afdb_obj, 'closing_date') and afdb_obj.closing_date:
        if isinstance(afdb_obj.closing_date, datetime):
            closing_date = afdb_obj.closing_date
        else:
            closing_date = parse_date_string(str(afdb_obj.closing_date))
    
    # If closing date not found, try to extract from description
    if not closing_date and hasattr(afdb_obj, 'description') and afdb_obj.description:
        # Look for deadline patterns in the text
        description = afdb_obj.description
        deadline_patterns = [
            r'deadline\s*(?:date|for|is|:)?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'deadline\s*(?:date|for|is|:)?\s*(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
            r'closing\s*(?:date|on|is|:)?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'closing\s*(?:date|on|is|:)?\s*(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
            r'due\s*(?:date|on|by|:)?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'due\s*(?:date|on|by|:)?\s*(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
            r'submission\s*(?:date|by|deadline|:)?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'submission\s*(?:date|by|deadline|:)?\s*(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
            r'(?:to be )?received by\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(?:to be )?received by\s*(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
            r'deadline\s*(?:date|for|is|:)?\s*(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',
            r'deadline\s*(?:date|for|is|:)?\s*((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})',
            r'deadline\s*(?:date|for|is|:)?\s*(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})',
            r'deadline\s*(?:date|for|is|:)?\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4})',
        ]
        
        for pattern in deadline_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                try:
                    closing_date = parse_date_string(date_str)
                    if closing_date:
                        break
                except:
                    continue
    
    # Determine status with enhanced logic
    status = None
    
    # First check if status is explicitly set
    if hasattr(afdb_obj, 'status') and afdb_obj.status:
        status = afdb_obj.status
    else:
        # If closing date exists, check if tender is closed
        if closing_date:
            current_dt = datetime.now()
            if current_dt > closing_date:
                status = "Closed"
            else:
                status = "Open"
        
        # If still no status, try to extract from description
        if not status and hasattr(afdb_obj, 'description') and afdb_obj.description:
            extracted_status = extract_status(description=afdb_obj.description)
            if extracted_status:
                status = extracted_status
        
        # If still no status, try to derive from tender_type
        if not status and hasattr(afdb_obj, 'tender_type') and afdb_obj.tender_type:
            tender_type_lower = afdb_obj.tender_type.lower()
            
            # Check for planning/procurement plan
            if "plan" in tender_type_lower or "ppm" in tender_type_lower:
                status = "Planning"
            
            # Check for expressions of interest
            elif "expression of interest" in tender_type_lower or "eoi" in tender_type_lower:
                if closing_date:
                    current_dt = datetime.now()
                    if current_dt > closing_date:
                        status = "Closed"
                    else:
                        status = "Open"
                else:
                    status = "Active"  # Default for EOIs
            
            # Default status if we have publication date
            elif publication_dt:
                status = "Active"

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
        deadline_date=closing_date,
        country=country,
        city=city,
        organization_name=organization_name,
        project_name=afdb_obj.project_name,
        project_id=afdb_obj.project_id,
        estimated_value=estimated_value,
        currency=currency,
        url=afdb_obj.url,
        document_links=normalize_document_links(afdb_obj.document_links),
        procurement_method=procurement_method,
        language=language,
        original_data=row,
        normalized_method="offline-dictionary",
    )

    # Use the common apply_translations function for all fields
    unified = apply_translations(unified, language)

    return unified 