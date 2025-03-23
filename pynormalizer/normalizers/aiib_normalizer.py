import json
import re
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
from dateutil import parser as date_parser

from pynormalizer.models.source_models import AIIBTender
from pynormalizer.models.unified_model import UnifiedTender
from pynormalizer.utils.translation import (
    translate_to_english, detect_language, apply_translations
)
from pynormalizer.utils.normalizer_helpers import (
    normalize_document_links,
    extract_financial_info,
    extract_location_info,
    extract_organization,
    extract_organization_and_buyer,
    extract_procurement_method,
    extract_status,
    extract_deadline,
    normalize_title,
    normalize_description,
    ensure_country,
    determine_normalized_method,
    clean_price,
    log_tender_normalization
)

# Import custom helper functions
try:
    from pynormalizer.utils.normalizer_helpers_custom import validate_extracted_data
except ImportError:
    # Define a fallback function if the import fails
    def validate_extracted_data(data):
        return {'is_valid': True, 'issues': []}

# Get logger
logger = logging.getLogger(__name__)

# AIIB-specific sector patterns
SECTOR_PATTERNS = {
    'energy': [
        r'energy',
        r'electricity',
        r'power',
        r'renewable',
        r'solar',
        r'wind',
        r'hydropower',
        r'transmission',
        r'distribution'
    ],
    'transport': [
        r'transport',
        r'road[s]?',
        r'highway[s]?',
        r'railway[s]?',
        r'metro',
        r'airport',
        r'port[s]?',
        r'logistics',
        r'mobility'
    ],
    'urban': [
        r'urban',
        r'city',
        r'municipal',
        r'housing',
        r'settlement[s]?',
        r'smart city',
        r'urban planning',
        r'urban development'
    ],
    'water': [
        r'water',
        r'sanitation',
        r'sewage',
        r'drainage',
        r'irrigation',
        r'water supply',
        r'wastewater',
        r'flood control'
    ],
    'digital': [
        r'digital',
        r'ict',
        r'broadband',
        r'telecommunications',
        r'internet',
        r'connectivity',
        r'smart infrastructure'
    ],
    'social': [
        r'health',
        r'education',
        r'hospital',
        r'school',
        r'social infrastructure',
        r'community development'
    ],
    'sustainable': [
        r'sustainable',
        r'green',
        r'climate',
        r'environmental',
        r'resilience',
        r'adaptation',
        r'mitigation'
    ]
}

def extract_title_and_description(tender: AIIBTender) -> Tuple[str, Optional[str]]:
    """Extract title and description from project_notice and PDF content."""
    title = None
    description = None
    
    # First try to extract title from project_notice
    if tender.project_notice:
        # Look for common title patterns
        title_patterns = [
            # Project name followed by type
            r'^(.*?(?:Project|Program|Initiative|Development))\s*[-:]\s*(.*)',
            # Type followed by project name
            r'^(?:Notice|Tender|RFP|EOI|Procurement)\s*[-:]\s*(.*)',
            # Simple project name
            r'^([^-:]+)(?:\s*[-:]\s*(.*))?'
        ]
        
        for pattern in title_patterns:
            match = re.match(pattern, tender.project_notice, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) >= 2 and groups[1]:  # If we have both title and description
                    title = groups[0].strip()
                    description = groups[1].strip()
                else:  # If we only have title
                    title = groups[0].strip()
                break
    
    # If no title found, use project_notice as is
    if not title:
        title = tender.project_notice or f"AIIB Tender - {tender.id}"
    
    # Try to extract description from PDF content if not already found
    if not description and tender.pdf_content:
        # Look for description sections in PDF content
        desc_patterns = [
            r'(?:Project|Program)\s+Description[:\n](.*?)(?=\n\s*\n|\Z)',
            r'(?:Scope|Overview)\s+of\s+(?:Work|Services)[:\n](.*?)(?=\n\s*\n|\Z)',
            r'Background[:\n](.*?)(?=\n\s*\n|\Z)',
            r'Introduction[:\n](.*?)(?=\n\s*\n|\Z)'
        ]
        
        for pattern in desc_patterns:
            match = re.search(pattern, tender.pdf_content, re.IGNORECASE | re.DOTALL)
            if match:
                description = match.group(1).strip()
                # Clean up the description
                description = re.sub(r'\s+', ' ', description)
                # Truncate if too long
                if len(description) > 5000:
                    description = description[:5000] + "..."
                break
    
    return title, description

