import json
import re
from typing import Dict, Any, Optional, List, Tuple

from pynormalizer.models.source_models import WBTender
from pynormalizer.models.unified_model import UnifiedTender
from pynormalizer.utils.translation import translate_to_english, detect_language

def extract_financial_info(text: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Extract estimated value and currency from text.
    
    Args:
        text: Text to extract from
        
    Returns:
        Tuple of (estimated_value, currency)
    """
    if not text:
        return None, None
        
    # Look for currency symbols and amounts
    currency_patterns = {
        'USD': r'US\$\s*([\d,]+(?:\.\d+)?)|USD\s*([\d,]+(?:\.\d+)?)|(\$\s*[\d,]+(?:\.\d+)?)',
        'EUR': r'EUR\s*([\d,]+(?:\.\d+)?)|€\s*([\d,]+(?:\.\d+)?)',
        'GBP': r'GBP\s*([\d,]+(?:\.\d+)?)|£\s*([\d,]+(?:\.\d+)?)',
        'CAD': r'CAD\s*([\d,]+(?:\.\d+)?)',
        'AUD': r'AUD\s*([\d,]+(?:\.\d+)?)',
        'INR': r'INR\s*([\d,]+(?:\.\d+)?)|Rs\.\s*([\d,]+(?:\.\d+)?)'
    }
    
    for currency, pattern in currency_patterns.items():
        matches = re.findall(pattern, text)
        if matches:
            # Flatten matches and find first non-empty group
            for match in matches:
                if isinstance(match, tuple):
                    for group in match:
                        if group:
                            # Remove commas and convert to float
                            try:
                                value = float(group.replace(',', ''))
                                return value, currency
                            except (ValueError, TypeError):
                                pass
    
    # Look for patterns like "1.5 million USD" or "USD 1.5 million"
    million_patterns = [
        r'(\d+(?:\.\d+)?)\s*million\s*(USD|EUR|GBP|CAD|AUD|INR|\$|€|£)',
        r'(USD|EUR|GBP|CAD|AUD|INR|\$|€|£)\s*(\d+(?:\.\d+)?)\s*million'
    ]
    
    for pattern in million_patterns:
        matches = re.findall(pattern, text)
        if matches:
            for match in matches:
                try:
                    value = float(match[0]) * 1000000
                    currency = match[1]
                    # Map symbols to currency codes
                    if currency == "$":
                        currency = "USD"
                    elif currency == "€":
                        currency = "EUR"
                    elif currency == "£":
                        currency = "GBP"
                    return value, currency
                except (ValueError, TypeError, IndexError):
                    pass
                    
    return None, None

def extract_location_info(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract country and city information from text.
    
    Args:
        text: Text to extract from
        
    Returns:
        Tuple of (country, city)
    """
    if not text:
        return None, None
    
    country = None
    city = None
    
    # Common countries in World Bank tenders
    country_patterns = {
        'Afghanistan': r'\bAfghanistan\b',
        'Albania': r'\bAlbania\b',
        'Algeria': r'\bAlgeria\b',
        'Angola': r'\bAngola\b',
        'Argentina': r'\bArgentina\b',
        'Armenia': r'\bArmenia\b',
        'Bangladesh': r'\bBangladesh\b',
        'Brazil': r'\bBrazil\b',
        'Cambodia': r'\bCambodia\b',
        'Cameroon': r'\bCameroon\b',
        'China': r'\bChina\b',
        'Colombia': r'\bColombia\b',
        'Congo': r'\bCongo\b',
        'Ecuador': r'\bEcuador\b',
        'Egypt': r'\bEgypt\b',
        'Ethiopia': r'\bEthiopia\b',
        'Georgia': r'\bGeorgia\b',
        'Ghana': r'\bGhana\b',
        'India': r'\bIndia\b',
        'Indonesia': r'\bIndonesia\b',
        'Iraq': r'\bIraq\b',
        'Jamaica': r'\bJamaica\b',
        'Jordan': r'\bJordan\b',
        'Kenya': r'\bKenya\b',
        'Laos': r'\bLaos\b',
        'Lebanon': r'\bLebanon\b',
        'Liberia': r'\bLiberia\b',
        'Libya': r'\bLibya\b',
        'Madagascar': r'\bMadagascar\b',
        'Malawi': r'\bMalawi\b',
        'Malaysia': r'\bMalaysia\b',
        'Mexico': r'\bMexico\b',
        'Morocco': r'\bMorocco\b',
        'Mozambique': r'\bMozambique\b',
        'Myanmar': r'\bMyanmar\b',
        'Nepal': r'\bNepal\b',
        'Nigeria': r'\bNigeria\b',
        'Pakistan': r'\bPakistan\b',
        'Peru': r'\bPeru\b',
        'Philippines': r'\bPhilippines\b',
        'Rwanda': r'\bRwanda\b',
        'Senegal': r'\bSenegal\b',
        'Sierra Leone': r'\bSierra Leone\b',
        'Somalia': r'\bSomalia\b',
        'South Africa': r'\bSouth Africa\b',
        'South Sudan': r'\bSouth Sudan\b',
        'Sri Lanka': r'\bSri Lanka\b',
        'Sudan': r'\bSudan\b',
        'Tanzania': r'\bTanzania\b',
        'Thailand': r'\bThailand\b',
        'Tunisia': r'\bTunisia\b',
        'Turkey': r'\bTurkey\b',
        'Uganda': r'\bUganda\b',
        'Ukraine': r'\bUkraine\b',
        'Vietnam': r'\bVietnam\b',
        'Yemen': r'\bYemen\b',
        'Zambia': r'\bZambia\b',
        'Zimbabwe': r'\bZimbabwe\b'
    }
    
    # Check for country mentions
    for country_name, pattern in country_patterns.items():
        if re.search(pattern, text):
            country = country_name
            break
    
    # Try to extract city using patterns like "City of X" or "X City"
    city_patterns = [
        r'City of ([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)',
        r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)*) City',
        r'in ([A-Z][a-z]+(?:\s[A-Z][a-z]+)*), ' + (country if country else r'[A-Z][a-z]+')
    ]
    
    for pattern in city_patterns:
        matches = re.findall(pattern, text)
        if matches:
            city = matches[0]
            break
    
    return country, city

