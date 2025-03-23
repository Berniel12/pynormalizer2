from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from pynormalizer.db.db_client import DBClient
from pynormalizer.normalizers.normalizer import get_normalizer
from pynormalizer.utils.logger import logger

def normalize_all_tenders(
    tables: Optional[List[str]] = None,
    limit: int = 5000,
    skip_normalized: bool = True,
    process_all: bool = False,
    db_client = None
) -> Dict[str, Any]:
    """
    Normalize tenders from all supported tables.
    
    Args:
        tables: List of table names to normalize. If None, all tables with a normalizer will be processed.
        limit: Maximum number of tenders to process per table.
        skip_normalized: Whether to skip already normalized tenders.
        process_all: If True, process all tenders regardless of other filters.
        db_client: Database client to use. If None, a new client will be created.
        
    Returns:
        Dict with statistics about the normalization process.
    """
    start_time = time.time()
    
    # Set up database client
    if not db_client:
        db_client = DBClient()
    
    # Set up global stats
    stats = {
        "total_processed": 0,
        "total_normalized": 0,
        "total_failed": 0,
        "tables_processed": [],
        "tables_stats": {},
        "errors": [],
        "time_taken": 0
    }

    # If no tables specified, use all tables with a normalizer
    if tables is None or len(tables) == 0:
        tables = [table for table in TABLE_MAPPING.keys()]
        logger.info(f"No tables specified, using all tables with a normalizer: {tables}")
    
    # Process each table
    for table in tables:
        if table not in TABLE_MAPPING:
            logger.warning(f"No normalizer found for table {table}, skipping.")
            stats["errors"].append(f"No normalizer found for table {table}")
            continue
        
        try:
            # Get the normalizer function for this table
            normalizer_id = TABLE_MAPPING[table]
            normalizer = get_normalizer(normalizer_id)
            
            if not normalizer:
                logger.warning(f"Normalizer {normalizer_id} for table {table} is not available, skipping.")
                stats["errors"].append(f"Normalizer {normalizer_id} for table {table} is not available")
                continue

            logger.info(f"Processing table {table} with normalizer {normalizer_id}")
            
            # Get tenders to normalize
            if process_all:
                tenders = db_client.fetch_all_rows(table, limit=limit)
                logger.info(f"Fetched {len(tenders)} tenders from {table} for processing (process_all=True)")
            else:
                tenders = db_client.fetch_unnormalized_rows(table, limit=limit, skip_normalized=skip_normalized)
                logger.info(f"Fetched {len(tenders)} unnormalized tenders from {table}")
            
            # Set up table stats
            table_stats = {
                "processed": len(tenders),
                "normalized": 0,
                "failed": 0,
                "start_time": time.time(),
                "end_time": 0,
                "time_taken": 0
            }
            
            # Normalize each tender
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = []
                for tender_data in tenders:
                    futures.append(executor.submit(
                        normalize_single_tender,
                        tender_data=tender_data,
                        table=table,
                        normalizer=normalizer,
                        db_client=db_client
                    ))
                
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        if result["success"]:
                            table_stats["normalized"] += 1
                        else:
                            table_stats["failed"] += 1
                            if "error" in result:
                                stats["errors"].append(f"{table}: {result['error']}")
                    except Exception as e:
                        logger.error(f"Error in future for table {table}: {str(e)}")
                        table_stats["failed"] += 1
                        stats["errors"].append(f"{table}: Executor error: {str(e)}")
            
            # Update table stats
            table_stats["end_time"] = time.time()
            table_stats["time_taken"] = table_stats["end_time"] - table_stats["start_time"]
            stats["tables_stats"][table] = table_stats
            
            # Update global stats
            stats["total_processed"] += table_stats["processed"]
            stats["total_normalized"] += table_stats["normalized"]
            stats["total_failed"] += table_stats["failed"]
            stats["tables_processed"].append(table)
            
            logger.info(f"Finished processing table {table}: {table_stats['normalized']} normalized, {table_stats['failed']} failed")
            
        except Exception as e:
            logger.error(f"Error processing table {table}: {str(e)}")
            stats["errors"].append(f"Error processing table {table}: {str(e)}")
    
    # Update final stats
    stats["time_taken"] = time.time() - start_time
    logger.info(f"Finished normalizing {stats['total_normalized']} tenders in {stats['time_taken']:.2f} seconds")
    
    return stats 