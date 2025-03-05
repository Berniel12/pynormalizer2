from datetime import datetime
from typing import Dict, Any

from pynormalizer.models.source_models import AFDTender
from pynormalizer.models.unified_model import UnifiedTender
from pynormalizer.utils.translation import translate_to_english

def normalize_afd(row: Dict[str, Any]) -> UnifiedTender:
    """
    Normalize an AFD tender record.
    
    Args:
        row: Dictionary containing AFD tender data
        
    Returns:
        Normalized UnifiedTender instance
    """
    # Validate with Pydantic
    try:
        afd_obj = AFDTender(**row)
    except Exception as e:
        raise ValueError(f"Failed to validate AFD tender: {e}")

    # Parse string dates if provided
    publication_dt = None
    deadline_dt = None
    
    try:
        if afd_obj.publication_date:
            publication_dt = datetime.fromisoformat(afd_obj.publication_date.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        # Just leave as None if we can't parse
        pass
        
    try:
        if afd_obj.deadline:
            deadline_dt = datetime.fromisoformat(afd_obj.deadline.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        # Just leave as None if we can't parse
        pass

    # Detect language from original_language field
    language = afd_obj.original_language or 'auto'

    # Construct the UnifiedTender
    unified = UnifiedTender(
        # Required fields
        title=afd_obj.notice_title or "No title",  # Placeholder if missing
        source_table="afd",
        source_id=str(afd_obj.id),
        
        # Additional fields
        description=afd_obj.notice_content if afd_obj.notice_content and afd_obj.notice_content != "NO CONTENT" else None,
        publication_date=publication_dt,
        deadline_date=deadline_dt,
        country=afd_obj.country,
        city=afd_obj.city_locality,
        buyer=afd_obj.buyer,
        organization_name=afd_obj.agency,
        language=language,
        contact_email=afd_obj.email,
        contact_address=afd_obj.address,
        url=afd_obj.url,
        notice_id=afd_obj.notice_id,
        document_links=afd_obj.services,  # Store services as document_links
        original_data=row,
        normalized_method="offline-dictionary",
    )

    # Translate non-English fields if needed
    language = unified.language or "en"
    
    # Translate title if needed
    if unified.title:
        unified.title_english, _ = translate_to_english(unified.title, language)
    
    # Translate description if needed
    if unified.description:
        unified.description_english, _ = translate_to_english(unified.description, language)
        
    # Translate buyer if needed
    if unified.buyer:
        unified.buyer_english, _ = translate_to_english(unified.buyer, language)
        
    # Translate organization name if needed
    if unified.organization_name:
        unified.organization_name_english, _ = translate_to_english(unified.organization_name, language)

    return unified 