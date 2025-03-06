from datetime import datetime
import uuid
import re
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
import traceback

from pynormalizer.models.source_models import WBTender
from pynormalizer.models.unified_model import UnifiedTender
from pynormalizer.utils.translation import (
    translate_to_english, detect_language, apply_translations
)
from pynormalizer.utils.normalizer_helpers import (
    normalize_document_links,
    extract_financial_info,
    extract_location_info,
    extract_procurement_method,
    extract_organization,
    extract_organization_and_buyer,
    extract_status,
    extract_sector_info,
    parse_date_string,
    ensure_country,
    standardize_status
)

# Initialize logger
logger = logging.getLogger(__name__)

def normalize_wb(row: Dict[str, Any]) -> UnifiedTender:
    """
    Normalize a World Bank tender record.
    
    Args:
        row: Dictionary containing World Bank tender data
        
    Returns:
        Normalized UnifiedTender instance
    """
    # Handle document_links if it's a string (sometimes it is)
    if "document_links" in row and isinstance(row["document_links"], str):
        # Try to parse as JSON if it starts with [ or {
        if row["document_links"].strip().startswith(("[", "{")):
            try:
                row["document_links"] = json.loads(row["document_links"])
            except json.JSONDecodeError:
                # If it fails to parse, just keep it as a string
                pass
        # If it's a URL string that starts with http or www, make it a list with a dict
        elif row["document_links"].strip().startswith(("http", "www")):
            row["document_links"] = [{"link": row["document_links"]}]
    
    # Validate with Pydantic
    try:
        wb_obj = WBTender(**row)
    except Exception as e:
        raise ValueError(f"Failed to validate World Bank tender: {e}")
    
    # Detect language - default for World Bank is English
    language = "en"
    
    # Safely check for title and description
    if hasattr(wb_obj, 'title') and wb_obj.title:
        detected = detect_language(wb_obj.title)
        if detected and detected != "en":
            language = detected
    
    if language == "en" and hasattr(wb_obj, 'description') and wb_obj.description:
        detected = detect_language(wb_obj.description)
        if detected and detected != "en":
            language = detected
    
    # Extract procurement method
    procurement_method = None
    
    # Try from tender_type first
    if hasattr(wb_obj, 'tender_type') and wb_obj.tender_type:
        procurement_method = extract_procurement_method(wb_obj.tender_type)
    
    # Try from procurement_method_code if available
    if not procurement_method and hasattr(wb_obj, 'procurement_method_code') and wb_obj.procurement_method_code:
        # Map World Bank procurement method codes to descriptions
        procurement_map = {
            "CQS": "Consultant's Qualifications Based Selection",
            "QCBS": "Quality and Cost-Based Selection",
            "LCS": "Least-Cost Selection",
            "FBS": "Fixed Budget Selection",
            "SSS": "Single-Source Selection",
            "ICB": "International Competitive Bidding",
            "NCB": "National Competitive Bidding",
            "DC": "Direct Contracting",
            "SHOP": "Shopping",
            "QBS": "Quality-Based Selection",
            "OPN": "Open Tender",
            "LIB": "Limited International Bidding",
            "IC": "Individual Consultants"
        }
        proc_code = wb_obj.procurement_method_code.upper()
        procurement_method = procurement_map.get(proc_code, proc_code)
    
    # Try from description if still not found
    if not procurement_method and hasattr(wb_obj, 'description') and wb_obj.description:
        procurement_method = extract_procurement_method(wb_obj.description)
    
    # Determine status with enhanced logic
    status = None
    
    # First check if status is explicitly set
    if hasattr(wb_obj, 'status') and wb_obj.status:
        status = wb_obj.status
    # Check tender_type/notice_type for clues about status
    elif hasattr(wb_obj, 'notice_type') and wb_obj.notice_type:
        notice_type_lower = wb_obj.notice_type.lower()
        
        if "award" in notice_type_lower or "awarded" in notice_type_lower:
            status = "Awarded"
        elif "contract" in notice_type_lower:
            status = "Contract Award"
    
    # Use deadline_date to determine if tender is open or closed
    deadline_dt = None
    if hasattr(wb_obj, 'deadline_date') and wb_obj.deadline_date:
        if isinstance(wb_obj.deadline_date, datetime):
            deadline_dt = wb_obj.deadline_date
        elif isinstance(wb_obj.deadline_date, str):
            try:
                # Try parsing common date formats
                deadline_dt = datetime.fromisoformat(wb_obj.deadline_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                try:
                    # Try with different format
                    deadline_dt = datetime.strptime(wb_obj.deadline_date, "%Y-%m-%d")
                except ValueError:
                    # Try additional date formats
                    date_formats = [
                        "%Y-%m-%dT%H:%M:%S",
                        "%Y-%m-%dT%H:%M:%S.%f",
                        "%Y/%m/%d",
                        "%d/%m/%Y",
                        "%d-%m-%Y",
                        "%d %b %Y",
                        "%d-%b-%Y",
                        "%B %d, %Y",
                        "%d %B %Y"
                    ]
                    for fmt in date_formats:
                        try:
                            deadline_dt = datetime.strptime(wb_obj.deadline_date, fmt)
                            break
                        except ValueError:
                            continue
    
    # Also parse publication_date with enhanced formats
    publication_dt = None
    if hasattr(wb_obj, 'publication_date') and wb_obj.publication_date:
        if isinstance(wb_obj.publication_date, datetime):
            publication_dt = wb_obj.publication_date
        elif isinstance(wb_obj.publication_date, str):
            try:
                # Try parsing common date formats
                publication_dt = datetime.fromisoformat(wb_obj.publication_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                try:
                    # Try with different format
                    publication_dt = datetime.strptime(wb_obj.publication_date, "%Y-%m-%d")
                except ValueError:
                    # Try additional date formats
                    date_formats = [
                        "%Y-%m-%dT%H:%M:%S",
                        "%Y-%m-%dT%H:%M:%S.%f",
                        "%Y/%m/%d",
                        "%d/%m/%Y",
                        "%d-%m-%Y",
                        "%d %b %Y",
                        "%d-%b-%Y",
                        "%B %d, %Y",
                        "%d %B %Y"
                    ]
                    for fmt in date_formats:
                        try:
                            publication_dt = datetime.strptime(wb_obj.publication_date, fmt)
                            break
                        except ValueError:
                            continue
    
    # Set status based on deadline if available and status still not determined
    if not status and deadline_dt:
        current_dt = datetime.now()
        if current_dt > deadline_dt:
            status = "Closed"
        else:
            status = "Open"
    
    # If still no status, try to extract from description
    if not status and hasattr(wb_obj, 'description') and wb_obj.description:
        extracted_status = extract_status(description=wb_obj.description)
        if extracted_status:
            status = extracted_status
    
    # Default to "Active" if we have a publication date
    if not status and hasattr(wb_obj, 'publication_date') and wb_obj.publication_date:
        status = "Active"
    
    # Extract country and city - try direct attributes first
    country_value = None
    city = None
    
    # First try to get country from direct attributes
    if hasattr(wb_obj, 'country') and wb_obj.country and isinstance(wb_obj.country, str) and wb_obj.country.strip():
        country_value = wb_obj.country.strip()
    elif hasattr(wb_obj, 'project_ctry_name') and wb_obj.project_ctry_name and isinstance(wb_obj.project_ctry_name, str) and wb_obj.project_ctry_name.strip():
        country_value = wb_obj.project_ctry_name.strip()
    
    # Get city if available
    if hasattr(wb_obj, 'city') and wb_obj.city and isinstance(wb_obj.city, str) and wb_obj.city.strip():
        city = wb_obj.city.strip()
    
    # Try to extract from contact_address if available
    if (not country_value or not city) and hasattr(wb_obj, 'contact_address') and wb_obj.contact_address:
        try:
            extracted_location = extract_location_info(wb_obj.contact_address)
            if extracted_location and isinstance(extracted_location, tuple) and len(extracted_location) > 1:
                extracted_country, extracted_city = extracted_location
                # Only use extracted country if it's a valid string and we don't already have one
                if not country_value and extracted_country and isinstance(extracted_country, str) and extracted_country.strip():
                    country_value = extracted_country.strip()
                # Only use extracted city if it's a valid string and we don't already have one
                if not city and extracted_city and isinstance(extracted_city, str) and extracted_city.strip():
                    city = extracted_city.strip()
        except Exception:
            # If extraction fails, continue with other methods
            pass
    
    # If still no country or city, try to extract from description
    if (not country_value or not city) and hasattr(wb_obj, 'description') and wb_obj.description:
        try:
            extracted_location = extract_location_info(wb_obj.description)
            if extracted_location and isinstance(extracted_location, tuple) and len(extracted_location) > 1:
                extracted_country, extracted_city = extracted_location
                # Only use extracted country if it's a valid string and we don't already have one
                if not country_value and extracted_country and isinstance(extracted_country, str) and extracted_country.strip():
                    country_value = extracted_country.strip()
                # Only use extracted city if it's a valid string and we don't already have one
                if not city and extracted_city and isinstance(extracted_city, str) and extracted_city.strip():
                    city = extracted_city.strip()
        except Exception:
            # If extraction fails, continue with other methods
            pass
    
    # Extract organization name
    organization_name = None
    
    if hasattr(wb_obj, 'organization_name') and wb_obj.organization_name:
        organization_name = wb_obj.organization_name
    elif hasattr(wb_obj, 'buyer') and wb_obj.buyer:
        organization_name = wb_obj.buyer
    
    # Try to extract from contact_organization if still not found
    if not organization_name and hasattr(wb_obj, 'contact_organization') and wb_obj.contact_organization:
        organization_name = wb_obj.contact_organization
    
    # Try to extract from original_data's nested fields
    if not organization_name and hasattr(wb_obj, 'original_data') and wb_obj.original_data:
        original = wb_obj.original_data
        if isinstance(original, dict):
            # Check for project_name field
            if not organization_name and 'project_name' in original and original['project_name']:
                organization_name = original['project_name']
            # Try contact_organization
            if not organization_name and 'contact_organization' in original and original['contact_organization']:
                organization_name = original['contact_organization']
        elif isinstance(original, str):
            try:
                original_dict = json.loads(original)
                if isinstance(original_dict, dict):
                    if not organization_name and 'project_name' in original_dict and original_dict['project_name']:
                        organization_name = original_dict['project_name']
                    if not organization_name and 'contact_organization' in original_dict and original_dict['contact_organization']:
                        organization_name = original_dict['contact_organization']
            except json.JSONDecodeError:
                pass
    
    # Try to extract from description if still not found
    if not organization_name and hasattr(wb_obj, 'description') and wb_obj.description:
        extracted_org = extract_organization(wb_obj.description)
        if extracted_org:
            organization_name = extracted_org
    
    # Extract financial information
    estimated_value = None
    currency = None
    
    # Try direct fields first
    if hasattr(wb_obj, 'estimated_value') and wb_obj.estimated_value:
        if isinstance(wb_obj.estimated_value, (int, float)):
            estimated_value = float(wb_obj.estimated_value)
        elif isinstance(wb_obj.estimated_value, str):
            try:
                # Remove commas and convert to float
                estimated_value = float(wb_obj.estimated_value.replace(',', ''))
            except (ValueError, TypeError):
                pass
    
    if hasattr(wb_obj, 'currency') and wb_obj.currency:
        currency = wb_obj.currency
    
    # Try to extract from description if not found directly
    if (not estimated_value or not currency) and hasattr(wb_obj, 'description') and wb_obj.description:
        extracted_value, extracted_curr = extract_financial_info(wb_obj.description)
        if not estimated_value and extracted_value:
            estimated_value = extracted_value
        if not currency and extracted_curr:
            currency = extracted_curr
    
    # Extract document links
    document_links = None
    
    # Process document_links if available
    if hasattr(wb_obj, 'document_links') and wb_obj.document_links:
        document_links = normalize_document_links(wb_obj.document_links)
    
    # Add URL as a document link if available and not already in document_links
    if hasattr(wb_obj, 'url') and wb_obj.url:
        url_already_included = False
        if document_links:
            for link in document_links:
                if isinstance(link, dict) and link.get('url') == wb_obj.url:
                    url_already_included = True
                    break
        
        if not url_already_included:
            document_links.append({
                "url": wb_obj.url, 
                "type": "unknown", 
                "language": language,
                "description": "Main tender notice"
            })
    
    # Extract title and description
    title = getattr(wb_obj, 'title', None)
    description = getattr(wb_obj, 'description', None)
    
    # Translate fields if needed
    title_english = None
    description_english = None
    organization_name_english = None
    buyer_english = None
    project_name_english = None
    
    # Translate title to English if not already in English
    if title:
        title_english, title_method = translate_to_english(title, language)
    
    # Translate description to English if not already in English
    if description:
        description_english, desc_method = translate_to_english(description, language)
    
    # Translate organization name to English if not already in English
    if organization_name:
        organization_name_english, org_method = translate_to_english(organization_name, language)
    
    # Translate buyer to English if not already in English and different from organization_name
    buyer = getattr(wb_obj, 'buyer', None)
    if buyer and buyer != organization_name:
        buyer_english, buyer_method = translate_to_english(buyer, language)
    
    # Translate project name to English if not already in English
    project_name = getattr(wb_obj, 'project_name', None)
    if project_name:
        project_name_english, project_method = translate_to_english(project_name, language)
    
    # Extract project information
    project_name = None
    project_id = None
    project_number = None
    
    # Try direct fields first
    if hasattr(wb_obj, 'project_name') and wb_obj.project_name:
        project_name = wb_obj.project_name
    if hasattr(wb_obj, 'project_id') and wb_obj.project_id:
        project_id = wb_obj.project_id
    if hasattr(wb_obj, 'project_number') and wb_obj.project_number:
        project_number = wb_obj.project_number
    
    # Try to extract from original_data
    if (not project_name or not project_id) and hasattr(wb_obj, 'original_data') and wb_obj.original_data:
        original = wb_obj.original_data
        if isinstance(original, dict):
            if not project_name and 'project_name' in original and original['project_name']:
                project_name = original['project_name']
            if not project_id and 'project_id' in original and original['project_id']:
                project_id = original['project_id']
        elif isinstance(original, str):
            try:
                original_dict = json.loads(original)
                if isinstance(original_dict, dict):
                    if not project_name and 'project_name' in original_dict and original_dict['project_name']:
                        project_name = original_dict['project_name']
                    if not project_id and 'project_id' in original_dict and original_dict['project_id']:
                        project_id = original_dict['project_id']
            except json.JSONDecodeError:
                pass
    
    # Try to extract from description
    if (not project_name or not project_id) and hasattr(wb_obj, 'description') and wb_obj.description:
        # Extract Project ID patterns like "P123456" or "Project: P123456"
        if not project_id:
            # Try different patterns for project IDs
            project_id_patterns = [
                r'Project(?:\s*:\s*|\s+)([Pp]\d{6})',
                r'Project ID(?:\s*:\s*|\s+)([Pp]\d{6})',
                r'Project No\.?(?:\s*:\s*|\s+)([Pp]\d{6})',
                r'(?:^|\s)([Pp]\d{6})(?:\s|$)'  # Standalone P-number
            ]
            
            for pattern in project_id_patterns:
                project_id_match = re.search(pattern, wb_obj.description)
                if project_id_match:
                    project_id = project_id_match.group(1)
                    break
        
        # Extract project name patterns like "Project Name: Example Project" or similar
        if not project_name:
            project_name_patterns = [
                r'Project(?:\s*:\s*|\s+)([^:]+?)(?:\s+Project|\s+Loan|\s+Credit|\s+Reference|$)',
                r'(?:for|under)\s+the\s+([^.]+?)\s+(?:Project|Program)',
                r'Project Name(?:\s*:\s*|\s+)([^.]+?)(?:\.|$)'
            ]
            
            for pattern in project_name_patterns:
                try:
                    project_name_match = re.search(pattern, wb_obj.description)
                    if project_name_match:
                        potential_name = project_name_match.group(1).strip()
                        # Ensure it's not just a project ID
                        if len(potential_name) > 7 and not re.match(r'^[Pp]\d{6}$', potential_name):
                            project_name = potential_name
                            break
                except Exception as e:
                    logger.warning(f"Error extracting project name: {e}")
            
            # If still no project name, try to extract from title
            if not project_name and wb_obj.title:
                # The title often contains the project name
                title_parts = wb_obj.title.split(" - ")
                if len(title_parts) > 1:
                    # If title has format "Action - Project Name", the project name is usually after the dash
                    project_name = title_parts[1].strip()
                elif "Project" in wb_obj.title:
                    # Try to extract project name based on the word "Project"
                    title_project_match = re.search(r'([^:]+?)\s+Project', wb_obj.title)
                    if title_project_match:
                        project_name = title_project_match.group(1).strip()
    
    # For contract awards, extract deadline from description if not available in object
    if hasattr(wb_obj, 'notice_type') and wb_obj.notice_type and 'Award' in wb_obj.notice_type and not deadline_dt and wb_obj.description:
        # Try to extract deadline from description text
        deadline_match = re.search(r'(?:Deadline|Due Date|Closing Date)[:;]?\s*(\d{1,2}[\s\-/\.]+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\-/\.]+\d{4}|\d{4}[\s\-/\.]+\d{1,2}[\s\-/\.]+\d{1,2})', wb_obj.description, re.IGNORECASE)
        if deadline_match:
            deadline_text = deadline_match.group(1).strip()
            try:
                deadline_dt = parse_date_string(deadline_text)
            except Exception as e:
                logger.warning(f"Failed to parse deadline date '{deadline_text}': {e}")
    
    # If we have a project ID but no project name, try to create a generic project name
    if project_id and not project_name:
        project_name = f"World Bank Project {project_id}"
        
    # Make sure project_id is a string, not a number
    if project_id and not isinstance(project_id, str):
        project_id = str(project_id)
    
    # Extract reference/bid number from description if not available
    reference_number = None
    if hasattr(wb_obj, 'reference_number') and wb_obj.reference_number:
        reference_number = wb_obj.reference_number
    elif hasattr(wb_obj, 'bid_reference_no') and wb_obj.bid_reference_no:
        reference_number = wb_obj.bid_reference_no
    elif hasattr(wb_obj, 'description') and wb_obj.description:
        # Common reference number patterns
        ref_patterns = [
            r'Bid/Contract Reference No:?\s*([A-Za-z0-9\-\./]+)',
            r'Reference No\.?:?\s*([A-Za-z0-9\-\./]+)',
            r'Ref\.? No\.?:?\s*([A-Za-z0-9\-\./]+)',
            r'Reference:?\s*([A-Za-z0-9\-\./]+)',
            r'Contract No\.?:?\s*([A-Za-z0-9\-\./]+)'
        ]
        
        for pattern in ref_patterns:
            match = re.search(pattern, wb_obj.description)
            if match:
                reference_number = match.group(1).strip()
                break
    
    # Extract sector information
    sector = None
    if hasattr(wb_obj, 'sector') and wb_obj.sector:
        sector = wb_obj.sector
    else:
        # Try to extract from description
        if hasattr(wb_obj, 'description') and wb_obj.description:
            sector = extract_sector_info(wb_obj.description)
        
        # Try from project name
        if not sector and project_name:
            sector = extract_sector_info(project_name)
            
    # Standardize status
    if status:
        status = standardize_status(status)
        
    # Improve document links handling
    document_links = []  # Initialize as empty list instead of None
    
    # Process document_links if available
    if hasattr(wb_obj, 'document_links') and wb_obj.document_links:
        try:
            doc_links = normalize_document_links(wb_obj.document_links)
            if doc_links:  # Only assign if not None and not empty
                document_links = doc_links
        except Exception as e:
            logger.warning(f"Error normalizing document links: {e}")
            # Continue with empty document_links
    
    # Add main URL as document link if not already included
    if hasattr(wb_obj, 'url') and wb_obj.url:
        # Check if URL already exists in document_links
        url_exists = False
        for link in document_links:
            if isinstance(link, dict) and 'url' in link and link['url'] == wb_obj.url:
                url_exists = True
                break
        
        if not url_exists:
            document_links.append({
                "url": wb_obj.url, 
                "type": "unknown", 
                "language": language,
                "description": "Main tender notice"
            })
    
    # DEBUG: Add comprehensive logging
    logger.info(f"WB Normalizer - Processing country extraction for ID: {row.get('id', 'unknown')}")
    
    # DEBUG: Log country_value details
    logger.info(f"country_value before processing: {country_value}, Type: {type(country_value).__name__ if country_value is not None else 'None'}")
    
    # Ensure we have a country value using our fallback mechanisms - FIXED
    # Ensure country_value is a proper string before passing to ensure_country
    # to prevent the 'tuple' object has no attribute 'strip' error
    country_str = None
    try:
        if country_value:
            logger.info(f"Processing country_value: {country_value}, Type: {type(country_value).__name__}")
            if isinstance(country_value, tuple):
                logger.info(f"country_value is a tuple of length {len(country_value)}")
                if len(country_value) > 0:
                    # If country_value is a tuple, extract the first element if it's a string
                    if isinstance(country_value[0], str):
                        country_str = country_value[0].strip() if country_value[0].strip() else None
                        logger.info(f"Extracted string from tuple: {country_str}")
                    else:
                        logger.warning(f"First element of tuple is not a string: {type(country_value[0]).__name__}")
            elif isinstance(country_value, str) and country_value.strip():
                country_str = country_value.strip()
                logger.info(f"country_value is a string: {country_str}")
            else:
                logger.warning(f"country_value is neither tuple nor string: {type(country_value).__name__}")
    except Exception as e:
        logger.error(f"Error processing country_value: {e}")
        logger.error(traceback.format_exc())
    
    logger.info(f"Final country_str: {country_str}, Type: {type(country_str).__name__ if country_str is not None else 'None'}")
    
    # DEBUG: Log parameters being passed to ensure_country
    logger.info("ensure_country parameters:")
    logger.info(f"- country: {country_str}, Type: {type(country_str).__name__ if country_str is not None else 'None'}")
    logger.info(f"- text: {wb_obj.description[:100] if hasattr(wb_obj, 'description') and wb_obj.description else None}..., Type: {type(wb_obj.description).__name__ if hasattr(wb_obj, 'description') and wb_obj.description is not None else 'None'}")
    logger.info(f"- organization: {organization_name}, Type: {type(organization_name).__name__ if organization_name is not None else 'None'}")
    logger.info(f"- email: {getattr(wb_obj, 'contact_email', None)}, Type: {type(getattr(wb_obj, 'contact_email', None)).__name__ if getattr(wb_obj, 'contact_email', None) is not None else 'None'}")
    logger.info(f"- language: {language}, Type: {type(language).__name__ if language is not None else 'None'}")
    
    # Now safely call ensure_country with a properly validated string (or None)
    try:
        country = ensure_country(
            country=country_str,  # Will be None or a valid string, never a tuple
            text=wb_obj.description if hasattr(wb_obj, 'description') and isinstance(wb_obj.description, str) else None,
            organization=organization_name,
            email=getattr(wb_obj, 'contact_email', None),
            language=language
        )
        logger.info(f"ensure_country returned: {country}")
    except Exception as e:
        logger.error(f"ensure_country failed with error: {e}")
        logger.error(traceback.format_exc())
        # Fall back to a safe value
        country = "Unknown"
    
    # Create UnifiedTender object
    normalized_tender = UnifiedTender(
        id=str(uuid.uuid4()),  # Generate a new UUID for the unified record
        title=wb_obj.title if wb_obj.title else "No title",
        description=wb_obj.description,
        tender_type=wb_obj.tender_type,
        status=status,
        publication_date=publication_dt,
        deadline_date=deadline_dt,
        country=country,  # Using our guaranteed non-empty country
        city=city,
        organization_name=organization_name,
        organization_id=getattr(wb_obj, 'organization_id', None),
        buyer=buyer,
        project_name=project_name,
        project_id=project_id,
        project_number=project_number,
        sector=sector,
        estimated_value=estimated_value,
        currency=currency,
        contact_name=getattr(wb_obj, 'contact_name', None),
        contact_email=getattr(wb_obj, 'contact_email', None),
        contact_phone=getattr(wb_obj, 'contact_phone', None),
        contact_address=getattr(wb_obj, 'contact_address', None),
        url=wb_obj.url,
        document_links=document_links,
        language=language,
        notice_id=getattr(wb_obj, 'notice_id', None),
        reference_number=reference_number,
        procurement_method=procurement_method,
        original_data=wb_obj.dict() if hasattr(wb_obj, 'dict') else row,
        source_table="wb",
        source_id=wb_obj.id,
        normalized_by="pynormalizer",
        title_english=title_english,
        description_english=description_english,
        organization_name_english=organization_name_english,
        buyer_english=buyer_english,
        project_name_english=project_name_english,
    )
    
    return normalized_tender 