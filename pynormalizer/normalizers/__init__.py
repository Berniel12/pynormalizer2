"""
Normalizer modules for different tender sources.
"""
import logging
from typing import Dict, Any, Optional, Callable
import time
import traceback

from pynormalizer.models.unified_model import UnifiedTender

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
    'tedeu': 'tedeu',
    'sam_gov': 'samgov',
    'samgov': 'samgov',
    'afd_tenders': 'afd',
    'afd': 'afd',
    'world_bank': 'wb',
    'wb': 'wb',
    'adb': 'adb',
    'afdb': 'afdb',
    'aiib': 'aiib',
    'iadb': 'iadb'
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

# Import normalizer functions for backward compatibility
try:
    from .tedeu_normalizer import normalize_tedeu
    from .ungm_normalizer import normalize_ungm
    from .samgov_normalizer import normalize_samgov
    from .wb_normalizer import normalize_wb
    from .adb_normalizer import normalize_adb
    from .afd_normalizer import normalize_afd
    from .afdb_normalizer import normalize_afdb
    from .aiib_normalizer import normalize_aiib
    from .iadb_normalizer import normalize_iadb
except ImportError as e:
    logger.warning(f"Failed to import some normalizer functions: {e}")

# Export available functions
__all__ = [
    'get_normalizer', 
    'normalize_tender',
    'normalize_tedeu',
    'normalize_ungm',
    'normalize_samgov',
    'normalize_wb',
    'normalize_adb',
    'normalize_afd',
    'normalize_afdb',
    'normalize_aiib',
    'normalize_iadb'
]

def normalize_and_save_tender(tender: Dict[str, Any], source: str, db_client: Optional[Any] = None, skip_save: bool = False) -> Optional[UnifiedTender]:
    """
    Normalize a tender from a specific source and save it to the database.
    
    Args:
        tender: Dictionary with tender data
        source: Source identifier (e.g., 'dgmarket', 'tedeu')
        db_client: Database client to save the tender (optional)
        skip_save: If True, don't save to the database
        
    Returns:
        Normalized UnifiedTender object, or None if normalization failed
    """
    logger = logging.getLogger(__name__)
    
    # Get the appropriate normalizer function
    normalizer = get_normalizer(source)
    
    if not normalizer:
        logger.error(f"No normalizer found for source: {source}")
        return None
    
    # Time the normalization process
    start_time = time.time()
    
    try:
        # Normalize the tender
        unified_tender = normalizer(tender)
        
        # Calculate processing time
        processing_time = int((time.time() - start_time) * 1000)  # Convert to milliseconds
        
        # Set additional metadata
        if hasattr(unified_tender, 'normalized_method'):
            unified_tender.normalized_method = f"pynormalizer_{source}"
        if hasattr(unified_tender, 'processing_time_ms'):
            unified_tender.processing_time_ms = processing_time
            
        # Make sure source_table is set
        if not hasattr(unified_tender, 'source_table') or not unified_tender.source_table:
            unified_tender.source_table = source
            
        # Handle compatibility with old field names
        # Convert publication_date to published_at if it exists
        if hasattr(unified_tender, 'publication_date') and not hasattr(unified_tender, 'published_at'):
            unified_tender.published_at = getattr(unified_tender, 'publication_date')
            
        # Convert deadline_date to deadline if it exists
        if hasattr(unified_tender, 'deadline_date') and not hasattr(unified_tender, 'deadline'):
            unified_tender.deadline = getattr(unified_tender, 'deadline_date')
            
        # Convert estimated_value to value if it exists
        if hasattr(unified_tender, 'estimated_value') and not hasattr(unified_tender, 'value'):
            unified_tender.value = getattr(unified_tender, 'estimated_value')
            
        # Convert document_links to documents if it exists
        if hasattr(unified_tender, 'document_links') and not hasattr(unified_tender, 'documents'):
            unified_tender.documents = getattr(unified_tender, 'document_links')
        
        # Log the fields we're about to save to identify any issues
        logger.info(f"Normalized tender fields: {', '.join(unified_tender.dict().keys())}")
        
        # Save to database if client provided and not skipping save
        if db_client and not skip_save:
            tender_dict = unified_tender.dict(exclude_none=True)
            success = db_client.save_normalized_tender(tender_dict)
            
            if not success:
                logger.error(f"Failed to save unified tender to database for {source} ID: {unified_tender.source_id}")
        
        return unified_tender
    
    except Exception as e:
        logger.error(f"Error normalizing tender from {source}: {str(e)}")
        logger.error(traceback.format_exc())
        return None
