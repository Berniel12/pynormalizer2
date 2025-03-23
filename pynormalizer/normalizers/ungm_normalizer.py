"""
UNGM tender normalizer with enhanced validation and error handling.
"""
import json
import re
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal

from pynormalizer.models.source_models import UNGMTender
from pynormalizer.models.unified_model import UnifiedTender
from pynormalizer.utils.translation import translate_to_english, detect_language
from pynormalizer.utils.normalizer_helpers import (
    normalize_document_links,
    extract_financial_info,
    extract_location_info,
    extract_organization_and_buyer,
    extract_procurement_method,
    extract_status,
    parse_date_string,
    ensure_country,
    clean_price,
    log_tender_normalization,
    log_before_after
)
from pynormalizer.utils.validation import (
    validate_field,
    calculate_tender_quality,
    normalize_text,
    detect_encoding_issues,
    validate_schema
)
from .base_normalizer import BaseNormalizer

logger = logging.getLogger(__name__)

# Constants for procurement methods in UN context
PROCUREMENT_METHOD_PATTERNS = {
    'open': [
        r'(?i)(?:open|international)\s+(?:tender|competition|bidding)',
        r'(?i)request\s+for\s+proposal',
        r'(?i)invitation\s+to\s+bid'
    ],
    'restricted': [
        r'(?i)restricted\s+(?:tender|bidding)',
        r'(?i)limited\s+competition',
        r'(?i)pre[-\s]qualified\s+suppliers'
    ],
    'direct': [
        r'(?i)direct\s+(?:procurement|contracting)',
        r'(?i)single\s+source',
        r'(?i)sole\s+source'
    ],
    'framework': [
        r'(?i)framework\s+agreement',
        r'(?i)long[-\s]term\s+agreement',
        r'(?i)lta'
    ]
}

# Status mapping for UNGM
STATUS_MAPPING = {
    'active': ['active', 'open', 'published', 'current'],
    'closed': ['closed', 'completed', 'awarded', 'expired'],
    'cancelled': ['canceled', 'cancelled', 'withdrawn'],
    'draft': ['draft', 'pending', 'upcoming']
}

def extract_financial_info_ungm(text: str, currency_hint: Optional[str] = None) -> Tuple[Optional[Decimal], Optional[str]]:
    """
    Extract financial information from UNGM tender text.
    
    Args:
        text: Text to extract financial information from
        currency_hint: Optional hint about the expected currency
        
    Returns:
        Tuple of (amount, currency)
    """
    if not text:
        return None, None
        
    # UN typically uses USD, but also look for other currencies
    amount_patterns = [
        # Match currency symbols/codes followed by amount
        r'(?:USD|US\$|\$|EUR|€|GBP|£)\s*([\d,]+(?:\.\d{2})?)',
        # Match amount followed by currency
        r'([\d,]+(?:\.\d{2})?)\s*(?:USD|US\$|\$|EUR|€|GBP|£)',
        # Match amount with million/billion
        r'(?:USD|US\$|\$|EUR|€|GBP|£)?\s*([\d,]+(?:\.\d{2})?)\s*(?:million|billion|M|B)'
    ]
    
    for pattern in amount_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            amount = Decimal(amount_str)
            
            # Handle million/billion
            if 'billion' in match.group().lower() or 'B' in match.group():
                amount *= 1000000000
            elif 'million' in match.group().lower() or 'M' in match.group():
                amount *= 1000000
                
            # Determine currency
            currency = currency_hint or 'USD'  # Default to USD for UN tenders
            if '€' in match.group() or 'EUR' in match.group().upper():
                currency = 'EUR'
            elif '£' in match.group() or 'GBP' in match.group().upper():
                currency = 'GBP'
                
            return amount, currency
            
    return None, None

