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
import traceback

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

def extract_financial_info(text: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Extract financial information (amount and currency) from text.
    
    Args:
        text: Text to extract financial information from
        
    Returns:
        Tuple of (amount as float, currency code)
    """
    if not text:
            return None, None
        
    # Define currency symbols and their corresponding codes
    currency_symbols = {
        '$': 'USD',
        '€': 'EUR',
        '£': 'GBP',
        '¥': 'JPY',
        '₹': 'INR',
        '₽': 'RUB',
        '₩': 'KRW',
        '₴': 'UAH',
        '₺': 'TRY',
        'R$': 'BRL',
        'C$': 'CAD',
        'A$': 'AUD',
        'HK$': 'HKD',
        'S$': 'SGD',
        'Fr': 'CHF',
        'zł': 'PLN',
        'kr': 'SEK',  # Note: could also be NOK or DKK
        '₦': 'NGN',
        '₱': 'PHP',
        'RM': 'MYR',
        '฿': 'THB',
        '₫': 'VND',
        'KSh': 'KES',
        'RWF': 'RWF',
        'TZS': 'TZS',
        'UGX': 'UGX',
        'ETB': 'ETB',
        'ZAR': 'ZAR',
        'Kč': 'CZK',
        'Ft': 'HUF',
        'lei': 'RON'
    }
    
    # Define currency codes that might appear in text (for cases without symbols)
    currency_codes = [
        'USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD', 
        'INR', 'RUB', 'CNY', 'BRL', 'MXN', 'ZAR', 'SGD', 'HKD', 
        'KRW', 'TRY', 'SEK', 'NOK', 'DKK', 'PLN', 'CZK', 'HUF', 
        'RON', 'BGN', 'HRK', 'ISK', 'ILS', 'SAR', 'AED', 'THB', 
        'MYR', 'IDR', 'PHP', 'TWD', 'KES', 'NGN', 'EGP', 'PKR', 
        'BDT', 'VND', 'UAH', 'COP', 'ARS', 'PEN', 'CLP', 'CRC',
        'RWF', 'UGX', 'TZS', 'ETB', 'MAD', 'DZD', 'TND', 'GHS',
        'XOF', 'XAF', 'XPF'
    ]
    
    # Patterns for financial information
    patterns = []
    
    # Pattern with currency symbol before amount: $1,000,000.00 or $1M or $1.5 million
    for symbol, code in currency_symbols.items():
        # Escape special regex characters in symbol
        escaped_symbol = re.escape(symbol)
        
        # Match symbol followed by amount with commas/decimals
        patterns.append(
            (rf'{escaped_symbol}\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*(?:million|m|billion|b|trillion|t)?', code)
        )
        
        # Match symbol followed by amount with M/B/T suffix
        patterns.append(
            (rf'{escaped_symbol}\s*(\d+(?:\.\d+)?)\s*(?:M|Mio|Mill|Million|B|Bio|Bill|Billion|T|Trill|Trillion)', code)
        )
    
    # Pattern with currency code after amount: 1,000,000.00 USD or 1M USD or 1.5 million USD
    for code in currency_codes:
        # Match amount followed by currency code (with or without space)
        patterns.append(
            (rf'(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*(?:million|m|billion|b|trillion|t)?\s*{code}', code)
        )
        
        # Match amount with M/B/T suffix followed by currency code
        patterns.append(
            (rf'(\d+(?:\.\d+)?)\s*(?:M|Mio|Mill|Million|B|Bio|Bill|Billion|T|Trill|Trillion)\s*{code}', code)
        )
    
    # Special patterns for formats like "EUR 10 million" or "USD 500,000"
    for code in currency_codes:
        patterns.append(
            (rf'{code}\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*(?:million|m|billion|b|trillion|t)?', code)
        )
        
        patterns.append(
            (rf'{code}\s*(\d+(?:\.\d+)?)\s*(?:M|Mio|Mill|Million|B|Bio|Bill|Billion|T|Trill|Trillion)', code)
        )
    
    # Additional patterns for common phrases
    special_phrases = [
        (r'(?:estimated|approximate|approx\.?|est\.?|about|total|contract)\s+(?:cost|value|amount|budget|price)\s+(?:of|is|:)?\s*(?:approximately|approx\.?|about|around)?\s*([A-Z]{3})?(?:\s*)(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*(?:million|m|billion|b|trillion|t)?(?:\s*)([A-Z]{3})?'),
        (r'(?:estimated|approximate|approx\.?|est\.?|about|total|contract)\s+(?:cost|value|amount|budget|price)\s+(?:of|is|:)?\s*(?:approximately|approx\.?|about|around)?\s*([A-Z]{3})?(?:\s*)(\d+(?:\.\d+)?)\s*(?:M|Mio|Mill|Million|B|Bio|Bill|Billion|T|Trill|Trillion)(?:\s*)([A-Z]{3})?'),
        (r'(?:budget|contract|project|procurement)\s+(?:cost|value|amount|worth|sum)\s*(?:of|is|:)?\s*(?:approximately|approx\.?|about|around)?\s*([A-Z]{3})?(?:\s*)(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*(?:million|m|billion|b|trillion|t)?(?:\s*)([A-Z]{3})?'),
        (r'(?:budget|contract|project|procurement)\s+(?:cost|value|amount|worth|sum)\s*(?:of|is|:)?\s*(?:approximately|approx\.?|about|around)?\s*([A-Z]{3})?(?:\s*)(\d+(?:\.\d+)?)\s*(?:M|Mio|Mill|Million|B|Bio|Bill|Billion|T|Trill|Trillion)(?:\s*)([A-Z]{3})?')
    ]
    
    # Try each pattern
    for pattern, currency in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            for match in matches:
                # Handle cases where match might be a tuple or a string
                if isinstance(match, tuple):
                    if len(match) > 0:
                        amount_str = match[0]
                    else:
                        continue
                else:
                    amount_str = match
                
                # Ensure amount_str is a string
                if not isinstance(amount_str, str):
                    continue
                
                # Strip and clean the amount string
                amount_str = amount_str.strip()
                amount_str = amount_str.replace(',', '')
                
                # Handle million/billion/trillion suffixes
                if re.search(r'million|mill\.?|mm|m$', amount_str, re.IGNORECASE):
                    multiplier = 1000000
                    amount_str = re.sub(r'million|mill\.?|mm|m$', '', amount_str, flags=re.IGNORECASE).strip()
                elif re.search(r'billion|bill\.?|bb|b$', amount_str, re.IGNORECASE):
                    multiplier = 1000000000
                    amount_str = re.sub(r'billion|bill\.?|bb|b$', '', amount_str, flags=re.IGNORECASE).strip()
                elif re.search(r'trillion|trill\.?|tt|t$', amount_str, re.IGNORECASE):
                    multiplier = 1000000000000
                    amount_str = re.sub(r'trillion|trill\.?|tt|t$', '', amount_str, flags=re.IGNORECASE).strip()
                else:
                    multiplier = 1
                
                try:
                    amount = float(amount_str) * multiplier
                    return amount, currency
                except (ValueError, TypeError):
                    continue
    
    # Try special phrases
    for pattern in special_phrases:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 3:
                    pre_currency = match[0].strip() if match[0] else None
                    amount_str = match[1].strip() if match[1] else None
                    post_currency = match[2].strip() if match[2] else None
                    
                    currency = pre_currency or post_currency
                    
                    if not amount_str:
                        continue
                        
                    # Clean the amount string
                    amount_str = amount_str.replace(',', '')
                    
                    # Handle million/billion/trillion suffixes
                    if re.search(r'million|mill\.?|mm|m$', amount_str, re.IGNORECASE):
                        multiplier = 1000000
                        amount_str = re.sub(r'million|mill\.?|mm|m$', '', amount_str, flags=re.IGNORECASE).strip()
                    elif re.search(r'billion|bill\.?|bb|b$', amount_str, re.IGNORECASE):
                        multiplier = 1000000000
                        amount_str = re.sub(r'billion|bill\.?|bb|b$', '', amount_str, flags=re.IGNORECASE).strip()
                    elif re.search(r'trillion|trill\.?|tt|t$', amount_str, re.IGNORECASE):
                        multiplier = 1000000000000
                        amount_str = re.sub(r'trillion|trill\.?|tt|t$', '', amount_str, flags=re.IGNORECASE).strip()
                    else:
                        multiplier = 1
                    
                    try:
                        amount = float(amount_str) * multiplier
                        if currency and currency.upper() in currency_codes:
                            return amount, currency.upper()
                        else:
                            # Default to USD if currency can't be determined
                            return amount, 'USD'
                    except (ValueError, TypeError):
                        continue
    
    # If no match found with currency, try to at least extract a financial amount
    amount_patterns = [
        r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*(?:million|m|billion|b|trillion|t)',
        r'(\d+(?:\.\d+)?)\s*(?:M|Mio|Mill|Million|B|Bio|Bill|Billion|T|Trill|Trillion)'
    ]
    
    for pattern in amount_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            for match in matches:
                # Handle cases where match might be a tuple or a string
                if isinstance(match, tuple):
                    if len(match) > 0:
                        amount_str = match[0]
                    else:
                        continue
                else:
                    amount_str = match
                
                # Ensure amount_str is a string
                if not isinstance(amount_str, str):
                    continue
                
                # Strip and clean the amount string
                amount_str = amount_str.strip()
                amount_str = amount_str.replace(',', '')
                
                # Handle million/billion/trillion suffixes
                if re.search(r'million|mill\.?|mm|m$', amount_str, re.IGNORECASE):
                    multiplier = 1000000
                    amount_str = re.sub(r'million|mill\.?|mm|m$', '', amount_str, flags=re.IGNORECASE).strip()
                elif re.search(r'billion|bill\.?|bb|b$', amount_str, re.IGNORECASE):
                    multiplier = 1000000000
                    amount_str = re.sub(r'billion|bill\.?|bb|b$', '', amount_str, flags=re.IGNORECASE).strip()
                elif re.search(r'trillion|trill\.?|tt|t$', amount_str, re.IGNORECASE):
                    multiplier = 1000000000000
                    amount_str = re.sub(r'trillion|trill\.?|tt|t$', '', amount_str, flags=re.IGNORECASE).strip()
                else:
                    multiplier = 1
                
                try:
                    amount = float(amount_str) * multiplier
                    # Default to USD if no currency specified
                    return amount, 'USD'
                except (ValueError, TypeError):
                    continue
                
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
    Extract organization name from text using improved heuristics.
    
    Args:
        text: Text to extract organization from
        
    Returns:
        Extracted organization name or None
    """
    if not text:
        return None
        
    # Common organization indicators
    org_indicators = [
        "by", "from", "for", "at", "with",
        "organization", "organisation", "agency", "authority", "ministry",
        "department", "commission", "bureau", "office", "institute",
        "corporation", "company", "ltd", "limited", "inc", "incorporated",
        "council", "administration", "board", "committee"
    ]
    
    # Try to find organization name after common indicators
    text_lower = text.lower()
    for indicator in org_indicators:
        idx = text_lower.find(f" {indicator} ")
        if idx >= 0:
            # Look for organization name in the next 100 characters
            potential_org = text[idx:idx+100].strip()
            # Split on common delimiters
            for delim in [". ", ", ", " - ", "\n", " for ", " to "]:
                if delim in potential_org:
                    potential_org = potential_org.split(delim)[0].strip()
            if len(potential_org) > 3 and len(potential_org) < 100:
                return potential_org
    
    # Try to find organization patterns
    import re
    
    # Pattern for organization-like strings
    org_patterns = [
        r"(?:Ministry of|Department of|Office of|Agency for|Authority of)\s+[A-Z][A-Za-z\s,]+",
        r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,5}\s+(?:Corporation|Authority|Agency|Commission|Department|Ministry|Office)",
        r"(?:The\s+)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,5}\s+(?:Ltd\.?|Limited|Inc\.?|Corporation|LLC)",
        r"(?:National|Federal|State|Regional|Local)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}"
    ]
    
    for pattern in org_patterns:
        matches = re.findall(pattern, text)
        if matches:
            # Return the longest match as it's likely the most complete
            return max(matches, key=len)
    
    return None

