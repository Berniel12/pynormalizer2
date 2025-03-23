import re
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal

from pynormalizer.models.source_models import SamGovTender
from pynormalizer.models.unified_model import UnifiedTender

# Constants for procurement methods
PROCUREMENT_METHOD_PATTERNS = {
    'sole_source': r'(?i)(sole\s*source|single\s*source|direct\s*award)',
    'competitive': r'(?i)(competitive|full\s*and\s*open\s*competition|multiple\s*award)',
    'limited': r'(?i)(limited\s*competition|set-aside|small\s*business\s*set-aside)',
    'simplified': r'(?i)(simplified\s*acquisition|micro-purchase)',
}

# Status mapping
STATUS_MAPPING = {
    'active': ['active', 'published', 'open', 'posted'],
    'closed': ['closed', 'archived', 'inactive', 'completed'],
    'cancelled': ['canceled', 'cancelled', 'deleted'],
    'draft': ['draft', 'pending'],
}

def extract_financial_info(text: str) -> Tuple[Optional[Decimal], Optional[Decimal], Optional[str]]:
    """
    Extract financial information from text including estimated value and currency.
    
    Args:
        text: Text to extract financial information from
        
    Returns:
        Tuple of (min_value, max_value, currency)
    """
    if not text:
        return None, None, None
        
    # Currency pattern (USD is default for SAM.gov)
    currency = 'USD'
    
    # Look for monetary values
    # Pattern matches: $X,XXX.XX, $X.XX million/billion, X,XXX USD
    amount_pattern = r'(?:[\$€£]|USD|EUR|GBP)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|billion|M|B)?'
    
    amounts = []
    for match in re.finditer(amount_pattern, text, re.IGNORECASE):
        amount_str = match.group(1)
        amount = Decimal(amount_str.replace(',', ''))
        
        # Handle million/billion
        if 'billion' in match.group().lower() or 'B' in match.group():
            amount *= 1000000000
        elif 'million' in match.group().lower() or 'M' in match.group():
            amount *= 1000000
            
        amounts.append(amount)
    
    if not amounts:
        return None, None, None
        
    return min(amounts), max(amounts), currency

def extract_procurement_method(text: str) -> Optional[str]:
    """
    Extract procurement method from text using defined patterns.
    
    Args:
        text: Text to extract procurement method from
        
    Returns:
        Extracted procurement method or None
    """
    if not text:
        return None
        
    for method, pattern in PROCUREMENT_METHOD_PATTERNS.items():
        if re.search(pattern, text):
            return method
            
    return None

def normalize_status(status: str) -> str:
    """
    Normalize opportunity status to standard values.
    
    Args:
        status: Raw status string
        
    Returns:
        Normalized status string
    """
    if not status:
        return 'unknown'
        
    status_lower = status.lower()
    
    for normalized_status, variations in STATUS_MAPPING.items():
        if any(var in status_lower for var in variations):
            return normalized_status
            
    return 'unknown'

