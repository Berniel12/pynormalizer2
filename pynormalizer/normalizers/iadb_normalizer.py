import json
from datetime import datetime, date
from typing import Dict, Any, Optional, Tuple, List
import re
import logging
from dateutil import parser as date_parser

from pynormalizer.models.source_models import IADBTender
from pynormalizer.models.unified_model import UnifiedTender
from pynormalizer.utils.translation import (
    translate_to_english, 
    detect_language, 
    apply_translations
)
from pynormalizer.utils.normalizer_helpers import (
    normalize_document_links,
    extract_financial_info,
    extract_procurement_method,
    parse_date_string,
    parse_date_from_text,
    clean_price,
    log_tender_normalization
)

logger = logging.getLogger(__name__)

# Common procurement method patterns in Spanish and English
PROCUREMENT_PATTERNS = {
    'open': [
        r'(?:licitación|licitacion)\s+(?:pública|publica)',
        r'(?:concurso|convocatoria)\s+(?:público|publico)',
        r'open\s+(?:tender|bidding)',
        r'international\s+competitive\s+bidding'
    ],
    'restricted': [
        r'licitación\s+restringida',
        r'concurso\s+limitado',
        r'restricted\s+(?:tender|bidding)',
        r'limited\s+competition'
    ],
    'direct': [
        r'adjudicación\s+directa',
        r'contratación\s+directa',
        r'direct\s+(?:contracting|award)',
        r'single\s+source'
    ],
    'framework': [
        r'acuerdo\s+marco',
        r'convenio\s+marco',
        r'framework\s+agreement',
        r'master\s+agreement'
    ]
}

# Financial amount patterns in Spanish and English
AMOUNT_PATTERNS = [
    # Spanish patterns
    r'(?:valor|monto|presupuesto|importe).*?(?:USD|US\$|\$)\s*([\d,.]+(?:\s*[mM](?:illon(?:es)?)?|\s*[bB](?:illon(?:es)?)?)?)',
    r'(?:USD|US\$|\$)\s*([\d,.]+(?:\s*[mM](?:illon(?:es)?)?|\s*[bB](?:illon(?:es)?)?)?)',
    # English patterns
    r'(?:value|amount|budget|cost).*?(?:USD|US\$|\$)\s*([\d,.]+(?:\s*[mM](?:illion)?|\s*[bB](?:illion)?)?)',
    r'([\d,.]+(?:\s*[mM](?:illion)?|\s*[bB](?:illion)?))\s*(?:USD|US\$|\$)'
]

def extract_description_from_pdf(tender: IADBTender) -> Optional[str]:
    """Extract and clean description from PDF content."""
    description = None
    
    # Try to get description from PDF content
    if hasattr(tender, 'pdf_content') and tender.pdf_content:
        content = tender.pdf_content
        
        # Remove common header/footer patterns
        content = re.sub(r'(?i)page \d+ of \d+', '', content)
        content = re.sub(r'(?i)inter-american development bank', '', content)
        
        # Extract main content sections
        sections = []
        
        # Look for project description section
        desc_patterns = [
            r'(?i)(?:project|tender)\s+description[:\n](.*?)(?=\n\s*\n|\Z)',
            r'(?i)descripción\s+del\s+(?:proyecto|contrato)[:\n](.*?)(?=\n\s*\n|\Z)',
            r'(?i)scope\s+of\s+(?:work|services)[:\n](.*?)(?=\n\s*\n|\Z)',
            r'(?i)alcance\s+(?:del\s+trabajo|de\s+los\s+servicios)[:\n](.*?)(?=\n\s*\n|\Z)'
        ]
        
        for pattern in desc_patterns:
            matches = re.finditer(pattern, content, re.DOTALL)
            for match in matches:
                section = match.group(1).strip()
                if len(section) > 50:  # Ignore very short matches
                    sections.append(section)
        
        if sections:
            # Combine sections and clean
            description = ' '.join(sections)
            # Clean up whitespace
            description = re.sub(r'\s+', ' ', description).strip()
            # Truncate if too long
            if len(description) > 5000:
                description = description[:5000] + "..."
    
    # Fallback to project name if no description found
    if not description and tender.project_name:
        description = tender.project_name
    
    return description

