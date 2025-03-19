"""
Helper functions for normalizers.
"""
import json
import logging
import re
from typing import Any, Dict, Optional, Tuple, List, Union
from datetime import datetime, date
import traceback

# Initialize logger
logger = logging.getLogger(__name__)

def normalize_document_links(links_data):
    """Normalize document links to a standardized format."""
    if not links_data:
        return []
    
    # Basic implementation that extracts URLs
    normalized_links = []
    
    # Define pattern to identify URLs
    url_pattern = re.compile(
        r'(https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*)'
    )
    
    # Handle string (single URL)
    if isinstance(links_data, str):
        urls = url_pattern.findall(links_data)
        for url in urls:
            normalized_links.append({
                'url': url,
                'type': 'unknown',
                'language': 'en',
                'description': None
            })
        return normalized_links
    
    # Handle list
    if isinstance(links_data, list):
        for item in links_data:
            if isinstance(item, str):
                urls = url_pattern.findall(item)
                for url in urls:
                    normalized_links.append({
                        'url': url,
                        'type': 'unknown',
                        'language': 'en',
                        'description': None
                    })
    
    # Remove duplicates
    seen = set()
    unique_links = []
    for link in normalized_links:
        if link['url'] not in seen:
            seen.add(link['url'])
            unique_links.append(link)
    
    return unique_links

def extract_financial_info(text: str) -> Tuple[Optional[float], Optional[str]]:
    """Extract financial information from text."""
    if not text:
        return None, None
    
    # Simple patterns for extracting financial info
    currency_pattern = r'([A-Z]{3})\s*(\d+(?:,\d{3})*(?:\.\d+)?)'
    amount_pattern = r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*([A-Z]{3})'
    
    # Try currency first then amount pattern
    for pattern in [currency_pattern, amount_pattern]:
        matches = re.findall(pattern, text)
        if matches:
            for match in matches:
                try:
                    if pattern == currency_pattern:
                        currency, amount_str = match
                    else:
                        amount_str, currency = match
                    
                    # Clean amount
                    amount_str = amount_str.replace(',', '')
                    amount = float(amount_str)
                    
                    return amount, currency
                except (ValueError, TypeError):
                    continue
    
    return None, None

def format_for_logging(data: Dict[str, Any]) -> str:
    """Format data for logging, handling special types and truncating long values."""
    try:
        # Process each field
        result = {}
        for key, value in data.items():
            if value is None:
                continue
            
            # Handle datetime objects
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            # Handle dictionaries and lists
            elif isinstance(value, (dict, list)):
                try:
                    # Try to serialize to JSON
                    json_str = json.dumps(value, default=str)
                    # Truncate if too long
                    if len(json_str) > 500:
                        result[key] = json_str[:497] + "..."
                    else:
                        result[key] = json_str
                except:
                    result[key] = str(value)[:100]
            # Handle long strings
            elif isinstance(value, str) and len(value) > 300:
                result[key] = value[:297] + "..."
            # Regular values
            else:
                result[key] = value
        
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return str(data)

def ensure_country(country_value=None, text=None, organization=None, email=None, language=None):
    """Normalize country names to standard English names."""
    if not country_value:
        return "Unknown"
    
    # Simple standardization
    country_mapping = {
        "usa": "United States",
        "us": "United States",
        "uk": "United Kingdom",
        "gb": "United Kingdom",
        "uae": "United Arab Emirates",
        "kyrgyz": "Kyrgyz Republic",
        "kyrgyzstan": "Kyrgyz Republic",
        "vietnam": "Vietnam",
        "viet nam": "Vietnam",
    }
    
    if isinstance(country_value, str):
        country_lower = country_value.lower().strip()
        if country_lower in country_mapping:
            return country_mapping[country_lower]
    
    return country_value

def log_tender_normalization(source_table, source_id, log_data):
    """Log tender normalization process."""
    try:
        if not isinstance(log_data, dict):
            log_data = {"data": str(log_data)}
            
        formatted_data = format_for_logging(log_data)
        logger.info(f"Normalizing tender from {source_table} (ID: {source_id}): {formatted_data}")
    except Exception as e:
        logger.error(f"Error logging tender normalization: {str(e)}")

def clean_price(price_value):
    """Clean and normalize a price value."""
    if price_value is None:
        return None

    if isinstance(price_value, (int, float)):
        return float(price_value)
    
    if not isinstance(price_value, str):
        try:
            return float(price_value)
        except (ValueError, TypeError):
            return None
    
    # Clean string representation
    price_str = price_value.strip()
    price_str = re.sub(r'[^0-9.,]', '', price_str)
    
    # Handle different decimal and thousand separators
    if ',' in price_str and '.' in price_str:
        if price_str.rindex('.') > price_str.rindex(','):
            price_str = price_str.replace(',', '')
        else:
            price_str = price_str.replace('.', '').replace(',', '.')
    elif ',' in price_str:
        if len(price_str.split(',')[1]) == 2:
            price_str = price_str.replace(',', '.')
    
    if not price_str:
        return None
    
    try:
        return float(price_str)
    except ValueError:
        return None

