from datetime import datetime
from typing import Dict, Any
import logging

from pynormalizer.models.source_models import ADBTender
from pynormalizer.models.unified_model import UnifiedTender
from pynormalizer.utils.translation import detect_language
from pynormalizer.utils.normalizer_helpers import apply_translations, log_before_after

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
        country=adb_obj.country,
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
    log_before_after("adb", str(adb_obj.id), row, unified)

    return unified 