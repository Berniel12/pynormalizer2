#!/usr/bin/env python3
"""
Script to fix incorrect country normalizations in the unified_tenders table.
"""
import os
import logging
import time
import argparse
import json
from datetime import datetime

from pynormalizer.utils.db import get_connection
from pynormalizer.utils.normalizer_helpers import log_before_after

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_country_normalization.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Mapping of incorrect country normalizations to correct values
COUNTRY_FIXES = {
    "Multinational": "Multinational",  # Keep as is, don't map to India
    "Burundi": "Burundi",              # Keep as is, don't map to Russia
    "Zambia": "Zambia",                # Keep as is, don't map to South Africa
    "Somalia": "Somalia",              # Keep as is, don't map to Mali
    "Botswana": "Botswana",            # Keep as is, don't map to Namibia
    "Bostwana": "Botswana",            # Fix spelling
    "Tanzania": "Tanzania",            # Keep as is, don't map to South Africa
    "CaboVerde": "Cape Verde",         # Standardize name
    "Cabo Verde": "Cape Verde",        # Standardize name
    "Eswatini": "Eswatini",            # Keep as is, don't map to India
    "RDC": "Democratic Republic of the Congo",  # Expand abbreviation
    "RCA": "Central African Republic",  # Expand abbreviation
    "Côte D'Ivoire": "Ivory Coast",     # Standardize to English name
    "Côte d'Ivoire": "Ivory Coast",     # Standardize to English name
    "Program for Integrated Rural Sanitation In Upper Egypt": "Egypt",  # Fix project title as country
    "Program for Integrated Rural Sanitation In Upper Egypt (simplified)": "Egypt"  # Fix project title as country
}

def fix_incorrect_country_normalizations(db_config=None, batch_size=100, dry_run=False):
    """
    Fix incorrect country normalizations in the unified_tenders table.
    
    Args:
        db_config: Database configuration (if None, uses environment variables)
        batch_size: Number of records to process in each batch
        dry_run: If True, only log changes without updating the database
        
    Returns:
        dict: Statistics about the fixes applied
    """
    start_time = time.time()
    stats = {
        "total_checked": 0,
        "total_fixed": 0,
        "fixes_by_country": {}
    }
    
    try:
        # Connect to the database using Supabase client
        supabase = get_connection(db_config)
        
        # Process each incorrect country normalization
        for incorrect, correct in COUNTRY_FIXES.items():
            logger.info(f"Checking for records with country='{incorrect}'")
            
            # Count records with this country value
            count_response = supabase.table('unified_tenders') \
                .select('id', count='exact') \
                .eq('country', incorrect) \
                .execute()
            
            count = count_response.count or 0
            logger.info(f"Found {count} records with country='{incorrect}'")
            stats["total_checked"] += count
            
            if count == 0:
                continue
                
            # Skip if the correct value is the same as the incorrect value
            if incorrect == correct:
                logger.info(f"Skipping '{incorrect}' as it should remain unchanged")
                continue
                
            # Process records in batches
            offset = 0
            fixed_count = 0
            
            while offset < count:
                # Get a batch of records
                records_response = supabase.table('unified_tenders') \
                    .select('id, country') \
                    .eq('country', incorrect) \
                    .range(offset, offset + batch_size - 1) \
                    .execute()
                
                records = records_response.data
                
                if not records:
                    break
                    
                # Process each record
                for record in records:
                    record_id = record['id']
                    country = record['country']
                    
                    log_before_after("country", country, correct)
                    
                    if not dry_run:
                        # Update the record
                        supabase.table('unified_tenders') \
                            .update({'country': correct}) \
                            .eq('id', record_id) \
                            .execute()
                    
                    fixed_count += 1
                
                offset += batch_size
                logger.info(f"Processed {min(offset, count)}/{count} records with country='{incorrect}'")
            
            # Update statistics
            stats["fixes_by_country"][incorrect] = fixed_count
            stats["total_fixed"] += fixed_count
            
            logger.info(f"Fixed {fixed_count} records with country='{incorrect}' -> '{correct}'")
        
        # Log summary
        elapsed = time.time() - start_time
        logger.info(f"Country normalization fix completed in {elapsed:.2f} seconds")
        logger.info(f"Total records checked: {stats['total_checked']}")
        logger.info(f"Total records fixed: {stats['total_fixed']}")
        
        for country, count in stats["fixes_by_country"].items():
            logger.info(f"  {country} -> {COUNTRY_FIXES[country]}: {count} records")
        
        return stats
    
    except Exception as e:
        logger.exception(f"Error fixing country normalizations: {e}")
        raise

def main():
    """Run the country normalization fix script."""
    parser = argparse.ArgumentParser(description="Fix incorrect country normalizations in the unified_tenders table")
    parser.add_argument("--dry-run", action="store_true", help="Only log changes without updating the database")
    parser.add_argument("--batch-size", type=int, default=100, help="Number of records to process in each batch")
    args = parser.parse_args()
    
    try:
        # Check if Supabase environment variables are set
        if not os.environ.get("SUPABASE_URL") or not os.environ.get("SUPABASE_KEY"):
            logger.error("Supabase environment variables not set. Please set SUPABASE_URL and SUPABASE_KEY.")
            return
        
        # Log start
        mode = "DRY RUN" if args.dry_run else "UPDATE"
        logger.info(f"Starting country normalization fix in {mode} mode")
        
        # Run the fix
        stats = fix_incorrect_country_normalizations(
            batch_size=args.batch_size,
            dry_run=args.dry_run
        )
        
        # Log completion
        logger.info(f"Country normalization fix completed. Fixed {stats['total_fixed']} records.")
    
    except Exception as e:
        logger.exception(f"Error during country normalization fix: {e}")
    
if __name__ == "__main__":
    main() 