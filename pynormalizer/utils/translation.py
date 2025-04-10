"""
Translation utilities for normalizing tender data.
Provides robust translation capabilities with fallbacks.
"""
import logging
import time
from typing import Dict, Optional, Any, Tuple
import json
import re

# Initialize logger
logger = logging.getLogger(__name__)

# Translation statistics for logging
TRANSLATION_STATS = {
    "total_requests": 0,
    "success": 0,
    "already_english": 0,
    "failed": 0,
    "encoding_fixed": 0,
    "languages": {}
}

# Set up imports with robust error handling
TRANSLATOR_AVAILABLE = False
LANGDETECT_AVAILABLE = False
GoogleTranslator = None
detect = None

# Define supported language codes
SUPPORTED_LANGS = {
    'ar': 'Arabic',
    'zh': 'Chinese',
    'nl': 'Dutch',
    'en': 'English',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'es': 'Spanish'
}

# Common words in different languages to help with detection
LANGUAGE_MARKERS = {
    'en': ['the', 'and', 'for', 'with', 'this', 'that', 'from', 'have', 'to', 'in', 'is', 'are', 'at', 'be', 'by'],
    'fr': ['le', 'la', 'les', 'un', 'une', 'des', 'et', 'pour', 'avec', 'ce', 'cette', 'de', 'du', 'au', 'aux'],
    'es': ['el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'y', 'para', 'con', 'este', 'esta', 'de', 'del'],
    'pt': ['o', 'a', 'os', 'as', 'um', 'uma', 'uns', 'umas', 'e', 'para', 'com', 'este', 'esta', 'de', 'do', 'da'],
    'de': ['der', 'die', 'das', 'ein', 'eine', 'und', 'für', 'mit', 'dieser', 'diese', 'von', 'zu', 'bei', 'aus'],
}

# Minimal character encoding corrections for common issues
ENCODING_CORRECTIONS = {
    # French special characters
    "Fran aise": "Française",
    "D veloppement": "Développement",
    "Developpement": "Développement",
    "Francaise": "Française",
    # Spanish special characters
    "Adquisicion": "Adquisición",
    "Informacion": "Información",
    "administracion": "administración",
    # Organizations
    "Agence Fran aise de D veloppement": "Agence Française de Développement",
    "Agence Francaise de Developpement": "Agence Française de Développement",
}

def detect_language_heuristic(text: str) -> Optional[str]:
    """
    Detect language using a simple heuristic based on common words.
    This is used as a fallback when langdetect is not available.
    
    Args:
        text: Text to detect language for
        
    Returns:
        ISO language code or None if detection fails
    """
    if not text or len(text) < 5:
        return None
        
    text_lower = text.lower()
    
    # Count language markers for each language
    lang_scores = {}
    for lang, markers in LANGUAGE_MARKERS.items():
        lang_scores[lang] = 0
        for marker in markers:
            pattern = r'\b' + re.escape(marker) + r'\b'
            matches = re.findall(pattern, text_lower)
            lang_scores[lang] += len(matches)
    
    # Find the language with the highest score
    max_score = 0
    detected_lang = None
    for lang, score in lang_scores.items():
        if score > max_score:
            max_score = score
            detected_lang = lang
    
    # Set a minimum threshold for detection confidence
    if max_score < 2:
        return None
        
    return detected_lang

def detect_language(text: str) -> Optional[str]:
    """
    Detect the language of a text string.
    Uses langdetect if available, falls back to heuristic method.
    
    Args:
        text: Text to detect language for
        
    Returns:
        ISO language code or None if detection fails
    """
    if not text or len(text.strip()) < 10:
        return None
        
    # Try langdetect first if available
    if LANGDETECT_AVAILABLE:
        try:
            return detect(text)
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
    
    # Fall back to heuristic method
    return detect_language_heuristic(text)

def detect_language_with_fallback(text: str, default_language: str = 'en') -> str:
    """
    Detect language with fallback to default if detection fails.
    
    Args:
        text: Text to detect language from
        default_language: Language code to return if detection fails
        
    Returns:
        Detected language code or default_language if detection fails
    """
    if not text or len(text.strip()) < 10:
        return default_language
        
    try:
        detected = detect_language(text)
        return detected if detected else default_language
    except Exception as e:
        logger.warning(f"Language detection failed: {e}")
        return default_language

def fix_character_encoding(text: Optional[str]) -> Optional[str]:
    """
    Fix common character encoding issues in the text.
    
    Args:
        text: The text to fix character encoding in
        
    Returns:
        The text with fixed character encoding
    """
    if not text:
        return text
    
    original = text
    # Apply the encoding corrections
    for incorrect, correct in ENCODING_CORRECTIONS.items():
        text = text.replace(incorrect, correct)
    
    # Log if we made changes
    if original != text:
        TRANSLATION_STATS["encoding_fixed"] += 1
        logger.debug(f"Fixed encoding issues in text")
    
    return text

def translate_to_english(text, source_language=None):
    """
    Translate text to English using deep-translator.
    """
    if not text:
        return text, 0.0
    
    # Map language codes to supported formats
    language_mapping = {
        'LAV': 'lv',  # Latvian
        'ENG': 'en',  # English
        'FIN': 'fi',  # Finnish
        'RON': 'ro',  # Romanian
        'FRA': 'fr',  # French
        'SWE': 'sv',  # Swedish
        'POL': 'pl',  # Polish
        'ITA': 'it',  # Italian
        'DEU': 'de',  # German
        'NLD': 'nl',  # Dutch
        'SPA': 'es',  # Spanish
        'POR': 'pt',  # Portuguese
        'RUS': 'ru',  # Russian
        'ARA': 'ar',  # Arabic
        'ZHO': 'zh-CN',  # Chinese
        'JPN': 'ja',  # Japanese
        'HIN': 'hi',  # Hindi
        'KOR': 'ko',  # Korean
        'TUR': 'tr',  # Turkish
        'VIE': 'vi',  # Vietnamese
        'THA': 'th',  # Thai
        'ELL': 'el',  # Greek
        'HUN': 'hu',  # Hungarian
        'CES': 'cs',  # Czech
        'DAN': 'da',  # Danish
        'NOR': 'no',  # Norwegian
        'BUL': 'bg',  # Bulgarian
        'HRV': 'hr',  # Croatian
        'UKR': 'uk',  # Ukrainian
        'CAT': 'ca'   # Catalan
    }
    
    # If source language is provided, map it to supported code
    mapped_source = 'auto'  # Default to auto detection
    if source_language:
        if source_language in language_mapping:
            mapped_source = language_mapping[source_language]
        else:
            logger.warning(f"Unmapped language code: {source_language}, using auto detection")
    
    # If English or already in English, return as is
    if mapped_source == 'en' or source_language == 'ENG':
        return text, 1.0
    
    try:
        # Try using Google Translate with the mapped source language
        translator = GoogleTranslator(source=mapped_source, target='en')
        translated = translator.translate(text)
        return translated, 0.8
    except Exception as e:
        error_message = str(e)
        # If it's a language support error, try with auto-detection
        if "No support for the provided language" in error_message:
            try:
                logger.warning(f"Language {mapped_source} not supported, falling back to auto-detection")
                translator = GoogleTranslator(source='auto', target='en')
                translated = translator.translate(text)
                return translated, 0.6  # Lower confidence since we used auto-detection
            except Exception as inner_e:
                logger.error(f"Auto-detection translation failed: {str(inner_e)}")
        else:
            logger.error(f"Translation error: {source_language} ({mapped_source}) --> {error_message}")
        
        # Return original text as fallback for unsupported languages
        return text, 0.0

def get_translation_stats() -> Dict[str, Any]:
    """Get statistics about translation usage and performance."""
    return TRANSLATION_STATS

def get_supported_languages() -> Dict[str, str]:
    """
    Get the dictionary of supported language codes and their names.
    
    Returns:
        Dictionary mapping ISO language codes to language names
    """
    return SUPPORTED_LANGS

def apply_translations(unified_tender: Any, source_language: Optional[str] = None) -> Any:
    """
    Apply translations to all relevant fields in a UnifiedTender object.
    
    Args:
        unified_tender: The UnifiedTender object to translate fields for
        source_language: Optional source language code, if known
        
    Returns:
        Updated UnifiedTender with translated fields
    """
    # Fields to translate from source language to English
    fields_to_translate = [
        'title',
        'description',
        'organization_name',
        'buyer',
        'project_name',
    ]
    
    # Store fallback reasons to track translation methods
    fallback_reason = {}
    
    # Skip translation if source language is English or not detected
    if source_language == "en":
        # Copy original values to *_english fields
        for field in fields_to_translate:
            if hasattr(unified_tender, f"{field}_english") and getattr(unified_tender, field):
                setattr(unified_tender, f"{field}_english", getattr(unified_tender, field))
        return unified_tender
    
    # Translate each field
    for field in fields_to_translate:
        # Get the original field value
        original_value = getattr(unified_tender, field, None)
        if not original_value:
            continue
            
        # Skip if already translated
        if hasattr(unified_tender, f"{field}_english") and getattr(unified_tender, f"{field}_english", None):
            continue
            
        # Fix character encoding first
        original_value = fix_character_encoding(original_value)
            
        # Translate and track the method used
        translated_value, quality = translate_to_english(original_value, source_language)
        
        # Set the translated field
        if hasattr(unified_tender, f"{field}_english"):
            setattr(unified_tender, f"{field}_english", translated_value)
            
            # Track fallback reasons
            if quality > 0:
                fallback_reason[field] = "deep-translator"
            else:
                fallback_reason[field] = "no-translation"
    
    # Store fallback reasons in the fallback_reason field if available
    if hasattr(unified_tender, "fallback_reason") and fallback_reason:
        # Store as a JSON string instead of a dict to avoid serialization issues
        unified_tender.fallback_reason = json.dumps(fallback_reason)
    
    return unified_tender

def setup_translation_models():
    """
    Initialize and prepare translation models.
    Ensures that the translation system is properly set up.
    
    Returns:
        bool: True if at least basic functionality is available
    """
    global TRANSLATOR_AVAILABLE, LANGDETECT_AVAILABLE, GoogleTranslator, detect
    
    # Try importing translation dependencies
    try:
        from deep_translator import GoogleTranslator
        TRANSLATOR_AVAILABLE = True
        logger.info("Successfully imported deep-translator")
    except Exception as e:
        logger.warning(f"Failed to import deep-translator: {e}")
        
        # Create a dummy translator for fallback
        class DummyTranslator:
            def __init__(self, source="auto", target="en"):
                self.source = source
                self.target = target
            
            def translate(self, text):
                logger.warning("Translation unavailable: deep-translator could not be imported")
                return text
        
        GoogleTranslator = DummyTranslator
    
    # Try importing language detection
    try:
        from langdetect import detect
        LANGDETECT_AVAILABLE = True
        logger.info("Successfully imported langdetect")
    except Exception as e:
        logger.warning(f"Failed to import langdetect: {e}")
        detect = lambda x: detect_language_heuristic(x)
    
    # We can still function with just the heuristic language detection
    # and without translation capabilities
    return True

# Export available functions
__all__ = [
    'detect_language',
    'detect_language_with_fallback',
    'translate_to_english',
    'setup_translation_models',
    'get_translation_stats',
    'get_supported_languages',
    'apply_translations',
    'fix_character_encoding'
] 