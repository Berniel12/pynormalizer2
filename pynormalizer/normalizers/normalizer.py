from typing import Optional, Dict, Any, Callable, Union
import time
import uuid
import json
from datetime import datetime
from pynormalizer.utils.logger import logger
from pynormalizer.models.unified_model import UnifiedTender
from pynormalizer.normalizers import NORMALIZERS, TABLE_MAPPING

def get_normalizer(normalizer_id: str) -> Optional[Callable]:
    """Get the normalizer function for the given source."""
    # Check if the normalizer is a table name
    if normalizer_id in TABLE_MAPPING:
        normalizer_id = TABLE_MAPPING[normalizer_id]
    
    # Get the normalizer function
    if normalizer_id in NORMALIZERS:
        return NORMALIZERS[normalizer_id]
    
    # Try fuzzy matching
    for key in NORMALIZERS:
        if normalizer_id.lower() in key.lower() or key.lower() in normalizer_id.lower():
            return NORMALIZERS[key]
    
    # No normalizer found
    return None

def normalize_single_tender(
    tender_data: Dict[str, Any],
    table: str,
    normalizer: Callable,
    db_client = None
) -> Dict[str, Any]:
    """
    Normalize a single tender using the provided normalizer function and save to the database.
    
    Args:
        tender_data: The raw tender data to normalize
        table: The source table name
        normalizer: The normalizer function to use
        db_client: Database client to use
        
    Returns:
        Dict with the result of the normalization
    """
    start_time = time.time()
    tender_id = tender_data.get('id', str(uuid.uuid4()))
    source_id = str(tender_data.get('source_id', tender_id))
    
    result = {
        "id": tender_id,
        "source_id": source_id,
        "table": table,
        "success": False,
        "time_taken": 0
    }
    
    try:
        # Apply the normalizer to the tender data
        unified_tender = normalizer(tender_data)
        
        # Add metadata
        unified_tender.source_table = table
        unified_tender.source_id = source_id
        unified_tender.normalized_at = datetime.now()
        
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
        
        # Convert to dict for validation and storage
        if isinstance(unified_tender, UnifiedTender):
            tender_dict = unified_tender.dict(exclude_none=True)
        else:
            tender_dict = unified_tender
            
        # Add processing time
        if 'processing_time_ms' not in tender_dict:
            tender_dict['processing_time_ms'] = int((time.time() - start_time) * 1000)
            
        # Save to database
        if db_client:
            db_client.save_normalized_tender(tender_dict)
        
        # Update result
        result["success"] = True
        
    except Exception as e:
        logger.error(f"Error normalizing tender {tender_id} from {table}: {str(e)}")
        result["success"] = False
        result["error"] = str(e)
    
    # Update time taken
    result["time_taken"] = time.time() - start_time
    
    return result 