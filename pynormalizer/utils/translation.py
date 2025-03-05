"""
Translation utilities for normalizing tender data.
Provides robust translation capabilities using deep-translator.
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

# Set up deep-translator imports with robust error handling
TRANSLATOR_AVAILABLE = False
GoogleTranslator = None
detect_language_func = None

try:
    # Try to import deep_translator
    from deep_translator import GoogleTranslator as dt_GoogleTranslator
    from deep_translator import detect_language as dt_detect_language
    
    # Define a wrapped detection function that handles errors
    def detect_language_func(text):
        try:
            return dt_detect_language(text)
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return None
    
    # Set up the translator
    GoogleTranslator = dt_GoogleTranslator
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
    
    # Create a dummy detection function
    def detect_language_func(text):
        logger.warning("Language detection unavailable")
        return None

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
        # Test a simple translation
        translator = GoogleTranslator(source='fr', target='en')
        result = translator.translate("bonjour")
        
        if result and result.lower() == "hello":
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
    
    # Count non-ASCII characters - English text typically has very few
    non_ascii_ratio = sum(1 for c in text if ord(c) > 127) / len(text)
    if non_ascii_ratio > 0.05:  # More than 5% non-ASCII suggests non-English
        return False
    
    # Check for common English words
    english_markers = ["the", "and", "for", "with", "this", "that", "from", "have", "to", "in"]
    text_lower = text.lower()
    
    # Count English markers
    english_marker_count = 0
    for marker in english_markers:
        pattern = r'\b' + re.escape(marker) + r'\b'
        english_marker_count += len(re.findall(pattern, text_lower))
    
    # If we find several English markers, it's likely English
    if english_marker_count >= 2:
        return True
    
    # Use language detection as a fallback if available
    if TRANSLATOR_AVAILABLE:
        try:
            detected = detect_language_func(text[:500])  # Limit to first 500 chars for speed
            return detected == "en"
        except Exception:
            pass
    
    # Default behavior - assume not English if we're unsure
    return False

def translate_to_english(text: Optional[str], src_lang: Optional[str] = "auto") -> Tuple[Optional[str], Optional[str]]:
    """
    Translate text to English using deep-translator.
    
    Args:
        text: Text to translate
        src_lang: Source language code or "auto" for auto-detection
        
    Returns:
        Tuple of (translated_text, method_used)
    """
    global TRANSLATION_STATS
    
    # Track total requests
    TRANSLATION_STATS["total_requests"] += 1
    
    # Handle None or empty text
    if not text or len(text.strip()) == 0:
        return None, None
    
    # Fix common character encoding issues
    text = fix_character_encoding(text)
    
    # Skip translation if already English
    if is_english_text(text):
        TRANSLATION_STATS["already_english"] += 1
        return text, "already_english"
    
    # Skip translation if not available
    if not TRANSLATOR_AVAILABLE:
        TRANSLATION_STATS["failed"] += 1
        return text, "translator_unavailable"
    
    # Detect language if set to auto
    if src_lang == "auto":
        detected = detect_language_func(text[:500])
        if detected:
            src_lang = detected
            # Log the detected language
            if detected not in TRANSLATION_STATS["languages"]:
                TRANSLATION_STATS["languages"][detected] = 0
            TRANSLATION_STATS["languages"][detected] += 1
    
    # Primary translation with retry mechanism
    for attempt in range(3):  # Try up to 3 times
        try:
            # Create translator with the appropriate source language
            translator = GoogleTranslator(source=src_lang if src_lang != "auto" else "auto", target='en')
            
            # Split text into smaller chunks if it's too long
            if len(text) > 5000:
                chunks = []
                for i in range(0, len(text), 4000):
                    chunks.append(text[i:i+4000])
                
                # Translate each chunk and combine
                translated_chunks = []
                for chunk in chunks:
                    translated_chunk = translator.translate(chunk)
                    if translated_chunk:
                        translated_chunks.append(translated_chunk)
                    else:
                        # If a chunk fails, try again with a different boundary
                        logger.warning(f"Chunk translation failed, retrying with different boundary")
                        continue
                
                # Combine translated chunks
                if translated_chunks:
                    TRANSLATION_STATS["success"] += 1
                    return " ".join(translated_chunks), None
            else:
                # Translate the whole text at once for smaller texts
                translated = translator.translate(text)
                if translated:
                    TRANSLATION_STATS["success"] += 1
                    return translated, None
        
        except Exception as e:
            logger.warning(f"Translation attempt {attempt+1} failed: {e}")
            if attempt < 2:  # Don't sleep on the last attempt
                time.sleep(1)  # Wait before retry
            continue
    
    # If all translation attempts fail
    TRANSLATION_STATS["failed"] += 1
    return text, "translation_failed"

def get_supported_languages() -> Dict[str, str]:
    """
    Get the dictionary of supported language codes and their names.
    
    Returns:
        Dictionary mapping ISO language codes to language names
    """
    return SUPPORTED_LANGS

def get_translation_stats() -> Dict[str, Any]:
    """Get statistics about translations performed."""
    return TRANSLATION_STATS

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

# Automatically test the translation setup when the module is imported
test_translation_setup() 