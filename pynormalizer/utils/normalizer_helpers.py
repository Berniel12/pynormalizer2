"""
Helper functions for normalizers.
"""
import json
import logging
import re
from typing import Any, Dict, Optional, Tuple, List, Union
from datetime import datetime, date
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
    
    # Define common currency codes and symbols with expanded variations
    currency_patterns = {
        'USD': ['USD', 'US$', '$', 'Dollar', 'Dollars', 'US Dollar', 'U.S. Dollar'],
        'EUR': ['EUR', '€', 'Euro', 'Euros', 'euro', 'euros'],
        'GBP': ['GBP', '£', 'Pound', 'Pounds', 'Sterling', 'British Pound'],
        'JPY': ['JPY', '¥', 'Yen', 'Japanese Yen'],
        'CNY': ['CNY', 'RMB', 'Yuan', 'Chinese Yuan'],
        'INR': ['INR', '₹', 'Rupee', 'Rupees', 'Indian Rupee'],
        'MWK': ['MWK', 'Malawi Kwacha', 'Kwacha'],
        'AUD': ['AUD', 'AU$', 'Australian Dollar', 'A$'],
        'CAD': ['CAD', 'CA$', 'Canadian Dollar', 'C$'],
        'CHF': ['CHF', 'Swiss Franc', 'Fr'],
        'XAF': ['XAF', 'CFA Franc', 'FCFA', 'Franc CFA'],
        'NGN': ['NGN', '₦', 'Naira'],
        'ZAR': ['ZAR', 'R', 'Rand', 'South African Rand'],
        'KES': ['KES', 'KSh', 'Kenyan Shilling', 'Shilling'],
        'BRL': ['BRL', 'R$', 'Real', 'Reais'],
        'RWF': ['RWF', 'Rwf', 'RF', 'FRw', 'Rwandan Francs', 'Rwandan Franc'],
        'TZS': ['TZS', 'TSh', 'Tanzanian Shilling'],
        'UGX': ['UGX', 'USh', 'Ugandan Shilling'],
        'ETB': ['ETB', 'Birr', 'Ethiopian Birr'],
    }
    
    # Check for specific currency patterns with values
    # First check for Rwanda Franc which is often misidentified
    rwandan_franc_patterns = [
        # Various Rwandan Franc patterns with values
        r'(?:RF|Rwf|RWF|FRw)[\s\:]*([\d,\.]+(?:\s*(?:million|m|billion|b))?)',
        r'([\d,\.]+(?:\s*(?:million|m|billion|b))?)[\s\:]?(?:RF|Rwf|RWF|FRw)',
        r'(?:Rwandan Franc[s]?)[\s\:]*([\d,\.]+(?:\s*(?:million|m|billion|b))?)',
        r'([\d,\.]+(?:\s*(?:million|m|billion|b))?)[\s\:]?(?:Rwandan Franc[s]?)',
    ]
    
    for pattern in rwandan_franc_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            for match in matches:
                try:
                    # Process the value
                    value_str = match.replace(',', '')
                    multiplier = 1
                    
                    # Check for million/billion indicators
                    if re.search(r'million|m\b', value_str, re.IGNORECASE):
                        multiplier = 1000000
                        value_str = re.sub(r'million|m\b', '', value_str, flags=re.IGNORECASE).strip()
                    elif re.search(r'billion|b\b', value_str, re.IGNORECASE):
                        multiplier = 1000000000
                        value_str = re.sub(r'billion|b\b', '', value_str, flags=re.IGNORECASE).strip()
                    
                    value = float(value_str) * multiplier
                    return value, 'RWF'
                except (ValueError, TypeError):
                    continue
    
    # General currency patterns
    # Pattern 1: Currency code/symbol followed by value
    currency_value_pattern = r'([A-Z]{3}|[€£$¥₹₦])\s*([\d,\.]+(?:\s*(?:million|m|billion|b))?)'
    
    # Pattern 2: Value followed by currency code/name
    value_currency_pattern = r'([\d,\.]+(?:\s*(?:million|m|billion|b))?)\s*([A-Z]{3}|[€£$¥₹₦]|dollars?|euros?|pounds?|yen|yuan|franc)'
    
    # Pattern 3: Value with M/B suffix (e.g., $1.5M, 1.5B EUR)
    value_suffix_pattern = r'([A-Z]{3}|[€£$¥₹₦])\s*([\d,\.]+[MB])'
    suffix_value_pattern = r'([\d,\.]+[MB])\s*([A-Z]{3}|[€£$¥₹₦]|dollars?|euros?|pounds?|yen|yuan|franc)'
    
    # Pattern 4: X million/billion [Currency]
    million_pattern = r'([\d,\.]+)\s+(?:million|billion)\s+([A-Z]{3}|dollars?|euros?|pounds?|francs?|yen|yuan)'
    
    # Pattern 5: Contract value/amount/price pattern
    contract_value_pattern = r'(?:contract|estimated) (?:value|amount|price|cost)[:\s]+([\d,\.]+\s*(?:million|m|billion|b)?)[:\s]*([A-Z]{3}|[€£$¥₹₦])?'
    contract_value_inv_pattern = r'(?:contract|estimated) (?:value|amount|price|cost)[:\s]*([A-Z]{3}|[€£$¥₹₦])?\s*([\d,\.]+\s*(?:million|m|billion|b)?)'
    
    # Try all patterns in sequence
    patterns = [
        (currency_value_pattern, 0, 1),  # (pattern, currency_group, value_group)
        (value_currency_pattern, 1, 0),
        (value_suffix_pattern, 0, 1),
        (suffix_value_pattern, 1, 0),
        (million_pattern, 1, 0),
        (contract_value_pattern, 1, 0),
        (contract_value_inv_pattern, 0, 1)
    ]
    
    for pattern_info in patterns:
        pattern, currency_group, value_group = pattern_info
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        for match in matches:
            try:
                groups = match.groups()
                if len(groups) < 2:
                    continue
                    
                currency_indicator = groups[currency_group].strip()
                value_str = groups[value_group].strip()
                
                # Process the value
                multiplier = 1
                if re.search(r'million|m\b', value_str, re.IGNORECASE) or re.search(r'million|m\b', match.group(0), re.IGNORECASE):
                    multiplier = 1000000
                    value_str = re.sub(r'million|m\b', '', value_str, flags=re.IGNORECASE).strip()
                elif re.search(r'billion|b\b', value_str, re.IGNORECASE) or re.search(r'billion|b\b', match.group(0), re.IGNORECASE):
                    multiplier = 1000000000
                    value_str = re.sub(r'billion|b\b', '', value_str, flags=re.IGNORECASE).strip()
                
                # Handle M/B suffixes
                if value_str.upper().endswith('M'):
                    multiplier = 1000000
                    value_str = value_str[:-1]
                elif value_str.upper().endswith('B'):
                    multiplier = 1000000000
                    value_str = value_str[:-1]
                
                # Clean value string and convert to float
                value_str = re.sub(r'[^\d\.]', '', value_str.replace(',', ''))
                value = float(value_str) * multiplier
                
                # Map currency indicator to standard code
                currency = None
                for code, indicators in currency_patterns.items():
                    if any(indicator.upper() == currency_indicator.upper() or currency_indicator.upper() in indicator.upper() for indicator in indicators):
                        currency = code
                        break
                        
                # If found currency with value, return it
                if currency and value:
                    return value, currency
            except (ValueError, TypeError, IndexError):
                continue
    
    # Fallback pattern: look for standalone monetary values with default currency
    # Try to guess currency from context if value found
    value_only_pattern = r'(?:value|amount|cost|price)[:]\s*([\d,\.]+\s*(?:million|m|billion|b)?)'
    value_only_matches = re.findall(value_only_pattern, text, re.IGNORECASE)
    
    if value_only_matches:
        try:
            value_str = value_only_matches[0]
            multiplier = 1
            
            if re.search(r'million|m\b', value_str, re.IGNORECASE):
                multiplier = 1000000
                value_str = re.sub(r'million|m\b', '', value_str, flags=re.IGNORECASE).strip()
            elif re.search(r'billion|b\b', value_str, re.IGNORECASE):
                multiplier = 1000000000
                value_str = re.sub(r'billion|b\b', '', value_str, flags=re.IGNORECASE).strip()
            
            value_str = re.sub(r'[^\d\.]', '', value_str.replace(',', ''))
            value = float(value_str) * multiplier
            
            # Try to detect currency from context
            currency = None
            text_lower = text.lower()
            
            # Default country-currency mapping
            if 'rwanda' in text_lower:
                currency = 'RWF'
            elif 'kenya' in text_lower:
                currency = 'KES'
            elif 'tanzania' in text_lower:
                currency = 'TZS'
            elif 'uganda' in text_lower:
                currency = 'UGX'
            elif 'south africa' in text_lower:
                currency = 'ZAR'
            elif 'nigeria' in text_lower:
                currency = 'NGN'
            elif 'ethiopia' in text_lower:
                currency = 'ETB'
            elif 'india' in text_lower:
                currency = 'INR'
            elif 'euro' in text_lower or 'eur' in text_lower:
                currency = 'EUR'
            elif 'dollar' in text_lower or 'usd' in text_lower:
                currency = 'USD'
            elif 'pound' in text_lower or 'gbp' in text_lower:
                currency = 'GBP'
            
            if value and currency:
                return value, currency
            elif value:
                # Default to USD if currency can't be determined but value exists
                return value, 'USD'
                
        except (ValueError, TypeError, IndexError):
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

