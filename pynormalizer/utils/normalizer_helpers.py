"""
Helper functions for normalizers.
"""
import json
import logging
import re
from typing import Any, Dict, Optional, Tuple, List, Union
from datetime import datetime
from pynormalizer.models.unified_model import UnifiedTender
from pynormalizer.utils.translation import translate_to_english

# Initialize logger
logger = logging.getLogger(__name__)

def normalize_document_links(links_data):
    """
    Normalize document links to a standardized format.
    
    Args:
        links_data: Document links data in various formats
        
    Returns:
        List of normalized document link objects
    """
    normalized_links = []
    
    if not links_data:
        return normalized_links
    
    # Define pattern to identify URLs
    url_pattern = re.compile(
        r'(https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*)'
    )
    
    # Handle string (single URL)
    if isinstance(links_data, str):
        # Try to extract URLs from text
        urls = url_pattern.findall(links_data)
        for url in urls:
            normalized_links.append({
                'url': url,
                'type': 'unknown',
                'language': 'en',
                'description': None
            })
        if not urls and links_data.startswith(('http://', 'https://', 'www.')):
            normalized_links.append({
                'url': links_data,
                'type': 'unknown',
                'language': 'en',
                'description': None
            })
        return normalized_links
    
    # Handle list of strings
    if isinstance(links_data, list) and all(isinstance(item, str) for item in links_data):
        for item in links_data:
            # Try to extract URLs from text
            urls = url_pattern.findall(item)
            for url in urls:
                normalized_links.append({
                    'url': url,
                    'type': 'unknown',
                    'language': 'en',
                    'description': None
                })
            if not urls and item.startswith(('http://', 'https://', 'www.')):
                normalized_links.append({
                    'url': item,
                    'type': 'unknown',
                    'language': 'en',
                    'description': None
                })
        return normalized_links
    
    # Handle list of dicts with various structures
    if isinstance(links_data, list):
        for item in links_data:
            if isinstance(item, dict):
                # Extract URL - try various common keys
                url = None
                for key in ['url', 'link', 'href', 'uri', 'location', 'path']:
                    if key in item and item[key]:
                        if isinstance(item[key], str):
                            # Try to extract URLs from text
                            urls = url_pattern.findall(item[key])
                            if urls:
                                url = urls[0]
                            elif item[key].startswith(('http://', 'https://', 'www.')):
                                url = item[key]
                            break
                
                if not url:
                    continue
                
                # Skip invalid URLs
                if not url.startswith(('http://', 'https://', 'www.')):
                    continue
                
                # Extract type
                doc_type = 'unknown'
                for key in ['type', 'document_type', 'doc_type', 'fileType', 'format']:
                    if key in item and item[key]:
                        doc_type = item[key]
                        break
                
                # Extract language
                language = 'en'  # Default to English
                for key in ['language', 'lang', 'locale']:
                    if key in item and item[key]:
                        language = item[key]
                        break
                
                # Extract description
                description = None
                for key in ['description', 'desc', 'title', 'name', 'text', 'label']:
                    if key in item and item[key]:
                        description = item[key]
                        break
                
                normalized_links.append({
                    'url': url,
                    'type': doc_type,
                    'language': language,
                    'description': description
                })
            elif isinstance(item, str):
                # Try to extract URLs from text
                urls = url_pattern.findall(item)
                for url in urls:
                    normalized_links.append({
                        'url': url,
                        'type': 'unknown',
                        'language': 'en',
                        'description': None
                    })
                if not urls and item.startswith(('http://', 'https://', 'www.')):
                    normalized_links.append({
                        'url': item,
                        'type': 'unknown',
                        'language': 'en',
                        'description': None
                    })
    
    # Handle dict with 'items' key (common pattern)
    elif isinstance(links_data, dict) and 'items' in links_data:
        try:
            items = links_data['items']
            if items and isinstance(items, (list, dict)):
                return normalize_document_links(items)
        except Exception:
            # In case of any error, return what we have so far
            pass
    
    # Handle dict with URLs as values
    elif isinstance(links_data, dict):
        # Try to extract direct links
        for key, value in links_data.items():
            if isinstance(value, str):
                # Try to extract URLs from text
                urls = url_pattern.findall(value)
                for url in urls:
                    normalized_links.append({
                        'url': url,
                        'type': 'unknown',
                        'language': 'en',
                        'description': key if key != 'url' and not key.isdigit() else None
                    })
                if not urls and value.startswith(('http://', 'https://', 'www.')):
                    normalized_links.append({
                        'url': value,
                        'type': 'unknown',
                        'language': 'en',
                        'description': key if key != 'url' and not key.isdigit() else None
                    })
            elif isinstance(value, dict) and 'url' in value and isinstance(value['url'], str):
                # Extract URLs from the url field
                urls = url_pattern.findall(value['url'])
                if urls:
                    doc = {
                        'url': urls[0],
                        'type': value.get('type', 'unknown'),
                        'language': value.get('language', 'en'),
                        'description': value.get('description', None)
                    }
                    normalized_links.append(doc)
                elif value['url'].startswith(('http://', 'https://', 'www.')):
                    doc = {
                        'url': value['url'],
                        'type': value.get('type', 'unknown'),
                        'language': value.get('language', 'en'),
                        'description': value.get('description', None)
                    }
                    normalized_links.append(doc)
    
    # Remove duplicates by URL
    seen_urls = set()
    unique_links = []
    
    for link in normalized_links:
        if link['url'] not in seen_urls:
            seen_urls.add(link['url'])
            unique_links.append(link)
    
    return unique_links

