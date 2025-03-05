"""
Translation utilities for normalizing tender data.
Provides lightweight translation capabilities using deep-translator.
"""
import os
import logging
from typing import Dict, Optional, List, Set, Any, Tuple
import json
import time
from pathlib import Path
import re

# Initialize logger
logger = logging.getLogger(__name__)

# Translation statistics for logging
TRANSLATION_STATS = {
    "total_requests": 0,
    "success": 0,
    "fallback_used": 0,
    "already_english": 0,
    "failed": 0,
    "encoding_fixed": 0,
    "languages": {}
}

# Try to import deep-translator
try:
    from deep_translator import (
        GoogleTranslator, 
        LingueeTranslator,
        DeepL,
        detect_language
    )
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False
    logger.warning("deep-translator not available. Install with pip install deep-translator")

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

# Character encoding corrections
ENCODING_CORRECTIONS = {
    # French special characters
    "Fran aise": "Française",
    "D veloppement": "Développement",
    "Developpement": "Développement",
    "Francaise": "Française",
    "a ": "à ",
    "e ": "è ",
    " a ": " à ",
    " e ": " è ",
    # Spanish special characters
    "Adquisicion": "Adquisición",
    "modernizacion": "modernización",
    "Informacion": "Información",
    "electronico": "electrónico",
    "administracion": "administración",
    # Organizations
    "Agence Fran aise de D veloppement": "Agence Française de Développement",
    "Agence Francaise de Developpement": "Agence Française de Développement",
    # Add other common patterns
}

# Extended fallback dictionary with common terms in multiple languages
FALLBACK_DICT = {
    # French terms
    "appel d'offres": "call for tender",
    "marché public": "public procurement",
    "appel à manifestation d'intérêt": "call for expression of interest",
    "développement": "development",
    "française": "french",
    "matériels": "equipment",
    "sonorisation": "sound system",
    "alerte": "alert",
    "acquisition": "acquisition",
    "installation": "installation",
    
    # Spanish terms
    "adquisición": "acquisition",
    "licitación": "tender",
    "contratación": "contracting",
    "administración": "administration",
    "proyecto": "project",
    "modernización": "modernization",
    "escritorio": "desktop",
    "portátiles": "laptops",
    "actualizado": "updated",
    
    # Organization names
    "Agence Française de Développement": "French Development Agency",
    "Banco Interamericano de Desarrollo": "Inter-American Development Bank",
    "Rwanda Information Society Authority": "Rwanda Information Society Authority",
    
    # Add many more common terms
}

# Extended list of French words to detect French language
FRENCH_WORDS = {
    "le", "la", "les", "un", "une", "des", "et", "ou", "pour", "dans", "sur", 
    "avec", "sans", "par", "du", "au", "aux", "de", "des", "appel", "offre", 
    "développement", "française", "projet", "marché", "services", "travaux"
}

# Extended list of Spanish words to detect Spanish language
SPANISH_WORDS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "y", "o", "para", 
    "en", "sobre", "con", "sin", "por", "del", "al", "adquisición", "proyecto",
    "servicios", "proceso", "contratación", "modernización"
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
    # Apply all the encoding corrections
    for incorrect, correct in ENCODING_CORRECTIONS.items():
        text = text.replace(incorrect, correct)
    
    # Log if we made changes
    if original != text:
        TRANSLATION_STATS["encoding_fixed"] += 1
        logger.debug(f"Fixed encoding: '{original}' -> '{text}'")
    
    return text

def setup_translation_models():
    """Initialize translation capabilities. No heavy downloads required with deep-translator."""
    if not TRANSLATOR_AVAILABLE:
        logger.warning("Translation not available. Install deep-translator with pip install deep-translator")
        return
    
    try:
        # Check translator is working by testing a simple translation
        translated = GoogleTranslator(source='auto', target='en').translate("test")
        logger.info("Deep-translator initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing deep-translator: {e}")