def extract_organization_and_buyer(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract organization and buyer information from text.
    
    Args:
        text: Text to extract organization and buyer information from
        
    Returns:
        Tuple of (organization_name, buyer)
    """
    if not text:
        return None, None
    
    organization_name = None
    buyer = None
    
    # Extract organization patterns
    org_patterns = [
        # Common organization intro phrases
        r'(?:by|from|for|issued by|on behalf of)\s+([A-Za-z0-9\s\(\)&,\.\-\']{5,50}?)(?:\s+in|\s+for|\s+at|\s+\(|\.|$)',
        # Organization followed by action
        r'([A-Za-z0-9\s\(\)&,\.\-\']{5,50}?)\s+(?:invites|announces|requests|is seeking|has issued)',
        # Explicit mentions
        r'(?:implementing agency|contracting authority|issuing authority|procurement entity|client)[\s\:]+([A-Za-z0-9\s\(\)&,\.\-\']{5,50}?)(?:\s+|\.|$)',
        # Specific to World Bank/ADB
        r'(?:borrower|recipient|purchaser)[\s\:]+([A-Za-z0-9\s\(\)&,\.\-\']{5,50}?)(?:\s+|\.|$)',
        # For buyer/client specific patterns
        r'(?:buyer|client|purchaser|employer)[\s\:]+([A-Za-z0-9\s\(\)&,\.\-\']{5,50}?)(?:\s+|\.|$)',
        # Awarded to pattern
        r'(?:awarded to|contract awarded to)[\s\:]+([A-Za-z0-9\s\(\)&,\.\-\']{5,50}?)(?:\s+|\.|$)'
    ]
    
    # Try each pattern for organization
    for pattern in org_patterns[:4]:  # First 4 patterns are for organizations
        try:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches:
                    potential_org = match.strip()
                    # Filter out false positives
                    if (len(potential_org) > 4 and 
                        potential_org.lower() not in ['the', 'this', 'that', 'these', 'those', 'their', 'our'] and
                        not re.match(r'^\d+$', potential_org)):
                        organization_name = potential_org
                        break
                if organization_name:
                    break
        except Exception:
            continue
    
    # Try buyer-specific patterns
    for pattern in org_patterns[4:]:  # Last 2 patterns are for buyers
        try:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches:
                    potential_buyer = match.strip()
                    # Filter out false positives
                    if (len(potential_buyer) > 4 and 
                        potential_buyer.lower() not in ['the', 'this', 'that', 'these', 'those', 'their', 'our'] and
                        not re.match(r'^\d+$', potential_buyer)):
                        buyer = potential_buyer
                        break
                if buyer:
                    break
        except Exception:
            continue
    
    # Special case for World Bank awarded contracts
    awarded_pattern = r'Awarded Bidder\(s\):\s*([A-Za-z0-9\s\(\)&,\.\-\']{5,50}?)(?:,|\(|$)'
    if not buyer:
        awarded_match = re.search(awarded_pattern, text)
        if awarded_match:
            buyer = awarded_match.group(1).strip()
    
    # If we have only a buyer but no organization, set organization to buyer
    if buyer and not organization_name:
        organization_name = buyer
    
    # Handle country prefixes in organization names (e.g., "RWANDA - Organization Name")
    if organization_name:
        country_prefix_match = re.match(r'^([A-Z]{2,})\s*-\s*(.+)$', organization_name)
        if country_prefix_match:
            country_code = country_prefix_match.group(1).strip()
            org_name = country_prefix_match.group(2).strip()
            
            # Only separate if first part looks like a country code
            if len(country_code) > 3 and country_code not in ['UNDP', 'UNEP', 'UNHCR', 'UNICEF', 'WHO', 'FAO', 'IBRD', 'ADB', 'AIIB', 'IFC']:
                organization_name = org_name
    
    # Clean up names
    if organization_name:
        organization_name = re.sub(r'\s+', ' ', organization_name).strip()
    if buyer:
        buyer = re.sub(r'\s+', ' ', buyer).strip()
    
    return organization_name, buyer

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
                   description: Optional[str] = None,
                   publication_date: Optional[datetime] = None) -> Optional[str]:
    """
    Determine the status of a tender based on the deadline, status text, and description.
    
    Args:
        deadline: Deadline date for the tender
        status_text: Explicit status text if available
        description: Description text to extract status from
        publication_date: Publication date for the tender
        
    Returns:
        Standardized status string or None if cannot be determined
    """
    # Current time for comparison
    now = datetime.now()
    
    # If explicit status text is provided, standardize it
    if status_text:
        return standardize_status(status_text)
    
    # Check for status keywords in description
    if description:
        # Look for common status phrases
        status_patterns = {
            r'(?:tender|bid) (?:status|is)\s*(?::|is)?\s*(active|open|closed|cancelled|canceled|awarded|complete|in progress|pending|published)': 1,
            r'status\s*(?::|is)?\s*(active|active & open|open|closed|cancelled|canceled|awarded|complete|completed|under review|in progress|pending|published)': 1,
            r'(?:this|the) (?:tender|opportunity) is (active|open|closed|cancelled|canceled|awarded|complete|in progress|pending|published)': 1,
            r'(?:project|procurement) status\s*(?::|is)?\s*(active|open|closed|cancelled|canceled|awarded|complete|in progress|pending|published)': 1,
            # World Bank "Status: Active" pattern in project_number field
            r'Status:\s*(Active|Open|Closed|Cancelled|Canceled|Awarded|Complete|In Progress|Pending|Published)': 1
        }
        
        for pattern, group in status_patterns.items():
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                found_status = match.group(group).strip().lower()
                return standardize_status(found_status)
        
        # Check for contract award language
        if re.search(r'contract(?:\s+has been)?\s+awarded', description, re.IGNORECASE):
            return "Awarded"
        
        # Check for cancellation language
        if re.search(r'(?:tender|bid|procurement)(?:\s+has been)?\s+cancelled', description, re.IGNORECASE) or \
           re.search(r'(?:tender|bid|procurement)(?:\s+has been)?\s+canceled', description, re.IGNORECASE):
            return "Cancelled"
    
    # Determine status based on deadline
    if deadline:
        if deadline > now:
            return "Open"
        else:
            return "Closed"
    
    # Use publication date as fallback
    if publication_date:
        # If published in the last 30 days and no deadline, assume Open
        thirty_days = 30 * 24 * 60 * 60  # 30 days in seconds
        if (now - publication_date).total_seconds() < thirty_days:
            return "Open"
        else:
            # If older than 30 days and no deadline, assume Closed
            return "Closed"
    
    # Default status if no other information
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
    Standardize a status string to a common format.
    
    Args:
        status: Raw status string
        
    Returns:
        Standardized status string
    """
    if not status:
        return None
        
    status_lower = status.lower().strip()
    
    # Standardized status mapping
    status_map = {
        # Open/Active statuses
        'open': 'Open',
        'active': 'Open',
        'active & open': 'Open',
        'published': 'Open',
        'current': 'Open',
        'ongoing': 'Open',
        'live': 'Open',
        'in progress': 'Open',
        'accepting': 'Open',
        'accepting bids': 'Open',
        'active & published': 'Open',
        'posted': 'Open',
        'soliciting': 'Open',
        
        # Closed statuses
        'closed': 'Closed',
        'complete': 'Closed',
        'completed': 'Closed',
        'expired': 'Closed',
        'finished': 'Closed',
        'ended': 'Closed',
        'terminated': 'Closed',
        'deadline passed': 'Closed',
        
        # Awarded statuses
        'awarded': 'Awarded', 
        'contract awarded': 'Awarded',
        'award': 'Awarded',
        'completed and awarded': 'Awarded',
        'closed and awarded': 'Awarded',
        
        # Cancelled statuses
        'cancelled': 'Cancelled',
        'canceled': 'Cancelled',
        'withdrawn': 'Cancelled',
        'suspended': 'Cancelled',
        'discontinued': 'Cancelled',
        'terminated early': 'Cancelled',
        
        # Draft/Planned statuses
        'draft': 'Planned',
        'planning': 'Planned',
        'planned': 'Planned',
        'upcoming': 'Planned',
        'scheduled': 'Planned',
        'future': 'Planned',
        'not yet published': 'Planned',
        'pre-solicitation': 'Planned',
        
        # Special statuses
        'under review': 'Under Review',
        'pending': 'Pending',
        'evaluation': 'Under Review',
        'evaluating': 'Under Review',
        'inactive': 'Inactive'
    }
    
    # First, check for exact matches in the standardized statuses
    if status_lower in status_map:
        return status_map[status_lower]
    
    # If not an exact match, check for key terms within the status
    for key_term, std_status in status_map.items():
        if key_term in status_lower:
            return std_status
    
    # Check specific patterns with phrases
    if any(term in status_lower for term in ['award', 'awarded', 'contract awarded']):
        return 'Awarded'
    elif any(term in status_lower for term in ['cancel', 'cancelled', 'canceled', 'withdraw']):
        return 'Cancelled'
    elif any(term in status_lower for term in ['review', 'evaluation', 'evaluating', 'processing']):
        return 'Under Review'
    
    # If no match found, return capitalized status as fallback
    words = status.split()
    capitalized = ' '.join(word.capitalize() for word in words)
    return capitalized

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

def parse_date_from_text(text: str) -> Optional[datetime]:
    """
    Extract and parse dates from text using various patterns.
    
    Args:
        text: Text containing date information
        
    Returns:
        Parsed datetime or None if no date found
    """
    if not text:
        return None
        
    # Handle common date formats in text
    date_patterns = [
        # Formal date patterns
        r'(?:deadline|due date|closing date|submission date)[:\s]+(\d{1,2}[\s\-\.]+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\-\.]+\d{4})',
        r'(?:deadline|due date|closing date|submission date)[:\s]+(\d{1,2}[\s\-\.]+(?:January|February|March|April|May|June|July|August|September|October|November|December)[a-z]*[\s\-\.]+\d{4})',
        r'(?:deadline|due date|closing date|submission date)[:\s]+(\d{4}[\s\-\.]+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\-\.]+\d{1,2})',
        r'(?:deadline|due date|closing date|submission date)[:\s]+(\d{4}[\s\-\.]+(?:January|February|March|April|May|June|July|August|September|October|November|December)[a-z]*[\s\-\.]+\d{1,2})',
        
        # Date in format DD Month YYYY
        r'(\d{1,2}(?:st|nd|rd|th)?[\s\-\.]+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\-\.]+\d{4})',
        r'(\d{1,2}(?:st|nd|rd|th)?[\s\-\.]+(?:January|February|March|April|May|June|July|August|September|October|November|December)[a-z]*[\s\-\.]+\d{4})',
        
        # Date in format Month DD, YYYY
        r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\-\.]+\d{1,2}(?:st|nd|rd|th)?[\s\,\-\.]+\d{4})',
        r'((?:January|February|March|April|May|June|July|August|September|October|November|December)[a-z]*[\s\-\.]+\d{1,2}(?:st|nd|rd|th)?[\s\,\-\.]+\d{4})',
        
        # Date in format YYYY/MM/DD or YYYY-MM-DD
        r'(\d{4}[\s\-\.\/]+\d{1,2}[\s\-\.\/]+\d{1,2})',
        
        # Date in format DD/MM/YYYY or DD-MM-YYYY
        r'(\d{1,2}[\s\-\.\/]+\d{1,2}[\s\-\.\/]+\d{4})'
    ]
    
    # Try each pattern
    for pattern in date_patterns:
        try:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                date_str = matches[0].strip()
                
                # Try multiple date formats
                date_formats = [
                    "%d %b %Y", "%d %B %Y", 
                    "%b %d, %Y", "%B %d, %Y",
                    "%d-%b-%Y", "%d-%B-%Y",
                    "%d.%m.%Y", "%m.%d.%Y",
                    "%d/%m/%Y", "%m/%d/%Y",
                    "%Y-%m-%d", "%Y/%m/%d",
                    "%d %m %Y", "%m %d %Y",
                    "%Y %m %d"
                ]
                
                # Clean up the date string
                date_str = re.sub(r'(?:st|nd|rd|th)', '', date_str)
                date_str = re.sub(r'\s+', ' ', date_str)
                date_str = date_str.strip()
                
                # Try each format
                for fmt in date_formats:
                    try:
                        dt = datetime.strptime(date_str, fmt)
                        return dt
                    except ValueError:
                        continue
        except Exception as e:
            logger.debug(f"Error parsing date from pattern {pattern}: {e}")
            continue
    
    # Special case for "Status: Active    Deadline: 13 Mar 2025" format
    deadline_match = re.search(r'Deadline:?\s*(\d{1,2}\s+[A-Za-z]{3,}\s+\d{4})', text)
    if deadline_match:
        deadline_str = deadline_match.group(1).strip()
        try:
            return datetime.strptime(deadline_str, "%d %b %Y")
        except ValueError:
            try:
                return datetime.strptime(deadline_str, "%d %B %Y")
            except ValueError:
                pass
    
    return None

