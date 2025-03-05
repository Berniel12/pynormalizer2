"""
Translation utilities for normalizing tender data.
Provides offline translation capabilities using argostranslate.
"""
import os
import logging
from typing import Dict, Optional, List, Set, Any
from pathlib import Path
import tempfile
import json

# Initialize logger
logger = logging.getLogger(__name__)

# Flag for tracking if models are downloaded
MODELS_DOWNLOADED = False

# Translation statistics for logging
TRANSLATION_STATS = {
    "total_requests": 0,
    "argos_success": 0,
    "fallback_used": 0,
    "already_english": 0,
    "failed": 0,
    "languages": {}
}

# Try to import translation libraries
try:
    import argostranslate.package
    import argostranslate.translate
    ARGOS_AVAILABLE = True
except ImportError:
    ARGOS_AVAILABLE = False
    logger.warning("argostranslate not available. Install with pip install argostranslate")

try:
    import langid
    LANGID_AVAILABLE = True
except ImportError:
    LANGID_AVAILABLE = False
    logger.warning("langid not available. Install with pip install langid")

try:
    import stanza
    STANZA_AVAILABLE = False  # Set to True if you want to use Stanza
except ImportError:
    STANZA_AVAILABLE = False

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
    """Download and install translation models for argostranslate."""
    global MODELS_DOWNLOADED
    
    if not ARGOS_AVAILABLE or MODELS_DOWNLOADED:
        return
    
    try:
        logger.info("Setting up translation models...")
        # Download and install available packages
        argostranslate.package.update_package_index()
        available_packages = argostranslate.package.get_available_packages()
        
        # Get packages that translate from any language to English
        packages_to_install = [
            pkg for pkg in available_packages 
            if pkg.from_code in SUPPORTED_LANGS and pkg.to_code == 'en'
        ]
        
        logger.info(f"Installing {len(packages_to_install)} translation packages...")
        
        for package in packages_to_install:
            logger.info(f"Installing {package.from_code} -> {package.to_code} translation")
            try:
                download_path = argostranslate.package.download_package(package)
                argostranslate.package.install_from_path(download_path)
                logger.info(f"Successfully installed {package.from_code} -> {package.to_code} translation")
            except Exception as e:
                logger.error(f"Failed to install {package.from_code} -> {package.to_code} translation: {e}")
        
        # Verify installed packages
        installed_languages = argostranslate.translate.get_installed_languages()
        logger.info(f"Installed languages: {[lang.code for lang in installed_languages]}")
        
        MODELS_DOWNLOADED = True
        logger.info("Translation models setup complete")
    except Exception as e:
        logger.error(f"Error setting up translation models: {e}")

def detect_language(text: Optional[str]) -> Optional[str]:
    """
    Detect the language of a text.
    
    Args:
        text: Text to detect language for
        
    Returns:
        ISO language code or None if detection fails
    """
    if not text or len(text) < 10:
        return None
    
    # Use langid for language detection if available
    if LANGID_AVAILABLE:
        try:
            lang, confidence = langid.classify(text)
            if confidence > 0.5:  # Only accept if confidence is reasonable
                logger.debug(f"Detected language: {lang} with confidence {confidence}")
                return lang
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
    
    # Fallback to simple word counting method
    language_markers = {
        "fr": ["le", "la", "les", "de", "et", "en", "pour", "dans", "un", "une"],
        "es": ["el", "la", "los", "las", "de", "y", "en", "para", "un", "una"],
        "de": ["der", "die", "das", "und", "in", "für", "ein", "eine", "mit", "von"],
        "pt": ["o", "a", "os", "as", "de", "e", "em", "para", "um", "uma"],
        "it": ["il", "la", "i", "le", "di", "e", "in", "per", "un", "una"],
    }
    
    text_lower = text.lower()
    word_counts = {}
    
    for lang, markers in language_markers.items():
        count = 0
        for marker in markers:
            # Count occurrences of marker words surrounded by spaces
            count += text_lower.count(f" {marker} ")
        word_counts[lang] = count
    
    # If no markers found, assume English
    if max(word_counts.values(), default=0) == 0:
        return "en"
    
    # Return the language with the most marker words
    return max(word_counts.items(), key=lambda x: x[1])[0]