def extract_enhanced_financial_info(tender: IADBTender) -> Tuple[Optional[float], Optional[str]]:
    """Extract financial information with improved pattern matching."""
    amount, currency = None, None
    
    # Try to extract from various fields
    fields_to_check = []
    
    # Add PDF content if available
    if hasattr(tender, 'pdf_content') and tender.pdf_content:
        fields_to_check.append(tender.pdf_content)
    
    # Add other potential fields
    if hasattr(tender, 'notice_title') and tender.notice_title:
        fields_to_check.append(tender.notice_title)
    if hasattr(tender, 'project_name') and tender.project_name:
        fields_to_check.append(tender.project_name)
    
    # Try each field
    for field in fields_to_check:
        # Try each pattern
        for pattern in AMOUNT_PATTERNS:
            matches = re.finditer(pattern, field, re.IGNORECASE)
            for match in matches:
                try:
                    value_str = match.group(1).strip()
                    
                    # Handle million/billion abbreviations
                    multiplier = 1
                    if any(x in value_str.lower() for x in ['m', 'million', 'millon', 'millones']):
                        multiplier = 1_000_000
                        value_str = re.sub(r'[mM](?:illion|illon(?:es)?)?', '', value_str)
                    elif any(x in value_str.lower() for x in ['b', 'billion', 'billon', 'billones']):
                        multiplier = 1_000_000_000
                        value_str = re.sub(r'[bB](?:illion|illon(?:es)?)?', '', value_str)
                    
                    # Clean and convert to float
                    value_str = re.sub(r'[^\d.]', '', value_str)
                    amount = float(value_str) * multiplier
                    currency = 'USD'  # IADB typically uses USD
                    
                    if amount and currency:
                        return amount, currency
                except (ValueError, IndexError) as e:
                    logger.debug(f"Failed to parse amount from {value_str}: {e}")
                    continue
    
    # Try general financial extraction as fallback
    if not amount or not currency:
        for field in fields_to_check:
            extracted_amount, extracted_currency = extract_financial_info(field)
            if extracted_amount and extracted_currency:
                return extracted_amount, extracted_currency
    
    return amount, currency

def extract_procurement_method(tender: IADBTender) -> Optional[str]:
    """Extract procurement method with bilingual pattern matching."""
    if not hasattr(tender, 'pdf_content') or not tender.pdf_content:
        return None
    
    content = tender.pdf_content.lower()
    
    # Check each procurement type
    for method, patterns in PROCUREMENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return method
    
    # Try general procurement method extraction as fallback
    return extract_procurement_method(content)

def parse_date_enhanced(date_value: Any) -> Optional[datetime]:
    """Parse dates with improved handling of various formats."""
    if not date_value:
        return None
    
    # If already a datetime
    if isinstance(date_value, datetime):
        return date_value
    
    # If a date object
    if isinstance(date_value, date):
        return datetime.combine(date_value, datetime.min.time())
    
    # If a string, try multiple parsing methods
    if isinstance(date_value, str):
        # Try standard date parsing
        parsed_date = parse_date_string(date_value)
        if parsed_date:
            return parsed_date
            
        # Try dateutil parser with error handling
        try:
            return date_parser.parse(date_value)
        except (ValueError, TypeError):
            pass
        
        # Try to extract date from text
        return parse_date_from_text(date_value)
    
    return None

