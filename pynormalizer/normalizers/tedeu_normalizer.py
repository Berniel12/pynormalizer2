from datetime import datetime
from typing import Dict, Any, Optional
import json

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

    # Extract estimated value and currency from links if present
    estimated_value = None
    currency = None
    
    # Extract city and country information if not in the main fields
    country = None
    city = None
    
    # Extract document links in consistent format
    document_links = []
    
    if tedeu_obj.links and isinstance(tedeu_obj.links, dict):
        # PDF links are often the most important, extract them
        if "pdf" in tedeu_obj.links and isinstance(tedeu_obj.links["pdf"], dict):
            for lang, link in tedeu_obj.links["pdf"].items():
                document_links.append({
                    "type": "pdf",
                    "language": lang,
                    "url": link
                })
                
        # Include XML links
        if "xml" in tedeu_obj.links and isinstance(tedeu_obj.links["xml"], dict):
            for lang, link in tedeu_obj.links["xml"].items():
                document_links.append({
                    "type": "xml",
                    "language": lang,
                    "url": link
                })
                
        # Include HTML links
        if "html" in tedeu_obj.links and isinstance(tedeu_obj.links["html"], dict):
            for lang, link in tedeu_obj.links["html"].items():
                document_links.append({
                    "type": "html",
                    "language": lang,
                    "url": link
                })
    
    # Try to extract country from lots if available
    if tedeu_obj.lots and isinstance(tedeu_obj.lots, list) and len(tedeu_obj.lots) > 0:
        for lot in tedeu_obj.lots:
            if isinstance(lot, dict):
                # Extract country
                if not country and 'country' in lot:
                    country = lot.get('country')
                    
                # Extract city
                if not city and 'city' in lot:
                    city = lot.get('city')
                    
                # Extract value information
                if not estimated_value and 'value' in lot:
                    lot_value = lot.get('value')
                    if isinstance(lot_value, dict):
                        if 'amount' in lot_value:
                            try:
                                estimated_value = float(lot_value.get('amount'))
                            except (ValueError, TypeError):
                                pass
                        if 'currency' in lot_value:
                            currency = lot_value.get('currency')

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
        country=country,
        city=city,
        organization_name=tedeu_obj.organisation_name,
        organization_id=tedeu_obj.organisation_id,
        contact_email=tedeu_obj.contact_email,
        contact_phone=tedeu_obj.contact_phone,
        url=tedeu_obj.contact_url,
        language=tedeu_obj.language,
        notice_id=tedeu_obj.notice_identifier or tedeu_obj.publication_number,
        document_links=document_links if document_links else tedeu_obj.links,
        procurement_method=procurement_method,
        estimated_value=estimated_value,
        currency=currency,
        original_data=row,
        normalized_method="offline-dictionary",
    )

    # Translate non-English fields if needed
    language = tedeu_obj.language or "en"
    
    # Translate title if needed
    if unified.title:
        title_en, title_method = translate_to_english(unified.title, language)
        unified.title_english = title_en
        
        # Set fallback_reason if already English
        if title_method == "already_english":
            unified.fallback_reason = json.dumps({"title": "already_english"})
    
    # Translate description if needed
    if unified.description:
        desc_en, desc_method = translate_to_english(unified.description, language)
        unified.description_english = desc_en
        
        # Update fallback_reason if already English
        if desc_method == "already_english":
            if unified.fallback_reason:
                fallback = json.loads(unified.fallback_reason)
                fallback["description"] = "already_english"
                unified.fallback_reason = json.dumps(fallback)
            else:
                unified.fallback_reason = json.dumps({"description": "already_english"})
    
    # Translate organization name if needed
    if unified.organization_name:
        org_en, org_method = translate_to_english(unified.organization_name, language)
        unified.organization_name_english = org_en
        
        # Update fallback_reason if already English
        if org_method == "already_english":
            if unified.fallback_reason:
                fallback = json.loads(unified.fallback_reason)
                fallback["organization_name"] = "already_english"
                unified.fallback_reason = json.dumps(fallback)
            else:
                unified.fallback_reason = json.dumps({"organization_name": "already_english"})

    return unified 