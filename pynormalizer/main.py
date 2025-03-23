"""
Main module for normalizing tender data.
"""
import time
import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import traceback

import psycopg2

from pynormalizer.utils.db import get_connection, fetch_rows, fetch_unnormalized_rows, ensure_unique_constraint, upsert_unified_tender
from pynormalizer.utils.translation import setup_translation_models, get_translation_stats
from pynormalizer.utils.normalizer_helpers import (
    log_before_after,
    log_tender_normalization,
    determine_normalized_method,
    ensure_country
)

# Import only the get_normalizer and normalize_tender functions from normalizers
from pynormalizer.normalizers import get_normalizer, normalize_tender

# Import specific normalizer functions
from pynormalizer.normalizers.tedeu_normalizer import normalize_tedeu
from pynormalizer.normalizers.ungm_normalizer import normalize_ungm
from pynormalizer.normalizers.samgov_normalizer import normalize_samgov
from pynormalizer.normalizers.wb_normalizer import normalize_wb
from pynormalizer.normalizers.adb_normalizer import normalize_adb
from pynormalizer.normalizers.afd_normalizer import normalize_afd
from pynormalizer.normalizers.afdb_normalizer import normalize_afdb
from pynormalizer.normalizers.aiib_normalizer import normalize_aiib
from pynormalizer.normalizers.iadb_normalizer import normalize_iadb

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

def normalize_table(conn, table_name: str, batch_size: int = 100, limit: Optional[int] = None, progress_callback=None, skip_normalized: bool = True) -> int:
    """
    Normalize tenders from a specific table.
    
    Args:
        conn: Database connection
        table_name: Name of the table to normalize
        batch_size: Number of records to process at once
        limit: Optional limit on number of records to process
        progress_callback: Optional callback for progress updates
        skip_normalized: Whether to skip already normalized records
        
    Returns:
        Number of records normalized
    """
    # Get the appropriate normalizer
    normalizer = get_normalizer(table_name)
    if not normalizer:
        logger.error(f"No normalizer available for table: {table_name}")
        return 0
        
    # Fetch unnormalized rows
    if skip_normalized:
        logger.info(f"Fetching only unnormalized records from {table_name}")
    logger.info(f"Fetching unnormalized rows from {table_name}")
    
    rows = fetch_unnormalized_rows(conn, table_name, skip_normalized=skip_normalized, limit=limit)
    
    if not rows:
        logger.info(f"No rows to process in {table_name}")
        return 0
        
    total_rows = len(rows)
    processed = 0
    successful = 0
    
    # Process in batches
    for i in range(0, total_rows, batch_size):
        batch = rows[i:i + batch_size]
        
        for row in batch:
            try:
                # Normalize the tender
                normalized = normalizer(row)
                
                # Upsert to unified_tenders table
                upsert_unified_tender(conn, normalized)
                
                successful += 1
                
            except Exception as e:
                logger.error(f"Error normalizing row {row.get('id', 'unknown')} from {table_name}: {e}")
                logger.debug(traceback.format_exc())
                continue
                
            finally:
                processed += 1
                
        # Log progress after each batch
        if processed > 0:
            success_rate = (successful / processed) * 100
            elapsed = time.time() - start_time
            rate = processed / elapsed if elapsed > 0 else 0
            
            logger.info(f"Processed {processed}/{total_rows} records from {table_name} ({success_rate:.1f}%) in {elapsed:.2f}s")
            logger.info(f"Processing rate: {rate:.2f} records/second")
            
            if progress_callback:
                progress_callback(processed, total_rows, table_name)
    
    return successful

def normalize_all_tenders(db_config: Dict[str, Any], 
                        tables: Optional[List[str]] = None,
                        batch_size: int = 100,
                        limit_per_table: Optional[int] = None,
                        progress_callback=None,
                        skip_normalized: bool = True) -> Dict[str, int]:
    """
    Normalize tenders from all source tables.
    
    Args:
        db_config: Database configuration
        tables: List of tables to process (default: all source tables)
        batch_size: Number of rows to process in a batch
        limit_per_table: Maximum number of rows to process per table (None for all)
        progress_callback: Function to be called with progress updates (processed, total, table_name)
        skip_normalized: Whether to skip already normalized records (default: True)
        
    Returns:
        Dictionary of table names to number of rows processed
    """
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
    
    for table_name in (tables or []):
        logger.info(f"Processing table: {table_name}")
        start_time = time.time()
        
        try:
            successful = normalize_table(
                conn=conn,
                table_name=table_name,
                batch_size=batch_size,
                limit=limit_per_table,
                progress_callback=progress_callback,
                skip_normalized=skip_normalized
            )
            
            # Store results for this table
            results[table_name] = successful
            
            # Log final stats for this table
            elapsed = time.time() - start_time
            if successful > 0:
                logger.info(f"Completed processing {table_name}: {successful} rows processed successfully.")
                logger.info(f"Total time: {elapsed:.2f}s, Average rate: {successful/elapsed:.2f} records/second")
            
        except Exception as e:
            logger.error(f"Error processing table {table_name}: {e}")
            logger.debug(traceback.format_exc())
            results[table_name] = 0
            continue
    
    # Log overall completion
    total_elapsed = time.time() - total_start_time
    total_processed = sum(results.values())
    logger.info(f"Completed normalizing all tables in {total_elapsed:.2f}s")
    logger.info(f"Total records processed: {total_processed}")
    
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