def extract_financial_info(text):
    """
    Extract financial information from text including currency and value.
    
    Args:
        text: Text to extract financial information from
        
    Returns:
        Tuple of (value, currency)
    """
    if not text:
        return None, None
    
    # Define common currency codes and symbols
    currency_patterns = {
        'USD': ['USD', 'US$', '$', 'Dollar', 'Dollars'],
        'EUR': ['EUR', '€', 'Euro', 'Euros'],
        'GBP': ['GBP', '£', 'Pound', 'Pounds'],
        'JPY': ['JPY', '¥', 'Yen'],
        'CNY': ['CNY', 'RMB', 'Yuan'],
        'INR': ['INR', '₹', 'Rupee', 'Rupees'],
        'MWK': ['MWK', 'Malawi Kwacha'],
        'AUD': ['AUD', 'AU$', 'Australian Dollar'],
        'CAD': ['CAD', 'CA$', 'Canadian Dollar'],
        'CHF': ['CHF', 'Swiss Franc'],
        'XAF': ['XAF', 'CFA Franc'],
        'NGN': ['NGN', '₦', 'Naira'],
        'ZAR': ['ZAR', 'R', 'Rand'],
        'KES': ['KES', 'KSh', 'Kenyan Shilling'],
        'BRL': ['BRL', 'R$', 'Real', 'Reais'],
        'RWF': ['RWF', 'Rwf', 'Rwandan Francs', 'Rwandan Franc'],
    }
    
    # First, check for specific Rwanda franc pattern which is often missed
    # Pattern like: "Rwf 10,000" or "10,000 Rwandan Francs"
    rwf_patterns = [
        r'(?:Rwf|RWF)\s*([\d,\.]+(?:\s*million|\s*M|\s*billion|\s*B)?)',
        r'([\d,\.]+)(?:\s*million|\s*M|\s*billion|\s*B)?\s*(?:Rwandan Francs?|RWF|Rwf)'
    ]
    
    for pattern in rwf_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            try:
                # Process the first match
                value_str = matches[0].replace(',', '')
                multiplier = 1
                
                # Check for million/billion indicators
                if re.search(r'million|M', text, re.IGNORECASE):
                    multiplier = 1000000
                    value_str = re.sub(r'million|M', '', value_str, flags=re.IGNORECASE).strip()
                elif re.search(r'billion|B', text, re.IGNORECASE):
                    multiplier = 1000000000
                    value_str = re.sub(r'billion|B', '', value_str, flags=re.IGNORECASE).strip()
                    
                value = float(value_str) * multiplier
                return value, 'RWF'
            except (ValueError, IndexError):
                # Skip if value can't be parsed
                pass
    
    # Find financial values with currency indicators
    # Pattern matches both "USD 1,000,000" and "1,000,000 USD" formats
    # Also handles decimal points and various separators
    financial_patterns = [
        # Currency code/symbol followed by number: USD 1,000,000.00
        r'([A-Z]{3}|[€£$¥₹₦])\s*([\d,\.]+)(?:\s*(?:million|billion|m|b))?',
        # Number followed by currency code/name: 1,000,000.00 USD
        r'([\d,\.]+)(?:\s*(?:million|billion|m|b))?\s*([A-Z]{3}|[€£$¥₹₦]|dollars?|euros?|pounds?|yen|yuan)',
        # Numeric with M/B suffix: USD 1.5M, 1.5B USD
        r'([A-Z]{3}|[€£$¥₹₦])\s*([\d,\.]+[MB])',
        r'([\d,\.]+[MB])\s*([A-Z]{3}|[€£$¥₹₦]|dollars?|euros?|pounds?|yen|yuan)',
        # Additional pattern for "X million USD" format
        r'([\d,\.]+)\s+(?:million|billion)\s+([A-Z]{3}|dollars?|euros?|pounds?)'
    ]
    
    # Search for patterns in text
    for pattern in financial_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            groups = match.groups()
            
            # Determine which group is the currency and which is the value
            currency_indicator = None
            value_str = None
            
            # Check if first group looks like a currency
            first_group = groups[0].strip().upper()
            if first_group in currency_patterns or any(first_group in patterns for patterns in currency_patterns.values()):
                currency_indicator = first_group
                value_str = groups[1]
            else:
                # Second group must be the currency
                currency_indicator = groups[1].strip().upper()
                value_str = groups[0]
            
            # Clean up the value string
            if value_str:
                # Handle million/billion indicators
                million_multiplier = 1
                if 'M' in value_str.upper() or 'MILLION' in value_str.upper() or 'million' in text.lower():
                    million_multiplier = 1000000
                    value_str = value_str.upper().replace('M', '').replace('MILLION', '')
                elif 'B' in value_str.upper() or 'BILLION' in value_str.upper() or 'billion' in text.lower():
                    million_multiplier = 1000000000
                    value_str = value_str.upper().replace('B', '').replace('BILLION', '')
                
                # Extract just digits and decimal point
                value_str = re.sub(r'[^\d\.]', '', value_str.replace(',', ''))
                
                try:
                    value = float(value_str) * million_multiplier
                    
                    # Map currency indicator to standard code
                    currency = None
                    for code, indicators in currency_patterns.items():
                        if any(indicator.upper() == currency_indicator.upper() or 
                               indicator.upper() in currency_indicator.upper() for indicator in indicators):
                            currency = code
                            break
                    
                    if currency:
                        return value, currency
                except (ValueError, TypeError):
                    continue
    
    # Look for numeric-only amounts without explicit currency if context suggests a currency
    if 'rwandan francs' in text.lower() or 'rwf' in text.lower():
        amount_pattern = r'([\d,\.]+)(?:\s*million|\s*billion)?'
        matches = re.findall(amount_pattern, text)
        if matches:
            try:
                value_str = matches[0].replace(',', '')
                multiplier = 1
                if 'million' in text.lower():
                    multiplier = 1000000
                elif 'billion' in text.lower():
                    multiplier = 1000000000
                value = float(value_str) * multiplier
                return value, 'RWF'
            except (ValueError, IndexError):
                pass
    
    return None, None