def detect_language(text: Optional[str]) -> Optional[str]:
    """
    Detect the language of a text using deep-translator and enhanced language detection.
    
    Args:
        text: Text to detect language for
        
    Returns:
        ISO language code or None if detection fails
    """
    if not text or len(text) < 10:
        return None
    
    # First, fix any character encoding issues
    text = fix_character_encoding(text)
    
    # Check for French content specifically with common French words
    text_lower = text.lower()
    french_word_count = 0
    for word in FRENCH_WORDS:
        french_word_count += len(re.findall(r'\b' + re.escape(word) + r'\b', text_lower))
    
    if french_word_count >= 3:
        logger.debug(f"Detected French with {french_word_count} French words")
        return "fr"
    
    # Check for Spanish content specifically with common Spanish words
    spanish_word_count = 0
    for word in SPANISH_WORDS:
        spanish_word_count += len(re.findall(r'\b' + re.escape(word) + r'\b', text_lower))
    
    if spanish_word_count >= 3:
        logger.debug(f"Detected Spanish with {spanish_word_count} Spanish words")
        return "es"
    
    # Check if the text is predominantly English by looking for common English words
    english_markers = ["the", "and", "for", "with", "this", "that", "from", "have", "will"]
    total_english_markers = 0
    english_threshold = 0.6  # 60% threshold for declaring text as English
    
    # Count English markers
    total_words = len([w for w in text_lower.split() if len(w) > 1])
    
    if total_words > 0:
        for marker in english_markers:
            pattern = r'\b' + marker + r'\b'
            total_english_markers += len(re.findall(pattern, text_lower))
        
        # If significant proportion of words are English markers, treat as English
        if total_english_markers / total_words > english_threshold:
            return "en"
    
    if not TRANSLATOR_AVAILABLE:
        return None
    
    try:
        # Use deep-translator's detection with retry
        for attempt in range(3):  # Try up to 3 times
            try:
                detected = detect_language(text[:500])  # Limit detection to first 500 chars for speed
                if detected in SUPPORTED_LANGS:
                    logger.debug(f"Detected language: {detected}")
                    return detected
            except Exception as e:
                if attempt < 2:  # Don't sleep on the last attempt
                    time.sleep(1)  # Wait before retry
                continue
    except Exception as e:
        logger.warning(f"Language detection failed after retries: {e}")
    
    # Fallback to our own detection method
    language_markers = {
        "fr": ["le", "la", "les", "de", "et", "en", "pour", "dans", "un", "une", "est", "sont", "par", "sur"],
        "es": ["el", "la", "los", "las", "de", "y", "en", "para", "un", "una", "es", "son", "por", "sobre"],
        "de": ["der", "die", "das", "und", "in", "für", "ein", "eine", "mit", "von", "zu", "ist", "sind", "auf"],
        "pt": ["o", "a", "os", "as", "de", "e", "em", "para", "um", "uma", "é", "são", "por", "sobre"],
        "it": ["il", "la", "i", "le", "di", "e", "in", "per", "un", "una", "è", "sono", "con", "su"],
        "ru": ["и", "в", "не", "на", "я", "что", "тот", "быть", "с", "он", "а", "весь", "это", "как"],
        "ar": ["في", "من", "إلى", "على", "و", "ل", "ب", "ان", "هذا", "أن", "عن", "هو", "مع", "أو"],
        "zh": ["的", "了", "和", "在", "是", "我", "有", "他", "这", "不", "人", "们", "一", "来"]
    }
    
    word_counts = {}
    
    for lang, markers in language_markers.items():
        count = 0
        for marker in markers:
            # Count occurrences of marker words with word boundaries
            count += len(re.findall(r'\b' + re.escape(marker) + r'\b', text_lower))
        word_counts[lang] = count
    
    # If no markers found, assume English
    if max(word_counts.values(), default=0) == 0:
        return "en"
    
    # Return the language with the most marker words
    most_likely_lang = max(word_counts.items(), key=lambda x: x[1])[0]
    
    # Only return the language if it has a significant count
    if word_counts[most_likely_lang] > 3:
        return most_likely_lang
    
    # Default to English if nothing else determined
    return "en"

