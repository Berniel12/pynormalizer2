"""
Normalizer modules for different tender sources.
"""
import logging
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)

# Dictionary to store normalizer functions
NORMALIZERS: Dict[str, Optional[Callable]] = {
    'tedeu': None,
    'ungm': None,
    'samgov': None,
    'wb': None,
    'adb': None,
    'afd': None,
    'afdb': None,
    'aiib': None,
    'iadb': None
}

# Import normalizers with error handling
try:
    from .tedeu_normalizer import normalize_tedeu
    NORMALIZERS['tedeu'] = normalize_tedeu
except ImportError as e:
    logger.warning(f"Failed to import tedeu_normalizer: {e}")

try:
    from .ungm_normalizer import normalize_ungm
    NORMALIZERS['ungm'] = normalize_ungm
except ImportError as e:
    logger.warning(f"Failed to import ungm_normalizer: {e}")

try:
    from .samgov_normalizer import normalize_samgov
    NORMALIZERS['samgov'] = normalize_samgov
except ImportError as e:
    logger.warning(f"Failed to import samgov_normalizer: {e}")

try:
    from .wb_normalizer import normalize_wb
    NORMALIZERS['wb'] = normalize_wb
except ImportError as e:
    logger.warning(f"Failed to import wb_normalizer: {e}")

try:
    from .adb_normalizer import normalize_adb
    NORMALIZERS['adb'] = normalize_adb
except ImportError as e:
    logger.warning(f"Failed to import adb_normalizer: {e}")

try:
    from .afd_normalizer import normalize_afd
    NORMALIZERS['afd'] = normalize_afd
except ImportError as e:
    logger.warning(f"Failed to import afd_normalizer: {e}")

try:
    from .afdb_normalizer import normalize_afdb
    NORMALIZERS['afdb'] = normalize_afdb
except ImportError as e:
    logger.warning(f"Failed to import afdb_normalizer: {e}")

try:
    from .aiib_normalizer import normalize_aiib
    NORMALIZERS['aiib'] = normalize_aiib
except ImportError as e:
    logger.warning(f"Failed to import aiib_normalizer: {e}")

try:
    from .iadb_normalizer import normalize_iadb
    NORMALIZERS['iadb'] = normalize_iadb
except ImportError as e:
    logger.warning(f"Failed to import iadb_normalizer: {e}")

def get_normalizer(source: str) -> Optional[Callable]:
    """
    Get the normalizer function for a given source.
    Returns None if the normalizer is not available.
    """
    return NORMALIZERS.get(source.lower())

def normalize_tender(source: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Normalize a tender using the appropriate normalizer.
    Returns None if the normalizer is not available.
    """
    normalizer = get_normalizer(source)
    if normalizer:
        try:
            return normalizer(data)
        except Exception as e:
            logger.error(f"Error normalizing {source} tender: {e}")
            return None
    else:
        logger.warning(f"No normalizer available for source: {source}")
        return None

# Export normalizer functions that were successfully imported
__all__ = ['normalize_tender', 'get_normalizer'] + [
    f'normalize_{source}' for source, func in NORMALIZERS.items() 
    if func is not None
]
