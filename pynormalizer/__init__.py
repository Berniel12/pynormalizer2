"""PyNormalizer - A Python framework for normalizing tender data from various sources."""

__version__ = "1.0.0"

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Initialize available functions
normalize_all_tenders = None
normalize_tedeu = None

# Try importing key functions
try:
    from .main import normalize_all_tenders
except ImportError as e:
    logger.warning(f"Failed to import normalize_all_tenders: {e}")

try:
    from .normalizers.tedeu_normalizer import normalize_tedeu
except ImportError as e:
    logger.warning(f"Failed to import normalize_tedeu: {e}")

try:
    from .normalizers import normalize_tender, get_normalizer
except ImportError as e:
    logger.warning(f"Failed to import normalize_tender and get_normalizer: {e}")

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
        if source == 'tedeu' and normalize_tedeu:
            return normalize_tedeu(data)
        elif normalize_tender:
            return normalize_tender(source, data)
        else:
            logger.error(f"No normalizer available for source: {source}")
            return None
    except Exception as e:
        logger.error(f"Error normalizing tender from {source}: {e}")
        return None

# Export available functions
__all__ = ['normalize']

if normalize_all_tenders:
    __all__.append('normalize_all_tenders')
    
if normalize_tedeu:
    __all__.append('normalize_tedeu')
    
if 'normalize_tender' in globals():
    __all__.append('normalize_tender')
    
if 'get_normalizer' in globals():
    __all__.append('get_normalizer')