def extract_status(text=None, deadline=None, publication_date=None, description=None):
    """Extract tender status information."""
    # Use description as text if text is None
    if text is None and description is not None:
        text = description
    
    # Default status
    status = 'active'
    
    if text and isinstance(text, str):
        text_lower = text.lower()
        
        if any(term in text_lower for term in ['complete', 'completed', 'closed', 'awarded']):
            status = 'complete'
        elif any(term in text_lower for term in ['cancelled', 'canceled', 'terminated']):
            status = 'cancelled'
    
    # Check dates if available
    if deadline or publication_date:
        try:
            current_date = datetime.now().date()
            
            if deadline and isinstance(deadline, datetime):
                deadline_date = deadline.date()
                if deadline_date < current_date:
                    status = 'complete'
        except Exception:
            pass
    
    return status

def parse_date_string(date_str):
    """Parse a date string into a datetime object."""
    if not date_str or not isinstance(date_str, str):
        return None

    # Clean the string
    date_str = date_str.strip()
    
    # Common date formats to try
    date_formats = [
        '%Y-%m-%d',      
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%d %H:%M:%S',
        '%d/%m/%Y',
        '%m/%d/%Y',
        '%d-%m-%Y',
        '%m-%d-%Y'
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None

def extract_sector_info(text):
    """Extract sector information from text."""
    if not text or not isinstance(text, str):
        return None
    
    text = text.lower()
    
    # Define common sectors
    sector_keywords = {
        'agriculture': ['agriculture', 'farming', 'irrigation', 'crop'],
        'construction': ['construction', 'building', 'infrastructure', 'roads'],
        'education': ['education', 'school', 'university', 'college'],
        'energy': ['energy', 'electricity', 'power', 'renewable'],
        'finance': ['finance', 'banking', 'insurance', 'investment'],
        'health': ['health', 'medical', 'hospital', 'clinic'],
        'ict': ['ict', 'information technology', 'technology', 'telecom'],
        'transportation': ['transportation', 'transport', 'logistics', 'railway'],
        'water': ['water', 'sanitation', 'sewage', 'wastewater']
    }
    
    identified_sectors = []
    
    # Check for each sector's keywords
    for sector, keywords in sector_keywords.items():
        if any(keyword in text for keyword in keywords):
            identified_sectors.append(sector)
    
    return identified_sectors if identified_sectors else None

def standardize_status(status_text):
    """Standardize various status values."""
    if not status_text:
        return None

    if not isinstance(status_text, str):
        status_text = str(status_text)
    
    status_text = status_text.lower().strip()
    
    # Active/Open status mappings
    if any(term in status_text for term in ['active', 'ongoing', 'open', 'current', 'in progress']):
        return 'active'
    
    # Complete/Closed status mappings
    if any(term in status_text for term in ['complete', 'completed', 'closed', 'awarded', 'finished']):
        return 'complete'
    
    # Cancelled status mappings
    if any(term in status_text for term in ['cancel', 'cancelled', 'canceled', 'terminated', 'withdrawn']):
        return 'cancelled'
    
    # Planned/Upcoming status mappings
    if any(term in status_text for term in ['planned', 'upcoming', 'future', 'announced']):
        return 'planned'
    
    # Default to active
    return 'active'

def normalize_title(title: str) -> str:
    """Normalize tender title."""
    if not title:
        return None
    
    # Remove multiple spaces
    title = ' '.join(title.split())
    
    # Remove common prefixes
    title = re.sub(r'^(?:Notice|Tender|RFP|RFQ|ITB|EOI)\s*[-:]\s*', '', title, flags=re.IGNORECASE)
    
    # Remove reference numbers at the start
    title = re.sub(r'^[A-Z0-9-/]+\s*[-:]\s*', '', title)
    
    return title

def normalize_description(description: str) -> str:
    """Normalize tender description."""
    if not description:
        return None

    # Remove multiple spaces
    description = ' '.join(description.split())
    
    # Remove common HTML artifacts
    description = re.sub(r'<[^>]+>', ' ', description)
    
    # Remove URLs (they should be in document_links)
    description = re.sub(r'http[s]?://\S+', '', description)
    
    return description.strip()

def standardize_procurement_method(method: str) -> str:
    """Standardize procurement method."""
    if not method:
        return None
    
    method = method.lower().strip()
    
    # Define method mappings
    method_mapping = {
        'open': 'Open Procedure',
        'restricted': 'Restricted Procedure',
        'negotiated': 'Negotiated Procedure',
        'competitive dialogue': 'Competitive Dialogue',
        'rfp': 'Request for Proposal',
        'request for proposal': 'Request for Proposal',
        'rfq': 'Request for Quotation',
        'request for quotation': 'Request for Quotation',
        'direct': 'Direct Procurement',
        'single source': 'Direct Procurement'
    }
    
    # Try direct mapping
    if method in method_mapping:
        return method_mapping[method]
    
    # Try partial matching
    for key, value in method_mapping.items():
        if key in method:
            return value
    
    # If no match found, capitalize words
    return ' '.join(word.capitalize() for word in method.split())

def normalize_value(value: float, currency: str = None) -> Tuple[float, str]:
    """Normalize tender value and currency."""
    if not value:
        return None, currency
    
    # Define reasonable value range
    if value < 100 or value > 1000000000000:  # $100 to $1 trillion
        return None, currency
    
    # Normalize currency code
    if currency:
        currency = currency.upper().strip()
        
        # Define currency mappings for non-standard codes
        currency_mapping = {
            'EURO': 'EUR',
            'EUROS': 'EUR',
            'US$': 'USD',
            'USD$': 'USD',
            'DOLLAR': 'USD',
            'DOLLARS': 'USD',
            'GBP£': 'GBP',
            'UKP': 'GBP',
            'RMB': 'CNY',
            'YUAN': 'CNY'
        }
        
        currency = currency_mapping.get(currency, currency)
    
    return value, currency

def extract_organization_and_buyer(text: str, title: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract both organization and buyer information from text.
    
    Args:
        text: Main text to extract from
        title: Optional title text to also check
        
    Returns:
        Tuple of (organization_name, buyer_name)
    """
    # Try to extract organization from title first if available
    organization = None
    buyer = None
    
    # Simple extraction logic
    if title:
        for prefix in ["for", "by", "from"]:
            if f" {prefix} " in title:
                org_part = title.split(f" {prefix} ", 1)[1].strip()
                if org_part:
                    organization = org_part
                    break
    
    # If not found in title, try main text
    if not organization and text:
        for prefix in ["organization:", "organisation:", "buyer:", "procuring entity:", "client:"]:
            if prefix in text.lower():
                idx = text.lower().find(prefix)
                if idx >= 0:
                    end_idx = text.find(".", idx)
                    if end_idx > idx:
                        organization = text[idx + len(prefix):end_idx].strip()
                        break
    
    # Look for buyer-specific patterns
    if text:
        for prefix in ["buyer:", "purchasing entity:", "contracting authority:"]:
            if prefix in text.lower():
                idx = text.lower().find(prefix)
                if idx >= 0:
                    end_idx = text.find(".", idx)
                    if end_idx > idx:
                        buyer = text[idx + len(prefix):end_idx].strip()
                        break
    
    # If organization is still missing but we found a buyer, use it as organization
    if not organization and buyer:
        organization = buyer
    
    return organization, buyer

def log_before_after(field, before, after):
    """
    Log the before and after values of a field during normalization.
    
    Args:
        field: Field name
        before: Value before normalization
        after: Value after normalization
    """
    if before != after:
        logger.info(f"Normalized {field}: '{before}' -> '{after}'")
    return after

def determine_normalized_method(row, default=None):
    """
    Determine the normalized_method for a tender based on source table and available data.
    
    Args:
        row (dict): Row of data from a source table
        default (str, optional): Default value if no method can be determined
        
    Returns:
        str: The normalized procurement method
    """
    # If normalized_method is already set and valid, return it
    if row.get('normalized_method') and row['normalized_method'].strip():
        return row['normalized_method']
    
    # Default methods by source table
    table_defaults = {
        'wb': 'International Competitive Bidding',
        'adb': 'Open Competitive Bidding',
        'afdb': 'International Competitive Bidding', 
        'afd': 'International Competitive Bidding',
        'aiib': 'International Open Competitive Tendering',
        'iadb': 'International Competitive Bidding',
        'tedeu': 'Open Procedure',
        'sam_gov': 'Full and Open Competition',
        'ungm': 'International Competitive Bidding'
    }
    
    # If we have the source table and a procurement method
    if row.get('source_table') and row.get('procurement_method') and row['procurement_method'].strip():
        method = row['procurement_method'].lower()
        
        # Standardize method names based on common patterns
        if 'open' in method or 'competitive' in method:
            if 'international' in method:
                return 'International Competitive Bidding'
            elif 'national' in method:
                return 'National Competitive Bidding'
            else:
                return 'Open Competitive Bidding'
        elif 'direct' in method or 'sole source' in method or 'single source' in method:
            return 'Direct Procurement'
        elif 'limited' in method or 'selective' in method or 'restricted' in method:
            return 'Limited Competitive Bidding'
        elif 'quality' in method and 'cost' in method:
            return 'Quality and Cost-Based Selection'
        elif 'consultant' in method and 'selection' in method:
            return 'Consultant Qualification Selection'
        elif 'request for proposal' in method or 'rfp' in method:
            return 'Request for Proposal'
        elif 'request for quotation' in method or 'rfq' in method:
            return 'Request for Quotation'
    
    # Use source table default
    if row.get('source_table') and row['source_table'] in table_defaults:
        return table_defaults[row['source_table']]
    
    # Fallback to the provided default or a generic term
    return default or 'Competitive Bidding'

def clean_date(date_value):
    """
    Clean and normalize a date value to ISO format (YYYY-MM-DD).
    
    Args:
        date_value: The date value to clean (can be string, datetime, date, or None)
        
    Returns:
        Cleaned date as string in ISO format or None if invalid
    """
    if date_value is None:
        return None
        
    # If already a date or datetime object, format it
    if isinstance(date_value, (datetime, date)):
        return date_value.strftime('%Y-%m-%d')
    
    if not isinstance(date_value, str):
        try:
            # Try to convert to string
            date_value = str(date_value)
        except (ValueError, TypeError):
            return None
    
    # Clean string representation
    date_str = date_value.strip()
    
    # Common date formats to try
    date_formats = [
        '%Y-%m-%d',       # 2023-01-30
        '%d/%m/%Y',       # 30/01/2023
        '%m/%d/%Y',       # 01/30/2023
        '%d-%m-%Y',       # 30-01-2023
        '%m-%d-%Y',       # 01-30-2023
        '%d.%m.%Y',       # 30.01.2023
        '%m.%d.%Y',       # 01.30.2023
        '%Y/%m/%d',       # 2023/01/30
        '%B %d, %Y',      # January 30, 2023
        '%d %B %Y',       # 30 January 2023
        '%d %b %Y',       # 30 Jan 2023
        '%b %d, %Y'       # Jan 30, 2023
    ]
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    # Special handling for Unix timestamps
    if date_str.isdigit() and len(date_str) >= 10:
        try:
            # Try as Unix timestamp (seconds since epoch)
            dt = datetime.fromtimestamp(int(date_str[:10]))
            return dt.strftime('%Y-%m-%d')
        except (ValueError, OverflowError):
            pass
    
    # If all parsing attempts fail
    return None

def extract_location_info(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract country and city information from text.
    
    Args:
        text: Text to extract from
        
    Returns:
        Tuple of (country, city)
    """
    if not text or not isinstance(text, str):
        return None, None
    
    # Country patterns mapped to common city names
    country_city_patterns = {
        'Afghanistan': ['Kabul', 'Herat', 'Mazar-i-Sharif'],
        'Bangladesh': ['Dhaka', 'Chittagong', 'Khulna'],
        'China': ['Beijing', 'Shanghai', 'Guangzhou'],
        'India': ['New Delhi', 'Mumbai', 'Bangalore'],
        'Indonesia': ['Jakarta', 'Surabaya', 'Bandung'],
        'Japan': ['Tokyo', 'Yokohama', 'Osaka'],
        'Kenya': ['Nairobi', 'Mombasa', 'Kisumu'],
        'Malaysia': ['Kuala Lumpur', 'George Town', 'Ipoh'],
        'Pakistan': ['Islamabad', 'Karachi', 'Lahore'],
        'Philippines': ['Manila', 'Quezon City', 'Davao City'],
        'United Kingdom': ['London', 'Birmingham', 'Manchester'],
        'United States': ['Washington', 'New York', 'Los Angeles'],
        'Vietnam': ['Hanoi', 'Ho Chi Minh City', 'Hai Phong']
    }
    
    # Check for country mentions
    country = None
    for country_name in country_city_patterns.keys():
        if country_name.lower() in text.lower():
            country = country_name
            break
    
    # Check for city mentions
    city = None
    
    # First try cities from the found country if available
    if country:
        cities = country_city_patterns.get(country, [])
        for city_name in cities:
            if city_name.lower() in text.lower():
                city = city_name
                break
    
    # If no city found, try all cities
    if not city:
        all_cities = [city for cities in country_city_patterns.values() for city in cities]
        for city_name in all_cities:
            if city_name.lower() in text.lower():
                city = city_name
                break
    
    return country, city