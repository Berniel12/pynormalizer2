from datetime import datetime
from typing import Dict, Any

from pynormalizer.models.source_models import AIIBTender
from pynormalizer.models.unified_model import UnifiedTender
from pynormalizer.utils.translation import translate_to_english

def normalize_aiib(row: Dict[str, Any]) -> UnifiedTender:
    """
    Normalize an AIIB (Asian Infrastructure Investment Bank) tender record.
    
    Args:
        row: Dictionary containing AIIB tender data
        
    Returns:
        Normalized UnifiedTender instance
    """
    # Validate with Pydantic
    try:
        aiib_obj = AIIBTender(**row)
    except Exception as e:
        raise ValueError(f"Failed to validate AIIB tender: {e}")

    # Parse date string if present
    publication_dt = None
    if aiib_obj.date:
        try:
            # Try different date formats
            date_formats = [
                "%Y-%m-%d",
                "%d/%m/%Y",
                "%m/%d/%Y",
                "%B %d, %Y",  # e.g. "January 15, 2023"
                "%d %B %Y",   # e.g. "15 January 2023"
            ]
            
            for fmt in date_formats:
                try:
                    publication_dt = datetime.strptime(aiib_obj.date, fmt)
                    break
                except ValueError:
                    continue
        except Exception:
            # If all parsing attempts fail, leave as None
            pass

    # Use project_notice as the title if available, otherwise use a placeholder
    title = aiib_obj.project_notice or f"AIIB Tender - {aiib_obj.id}"

    # Construct the UnifiedTender
    unified = UnifiedTender(
        # Required fields
        title=title,
        source_table="aiib",
        source_id=str(aiib_obj.id),
        
        # Additional fields
        description=aiib_obj.pdf_content,  # Using PDF content as description
        tender_type=aiib_obj.type,
        publication_date=publication_dt,
        country=aiib_obj.member,  # Member is equivalent to country
        sector=aiib_obj.sector,
        original_data=row,
        normalized_method="offline-dictionary",
    )

    # Translate title if needed
    if unified.title:
        unified.title_english, _ = translate_to_english(unified.title)
    
    # Translate description if needed
    if unified.description:
        unified.description_english, _ = translate_to_english(unified.description)

    return unified 