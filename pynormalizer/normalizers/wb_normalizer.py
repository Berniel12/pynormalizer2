"""
World Bank tender normalizer module.
"""
import json
import datetime
import re
import logging
import uuid
import traceback
from typing import List, Dict, Any, Optional

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

# Improved regex patterns using search instead of match
CITY_PATTERN = re.compile(r'(?:in|at|near|from)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)')
PROJECT_ID_PATTERN = re.compile(r'(?:Project\s+ID|Project\s+No|Project\s+Number)[:. ]*([A-Za-z0-9-]+)')
WB_REF_PATTERN = re.compile(r'(?:Reference\s+No|Ref\.?\s+No|Ref\s+Number)[:. ]*([A-Za-z0-9-/]+)')

def extract_wb_city(tender: WBTender) -> Optional[str]:
    """Extract city information from WB tender."""
    # Try various fields for city information
    possible_fields = [
        getattr(tender, 'location', None),
        getattr(tender, 'address', None),
        getattr(tender, 'project_location', None),
        getattr(tender, 'description', None)
    ]
    
    # Filter out None values
    text_fields = [field for field in possible_fields if field]
    
    for text in text_fields:
        # Try pattern matching first
        match = CITY_PATTERN.search(text)
        if match:
            return match.group(1).strip()
        
        # Try location extraction helper
        _, city = extract_location_info(text)
        if city:
            return city
    
    return None

def extract_project_info(tender: WBTender) -> Dict[str, Any]:
    """Extract project-related information from tender data."""
    project_info = {}
    
    # Extract from multiple fields
    text_fields = [
        getattr(tender, 'title', ''),
        getattr(tender, 'description', ''),
        getattr(tender, 'project_name', ''),
        getattr(tender, 'additional_info', '')
    ]
    
    # Filter out None values and join with spaces
    combined_text = ' '.join([field for field in text_fields if field])
    
    # Extract project ID
    project_id_match = PROJECT_ID_PATTERN.search(combined_text)
    if project_id_match:
        project_info['project_id'] = project_id_match.group(1).strip()
    elif hasattr(tender, 'project_id') and tender.project_id:
        project_info['project_id'] = tender.project_id
    
    # Extract reference number
    ref_match = WB_REF_PATTERN.search(combined_text)
    if ref_match:
        project_info['reference_no'] = ref_match.group(1).strip()
    
    # Add direct fields if they exist
    if hasattr(tender, 'project_name') and tender.project_name:
        project_info['project_name'] = tender.project_name
    
    if hasattr(tender, 'funding_source') and tender.funding_source:
        project_info['funding_source'] = tender.funding_source
    
    if hasattr(tender, 'borrower') and tender.borrower:
        project_info['borrower'] = tender.borrower
    
    return project_info

def safe_get_attr(obj: Any, attr: str, default: Any = None) -> Any:
    """Safely get an attribute from an object, returning default if not present."""
    if obj is None:
        return default
    return getattr(obj, attr, default)

