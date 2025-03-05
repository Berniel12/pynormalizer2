from typing import Dict, Any

from pynormalizer.models.source_models import WBTender
from pynormalizer.models.unified_model import UnifiedTender
from pynormalizer.utils.translation import translate_to_english, detect_language

def normalize_wb(row: Dict[str, Any]) -> UnifiedTender:
    """
    Normalize a World Bank tender record.
    
    Args:
        row: Dictionary containing World Bank tender data
        
    Returns:
        Normalized UnifiedTender instance
    """
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

    # Construct the UnifiedTender
    unified = UnifiedTender(
        # Required fields
        title=wb_obj.title or f"World Bank Tender - {wb_obj.id}",
        source_table="wb",
        source_id=wb_obj.id,
        
        # Additional fields
        description=wb_obj.description or wb_obj.notice_text,
        tender_type=wb_obj.tender_type or wb_obj.notice_type,
        status=wb_obj.notice_status,
        publication_date=wb_obj.publication_date,
        deadline_date=wb_obj.deadline or wb_obj.submission_date,
        country=wb_obj.country or wb_obj.project_ctry_name,
        project_name=wb_obj.project_name,
        project_id=wb_obj.project_id,
        contact_name=wb_obj.contact_name,
        contact_email=wb_obj.contact_email,
        contact_phone=wb_obj.contact_phone,
        contact_address=wb_obj.contact_address,
        organization_name=wb_obj.contact_organization,
        url=wb_obj.url,
        document_links=wb_obj.document_links,
        language=language,
        reference_number=wb_obj.bid_reference_no,
        procurement_method=wb_obj.procurement_method or wb_obj.procurement_method_name,
        original_data=row,
        normalized_method="offline-dictionary",
    )

    # Apply translations
    if language != 'en':
        unified.title_english = translate_to_english(unified.title, language)
        if unified.description:
            unified.description_english = translate_to_english(unified.description, language)
        if unified.project_name:
            unified.project_name_english = translate_to_english(unified.project_name, language)
        if unified.organization_name:
            unified.organization_name_english = translate_to_english(unified.organization_name, language)
    else:
        # If language is English, keep as is
        unified.title_english = unified.title
        unified.description_english = unified.description
        unified.project_name_english = unified.project_name
        unified.organization_name_english = unified.organization_name

    return unified 