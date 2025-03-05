from datetime import datetime
from typing import Dict, Any

from pynormalizer.models.source_models import IADBTender
from pynormalizer.models.unified_model import UnifiedTender
from pynormalizer.utils.translation import translate_to_english, detect_language

def normalize_iadb(row: Dict[str, Any]) -> UnifiedTender:
    """
    Normalize an IADB (Inter-American Development Bank) tender record.
    
    Args:
        row: Dictionary containing IADB tender data
        
    Returns:
        Normalized UnifiedTender instance
    """
    # Validate with Pydantic
    try:
        iadb_obj = IADBTender(**row)
    except Exception as e:
        raise ValueError(f"Failed to validate IADB tender: {e}")

    # Convert date objects to datetime if needed
    publication_dt = None
    if iadb_obj.publication_date:
        publication_dt = datetime.combine(iadb_obj.publication_date, datetime.min.time())
    
    due_dt = None
    if iadb_obj.pue_date:  # "pue" appears to be the deadline date
        due_dt = datetime.combine(iadb_obj.pue_date, datetime.min.time())

    # Detect language based on country (many IADB countries are Spanish-speaking)
    spanish_countries = [
        "Argentina", "Bolivia", "Chile", "Colombia", "Costa Rica", "Cuba", 
        "Dominican Republic", "Ecuador", "El Salvador", "Guatemala", "Honduras", 
        "Mexico", "Nicaragua", "Panama", "Paraguay", "Peru", "Puerto Rico", 
        "Uruguay", "Venezuela"
    ]
    
    # Default language detection
    language = "es" if iadb_obj.country in spanish_countries else "en"
    
    # Try to detect from title if available
    if iadb_obj.notice_title:
        detected = detect_language(iadb_obj.notice_title)
        if detected:
            language = detected

    # Construct the UnifiedTender
    unified = UnifiedTender(
        # Required fields
        title=iadb_obj.notice_title or iadb_obj.project_name or f"IADB Project - {iadb_obj.project_number}",
        source_table="iadb",
        source_id=iadb_obj.project_number,  # Using project_number as the ID
        
        # Additional fields
        tender_type=iadb_obj.type,
        publication_date=publication_dt,
        deadline_date=due_dt,
        country=iadb_obj.country,
        project_name=iadb_obj.project_name,
        project_number=iadb_obj.project_number,
        url=iadb_obj.url or iadb_obj.url_pdf,
        language=language,
        original_data=row,
        normalized_method="offline-dictionary",
    )

    # Translate non-English fields if needed
    language = unified.language or "en"
    
    # Translate title if needed
    if unified.title:
        unified.title_english, _ = translate_to_english(unified.title, language)
    
    # Translate project name if needed
    if unified.project_name:
        unified.project_name_english, _ = translate_to_english(unified.project_name, language)

    return unified 