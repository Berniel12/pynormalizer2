from datetime import datetime
from typing import Dict, Any, Optional

from pynormalizer.models.source_models import TEDEuTender
from pynormalizer.models.unified_model import UnifiedTender
from pynormalizer.utils.translation import translate_to_english

def normalize_tedeu(row: Dict[str, Any]) -> UnifiedTender:
    """
    Normalize a TED.eu (Tenders Electronic Daily) tender record.
    
    Args:
        row: Dictionary containing TED.eu tender data
        
    Returns:
        Normalized UnifiedTender instance
    """
    # Validate with Pydantic
    try:
        tedeu_obj = TEDEuTender(**row)
    except Exception as e:
        raise ValueError(f"Failed to validate TED.eu tender: {e}")

    # Convert date objects to datetime if needed
    publication_dt = None
    if tedeu_obj.publication_date:
        if isinstance(tedeu_obj.publication_date, datetime):
            publication_dt = tedeu_obj.publication_date
        else:
            publication_dt = datetime.combine(tedeu_obj.publication_date, datetime.min.time())
    
    deadline_dt = None
    if tedeu_obj.deadline_date:
        if isinstance(tedeu_obj.deadline_date, datetime):
            deadline_dt = tedeu_obj.deadline_date
        else:
            deadline_dt = datetime.combine(tedeu_obj.deadline_date, datetime.min.time())

    # Determine procurement method from procedure_type
    procurement_method = None
    if tedeu_obj.procedure_type:
        # Map TED procedure types to general procurement methods
        procurement_map = {
            "OPEN": "Open Procedure",
            "RESTRICTED": "Restricted Procedure",
            "COMPETITIVE_NEGOTIATION": "Competitive Procedure with Negotiation",
            "COMPETITIVE_DIALOGUE": "Competitive Dialogue",
            "INNOVATION_PARTNERSHIP": "Innovation Partnership",
            "DESIGN_CONTEST": "Design Contest",
            "NEGOTIATED_WITH_PRIOR_CALL": "Negotiated Procedure with Prior Call for Competition",
            "NEGOTIATED_WITHOUT_PRIOR_CALL": "Negotiated Procedure without Prior Call for Competition",
        }
        procurement_method = procurement_map.get(tedeu_obj.procedure_type.upper(), tedeu_obj.procedure_type)

    # Construct the UnifiedTender
    unified = UnifiedTender(
        # Required fields
        title=tedeu_obj.title or f"TED Notice - {tedeu_obj.publication_number}",
        source_table="ted_eu",
        source_id=tedeu_obj.publication_number,  # Using publication_number as the ID
        
        # Additional fields
        description=tedeu_obj.summary or tedeu_obj.additional_information,
        tender_type=tedeu_obj.notice_type,
        status=tedeu_obj.notice_status,
        publication_date=publication_dt,
        deadline_date=deadline_dt,
        organization_name=tedeu_obj.organisation_name,
        organization_id=tedeu_obj.organisation_id,
        contact_email=tedeu_obj.contact_email,
        contact_phone=tedeu_obj.contact_phone,
        url=tedeu_obj.contact_url,
        language=tedeu_obj.language,
        notice_id=tedeu_obj.notice_identifier or tedeu_obj.publication_number,
        document_links=tedeu_obj.links,
        procurement_method=procurement_method,
        original_data=row,
        normalized_method="offline-dictionary",
    )

    # Translate non-English fields if needed
    language = tedeu_obj.language or "en"
    
    # Translate title if needed
    if unified.title:
        unified.title_english, _ = translate_to_english(unified.title, language)
    
    # Translate description if needed
    if unified.description:
        unified.description_english, _ = translate_to_english(unified.description, language)
    
    # Translate organization name if needed
    if unified.organization_name:
        unified.organization_name_english, _ = translate_to_english(unified.organization_name, language)

    return unified 