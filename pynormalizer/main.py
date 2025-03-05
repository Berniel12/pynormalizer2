import time
import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

import psycopg2

from pynormalizer.utils.db import get_connection, fetch_rows, ensure_unique_constraint, upsert_unified_tender
from pynormalizer.utils.translation import setup_translation_models, get_translation_stats

from pynormalizer.normalizers import (
    normalize_adb,
    normalize_afd,
    normalize_afdb,
    normalize_aiib,
    normalize_iadb,
    normalize_samgov,
    normalize_tedeu,
    normalize_ungm,
    normalize_wb
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pynormalizer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Detail logging for comparison
detail_logger = logging.getLogger("pynormalizer.comparison")
detail_logger.setLevel(logging.DEBUG)
# Create a file handler
detail_handler = logging.FileHandler("normalization_comparison.log")
detail_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
detail_logger.addHandler(detail_handler)

# Mapping of source table names to their normalizer functions
SOURCE_NORMALIZERS = {
    "adb": normalize_adb,
    "afd_tenders": normalize_afd,
    "afdb": normalize_afdb,
    "aiib": normalize_aiib,
    "iadb": normalize_iadb,
    "samgov": normalize_samgov,
    "tedeu": normalize_tedeu,
    "ungm": normalize_ungm,
    "wb": normalize_wb
}

# Table names in the database
SOURCE_TABLES = list(SOURCE_NORMALIZERS.keys())

def normalize_table(conn, table_name: str, batch_size: int = 100, limit: Optional[int] = None) -> int:
    """
    Normalize a single source table.
    
    Args:
        conn: Database connection
        table_name: Name of the source table
        batch_size: Number of rows to process in a batch
        limit: Maximum number of rows to process (None for all)
        
    Returns:
        Number of rows processed
    """
    logger.info(f"Processing table: {table_name}")
    
    # Get the normalize function for this table
    normalize_fn = SOURCE_NORMALIZERS.get(table_name)
    if not normalize_fn:
        logger.error(f"No normalizer function found for table: {table_name}")
        return 0
    
    # Fetch rows from the table
    rows = fetch_rows(conn, table_name)
    total_rows = len(rows)
    logger.info(f"Found {total_rows} rows in {table_name}")
    
    # Apply limit if specified
    if limit is not None and limit < total_rows:
        rows = rows[:limit]
        logger.info(f"Limiting to first {limit} rows as requested")
        total_rows = limit
    
    # Process rows in batches
    processed = 0
    errors = 0
    start_time = time.time()
    
    for i, row in enumerate(rows):
        try:
            # Record processing time
            start_process = time.time()
            
            # Log original data for comparison
            row_id = row.get('id', i)
            source = table_name
            
            # Log key fields from source data for comparison
            detail_logger.info(f"--- SOURCE DATA: {source} ID: {row_id} ---")
            
            # Log important fields from original data
            important_fields = ['title', 'description', 'amount', 'deadline', 'publication_date', 'status']
            for field in important_fields:
                if field in row:
                    detail_logger.info(f"BEFORE - {field}: {row.get(field)}")
            
            # Normalize the row
            unified_tender = normalize_fn(row)
            
            # Set processing metadata
            unified_tender.normalized_at = datetime.utcnow()
            unified_tender.normalized_by = "pynormalizer"
            unified_tender.processing_time_ms = int((time.time() - start_process) * 1000)
            
            # Log normalized data for comparison
            detail_logger.info(f"--- NORMALIZED DATA: {source} ID: {row_id} ---")
            detail_logger.info(f"AFTER - title: {unified_tender.title}")
            
            # Handle description that might be None
            if unified_tender.description:
                detail_logger.info(f"AFTER - description: {unified_tender.description[:100]}...")
            else:
                detail_logger.info(f"AFTER - description: None")
            
            # These attributes might not exist in UnifiedTender model, so check with hasattr
            if hasattr(unified_tender, 'category'):
                detail_logger.info(f"AFTER - category: {unified_tender.category}")
                
            if hasattr(unified_tender, 'source_country'):
                detail_logger.info(f"AFTER - source_country: {unified_tender.source_country}")
                
            if hasattr(unified_tender, 'value_usd'):
                detail_logger.info(f"AFTER - value_usd: {unified_tender.value_usd}")
            
            if unified_tender.status:
                detail_logger.info(f"AFTER - status: {unified_tender.status}")
            
            # Check for deadline and publication_date which exist in the model but might be None
            if hasattr(unified_tender, 'deadline') and unified_tender.deadline:
                detail_logger.info(f"AFTER - deadline: {unified_tender.deadline}")
            
            if hasattr(unified_tender, 'publication_date') and unified_tender.publication_date:
                detail_logger.info(f"AFTER - publication_date: {unified_tender.publication_date}")
            
            if unified_tender.tags:
                detail_logger.info(f"AFTER - tags: {unified_tender.tags}")
            
            # Log summary of changes
            detail_logger.info(f"Processing time: {unified_tender.processing_time_ms}ms")
            detail_logger.info("------------------------\n")
            
            # Upsert the normalized tender
            upsert_unified_tender(conn, unified_tender)
            
            processed += 1
            
            # Log progress periodically
            if (i + 1) % batch_size == 0 or i == total_rows - 1:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                logger.info(f"Processed {i + 1}/{total_rows} rows from {table_name} " +
                           f"({(i + 1) / total_rows * 100:.1f}%) at {rate:.1f} rows/sec")
        
        except Exception as e:
            errors += 1
            logger.exception(f"Error processing row {i} from {table_name}: {e}")
    
    logger.info(f"Completed processing {processed}/{total_rows} rows from {table_name}")
    logger.info(f"Errors: {errors}")
    
    return processed


def normalize_all_tenders(db_config: Dict[str, Any], 
                          tables: Optional[List[str]] = None,
                          batch_size: int = 100,
                          limit_per_table: Optional[int] = None) -> Dict[str, int]:
    """
    Normalize tenders from all source tables.
    
    Args:
        db_config: Database configuration
        tables: List of tables to process (default: all source tables)
        batch_size: Number of rows to process in a batch
        limit_per_table: Maximum number of rows to process per table (None for all)
        
    Returns:
        Dictionary of table names to number of rows processed
    """
    # Use all tables if none specified
    if tables is None:
        tables = SOURCE_TABLES
    
    # Initialize translation models
    try:
        logger.info("Initializing translation models...")
        setup_translation_models()
    except Exception as e:
        logger.warning(f"Error initializing translation models: {e}")
        logger.warning("Continuing with fallback translation methods")
    
    # Connect to the database
    conn = get_connection(db_config)
    
    # Ensure unique constraint exists
    ensure_unique_constraint(conn)
    
    # Process each table
    results = {}
    total_start_time = time.time()
    
    for table_name in tables:
        if table_name not in SOURCE_NORMALIZERS:
            logger.warning(f"No normalizer found for table: {table_name}")
            continue
        
        try:
            processed = normalize_table(conn, table_name, batch_size, limit_per_table)
            results[table_name] = processed
        except Exception as e:
            logger.exception(f"Error processing table {table_name}: {e}")
            results[table_name] = 0
    
    # Log summary
    total_time = time.time() - total_start_time
    total_processed = sum(results.values())
    
    logger.info(f"Normalization complete. Processed {total_processed} tenders " +
                f"from {len(results)} tables in {total_time:.1f} seconds.")
    
    # Log translation statistics
    try:
        translation_stats = get_translation_stats()
        logger.info(f"Translation statistics: {json.dumps(translation_stats, indent=2)}")
    except Exception as e:
        logger.warning(f"Could not retrieve translation statistics: {e}")
    
    # Close the connection if it's a PostgreSQL connection
    # Supabase client doesn't need/have a close method
    if hasattr(conn, 'close'):
        conn.close()
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Normalize tender data from multiple sources")
    parser.add_argument("--config", type=str, default="config.json", help="Path to database config JSON file")
    parser.add_argument("--tables", type=str, nargs="*", help="Specific tables to process")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")
    parser.add_argument("--limit", type=int, help="Maximum number of records to process per table")
    parser.add_argument("--test", action="store_true", help="Run in test mode (2 records per table)")
    
    args = parser.parse_args()
    
    # Check for environment variables first
    if os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_KEY"):
        logger.info("Using Supabase connection from environment variables")
        db_config = {}  # Empty config will trigger env var usage
    else:
        # Load database config from file
        try:
            with open(args.config, 'r') as f:
                db_config = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
            logger.info("Please create a config.json file or set SUPABASE_URL and SUPABASE_KEY environment variables")
            exit(1)
    
    # Set limit for test mode
    if args.test:
        logger.info("Running in TEST mode with 2 records per table")
        limit = 2
    else:
        limit = args.limit
    
    # Run normalization
    normalize_all_tenders(db_config, args.tables, args.batch_size, limit) 