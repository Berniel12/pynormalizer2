import json
from datetime import datetime
from typing import Dict, Any

from pynormalizer.models.source_models import AFDBTender
from pynormalizer.models.unified_model import UnifiedTender
from pynormalizer.utils.translation import translate_to_english

def normalize_afdb(row: Dict[str, Any]) -> UnifiedTender:
    """
    Normalize an AFDB (African Development Bank) tender record.
    
    Args:
        row: Dictionary containing AFDB tender data
        
    Returns:
        Normalized UnifiedTender instance
    """
    # Handle document_links if it's a string
    if isinstance(row.get('document_links'), str):
        try:
            if row['document_links'].strip():
                row['document_links'] = json.loads(row['document_links'])
            else:
                row['document_links'] = None
        except (json.JSONDecodeError, ValueError):
            row['document_links'] = None
    
    # Validate with Pydantic
    try:
        afdb_obj = AFDBTender(**row)
    except Exception as e:
        raise ValueError(f"Failed to validate AFDB tender: {e}")

    # Parse string publication_date if it's a string
    publication_dt = None
    if afdb_obj.publication_date:
        if isinstance(afdb_obj.publication_date, str):
            try:
                publication_dt = datetime.fromisoformat(afdb_obj.publication_date.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                pass
        else:
            publication_dt = afdb_obj.publication_date  # Assume it's already a datetime

    # Construct the UnifiedTender
    unified = UnifiedTender(
        # Required fields
        title=afdb_obj.title or "No title",  # Placeholder if missing
        source_table="afdb",
        source_id=str(afdb_obj.id),
        
        # Additional fields
        description=afdb_obj.description,
        tender_type=afdb_obj.tender_type,
        status=afdb_obj.status,
        publication_date=publication_dt,
        deadline_date=afdb_obj.closing_date,  # Already a date object
        country=afdb_obj.country,
        project_name=afdb_obj.project_name,
        project_id=afdb_obj.project_id,
        sector=afdb_obj.sector,
        estimated_value=afdb_obj.estimated_value,
        currency=afdb_obj.currency,
        url=afdb_obj.url,
        document_links=afdb_obj.document_links,
        original_data=row,
        normalized_method="offline-dictionary",
    )

    # Apply translations
    unified.title_english = translate_to_english(unified.title)
    if unified.description:
        unified.description_english = translate_to_english(unified.description)
    if unified.project_name:
        unified.project_name_english = translate_to_english(unified.project_name)

    return unified 