def format_for_logging(data: Dict[str, Any]) -> str:
    """
    Format data for logging, handling special types and truncating long values.
    
    Args:
        data: Dictionary of data to format
        
    Returns:
        Formatted string
    """
    result = {}
    
    # Process each field
    for key, value in data.items():
        # Skip None values
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
        'Afghanistan': ['Kabul', 'Herat', 'Mazar-i-Sharif', 'Kandahar'],
        'Albania': ['Tirana', 'Durrës', 'Vlorë'],
        'Algeria': ['Algiers', 'Oran', 'Constantine'],
        'Angola': ['Luanda', 'Huambo', 'Lobito'],
        'Argentina': ['Buenos Aires', 'Córdoba', 'Rosario'],
        'Armenia': ['Yerevan', 'Gyumri', 'Vanadzor'],
        'Australia': ['Sydney', 'Melbourne', 'Brisbane', 'Perth', 'Adelaide'],
        'Austria': ['Vienna', 'Graz', 'Linz', 'Salzburg'],
        'Bangladesh': ['Dhaka', 'Chittagong', 'Khulna', 'Rajshahi'],
        'Belgium': ['Brussels', 'Antwerp', 'Ghent', 'Charleroi'],
        'Brazil': ['Brasília', 'São Paulo', 'Rio de Janeiro', 'Salvador'],
        'Cambodia': ['Phnom Penh', 'Siem Reap', 'Battambang'],
        'Canada': ['Ottawa', 'Toronto', 'Montreal', 'Vancouver', 'Calgary'],
        'China': ['Beijing', 'Shanghai', 'Guangzhou', 'Shenzhen', 'Hong Kong'],
        'Colombia': ['Bogotá', 'Medellín', 'Cali', 'Barranquilla'],
        'Democratic Republic of the Congo': ['Kinshasa', 'Lubumbashi', 'Mbuji-Mayi', 'Kisangani'],
        'Egypt': ['Cairo', 'Alexandria', 'Giza', 'Shubra El Kheima'],
        'Ethiopia': ['Addis Ababa', 'Dire Dawa', 'Mek\'ele', 'Adama'],
        'France': ['Paris', 'Marseille', 'Lyon', 'Toulouse', 'Nice'],
        'Germany': ['Berlin', 'Hamburg', 'Munich', 'Cologne', 'Frankfurt'],
        'Ghana': ['Accra', 'Kumasi', 'Tamale', 'Sekondi-Takoradi'],
        'India': ['New Delhi', 'Mumbai', 'Bangalore', 'Hyderabad', 'Chennai'],
        'Indonesia': ['Jakarta', 'Surabaya', 'Bandung', 'Medan', 'Semarang'],
        'Italy': ['Rome', 'Milan', 'Naples', 'Turin', 'Palermo'],
        'Japan': ['Tokyo', 'Yokohama', 'Osaka', 'Nagoya', 'Sapporo'],
        'Kenya': ['Nairobi', 'Mombasa', 'Kisumu', 'Nakuru'],
        'Liberia': ['Monrovia', 'Gbarnga', 'Buchanan', 'Voinjama'],
        'Malawi': ['Lilongwe', 'Blantyre', 'Mzuzu', 'Zomba'],
        'Malaysia': ['Kuala Lumpur', 'George Town', 'Ipoh', 'Johor Bahru'],
        'Mexico': ['Mexico City', 'Guadalajara', 'Monterrey', 'Puebla'],
        'Morocco': ['Rabat', 'Casablanca', 'Fes', 'Marrakesh'],
        'Myanmar': ['Naypyidaw', 'Yangon', 'Mandalay', 'Mawlamyine'],
        'Nepal': ['Kathmandu', 'Pokhara', 'Lalitpur', 'Bhaktapur'],
        'Netherlands': ['Amsterdam', 'Rotterdam', 'The Hague', 'Utrecht'],
        'Nigeria': ['Abuja', 'Lagos', 'Kano', 'Ibadan', 'Port Harcourt'],
        'Pakistan': ['Islamabad', 'Karachi', 'Lahore', 'Faisalabad'],
        'Philippines': ['Manila', 'Quezon City', 'Davao City', 'Cebu City'],
        'Poland': ['Warsaw', 'Kraków', 'Łódź', 'Wrocław'],
        'Russia': ['Moscow', 'Saint Petersburg', 'Novosibirsk', 'Yekaterinburg'],
        'Rwanda': ['Kigali', 'Butare', 'Gitarama', 'Ruhengeri', 'Huye'],
        'Saudi Arabia': ['Riyadh', 'Jeddah', 'Mecca', 'Medina'],
        'Senegal': ['Dakar', 'Thiès', 'Kaolack', 'Saint-Louis'],
        'Serbia': ['Belgrade', 'Novi Sad', 'Niš', 'Kragujevac'],
        'Sierra Leone': ['Freetown', 'Bo', 'Kenema', 'Makeni'],
        'South Africa': ['Pretoria', 'Cape Town', 'Johannesburg', 'Durban'],
        'South Sudan': ['Juba', 'Wau', 'Malakal', 'Yei'],
        'Spain': ['Madrid', 'Barcelona', 'Valencia', 'Seville'],
        'Sri Lanka': ['Colombo', 'Kandy', 'Galle', 'Jaffna'],
        'Sweden': ['Stockholm', 'Gothenburg', 'Malmö', 'Uppsala'],
        'Tanzania': ['Dodoma', 'Dar es Salaam', 'Mwanza', 'Arusha'],
        'Thailand': ['Bangkok', 'Nonthaburi', 'Nakhon Ratchasima', 'Chiang Mai'],
        'Turkey': ['Ankara', 'Istanbul', 'Izmir', 'Bursa'],
        'Uganda': ['Kampala', 'Gulu', 'Lira', 'Mbarara'],
        'Ukraine': ['Kyiv', 'Kharkiv', 'Odesa', 'Dnipro'],
        'United Kingdom': ['London', 'Birmingham', 'Manchester', 'Glasgow'],
        'United States': ['Washington', 'New York', 'Los Angeles', 'Chicago', 'Houston'],
        'Uzbekistan': ['Tashkent', 'Samarkand', 'Namangan', 'Andijan'],
        'Vietnam': ['Hanoi', 'Ho Chi Minh City', 'Hai Phong', 'Da Nang'],
        'Yemen': ['Sana\'a', 'Aden', 'Taiz', 'Hodeidah'],
        'Zambia': ['Lusaka', 'Kitwe', 'Ndola', 'Kabwe'],
        'Zimbabwe': ['Harare', 'Bulawayo', 'Chitungwiza', 'Mutare']
    }
    
    # Create country and city regex patterns
    country_patterns = {country: re.compile(fr'\b{re.escape(country)}\b', re.IGNORECASE) for country in country_city_patterns.keys()}
    city_patterns = {}
    
    for country, cities in country_city_patterns.items():
        for city in cities:
            city_patterns[city] = re.compile(fr'\b{re.escape(city)}\b', re.IGNORECASE)
    
    # Check for country mentions
    country = None
    for country_name, pattern in country_patterns.items():
        if pattern.search(text):
            country = country_name
            break
    
    # Check for city mentions
    city = None
    
    # First try cities from the found country if available
    if country:
        cities = country_city_patterns.get(country, [])
        for city_name in cities:
            if re.search(fr'\b{re.escape(city_name)}\b', text, re.IGNORECASE):
                city = city_name
                break
    
    # If no city found, try all cities
    if not city:
        for city_name, pattern in city_patterns.items():
            if pattern.search(text):
                city = city_name
                break
    
    # Try to extract city using patterns like "City of X" or "X City" or "in X, Country"
    if not city:
        city_extraction_patterns = [
            r'City of ([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)*) City',
            r'in ([A-Z][a-z]+(?:\s[A-Z][a-z]+)*),',
            r'at ([A-Z][a-z]+(?:\s[A-Z][a-z]+)*),',
            r'location: ([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)'
        ]
        
        for pattern in city_extraction_patterns:
            matches = re.findall(pattern, text)
            if matches:
                city = matches[0]
                break
    
    # Handle country/city combinations like "Country - City"
    if not city and country and " - " in text:
        for part in text.split(" - "):
            part = part.strip()
            # Check if this part is a city in our known list
            for known_city in sum(country_city_patterns.values(), []):
                if part.lower() == known_city.lower():
                    city = known_city
                    break
    
    return country, city

