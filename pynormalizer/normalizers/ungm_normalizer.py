import json
from datetime import datetime
from typing import Dict, Any, List

from pynormalizer.models.source_models import UNGMTender
from pynormalizer.models.unified_model import UnifiedTender
from pynormalizer.utils.translation import translate_to_english, detect_language

def normalize_ungm(row: Dict[str, Any]) -> UnifiedTender:
    """
    Normalize a UNGM (United Nations Global Marketplace) tender record.
    
    Args:
        row: Dictionary containing UNGM tender data
        
    Returns:
        Normalized UnifiedTender instance
    """
    # Handle JSON fields that might be lists or strings
    for field in ['links', 'unspscs', 'revisions', 'documents', 'contacts', 'sustainability', 'countries']:
        if field in row and isinstance(row[field], list):
            # Convert list to a dictionary with an 'items' key
            row[field] = {'items': row[field]}
        elif field in row and isinstance(row[field], str):
            try:
                if row[field].strip():
                    data = json.loads(row[field])
                    if isinstance(data, list):
                        row[field] = {'items': data}
                    else:
                        row[field] = data
                else:
                    row[field] = None
            except (json.JSONDecodeError, ValueError):
                row[field] = None
    
    # Validate with Pydantic
    try:
        ungm_obj = UNGMTender(**row)
    except Exception as e:
        raise ValueError(f"Failed to validate UNGM tender: {e}")

    # Parse date strings
    publication_dt = None
    if ungm_obj.published_on:
        try:
            # Try different date formats
            date_formats = [
                "%Y-%m-%d",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%d %b %Y",  # e.g., "15 Jan 2023"
                "%d-%b-%Y",  # e.g., "15-Jan-2023"
            ]
            
            for fmt in date_formats:
                try:
                    publication_dt = datetime.strptime(ungm_obj.published_on, fmt)
                    break
                except ValueError:
                    continue
        except Exception:
            # If all parsing attempts fail, leave as None
            pass
    
    deadline_dt = None
    if ungm_obj.deadline_on:
        try:
            for fmt in date_formats:
                try:
                    deadline_dt = datetime.strptime(ungm_obj.deadline_on, fmt)
                    break
                except ValueError:
                    continue
        except Exception:
            # If all parsing attempts fail, leave as None
            pass

    # Extract contact information
    contact_name = None
    contact_email = None
    contact_phone = None
    
    if ungm_obj.contacts and isinstance(ungm_obj.contacts, dict):
        # Try to find primary contact
        primary_contact = None
        if 'primary' in ungm_obj.contacts:
            primary_contact = ungm_obj.contacts['primary']
        elif isinstance(ungm_obj.contacts.get('contacts'), list) and ungm_obj.contacts['contacts']:
            primary_contact = ungm_obj.contacts['contacts'][0]
            
        if primary_contact and isinstance(primary_contact, dict):
            contact_name = primary_contact.get('name')
            contact_email = primary_contact.get('email')
            contact_phone = primary_contact.get('phone')

    # Extract countries
    country = None
    if ungm_obj.beneficiary_countries:
        # It might be a comma-separated string
        if isinstance(ungm_obj.beneficiary_countries, str):
            countries = ungm_obj.beneficiary_countries.split(',')
            country = countries[0].strip()  # Take the first one
        # Or it might be a list
        elif isinstance(ungm_obj.beneficiary_countries, list) and ungm_obj.beneficiary_countries:
            country = ungm_obj.beneficiary_countries[0]
    
    # If we couldn't extract from beneficiary_countries, try countries field
    if not country and ungm_obj.countries:
        if isinstance(ungm_obj.countries, dict) and 'countries' in ungm_obj.countries:
            countries_list = ungm_obj.countries['countries']
            if isinstance(countries_list, list) and countries_list:
                if isinstance(countries_list[0], dict) and 'name' in countries_list[0]:
                    country = countries_list[0]['name']
                else:
                    country = str(countries_list[0])

    # Get document links
    document_links = None
    if ungm_obj.documents and isinstance(ungm_obj.documents, dict) and 'documents' in ungm_obj.documents:
        documents = ungm_obj.documents['documents']
        if isinstance(documents, list):
            document_links = documents

    # Get URL
    url = None
    if ungm_obj.links and isinstance(ungm_obj.links, dict):
        if 'self' in ungm_obj.links:
            url = ungm_obj.links['self']
        elif 'notice' in ungm_obj.links:
            url = ungm_obj.links['notice']

    # Detect language from title
    language = detect_language(ungm_obj.title) or 'en'

    # Construct the UnifiedTender
    unified = UnifiedTender(
        # Required fields
        title=ungm_obj.title,
        source_table="ungm",
        source_id=str(ungm_obj.id),
        
        # Additional fields
        description=ungm_obj.description,
        status=ungm_obj.status,
        publication_date=publication_dt,
        deadline_date=deadline_dt,
        country=country,
        reference_number=ungm_obj.reference,
        contact_name=contact_name,
        contact_email=contact_email,
        contact_phone=contact_phone,
        url=url,
        document_links=document_links,
        language=language,
        original_data=row,
        normalized_method="offline-dictionary",
    )

    # Apply translations based on detected language
    if language != 'en':
        unified.title_english = translate_to_english(unified.title, language)
        if unified.description:
            unified.description_english = translate_to_english(unified.description, language)
    else:
        unified.title_english = unified.title
        unified.description_english = unified.description

    return unified 