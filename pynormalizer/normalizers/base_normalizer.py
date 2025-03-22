import logging
from typing import Dict, Any, Optional
from datetime import datetime
from abc import ABC, abstractmethod

from pynormalizer.models.unified_model import UnifiedTender
from pynormalizer.utils.normalizer_helpers import (
    extract_financial_info,
    extract_organization_info,
    normalize_document_links,
    determine_status,
    parse_date_string,
    extract_location_info,
    safe_get_value,
    log_normalization_error
)

logger = logging.getLogger(__name__)

class BaseNormalizer(ABC):
    """
    Base class for all tender normalizers implementing common functionality.
    """
    
    def __init__(self, source: str):
        self.source = source
        self.logger = logging.getLogger(f"{__name__}.{source}")

    @abstractmethod
    def _validate_input(self, data: Dict[str, Any]) -> bool:
        """
        Validate input data before normalization.
        Must be implemented by child classes.
        """
        pass

    @abstractmethod
    def _extract_required_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract required fields from input data.
        Must be implemented by child classes.
        """
        pass

    def normalize(self, data: Dict[str, Any]) -> UnifiedTender:
        """
        Main normalization method with consistent error handling.
        """
        try:
            # Validate input
            if not self._validate_input(data):
                raise ValueError("Invalid input data")

            # Extract required fields
            required_fields = self._extract_required_fields(data)
            
            # Extract dates
            publication_date = parse_date_string(safe_get_value(data, 'publication_date'))
            deadline_date = parse_date_string(safe_get_value(data, 'deadline_date'))
            
            # Extract organization info
            organization_name, buyer = extract_organization_info(
                text=required_fields.get('title', ''),
                contact_info=safe_get_value(data, 'contact_info'),
                org_field=safe_get_value(data, 'organization')
            )
            
            # Extract location info
            country, state, city = extract_location_info(
                text=required_fields.get('description', ''),
                country_hint=safe_get_value(data, 'country')
            )
            
            # Extract financial info
            min_value, max_value, currency = extract_financial_info(
                text=required_fields.get('description', ''),
                currency_hint=safe_get_value(data, 'currency')
            )
            
            # Process document links
            document_links = normalize_document_links(
                safe_get_value(data, 'documents', []),
                base_url=safe_get_value(data, 'base_url')
            )
            
            # Determine status
            status = determine_status(
                status_text=safe_get_value(data, 'status'),
                publication_date=publication_date,
                deadline_date=deadline_date
            )
            
            # Create unified tender
            unified = UnifiedTender(
                # Required fields
                title=required_fields['title'],
                source_table=self.source,
                source_id=required_fields['source_id'],
                
                # Optional fields with defaults
                description=required_fields.get('description'),
                status=status,
                publication_date=publication_date,
                deadline_date=deadline_date,
                country=country,
                state=state,
                city=city,
                organization_name=organization_name,
                buyer=buyer,
                reference_number=safe_get_value(data, 'reference_number'),
                contact_name=safe_get_value(data, 'contact_name'),
                contact_email=safe_get_value(data, 'contact_email'),
                contact_phone=safe_get_value(data, 'contact_phone'),
                contact_address=safe_get_value(data, 'contact_address'),
                document_links=document_links,
                estimated_value=min_value,
                estimated_value_max=max_value,
                currency=currency,
                procurement_method=safe_get_value(data, 'procurement_method'),
                language=safe_get_value(data, 'language', 'en'),
                original_data=data,
                normalized_method=f"{self.source}_normalizer"
            )
            
            # Allow child classes to perform additional processing
            unified = self._post_process(unified)
            
            return unified
            
        except Exception as e:
            log_normalization_error(
                source=self.source,
                tender_id=str(safe_get_value(data, 'id', 'unknown')),
                error=e,
                context={'data': data}
            )
            
            # Return minimal tender with error info
            return UnifiedTender(
                title="Normalization Error",
                source_table=self.source,
                source_id=str(safe_get_value(data, 'id', 'unknown')),
                fallback_reason=f"Normalization error: {str(e)}",
                original_data=data
            )

    def _post_process(self, tender: UnifiedTender) -> UnifiedTender:
        """
        Hook for child classes to perform additional processing.
        Default implementation returns tender as is.
        """
        return tender

    def _safe_extract(self, data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """
        Safely extract value from nested dictionary.
        """
        return safe_get_value(data, key, default)

    def _get_nested_value(self, data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
        """
        Get value from nested dictionary using multiple keys.
        """
        current = data
        for key in keys:
            if not isinstance(current, dict):
                return default
            current = current.get(key, default)
            if current is None:
                return default
        return current 