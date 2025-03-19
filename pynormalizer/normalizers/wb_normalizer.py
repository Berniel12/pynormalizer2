"""
World Bank tender normalizer module.
"""
import json
import datetime
import re
import logging
import uuid

from pynormalizer.models.source_models import WBTender
from pynormalizer.models.unified_model import UnifiedTender
from pynormalizer.utils.translation import translate_to_english, detect_language, apply_translations
from pynormalizer.utils.normalizer_helpers import (
    normalize_document_links,
    extract_financial_info,
    extract_location_info,
    extract_organization,
    extract_procurement_method,
    extract_status,
    extract_deadline,
    normalize_title,
    normalize_description,
    ensure_country,
    clean_price,
    log_tender_normalization
)
from pynormalizer.utils.standardization import (
    standardize_title,
    structure_description,
    normalize_country,
    validate_cpv_code,
    validate_nuts_code,
    validate_currency_value,
    calculate_data_quality_score
)

logger = logging.getLogger(__name__)

def normalize_wb(tender: WBTender) -> UnifiedTender:
    """
    Normalize World Bank tender to unified format.
    
    Args:
        tender: WBTender object containing source data
        
    Returns:
        UnifiedTender object with normalized data
    """
    try:
        # Generate unique ID for the tender
        tender_id = str(uuid.uuid4())
        
        # Initialize unified tender
        unified = UnifiedTender(
            id=tender_id,
            source="worldbank",
            source_id=tender.id,
            source_url=tender.url
        )
        
        # Normalize title
        unified.title = normalize_title(tender.title)
        log_tender_normalization(tender_id, "title", tender.title, unified.title)
        
        # Normalize description
        unified.description = normalize_description(tender.description)
        log_tender_normalization(tender_id, "description", tender.description, unified.description)
        
        # Detect language and translate if needed
        language = detect_language(tender.title)
        unified.language = language or 'en'
        
        if language and language != 'en':
            logger.info(f"Detected non-English language: {language}")
            # Apply translations for key fields
            translations = {}
            
            # Title translation
            if unified.title:
                title_english = translate_to_english(unified.title, language)
                unified.title_english = title_english
                translations["title"] = title_english
                log_tender_normalization(tender_id, "title_translation", unified.title, unified.title_english)
            
            # Description translation
            if unified.description:
                desc_english = translate_to_english(unified.description, language)
                unified.description_english = desc_english
                translations["description"] = desc_english
                log_tender_normalization(tender_id, "description_translation", unified.description, unified.description_english)
                
            # Store translations for later reference
            unified.translations = json.dumps(translations)
        else:
            # For English content, copy the fields directly
            unified.title_english = unified.title
            unified.description_english = unified.description
        
        # Extract and normalize country
        country_name, country_code, country_code_3 = ensure_country(tender.country)
        unified.country = country_name
        # Don't add these to unified_tenders as they aren't in the schema yet
        # unified.country_code = country_code
        # unified.country_code_3 = country_code_3
        log_tender_normalization(tender_id, "country", tender.country, unified.country)
        
        # Extract additional location info if needed
        if not country_name or country_name == "Unknown":
            extracted_country, city = extract_location_info(unified.description)
            if extracted_country:
                unified.country = extracted_country
                log_tender_normalization(tender_id, "extracted_country", None, unified.country)
            if city:
                unified.city = city
                log_tender_normalization(tender_id, "city", None, unified.city)
        
        # Extract financial information
        amount, currency = extract_financial_info(unified.description)
        if amount and currency:
            unified.estimated_value = amount
            unified.currency = currency
            log_tender_normalization(tender_id, "financial_info", None, f"{amount} {currency}")
        
        # Extract procurement method
        method = extract_procurement_method(unified.description)
        if method:
            unified.procurement_method = method
            log_tender_normalization(tender_id, "procurement_method", None, method)
        
        # Extract organization information
        org_name = extract_organization(unified.description)
        if org_name:
            unified.organization_name = org_name
            log_tender_normalization(tender_id, "organization", None, org_name)
            
            # Also set in English if language is not English
            if language and language != 'en':
                org_english = translate_to_english(org_name, language)
                unified.organization_name_english = org_english
        
        # Extract and normalize status
        status = extract_status(unified.description)
        if status:
            unified.status = status
            log_tender_normalization(tender_id, "status", None, status)
        
        # Extract deadline
        deadline = extract_deadline(unified.description)
        if deadline:
            unified.deadline_date = deadline
            log_tender_normalization(tender_id, "deadline", None, deadline.isoformat())
        
        # Set publication date
        if tender.publication_date:
            unified.publication_date = tender.publication_date
        
        # Normalize document links
        if tender.documents:
            unified.documents = normalize_document_links(tender.documents)
        
        # World Bank specific fields
        if hasattr(tender, 'project_id'):
            unified.project_id = tender.project_id
        if hasattr(tender, 'borrower'):
            unified.organization_name = unified.organization_name or tender.borrower
        if hasattr(tender, 'funding_source'):
            # Store as part of original_data
            original_data = {"funding_source": tender.funding_source}
            unified.original_data = json.dumps(original_data)
        
        # Calculate data quality score
        quality_scores = calculate_data_quality_score(unified.dict())
        # Not storing in data_quality as it's not in the schema yet
        
        # Add normalized timestamp
        unified.normalized_at = datetime.utcnow()
        unified.normalized_method = "pynormalizer"
        
        return unified
        
    except Exception as e:
        logger.error(f"Error normalizing World Bank tender {tender.id}: {str(e)}")
        # Return a minimal unified tender for error cases
        error_tender = UnifiedTender(
            id=str(uuid.uuid4()),
            source="worldbank",
            source_id=tender.id if hasattr(tender, 'id') else "unknown",
            title=tender.title if hasattr(tender, 'title') else "Error in normalization",
            fallback_reason=f"Error: {str(e)}"
        )
        return error_tender