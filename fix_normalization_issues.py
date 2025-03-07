#!/usr/bin/env python3
"""
Script to fix normalization issues in existing records in the unified_tenders table.

This script applies enhanced normalization functions to existing records to fix:
1. Country names - standardize to English names
2. Missing normalized_method values
3. Missing organization names

Usage:
    ./fix_normalization_issues.py [--skip-country] [--skip-method] [--skip-organization] [--batch-size BATCH_SIZE]
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

# Set Supabase environment variables
os.environ["SUPABASE_URL"] = "https://xmakjwxlwlsrblytfibm.supabase.co"
os.environ["SUPABASE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhtYWtqd3hsd2xzcmJseXRmaWJtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDk3MDc5MDcsImV4cCI6MjAyNTI4MzkwN30.r8_6_WI2SJlzfCjXxZdGdzLQtJYx0Z8EXbZBL4-6ZVA"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_normalization.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("fix_normalization")

# Import helper functions
from pynormalizer.utils.db import get_connection
from pynormalizer.utils.normalizer_helpers import ensure_country, determine_normalized_method, extract_organization, log_before_after

def fix_country_values(conn, batch_size: int = 100) -> Dict[str, int]:
    """
    Fix country values in the unified_tenders table.
    
    Args:
        conn: Database connection
        batch_size: Number of records to process in each batch
        
    Returns:
        Dict with statistics about the operation
    """
    logger.info("Starting country name normalization...")
    
    # Get count of records with country values
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM unified_tenders WHERE country IS NOT NULL AND country != ''")
    total_records = cursor.fetchone()[0]
    logger.info(f"Found {total_records} records with country values")
    
    # Process in batches
    processed = 0
    updated = 0
    errors = 0
    
    # Get records in batches
    offset = 0
    while offset < total_records:
        cursor.execute(
            """
            SELECT id, country, source_table 
            FROM unified_tenders 
            WHERE country IS NOT NULL AND country != '' 
            ORDER BY id 
            LIMIT %s OFFSET %s
            """,
            (batch_size, offset)
        )
        records = cursor.fetchall()
        
        if not records:
            break
        
        for record in records:
            try:
                record_id = record[0]
                original_country = record[1]
                source_table = record[2]
                
                # Apply country normalization
                normalized_country = ensure_country(country_value=original_country)
                
                # Update if changed
                if normalized_country != original_country:
                    update_cursor = conn.cursor()
                    update_cursor.execute(
                        "UPDATE unified_tenders SET country = %s WHERE id = %s",
                        (normalized_country, record_id)
                    )
                    conn.commit()
                    log_before_after("country", original_country, normalized_country)
                    updated += 1
                
                processed += 1
                
                # Log progress
                if processed % 100 == 0:
                    logger.info(f"Processed {processed}/{total_records} country values, updated {updated}")
                
            except Exception as e:
                errors += 1
                logger.error(f"Error processing country for record {record[0]}: {str(e)}")
                conn.rollback()
        
        # Move to next batch
        offset += batch_size
    
    logger.info(f"Completed country normalization: processed {processed}, updated {updated}, errors {errors}")
    return {
        "processed": processed,
        "updated": updated,
        "errors": errors
    }

def fix_normalized_method(conn, batch_size: int = 100) -> Dict[str, int]:
    """
    Fix missing normalized_method values in the unified_tenders table.
    
    Args:
        conn: Database connection
        batch_size: Number of records to process in each batch
        
    Returns:
        Dict with statistics about the operation
    """
    logger.info("Starting normalized_method fixes...")
    
    # Get count of records with missing normalized_method
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT COUNT(*) FROM unified_tenders 
        WHERE normalized_method IS NULL OR normalized_method = ''
        """
    )
    total_records = cursor.fetchone()[0]
    logger.info(f"Found {total_records} records with missing normalized_method")
    
    # Process in batches
    processed = 0
    updated = 0
    errors = 0
    
    # Get records in batches
    offset = 0
    while offset < total_records:
        cursor.execute(
            """
            SELECT id, source_table, procurement_method 
            FROM unified_tenders 
            WHERE normalized_method IS NULL OR normalized_method = '' 
            ORDER BY id 
            LIMIT %s OFFSET %s
            """,
            (batch_size, offset)
        )
        records = cursor.fetchall()
        
        if not records:
            break
        
        for record in records:
            try:
                record_id = record[0]
                source_table = record[1]
                procurement_method = record[2]
                
                # Create a row dict for the helper function
                row = {
                    "source_table": source_table,
                    "procurement_method": procurement_method
                }
                
                # Determine normalized method
                normalized_method = determine_normalized_method(row)
                
                # Update the record
                update_cursor = conn.cursor()
                update_cursor.execute(
                    "UPDATE unified_tenders SET normalized_method = %s WHERE id = %s",
                    (normalized_method, record_id)
                )
                conn.commit()
                logger.info(f"Set normalized_method for {source_table} record {record_id}: {normalized_method}")
                updated += 1
                
                processed += 1
                
                # Log progress
                if processed % 100 == 0:
                    logger.info(f"Processed {processed}/{total_records} normalized_method values, updated {updated}")
                
            except Exception as e:
                errors += 1
                logger.error(f"Error processing normalized_method for record {record[0]}: {str(e)}")
                conn.rollback()
        
        # Move to next batch
        offset += batch_size
    
    logger.info(f"Completed normalized_method fixes: processed {processed}, updated {updated}, errors {errors}")
    return {
        "processed": processed,
        "updated": updated,
        "errors": errors
    }

