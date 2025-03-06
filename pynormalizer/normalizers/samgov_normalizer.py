from typing import Dict, Any

from pynormalizer.models.source_models import SamGovTender
from pynormalizer.models.unified_model import UnifiedTender

def normalize_samgov(row: Dict[str, Any]) -> UnifiedTender:
    """
    Normalize a SAM.gov tender record.
    
    Args:
        row: Dictionary containing SAM.gov tender data
        
    Returns:
        Normalized UnifiedTender instance
    """
    # Pre-process contacts field if it's a list instead of a dict
    if 'contacts' in row and isinstance(row['contacts'], list) and row['contacts']:
        # Convert list to dict by using the first contact
        row['contacts'] = row['contacts'][0]
    
    # Validate with Pydantic
    try:
        samgov_obj = SamGovTender(**row)
    except Exception as e:
        raise ValueError(f"Failed to validate SAM.gov tender: {e}")

    # Extract organization name from contacts if available
    organization_name = None
    contact_name = None
    contact_email = None
    contact_phone = None
    contact_address = None
    
    if samgov_obj.contacts:
        primary_contact = None
        # Try to find a primary contact in the contacts
        if isinstance(samgov_obj.contacts, list) and samgov_obj.contacts:
            primary_contact = samgov_obj.contacts[0]
        elif isinstance(samgov_obj.contacts, dict):
            # If it's a dict, it might be a single contact
            primary_contact = samgov_obj.contacts
            
        # Extract contact details
        if primary_contact:
            if isinstance(primary_contact, dict):
                contact_name = primary_contact.get('name')
                contact_email = primary_contact.get('email')
                contact_phone = primary_contact.get('phone')
                organization_name = primary_contact.get('organization') or primary_contact.get('org')
                
                # Try to extract address information
                if 'address' in primary_contact and primary_contact['address']:
                    addr = primary_contact['address']
                    if isinstance(addr, dict):
                        address_parts = []
                        # Common address components
                        for field in ['street', 'line1', 'line2', 'city', 'state', 'zip', 'zipcode', 'postal_code', 'country']:
                            if field in addr and addr[field]:
                                address_parts.append(str(addr[field]))
                        if address_parts:
                            contact_address = ", ".join(address_parts)
                    elif isinstance(addr, str):
                        contact_address = addr
    
    # Also try to get organization from additional fields
    if not organization_name:
        # Try departments, agency, etc.
        org_fields = ['department_name', 'agency', 'sub_tier', 'office']
        org_parts = []
        for field in org_fields:
            if hasattr(samgov_obj, field) and getattr(samgov_obj, field):
                org_parts.append(getattr(samgov_obj, field))
        
        if org_parts:
            organization_name = " - ".join(org_parts)
    
    # Fall back to naics code description if still no organization
    if not organization_name and hasattr(samgov_obj, 'naics') and isinstance(samgov_obj.naics, dict):
        if 'description' in samgov_obj.naics and samgov_obj.naics['description']:
            organization_name = samgov_obj.naics['description']

    # Extract location from place_of_performance
    city = None
    country = "United States"  # Default for SAM.gov
    
    if samgov_obj.place_of_performance and isinstance(samgov_obj.place_of_performance, dict):
        city_value = (
            samgov_obj.place_of_performance.get('city') or 
            samgov_obj.place_of_performance.get('cityName')
        )
        
        # Check for country info
        country_code = (
            samgov_obj.place_of_performance.get('country') or 
            samgov_obj.place_of_performance.get('countryCode')
        )
        
        # Only override default if explicitly specified
        if country_code and country_code != "USA" and country_code != "US":
            if isinstance(country_code, dict) and 'code' in country_code:
                country = country_code['code']
            else:
                country = str(country_code)
                
        # Handle city field being a dictionary
        if isinstance(city_value, dict):
            if 'name' in city_value:
                city = city_value['name']
            else:
                # Extract first value from the dictionary if it exists
                city_values = list(city_value.values())
                if city_values:
                    city = str(city_values[0])
        else:
            city = city_value

    # Handle country field if it's a dictionary
    if isinstance(country, dict):
        if 'code' in country:
            country = country['code']
        elif 'name' in country:
            country = country['name']
        else:
            # Extract first value from the dictionary if it exists
            country_values = list(country.values())
            if country_values:
                country = str(country_values[0])
            else:
                country = "United States"  # Default fallback

    # Construct the UnifiedTender
    unified = UnifiedTender(
        # Required fields
        title=samgov_obj.opportunity_title or f"Opportunity {samgov_obj.opportunity_id}",
        source_table="sam_gov",  # Updated to use the correct table name
        source_id=samgov_obj.opportunity_id,
        
        # Additional fields
        description=samgov_obj.description,
        tender_type=samgov_obj.opportunity_type,
        status=samgov_obj.opportunity_status,
        publication_date=samgov_obj.publish_date,
        deadline_date=samgov_obj.response_date,
        country=country,
        city=city,
        organization_name=organization_name,
        organization_id=samgov_obj.organization_id,
        reference_number=samgov_obj.solicitation_number,
        notice_id=samgov_obj.opportunity_id,
        contact_name=contact_name,
        contact_email=contact_email,
        contact_phone=contact_phone,
        contact_address=contact_address,
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