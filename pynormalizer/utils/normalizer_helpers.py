"""
Helper functions for normalizers.
"""
import json
import logging
import re
from typing import Any, Dict, Optional, Tuple, List
from datetime import datetime
from pynormalizer.models.unified_model import UnifiedTender
from pynormalizer.utils.translation import translate_to_english

logger = logging.getLogger(__name__)

def normalize_document_links(links: Any) -> List[Dict[str, str]]:
    """
    Normalize document links to a consistent format.
    
    Args:
        links: Document links in various formats (string, list, dict, etc.)
        
    Returns:
        List of dictionaries with standardized format
    """
    if not links:
        return []
        
    normalized_links = []
    
    # Handle string format (single URL or JSON string)
    if isinstance(links, str):
        try:
            # Check if it's a JSON string
            parsed = json.loads(links)
            return normalize_document_links(parsed)
        except (json.JSONDecodeError, ValueError):
            # Single URL string
            if links.strip():
                url_type = "unknown"
                # Determine type based on extension
                if links.lower().endswith(".pdf"):
                    url_type = "pdf"
                elif links.lower().endswith((".xml", ".rss", ".atom")):
                    url_type = "xml"
                elif links.lower().endswith((".html", ".htm", ".aspx", ".php")):
                    url_type = "html"
                    
                normalized_links.append({
                    "url": links.strip(),
                    "type": url_type,
                    "language": "en"  # Default language
                })
    
    # Handle list format
    elif isinstance(links, list):
        for item in links:
            # List of strings (URLs)
            if isinstance(item, str):
                url = item.strip()
                if url:
                    url_type = "unknown"
                    # Determine type based on extension
                    if url.lower().endswith(".pdf"):
                        url_type = "pdf"
                    elif url.lower().endswith((".xml", ".rss", ".atom")):
                        url_type = "xml"
                    elif url.lower().endswith((".html", ".htm", ".aspx", ".php")):
                        url_type = "html"
                        
                    normalized_links.append({
                        "url": url,
                        "type": url_type,
                        "language": "en"  # Default language
                    })
            # List of dictionaries
            elif isinstance(item, dict):
                if "link" in item or "url" in item:
                    url = item.get("link") or item.get("url")
                    if url and isinstance(url, str) and url.strip():
                        url_type = item.get("type", "unknown")
                        # If type not specified, try to determine from URL
                        if url_type == "unknown":
                            if url.lower().endswith(".pdf"):
                                url_type = "pdf"
                            elif url.lower().endswith((".xml", ".rss", ".atom")):
                                url_type = "xml"
                            elif url.lower().endswith((".html", ".htm", ".aspx", ".php")):
                                url_type = "html"
                                
                        normalized_links.append({
                            "url": url.strip(),
                            "type": url_type,
                            "language": item.get("language", "en"),
                            "description": item.get("description")
                        })
                else:
                    # Handle dictionaries without standard keys
                    for key, value in item.items():
                        if isinstance(value, str) and (value.strip().startswith(("http", "www.")) or 
                                                    any(value.lower().endswith(ext) for ext in 
                                                        (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".xml", ".html", ".htm"))):
                            url_type = "unknown"
                            if value.lower().endswith(".pdf"):
                                url_type = "pdf"
                            elif value.lower().endswith((".doc", ".docx")):
                                url_type = "doc"
                            elif value.lower().endswith((".xls", ".xlsx")):
                                url_type = "excel"
                            elif value.lower().endswith((".ppt", ".pptx")):
                                url_type = "presentation"
                            elif value.lower().endswith((".xml", ".rss", ".atom")):
                                url_type = "xml"
                            elif value.lower().endswith((".html", ".htm", ".aspx", ".php")):
                                url_type = "html"
                                
                            normalized_links.append({
                                "url": value.strip(),
                                "type": url_type,
                                "description": key if key != "url" and key != "link" else None
                            })
    
    # Handle dictionary format
    elif isinstance(links, dict):
        # Known dictionary formats (like TED EU with language-specific URLs)
        pdf_extensions = [".pdf", ".PDF"]
        xml_extensions = [".xml", ".XML"]
        html_extensions = [".html", ".htm", ".HTML", ".HTM", ".aspx", ".php"]
        doc_extensions = [".doc", ".docx", ".DOC", ".DOCX"]
        excel_extensions = [".xls", ".xlsx", ".XLS", ".XLSX"]
        
        # Process different sections
        for section, content in links.items():
            if isinstance(content, dict):
                # Handle language-specific links
                for lang, url in content.items():
                    if url and isinstance(url, str) and url.strip():
                        link_type = "unknown"
                        if section.lower() == "pdf" or any(url.endswith(ext) for ext in pdf_extensions):
                            link_type = "pdf"
                        elif section.lower() == "xml" or any(url.endswith(ext) for ext in xml_extensions):
                            link_type = "xml"
                        elif section.lower() == "html" or any(url.endswith(ext) for ext in html_extensions):
                            link_type = "html"
                        elif section.lower() in ["doc", "document", "word"] or any(url.endswith(ext) for ext in doc_extensions):
                            link_type = "doc"
                        elif section.lower() in ["xls", "excel", "spreadsheet"] or any(url.endswith(ext) for ext in excel_extensions):
                            link_type = "excel"
                            
                        normalized_links.append({
                            "url": url.strip(),
                            "type": link_type,
                            "language": lang
                        })
            elif isinstance(content, str) and content.strip():
                link_type = "unknown"
                if section.lower() == "pdf" or any(content.endswith(ext) for ext in pdf_extensions):
                    link_type = "pdf"
                elif section.lower() == "xml" or any(content.endswith(ext) for ext in xml_extensions):
                    link_type = "xml"
                elif section.lower() == "html" or any(content.endswith(ext) for ext in html_extensions):
                    link_type = "html"
                elif section.lower() in ["doc", "document", "word"] or any(content.endswith(ext) for ext in doc_extensions):
                    link_type = "doc"
                elif section.lower() in ["xls", "excel", "spreadsheet"] or any(content.endswith(ext) for ext in excel_extensions):
                    link_type = "excel"
                
                normalized_links.append({
                    "url": content.strip(),
                    "type": link_type,
                    "description": section if section not in ["pdf", "xml", "html", "doc", "excel"] else None
                })
            elif isinstance(content, list):
                # Handle lists nested in dictionaries
                for item in content:
                    if isinstance(item, str) and item.strip():
                        link_type = "unknown"
                        if any(item.endswith(ext) for ext in pdf_extensions):
                            link_type = "pdf"
                        elif any(item.endswith(ext) for ext in xml_extensions):
                            link_type = "xml"
                        elif any(item.endswith(ext) for ext in html_extensions):
                            link_type = "html"
                        elif any(item.endswith(ext) for ext in doc_extensions):
                            link_type = "doc"
                        elif any(item.endswith(ext) for ext in excel_extensions):
                            link_type = "excel"
                            
                        normalized_links.append({
                            "url": item.strip(),
                            "type": link_type,
                            "description": section if section not in ["pdf", "xml", "html", "doc", "excel"] else None
                        })
    
    return normalized_links