def normalize_wb(row: Dict[str, Any]) -> UnifiedTender:
    """
    Normalize a World Bank tender record.
    
    Args:
        row: Dictionary containing World Bank tender data
        
    Returns:
        Normalized UnifiedTender instance
    """
    # Handle document_links if it's a string
    if isinstance(row.get('document_links'), str):
        try:
            if row['document_links'].strip():
                row['document_links'] = json.loads(row['document_links'])
            else:
                row['document_links'] = None
        except (json.JSONDecodeError, ValueError):
            row['document_links'] = None
            
    # Validate with Pydantic
    try:
        wb_obj = WBTender(**row)
    except Exception as e:
        raise ValueError(f"Failed to validate World Bank tender: {e}")

    # Detect language from title and/or description
    language = "en"  # Default to English for World Bank
    
    if wb_obj.title:
        detected = detect_language(wb_obj.title)
        if detected:
            language = detected
    elif wb_obj.description and not language:
        detected = detect_language(wb_obj.description)
        if detected:
            language = detected

    # Extract procurement method information with more detail
    procurement_method = None
    
    # Try direct fields first
    if wb_obj.procurement_method_name:
        procurement_method = wb_obj.procurement_method_name
    elif wb_obj.procurement_method:
        procurement_method = wb_obj.procurement_method
        
    # Try to extract from description if needed
    if not procurement_method and wb_obj.description:
        # Common procurement methods
        proc_method_patterns = {
            'International Competitive Bidding': r'\bInternational Competitive Bidding\b|\bICB\b',
            'National Competitive Bidding': r'\bNational Competitive Bidding\b|\bNCB\b',
            'Request for Proposals': r'\bRequest for Proposals\b|\bRFP\b',
            'Quality and Cost-Based Selection': r'\bQuality and Cost-Based Selection\b|\bQCBS\b',
            'Quality-Based Selection': r'\bQuality-Based Selection\b|\bQBS\b',
            'Fixed Budget Selection': r'\bFixed Budget Selection\b|\bFBS\b',
            'Least Cost Selection': r'\bLeast Cost Selection\b|\bLCS\b',
            'Shopping': r'\bShopping\b',
            'Direct Contracting': r'\bDirect Contracting\b',
            'Request for Quotations': r'\bRequest for Quotations\b|\bRFQ\b',
            'Consultant\'s Qualification Selection': r'\bConsultant\'s Qualification Selection\b|\bCQS\b'
        }
        
        for method, pattern in proc_method_patterns.items():
            if re.search(pattern, wb_obj.description):
                procurement_method = method
                break
                
    # Extract procurement method from procurement_method_code if available
    if not procurement_method and wb_obj.procurement_method_code:
        # Common procurement method codes
        proc_code_map = {
            'ICB': 'International Competitive Bidding',
            'NCB': 'National Competitive Bidding',
            'RFP': 'Request for Proposals',
            'QCBS': 'Quality and Cost-Based Selection',
            'QBS': 'Quality-Based Selection',
            'FBS': 'Fixed Budget Selection',
            'LCS': 'Least Cost Selection',
            'CQS': 'Consultant\'s Qualification Selection',
            'SSS': 'Single Source Selection',
            'RFQ': 'Request for Quotations',
            'DC': 'Direct Contracting'
        }
        procurement_method = proc_code_map.get(wb_obj.procurement_method_code, wb_obj.procurement_method_code)
    
    # Extract status information
    status = None
    
    # Try direct field first
    if wb_obj.notice_status:
        status = wb_obj.notice_status
    elif wb_obj.tender_type == "Contract Award":
        status = "Awarded"
    
    # Extract status from tender type
    if not status and wb_obj.tender_type:
        status_map = {
            'Invitation for Bids': 'Open',
            'Request for Expression of Interest': 'Open',
            'Request for Proposals': 'Open',
            'Request for Qualifications': 'Open',
            'Request for Quotations': 'Open',
            'General Procurement Notice': 'Planned',
            'Specific Procurement Notice': 'Open',
            'Contract Award': 'Awarded'
        }
        status = status_map.get(wb_obj.tender_type)
        
    # Try to extract from description or notice text if available
    if not status:
        status_text = wb_obj.description or wb_obj.notice_text or ""
        
        if re.search(r'\bawarded\b|\bcontract award\b|\bwinner\b', status_text, re.IGNORECASE):
            status = "Awarded"
        elif re.search(r'\bclosed\b|\bcompleted\b|\bdeadline passed\b', status_text, re.IGNORECASE):
            status = "Closed"
        elif re.search(r'\bopen\b|\bongoing\b|\bcurrent\b', status_text, re.IGNORECASE):
            status = "Open"
        elif re.search(r'\bcancelled\b|\bcanceled\b', status_text, re.IGNORECASE):
            status = "Cancelled"
    
    # Extract financial information (estimated value and currency)
    estimated_value = None
    currency = None
    
    # Extract from description
    if wb_obj.description:
        value, curr = extract_financial_info(wb_obj.description)
        if value and curr:
            estimated_value = value
            currency = curr
            
    # Try notice text if needed
    if not estimated_value and wb_obj.notice_text:
        value, curr = extract_financial_info(wb_obj.notice_text)
        if value and curr:
            estimated_value = value
            currency = curr
    
    # Extract location information
    country = wb_obj.country or wb_obj.project_ctry_name
    city = None
    
    # Try to extract city if country is available
    if wb_obj.description:
        extracted_country, extracted_city = extract_location_info(wb_obj.description)
        if not country:
            country = extracted_country
        if extracted_city:
            city = extracted_city
    
    # Construct the UnifiedTender
    unified = UnifiedTender(
        # Required fields
        title=wb_obj.title or f"World Bank Tender - {wb_obj.id}",
        source_table="wb",
        source_id=wb_obj.id,
        
        # Additional fields
        description=wb_obj.description or wb_obj.notice_text,
        tender_type=wb_obj.tender_type or wb_obj.notice_type,
        status=status,
        publication_date=wb_obj.publication_date,
        deadline_date=wb_obj.deadline or wb_obj.submission_date,
        country=country,
        city=city,
        project_name=wb_obj.project_name,
        project_id=wb_obj.project_id,
        contact_name=wb_obj.contact_name,
        contact_email=wb_obj.contact_email,
        contact_phone=wb_obj.contact_phone,
        contact_address=wb_obj.contact_address,
        organization_name=wb_obj.contact_organization,
        url=wb_obj.url,
        document_links=wb_obj.document_links,
        language=language,
        reference_number=wb_obj.bid_reference_no,
        procurement_method=procurement_method,
        estimated_value=estimated_value,
        currency=currency,
        original_data=row,
        normalized_method="offline-dictionary",
    )

    # Translate non-English fields if needed
    language = unified.language or "en"
    
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
        
        # Update fallback_reason
        if desc_method == "already_english":
            if unified.fallback_reason:
                fallback = json.loads(unified.fallback_reason)
                fallback["description"] = "already_english"
                unified.fallback_reason = json.dumps(fallback)
            else:
                unified.fallback_reason = json.dumps({"description": "already_english"})
    
    # Translate project name if needed
    if unified.project_name:
        proj_en, proj_method = translate_to_english(unified.project_name, language)
        unified.project_name_english = proj_en
        
        # Update fallback_reason
        if proj_method == "already_english":
            if unified.fallback_reason:
                fallback = json.loads(unified.fallback_reason)
                fallback["project_name"] = "already_english"
                unified.fallback_reason = json.dumps(fallback)
            else:
                unified.fallback_reason = json.dumps({"project_name": "already_english"})
    
    # Translate organization name if needed
    if unified.organization_name:
        org_en, org_method = translate_to_english(unified.organization_name, language)
        unified.organization_name_english = org_en
        
        # Update fallback_reason
        if org_method == "already_english":
            if unified.fallback_reason:
                fallback = json.loads(unified.fallback_reason)
                fallback["organization_name"] = "already_english"
                unified.fallback_reason = json.dumps(fallback)
            else:
                unified.fallback_reason = json.dumps({"organization_name": "already_english"})

    return unified 