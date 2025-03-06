#!/usr/bin/env python3
"""
Script to run the normalization process on Apify using Supabase.
"""
import os
import logging
import time
import argparse
import json
from datetime import datetime

from pynormalizer.utils.db import get_supabase_client
from pynormalizer.main import normalize_all_tenders
from pynormalizer.utils.translation import setup_translation_models, get_supported_languages

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("apify_normalize.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Run the normalization process on Apify."""
    start_time = time.time()
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Normalize tender data using Supabase connection")
    parser.add_argument("--test", action="store_true", help="Run in test mode (process fewer records)")
    parser.add_argument("--tables", type=str, nargs="*", help="Specific tables to process")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for processing")
    parser.add_argument("--limit", type=int, help="Maximum number of records to process per table")
    args = parser.parse_args()
    
    try:
        # Check if Supabase environment variables are set
        if not os.environ.get("SUPABASE_URL") or not os.environ.get("SUPABASE_KEY"):
            logger.error("Supabase environment variables not set. Please set SUPABASE_URL and SUPABASE_KEY.")
            return
        
        # Check for Apify environment variables
        apify_input = os.environ.get("APIFY_INPUT_JSON")
        test_mode = args.test
        tables = args.tables
        limit_per_table = args.limit
        
        # Parse Apify input if available (overrides command-line arguments)
        if apify_input:
            try:
                logger.info("Reading input from Apify environment")
                apify_config = json.loads(apify_input)
                
                # Get source name (table)
                source_name = apify_config.get("sourceName")
                if source_name and source_name.strip():
                    tables = [source_name.strip()]
                    logger.info(f"Processing specific source from Apify input: {source_name}")
                
                # Get test mode setting (overrides command line)
                if "testMode" in apify_config:
                    test_mode = apify_config.get("testMode", False)
                    logger.info(f"Using testMode from Apify input: {test_mode}")
                
                # Get limit (overrides command line)
                if "limit" in apify_config and apify_config["limit"] is not None:
                    limit_per_table = apify_config["limit"]
                    logger.info(f"Using limit from Apify input: {limit_per_table}")
            except Exception as e:
                logger.error(f"Error parsing Apify input: {e}")
        
        # Log start with mode based on settings
        mode = "TEST MODE" if test_mode else "PRODUCTION MODE"
        logger.info(f"Starting normalization process in {mode} using Supabase")
        logger.info(f"Supabase URL: {os.environ.get('SUPABASE_URL')}")
        
        # Log language support
        try:
            supported_langs = get_supported_languages()
            logger.info(f"Supported languages for translation: {', '.join(supported_langs.keys())}")
        except Exception as e:
            logger.warning(f"Could not determine supported languages: {e}")
        
        # Initialize translation models
        try:
            logger.info("Initializing translation models...")
            setup_translation_models()
            logger.info("Translation models initialized successfully")
        except Exception as e:
            logger.warning(f"Translation model initialization failed: {e}")
            logger.warning("Continuing with fallback translation methods")
        
        # Create empty config - we'll use environment variables instead
        db_config = {}
        
        # Set the limit based on mode
        if test_mode:
            # In test mode, limit to 3 records per table as per Apify config
            if not limit_per_table or limit_per_table > 3:
                limit_per_table = 3
            logger.info(f"TEST MODE: Processing max {limit_per_table} records per table")
        else:
            # In production mode, use the specified limit or process all records
            if limit_per_table:
                logger.info(f"PRODUCTION MODE: Processing up to {limit_per_table} records per table")
            else:
                logger.info("PRODUCTION MODE: Processing all records (no limit)")
        
        # Run normalization with the specified parameters
        try:
            results = normalize_all_tenders(
                db_config,
                tables=tables,  # None means all tables
                batch_size=args.batch_size,
                limit_per_table=limit_per_table
            )
            
            # Print summary
            total_processed = sum(results.values())
            logger.info(f"Normalization complete. Processed {total_processed} tenders.")
            for table_name, count in results.items():
                logger.info(f"  {table_name}: {count} tenders processed")
        except Exception as e:
            logger.error(f"Error during normalization: {e}")
            raise
    except Exception as e:
        logger.exception(f"Error during normalization: {e}")
    finally:
        # Log completion time
        elapsed = time.time() - start_time
        logger.info(f"Process completed in {elapsed:.2f} seconds")

if __name__ == "__main__":
    main() 