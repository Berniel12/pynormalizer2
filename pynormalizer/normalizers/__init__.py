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

# Table name mapping
TABLE_MAPPING = {
    'ted_eu': 'tedeu',
    'sam_gov': 'samgov',
    'afd_tenders': 'afd',
    'world_bank': 'wb'
}

def get_normalizer(source: str) -> Optional[Callable]:
    """
    Get the normalizer function for a given source.
    
    Args:
        source: Source identifier (e.g. 'tedeu', 'ungm', etc.)
        
    Returns:
        Normalizer function if available, None otherwise
    """
    # Handle table name variations
    source = TABLE_MAPPING.get(source, source)
    
    # Try to import if not already loaded
    if source in NORMALIZERS and NORMALIZERS[source] is None:
        try:
            if source == 'tedeu':
                from .tedeu_normalizer import normalize_tedeu
                NORMALIZERS['tedeu'] = normalize_tedeu
            elif source == 'ungm':
                from .ungm_normalizer import normalize_ungm
                NORMALIZERS['ungm'] = normalize_ungm
            elif source == 'samgov':
                from .samgov_normalizer import normalize_samgov
                NORMALIZERS['samgov'] = normalize_samgov
            elif source == 'wb':
                from .wb_normalizer import normalize_wb
                NORMALIZERS['wb'] = normalize_wb
            elif source == 'adb':
                from .adb_normalizer import normalize_adb
                NORMALIZERS['adb'] = normalize_adb
            elif source == 'afd':
                from .afd_normalizer import normalize_afd
                NORMALIZERS['afd'] = normalize_afd
            elif source == 'afdb':
                from .afdb_normalizer import normalize_afdb
                NORMALIZERS['afdb'] = normalize_afdb
            elif source == 'aiib':
                from .aiib_normalizer import normalize_aiib
                NORMALIZERS['aiib'] = normalize_aiib
            elif source == 'iadb':
                from .iadb_normalizer import normalize_iadb
                NORMALIZERS['iadb'] = normalize_iadb
        except ImportError as e:
            logger.warning(f"Failed to import normalizer for {source}: {e}")
            return None
    
    return NORMALIZERS.get(source)

def normalize_tender(source: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Normalize a tender from any supported source.
    
    Args:
        source: Source identifier
        data: Tender data to normalize
        
    Returns:
        Normalized tender data or None if normalization fails
    """
    normalizer = get_normalizer(source)
    if normalizer:
        try:
            return normalizer(data)
        except Exception as e:
            logger.error(f"Error normalizing tender from {source}: {e}")
            return None
    else:
        logger.error(f"No normalizer available for source: {source}")
        return None

# Export available functions
__all__ = ['get_normalizer', 'normalize_tender']
