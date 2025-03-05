#!/usr/bin/env python3
"""
Script to run the normalization process on Apify using Supabase.
"""
import os
import logging
import time
import argparse
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
    parser.add_argument("--test", action="store_true", help="Run in test mode (2 records per source)")
    parser.add_argument("--tables", type=str, nargs="*", help="Specific tables to process")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for processing")
    args = parser.parse_args()
    
    try:
        # Check if Supabase environment variables are set
        if not os.environ.get("SUPABASE_URL") or not os.environ.get("SUPABASE_KEY"):
            logger.error("Supabase environment variables not set. Please set SUPABASE_URL and SUPABASE_KEY.")
            return
        
        # Log start
        mode = "TEST MODE" if args.test else "PRODUCTION MODE"
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
        
        # Run normalization
        if args.test:
            # In test mode, limit to 2 records per table
            limit_per_table = 2
            logger.info(f"TEST MODE: Processing max {limit_per_table} records per table")
        else:
            # In production mode, process all records
            limit_per_table = None
            logger.info("PRODUCTION MODE: Processing all records")
        
        # Run normalization with the specified parameters
        results = normalize_all_tenders(
            db_config,
            tables=args.tables,  # None means all tables
            batch_size=args.batch_size,
            limit_per_table=limit_per_table
        )
        
        # Print summary
        total_processed = sum(results.values())
        logger.info(f"Normalization complete. Processed {total_processed} tenders.")
        for table_name, count in results.items():
            logger.info(f"  {table_name}: {count} tenders processed")
        
    except Exception as e:
        logger.exception(f"Error during normalization: {e}")
    finally:
        # Log completion time
        elapsed = time.time() - start_time
        logger.info(f"Process completed in {elapsed:.2f} seconds")

if __name__ == "__main__":
    main() 