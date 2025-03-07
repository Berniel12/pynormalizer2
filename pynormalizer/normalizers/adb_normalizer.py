import json
from datetime import datetime
from typing import Dict, Any, Optional
import logging

from pynormalizer.models.source_models import ADBTender
from pynormalizer.models.unified_model import UnifiedTender
from pynormalizer.utils.translation import (
    translate_to_english, detect_language, apply_translations
)
from pynormalizer.utils.normalizer_helpers import (
    normalize_document_links, 
    extract_financial_info,
    log_before_after,
    ensure_country
)

logger = logging.getLogger(__name__)

def normalize_adb(row: Dict[str, Any]) -> UnifiedTender:
    """
    Normalize an ADB tender record.
    
    Args:
        row: Dictionary containing ADB tender data
        
    Returns:
        Normalized UnifiedTender instance
    """
    # Validate with Pydantic
    try:
        adb_obj = ADBTender(**row)
    except Exception as e:
        logger.error(f"Failed to validate ADB tender: {e}")
        raise ValueError(f"Failed to validate ADB tender: {e}")

    # Convert date -> datetime for publication_date/deadline
    publication_dt = datetime.combine(adb_obj.publication_date, datetime.min.time()) if adb_obj.publication_date else None
    deadline_dt = datetime.combine(adb_obj.due_date, datetime.min.time()) if adb_obj.due_date else None

    # Detect language from title and description
    language = "en"  # Default
    if adb_obj.notice_title:
        lang = detect_language(adb_obj.notice_title)
        if lang:
            language = lang
    elif adb_obj.description:
        lang = detect_language(adb_obj.description)
        if lang:
            language = lang
    
    logger.debug(f"Detected language for ADB tender {adb_obj.id}: {language}")

    # Handle country normalization - ensure it's never None
    country = adb_obj.country
    
    # Use ensure_country to normalize the country value
    normalized_country = ensure_country(
        country_value=country,
        text=adb_obj.description,
        organization=adb_obj.project_name  # Use project_name instead of executing_agency
    )
    
    # Never use None as a country value
    if normalized_country is not None:
        country = normalized_country
    elif country is None and adb_obj.project_name and 'philippines' in adb_obj.project_name.lower():
        # ADB is headquartered in the Philippines, use as fallback
        country = 'Philippines'
    elif country is None:
        # If everything fails, use 'Unknown' instead of None
        country = 'Unknown'
        logger.warning(f"Could not determine country for ADB tender {adb_obj.id}, using 'Unknown'")
    
    # Construct the UnifiedTender
    unified = UnifiedTender(
        # Required fields
        title=adb_obj.notice_title,
        source_table="adb",
        source_id=str(adb_obj.id),
        
        # Additional fields
        description=adb_obj.description,
        tender_type=adb_obj.type,
        publication_date=publication_dt,
        deadline_date=deadline_dt,
        country=country,
        project_name=adb_obj.project_name,
        project_id=adb_obj.project_id,
        project_number=adb_obj.project_number,
        sector=adb_obj.sector,
        url=adb_obj.pdf_url,
        reference_number=adb_obj.borrower_bid_no,
        original_data=row,
        language=language,
    )

    # Apply translations
    unified = apply_translations(unified, language)
    
    # Log before and after data
    logger.info(f"NORMALIZING ADB - {adb_obj.id}")
    logger.info(f"BEFORE:\n{row}")
    logger.info(f"AFTER:\n{unified.model_dump()}")
    logger.info(f"TRANSLATION: {unified.normalized_method}")
    logger.info("-" * 80)

    return unified 