def translate_to_english(text: Optional[str], src_lang: Optional[str] = "auto", 
                         use_fallback: bool = True) -> tuple[Optional[str], Optional[str]]:
    """
    Translate text to English using offline translation.
    
    Args:
        text: Text to translate
        src_lang: Source language code or "auto" for auto-detection
        use_fallback: Whether to use fallback methods if primary translation fails
        
    Returns:
        Tuple of (translated_text, method_used)
    """
    global TRANSLATION_STATS
    
    if not text:
        return text, None
    
    TRANSLATION_STATS["total_requests"] += 1
    
    # Detect language if src_lang is "auto"
    if src_lang == "auto":
        detected_lang = detect_language(text)
        if detected_lang:
            src_lang = detected_lang
            
            # Update language statistics
            if src_lang not in TRANSLATION_STATS["languages"]:
                TRANSLATION_STATS["languages"][src_lang] = 0
            TRANSLATION_STATS["languages"][src_lang] += 1
    
    # If detected as English or couldn't detect, return original
    if src_lang == "en" or not src_lang:
        TRANSLATION_STATS["already_english"] += 1
        return text, "already_english"
    
    # Log the original text and source language for debugging
    logger.debug(f"Translating from {src_lang} to English: {text[:50]}...")
    
    # Check if the language is supported by our translation system
    if src_lang not in SUPPORTED_LANGS:
        logger.warning(f"Language '{src_lang}' not supported for translation")
        if use_fallback:
            TRANSLATION_STATS["fallback_used"] += 1
            return fallback_translate(text), "fallback_dictionary"
        TRANSLATION_STATS["failed"] += 1
        return text, "unsupported_language"
    
    # Try to translate with argostranslate
    if ARGOS_AVAILABLE:
        try:
            # Initialize models if not done already
            if not MODELS_DOWNLOADED:
                setup_translation_models()
            
            # Get translation
            from_lang = src_lang
            to_lang = "en"
            
            # Find the installed translation package
            installed_languages = argostranslate.translate.get_installed_languages()
            from_lang_obj = list(filter(lambda x: x.code == from_lang, installed_languages))
            to_lang_obj = list(filter(lambda x: x.code == to_lang, installed_languages))
            
            if from_lang_obj and to_lang_obj:
                translation = from_lang_obj[0].get_translation(to_lang_obj[0])
                result = translation.translate(text)
                
                if result and result.strip():
                    # Log the before and after for comparison
                    logger.debug(f"Original ({src_lang}): {text[:50]}...")
                    logger.debug(f"Translated (en): {result[:50]}...")
                    
                    TRANSLATION_STATS["argos_success"] += 1
                    return result, "argostranslate"
        except Exception as e:
            logger.warning(f"ArgosTranslate error: {e}")
    
    # If we get here, use fallback dictionary if enabled
    if use_fallback:
        logger.debug(f"Using fallback dictionary for {src_lang}")
        TRANSLATION_STATS["fallback_used"] += 1
        return fallback_translate(text), "fallback_dictionary"
    
    # Return original if all else fails
    TRANSLATION_STATS["failed"] += 1
    return text, "no_translation"

def fallback_translate(text: str) -> str:
    """
    Use a simple dictionary-based translation as a fallback method.
    
    Args:
        text: Text to translate
        
    Returns:
        Translated text using simple word replacement
    """
    result = text
    for foreign_word, english_word in FALLBACK_DICTIONARY.items():
        # Case-insensitive replacement
        result = result.replace(foreign_word, english_word)
        # Also try lowercase version
        result = result.replace(foreign_word.lower(), english_word.lower())
        # Try capitalized version
        result = result.replace(foreign_word.capitalize(), english_word.capitalize())
    
    return result

def get_supported_languages() -> Dict[str, str]:
    """
    Get a dictionary of supported language codes and their names.
    
    Returns:
        Dictionary of language codes to language names
    """
    return SUPPORTED_LANGS

def get_translation_stats() -> Dict[str, Any]:
    """
    Get statistics about translation operations.
    
    Returns:
        Dictionary of translation statistics
    """
    return TRANSLATION_STATS

# Initialize translation models when module is imported
if ARGOS_AVAILABLE:
    try:
        # Don't download immediately - wait until first translation request
        pass
    except Exception as e:
        logger.warning(f"Failed to initialize translation models: {e}") 