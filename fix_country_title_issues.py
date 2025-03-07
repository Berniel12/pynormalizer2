#!/usr/bin/env python3
"""
Script to fix records where titles were incorrectly set as country values.

This script identifies and fixes records where country values are actually titles or other long text,
which indicates a normalization error.

Usage:
    ./fix_country_title_issues.py [--dry-run] [--batch-size BATCH_SIZE]
"""

import argparse
import json
import logging
import os
import sys
import time
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_country_title_issues.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("fix_country_title_issues")

# Import helper functions
from pynormalizer.utils.db import get_connection
from pynormalizer.utils.normalizer_helpers import extract_location_info

def is_valid_country(value: str) -> bool:
    """
    Check if a string is likely to be a valid country name.
    
    Args:
        value: String to check
        
    Returns:
        bool: True if the string is likely a country name, False otherwise
    """
    if not value or not isinstance(value, str):
        return False
        
    # Clean the string
    value = value.strip()
    
    # Check if it's too long to be a country name
    if len(value) > 50:
        return False
        
    # Check if it contains certain keywords that suggest it's a title
    title_indicators = [
        "procurement of", "supply of", "provision of", "recruitment of",
        "consultancy for", "consultant for", "services for", "support to",
        "evaluation of", "implementation of", "construction of", "rehabilitation of",
        "supervision of", "monitoring of", "acquisition of", "assessment of"
    ]
    
    for indicator in title_indicators:
        if indicator.lower() in value.lower():
            return False
    
    # Check if it has too many spaces (suggesting it's a phrase, not a country)
    if value.count(" ") > 5:
        return False
        
    return True

def fix_country_title_issues(conn, dry_run: bool = False, batch_size: int = 100) -> Dict[str, int]:
    """
    Fix country values that are actually titles or other long text.
    
    Args:
        conn: Database connection
        dry_run: If True, don't apply changes
        batch_size: Number of records to process in each batch
        
    Returns:
        Dict with statistics about the operation
    """
    logger.info("Starting country title issue fixes...")
    
    # Get count of records with potentially invalid country values
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM unified_tenders WHERE LENGTH(country) > 50")
    total_records = cursor.fetchone()[0]
    logger.info(f"Found {total_records} records with potentially invalid country values")
    
    # Process in batches
    processed = 0
    updated = 0
    errors = 0
    
    # Log title-as-country instances for manual review
    title_country_instances = []
    
    # Get records in batches
    offset = 0
    while offset < total_records:
        cursor.execute(
            """
            SELECT id, source_table, source_id, country, title, description 
            FROM unified_tenders 
            WHERE LENGTH(country) > 50
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
                source_id = record[2]
                current_country = record[3]
                title = record[4]
                description = record[5]
                
                logger.info(f"Processing record {record_id} from {source_table}:")
                logger.info(f"  Current country: {current_country}")
                
                # Extract potential country name from title or description
                extracted_country = None
                
                # First try to extract from title
                if title:
                    location_info = extract_location_info(title)
                    if location_info and location_info[0]:
                        extracted_country = location_info[0]
                        logger.info(f"  Extracted country from title: {extracted_country}")
                
                # If not found in title, try description
                if not extracted_country and description:
                    location_info = extract_location_info(description)
                    if location_info and location_info[0]:
                        extracted_country = location_info[0]
                        logger.info(f"  Extracted country from description: {extracted_country}")
                
                # If still not found, set to "Unknown"
                if not extracted_country:
                    extracted_country = "Unknown"
                    logger.info("  Could not extract country, setting to 'Unknown'")
                
                # Record the title-as-country instance for manual review
                title_country_instances.append({
                    "id": record_id,
                    "source_table": source_table,
                    "source_id": source_id,
                    "original_country": current_country,
                    "extracted_country": extracted_country,
                    "title": title
                })
                
                # Update the database record if not dry run
                if not dry_run:
                    update_cursor = conn.cursor()
                    update_cursor.execute(
                        """
                        UPDATE unified_tenders 
                        SET country = %s, 
                            normalized_method = 'corrected-title-as-country'
                        WHERE id = %s
                        """,
                        (extracted_country, record_id)
                    )
                    conn.commit()
                    logger.info(f"  Updated country to: {extracted_country}")
                    updated += 1
                else:
                    logger.info("  Dry run - no changes made")
                
                processed += 1
                
                # Log progress
                if processed % 10 == 0:
                    logger.info(f"Processed {processed}/{total_records} records, updated {updated if not dry_run else 0}")
                
            except Exception as e:
                errors += 1
                logger.error(f"Error processing record {record[0]}: {str(e)}")
                if not dry_run:
                    conn.rollback()
        
        # Move to next batch
        offset += batch_size
    
    # Save the title-as-country instances to a JSON file for review
    with open("title_country_instances.json", "w") as f:
        json.dump(title_country_instances, f, indent=2)
    
    logger.info(f"Saved {len(title_country_instances)} title-as-country instances to title_country_instances.json")
    
    logger.info(f"Completed country title issue fixes: processed {processed}, updated {updated if not dry_run else 0}, errors {errors}")
    return {
        "processed": processed,
        "updated": updated if not dry_run else 0,
        "errors": errors
    }

def main():
    """Main function to run the title-as-country fixes."""
    parser = argparse.ArgumentParser(description="Fix records where titles were incorrectly set as country values")
    parser.add_argument("--dry-run", action="store_true", help="Run without making changes to the database")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")
    args = parser.parse_args()
    
    # Try to get Supabase connection from environment variables
    db_config = {}
    if "SUPABASE_URL" in os.environ and "SUPABASE_KEY" in os.environ:
        logger.info("Using Supabase connection from environment variables")
    else:
        # Otherwise try database config
        config_file = "config.json"
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                db_config = json.load(f)
            logger.info("Using database config from config.json")
        else:
            # Try environment variables for direct database connection
            db_config = {
                "host": os.environ.get("DB_HOST", "localhost"),
                "port": int(os.environ.get("DB_PORT", 5432)),
                "database": os.environ.get("DB_NAME", "postgres"),
                "user": os.environ.get("DB_USER", "postgres"),
                "password": os.environ.get("DB_PASSWORD", "")
            }
            logger.info("Using database config from environment variables")
    
    # Connect to database
    try:
        conn = get_connection(db_config)
        logger.info("Connected to database")
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        sys.exit(1)
    
    start_time = time.time()
    
    # Run the fixes
    results = fix_country_title_issues(conn, args.dry_run, args.batch_size)
    
    # Log summary
    elapsed = time.time() - start_time
    logger.info(f"Completed all fixes in {elapsed:.2f} seconds")
    logger.info(f"Summary: processed {results['processed']}, updated {results['updated']}, errors {results['errors']}")
    
    # Close connection
    conn.close()

if __name__ == "__main__":
    main() 