def normalize_wb_documents(tender: WBTender) -> List[Dict[str, Any]]:
    """Enhanced document link normalization for World Bank tenders."""
    normalized_docs = []
    
    # Get documents from the tender object
    documents = safe_get_attr(tender, 'documents', [])
    
    # Return empty list if documents is None
    if documents is None:
        return []
    
    # Handle string documents (single URL or description)
    if isinstance(documents, str):
        # Use the general normalizer first
        normalized = normalize_document_links(documents)
        
        # If it returned something, use it
        if normalized:
            return normalized
        
        # Otherwise, try to extract URLs manually
        url_pattern = re.compile(r'https?://\S+')
        urls = url_pattern.findall(documents)
        
        for url in urls:
            normalized_docs.append({
                'url': url.strip(),
                'type': 'document',
                'language': 'en',
                'description': 'Document from World Bank'
            })
        
        return normalized_docs
    
    # Handle list of documents
    if isinstance(documents, list):
        for doc in documents:
            if doc is None:
                continue
                
            # If the document is already a dictionary
            if isinstance(doc, dict):
                normalized_doc = {
                    'url': doc.get('url', ''),
                    'type': doc.get('type', 'document'),
                    'language': doc.get('language', 'en'),
                    'description': doc.get('description', 'World Bank document')
                }
                
                # Only add if it has a valid URL
                if normalized_doc['url']:
                    normalized_docs.append(normalized_doc)
            
            # If the document is a string (likely a URL)
            elif isinstance(doc, str):
                # First try the general normalizer
                normalized = normalize_document_links(doc)
                
                if normalized:
                    normalized_docs.extend(normalized)
                else:
                    # Try to extract URLs manually
                    url_pattern = re.compile(r'https?://\S+')
                    urls = url_pattern.findall(doc)
                    
                    for url in urls:
                        normalized_docs.append({
                            'url': url.strip(),
                            'type': 'document',
                            'language': 'en',
                            'description': 'Document from World Bank'
                        })
    
    # Remove duplicates while preserving order
    seen_urls = set()
    unique_docs = []
    
    for doc in normalized_docs:
        if doc['url'] not in seen_urls:
            seen_urls.add(doc['url'])
            unique_docs.append(doc)
    
    return unique_docs

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
        
        # Get source ID safely
        source_id = safe_get_attr(tender, 'id', str(uuid.uuid4()))
        
        # Initialize unified tender
        unified = UnifiedTender(
            id=tender_id,
            source="worldbank",
            source_id=source_id,
            source_url=safe_get_attr(tender, 'url', None),
            source_table="wb_tenders"  # Add source_table which is a required field
        )
        
        # Normalize title (safely get title with fallback)
        title = safe_get_attr(tender, 'title', '')
        unified.title = normalize_title(title)
        log_tender_normalization("worldbank", source_id, {"field": "title", "before": title, "after": unified.title})
        
        # Normalize description
        description = safe_get_attr(tender, 'description', '')
        unified.description = normalize_description(description)
        log_tender_normalization("worldbank", source_id, {"field": "description", "before": description, "after": unified.description})
        
        # Detect language and translate if needed
        language = detect_language(title)
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
                log_tender_normalization("worldbank", source_id, {"field": "title_translation", "before": unified.title, "after": unified.title_english})
            
            # Description translation
            if unified.description:
                desc_english = translate_to_english(unified.description, language)
                unified.description_english = desc_english
                translations["description"] = desc_english
                log_tender_normalization("worldbank", source_id, {"field": "description_translation", "before": unified.description, "after": unified.description_english})
                
            # Store translations for later reference
            unified.translations = json.dumps(translations)
        else:
            # For English content, copy the fields directly
            unified.title_english = unified.title
            unified.description_english = unified.description
        
        # Extract and normalize country
        country = safe_get_attr(tender, 'country', None)
        country_name, country_code, country_code_3 = ensure_country(country_value=country)
        unified.country = country_name
        if country_code:
            unified.country_code = country_code
        if country_code_3:
            unified.country_code_3 = country_code_3
            
        log_tender_normalization("worldbank", source_id, {"field": "country", "before": country, "after": unified.country})
        
        # Extract additional location info if needed
        if not country_name or country_name == "Unknown":
            extracted_country, city = extract_location_info(unified.description)
            if extracted_country:
                unified.country = extracted_country
                log_tender_normalization("worldbank", source_id, {"field": "extracted_country", "before": None, "after": unified.country})
        
        # Extract city information with improved method
        city = extract_wb_city(tender)
        if city:
            unified.city = city
            log_tender_normalization("worldbank", source_id, {"field": "city", "before": None, "after": unified.city})
        
        # Extract financial information with improved methods
        amount, currency = None, None
        
        # Try direct fields first
        if hasattr(tender, 'value') and tender.value:
            amount = clean_price(tender.value)
            
        if hasattr(tender, 'currency') and tender.currency:
            currency = tender.currency
        
        # If not found, try extracting from description
        if not amount or not currency:
            extracted_amount, extracted_currency = extract_financial_info(unified.description)
            amount = amount or extracted_amount
            currency = currency or extracted_currency
            
        if amount and currency:
            unified.estimated_value = amount
            unified.currency = currency
            log_tender_normalization("worldbank", source_id, {"field": "financial_info", "before": None, "after": f"{amount} {currency}"})
        
        # Extract procurement method with fallback
        method = None
        if hasattr(tender, 'method') and tender.method:
            method = tender.method
        else:
            method = extract_procurement_method(unified.description)
            
        if method:
            unified.procurement_method = method
            log_tender_normalization("worldbank", source_id, {"field": "procurement_method", "before": None, "after": method})
        
        # Extract organization information
        org_name = None
    
    # Try direct fields first
        if hasattr(tender, 'borrower') and tender.borrower:
            org_name = tender.borrower
        elif hasattr(tender, 'organization') and tender.organization:
            org_name = tender.organization
        
        # Fall back to extraction from description
        if not org_name:
            org_name = extract_organization(unified.description)
            
        if org_name:
            unified.organization_name = org_name
            log_tender_normalization("worldbank", source_id, {"field": "organization", "before": None, "after": org_name})
            
            # Also set in English if language is not English
            if language and language != 'en':
                org_english = translate_to_english(org_name, language)
                unified.organization_name_english = org_english
        
        # Extract and normalize status
        status = None
        if hasattr(tender, 'status') and tender.status:
            status = tender.status
        else:
            status = extract_status(text=unified.description)
            
        if status:
            unified.status = status
            log_tender_normalization("worldbank", source_id, {"field": "status", "before": None, "after": status})
        
        # Set dates with improved handling
        # Extract deadline from multiple fields
        deadline = None
        
        if hasattr(tender, 'deadline_date') and tender.deadline_date:
            deadline = tender.deadline_date
        else:
            deadline = extract_deadline(unified.description)
            
        if deadline:
            unified.deadline_date = deadline
            log_tender_normalization("worldbank", source_id, {"field": "deadline", "before": None, "after": deadline.isoformat()})
        
        # Set publication date
        if hasattr(tender, 'publication_date') and tender.publication_date:
            unified.publication_date = tender.publication_date
        
        # Normalize document links with enhanced method
        unified.documents = normalize_wb_documents(tender)
        
        # World Bank specific fields with improved project info extraction
        project_info = extract_project_info(tender)
        
        # Set project_id directly in unified tender if available
        if 'project_id' in project_info:
            unified.project_id = project_info['project_id']
        
        # Set organization_name from borrower if not already set
        if not unified.organization_name and 'borrower' in project_info:
            unified.organization_name = project_info['borrower']
        
        # Store project info and other WB specific fields in original_data
        original_data = {**project_info}
        
        # Add sector information if available
        if hasattr(tender, 'sectors') and tender.sectors:
            original_data['sectors'] = tender.sectors
        
        if original_data:
            unified.original_data = json.dumps(original_data)
        
        # Calculate data quality score
        quality_scores = calculate_data_quality_score(unified.dict())
        # Not storing in data_quality as it's not in the schema yet
        
        # Add normalized timestamp
        unified.normalized_at = datetime.datetime.utcnow()
        unified.normalized_method = "pynormalizer"
        
        return unified
        
    except Exception as e:
        logger.error(f"Error normalizing World Bank tender {safe_get_attr(tender, 'id', 'unknown')}: {str(e)}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        
        # Return a minimal unified tender for error cases with safer attribute access
        error_tender = UnifiedTender(
            id=str(uuid.uuid4()),
            source="worldbank",
            source_id=safe_get_attr(tender, 'id', "unknown"),
            source_table="wb_tenders",  # Add required source_table field
            title=safe_get_attr(tender, 'title', "World Bank Tender Error"),  # Ensure title is never empty
            fallback_reason=f"Error: {str(e)}"
        )
        return error_tender