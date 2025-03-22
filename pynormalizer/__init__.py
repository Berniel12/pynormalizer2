"""PyNormalizer - A Python framework for normalizing tender data from various sources."""

__version__ = "1.0.0"

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Import key functions
from .main import normalize_all_tenders
from .normalizers import normalize_tender, get_normalizer
from .normalizers.tedeu_normalizer import normalize_tedeu

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
    try:
        return normalize_tender(source, data)
    except Exception as e:
        logger.error(f"Error normalizing tender from {source}: {e}")
        return None

# Export available functions
__all__ = [
    'normalize',
    'normalize_all_tenders',
    'normalize_tender',
    'get_normalizer',
    'normalize_tedeu'
]