def normalize_document_links_ungm(ungm_obj: UNGMTender) -> List[Dict[str, str]]:
    """
    Enhanced document link normalization for UNGM tenders.
    
    Args:
        ungm_obj: UNGM tender object
        
    Returns:
        List of normalized document links
    """
    document_links = []
    
    # Process main documents
    if ungm_obj.documents and isinstance(ungm_obj.documents, dict):
        if 'documents' in ungm_obj.documents:
            docs = ungm_obj.documents['documents']
            if isinstance(docs, list):
                for doc in docs:
                    if isinstance(doc, dict) and 'url' in doc:
                        doc_info = {
                            'url': doc['url'],
                            'type': doc.get('type', 'attachment'),
                            'language': doc.get('language', 'en'),
                            'description': doc.get('description') or doc.get('title', 'Document')
                        }
                        document_links.append(doc_info)
    
    # Process links field
    if ungm_obj.links and isinstance(ungm_obj.links, dict):
        # Check various URL fields
        url_fields = ['self', 'notice', 'tender', 'details', 'href', 'url']
        for field in url_fields:
            if field in ungm_obj.links and ungm_obj.links[field]:
                url = ungm_obj.links[field]
                if url and not any(d['url'] == url for d in document_links):
                    document_links.append({
                        'url': url,
                        'type': 'main_notice',
                        'language': 'en',
                        'description': 'Main tender notice'
                    })
                    break
        
        # Check items list
        if 'items' in ungm_obj.links and isinstance(ungm_obj.links['items'], list):
            for item in ungm_obj.links['items']:
                if isinstance(item, dict):
                    url = item.get('href') or item.get('url')
                    if url and not any(d['url'] == url for d in document_links):
                        document_links.append({
                            'url': url,
                            'type': item.get('type', 'related'),
                            'language': item.get('language', 'en'),
                            'description': item.get('description', 'Related document')
                        })
    
    # Add generic UNGM URL if we have a reference number
    if ungm_obj.reference:
        generic_url = f"https://www.ungm.org/Public/Notice/{ungm_obj.reference}"
        if not any(d['url'] == generic_url for d in document_links):
            document_links.append({
                'url': generic_url,
                'type': 'source',
                'language': 'en',
                'description': 'Source tender notice'
            })
    
    return document_links