def extract_deadline_date(tender: AIIBTender) -> Optional[datetime]:
    """Extract deadline date from tender data with improved accuracy."""
    if not tender.pdf_content:
        return None
    
    # Common deadline patterns in AIIB documents
    deadline_patterns = [
        r'(?:deadline|due date|closing date|submission deadline|applications? due).*?(\d{1,2}[\s\./\-]+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\./\-]+\d{2,4})',
        r'(?:deadline|due date|closing date|submission deadline|applications? due).*?(\d{1,2}[\s\./\-]+\d{1,2}[\s\./\-]+\d{2,4})',
        r'(?:deadline|due date|closing date|submission deadline|applications? due).*?(\d{4}[\s\./\-]+\d{1,2}[\s\./\-]+\d{1,2})',
        r'(?:must be submitted|to be submitted).*?by.*?(\d{1,2}[\s\./\-]+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\./\-]+\d{2,4})',
        r'(?:must be submitted|to be submitted).*?before.*?(\d{1,2}[\s\./\-]+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\./\-]+\d{2,4})'
    ]
    
    for pattern in deadline_patterns:
        matches = re.finditer(pattern, tender.pdf_content, re.IGNORECASE)
        for match in matches:
            date_str = match.group(1).strip()
            
            # Clean up the date string
            date_str = re.sub(r'(?:st|nd|rd|th)', '', date_str)  # Remove ordinals
            date_str = re.sub(r'[,]', '', date_str)  # Remove commas
            date_str = re.sub(r'[\s\./\-]+', ' ', date_str)  # Normalize separators
            
            try:
                # Try parsing with dateutil first
                deadline = date_parser.parse(date_str)
                
                # Validate the date is reasonable (not in past, not too far in future)
                now = datetime.now()
                if now <= deadline <= now.replace(year=now.year + 2):
                    return deadline
            except (ValueError, TypeError):
                continue
    
    # Try extracting deadline using helper function
    return extract_deadline(tender.pdf_content)

def extract_sectors(tender: AIIBTender) -> List[str]:
    """Extract and categorize sectors with improved accuracy for AIIB context."""
    sectors = set()
    
    # Combine available text sources
    text_sources = []
    if tender.project_notice:
        text_sources.append(tender.project_notice)
    if tender.pdf_content:
        text_sources.append(tender.pdf_content)
    
    combined_text = ' '.join(text_sources).lower()
    
    # Check each sector's patterns
    for sector, patterns in SECTOR_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, combined_text, re.IGNORECASE):
                sectors.add(sector)
                break
    
    return list(sectors)

def normalize_document_links_enhanced(tender: AIIBTender) -> List[Dict[str, str]]:
    """Enhanced document link normalization for AIIB tenders."""
    normalized_docs = []
    
    # Process main PDF URL if available
    if tender.pdf_url:
        normalized = normalize_document_links(tender.pdf_url)
        if normalized:
            # Add AIIB-specific metadata
            for doc in normalized:
                doc.update({
                    'source': 'aiib',
                    'type': 'pdf',
                    'language': detect_language(tender.pdf_content) if tender.pdf_content else 'en',
                    'description': 'AIIB Tender Notice'
                })
            normalized_docs.extend(normalized)
    
    # Extract additional document links from PDF content
    if tender.pdf_content:
        # Look for document references in content
        doc_patterns = [
            r'(?:download|access|view|obtain)\s+(?:the|detailed)?\s*(?:document|tender|rfp|specification)s?\s+(?:at|from|via|through)?\s*(https?://\S+)',
            r'(?:document|tender|rfp|specification)s?\s+(?:are|is)\s+available\s+(?:at|from|via|through)?\s*(https?://\S+)',
            r'(?:please|kindly)\s+(?:visit|check|refer\s+to)\s*(https?://\S+)'
        ]
        
        for pattern in doc_patterns:
            matches = re.finditer(pattern, tender.pdf_content, re.IGNORECASE)
            for match in matches:
                url = match.group(1).strip()
                if url.endswith(('.', ')', ']', '}')):
                    url = url[:-1]
                
                # Normalize and validate the URL
                normalized = normalize_document_links(url)
                if normalized:
                    normalized_docs.extend(normalized)
    
    # Remove duplicates while preserving order
    seen_urls = set()
    unique_docs = []
    for doc in normalized_docs:
        if doc['url'] not in seen_urls:
            seen_urls.add(doc['url'])
            unique_docs.append(doc)
    
    return unique_docs

