"""
Script for normalizing tender data from various sources.
"""
import argparse
import json
import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import traceback
from pynormalizer.db.db_client import DBClient
from pynormalizer.normalizers.normalizer import get_normalizer, normalize_single_tender
from pynormalizer.normalizers.base import normalize_all_tenders
from pynormalizer.normalizers import TABLE_MAPPING
from pynormalizer.utils.logger import logger
from pynormalizer.utils.apify_utils import get_apify_input

# Only load .env if environment variables aren't already set
try:
    from dotenv import load_dotenv
    # Check if any of the required environment variables are missing
    required_env_vars = ['SUPABASE_DB_HOST', 'SUPABASE_DB_USER', 'SUPABASE_DB_PASSWORD', 'SUPABASE_DB_NAME']
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    
    # Only load .env if we're missing environment variables
    if missing_vars:
        logger.info(f"Missing environment variables: {missing_vars}. Trying to load from .env file.")
        # Look for .env file in the current directory and parent directories
        for i in range(3):  # Try current directory and up to 2 parent directories
            env_path = os.path.join(os.path.dirname(__file__), '../' * i, '.env')
            if os.path.exists(env_path):
                load_dotenv(env_path, override=False)  # Don't override existing env vars
                logger.info(f"Loaded environment variables from {env_path}")
                break
    else:
        logger.info("Using existing environment variables (not loading from .env)")
except ImportError:
    logger.warning("dotenv package not found, environment variables must be set manually")

def main():
    """Main entry point for the normalizer."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Normalize tender data.')
    parser.add_argument('--tables', nargs='+', help='Tables to process')
    parser.add_argument('--limit', type=int, default=100, help='Maximum number of tenders to process per table')
    parser.add_argument('--process-all', action='store_true', help='Process all tenders, including already normalized ones')
    parser.add_argument('--skip-validation', action='store_true', help='Skip data validation')
    parser.add_argument('--skip-translation', action='store_true', help='Skip translation')
    parser.add_argument('--source-id', help='Process a specific tender by source ID')
    parser.add_argument('--save-interim', action='store_true', help='Save interim results')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    # Enable debug mode if requested
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    try:
        # Get input data from Apify
        apify_input = None
        try:
            if os.path.exists('./input.json'):
                with open('./input.json', 'r') as f:
                    apify_input = json.load(f)
                logger.info(f"Loaded Apify input: {apify_input}")
        except Exception as e:
            logger.warning(f"Apify input file not found at ./input.json")
        
        # Get tables to process
        tables = args.tables or []
        if apify_input and 'tables' in apify_input:
            tables = apify_input['tables']
        
        # If no tables specified, process all
        if not tables:
            logger.info("No tables specified, processing all")
            tables = None  # Use None to indicate all tables
        
        # Get limit
        limit = args.limit
        if apify_input and 'limit' in apify_input:
            limit = int(apify_input['limit'])
        
        # Get skip_normalized flag
        skip_normalized = not args.process_all
        if apify_input and 'skip_normalized' in apify_input:
            skip_normalized = apify_input['skip_normalized']
        
        # Log parameters
        logger.info(f"Starting normalization with Tables: {tables or 'ALL'} (skip_normalized={skip_normalized})")
        
        # Check if required environment variables are set
        required_env_vars = ['SUPABASE_DB_HOST', 'SUPABASE_DB_USER', 'SUPABASE_DB_PASSWORD', 'SUPABASE_DB_NAME']
        for var in required_env_vars:
            if not os.environ.get(var):
                logger.error(f"Environment variable {var} is not set!")
                return 1
        
        # Log DB connection info (without sensitive credentials)
        logger.info(f"Connecting to database at {os.environ.get('SUPABASE_DB_HOST')}:{os.environ.get('SUPABASE_DB_PORT', '5432')} as {os.environ.get('SUPABASE_DB_USER')}")
        
        # Initialize the DB client
        db_client = DBClient()
        
        # Start timer
        start_time = time.time()
        
        # Normalize tenders - call the normalize_all_tenders function correctly
        try:
            stats = normalize_all_tenders(
                tables=tables,
                limit=limit,
                skip_normalized=skip_normalized,
                process_all=args.process_all,
                db_client=db_client
            )
            
            # Calculate time taken
            stats["time_taken"] = time.time() - start_time
            
            # Log statistics
            logger.info(f"Normalization complete!")
            logger.info(f"Tables processed: {len(stats['tables_processed'])}")
            logger.info(f"Total tenders processed: {stats['total_processed']}")
            logger.info(f"Total tenders normalized: {stats['total_normalized']}")
            logger.info(f"Total tenders failed: {stats['total_failed']}")
            logger.info(f"Time taken: {stats['time_taken']:.2f} seconds")
            
            if stats["errors"]:
                for error in stats["errors"][:10]:  # Only show first 10 errors
                    logger.error(f"Error: {error}")
                
                if len(stats["errors"]) > 10:
                    logger.error(f"... and {len(stats['errors']) - 10} more errors")
            
        except Exception as e:
            logger.error(f"Error in normalize_all_tenders: {str(e)}")
            logger.error(traceback.format_exc())
            return 1
        
        # Return success code
        return 0
        
    except Exception as e:
        logger.error(f"Unhandled exception in main: {str(e)}")
        logger.exception(e)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 