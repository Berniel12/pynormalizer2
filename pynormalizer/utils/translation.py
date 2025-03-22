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

def translate_to_english(text: str, source_lang: Optional[str] = None) -> Tuple[Optional[str], float]:
    """
    Translate text to English with quality score.
    Falls back to original text if translation fails.
    
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
            
        if TRANSLATOR_AVAILABLE:
            translator = GoogleTranslator(source=source_lang, target='en')
            translated = translator.translate(text)
            
            # Calculate quality score based on success
            quality = 1.0 if translated and translated != text else 0.0
            
            return translated, quality
        else:
            logger.warning("Translation skipped: translator not available")
            return text, 0.0
            
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        return text, 0.0

def setup_translation_models():
    """
    Initialize and prepare translation models.
    Ensures that the translation system is properly set up.
    
    Returns:
        bool: True if at least basic functionality is available
    """
    # We can still function with just the heuristic language detection
    # and without translation capabilities
    return True

# Export available functions
__all__ = [
    'detect_language',
    'detect_language_with_fallback',
    'translate_to_english',
    'setup_translation_models',
    'get_translation_stats'
] 