def normalize_iadb(row: Dict[str, Any]) -> UnifiedTender:
    """
    Normalize an IADB (Inter-American Development Bank) tender record with improved extraction and validation.
    
    Args:
        row: Dictionary containing IADB tender data
        
    Returns:
        Normalized UnifiedTender instance
    """
    # Validate with Pydantic
    try:
        iadb_obj = IADBTender(**row)
    except Exception as e:
        logger.error(f"Failed to validate IADB tender: {e}")
        # Return minimal tender with error info
        return UnifiedTender(
            title="Validation Error",
            source_table="iadb",
            source_id=str(row.get('project_number', 'unknown')),
            fallback_reason=f"Validation error: {str(e)}",
            original_data=row
        )

    try:
        # Parse dates with enhanced handling
        publication_dt = parse_date_enhanced(iadb_obj.publication_date)
        due_dt = parse_date_enhanced(iadb_obj.pue_date)  # "pue" appears to be the deadline date

        # Detect language with improved accuracy
        spanish_countries = [
            "Argentina", "Bolivia", "Chile", "Colombia", "Costa Rica", "Cuba", 
            "Dominican Republic", "Ecuador", "El Salvador", "Guatemala", "Honduras", 
            "Mexico", "Nicaragua", "Panama", "Paraguay", "Peru", "Puerto Rico", 
            "Uruguay", "Venezuela"
        ]
    
        # Default language detection based on country
        language = "es" if iadb_obj.country in spanish_countries else "en"
    
        # Try to detect from available text
        if iadb_obj.notice_title:
            detected = detect_language(iadb_obj.notice_title)
            if detected:
                language = detected
            elif hasattr(iadb_obj, 'pdf_content') and iadb_obj.pdf_content:
                # Try to detect from first 1000 characters of PDF content
                detected = detect_language(iadb_obj.pdf_content[:1000])
                if detected:
                    language = detected

        # Extract description from PDF content
        description = extract_description_from_pdf(iadb_obj)
        
        # Extract financial information
        estimated_value, currency = extract_enhanced_financial_info(iadb_obj)
        
        # Extract procurement method
        procurement_method = extract_procurement_method(iadb_obj)
        
        # Process document links
        document_links = []
        if iadb_obj.url_pdf:
            document_links.extend(normalize_document_links(iadb_obj.url_pdf))
        if iadb_obj.url:
            document_links.extend(normalize_document_links(iadb_obj.url))

        # Construct the UnifiedTender with improved data
        unified = UnifiedTender(
            # Required fields
            title=iadb_obj.notice_title or iadb_obj.project_name or f"IADB Project - {iadb_obj.project_number}",
            source_table="iadb",
            source_id=iadb_obj.project_number,  # Using project_number as the ID
            
            # Additional fields with enhanced data
            description=description,
            tender_type=iadb_obj.type,
            publication_date=publication_dt,
            deadline_date=due_dt,
            country=iadb_obj.country,
            project_name=iadb_obj.project_name,
            project_number=iadb_obj.project_number,
            url=iadb_obj.url or iadb_obj.url_pdf,
            document_links=document_links,
            estimated_value=estimated_value,
            currency=currency,
            procurement_method=procurement_method,
            language=language,
            original_data={
                **row,
                'normalized_method': 'enhanced_iadb_normalizer',
                'extracted_description': bool(description),
                'extracted_financial': bool(estimated_value and currency),
                'extracted_procurement': bool(procurement_method)
            }
        )

        # Apply translations if needed
        if language != 'en':
            unified = apply_translations(unified, language)
        
        # Log normalization results
        log_tender_normalization(
            source="iadb",
            tender_id=str(iadb_obj.project_number),
            data={
                "extracted_description": bool(description),
                "financial_info": f"{estimated_value} {currency}" if estimated_value and currency else None,
                "procurement_method": procurement_method,
                "document_count": len(document_links)
            }
        )

        return unified
        
    except Exception as e:
        logger.error(f"Error normalizing IADB tender: {e}")
        # Return minimal tender with error info
        return UnifiedTender(
            title="Normalization Error",
            source_table="iadb",
            source_id=str(row.get('project_number', 'unknown')),
            fallback_reason=f"Normalization error: {str(e)}",
            original_data=row
        ) 