def apply_translations(unified: UnifiedTender, detected_language: Optional[str] = "auto") -> UnifiedTender:
    """
    Apply translations to a unified tender record.
    
    Args:
        unified: The unified tender record
        detected_language: Detected language code or "auto" for auto-detection
        
    Returns:
        Updated unified tender with translations
    """
    # Track translation methods used
    translation_methods = {}
    already_english_fields = []
    
    # Translate title
    if unified.title:
        unified.title_english, method = translate_to_english(unified.title, detected_language)
        if method:
            translation_methods["title"] = method
            if method == "already_english":
                already_english_fields.append("title")
    
    # Translate description
    if unified.description:
        unified.description_english, method = translate_to_english(unified.description, detected_language)
        if method:
            translation_methods["description"] = method
            if method == "already_english":
                already_english_fields.append("description")
    
    # Translate organization name
    if unified.organization_name:
        unified.organization_name_english, method = translate_to_english(unified.organization_name, detected_language)
        if method:
            translation_methods["organization_name"] = method
            if method == "already_english":
                already_english_fields.append("organization_name")
    
    # Translate project name
    if unified.project_name:
        unified.project_name_english, method = translate_to_english(unified.project_name, detected_language)
        if method:
            translation_methods["project_name"] = method
            if method == "already_english":
                already_english_fields.append("project_name")
    
    # Translate buyer
    if unified.buyer:
        unified.buyer_english, method = translate_to_english(unified.buyer, detected_language)
        if method:
            translation_methods["buyer"] = method
            if method == "already_english":
                already_english_fields.append("buyer")
    
    # Store translation methods used in normalized_method field
    if translation_methods:
        unified.normalized_method = json.dumps(translation_methods)
    
    # Set fallback_reason field if fields were already in English
    if already_english_fields:
        unified.fallback_reason = json.dumps({field: "already_english" for field in already_english_fields})
    
    return unified

