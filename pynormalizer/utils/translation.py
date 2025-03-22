"""
Translation utilities for normalizing tender data.
Provides robust translation capabilities using deep-translator.
"""
import logging
import time
from typing import Dict, Optional, Any, Tuple
import json
import re
from deep_translator import GoogleTranslator
from langdetect import detect, LangDetectException

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

# Set up deep-translator imports with robust error handling
TRANSLATOR_AVAILABLE = False

# Common words in different languages to help with detection
LANGUAGE_MARKERS = {
    'en': ['the', 'and', 'for', 'with', 'this', 'that', 'from', 'have', 'to', 'in', 'is', 'are', 'at', 'be', 'by'],
    'fr': ['le', 'la', 'les', 'un', 'une', 'des', 'et', 'pour', 'avec', 'ce', 'cette', 'de', 'du', 'au', 'aux'],
    'es': ['el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'y', 'para', 'con', 'este', 'esta', 'de', 'del'],
    'pt': ['o', 'a', 'os', 'as', 'um', 'uma', 'uns', 'umas', 'e', 'para', 'com', 'este', 'esta', 'de', 'do', 'da'],
    'de': ['der', 'die', 'das', 'ein', 'eine', 'und', 'für', 'mit', 'dieser', 'diese', 'von', 'zu', 'bei', 'aus'],
}

def detect_language_heuristic(text: str) -> Optional[str]:
    """
    Detect language using a simple heuristic based on common words.
    
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
    Returns None if detection fails.
    """
    if not text or len(text.strip()) < 10:
        return None
        
    try:
        return detect(text)
    except LangDetectException as e:
        logger.warning(f"Language detection failed: {e}")
        return None

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

try:
    # Try to import deep_translator
    GoogleTranslator = GoogleTranslator
    TRANSLATOR_AVAILABLE = True
    logger.info("Successfully imported deep-translator")
    
except Exception as e:
    logger.error(f"Failed to import deep-translator: {e}")
    
    # Create a dummy translator for fallback
    class DummyTranslator:
        def __init__(self, source="auto", target="en"):
            self.source = source
            self.target = target
        
        def translate(self, text):
            logger.warning("Translation unavailable: deep-translator could not be imported")
            return text
    
    GoogleTranslator = DummyTranslator

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

def test_translation_setup():
    """Test the translation setup to ensure it's working correctly."""
    global TRANSLATOR_AVAILABLE
    
    if not TRANSLATOR_AVAILABLE:
        logger.warning("Translation setup test skipped: deep-translator not available")
        return False
    
    try:
        # Test language detection
        if is_english_text("Hello world"):
            logger.info("English detection test passed")
        else:
            logger.warning("English detection test failed")
            return False
            
        if not is_english_text("Bonjour le monde"):
            logger.info("French detection test passed")
        else:
            logger.warning("French detection test failed")
            return False
        
        # Test a simple translation
        translator = GoogleTranslator(source='fr', target='en')
        result = translator.translate("bonjour")
        
        valid_translations = ["hello", "good morning", "hello there"]
        if result and result.lower() in valid_translations:
            logger.info("Translation test successful")
            return True
        else:
            logger.warning(f"Translation test failed - unexpected result: {result}")
            TRANSLATOR_AVAILABLE = False
            return False
    except Exception as e:
        logger.error(f"Translation test failed with error: {str(e)}")
        TRANSLATOR_AVAILABLE = False
        return False

def is_english_text(text: str) -> bool:
    """
    Determine if text is likely already in English.
    
    Args:
        text: The text to check
        
    Returns:
        True if the text is likely English, False otherwise
    """
    if not text or len(text) < 5:
        return True
    
    # Known non-English words that indicate other languages
    french_words = ["bonjour", "monde", "merci", "être", "jour", "français", "votre", "vous", "cette"]
    spanish_words = ["hola", "gracias", "buenos", "días", "español", "hacer", "mundo"]
    german_words = ["danke", "bitte", "guten", "morgen", "deutsch", "nicht", "hallo"]
    
    text_lower = text.lower()
    
    # Check for common non-English words
    for word in french_words + spanish_words + german_words:
        if f" {word} " in f" {text_lower} " or text_lower.startswith(f"{word} ") or text_lower.endswith(f" {word}"):
            return False
    
    # Count non-ASCII characters - English text typically has very few
    non_ascii_ratio = sum(1 for c in text if ord(c) > 127) / len(text)
    if non_ascii_ratio > 0.05:  # More than 5% non-ASCII suggests non-English
        return False
    
    # Check for common English words
    english_markers = LANGUAGE_MARKERS['en']
    
    # Count English markers
    english_marker_count = 0
    for marker in english_markers:
        pattern = r'\b' + re.escape(marker) + r'\b'
        english_marker_count += len(re.findall(pattern, text_lower))
    
    # Check for non-English markers
    non_english_marker_count = 0
    for lang, markers in LANGUAGE_MARKERS.items():
        if lang == 'en':
            continue
        for marker in markers:
            pattern = r'\b' + re.escape(marker) + r'\b'
            non_english_marker_count += len(re.findall(pattern, text_lower))
    
    # If more non-English markers than English markers, it's likely not English
    if non_english_marker_count > english_marker_count:
        return False
        
    # If we find several English markers and few non-English markers, it's likely English
    if english_marker_count >= 2 and english_marker_count > non_english_marker_count:
        return True
    
    # Language detection using our heuristic
    detected = detect_language_heuristic(text)
    if detected and detected != 'en':
        return False
    
    # Default behavior - if no strong signals, assume English
    return True

def translate_to_english(text: str, source_lang: Optional[str] = None) -> Tuple[Optional[str], float]:
    """
    Translate text to English with quality score.
    
    Args:
        text: Text to translate
        source_lang: Source language code (if known)
        
    Returns:
        Tuple of (translated_text, quality_score)
        quality_score ranges from 0.0 to 1.0
    """
    if not text:
        return None, 0.0
        
    try:
        # Detect language if not provided
        if not source_lang:
            source_lang = detect_language_with_fallback(text)
            
        # Skip translation if already English
        if source_lang == 'en':
            return text, 1.0
            
        translator = GoogleTranslator(source=source_lang, target='en')
        translated = translator.translate(text)
        
        # Calculate quality score based on success
        quality = 1.0 if translated and translated != text else 0.0
        
        return translated, quality
        
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        return None, 0.0

def get_supported_languages() -> Dict[str, str]:
    """
    Get the dictionary of supported language codes and their names.
    
    Returns:
        Dictionary mapping ISO language codes to language names
    """
    return SUPPORTED_LANGS

def get_translation_stats() -> dict:
    """Get statistics about translation usage and performance."""
    # TODO: Implement translation statistics tracking
    return {
        "translations_performed": 0,
        "average_quality": 0.0,
        "errors": 0
    }

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
            
        # Translate and track the method used
        translated_value, method = translate_to_english(original_value, source_language)
        
        # Set the translated field
        if hasattr(unified_tender, f"{field}_english"):
            setattr(unified_tender, f"{field}_english", translated_value)
            
            # Track fallback reasons
            if method:
                fallback_reason[field] = method
    
    # Store fallback reasons in the normalized_method field if available
    if hasattr(unified_tender, "fallback_reason") and fallback_reason:
        # Store as a JSON string instead of a dict to avoid serialization issues
        unified_tender.fallback_reason = json.dumps(fallback_reason)
    
    if hasattr(unified_tender, "normalized_method") and not getattr(unified_tender, "normalized_method", None):
        if TRANSLATOR_AVAILABLE:
            unified_tender.normalized_method = "deep-translator"
        else:
            unified_tender.normalized_method = "no-translation"
    
    return unified_tender

def setup_translation_models():
    """
    Initialize and prepare translation models.
    Ensures that the translation system is properly set up.
    
    This function is called at the start of the normalization process
    to ensure translation capabilities are available.
    
    Returns:
        bool: True if translation setup was successful, False otherwise
    """
    global TRANSLATOR_AVAILABLE
    
    # Test the translation setup to ensure it's working
    result = test_translation_setup()
    
    if result:
        logger.info("Translation models successfully set up")
    else:
        logger.warning("Translation models setup failed, using fallbacks")
    
    return result

# Automatically test the translation setup when the module is imported
test_translation_setup()

__all__ = [
    'detect_language',
    'detect_language_with_fallback',
    'translate_to_english',
    'setup_translation_models',
    'get_translation_stats'
] 