def parse_date_string(date_str: Optional[Union[str, datetime, date]]) -> Optional[datetime]:
    """
    Parse a date string in various formats into a datetime object.
    
    Args:
        date_str: Date string to parse
        
    Returns:
        Parsed datetime or None if parsing fails
    """
    if not date_str:
        return None
        
    # If already a datetime or date, convert/return it
    if isinstance(date_str, datetime):
        return date_str
    elif isinstance(date_str, date):
        return datetime.combine(date_str, datetime.min.time())
    
    # For string dates, try multiple formats
    if isinstance(date_str, str):
        # Strip any timezone indicators for simpler parsing
        clean_date_str = date_str.strip().split('+')[0].split('Z')[0].strip()
        
        # Try ISO format first
        try:
            return datetime.fromisoformat(clean_date_str)
        except (ValueError, TypeError):
            pass
        
        # Try common formats
        date_formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%d-%m-%Y",
            "%m-%d-%Y",
            "%d %b %Y",
            "%d %B %Y",
            "%b %d, %Y",
            "%B %d, %Y"
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(clean_date_str, fmt)
            except (ValueError, TypeError):
                continue
        
        # Try to extract a date from text
        return parse_date_from_text(clean_date_str)
    
    return None 

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
        
    # Use the new enhanced function and return just the organization
    organization_name, _ = extract_organization_and_buyer(text)
    return organization_name 