class UNGMNormalizer(BaseNormalizer):
    """
    Enhanced UNGM tender normalizer implementing the base normalizer interface.
    """
    
    def __init__(self):
        super().__init__('ungm')

    def _normalize_text_field(self, field_name: str, value: Optional[str]) -> str:
        """
        Normalize a text field by cleaning and validating it.
        
        Args:
            field_name: Name of the field being normalized
            value: Text value to normalize
            
        Returns:
            Normalized text value with proper encoding and sanitized content
        """
        if not value:
            self.logger.warning(f"Empty {field_name} field")
            return ""
            
        # Clean up text
        clean_value = value.strip()
        
        # Check for encoding issues
        if detect_encoding_issues(clean_value):
            self.logger.warning(f"Possible encoding issues in {field_name}: {clean_value}")
            # Try to fix encoding issues
            clean_value = normalize_text(clean_value)
            
        # Log the normalization
        log_before_after(field_name, value, clean_value)
        
        return clean_value
        
    def _validate_input(self, data: Dict[str, Any]) -> bool:
        """
        Validate UNGM tender data with enhanced error checking.
        """
        if not isinstance(data, dict):
            self.logger.error("Input data must be a dictionary")
            return False
            
        required_fields = ['id', 'title']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            self.logger.error(f"Missing required fields: {', '.join(missing_fields)}")
            return False
            
        # Validate field types
        field_types = {
            'id': (int, str),
            'title': str,
            'description': str,
            'status': str,
            'published_on': (str, datetime),
            'deadline_on': (str, datetime)
        }
        
        for field, expected_types in field_types.items():
            value = data.get(field)
            if value is not None:
                if not isinstance(value, expected_types):
                    self.logger.error(
                        f"Invalid type for field '{field}': expected {expected_types}, got {type(value)}"
                    )
                    return False
        
        return True

    def _extract_required_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract required fields from UNGM tender data with enhanced validation.
        """
        try:
            # Pre-process JSON fields
            processed_data = self._preprocess_json_fields(data)
            
            # Log original values
            for field in ['title', 'description', 'status']:
                log_before_after(field, data.get(field), processed_data.get(field))
            
            # Validate with Pydantic
            try:
                ungm_obj = UNGMTender(**processed_data)
            except Exception as e:
                self.logger.error(f"Failed to validate UNGM tender: {e}")
                raise ValueError(f"Failed to validate UNGM tender: {e}")
            
            # Extract and normalize text fields
            title = self._normalize_text_field('title', ungm_obj.title)
            description = self._normalize_text_field('description', ungm_obj.description)
            
            # Extract and validate dates
            publication_date = self._extract_date('publication_date', ungm_obj.published_on)
            deadline_date = self._extract_date('deadline_date', ungm_obj.deadline_on)
            
            # Process contact information
            contact_info = self._process_contact_info(ungm_obj.contacts)
            
            # Process document links
            document_links = self._process_document_links(ungm_obj.documents)
            
            # Extract countries
            countries = self._extract_countries(ungm_obj)
            
            return {
                'title': title,
                'source_id': str(ungm_obj.id),
                'description': description,
                'status': ungm_obj.status,
                'publication_date': publication_date,
                'deadline_date': deadline_date,
                'reference_number': ungm_obj.reference,
                'contact_info': contact_info,
                'documents': document_links,
                'links': ungm_obj.links,
                'countries': countries
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting required fields: {str(e)}", exc_info=True)
            raise

    def _preprocess_json_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pre-process JSON fields in UNGM data with enhanced error handling.
        """
        processed = data.copy()
        
        json_fields = [
            'links', 'unspscs', 'revisions', 'documents', 
            'contacts', 'sustainability', 'countries'
        ]
        
        for field in json_fields:
            try:
                value = processed.get(field)
                if value is None:
                    continue
                    
                if isinstance(value, str):
                    if value.strip():
                        try:
                            parsed = json.loads(value)
                            if isinstance(parsed, list):
                                processed[field] = {'items': parsed}
                            else:
                                processed[field] = parsed
                        except json.JSONDecodeError as e:
                            self.logger.warning(f"Failed to parse JSON for field '{field}': {str(e)}")
                            processed[field] = None
                    else:
                        processed[field] = None
                elif isinstance(value, list):
                    processed[field] = {'items': value}
                    
            except Exception as e:
                self.logger.error(f"Error processing field '{field}': {str(e)}")
                processed[field] = None
                
        return processed

    def _process_contact_info(self, contacts: Any) -> Dict[str, Any]:
        """
        Process contact information with validation.
        """
        if not contacts:
            return {}
            
        try:
            if isinstance(contacts, str):
                try:
                    contacts = json.loads(contacts)
                except json.JSONDecodeError:
                    return {}
                    
            if isinstance(contacts, dict):
                # Normalize contact fields
                normalized = {}
                for key, value in contacts.items():
                    if value:
                        normalized[key] = normalize_text(str(value))
                return normalized
                
            if isinstance(contacts, list):
                # Take first contact if list
                if contacts and isinstance(contacts[0], dict):
                    return self._process_contact_info(contacts[0])
                    
            return {}
            
        except Exception as e:
            self.logger.warning(f"Error processing contact info: {str(e)}")
            return {}

    def _extract_countries(self, ungm_obj: UNGMTender) -> List[str]:
        """
        Extract and validate country information.
        """
        countries = set()
        
        try:
            # Check beneficiary countries
            if ungm_obj.beneficiary_countries:
                if isinstance(ungm_obj.beneficiary_countries, list):
                    for country in ungm_obj.beneficiary_countries:
                        if isinstance(country, str):
                            normalized = normalize_text(country)
                            if normalized:
                                countries.add(normalized)
                                
            # Check countries field
            if ungm_obj.countries:
                if isinstance(ungm_obj.countries, list):
                    for country in ungm_obj.countries:
                        if isinstance(country, str):
                            normalized = normalize_text(country)
                            if normalized:
                                countries.add(normalized)
                elif isinstance(ungm_obj.countries, dict):
                    for country in ungm_obj.countries.get('items', []):
                        if isinstance(country, str):
                            normalized = normalize_text(country)
                            if normalized:
                                countries.add(normalized)
                                
        except Exception as e:
            self.logger.warning(f"Error extracting countries: {str(e)}")
            
        return list(countries)

    def _post_process(self, tender: UnifiedTender) -> UnifiedTender:
        """
        Perform UNGM-specific post-processing with enhanced validation.
        """
        try:
            # Handle translations if needed
            if tender.language and tender.language != 'en':
                try:
                    if tender.title:
                        original_title = tender.title
                        tender.title_english, quality = translate_to_english(tender.title, tender.language)
                        log_before_after('title_translation', original_title, tender.title_english)
                        
                    if tender.description:
                        original_desc = tender.description
                        tender.description_english, quality = translate_to_english(tender.description, tender.language)
                        log_before_after('description_translation', original_desc, tender.description_english)
                        
                    if tender.organization_name:
                        original_org = tender.organization_name
                        tender.organization_name_english, quality = translate_to_english(tender.organization_name, tender.language)
                        log_before_after('organization_translation', original_org, tender.organization_name_english)
                        
                except Exception as e:
                    self.logger.warning(f"Translation error: {str(e)}")
            
            # Calculate quality score
            tender.quality_score = calculate_tender_quality(tender.dict())
            
            return tender
            
        except Exception as e:
            self.logger.error(f"Error in post-processing: {str(e)}")
            return tender

def normalize_ungm(row: Dict[str, Any]) -> UnifiedTender:
    """
    Legacy wrapper function for backward compatibility.
    """
    normalizer = UNGMNormalizer()
    return normalizer.normalize(row) 