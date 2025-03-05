"""
Translation utilities for normalizing tender data.
Provides lightweight translation capabilities using deep-translator.
"""
import os
import logging
from typing import Dict, Optional, List, Set, Any
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

# Fallback dictionary for very basic word replacements when translation fails
FALLBACK_DICTIONARY: Dict[str, str] = {
    # French
    "Avis": "Notice",
    "Contrat": "Contract",
    "Projet": "Project",
    "Titre": "Title",
    "Fournisseur": "Supplier",
    "Appel d'offres": "Call for Tenders",
    "Marché": "Market",
    "Date limite": "Deadline",
    "Pays": "Country",
    "Description": "Description",
    "Services": "Services",
    "Fournitures": "Supplies",
    "Travaux": "Works",
    "Date de publication": "Publication date",
    "Montant": "Amount",
    
    # Spanish
    "Aviso": "Notice",
    "Contrato": "Contract",
    "Proyecto": "Project",
    "Título": "Title",
    "Proveedor": "Supplier",
    "Licitación": "Tender",
    "Fecha límite": "Deadline",
    "País": "Country",
    "Descripción": "Description",
    "Servicios": "Services",
    "Suministros": "Supplies",
    "Obras": "Works",
    "Fecha de publicación": "Publication date",
    "Importe": "Amount",
    
    # German
    "Bekanntmachung": "Notice",
    "Vertrag": "Contract",
    "Projekt": "Project",
    "Titel": "Title",
    "Lieferant": "Supplier",
    "Ausschreibung": "Tender",
    "Frist": "Deadline",
    "Land": "Country",
    "Beschreibung": "Description",
    "Dienstleistungen": "Services",
    "Lieferungen": "Supplies",
    "Arbeiten": "Works",
    "Veröffentlichungsdatum": "Publication date",
    "Betrag": "Amount",
    
    # Portuguese
    "Aviso": "Notice",
    "Contrato": "Contract",
    "Projeto": "Project",
    "Título": "Title",
    "Fornecedor": "Supplier",
    "Concurso": "Tender",
    "Prazo": "Deadline",
    "País": "Country",
    "Descrição": "Description",
    "Serviços": "Services",
    "Fornecimentos": "Supplies",
    "Obras": "Works",
    "Data de publicação": "Publication date",
    "Montante": "Amount",
    
    # Italian
    "Avviso": "Notice",
    "Contratto": "Contract",
    "Progetto": "Project",
    "Titolo": "Title",
    "Fornitore": "Supplier",
    "Gara d'appalto": "Tender",
    "Scadenza": "Deadline",
    "Paese": "Country",
    "Descrizione": "Description",
    "Servizi": "Services",
    "Forniture": "Supplies",
    "Lavori": "Works",
    "Data di pubblicazione": "Publication date",
    "Importo": "Amount",
}

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
    Detect the language of a text using deep-translator.
    
    Args:
        text: Text to detect language for
        
    Returns:
        ISO language code or None if detection fails
    """
    if not text or len(text) < 10:
        return None
    
    # First, check if the text is predominantly English by looking for common English words
    english_markers = ["the", "and", "for", "with", "this", "that", "from", "have", "will"]
    total_english_markers = 0
    english_threshold = 0.6  # 60% threshold for declaring text as English
    
    # Convert to lowercase and count English markers
    text_lower = text.lower()
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
        # Use deep-translator's detection 
        detected = detect_language(text[:500])  # Limit detection to first 500 chars for speed
        if detected in SUPPORTED_LANGS:
            logger.debug(f"Detected language: {detected}")
            return detected
    except Exception as e:
        logger.warning(f"Language detection failed: {e}")
    
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
    
    text_lower = text.lower()
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
    Translate text to English using deep-translator.
    
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
    
    # Detect language if set to auto
    detected_lang = src_lang
    if src_lang == "auto":
        detected_lang = detect_language(text)
        
    # Skip translation if already English
    if detected_lang == "en":
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
                # Log language detection
                if detected_lang and detected_lang in TRANSLATION_STATS["languages"]:
                    TRANSLATION_STATS["languages"][detected_lang] = TRANSLATION_STATS["languages"].get(detected_lang, 0) + 1
                return text, "already_english"
        else:
            # Short text - just assume it's English as detected
            TRANSLATION_STATS["already_english"] += 1
            return text, "already_english"
    
    # Try primary translation method
    if TRANSLATOR_AVAILABLE:
        try:
            start_time = time.time()
            translated = GoogleTranslator(source=src_lang, target='en').translate(text)
            logger.debug(f"Translation completed in {time.time() - start_time:.2f} seconds")
            
            if translated and translated.strip():
                TRANSLATION_STATS["success"] += 1
                
                # Log detected language
                if src_lang == "auto":
                    detected = detect_language(text)
                    if detected:
                        TRANSLATION_STATS["languages"][detected] = TRANSLATION_STATS["languages"].get(detected, 0) + 1
                else:
                    TRANSLATION_STATS["languages"][src_lang] = TRANSLATION_STATS["languages"].get(src_lang, 0) + 1
                
                return translated, "deep_translator"
        except Exception as e:
            logger.warning(f"Primary translation method failed: {e}")
    
    # Fallback to dictionary-based translation if enabled
    if use_fallback:
        try:
            TRANSLATION_STATS["fallback_used"] += 1
            # Simple word replacement using the fallback dictionary
            translated_text = text
            for src_word, tgt_word in FALLBACK_DICTIONARY.items():
                translated_text = translated_text.replace(src_word, tgt_word)
            
            # Only return the fallback translation if it's actually different from the original
            if translated_text != text:
                return translated_text, "fallback_dictionary"
            
            # If fallback didn't change anything, log as failure
            logger.warning(f"Fallback translation didn't modify text: {text[:50]}...")
        except Exception as e:
            logger.error(f"Fallback translation failed: {e}")
    
    # Track failed translations
    TRANSLATION_STATS["failed"] += 1
    return text, "failed"  # Return original text if all methods fail

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