def normalize_aiib(row: Dict[str, Any]) -> UnifiedTender:
    """
    Normalize an AIIB tender record with improved extraction and validation.
    
    Args:
        row: Dictionary containing AIIB tender data
        
    Returns:
        Normalized UnifiedTender instance
    """
    try:
        logger.info(f"Starting AIIB normalization for row ID: {row.get('id', 'unknown')}")
        
        # Validate with Pydantic
        try:
            aiib_obj = AIIBTender(**row)
            logger.info("AIIB object validated successfully")
        except Exception as e:
            logger.error(f"Failed to validate AIIB tender: {e}")
            return UnifiedTender(
                title="Validation Error",
                source="aiib",
                source_id=str(row.get('id', 'unknown')),
                fallback_reason=f"Validation error: {str(e)}",
                original_data=row
            )

        try:
            # Extract title and description
            title, description = extract_title_and_description(aiib_obj)
            
            # Detect language
            language = detect_language(aiib_obj.pdf_content) if aiib_obj.pdf_content else "en"
            
            # Initialize unified tender
            unified = UnifiedTender(
                source="aiib",
                source_id=str(aiib_obj.id),
                title=title,
                description=description,
                language=language
            )
            
            # Apply translations if needed
            if language != 'en':
                unified = apply_translations(unified, language)
            
            # Extract deadline date
            deadline_date = extract_deadline_date(aiib_obj)
            if deadline_date:
                unified.deadline_date = deadline_date
            
            # Extract organization information
            org_name, buyer_info = extract_organization_and_buyer(aiib_obj.pdf_content or '')
            if org_name:
                unified.organization_name = org_name
                if language != 'en':
                    unified.organization_name_english = translate_to_english(org_name, language)
            
            if buyer_info:
                unified.buyer = buyer_info
            
            # Extract sectors
            sectors = extract_sectors(aiib_obj)
            if sectors:
                unified.sector = sectors[0]  # Primary sector
                unified.original_data = json.dumps({
                    **(json.loads(unified.original_data) if unified.original_data else {}),
                    "all_sectors": sectors
                })
            
            # Process document links
            unified.documents = normalize_document_links_enhanced(aiib_obj)
            
            # Extract other information using existing functions
            if aiib_obj.pdf_content:
                # Extract financial information
                amount, currency = extract_financial_info(aiib_obj.pdf_content)
                if amount and currency:
                    unified.estimated_value = amount
                    unified.currency = currency
                
                # Extract procurement method
                method = extract_procurement_method(aiib_obj.pdf_content)
                if method:
                    unified.procurement_method = method
                
                # Extract status
                status = extract_status(aiib_obj.pdf_content)
                if status:
                    unified.status = status
            
            # Validate extracted fields
            try:
                validation_results = validate_extracted_data(unified.dict())
                if not validation_results['is_valid']:
                    logger.warning(f"Validation issues for tender {aiib_obj.id}: {validation_results['issues']}")
                    unified.data_quality_issues = json.dumps(validation_results['issues'])
            except (NameError, ImportError) as e:
                # Function may not be available, log and continue
                logger.warning(f"Could not validate extracted data: {str(e)}")
            
            # Add normalized timestamp and method
            unified.normalized_at = datetime.utcnow()
            unified.normalized_method = "enhanced_aiib_normalizer"
            
            return unified
            
        except Exception as e:
            logger.error(f"Error during AIIB normalization: {e}")
            logger.error(traceback.format_exc())
            return UnifiedTender(
                title="Normalization Error",
                source="aiib",
                source_id=str(row.get('id', 'unknown')),
                fallback_reason=f"Normalization error: {str(e)}",
                original_data=row,
                normalized_method="error_fallback"
            )
            
    except Exception as e:
        logger.error(f"Critical error in AIIB normalizer: {e}")
        logger.error(traceback.format_exc())
        return UnifiedTender(
            title="Critical Error",
            source="aiib",
            source_id=str(row.get('id', 'unknown')),
            fallback_reason=f"Critical error: {str(e)}",
            original_data=row,
            normalized_method="critical_error"
        ) 