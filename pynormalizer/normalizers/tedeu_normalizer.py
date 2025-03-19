"""
Normalizer for TED.eu tenders.
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid

from pynormalizer.models.source_models import TEDEuTender as TEDTender
from pynormalizer.models.unified_model import UnifiedTender
from pynormalizer.utils.translation import (
    translate_to_english,
    detect_language,
    apply_translations
)
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
    validate_cpv_code,
    validate_nuts_code,
    validate_currency_value,
    calculate_data_quality_score
)

logger = logging.getLogger(__name__)

def extract_tedeu_country(tender: Dict[str, Any]) -> Optional[str]:
    """Extract country from TED.eu tender data."""
    # Try org country first
    if 'organisation_country' in tender and tender['organisation_country']:
        return tender['organisation_country']
    
    # Try NUTS code
    if 'nuts_code' in tender and tender['nuts_code']:
        # Extract country code from NUTS code (first two chars)
        return tender['nuts_code'][:2]
    
    # Try from original address or name
    if 'organisation_address' in tender and tender['organisation_address']:
        # Extract from address
        _, country = extract_location_info(tender['organisation_address'])
        if country:
            return country
    
    # Try from summary
    if 'summary' in tender and tender['summary']:
        # Extract from summary
        country, _ = extract_location_info(tender['summary'])
        if country:
            return country
    
    return None

def normalize_tedeu(tender: Dict[str, Any]) -> UnifiedTender:
    """
    Normalize TED.eu tender to unified format.
    
    Args:
        tender: Dictionary containing source data
        
    Returns:
        UnifiedTender object with normalized data
    """
    try:
        # Generate unique ID for the tender
        tender_id = str(uuid.uuid4())
        
        # Initialize unified tender
        source_id = tender.get('id') or tender.get('publication_number', str(uuid.uuid4()))
        source_url = tender.get('url')
        
        unified = UnifiedTender(
            id=tender_id,
            source="tedeu",
            source_id=str(source_id),
            source_url=source_url,
            source_table="ted_eu"  # Add source_table which is a required field
        )
        
        # Use summary as description
        description = tender.get('summary', '')
        
        # Get title, defaulting to empty string if not present
        title = tender.get('title', '')
        
        # Normalize title
        unified.title = normalize_title(title)
        log_tender_normalization(tender_id, "title", title, unified.title)
        
        # Normalize description
        unified.description = normalize_description(description)
        log_tender_normalization(tender_id, "description", description, unified.description)
        
        # Detect language
        language = tender.get('language') or detect_language(title)
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
        country = extract_tedeu_country(tender)
        country_name, country_code, country_code_3 = ensure_country(country)
        unified.country = country_name
        log_tender_normalization(tender_id, "country", country, unified.country)
        
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
        amount, currency = None, None
        
        # Try value_magnitude first
        if 'value_magnitude' in tender and tender['value_magnitude']:
            amount = clean_price(tender['value_magnitude'])
            currency = tender.get('currency')
        
        # Fall back to extraction from description
        if not amount or not currency:
            extracted_amount, extracted_currency = extract_financial_info(unified.description)
            amount = amount or extracted_amount
            currency = currency or extracted_currency
            
        if amount and currency:
            unified.estimated_value = amount
            unified.currency = currency
            log_tender_normalization(tender_id, "financial_info", None, f"{amount} {currency}")
        
        # Extract procurement method
        method = None
        
        # Try procedure_type first
        if 'procedure_type' in tender and tender['procedure_type']:
            method = tender['procedure_type']
        
        # Fall back to extraction from description
        if not method:
            method = extract_procurement_method(unified.description)
            
        if method:
            unified.procurement_method = method
            log_tender_normalization(tender_id, "procurement_method", None, method)
        
        # Extract organization information
        org_name = None
        
        # Try organisation_name first
        if 'organisation_name' in tender and tender['organisation_name']:
            org_name = tender['organisation_name']
        
        # Fall back to extraction from description
        if not org_name:
            org_name = extract_organization(unified.description)
            
        if org_name:
            unified.organization_name = org_name
            log_tender_normalization(tender_id, "organization", None, org_name)
            
            # Also set in English if language is not English
            if language and language != 'en':
                org_english = translate_to_english(org_name, language)
                unified.organization_name_english = org_english
        
        # Extract and normalize status
        status = None
        
        # Try notice_status first
        if 'notice_status' in tender and tender['notice_status']:
            status = tender['notice_status']
        
        # Fall back to extraction from description
        if not status:
            status = extract_status(unified.description)
            
        if status:
            unified.status = status
            log_tender_normalization(tender_id, "status", None, status)
        
        # Set dates
        if 'publication_date' in tender and tender['publication_date']:
            unified.publication_date = tender['publication_date']
            
        if 'deadline_date' in tender and tender['deadline_date']:
            unified.deadline_date = tender['deadline_date']
        else:
            # Try to extract from description
            deadline = extract_deadline(unified.description)
            if deadline:
                unified.deadline_date = deadline
                log_tender_normalization(tender_id, "deadline", None, deadline.isoformat())
        
        # Normalize document links
        if 'links' in tender and tender['links']:
            unified.documents = normalize_document_links(tender['links'])
        
        # TED.eu specific fields - store in original_data
        original_data = {}
        
        # CPV codes
        if 'cpv_codes' in tender and tender['cpv_codes']:
            cpv_codes = []
            for code in tender['cpv_codes']:
                valid, issues = validate_cpv_code(code)
                if valid:
                    cpv_codes.append(code)
                else:
                    logger.warning(f"Invalid CPV code {code}: {issues}")
            
            if cpv_codes:
                original_data["cpv_codes"] = cpv_codes
        
        # NUTS codes
        if 'nuts_codes' in tender and tender['nuts_codes']:
            nuts_codes = []
            for code in tender['nuts_codes']:
                valid, issues = validate_nuts_code(code)
                if valid:
                    nuts_codes.append(code)
                else:
                    logger.warning(f"Invalid NUTS code {code}: {issues}")
            
            if nuts_codes:
                original_data["nuts_codes"] = nuts_codes
        
        # Additional specific fields
        for field in ['notice_type', 'regulation', 'procedure_type', 'award_criteria']:
            if field in tender and tender[field]:
                original_data[field] = tender[field]
                
                # Also set in the unified tender if field exists
                if hasattr(unified, field):
                    setattr(unified, field, tender[field])
        
        # Store original data
        if original_data:
            unified.original_data = json.dumps(original_data)
        
        # Calculate data quality score
        quality_scores = calculate_data_quality_score(unified.dict())
        # Not storing in data_quality as it's not in the schema yet
        
        # Add normalized timestamp
        unified.normalized_at = datetime.utcnow()
        unified.normalized_method = "pynormalizer"
        
        return unified
        
    except Exception as e:
        logger.error(f"Error normalizing TED.eu tender {tender.get('id', 'unknown')}: {str(e)}")
        # Return a minimal unified tender for error cases
        error_tender = UnifiedTender(
            id=str(uuid.uuid4()),
            source="tedeu",
            source_id=str(tender.get('id', None) or tender.get('publication_number', 'unknown')),
            source_table="ted_eu",  # Add required source_table field
            title=tender.get('title', "Error in normalization"),
            fallback_reason=f"Error: {str(e)}"
        )
        return error_tender 