def extract_organization_and_buyer(text: str, title: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract both organization and buyer information from text.
    
    Args:
        text: Main text to extract from
        title: Optional title text to also check
        
    Returns:
        Tuple of (organization_name, buyer_name)
    """
    organization = None
    buyer = None
    
    # Try to extract from title first if available
    if title:
        organization = extract_organization(title)
        
    # If not found in title, try main text
    if not organization:
        organization = extract_organization(text)
    
    # Look for buyer-specific patterns
    buyer_patterns = [
        r"(?:buyer|purchasing entity|contracting authority|procuring entity):\s*([A-Z][A-Za-z\s,]+(?:Ltd\.?|Limited|Inc\.?|Corporation|LLC)?)",
        r"(?:on behalf of|for)\s+([A-Z][A-Za-z\s,]+(?:Ltd\.?|Limited|Inc\.?|Corporation|LLC)?)",
        r"(?:client|end-user):\s*([A-Z][A-Za-z\s,]+(?:Ltd\.?|Limited|Inc\.?|Corporation|LLC)?)"
    ]
    
    import re
    for pattern in buyer_patterns:
        if text:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                buyer = matches[0].strip()
                break
                
        if title and not buyer:
            matches = re.findall(pattern, title, re.IGNORECASE)
            if matches:
                buyer = matches[0].strip()
                break
    
    # If organization is still missing but we found a buyer, use it as organization
    if not organization and buyer:
        organization = buyer
        
    return organization, buyer

def ensure_country(country_value=None, text=None, organization=None, email=None, language=None):
    """
    Normalize country names to standard English names.
    
    Args:
        country_value: Country name or code to normalize
        text: Text to search for country mentions (fallback)
        organization: Organization name to extract country from (fallback) 
        email: Email address to extract country from domain (fallback)
        language: Language code to infer country (lowest priority fallback)
        
    Returns:
        str: Normalized country name or original value if can't be normalized
    """
    # Handle both keyword and positional arguments for backward compatibility
    # The old API only had the country_value parameter
    # If country is passed as a keyword arg, use it as country_value
    if 'country' in locals() or 'country' in globals():
        country_value = locals().get('country') or globals().get('country')
    
    # If the original value is empty, try to extract from text
    if not country_value or country_value == '':
        # Try to extract from text if no value provided
        if text:
            country_from_text, _ = extract_location_info(text)
            if country_from_text:
                return country_from_text
        
        # If we have organization info, try to extract from that
        if organization:
            for country_name in ["Philippines", "Bangladesh", "Pakistan", "India", "Nepal", "Vietnam", "China"]:
                if country_name.lower() in organization.lower():
                    return country_name
        
        # At this point, we couldn't find a country, but we don't want to return None
        # since that can cause issues in the unified tender model
        return country_value  # Return the original value, even if it's empty
    
    # Convert to string and clean
    if not isinstance(country_value, str):
        country_value = str(country_value)
    
    # Store the original value before cleaning in case we need to fall back to it
    original_value = country_value
    
    # Convert to string and clean
    if not isinstance(country_value, str):
        country_value = str(country_value)
    
    # Store the original value before cleaning in case we need to fall back to it
    original_value = country_value
    
    # Instead of just removing special characters, replace accented characters with non-accented equivalents
    # This maintains readability of country names
    accent_map = {
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'á': 'a', 'à': 'a', 'â': 'a', 'ä': 'a',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'ó': 'o', 'ò': 'o', 'ô': 'o', 'ö': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
        'ý': 'y', 'ÿ': 'y',
        'ç': 'c', 'ñ': 'n',
        'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
        'Á': 'A', 'À': 'A', 'Â': 'A', 'Ä': 'A',
        'Í': 'I', 'Ì': 'I', 'Î': 'I', 'Ï': 'I',
        'Ó': 'O', 'Ò': 'O', 'Ô': 'O', 'Ö': 'O',
        'Ú': 'U', 'Ù': 'U', 'Û': 'U', 'Ü': 'U',
        'Ý': 'Y', 'Ç': 'C', 'Ñ': 'N',
        'ã': 'a', 'õ': 'o', 'Ã': 'A', 'Õ': 'O'  # Portuguese characters
    }
    
    # Replace accented characters
    for accented, non_accented in accent_map.items():
        country_value = country_value.replace(accented, non_accented)
    
    # Handle apostrophes and special cases
    country_value = country_value.replace("'", " ").replace("`", " ")
    
    # Now remove any remaining non-alphanumeric characters except spaces and hyphens
    cleaned_value = re.sub(r'[^a-zA-Z0-9\s-]', ' ', country_value).strip()
    cleaned_value = re.sub(r'\s+', ' ', cleaned_value)  # Replace multiple spaces with a single space
    
    if not cleaned_value:
        return original_value  # Return the original value if cleaning resulted in empty string
    
    # Use the cleaned value for further processing
    country_value = cleaned_value
    
    # Special cases that need exact matching
    special_cases = {
        "multinational": "Multinational",
        "rca": "Central African Republic",
        "rdc": "Democratic Republic of the Congo",
        "program for integrated rural sanitation in upper egypt": "Egypt",
        "program for integrated rural sanitation in upper egypt (simplified)": "Egypt",
        "cabo verde": "Cape Verde",
        "caboverde": "Cape Verde",
        "eswatini": "Eswatini",
        "bostwana": "Botswana",
        
        # Add common ADB country names
        "kyrgyz": "Kyrgyz Republic",
        "kyrgyzstan": "Kyrgyz Republic",
        "republic of korea": "South Korea",
        "korea republic": "South Korea",
        "democratic republic of korea": "North Korea",
        "uzbek": "Uzbekistan",
        "micronesia": "Federated States of Micronesia",
        "fiji": "Fiji",
        "kazakhstan": "Kazakhstan",
        "mongolia": "Mongolia",
        "papua": "Papua New Guinea",
        "papua new guinea": "Papua New Guinea",
        "philippines": "Philippines",
        "uzbekistan": "Uzbekistan",
        "indonesia": "Indonesia"
    }
    
    # Check for exact match in special cases first (case insensitive)
    normalized = special_cases.get(country_value.lower())
    if normalized:
        return normalized
    
    # Country code mapping
    country_code_map = {
        "USA": "United States", "US": "United States",
        "UK": "United Kingdom", "GB": "United Kingdom",
        "UAE": "United Arab Emirates", "AE": "United Arab Emirates",
        "DRC": "Democratic Republic of the Congo",
        "ROK": "South Korea", "PRC": "China",
        "PRY": "Paraguay", "CHE": "Switzerland",
        "TWN": "Taiwan", "PSE": "Palestine",
        
        # Add codes for countries typically found in ADB records
        "KGZ": "Kyrgyz Republic",
        "UZB": "Uzbekistan",
        "KAZ": "Kazakhstan",
        "MNG": "Mongolia",
        "PNG": "Papua New Guinea",
        "PHL": "Philippines",
        "IDN": "Indonesia",
        "REG": "Regional",  # ADB uses REG for regional projects
        "FJI": "Fiji"
    }
    
    if country_value.upper() in country_code_map:
        return country_code_map[country_value.upper()]
    
    # Common alternate spellings
    country_names = {
        "america": "United States",
        "england": "United Kingdom",
        "scotland": "United Kingdom",
        "wales": "United Kingdom",
        "northern ireland": "United Kingdom",
        "hongkong": "Hong Kong",
        "ivory coast": "Côte d'Ivoire",
        "cote divoire": "Côte d'Ivoire",
        "cte divoire": "Côte d'Ivoire",
        "burma": "Myanmar",
        "macedonia": "North Macedonia",
        "vietnam": "Vietnam",
        "viet nam": "Vietnam",
        "armenia": "Armenia",
        "senegal": "Senegal",
        "guinea": "Guinea",
        "benin": "Benin", 
        "nigeria": "Nigeria",
        "algeria": "Algeria",
        "equatorial guinea": "Equatorial Guinea"
    }
    normalized = country_names.get(country_value.lower())
    if normalized:
        return normalized
    
    # Try to extract from organization name
    if organization:
        # Updated list of countries to search for in organization name
        common_countries = [
            "Philippines", "Bangladesh", "Pakistan", "India", "Nepal",
            "Vietnam", "China", "Kyrgyz Republic", "Uzbekistan", "Kazakhstan",
            "Mongolia", "Papua New Guinea", "Fiji", "Indonesia"
        ]
        
        # Search for common countries in organization name
        for country in common_countries:
            if country.lower() in organization.lower():
                return country
        
        # If no match found with common countries, try broader pattern matching
        org_country_pattern = r'\b({})\b'.format('|'.join(re.escape(c) for c in country_code_map.values()))
        match = re.search(org_country_pattern, organization, re.I)
        if match:
            return match.group(0)
    
    # Final cleanup and title case
    cleaned = re.sub(r'\s+', ' ', country_value).title()
    
    # Expanded list of known countries with a focus on ADB member countries
    known_countries = {
        # Major countries
        "United States", "China", "India", "Germany", "France", "United Kingdom", "Japan", "Brazil",
        
        # ADB regional member countries
        "Afghanistan", "Armenia", "Australia", "Azerbaijan", "Bangladesh", "Bhutan",
        "Brunei Darussalam", "Cambodia", "Cook Islands", "Fiji", "Georgia", "Hong Kong",
        "Indonesia", "Kazakhstan", "Kiribati", "Kyrgyz Republic", "Lao People's Democratic Republic",
        "Malaysia", "Maldives", "Marshall Islands", "Micronesia", "Mongolia", "Myanmar", "Nauru",
        "Nepal", "New Zealand", "Niue", "Pakistan", "Palau", "Papua New Guinea", "Philippines",
        "Republic of Korea", "Samoa", "Singapore", "Solomon Islands", "Sri Lanka", "Taiwan",
        "Tajikistan", "Thailand", "Timor-Leste", "Tonga", "Turkmenistan", "Tuvalu",
        "Uzbekistan", "Vanuatu", "Vietnam",
        
        # Other common countries
        "Russia", "Italy", "Spain", "Mexico", "Canada", "Brazil", "South Africa", "Nigeria",
        "Egypt", "Kenya", "Ghana", "Ethiopia", "Tanzania", "Uganda", "Zimbabwe", "Botswana",
        "Namibia", "Zambia", "Mozambique", "Angola", "Senegal", "Côte d'Ivoire", "Saudi Arabia",
        "Turkey", "Portugal", "Iceland", "Ireland", "Sweden", "Norway", "Finland", "Denmark",
        "Belgium", "Netherlands", "Luxembourg", "Switzerland", "Austria", "Greece",
        "Albania", "Bulgaria", "Serbia", "Croatia", "Bosnia and Herzegovina", "Romania",
        "Ukraine", "Moldova", "Belarus", "Lithuania", "Latvia", "Estonia", "Poland",
        "Czech Republic", "Slovakia", "Hungary", "Slovenia", "North Macedonia",
        "Montenegro", "Mali", "Niger", "Chad", "Sudan", "South Sudan", "Eritrea",
        "Djibouti", "Somalia", "Morocco", "Tunisia", "Libya", "Algeria", "Mauritania",
        "Senegal", "Gambia", "Guinea-Bissau", "Guinea", "Sierra Leone", "Liberia",
        "Togo", "Benin", "Burkina Faso", "Cape Verde", "Cameroon", "Central African Republic",
        "Gabon", "Equatorial Guinea", "Republic of the Congo", "Democratic Republic of the Congo",
        "Burundi", "Rwanda", "Malawi", "Lesotho", "Eswatini", "Madagascar", "Mauritius",
        "Seychelles", "Comoros", "North Korea", "South Korea"
    }
    
    if cleaned in known_countries:
        return cleaned
    
    # More lenient validation for country-like strings
    # Accept any string that looks like a properly capitalized name and doesn't contain numbers
    if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$', cleaned) and not re.search(r'\d', cleaned):
        return cleaned
    
    # Extremely lenient fallback - just return the original value if we couldn't normalize it
    # This prevents country fields from being set to None/null in the database
    return original_value

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


def log_tender_normalization(source_table, source_id, log_data):
    """
    Log detailed information about a tender normalization process.
    
    Args:
        source_table: The source table name
        source_id: The ID in the source table
        log_data: Dictionary of data to log
    """
    try:
        if not isinstance(log_data, dict):
            log_data = {"data": str(log_data)}
            
        formatted_data = format_for_logging(log_data)
        logger.info(f"Normalizing tender from {source_table} (ID: {source_id}): {formatted_data}")
    except Exception as e:
        logger.error(f"Error logging tender normalization: {str(e)}")


def clean_price(price_value):
    """
    Clean and normalize a price value.
    
    Args:
        price_value: The price value to clean (can be string, float, int, or None)
        
    Returns:
        Cleaned price as float or None if invalid
    """
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
    
    # Remove currency symbols and other non-numeric characters
    price_str = re.sub(r'[^0-9.,]', '', price_str)
    
    # Handle different decimal and thousand separators
    if ',' in price_str and '.' in price_str:
        # If both are present, determine which is the decimal separator
        if price_str.rindex('.') > price_str.rindex(','):
            # Format like 1,000.00
            price_str = price_str.replace(',', '')
        else:
            # Format like 1.000,00
            price_str = price_str.replace('.', '').replace(',', '.')
    elif ',' in price_str:
        # Could be either 1,000 or 1,00
        if len(price_str.split(',')[1]) == 2:
            # Likely a decimal separator (1,50)
            price_str = price_str.replace(',', '.')
    
    # Handle empty result after cleaning
    if not price_str:
        return None
        
    try:
        return float(price_str)
    except ValueError:
        return None


def extract_procurement_method(text):
    """
    Extract procurement method information from text.
    
    Args:
        text: Text to extract procurement method from
        
    Returns:
        Normalized procurement method (open, limited, selective) or None if not found
    """
    if not text or not isinstance(text, str):
        return None
    
    text = text.lower()
    
    # Check for open/competitive procurement
    if any(term in text for term in ['open tender', 'open bidding', 'open procedure', 'competitive tender', 
                                    'competitive bidding', 'public tender', 'public procurement']):
        return 'open'
        
    # Check for limited/direct procurement
    if any(term in text for term in ['limited tender', 'direct award', 'sole source', 'single source', 
                                    'negotiated procedure', 'restricted procedure', 'direct procurement']):
        return 'limited'
        
    # Check for selective procurement
    if any(term in text for term in ['selective tender', 'invitation to tender', 'pre-qualified', 
                                    'shortlist', 'selected bidders', 'invitation only']):
        return 'selective'
    
    return None


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


def extract_status(text=None, deadline=None, publication_date=None, description=None):
    """
    Extract tender status information from text and date information.
    
    Args:
        text: Text to extract status from
        deadline: Deadline date for the tender
        publication_date: Publication date of the tender
        description: Description text to extract status from (used if text is None)
        
    Returns:
        Normalized status (active, complete, cancelled) or None if not found
    """
    # Use description as text if text is None
    if text is None and description is not None:
        text = description
        
    status_from_text = None
    if text and isinstance(text, str):
        text_lower = text.lower()
        
        # Check for active status
        if any(term in text_lower for term in ['active', 'ongoing', 'in progress', 'open for bids', 
                                        'accepting bids', 'open for proposals', 'current']):
            status_from_text = 'active'
            
        # Check for completed status
        elif any(term in text_lower for term in ['complete', 'completed', 'closed', 'awarded', 'finished', 
                                            'concluded', 'contract awarded', 'successful']):
            status_from_text = 'complete'
            
        # Check for cancelled status
        elif any(term in text_lower for term in ['cancelled', 'canceled', 'terminated', 'withdrawn', 
                                            'abandoned', 'unsuccessful', 'failed', 'not awarded']):
            status_from_text = 'cancelled'
    
    # If we have date information, use it to determine status
    if deadline or publication_date:
        from datetime import datetime
        current_date = datetime.now().date()
        
        # If deadline is in the future and we have a publication date, tender is active
        if deadline and hasattr(deadline, 'date'):
            deadline_date = deadline.date()
            if deadline_date >= current_date:
                # Text-based status takes precedence over date-based status
                if status_from_text in ['complete', 'cancelled']:
                    return status_from_text
                return 'active'
            else:
                # Deadline has passed, so tender is likely complete unless explicitly cancelled
                if status_from_text == 'cancelled':
                    return 'cancelled'
                return 'complete'
                
        # If we only have publication date and no deadline
        elif publication_date and hasattr(publication_date, 'date'):
            # If publication date is very recent (within 90 days), tender is likely active
            days_since_publication = (current_date - publication_date.date()).days
            if days_since_publication <= 90:
                # Text-based status takes precedence over date-based status
                if status_from_text in ['complete', 'cancelled']:
                    return status_from_text
                return 'active'
    
    # Return text-based status if found, otherwise None
    return status_from_text


def parse_date_string(date_str):
    """
    Parse a date string into a datetime object.
    
    Args:
        date_str: String containing a date
        
    Returns:
        datetime object or None if parsing fails
    """
    if not date_str or not isinstance(date_str, str):
            return None

    # Clean the string
    date_str = date_str.strip()
    
    # Common date formats to try
    date_formats = [
        '%Y-%m-%d',       # 2023-01-30
        '%Y-%m-%dT%H:%M:%S',  # 2023-01-30T14:30:00
        '%Y-%m-%dT%H:%M:%SZ', # 2023-01-30T14:30:00Z
        '%Y-%m-%d %H:%M:%S',  # 2023-01-30 14:30:00
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
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # If all parsing attempts fail
    return None


def parse_date_from_text(text):
    """
    Extract and parse a date from free-form text.
    
    Args:
        text: Free-form text that might contain a date
        
    Returns:
        datetime object or None if no date found
    """
    if not text or not isinstance(text, str):
        return None
        
    # Common date patterns in text
    date_patterns = [
        r'\b(\d{4})[-/\.](\d{1,2})[-/\.](\d{1,2})\b',  # YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD
        r'\b(\d{1,2})[-/\.](\d{1,2})[-/\.](\d{4})\b',  # DD-MM-YYYY, DD/MM/YYYY, DD.MM.YYYY
        r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (\d{1,2}),? (\d{4})\b',  # Month DD, YYYY
        r'\b(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (\d{4})\b',  # DD Month YYYY
        r'\b(\d{1,2})\s?(?:st|nd|rd|th)? of (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (\d{4})\b'  # DDth of Month YYYY
    ]
    
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            for match in matches:
                # Try to construct a date string and parse it
                date_str = ' '.join(match).strip()
                parsed_date = parse_date_string(date_str)
                if parsed_date:
                    return parsed_date
    
    # If no patterns matched
    return None


def extract_sector_info(text):
    """
    Extract sector information from text.
    
    Args:
        text: Text to extract sectors from
        
    Returns:
        List of identified sectors or None if no sectors found
    """
    if not text or not isinstance(text, str):
        return None
        
    text = text.lower()
    
    # Define common sectors in the procurement domain
    sector_keywords = {
        'agriculture': ['agriculture', 'farming', 'irrigation', 'crop', 'livestock'],
        'construction': ['construction', 'building', 'infrastructure', 'roads', 'highways', 'bridges'],
        'education': ['education', 'school', 'university', 'college', 'teaching', 'learning'],
        'energy': ['energy', 'electricity', 'power', 'renewable', 'solar', 'wind', 'hydropower'],
        'finance': ['finance', 'banking', 'insurance', 'investment', 'financial'],
        'health': ['health', 'medical', 'hospital', 'clinic', 'medicine', 'healthcare'],
        'ict': ['ict', 'information technology', 'technology', 'telecom', 'software', 'hardware', 'digital'],
        'manufacturing': ['manufacturing', 'industrial', 'production', 'factory'],
        'mining': ['mining', 'mineral', 'extraction', 'coal', 'ore'],
        'transportation': ['transportation', 'transport', 'logistics', 'railway', 'aviation', 'maritime'],
        'water': ['water', 'sanitation', 'sewage', 'wastewater', 'utility']
    }
    
    identified_sectors = []
    
    # Check for each sector's keywords in the text
    for sector, keywords in sector_keywords.items():
        if any(keyword in text for keyword in keywords):
            identified_sectors.append(sector)
    
    return identified_sectors if identified_sectors else None


def standardize_status(status_text):
    """
    Standardize various status values to a common set of status values.
    
    Args:
        status_text: The status text to standardize
        
    Returns:
        Standardized status value (active, complete, cancelled, etc.)
    """
    if not status_text:
        return None
        
    if not isinstance(status_text, str):
        status_text = str(status_text)
        
    status_text = status_text.lower().strip()
    
    # Active/Open status mappings
    if any(term in status_text for term in ['active', 'ongoing', 'open', 'current', 'in progress', 
                                         'pending', 'published', 'accepting', 'available']):
        return 'active'
        
    # Complete/Closed status mappings
    if any(term in status_text for term in ['complete', 'completed', 'closed', 'awarded', 'finished', 
                                         'done', 'executed', 'successful', 'implemented', 'issued']):
        return 'complete'
        
    # Cancelled status mappings
    if any(term in status_text for term in ['cancel', 'cancelled', 'canceled', 'terminated', 'withdrawn', 
                                         'failed', 'abandoned', 'unsuccessful']):
        return 'cancelled'
        
    # Planned/Upcoming status mappings
    if any(term in status_text for term in ['planned', 'upcoming', 'future', 'announced', 'notice', 
                                         'forecast', 'scheduled', 'preliminary']):
        return 'planned'
        
    # Draft status mappings
    if any(term in status_text for term in ['draft', 'preparation', 'preparatory', 'pre-release']):
        return 'draft'
        
    # If we can't determine the status, return the original text
    return status_text

def normalize_title(title: str) -> str:
    """
    Normalize tender title by removing common issues and standardizing format.
    
    Args:
        title: Raw title string
        
    Returns:
        Normalized title string
    """
    if not title:
        return ""  # Return empty string instead of None
        
    # Remove multiple spaces
    title = ' '.join(title.split())
    
    # Remove common prefixes
    prefixes_to_remove = [
        r'^(?:Notice|Tender|RFP|RFQ|ITB|EOI|Procurement|Contract)\s*[-:]\s*',
        r'^\d{4}\s*[-:]\s*',
        r'^\d{4}/\d{2,4}\s*[-:]\s*'
    ]
    
    for prefix in prefixes_to_remove:
        title = re.sub(prefix, '', title, flags=re.IGNORECASE)
    
    # Remove reference numbers at the start
    title = re.sub(r'^[A-Z0-9-/]+\s*[-:]\s*', '', title)
    
    # Remove dates at the end
    title = re.sub(r'\s*\(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}\)\s*$', '', title)
    
    # Capitalize first letter of each word except articles and prepositions
    skip_words = {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 
                 'to', 'by', 'from', 'in', 'into', 'of', 'with'}
    words = title.split()
    for i, word in enumerate(words):
        if i == 0 or word.lower() not in skip_words:
            words[i] = word.capitalize()
        else:
            words[i] = word.lower()
    
    return ' '.join(words)

def normalize_description(description: str) -> str:
    """
    Normalize tender description by cleaning and standardizing format.
    
    Args:
        description: Raw description string
        
    Returns:
        Normalized description string
    """
    if not description:
        return ""  # Return empty string instead of None
        
    # Remove multiple spaces and normalize newlines
    description = ' '.join(description.split())
    
    # Remove common HTML artifacts
    description = re.sub(r'<[^>]+>', ' ', description)
    description = re.sub(r'&[a-z]+;', ' ', description)
    
    # Remove multiple punctuation
    description = re.sub(r'[.!?]+', '.', description)
    description = re.sub(r'[-]+', '-', description)
    
    # Ensure proper spacing after punctuation
    description = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', description)
    
    # Remove URLs (they should be in document_links)
    description = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', description)
    
    return description.strip()

def standardize_status(status: str) -> str:
    """
    Standardize tender status to a common format.
    
    Args:
        status: Raw status string
        
    Returns:
        Standardized status string
    """
    if not status:
        return None
        
    status = status.lower().strip()
    
    # Define status mappings
    status_mapping = {
        # Active variations
        'active': 'active',
        'open': 'active',
        'ongoing': 'active',
        'in progress': 'active',
        'published': 'active',
        
        # Complete variations
        'complete': 'complete',
        'completed': 'complete',
        'closed': 'complete',
        'awarded': 'complete',
        'finished': 'complete',
        
        # Cancelled variations
        'cancelled': 'cancelled',
        'canceled': 'cancelled',
        'terminated': 'cancelled',
        'withdrawn': 'cancelled',
        
        # Planned variations
        'planned': 'planned',
        'upcoming': 'planned',
        'draft': 'planned',
        'preparation': 'planned',
        
        # Expression of Interest variations
        'expression of interest': 'active',
        'eoi': 'active',
        'request for eoi': 'active',
        
        # Request variations
        'request for proposal': 'active',
        'request for quotation': 'active',
        'invitation to bid': 'active',
        'rfp': 'active',
        'rfq': 'active',
        'itb': 'active'
    }
    
    # Try direct mapping
    if status in status_mapping:
        return status_mapping[status]
    
    # Try partial matching
    for key, value in status_mapping.items():
        if key in status:
            return value
    
    # Default to active if no match found
    return 'active'

def standardize_procurement_method(method: str) -> str:
    """
    Standardize procurement method to a common format.
    
    Args:
        method: Raw procurement method string
        
    Returns:
        Standardized procurement method string
    """
    if not method:
        return None
        
    method = method.lower().strip()
    
    # Define method mappings
    method_mapping = {
        # Open variations
        'open': 'Open Procedure',
        'open procedure': 'Open Procedure',
        'open tender': 'Open Procedure',
        'open competition': 'Open Procedure',
        'open bidding': 'Open Procedure',
        
        # Restricted variations
        'restricted': 'Restricted Procedure',
        'restricted procedure': 'Restricted Procedure',
        'selective': 'Restricted Procedure',
        'limited': 'Restricted Procedure',
        
        # Negotiated variations
        'negotiated': 'Negotiated Procedure',
        'neg-w-call': 'Negotiated Procedure with Call',
        'neg-wo-call': 'Negotiated Procedure without Call',
        
        # Competitive dialogue variations
        'competitive dialogue': 'Competitive Dialogue',
        'comp-dial': 'Competitive Dialogue',
        'dialogue': 'Competitive Dialogue',
        
        # Request variations
        'rfp': 'Request for Proposal',
        'request for proposal': 'Request for Proposal',
        'rfq': 'Request for Quotation',
        'request for quotation': 'Request for Quotation',
        'itb': 'Invitation to Bid',
        'invitation to bid': 'Invitation to Bid',
        'eoi': 'Expression of Interest',
        'expression of interest': 'Expression of Interest',
        
        # Quality-based variations
        'qcbs': 'Quality and Cost-Based Selection',
        'quality and cost-based selection': 'Quality and Cost-Based Selection',
        'quality-based selection': 'Quality-Based Selection',
        
        # Other variations
        'direct': 'Direct Procurement',
        'single source': 'Direct Procurement',
        'shopping': 'Shopping Procedure'
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
    """
    Normalize tender value and currency.
    
    Args:
        value: Estimated value
        currency: Currency code
        
    Returns:
        Tuple of (normalized_value, normalized_currency)
    """
    if not value:
        return None, currency
        
    # Define suspicious value thresholds
    MIN_VALUE = 100  # Minimum reasonable tender value
    MAX_VALUE = 1000000000000  # Maximum reasonable tender value (1 trillion)
    
    # Check if value is within reasonable range
    if value < MIN_VALUE or value > MAX_VALUE:
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
            'YUAN': 'CNY',
            'YEN': 'JPY',
            '¥': 'JPY'
        }
        
        currency = currency_mapping.get(currency, currency)
        
        # Validate currency code (must be 3 letters)
        if not re.match(r'^[A-Z]{3}$', currency):
            currency = None
    
    return value, currency