def extract_financial_info(text: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Extract estimated value and currency from text.
    
    Args:
        text: Text to extract from
        
    Returns:
        Tuple of (estimated_value, currency)
    """
    if not text or not isinstance(text, str):
        return None, None
        
    # Look for currency symbols and amounts with more comprehensive patterns
    currency_patterns = {
        'USD': [
            r'US\$\s*([\d,\.]+(?:\s*million|\s*m|\s*billion|\s*b)?)',
            r'USD\s*([\d,\.]+(?:\s*million|\s*m|\s*billion|\s*b)?)',
            r'\$\s*([\d,\.]+(?:\s*million|\s*m|\s*billion|\s*b)?)',
            r'([\d,\.]+)\s*(?:US dollars|dollars|USD)'
        ],
        'EUR': [
            r'EUR\s*([\d,\.]+(?:\s*million|\s*m|\s*billion|\s*b)?)',
            r'€\s*([\d,\.]+(?:\s*million|\s*m|\s*billion|\s*b)?)',
            r'([\d,\.]+)\s*(?:euros|EUR|€)'
        ],
        'GBP': [
            r'GBP\s*([\d,\.]+(?:\s*million|\s*m|\s*billion|\s*b)?)',
            r'£\s*([\d,\.]+(?:\s*million|\s*m|\s*billion|\s*b)?)',
            r'([\d,\.]+)\s*(?:pounds|GBP|£)'
        ],
        'JPY': [
            r'JPY\s*([\d,\.]+(?:\s*million|\s*m|\s*billion|\s*b)?)',
            r'¥\s*([\d,\.]+(?:\s*million|\s*m|\s*billion|\s*b)?)',
            r'([\d,\.]+)\s*(?:yen|JPY|¥)'
        ],
        'CAD': [
            r'CAD\s*([\d,\.]+(?:\s*million|\s*m|\s*billion|\s*b)?)',
            r'C\$\s*([\d,\.]+(?:\s*million|\s*m|\s*billion|\s*b)?)',
            r'([\d,\.]+)\s*(?:Canadian dollars|CAD)'
        ],
        'AUD': [
            r'AUD\s*([\d,\.]+(?:\s*million|\s*m|\s*billion|\s*b)?)',
            r'A\$\s*([\d,\.]+(?:\s*million|\s*m|\s*billion|\s*b)?)',
            r'([\d,\.]+)\s*(?:Australian dollars|AUD)'
        ],
        'INR': [
            r'INR\s*([\d,\.]+(?:\s*lakhs?|\s*crores?|\s*million|\s*m|\s*billion|\s*b)?)',
            r'Rs\.\s*([\d,\.]+(?:\s*lakhs?|\s*crores?|\s*million|\s*m|\s*billion|\s*b)?)',
            r'₹\s*([\d,\.]+(?:\s*lakhs?|\s*crores?|\s*million|\s*m|\s*billion|\s*b)?)',
            r'([\d,\.]+)\s*(?:rupees|INR|Rs\.)'
        ],
        'CNY': [
            r'CNY\s*([\d,\.]+(?:\s*million|\s*m|\s*billion|\s*b)?)',
            r'元\s*([\d,\.]+(?:\s*million|\s*m|\s*billion|\s*b)?)',
            r'([\d,\.]+)\s*(?:yuan|CNY|元)'
        ],
        'MWK': [
            r'MWK\s*([\d,\.]+(?:\s*million|\s*m|\s*billion|\s*b)?)',
            r'K\s*([\d,\.]+(?:\s*million|\s*m|\s*billion|\s*b)?)',
            r'([\d,\.]+)\s*(?:kwacha|MWK)'
        ],
        'RWF': [
            r'RWF\s*([\d,\.]+(?:\s*million|\s*m|\s*billion|\s*b)?)',
            r'RF\s*([\d,\.]+(?:\s*million|\s*m|\s*billion|\s*b)?)',
            r'([\d,\.]+)\s*(?:Rwandan francs|RWF)'
        ]
    }
    
    for currency, patterns in currency_patterns.items():
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]  # Extract the first group if it's a tuple
                    
                    if match:
                        # Process the value
                        try:
                            # Remove commas from numbers
                            value_str = match.replace(',', '')
                            
                            # Handle million/billion/m/b suffixes
                            multiplier = 1
                            if any(suffix in value_str.lower() for suffix in ['million', ' m']):
                                multiplier = 1000000
                                value_str = re.sub(r'million|m', '', value_str, flags=re.IGNORECASE).strip()
                            elif any(suffix in value_str.lower() for suffix in ['billion', ' b']):
                                multiplier = 1000000000
                                value_str = re.sub(r'billion|b', '', value_str, flags=re.IGNORECASE).strip()
                            elif 'crore' in value_str.lower():
                                multiplier = 10000000  # 1 crore = 10 million
                                value_str = re.sub(r'crores?', '', value_str, flags=re.IGNORECASE).strip()
                            elif 'lakh' in value_str.lower():
                                multiplier = 100000  # 1 lakh = 100,000
                                value_str = re.sub(r'lakhs?', '', value_str, flags=re.IGNORECASE).strip()
                                
                            # Convert to float and apply multiplier
                            value = float(value_str) * multiplier
                            return value, currency
                        except (ValueError, TypeError):
                            pass
    
    # Generic pattern for numbers with currency codes
    generic_pattern = r'([\d,\.]+)\s*(?:million|m|billion|b)?\s*(USD|EUR|GBP|CAD|AUD|INR|JPY|CNY|MWK|RWF)'
    matches = re.findall(generic_pattern, text, re.IGNORECASE)
    
    if matches:
        for value_str, curr in matches:
            try:
                # Process the value
                value_str = value_str.replace(',', '')
                multiplier = 1
                
                if 'million' in text.lower() or ' m' in text.lower():
                    multiplier = 1000000
                elif 'billion' in text.lower() or ' b' in text.lower():
                    multiplier = 1000000000
                    
                value = float(value_str) * multiplier
                return value, curr.upper()
            except (ValueError, TypeError):
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