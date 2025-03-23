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
        
        # Convert to dict for validation and storage
        if isinstance(unified_tender, UnifiedTender):
            tender_dict = unified_tender.dict(exclude_none=True)
        else:
            tender_dict = unified_tender
            
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