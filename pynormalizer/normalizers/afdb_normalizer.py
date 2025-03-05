import json
from datetime import datetime
from typing import Dict, Any, Optional
import re

from pynormalizer.models.source_models import AFDBTender
from pynormalizer.models.unified_model import UnifiedTender
from pynormalizer.utils.translation import translate_to_english
from pynormalizer.utils.normalizer_helpers import normalize_document_links, extract_financial_info

def extract_organization(text: Optional[str]) -> Optional[str]:
    """
    Extract organization name from text.
    
    Args:
        text: Text to extract from
        
    Returns:
        Organization name if found, None otherwise
    """
    if not text:
        return None
        
    # Common organization patterns
    org_patterns = [
        r"(?:Ministry of|Ministry)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        r"(?:Department of|Department)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        r"(?:Authority of|Authority)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Authority|Board|Agency|Commission)"
    ]
    
    for pattern in org_patterns:
        matches = re.findall(pattern, text)
        if matches:
            return matches[0]
            
    return None

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

    # Extract city from country field if it contains format "Country - City"
    country = afdb_obj.country
    city = None
    
    if country and " - " in country:
        parts = country.split(" - ", 1)
        country = parts[0].strip()
        city = parts[1].strip() if len(parts) > 1 else None
    
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
                
    # Normalize document links to standardized format
    document_links = normalize_document_links(afdb_obj.document_links)
    
    # Determine status based on closing date
    status = None
    if afdb_obj.closing_date:
        if afdb_obj.closing_date < datetime.now().date():
            status = "Closed"
        else:
            status = "Open"
    elif afdb_obj.status:
        status = afdb_obj.status

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
        deadline_date=afdb_obj.closing_date,
        country=country,
        city=city,
        organization_name=organization_name,
        project_name=afdb_obj.project_name,
        project_id=afdb_obj.project_id,
        estimated_value=estimated_value,
        currency=currency,
        url=afdb_obj.url,
        document_links=document_links,
        original_data=row,
        normalized_method="offline-dictionary",
    )

    # Detect language from title and description
    language = "en"  # Default for AFDB
    
    # Apply translations
    if unified.title:
        title_en, title_method = translate_to_english(unified.title, language)
        unified.title_english = title_en
        
        # Set fallback_reason if already English
        if title_method == "already_english":
            unified.fallback_reason = json.dumps({"title": "already_english"})
    
    if unified.description:
        desc_en, desc_method = translate_to_english(unified.description, language)
        unified.description_english = desc_en
        
        # Update fallback_reason
        if desc_method == "already_english":
            if unified.fallback_reason:
                fallback = json.loads(unified.fallback_reason)
                fallback["description"] = "already_english"
                unified.fallback_reason = json.dumps(fallback)
            else:
                unified.fallback_reason = json.dumps({"description": "already_english"})
    
    if unified.organization_name:
        org_en, org_method = translate_to_english(unified.organization_name, language)
        unified.organization_name_english = org_en
        
        # Update fallback_reason
        if org_method == "already_english":
            if unified.fallback_reason:
                fallback = json.loads(unified.fallback_reason)
                fallback["organization_name"] = "already_english"
                unified.fallback_reason = json.dumps(fallback)
            else:
                unified.fallback_reason = json.dumps({"organization_name": "already_english"})
                
    if unified.project_name:
        proj_en, proj_method = translate_to_english(unified.project_name, language)
        unified.project_name_english = proj_en
        
        # Update fallback_reason
        if proj_method == "already_english":
            if unified.fallback_reason:
                fallback = json.loads(unified.fallback_reason)
                fallback["project_name"] = "already_english"
                unified.fallback_reason = json.dumps(fallback)
            else:
                unified.fallback_reason = json.dumps({"project_name": "already_english"})

    return unified 