def translate_to_english(text: Optional[str], src_lang: Optional[str] = "auto", 
                         use_fallback: bool = True) -> tuple[Optional[str], Optional[str]]:
    """
    Translate text to English using deep-translator with enhanced robustness.
    
    Args:
        text: Text to translate
        src_lang: Source language code or "auto" for auto-detection
        use_fallback: Whether to use fallback methods if primary translation fails
        
    Returns:
        Tuple of (translated_text, method_used)
    """
    global TRANSLATION_STATS
    
    # Track total requests
    TRANSLATION_STATS["total_requests"] += 1
    
    # Handle None or empty texts
    if not text or len(text.strip()) == 0:
        return None, None
    
    # First fix any character encoding issues
    text = fix_character_encoding(text)
    
    # Detect language if set to auto
    detected_lang = src_lang
    if src_lang == "auto":
        detected_lang = detect_language(text)
        
    # Check if language detection identified it as non-English
    # by checking for specific non-English words that indicate it is not English
    is_definitely_not_english = False
    if any(word in text.lower().split() for word in FRENCH_WORDS) or \
       any(word in text.lower().split() for word in SPANISH_WORDS):
        is_definitely_not_english = True
    
    # Skip translation if already English and not definitely non-English
    if detected_lang == "en" and not is_definitely_not_english:
        # But verify it's really English using our enhanced detection
        if len(text.split()) > 3:  # Only check if more than 3 words
            english_markers = ["the", "and", "for", "with", "this", "that", "from", "have", "will"]
            text_lower = text.lower()
            english_marker_count = 0
            
            for marker in english_markers:
                english_marker_count += len(re.findall(r'\b' + re.escape(marker) + r'\b', text_lower))
            
            # If English markers are found, it's likely English
            if english_marker_count > 0:
                TRANSLATION_STATS["already_english"] += 1
                if "en" not in TRANSLATION_STATS["languages"]:
                    TRANSLATION_STATS["languages"]["en"] = 0
                TRANSLATION_STATS["languages"]["en"] += 1
                return text, "already_english"
    
    # If no translator available, return original
    if not TRANSLATOR_AVAILABLE:
        TRANSLATION_STATS["failed"] += 1
        return text, "failed"
    
    # Record the detected language in stats
    if detected_lang:
        if detected_lang not in TRANSLATION_STATS["languages"]:
            TRANSLATION_STATS["languages"][detected_lang] = 0
        TRANSLATION_STATS["languages"][detected_lang] += 1
    
    # Primary translation method with retry
    for attempt in range(3):  # Try up to 3 times
        try:
            # Use the detected language if available, otherwise use auto
            source_lang = detected_lang if detected_lang else "auto"
            translated = GoogleTranslator(source=source_lang, target='en').translate(text)
            
            if translated:
                TRANSLATION_STATS["success"] += 1
                return translated, None
        except Exception as e:
            logger.warning(f"Translation attempt {attempt+1} failed: {e}")
            if attempt < 2:  # Don't sleep on the last attempt
                time.sleep(1)  # Wait before retry
            continue
    
    # If primary translation failed and fallback is enabled
    if use_fallback:
        # Use our own word replacement method
        try:
            # Start with a copy of the original text
            translated_text = text
            
            # Apply word-by-word replacement
            for src_word, tgt_word in FALLBACK_DICT.items():
                # Replace full words with word boundaries
                translated_text = re.sub(r'\b' + re.escape(src_word) + r'\b', tgt_word, translated_text, flags=re.IGNORECASE)
            
            TRANSLATION_STATS["fallback_used"] += 1
            return translated_text, "offline_dictionary"
        except Exception as e:
            logger.error(f"Fallback translation failed: {e}")
    
    # If all translation methods failed
    TRANSLATION_STATS["failed"] += 1
    return text, "failed"

def get_supported_languages() -> Dict[str, str]:
    """
    Get the dictionary of supported language codes and their names.
    
    Returns:
        Dictionary mapping ISO language codes to language names
    """
    return SUPPORTED_LANGS

def get_translation_stats() -> Dict[str, Any]:
    """Get statistics about translation operations."""
    return TRANSLATION_STATS 