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
    "sam_gov": normalize_samgov,
    "ted_eu": normalize_tedeu,
    "ungm": normalize_ungm,
    "wb": normalize_wb
}

# Table names in the database
SOURCE_TABLES = list(SOURCE_NORMALIZERS.keys())

def normalize_table(conn, table_name: str, batch_size: int = 100, limit: Optional[int] = None, progress_callback=None, skip_normalized: bool = True) -> int:
    """
    Normalize a single source table.
    
    Args:
        conn: Database connection
        table_name: Name of the table to normalize
        batch_size: Number of rows to process in a batch
        limit: Maximum number of rows to process (default: all)
        progress_callback: Callback function for progress updates
        skip_normalized: Whether to skip already normalized records (default: True)
        
    Returns:
        Number of rows processed
    """
    logger.info(f"Processing table: {table_name}")
    
    # Get the normalize function for this table
    normalize_fn = SOURCE_NORMALIZERS.get(table_name)
    if not normalize_fn:
        logger.error(f"No normalizer function found for table: {table_name}")
        return 0
    
    # Fetch rows from the table (either all or only unnormalized)
    try:
        if skip_normalized:
            logger.info(f"Fetching only unnormalized records from {table_name}")
            start_time = time.time()
            rows = fetch_unnormalized_rows(conn, table_name)
            fetch_time = time.time() - start_time
            
            # Count total records for comparison
            total_records = len(fetch_rows(conn, table_name))
            skipped_count = total_records - len(rows)
            
            logger.info(f"Found {len(rows)} unnormalized rows to process in {table_name} (skipped {skipped_count} already normalized records)")
            logger.info(f"Fetch operation completed in {fetch_time:.2f} seconds")
            
            # If we didn't skip any records but skip_normalized is True, log a warning
            if skipped_count == 0 and total_records > 0:
                logger.warning(f"No records were skipped in {table_name} despite skip_normalized=True. This could indicate an issue with the normalization tracking.")
        else:
            logger.info(f"Fetching all records from {table_name} (including already normalized)")
            rows = fetch_rows(conn, table_name)
            logger.info(f"Found {len(rows)} total rows in {table_name}")
    except Exception as e:
        logger.error(f"Error fetching rows from {table_name}: {e}")
        logger.warning(f"Unable to process table {table_name} due to fetch error")
        return 0
    
    total_rows = len(rows)
    
    # Apply limit if specified
    if limit is not None and limit < total_rows:
        rows = rows[:limit]
        logger.info(f"Limiting to first {limit} rows as requested")
        total_rows = limit
    
    # Process rows in batches
    processed = 0
    errors = 0
    error_details = {}  # Track specific error types and counts
    start_time = time.time()
    last_report_time = start_time
    process_times = []  # Keep track of processing times for statistics
    
    for i, row in enumerate(rows):
        # Check if we should continue processing
        if progress_callback and not progress_callback(processed, total_rows, table_name):
            logger.warning(f"Processing stopped by callback after {processed}/{total_rows} records")
            break
            
        try:
            # Record processing time
            start_process = time.time()
            
            # Extract source_id for logging
            source_id = None
            if 'id' in row:
                source_id = row['id']
            elif 'source_id' in row:
                source_id = row['source_id']
            
            # Call the normalizer function
            try:
                unified_tender = normalize_fn(row)
            except Exception as e:
                # Detailed error logging for normalization failures
                error_type = type(e).__name__
                if error_type not in error_details:
                    error_details[error_type] = {
                        'count': 0,
                        'examples': []
                    }
                
                error_details[error_type]['count'] += 1
                
                # Store example errors (up to 5 per type)
                if len(error_details[error_type]['examples']) < 5:
                    error_details[error_type]['examples'].append({
                        'source_id': source_id,
                        'message': str(e),
                        'row_index': i
                    })
                
                # Re-raise the exception
                raise
            
            # Calculate processing time
            process_time_ms = int((time.time() - start_process) * 1000)
            process_times.append(process_time_ms)
            
            # Add processing time to the unified tender
            unified_tender.processing_time_ms = process_time_ms
            
            # Set normalized timestamp
            unified_tender.normalized_at = datetime.now()
            
            # Apply additional data quality enhancements
            
            # 1. Ensure normalized_method is set
            if not unified_tender.normalized_method:
                # Add source_table to the row for the helper function
                row['source_table'] = table_name
                # Use the new helper function to determine normalized_method
                unified_tender.normalized_method = determine_normalized_method(row)
                logger.info(f"Set normalized_method for {table_name}: {unified_tender.normalized_method}")
            
            # 2. Normalize country values
            if unified_tender.country:
                # Apply enhanced country normalization
                original_country = unified_tender.country
                normalized_country = ensure_country(country_value=unified_tender.country)
                if normalized_country != original_country:
                    log_before_after("country", original_country, normalized_country)
                    unified_tender.country = normalized_country
            
            # 3. Set organization name if missing
            if not unified_tender.organization_name or len(unified_tender.organization_name or '') < 3:
                # Try to extract from project name if available
                if unified_tender.project_name and len(unified_tender.project_name) > 10:
                    from pynormalizer.utils.normalizer_helpers import extract_organization
                    org = extract_organization(unified_tender.project_name)
                    if org:
                        unified_tender.organization_name = org
                        logger.info(f"Extracted organization from project name: {org}")
            
            # Upsert to the unified table
            upsert_unified_tender(conn, unified_tender)
            
            processed += 1
            
            # Log progress for every batch_size records
            if processed % batch_size == 0 or processed == total_rows:
                elapsed = time.time() - start_time
                avg_time = elapsed / processed if processed > 0 else 0
                logger.info(f"Processed {processed}/{total_rows} rows from {table_name} " +
                            f"({processed/total_rows*100:.1f}%). " +
                            f"Elapsed: {elapsed:.1f}s, Avg: {avg_time:.2f}s/row")
                
                # Detailed statistics every batch_size records
                if len(process_times) > 0:
                    avg_process_time = sum(process_times) / len(process_times)
                    min_process_time = min(process_times) if process_times else 0
                    max_process_time = max(process_times) if process_times else 0
                    
                    # Reset process_times for next batch
                    process_times = []
                    
                    # Calculate records per second
                    recent_elapsed = time.time() - last_report_time
                    records_per_second = batch_size / recent_elapsed if recent_elapsed > 0 else 0
                    
                    logger.info(f"  Performance: {records_per_second:.2f} records/sec | " +
                                f"Avg: {avg_process_time:.0f}ms | Min: {min_process_time}ms | Max: {max_process_time}ms")
                    
                    # Reset for next batch reporting
                    last_report_time = time.time()
                
                # Error rate statistics
                if errors > 0:
                    error_rate = (errors / processed) * 100
                    logger.info(f"  Errors: {errors} ({error_rate:.1f}% error rate)")
                
        except Exception as e:
            errors += 1
            logger.error(f"Error processing row {i} from {table_name}: {e}")
            if errors <= 5:  # Limit the number of detailed error logs
                logger.error(f"Row data sample: {str(row)[:200]}...")
    
    # Summarize results
    success_rate = (processed / total_rows) * 100 if total_rows > 0 else 0
    logger.info(f"Completed processing {table_name}: {processed}/{total_rows} rows " +
                f"processed successfully ({success_rate:.1f}%).")
    
    if errors > 0:
        logger.warning(f"Encountered {errors} errors while processing {table_name} ({errors/total_rows*100:.1f}%).")
        
        # Log error details
        logger.warning(f"Error breakdown for {table_name}:")
        for error_type, details in error_details.items():
            logger.warning(f"  {error_type}: {details['count']} occurrences")
            if details['examples']:
                for i, example in enumerate(details['examples'], 1):
                    logger.warning(f"    Example {i}: source_id={example['source_id']}, message: {example['message']}")
    
    return processed


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
        logger.info(f"Processing table: {table_name}")
        start_time = time.time()
        
        try:
            # Get the appropriate normalizer function
            normalizer = SOURCE_NORMALIZERS.get(table_name)
            if not normalizer:
                logger.warning(f"No normalizer found for table {table_name}, skipping")
                continue
            
            # Fetch unnormalized rows
            if skip_normalized:
                logger.info(f"Fetching only unnormalized records from {table_name}")
            logger.info(f"Fetching unnormalized rows from {table_name}")
            
            rows = fetch_unnormalized_rows(conn, table_name, skip_normalized=skip_normalized, limit=limit_per_table)
            
            if not rows:
                logger.info(f"No rows to process in {table_name}")
                results[table_name] = 0
                continue
                
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
            
            # Store results for this table
            results[table_name] = successful
            
            # Log final stats for this table
            elapsed = time.time() - start_time
            if processed > 0:
                success_rate = (successful / processed) * 100
                logger.info(f"Completed processing {table_name}: {successful}/{processed} rows processed successfully ({success_rate:.1f}%).")
                logger.info(f"Total time: {elapsed:.2f}s, Average rate: {processed/elapsed:.2f} records/second")
            
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