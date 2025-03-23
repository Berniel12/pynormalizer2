"""PyNormalizer - A Python framework for normalizing tender data from various sources."""

__version__ = "1.0.0"

import logging
from typing import Dict, Any, Optional, Callable
import sys
import importlib

logger = logging.getLogger(__name__)

# Use lazy imports to avoid circular dependencies
_normalize_all_tenders = None
_normalize_tedeu = None
_normalize_tender = None
_get_normalizer = None
_normalize_afdb = None

def _lazy_import(module_name, attr_name):
    """Lazily import a module attribute to avoid circular dependencies."""
    def _import():
        module = importlib.import_module(module_name)
        return getattr(module, attr_name)
    return _import

def normalize(source: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Normalize a tender from any supported source.
    This is the main entry point for the package.
    
    Args:
        source: The source of the tender (e.g. 'tedeu', 'ungm', etc.)
        data: The tender data to normalize
        
    Returns:
        Normalized tender data or None if normalization fails
    """
    global _normalize_tender
    
    if _normalize_tender is None:
        try:
            from .normalizers import normalize_tender
            _normalize_tender = normalize_tender
        except ImportError as e:
            logger.error(f"Error importing normalize_tender: {e}")
            return None
    
    try:
        return _normalize_tender(source, data)
    except Exception as e:
        logger.error(f"Error normalizing tender from {source}: {e}")
        return None

def normalize_all_tenders(*args, **kwargs):
    """Lazy-loaded function to normalize all tenders."""
    global _normalize_all_tenders
    
    if _normalize_all_tenders is None:
        try:
            from .main import normalize_all_tenders as func
            _normalize_all_tenders = func
        except ImportError as e:
            logger.error(f"Error importing normalize_all_tenders: {e}")
            raise ImportError(f"Failed to import normalize_all_tenders: {e}")
    
    return _normalize_all_tenders(*args, **kwargs)

def normalize_tedeu(*args, **kwargs):
    """Lazy-loaded function to normalize tedeu tenders."""
    global _normalize_tedeu
    
    if _normalize_tedeu is None:
        try:
            from .normalizers.tedeu_normalizer import normalize_tedeu as func
            _normalize_tedeu = func
        except ImportError as e:
            logger.error(f"Error importing normalize_tedeu: {e}")
            raise ImportError(f"Failed to import normalize_tedeu: {e}")
    
    return _normalize_tedeu(*args, **kwargs)

def normalize_afdb(*args, **kwargs):
    """Lazy-loaded function to normalize afdb tenders."""
    global _normalize_afdb
    
    if _normalize_afdb is None:
        try:
            from .normalizers.afdb_normalizer import normalize_afdb as func
            _normalize_afdb = func
        except ImportError as e:
            logger.error(f"Error importing normalize_afdb: {e}")
            raise ImportError(f"Failed to import normalize_afdb: {e}")
    
    return _normalize_afdb(*args, **kwargs)

def get_normalizer(*args, **kwargs):
    """Lazy-loaded function to get a normalizer."""
    global _get_normalizer
    
    if _get_normalizer is None:
        try:
            from .normalizers import get_normalizer as func
            _get_normalizer = func
        except ImportError as e:
            logger.error(f"Error importing get_normalizer: {e}")
            raise ImportError(f"Failed to import get_normalizer: {e}")
    
    return _get_normalizer(*args, **kwargs)

# Define all exported names
__all__ = [
    'normalize',
    'normalize_all_tenders',
    'normalize_tedeu',
    'normalize_afdb',
    'normalize',
    'get_normalizer'
]