def extract_organization(text: str) -> Optional[str]:
    """
    Extract organization name from text.
    
    Args:
        text: Text to extract from
        
    Returns:
        Organization name or None if not found
    """
    if not text or not isinstance(text, str):
        return None
    
    # Common patterns for organization names
    org_patterns = [
        # Government ministries
        r"Ministry of ([A-Z][a-z]+(?:\s+[A-Za-z][a-z]+)*)",
        r"([A-Z][a-z]+(?:\s+[A-Za-z][a-z]+)*) Ministry",
        # Departments
        r"Department of ([A-Z][a-z]+(?:\s+[A-Za-z][a-z]+)*)",
        r"([A-Z][a-z]+(?:\s+[A-Za-z][a-z]+)*) Department",
        # Authorities, agencies, boards, etc.
        r"([A-Z][a-z]+(?:\s+[A-Za-z][a-z]+)*) Authority",
        r"([A-Z][a-z]+(?:\s+[A-Za-z][a-z]+)*) Agency",
        r"([A-Z][a-z]+(?:\s+[A-Za-z][a-z]+)*) Board",
        r"([A-Z][a-z]+(?:\s+[A-Za-z][a-z]+)*) Commission",
        # Offices
        r"Office of ([A-Z][a-z]+(?:\s+[A-Za-z][a-z]+)*)",
        r"([A-Z][a-z]+(?:\s+[A-Za-z][a-z]+)*) Office",
        # Banks, funds
        r"([A-Z][a-z]+(?:\s+[A-Za-z][a-z]+)*) Bank",
        r"([A-Z][a-z]+(?:\s+[A-Za-z][a-z]+)*) Fund",
        # Full organization names (common patterns)
        r"(?:The )?([A-Z][a-z]+(?:\s+[A-Za-z][a-z]+)*) (?:Authority|Agency|Bank|Board|Commission|Corporation|Council|Fund|Group|Institute|Organization|Programme|Project|Service|Trust|Unit)",
        # Client: or buyer: patterns
        r"Client: ([^\.]+)",
        r"Buyer: ([^\.]+)",
        r"Employer: ([^\.]+)",
        r"Procuring entity: ([^\.]+)",
        r"Executing agency: ([^\.]+)"
    ]
    
    # Check each pattern
    for pattern in org_patterns:
        matches = re.findall(pattern, text)
        if matches:
            # Return the first non-empty match
            for match in matches:
                if match and isinstance(match, str) and match.strip():
                    return match.strip()
    
    return None

