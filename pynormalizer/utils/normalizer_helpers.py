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
                amount_str = match.strip()
                
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
                amount_str = match.strip()
                
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
        'combined synopsis/solicitation': 'Open',
        'sources sought': 'Open',
        'request for information': 'Open',
        'request for proposal': 'Open',
        'request for quotation': 'Open',
        'invitation to bid': 'Open',
        'call for tenders': 'Open',
        'solicitation': 'Open',
        
        # Closed statuses
        'closed': 'Closed',
        'complete': 'Closed',
        'completed': 'Closed',
        'expired': 'Closed',
        'finished': 'Closed',
        'ended': 'Closed',
        'terminated': 'Closed',
        'deadline passed': 'Closed',
        'inactive': 'Closed',
        
        # Awarded statuses
        'awarded': 'Awarded', 
        'contract awarded': 'Awarded',
        'award': 'Awarded',
        'completed and awarded': 'Awarded',
        'closed and awarded': 'Awarded',
        'award notice': 'Awarded',
        'contract notice': 'Awarded',
        'contract award': 'Awarded',
        'contract award notice': 'Awarded',
        
        # Cancelled statuses
        'cancelled': 'Cancelled',
        'canceled': 'Cancelled',
        'withdrawn': 'Cancelled',
        'suspended': 'Cancelled',
        'discontinued': 'Cancelled',
        'terminated early': 'Cancelled',
        'revoked': 'Cancelled',
        
        # Draft/Planned statuses
        'draft': 'Planned',
        'planning': 'Planned',
        'planned': 'Planned',
        'upcoming': 'Planned',
        'scheduled': 'Planned',
        'future': 'Planned',
        'not yet published': 'Planned',
        'pre-solicitation': 'Planned',
        'intent to bundle requirements': 'Planned',
        'presolicitation': 'Planned',
        'prior information notice': 'Planned',
        'prior notice': 'Planned',
        
        # Special statuses
        'under review': 'Under Review',
        'pending': 'Pending',
        'evaluation': 'Under Review',
        'evaluating': 'Under Review',
        'in evaluation': 'Under Review',
        'under consideration': 'Under Review',
        'in selection': 'Under Review',
        'reviewing': 'Under Review'
    }
    
    # First, check for exact matches in the standardized statuses
    if status_lower in status_map:
        return status_map[status_lower]
    
    # If not an exact match, check for key terms within the status
    for key_term, std_status in status_map.items():
        if key_term in status_lower:
            return std_status
    
    # Check specific patterns with phrases
    if any(term in status_lower for term in ['award', 'awarded', 'contract awarded', 'winner']):
        return 'Awarded'
    elif any(term in status_lower for term in ['cancel', 'cancelled', 'canceled', 'withdraw', 'revoke']):
        return 'Cancelled'
    elif any(term in status_lower for term in ['review', 'evaluation', 'evaluating', 'processing', 'assessing']):
        return 'Under Review'
    elif any(term in status_lower for term in ['plan', 'schedule', 'future', 'upcoming', 'intent', 'pre-', 'prior']):
        return 'Planned'
    elif any(term in status_lower for term in ['open', 'active', 'current', 'ongoing', 'accept']):
        return 'Open'
    elif any(term in status_lower for term in ['close', 'end', 'complete', 'finish', 'expire', 'deadline pass']):
        return 'Closed'
    
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
    Ensures a valid country value is always returned, using fallback mechanisms if needed.
    
    Args:
        country: Direct country value if available
        text: Description or content text that might mention a country
        organization: Organization name that might include country information
        email: Email address that might have country TLD
        language: Language code that could indicate a country
        
    Returns:
        A non-empty country string, or "Unknown" as absolute fallback
    """
    # ULTIMATE BULLETPROOF WRAPPER
    try:
        # Get logger
        logger = logging.getLogger(__name__)
        logger.info("ensure_country called with country=" + str(country))
        
        # BULLETPROOF TYPE HANDLING
        # Handle all possible types for country parameter
        try:
            # First, identify and convert tuples
            if isinstance(country, tuple):
                logger.info(f"Country is a tuple of length {len(country)}")
                # Extract first element if it's a tuple (typical from extract_location_info)
                if len(country) > 0:
                    country = country[0]  # Now country might be a string or another type
                    logger.info(f"Extracted first element from tuple: {country}, Type: {type(country).__name__ if country is not None else 'None'}")
                else:
                    logger.info("Empty tuple found, setting country to None")
                    country = None
            
            # Now ensure country is a valid string
            if not country:
                logger.info("Country is None or empty, setting to None")
                country = None
            elif not isinstance(country, str):
                logger.info(f"Country is not a string but {type(country).__name__}, converting to string")
                try:
                    country = str(country).strip()
                    if not country:
                        country = None
                except Exception as e:
                    logger.error(f"Error converting country to string: {e}")
                    country = None
            elif not country.strip():
                logger.info("Country is an empty string, setting to None")
                country = None
            else:
                logger.info(f"Country is a valid string: {country}")
                country = country.strip()
            
            # The next part of the function relies on country being None or a valid string
            logger.info(f"Normalized country value: {country}")
            
            # The old tuple handling code is now redundant but keeping for backward compatibility
            # with any code paths we haven't updated yet - This should never be reached now
            if isinstance(country, tuple) and len(country) > 0:
                # If it's a tuple from extract_location_info, the first element is the country
                country_val = country[0]
                if country_val and isinstance(country_val, str) and country_val.strip():
                    logger.info(f"Legacy tuple handling used: {country_val}")
                    return country_val.strip()
            # Normal string case
            elif country and isinstance(country, str) and country.strip():
                logger.info(f"Valid country string found: {country}")
                return country
            
            # IMPROVED SAFETY: Type checking for all parameters
            if text and not isinstance(text, str):
                logger.info(f"Text is not a string but {type(text).__name__}, setting to None")
                text = None
            
            if organization and not isinstance(organization, str):
                logger.info(f"Organization is not a string but {type(organization).__name__}, setting to None")
                organization = None
            
            if email and not isinstance(email, str):
                logger.info(f"Email is not a string but {type(email).__name__}, setting to None")
                email = None
            
            if language and not isinstance(language, str):
                logger.info(f"Language is not a string but {type(language).__name__}, setting to None")
                language = None
        
            # Extract from text - with additional error handling
            if text and isinstance(text, str):
                try:
                    # First, try extract_location_info which is specialized for this
                    logger.info("Attempting to extract location from text...")
                    extracted_location = extract_location_info(text)
                    logger.info(f"Location extraction result: {extracted_location}, Type: {type(extracted_location).__name__ if extracted_location is not None else 'None'}")
                    
                    # IMPROVED SAFETY: More thorough type and value checking
                    if extracted_location:
                        if isinstance(extracted_location, tuple) and len(extracted_location) > 0:
                            extracted_country = extracted_location[0]
                            if extracted_country and isinstance(extracted_country, str) and extracted_country.strip():
                                logger.info(f"Using extracted country: {extracted_country}")
                                return extracted_country.strip()
                        elif isinstance(extracted_location, str) and extracted_location.strip():
                            # Handle case where extraction might return a string directly
                            logger.info(f"Using extracted location as string: {extracted_location}")
                            return extracted_location.strip()
                except Exception as e:
                    # IMPROVED SAFETY: More specific exception handling
                    logger.error(f"Location extraction failed: {e}")
                    # If extraction fails, continue with other methods
                    pass
        except Exception as e:
            logger.error(f"Error in ensure_country internal processing: {e}")
            logger.error(traceback.format_exc())
        
        # Countries to look for in text
        countries = [
            "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", 
            "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", 
            "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", 
            "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", 
            "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", 
            "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", 
            "Congo", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czech Republic", "Denmark", 
            "Djibouti", "Dominica", "Dominican Republic", "DR Congo", "Ecuador", "Egypt", 
            "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", 
            "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", 
            "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", 
            "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", 
            "Israel", "Italy", "Ivory Coast", "Jamaica", "Japan", "Jordan", "Kazakhstan", 
            "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", 
            "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", 
            "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", 
            "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", 
            "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", 
            "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", 
            "Norway", "Oman", "Pakistan", "Palau", "Palestine", "Panama", "Papua New Guinea", 
            "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", 
            "Russia", "Rwanda", "Saint Kitts and Nevis",
            "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", 
            "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", 
            "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", 
            "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Taiwan", "Tajikistan", 
            "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", 
            "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", 
            "United Kingdom", "United States", "Uruguay", "Uzbekistan", "Vanuatu", "Vatican City", 
            "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe", "USA", "UK", "UAE", "EU",
            "Hong Kong", "Puerto Rico"
        ]
        
        # Look for country names directly in text
        if text and isinstance(text, str):
            for country_name in countries:
                # Try both "Country" and "COUNTRY" formats
                patterns = [
                    rf'\b{country_name}\b',
                    rf'\b{country_name.upper()}\b',
                ]
                
                for pattern in patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        logger.info(f"Found country in text: {country_name}")
                        return country_name
        
        # Extract from organization name
        if organization and isinstance(organization, str):
            # Look for "COUNTRY - Organization" pattern
            country_prefix_pattern = r'^([A-Za-z\s]+)\s*[-–:]\s*'
            match = re.search(country_prefix_pattern, organization)
            if match and match.group(1).strip():
                country_text = match.group(1).strip()
                # Check if it's a valid country name
                for country_name in countries:
                    if country_name.lower() == country_text.lower():
                        logger.info(f"Found country in organization prefix: {country_name}")
                        return country_name
            
            # Look for country name in organization
            for country_name in countries:
                if country_name.lower() in organization.lower():
                    logger.info(f"Found country in organization name: {country_name}")
                    return country_name
                    
        # Extract from email domain
        if email and isinstance(email, str):
            # Country TLD mapping (partial list of common ones)
            tld_to_country = {
                '.uk': 'United Kingdom',
                '.us': 'United States',
                '.ca': 'Canada',
                '.au': 'Australia',
                '.fr': 'France',
                '.de': 'Germany',
                '.it': 'Italy',
                '.es': 'Spain',
                '.jp': 'Japan',
                '.cn': 'China',
                '.in': 'India',
                '.br': 'Brazil',
                '.ru': 'Russia',
                '.za': 'South Africa',
                '.mx': 'Mexico',
                '.ar': 'Argentina',
                '.id': 'Indonesia',
                '.ph': 'Philippines',
                '.ng': 'Nigeria',
                '.pk': 'Pakistan',
                '.ke': 'Kenya',
                '.rw': 'Rwanda',
                '.tz': 'Tanzania',
                '.ug': 'Uganda',
                '.gh': 'Ghana',
                '.sg': 'Singapore',
                '.my': 'Malaysia',
                '.th': 'Thailand',
                '.vn': 'Vietnam',
                '.nl': 'Netherlands',
                '.se': 'Sweden',
                '.no': 'Norway',
                '.fi': 'Finland',
                '.dk': 'Denmark',
                '.pl': 'Poland',
                '.cz': 'Czech Republic',
                '.hu': 'Hungary',
                '.ro': 'Romania',
                '.pt': 'Portugal',
                '.gr': 'Greece',
                '.ie': 'Ireland',
                '.nz': 'New Zealand',
                '.ae': 'United Arab Emirates',
                '.sa': 'Saudi Arabia',
                '.tr': 'Turkey',
                '.il': 'Israel',
                '.eg': 'Egypt',
                '.za': 'South Africa',
                '.pe': 'Peru',
                '.cl': 'Chile',
                '.ec': 'Ecuador',
                '.kr': 'South Korea',
                '.tw': 'Taiwan',
                '.hk': 'Hong Kong',
                '.gov': 'United States',  # .gov typically indicates US government
                '.mil': 'United States',  # .mil typically indicates US military
            }
            
            for tld, country_name in tld_to_country.items():
                if tld in email.lower():
                    logger.info(f"Found country in email TLD: {country_name}")
                    return country_name
            
            # Look for country domains in email address
            email_domain = email.split('@')[-1] if '@' in email else email
            country_domains = {
                'gov.uk': 'United Kingdom',
                'nic.in': 'India',
                'gov.in': 'India',
                'gc.ca': 'Canada',
                'gov.au': 'Australia',
                'go.jp': 'Japan',
                'gov.cn': 'China',
                'gov.ru': 'Russia',
                'gov.za': 'South Africa',
                'gob.mx': 'Mexico',
                'gov.ar': 'Argentina',
                'go.id': 'Indonesia',
                'gov.ph': 'Philippines',
                'gov.ng': 'Nigeria',
                'gov.pk': 'Pakistan',
                'go.ke': 'Kenya',
                'gov.rw': 'Rwanda',
                'go.tz': 'Tanzania',
                'go.ug': 'Uganda',
                'gov.gh': 'Ghana',
                'gov.sg': 'Singapore',
                'gov.my': 'Malaysia',
                'go.th': 'Thailand',
                'gov.vn': 'Vietnam'
            }
            
            for domain, country_name in country_domains.items():
                if domain in email_domain.lower():
                    logger.info(f"Found country in email domain: {country_name}")
                    return country_name
        
        # Try to infer from language
        if language and isinstance(language, str):
            language_to_country = {
                'en': 'United States',  # Default to US for English
                'fr': 'France',
                'de': 'Germany',
                'es': 'Spain',
                'it': 'Italy',
                'pt': 'Portugal',
                'ru': 'Russia',
                'zh': 'China',
                'ja': 'Japan',
                'ko': 'South Korea',
                'ar': 'Saudi Arabia',  # Default for Arabic
                'hi': 'India',
                'nl': 'Netherlands',
                'sv': 'Sweden',
                'no': 'Norway',
                'da': 'Denmark',
                'fi': 'Finland',
                'pl': 'Poland',
                'tr': 'Turkey',
                'he': 'Israel',
                'th': 'Thailand',
                'vi': 'Vietnam',
                'id': 'Indonesia',
                'uk': 'Ukraine'
            }
            
            if language.lower() in language_to_country:
                logger.info(f"Inferred country from language: {language_to_country[language.lower()]}")
                return language_to_country[language.lower()]
        
        # If all else fails, return "Unknown"
        logger.info("No country found, returning Unknown")
        return "Unknown"
        
    except Exception as e:
        # Ultimate fallback for ANY error
        logger = logging.getLogger(__name__)
        logger.error(f"CRITICAL ERROR in ensure_country: {e}")
        logger.error(traceback.format_exc())
        return "Unknown"