def extract_location_info(place_of_performance: Dict) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extract detailed location information from place of performance data.
    
    Args:
        place_of_performance: Dictionary containing location data
        
    Returns:
        Tuple of (city, state, country)
    """
    city = None
    state = None
    country = "United States"  # Default for SAM.gov
    
    if not place_of_performance:
        return city, state, country
        
    # Extract city
    city_value = (
        place_of_performance.get('city') or 
        place_of_performance.get('cityName')
    )
    
    if isinstance(city_value, dict):
        city = city_value.get('name') or next(iter(city_value.values()), None)
    else:
        city = city_value
        
    # Extract state
    state_value = (
        place_of_performance.get('state') or 
        place_of_performance.get('stateOrProvince')
    )
    
    if isinstance(state_value, dict):
        state = state_value.get('name') or next(iter(state_value.values()), None)
    else:
        state = state_value
        
    # Extract country
    country_value = (
        place_of_performance.get('country') or 
        place_of_performance.get('countryCode')
    )
    
    if country_value:
        if isinstance(country_value, dict):
            country = country_value.get('name') or country_value.get('code') or next(iter(country_value.values()), "United States")
        else:
            country = str(country_value)
            
    return city, state, country

def extract_organization_info(samgov_obj: SamGovTender) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Extract comprehensive organization information from SAM.gov tender.
    
    Args:
        samgov_obj: SAM.gov tender object
        
    Returns:
        Tuple of (organization_name, contact_name, contact_email, contact_phone, contact_address)
    """
    organization_name = None
    contact_name = None
    contact_email = None
    contact_phone = None
    contact_address = None
    
    # Extract from contacts
    if samgov_obj.contacts:
        primary_contact = None
        if isinstance(samgov_obj.contacts, list) and samgov_obj.contacts:
            primary_contact = samgov_obj.contacts[0]
        elif isinstance(samgov_obj.contacts, dict):
            primary_contact = samgov_obj.contacts
            
        if primary_contact and isinstance(primary_contact, dict):
            contact_name = primary_contact.get('name')
            contact_email = primary_contact.get('email')
            contact_phone = primary_contact.get('phone')
            organization_name = primary_contact.get('organization') or primary_contact.get('org')
            
            # Process address
            if 'address' in primary_contact and primary_contact['address']:
                addr = primary_contact['address']
                if isinstance(addr, dict):
                    address_parts = []
                    for field in ['street', 'line1', 'line2', 'city', 'state', 'zip', 'zipcode', 'postal_code', 'country']:
                        if field in addr and addr[field]:
                            address_parts.append(str(addr[field]))
                    if address_parts:
                        contact_address = ", ".join(address_parts)
                elif isinstance(addr, str):
                    contact_address = addr
    
    # Build organization name from department hierarchy
    if not organization_name:
        org_fields = ['department_name', 'agency', 'sub_tier', 'office']
        org_parts = []
        for field in org_fields:
            if hasattr(samgov_obj, field) and getattr(samgov_obj, field):
                value = getattr(samgov_obj, field)
                if isinstance(value, dict):
                    value = value.get('name') or next(iter(value.values()), None)
                if value:
                    org_parts.append(str(value))
        
        if org_parts:
            organization_name = " - ".join(org_parts)
    
    # Fall back to NAICS description
    if not organization_name and hasattr(samgov_obj, 'naics') and isinstance(samgov_obj.naics, dict):
        organization_name = samgov_obj.naics.get('description')
        
    return organization_name, contact_name, contact_email, contact_phone, contact_address

def normalize_samgov(row: Dict[str, Any]) -> UnifiedTender:
    """
    Normalize a SAM.gov tender record.
    
    Args:
        row: Dictionary containing SAM.gov tender data
        
    Returns:
        Normalized UnifiedTender instance
    """
    # Pre-process contacts field
    if 'contacts' in row and isinstance(row['contacts'], list):
        if row['contacts']:
            row['contacts'] = row['contacts'][0]
        else:
            row['contacts'] = {}
    
    # Validate with Pydantic
    try:
        samgov_obj = SamGovTender(**row)
    except Exception as e:
        raise ValueError(f"Failed to validate SAM.gov tender: {e}")

    # Extract organization information
    organization_name, contact_name, contact_email, contact_phone, contact_address = extract_organization_info(samgov_obj)

    # Extract location information
    city, state, country = extract_location_info(samgov_obj.place_of_performance)

    # Extract financial information from description
    min_value, max_value, currency = extract_financial_info(samgov_obj.description)

    # Extract procurement method
    procurement_method = extract_procurement_method(samgov_obj.description)

    # Normalize status
    normalized_status = normalize_status(samgov_obj.opportunity_status)

    # Construct the UnifiedTender
    unified = UnifiedTender(
        # Required fields
        title=samgov_obj.opportunity_title or f"Opportunity {samgov_obj.opportunity_id}",
        source_table="sam_gov",
        source_id=samgov_obj.opportunity_id,
        
        # Enhanced fields
        description=samgov_obj.description,
        tender_type=samgov_obj.opportunity_type,
        status=normalized_status,
        publication_date=samgov_obj.publish_date,
        deadline_date=samgov_obj.response_date,
        country=country,
        state=state,
        city=city,
        organization_name=organization_name,
        organization_id=samgov_obj.organization_id,
        reference_number=samgov_obj.solicitation_number,
        notice_id=samgov_obj.opportunity_id,
        contact_name=contact_name,
        contact_email=contact_email,
        contact_phone=contact_phone,
        contact_address=contact_address,
        procurement_method=procurement_method,
        estimated_cost_min=min_value,
        estimated_cost_max=max_value,
        currency=currency,
        original_data=row,
        language="en",  # SAM.gov is in English
        normalized_method="offline-dictionary",
    )

    # For SAM.gov, title is already in English
    unified.title_english = unified.title
    if unified.description:
        unified.description_english = unified.description
    if unified.organization_name:
        unified.organization_name_english = unified.organization_name

    return unified 