def extract_procurement_method(text: str) -> Optional[str]:
    """
    Extract procurement method from text.
    
    Args:
        text: Text to extract from
        
    Returns:
        Procurement method or None if not found
    """
    if not text or not isinstance(text, str):
        return None
    
    # Dictionary mapping procurement method patterns to standardized names
    procurement_methods = {
        'International Competitive Bidding': [
            r'\bInternational Competitive Bidding\b', 
            r'\bICB\b'
        ],
        'National Competitive Bidding': [
            r'\bNational Competitive Bidding\b', 
            r'\bNCB\b'
        ],
        'Request for Proposals': [
            r'\bRequest for Proposals\b', 
            r'\bRFP\b'
        ],
        'Quality and Cost-Based Selection': [
            r'\bQuality and Cost-Based Selection\b', 
            r'\bQCBS\b'
        ],
        'Quality-Based Selection': [
            r'\bQuality-Based Selection\b', 
            r'\bQBS\b'
        ],
        'Fixed Budget Selection': [
            r'\bFixed Budget Selection\b', 
            r'\bFBS\b'
        ],
        'Least Cost Selection': [
            r'\bLeast Cost Selection\b', 
            r'\bLCS\b'
        ],
        'Shopping': [
            r'\bShopping\b'
        ],
        'Direct Contracting': [
            r'\bDirect Contracting\b', 
            r'\bSingle Source\b', 
            r'\bSole Source\b'
        ],
        'Request for Quotations': [
            r'\bRequest for Quotations\b', 
            r'\bRFQ\b'
        ],
        'Consultant\'s Qualification Selection': [
            r'\bConsultant\'s Qualification Selection\b', 
            r'\bCQS\b'
        ],
        'Open Procedure': [
            r'\bOpen Procedure\b', 
            r'\bOpen Tender\b', 
            r'\bOpen Bidding\b'
        ],
        'Restricted Procedure': [
            r'\bRestricted Procedure\b', 
            r'\bRestricted Tender\b', 
            r'\bRestricted Bidding\b'
        ],
        'Competitive Dialogue': [
            r'\bCompetitive Dialogue\b'
        ],
        'Negotiated Procedure': [
            r'\bNegotiated Procedure\b'
        ],
        'Competitive Procedure with Negotiation': [
            r'\bCompetitive Procedure with Negotiation\b'
        ],
        'Innovation Partnership': [
            r'\bInnovation Partnership\b'
        ],
        'Framework Agreement': [
            r'\bFramework Agreement\b'
        ],
        'Design Contest': [
            r'\bDesign Contest\b'
        ]
    }
    
    # Check for procurement method mentions
    for method, patterns in procurement_methods.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return method
    
    # Check for shorthand codes
    procurement_codes = {
        'ICB': 'International Competitive Bidding',
        'NCB': 'National Competitive Bidding',
        'RFP': 'Request for Proposals',
        'RFQ': 'Request for Quotations',
        'QCBS': 'Quality and Cost-Based Selection',
        'QBS': 'Quality-Based Selection',
        'FBS': 'Fixed Budget Selection',
        'LCS': 'Least Cost Selection',
        'CQS': 'Consultant\'s Qualification Selection',
        'SSS': 'Single Source Selection',
        'DC': 'Direct Contracting'
    }
    
    # Try to extract code pattern (e.g., "Method: ICB" or "Procurement Method: ICB")
    code_pattern = r'(?:Method|Procurement Method|Procurement Type):\s*([A-Z]{2,5})'
    code_matches = re.search(code_pattern, text)
    if code_matches:
        code = code_matches.group(1)
        if code in procurement_codes:
            return procurement_codes[code]
    
    return None