def fix_organization_names(conn, batch_size: int = 100) -> Dict[str, int]:
    """
    Fix missing organization names in the unified_tenders table.
    
    Args:
        conn: Database connection
        batch_size: Number of records to process in each batch
        
    Returns:
        Dict with statistics about the operation
    """
    logger.info("Starting organization name extraction...")
    
    # Get count of records with missing organization names but with project names
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT COUNT(*) FROM unified_tenders 
        WHERE (organization_name IS NULL OR organization_name = '' OR LENGTH(organization_name) < 3)
        AND project_name IS NOT NULL AND LENGTH(project_name) > 10
        """
    )
    total_records = cursor.fetchone()[0]
    logger.info(f"Found {total_records} records with missing organization names but with project names")
    
    # Process in batches
    processed = 0
    updated = 0
    errors = 0
    
    # Get records in batches
    offset = 0
    while offset < total_records:
        cursor.execute(
            """
            SELECT id, project_name, title 
            FROM unified_tenders 
            WHERE (organization_name IS NULL OR organization_name = '' OR LENGTH(organization_name) < 3)
            AND project_name IS NOT NULL AND LENGTH(project_name) > 10
            ORDER BY id 
            LIMIT %s OFFSET %s
            """,
            (batch_size, offset)
        )
        records = cursor.fetchall()
        
        if not records:
            break
        
        for record in records:
            try:
                record_id = record[0]
                project_name = record[1]
                title = record[2]
                
                # Try to extract organization from project name
                org = extract_organization(project_name)
                
                # If not found in project name, try title
                if not org and title and len(title) > 10:
                    org = extract_organization(title)
                
                # Update if organization found
                if org:
                    update_cursor = conn.cursor()
                    update_cursor.execute(
                        "UPDATE unified_tenders SET organization_name = %s WHERE id = %s",
                        (org, record_id)
                    )
                    conn.commit()
                    logger.info(f"Extracted organization for record {record_id}: {org}")
                    updated += 1
                
                processed += 1
                
                # Log progress
                if processed % 100 == 0:
                    logger.info(f"Processed {processed}/{total_records} organization extractions, updated {updated}")
                
            except Exception as e:
                errors += 1
                logger.error(f"Error extracting organization for record {record[0]}: {str(e)}")
                conn.rollback()
        
        # Move to next batch
        offset += batch_size
    
    logger.info(f"Completed organization extraction: processed {processed}, updated {updated}, errors {errors}")
    return {
        "processed": processed,
        "updated": updated,
        "errors": errors
    }

def main():
    """Main function to run the normalization fixes."""
    parser = argparse.ArgumentParser(description="Fix normalization issues in existing records")
    parser.add_argument("--skip-country", action="store_true", help="Skip country normalization")
    parser.add_argument("--skip-method", action="store_true", help="Skip normalized_method fixes")
    parser.add_argument("--skip-organization", action="store_true", help="Skip organization name extraction")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")
    args = parser.parse_args()
    
    # Load database configuration
    db_config = {}
    config_file = "config.json"
    
    # Try to load from config file
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            db_config = json.load(f)
    # Otherwise, try environment variables
    else:
        db_config = {
            "host": os.environ.get("DB_HOST", "localhost"),
            "port": int(os.environ.get("DB_PORT", 5432)),
            "database": os.environ.get("DB_NAME", "postgres"),
            "user": os.environ.get("DB_USER", "postgres"),
            "password": os.environ.get("DB_PASSWORD", "")
        }
    
    # Connect to database
    try:
        conn = get_connection(db_config)
        logger.info("Connected to database")
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        sys.exit(1)
    
    start_time = time.time()
    results = {}
    
    # Run the fixes
    if not args.skip_country:
        results["country"] = fix_country_values(conn, args.batch_size)
    
    if not args.skip_method:
        results["normalized_method"] = fix_normalized_method(conn, args.batch_size)
    
    if not args.skip_organization:
        results["organization"] = fix_organization_names(conn, args.batch_size)
    
    # Log summary
    elapsed = time.time() - start_time
    logger.info(f"Completed all fixes in {elapsed:.2f} seconds")
    logger.info("Summary of fixes:")
    
    for fix_type, stats in results.items():
        logger.info(f"  {fix_type}: processed {stats['processed']}, updated {stats['updated']}, errors {stats['errors']}")
    
    # Close connection
    conn.close()

if __name__ == "__main__":
    main() 