import json
import re
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional

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
    extract_procurement_method,
    extract_status,
    ensure_country,
)

# Get logger
logger = logging.getLogger(__name__)

def normalize_aiib(row: Dict[str, Any]) -> UnifiedTender:
    """
    Normalize an AIIB (Asian Infrastructure Investment Bank) tender record.
    
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
            raise ValueError(f"Failed to validate AIIB tender: {e}")

        # Parse date string if present
        publication_dt = None
        if aiib_obj.date:
            try:
                # Try different date formats
                date_formats = [
                    "%Y-%m-%d",
                    "%d/%m/%Y",
                    "%m/%d/%Y",
                    "%B %d, %Y",  # e.g. "January 15, 2023"
                    "%d %B %Y",   # e.g. "15 January 2023"
                ]
                
                for fmt in date_formats:
                    try:
                        publication_dt = datetime.strptime(aiib_obj.date, fmt)
                        break
                    except ValueError:
                        continue
            except Exception as e:
                logger.warning(f"Failed to parse date: {aiib_obj.date}. Error: {e}")
                # If all parsing attempts fail, leave as None
                pass

        # Use project_notice as the title if available, otherwise use a placeholder
        title = aiib_obj.project_notice or f"AIIB Tender - {aiib_obj.id}"
        
        # Detect language - MOVED UP before country extraction
        language = "en"  # Default for AIIB
        if aiib_obj.pdf_content:
            try:
                detected = detect_language(aiib_obj.pdf_content)
                if detected:
                    language = detected
                logger.info(f"Detected language: {language}")
            except Exception as e:
                logger.warning(f"Language detection failed: {e}")
        
        # Extract status from text or dates
        status = None
        if aiib_obj.type:
            status = extract_status(status_text=aiib_obj.type)
        
        # Try to extract status from description if not found
        if not status and aiib_obj.pdf_content:
            status = extract_status(description=aiib_obj.pdf_content)
        
        # Try to extract organization name from description
        organization_name = None
        if aiib_obj.pdf_content:
            organization_name = extract_organization(aiib_obj.pdf_content)
        
        # Try to extract financial information
        estimated_value = None
        currency = None
        if aiib_obj.pdf_content:
            estimated_value, currency = extract_financial_info(aiib_obj.pdf_content)
        
        # DEBUG: Add traceback logging to identify the source of the error
        logger.info("Starting country extraction process...")
        
        # Try to extract country and city - COMPLETELY REWRITTEN for safety
        country_string = None  # This will hold our final string value for country
        city = None
        
        # DEBUG: Member data
        logger.info(f"Member value: {aiib_obj.member}, Type: {type(aiib_obj.member).__name__}")
        
        # First try to get country from member field - with strict type checking
        if aiib_obj.member and isinstance(aiib_obj.member, str) and aiib_obj.member.strip():
            country_string = aiib_obj.member.strip()
            logger.info(f"Extracted country from member field: {country_string}")
        
        # If no country from member field, try to extract from content
        if not country_string and aiib_obj.pdf_content and isinstance(aiib_obj.pdf_content, str):
            try:
                # Extract location info safely
                logger.info("Attempting to extract location from PDF content...")
                location_tuple = extract_location_info(aiib_obj.pdf_content)
                logger.info(f"Location tuple: {location_tuple}, Type: {type(location_tuple).__name__}")
                
                # Properly unpack the tuple with type checking
                if isinstance(location_tuple, tuple) and len(location_tuple) >= 2:
                    extracted_country, extracted_city = location_tuple
                    logger.info(f"Unpacked tuple - Country: {extracted_country}, Type: {type(extracted_country).__name__}, City: {extracted_city}, Type: {type(extracted_city).__name__}")
                    
                    # Verify extracted country is a valid string
                    if extracted_country and isinstance(extracted_country, str) and extracted_country.strip():
                        country_string = extracted_country.strip()
                        logger.info(f"Set country_string to: {country_string}")
                    
                    # Verify extracted city is a valid string
                    if extracted_city and isinstance(extracted_city, str) and extracted_city.strip():
                        city = extracted_city.strip()
                        logger.info(f"Set city to: {city}")
            except Exception as e:
                # If extraction fails, keep country_string as None
                logger.error(f"Location extraction failed: {e}")
                logger.error(traceback.format_exc())
                pass
        
        logger.info(f"Final country_string before ensure_country: {country_string}, Type: {type(country_string).__name__ if country_string is not None else 'None'}")
        
        # DEBUG: Print all parameters being passed to ensure_country
        logger.info(f"ensure_country parameters:")
        logger.info(f"- country: {country_string}, Type: {type(country_string).__name__ if country_string is not None else 'None'}")
        logger.info(f"- text: {aiib_obj.pdf_content[:100] if aiib_obj.pdf_content and isinstance(aiib_obj.pdf_content, str) else None}..., Type: {type(aiib_obj.pdf_content).__name__ if aiib_obj.pdf_content is not None else 'None'}")
        logger.info(f"- organization: {organization_name}, Type: {type(organization_name).__name__ if organization_name is not None else 'None'}")
        logger.info(f"- language: {language}, Type: {type(language).__name__ if language is not None else 'None'}")
        
        # Ensure we have a country value using our fallback mechanisms
        # ONLY pass a string to ensure_country, never a tuple
        try:
            country = ensure_country(
                country=country_string,  # Now guaranteed to be None or a valid string
                text=aiib_obj.pdf_content if isinstance(aiib_obj.pdf_content, str) else None,
                organization=organization_name,
                email=None,  # We don't have email in AIIB data
                language=language
            )
            logger.info(f"ensure_country returned: {country}")
        except Exception as e:
            logger.error(f"ensure_country failed with error: {e}")
            logger.error(traceback.format_exc())
            # Fall back to a safe value
            country = "Unknown"
        
        # Extract procurement method
        procurement_method = None
        if aiib_obj.type:
            procurement_method = extract_procurement_method(aiib_obj.type)
        
        if not procurement_method and aiib_obj.pdf_content:
            procurement_method = extract_procurement_method(aiib_obj.pdf_content)
            
        # Extract document links if available
        document_links = []
        if "pdf" in row and row["pdf"]:
            pdf_url = row["pdf"]
            document_links = normalize_document_links(pdf_url)
        
        # Construct the UnifiedTender
        unified = UnifiedTender(
            # Required fields
            title=title,
            source_table="aiib",
            source_id=str(aiib_obj.id),
            
            # Additional fields
            description=aiib_obj.pdf_content,  # Using PDF content as description
            tender_type=aiib_obj.type,
            status=status,
            publication_date=publication_dt,
            country=country,
            city=city,
            organization_name=organization_name,
            sector=aiib_obj.sector,
            estimated_value=estimated_value,
            currency=currency,
            document_links=document_links,
            procurement_method=procurement_method,
            language=language,
            original_data=row,
            normalized_method="offline-dictionary",
        )

        # Use the common apply_translations function for all fields
        unified = apply_translations(unified, language)
        
        logger.info(f"AIIB normalization completed successfully for row ID: {row.get('id', 'unknown')}")
        return unified
    
    except Exception as e:
        logger.error(f"AIIB normalization failed with error: {e}")
        logger.error(traceback.format_exc())
        raise 