def extract_status(deadline: Optional[datetime] = None, 
                   status_text: Optional[str] = None, 
                   description: Optional[str] = None) -> Optional[str]:
    """
    Extract or determine status of a tender from various fields.
    
    Args:
        deadline: Deadline date if available
        status_text: Explicit status text if available
        description: Description text to extract status from if other methods fail
        
    Returns:
        Status string or None if unable to determine
    """
    # If explicit status is provided, use specific status mappings
    if status_text:
        status_text = status_text.lower()
        
        # Common status mappings
        if any(term in status_text for term in ['active', 'open', 'ongoing', 'current', 'published']):
            return 'Open'
        elif any(term in status_text for term in ['closed', 'complete', 'awarded', 'finished', 'expired']):
            return 'Closed'
        elif any(term in status_text for term in ['cancel', 'withdrawn', 'suspend']):
            return 'Canceled'
        elif any(term in status_text for term in ['upcoming', 'planned', 'future']):
            return 'Planned'
    
    # Check deadline if available
    if deadline:
        # If deadline has passed, mark as closed
        if deadline < datetime.now():
            return 'Closed'
        else:
            return 'Open'
    
    # Try to extract from description as last resort
    if description:
        description = description.lower()
        
        # Check for status indicators in description
        if any(term in description for term in ['has been awarded', 'contract awarded', 'tender closed', 'bidding closed']):
            return 'Closed'
        elif any(term in description for term in ['is now open', 'bidding open', 'currently accepting', 'submit bid by']):
            return 'Open'
        elif any(term in description for term in ['has been canceled', 'tender canceled', 'bidding canceled']):
            return 'Canceled'
    
    # Unable to determine    
    return None