def ensure_country(country: Optional[str], 
                  text: Optional[str] = None, 
                  organization: Optional[str] = None,
                  email: Optional[str] = None,
                  language: Optional[str] = None) -> str:
    """
    Ensure country is not empty, using various fallback strategies.
    
    Args:
        country: Current country value (may be None or empty)
        text: Text to extract country from if country is empty
        organization: Organization name to extract country from if country is empty
        email: Email to extract domain country from if country is empty
        language: Language to guess country from if country is empty
        
    Returns:
        Non-empty country string, with "Unknown" as last resort
    """
    # If country already exists, return it
    if country:
        return country
    
    # Attempt to extract from text if available
    if text:
        extracted_country, _ = extract_location_info(text)
        if extracted_country:
            return extracted_country
    
    # Try to extract from organization name if contains country prefix
    if organization:
        country_prefix_match = re.match(r'^([A-Z]{3,})\s*-\s*', organization)
        if country_prefix_match:
            country_code = country_prefix_match.group(1).strip()
            # Skip organization abbreviations
            if country_code not in ['UNDP', 'UNEP', 'UNHCR', 'UNICEF', 'WHO', 'FAO', 'IBRD', 'ADB', 'AIIB', 'IFC']:
                return country_code
    
    # Try to extract from email domain if available
    if email and '@' in email:
        domain = email.split('@')[1]
        tld = domain.split('.')[-1].lower()
        
        # Map common TLDs to countries
        tld_country_map = {
            'uk': 'United Kingdom',
            'fr': 'France',
            'de': 'Germany',
            'it': 'Italy',
            'es': 'Spain',
            'ru': 'Russia',
            'jp': 'Japan',
            'cn': 'China',
            'in': 'India',
            'br': 'Brazil',
            'ca': 'Canada',
            'au': 'Australia',
            'za': 'South Africa',
            'ke': 'Kenya',
            'ng': 'Nigeria',
            'mx': 'Mexico',
            'kr': 'South Korea',
            'nl': 'Netherlands',
            'se': 'Sweden',
            'no': 'Norway',
            'dk': 'Denmark',
            'fi': 'Finland',
            'pl': 'Poland',
            'ua': 'Ukraine',
            'gr': 'Greece',
            'rw': 'Rwanda',
            'lv': 'Latvia',
            'lt': 'Lithuania',
            'et': 'Estonia',
            'tr': 'Turkey'
        }
        
        if tld in tld_country_map:
            return tld_country_map[tld]
        
        # For gov domains, check for country prefix (e.g., ke.gov, rw.gov)
        if 'gov' in domain.split('.'):
            for country_code in tld_country_map.keys():
                if country_code + '.gov' in domain:
                    return tld_country_map[country_code]
    
    # Try to guess from language if available
    if language:
        # Map common languages to primary countries
        language_country_map = {
            'en': 'United States',  # Default for English
            'fr': 'France',
            'es': 'Spain',
            'de': 'Germany',
            'it': 'Italy',
            'pt': 'Portugal',
            'ru': 'Russia',
            'zh': 'China',
            'ja': 'Japan',
            'ko': 'South Korea',
            'ar': 'Saudi Arabia',
            'hi': 'India',
            'lv': 'Latvia',
            'lt': 'Lithuania',
            'et': 'Estonia',
            'fi': 'Finland',
            'sv': 'Sweden',
            'no': 'Norway',
            'da': 'Denmark',
            'nl': 'Netherlands',
            'el': 'Greece',
            'tr': 'Turkey',
            'pl': 'Poland',
            'cs': 'Czech Republic',
            'sk': 'Slovakia',
            'hu': 'Hungary',
            'uk': 'Ukraine',
            'ro': 'Romania',
            'bg': 'Bulgaria',
            'sr': 'Serbia',
            'hr': 'Croatia',
            'sl': 'Slovenia'
        }
        
        if language in language_country_map:
            return language_country_map[language]
    
    # Last resort: return "Unknown" to ensure field is not empty
    return "Unknown" 