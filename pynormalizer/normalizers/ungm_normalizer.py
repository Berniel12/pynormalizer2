import json
from datetime import datetime
from typing import Dict, Any, List
import re

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
    
    # If no country yet, try country from beneficiary_countries
    if not country and ungm_obj.beneficiary_countries:
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
    document_links = []
    if ungm_obj.documents and isinstance(ungm_obj.documents, dict) and 'documents' in ungm_obj.documents:
        documents = ungm_obj.documents['documents']
        if isinstance(documents, list):
            for doc in documents:
                if isinstance(doc, dict) and 'url' in doc:
                    document_links.append({
                        'url': doc['url'],
                        'type': doc.get('type', 'unknown'),
                        'language': doc.get('language', 'en'),
                        'description': doc.get('description', doc.get('title', None))
                    })

    # Get URL - improved extraction and fallback mechanisms
    url = None
    if ungm_obj.links and isinstance(ungm_obj.links, dict):
        # Try several potential fields where URLs might be stored
        url_fields = ['self', 'notice', 'tender', 'details', 'href', 'url']
        for field in url_fields:
            if field in ungm_obj.links and ungm_obj.links[field]:
                url = ungm_obj.links[field]
                break
        
        # If URL is still not found but there's an 'items' list, check the items
        if not url and 'items' in ungm_obj.links and isinstance(ungm_obj.links['items'], list):
            for item in ungm_obj.links['items']:
                if isinstance(item, dict) and 'href' in item:
                    url = item['href']
                    break
                elif isinstance(item, dict) and 'url' in item:
                    url = item['url']
                    break
                elif isinstance(item, str) and (item.startswith('http://') or item.startswith('https://')):
                    url = item
                    break
    
    # If still no URL found and we have a reference number, try to construct a generic UNGM URL
    if not url and ungm_obj.reference:
        url = f"https://www.ungm.org/Public/Notice/{ungm_obj.reference}"
    
    # If we have a URL, add it to document_links if not already included
    if url:
        url_already_included = False
        for link in document_links:
            if isinstance(link, dict) and link.get('url') == url:
                url_already_included = True
                break
        
        if not url_already_included:
            document_links.append({
                'url': url,
                'type': 'main',
                'language': 'en',
                'description': 'Main tender notice'
            })
    
    # Detect language from title and description combined
    lang_sample = ""
    if ungm_obj.title:
        lang_sample += ungm_obj.title + " "
    if ungm_obj.description:
        # Add first 200 characters from description for better language detection
        lang_sample += ungm_obj.description[:200]
    
    language = detect_language(lang_sample.strip()) or 'en'

    # Get organization name
    organization_name = None
    buyer = None
    
    # Try to get from contacts
    if ungm_obj.contacts and isinstance(ungm_obj.contacts, dict):
        if 'title' in ungm_obj.contacts and ungm_obj.contacts['title']:
            organization_name = ungm_obj.contacts['title']
        elif 'contact_details' in ungm_obj.contacts and isinstance(ungm_obj.contacts['contact_details'], dict):
            if 'Organization' in ungm_obj.contacts['contact_details']:
                organization_name = ungm_obj.contacts['contact_details']['Organization']
    
    # Try to parse organization name from title/description if still not found
    if not organization_name and ungm_obj.title:
        # Look for patterns like "Organization: XYZ" or "by XYZ" in title
        org_patterns = [
            r'(?:by|from|for)\s+([A-Za-z0-9\s\(\)&,\.\-]+?)(?:\s+in|\s+for|\s+at|$)',
            r'([A-Za-z0-9\s\(\)&,\.\-]+?)\s+(?:is seeking|requests|invites)'
        ]
        
        for pattern in org_patterns:
            match = re.search(pattern, ungm_obj.title)
            if match:
                potential_org = match.group(1).strip()
                if len(potential_org) > 3 and potential_org.lower() not in ['the', 'and', 'for', 'of']:
                    organization_name = potential_org
                    break
    
    # Parse organization name that includes country information
    if organization_name:
        # Check if organization name has country prefix like "COUNTRY - Organization Name"
        country_org_match = re.match(r'^([A-Z]{2,})\s*-\s*(.+)$', organization_name)
        if country_org_match:
            country_code = country_org_match.group(1).strip()
            org_name = country_org_match.group(2).strip()
            
            # Only separate if first part looks like a country code
            if len(country_code) <= 3 or country_code in ['UNDP', 'UNEP', 'UNHCR', 'UNICEF', 'WHO', 'FAO']:
                # It's likely an organization abbreviation, not a country
                pass
            else:
                # It's a country name, so update the country field if not set
                if not country:
                    country = country_code
                organization_name = org_name
                
    # Use the organization name as buyer if it's not set
    if organization_name and not buyer:
        buyer = organization_name

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

    # Translate non-English fields if needed
    language = unified.language or "en"
    
    try:
        # Translate title if needed
        if unified.title and language != "en":
            unified.title_english, _ = translate_to_english(unified.title, language)
            # Verify translation quality - if translation is too short compared to original,
            # try translating larger chunks of the title
            if unified.title_english and len(unified.title_english) < len(unified.title) * 0.5:
                # Try translating again with more context
                title_chunks = [unified.title[i:i+500] for i in range(0, len(unified.title), 500)]
                translated_chunks = []
                for chunk in title_chunks:
                    trans, _ = translate_to_english(chunk, language)
                    translated_chunks.append(trans)
                unified.title_english = " ".join(translated_chunks)
    except Exception as e:
        # Log the error and continue with untranslated text
        print(f"Error translating title: {e}")
        if not unified.title_english:
            unified.title_english = unified.title
    
    try:
        # Translate description if needed
        if unified.description and language != "en":
            # For longer descriptions, split into manageable chunks for translation
            if len(unified.description) > 1000:
                desc_chunks = [unified.description[i:i+1000] for i in range(0, len(unified.description), 1000)]
                translated_chunks = []
                for chunk in desc_chunks:
                    trans, _ = translate_to_english(chunk, language)
                    translated_chunks.append(trans)
                unified.description_english = " ".join(translated_chunks)
            else:
                unified.description_english, _ = translate_to_english(unified.description, language)
    except Exception as e:
        # Log the error and continue with untranslated text
        print(f"Error translating description: {e}")
        if not unified.description_english:
            unified.description_english = unified.description

    return unified 