def log_before_after(source_type: str, source_id: str, before: Dict[str, Any], after: UnifiedTender):
    """
    Log before and after data for a tender.
    
    Args:
        source_type: Source table name
        source_id: Source ID
        before: Original source data
        after: Normalized unified tender
    """
    logger.info(f"NORMALIZING {source_type.upper()} - {source_id}")
    logger.info(f"BEFORE:\n{format_for_logging(before)}")
    logger.info(f"AFTER:\n{format_for_logging(after.model_dump())}")
    logger.info(f"TRANSLATION: {after.normalized_method}")
    logger.info("-" * 80)

def standardize_status(status: str) -> str:
    """
    Standardize status values across different sources.
    
    Args:
        status: Original status string
        
    Returns:
        Standardized status string
    """
    if not status:
        return None
        
    status = status.strip().lower()
    
    # Status mapping to standard values
    status_mapping = {
        # Active statuses
        'active': 'Active',
        'open': 'Open',
        'current': 'Active',
        'ongoing': 'Active',
        'in progress': 'Active',
        'published': 'Published',
        
        # Closed statuses
        'closed': 'Closed',
        'canceled': 'Cancelled',
        'cancelled': 'Cancelled',
        'completed': 'Completed',
        'terminated': 'Cancelled',
        'expired': 'Closed',
        
        # Award statuses
        'awarded': 'Awarded',
        'award': 'Awarded',
        'contract award': 'Awarded',
        'awarded contract': 'Awarded',
        'contract awarded': 'Awarded',
        
        # Pending statuses
        'pending': 'Pending',
        'evaluation': 'Under Evaluation',
        'under evaluation': 'Under Evaluation',
        'evaluating': 'Under Evaluation',
        
        # Draft statuses
        'draft': 'Draft',
        'planned': 'Planned',
        'planning': 'Planned',
        
        # Other statuses
        'request for quotation': 'Open',
        'request for proposal': 'Open',
        'request for information': 'Open',
        'request for interest': 'Open'
    }
    
    # Try exact match first
    if status in status_mapping:
        return status_mapping[status]
    
    # Try partial match if exact match fails
    for key, value in status_mapping.items():
        if key in status:
            return value
    
    # Handle special cases with keyword detection
    if any(keyword in status for keyword in ['rfp', 'rfq', 'rfi', 'tender']):
        return 'Open'
    
    if any(keyword in status for keyword in ['award', 'awarded', 'contract']):
        return 'Awarded'
    
    # Default to returning the original status with proper capitalization
    return status.title()

def extract_sector_info(text: str) -> str:
    """
    Extract sector information from text.
    
    Args:
        text: Text to extract sector information from
        
    Returns:
        Extracted sector or None if not found
    """
    if not text:
        return None
        
    # Common sectors in procurement/tender notices
    sector_patterns = {
        'Agriculture': ['agriculture', 'farming', 'irrigation', 'crops', 'livestock', 'fishery'],
        'Construction': ['construction', 'building', 'infrastructure', 'housing', 'roads', 'bridges', 'facility'],
        'Education': ['education', 'school', 'university', 'teaching', 'training', 'academic'],
        'Energy': ['energy', 'power', 'electricity', 'renewable', 'solar', 'wind', 'hydro', 'electric'],
        'Environment': ['environment', 'climate', 'green', 'sustainability', 'recycling', 'waste management'],
        'Finance': ['finance', 'banking', 'investment', 'financial', 'insurance', 'accounting'],
        'Health': ['health', 'medical', 'hospital', 'clinic', 'pharmaceutical', 'drugs', 'medicine'],
        'ICT': ['ict', 'information technology', 'computer', 'software', 'hardware', 'network', 'digital', 'telecommunications'],
        'Manufacturing': ['manufacturing', 'industrial', 'factory', 'production', 'processing'],
        'Mining': ['mining', 'minerals', 'extraction', 'coal', 'ore', 'metals', 'geological'],
        'Transportation': ['transport', 'transportation', 'logistics', 'airport', 'railway', 'road', 'shipping', 'vehicles'],
        'Water': ['water', 'sanitation', 'sewage', 'drainage', 'plumbing', 'hygiene'],
        'Social Development': ['social', 'welfare', 'community', 'poverty', 'gender', 'youth', 'empowerment'],
        'Defense': ['defense', 'defence', 'military', 'security', 'army', 'navy', 'air force', 'weapons'],
        'Tourism': ['tourism', 'hospitality', 'hotel', 'travel', 'leisure']
    }
    
    # Check for sector indicators in the text
    text_lower = text.lower()
    matches = []
    
    for sector, keywords in sector_patterns.items():
        for keyword in keywords:
            if keyword in text_lower:
                # Calculate a confidence score based on frequency and context
                count = text_lower.count(keyword)
                # Check if term appears as a standalone word, not substring
                standalone = False
                try:
                    standalone = bool(re.search(r'\b' + re.escape(keyword) + r'\b', text_lower))
                except Exception:
                    # In case of regex errors (e.g., with special characters)
                    pass
                
                confidence = count * (2 if standalone else 1)
                matches.append((sector, confidence))
                break  # Only count each sector once
    
    if matches:
        # Sort by confidence score and return the highest one
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[0][0]
    
    # Try to extract sector from common phrases
    sector_phrases = [
        (r'sector:\s*([A-Za-z\s&]+?)(?:\.|,|\n)', 1),
        (r'in the\s+([A-Za-z\s&]+?)\s+sector', 1),
        (r'([A-Za-z\s&]+?)\s+sector', 1)
    ]
    
    for pattern, group in sector_phrases:
        try:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                potential_sector = match.group(group).strip()
                # Check if it's not just a generic word
                if len(potential_sector) > 3 and potential_sector.lower() not in ['this', 'the', 'and', 'for', 'from']:
                    return potential_sector
        except Exception:
            # Skip this pattern if regex fails
            continue
    
    return None 