#!/usr/bin/env python3
"""
Script to run the normalization process on Apify using Supabase.
"""
import os
import sys
import logging
import time
import argparse
import json
from datetime import datetime

# Debug import paths before attempting imports
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info(f"Python Path: {sys.path}")
logger.info(f"Working Directory: {os.getcwd()}")
logger.info(f"Directory Contents: {os.listdir('.')}")
logger.info(f"Pynormalizer Directory: {os.path.exists('pynormalizer')}")

# Check if Supabase environment variables are set
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
if not supabase_url or not supabase_key:
    logger.error("❌ SUPABASE_URL or SUPABASE_KEY environment variables are not set!")
    logger.error("Please set these environment variables in the Apify console.")
    logger.error("Current environment variables:")
    for key in os.environ:
        if key.startswith("SUPABASE") or key.startswith("APIFY"):
            # Hide the actual key value for security
            if key == "SUPABASE_KEY":
                value = "****" if os.environ[key] else "NOT SET"
            else:
                value = os.environ[key] or "NOT SET"
            logger.error(f"  {key}: {value}")
else:
    logger.info("✅ SUPABASE_URL and SUPABASE_KEY environment variables are set")

# Check pynormalizer structure for debugging
if os.path.exists('pynormalizer'):
    logger.info(f"Pynormalizer contents: {os.listdir('pynormalizer')}")
    if os.path.exists('pynormalizer/normalizers'):
        logger.info(f"Normalizers contents: {os.listdir('pynormalizer/normalizers')}")
    if os.path.exists('pynormalizer/models'):
        logger.info(f"Models contents: {os.listdir('pynormalizer/models')}")

# Ensure pynormalizer is in the Python path if not already
sys.path.insert(0, os.getcwd())

# Try multiple import strategies to increase reliability
normalize_all_tenders = None
normalize_tedeu = None

# Strategy 1: Import through the package structure (recommended way)
try:
    # First, check if supabase module is available
    try:
        import supabase
        logger.info(f"✅ Supabase module is available: {supabase.__version__ if hasattr(supabase, '__version__') else 'version unknown'}")
    except ImportError as e:
        logger.error(f"❌ Failed to import supabase module: {e}")
        logger.error(f"Installed packages: {[p for p in sys.modules.keys() if not p.startswith('_')]}")
    
    # Now try to import our client function
    try:
        from pynormalizer.utils.db import get_supabase_client
        logger.info("✅ Successfully imported get_supabase_client")
    except ImportError as e:
        logger.error(f"❌ Failed to import get_supabase_client: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Try importing directly from pynormalizer package
    from pynormalizer import normalize_all_tenders
    logger.info("✅ Successfully imported normalize_all_tenders from package")
    
    # Explicitly try to import normalize_tedeu
    try:
        from pynormalizer import normalize_tedeu
        logger.info("✅ Successfully imported normalize_tedeu from package")
    except ImportError as e:
        logger.warning(f"Failed to import normalize_tedeu from package: {e}")
        try:
            from pynormalizer.normalizers.tedeu_normalizer import normalize_tedeu
            logger.info("✅ Successfully imported normalize_tedeu from normalizers.tedeu_normalizer")
        except ImportError as e:
            logger.error(f"Failed to import normalize_tedeu from any location: {e}")
    
    from pynormalizer.utils.translation import setup_translation_models, get_supported_languages
    logger.info("✅ Successfully imported translation modules")
except ImportError as e:
    logger.warning(f"Package import failed: {e}, trying alternative import method...")
    
    # Strategy 2: Direct import from main module
    try:
        from pynormalizer.main import normalize_all_tenders
        logger.info("✅ Successfully imported normalize_all_tenders from main module")
        
        # Try to import normalize_tedeu from normalizers
        try:
            from pynormalizer.normalizers.tedeu_normalizer import normalize_tedeu
            logger.info("✅ Successfully imported normalize_tedeu from normalizers.tedeu_normalizer")
        except ImportError as e:
            logger.error(f"Failed to import normalize_tedeu from normalizers: {e}")
    except ImportError as e:
        logger.error(f"Main module import failed: {e}")
        
        # Strategy 3: Direct import with module loading
        try:
            import importlib.util
            
            # Load main module for normalize_all_tenders
            main_spec = importlib.util.spec_from_file_location("main", "pynormalizer/main.py")
            main = importlib.util.module_from_spec(main_spec)
            main_spec.loader.exec_module(main)
            normalize_all_tenders = main.normalize_all_tenders
            logger.info("✅ Successfully imported normalize_all_tenders using importlib")
            
            # Load tedeu_normalizer module for normalize_tedeu
            try:
                tedeu_spec = importlib.util.spec_from_file_location(
                    "tedeu_normalizer", 
                    "pynormalizer/normalizers/tedeu_normalizer.py"
                )
                tedeu_module = importlib.util.module_from_spec(tedeu_spec)
                tedeu_spec.loader.exec_module(tedeu_module)
                normalize_tedeu = tedeu_module.normalize_tedeu
                logger.info("✅ Successfully imported normalize_tedeu using importlib")
            except Exception as e:
                logger.error(f"Failed to import normalize_tedeu using importlib: {e}")
        except Exception as e:
            logger.error(f"All import strategies failed: {e}")
            logger.error(f"Module info - pynormalizer exists: {os.path.exists('pynormalizer')}")
            if os.path.exists('pynormalizer'):
                logger.error(f"Pynormalizer contents: {os.listdir('pynormalizer')}")
                if os.path.exists('pynormalizer/main.py'):
                    with open('pynormalizer/main.py', 'r') as f:
                        logger.error(f"First 20 lines of main.py: {f.readlines()[:20]}")
                if os.path.exists('pynormalizer/__init__.py'):
                    with open('pynormalizer/__init__.py', 'r') as f:
                        logger.error(f"__init__.py contents: {f.read()}")
                if os.path.exists('pynormalizer/normalizers/tedeu_normalizer.py'):
                    with open('pynormalizer/normalizers/tedeu_normalizer.py', 'r') as f:
                        logger.error(f"First 20 lines of tedeu_normalizer.py: {f.readlines()[:20]}")
            raise

# Verify that we successfully imported the functions
if normalize_all_tenders is None:
    logger.error("Failed to import normalize_all_tenders using any method")
    raise ImportError("normalize_all_tenders could not be imported")
else:
    logger.info(f"✅ normalize_all_tenders successfully imported: {normalize_all_tenders.__module__}")

# Verify normalize_tedeu separately since it's specifically causing issues
if normalize_tedeu is None:
    logger.warning("⚠️ normalize_tedeu could not be imported, some functionality may be limited")
else:
    logger.info(f"✅ normalize_tedeu successfully imported: {normalize_tedeu.__module__}")

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
    parser.add_argument("--max-runtime", type=int, default=18000, help="Maximum runtime in seconds (default: 18000 = 5 hours)")
    parser.add_argument("--process-all", action="store_true", help="Process all records, including already normalized ones")
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
        max_runtime = args.max_runtime
        skip_normalized = not args.process_all  # Skip by default unless process-all is specified
        
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
                
                # Get max runtime (if specified)
                if "maxRuntime" in apify_config and apify_config["maxRuntime"] is not None:
                    max_runtime = apify_config["maxRuntime"]
                    logger.info(f"Using maxRuntime from Apify input: {max_runtime} seconds")
                
                # Check if we should process all records (including already normalized)
                if "processAll" in apify_config:
                    skip_normalized = not apify_config.get("processAll", False)
                    logger.info(f"Using processAll from Apify input: {not skip_normalized}")
            except Exception as e:
                logger.error(f"Error parsing Apify input: {e}")
        
        # Log start with mode based on settings
        mode = "TEST MODE" if test_mode else "PRODUCTION MODE"
        logger.info(f"Starting normalization process in {mode} using Supabase")
        logger.info(f"Supabase URL: {os.environ.get('SUPABASE_URL')}")
        
        # Set timeout deadline
        end_time_limit = start_time + max_runtime
        logger.info(f"Set maximum runtime to {max_runtime} seconds (will end at {datetime.fromtimestamp(end_time_limit).strftime('%H:%M:%S')})")
        
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
            # Add progress checking callback
            def progress_callback(processed, total, table_name):
                current_time = time.time()
                # Check if we've exceeded the maximum runtime
                if current_time > end_time_limit:
                    logger.warning(f"Maximum runtime of {max_runtime} seconds exceeded. Stopping processing.")
                    return False  # Return False to stop processing
                
                # Continue processing
                if processed % 10 == 0 or processed == total:
                    elapsed = current_time - start_time
                    logger.info(f"Processed {processed}/{total} records from {table_name} ({processed/total*100:.1f}%) in {elapsed:.2f}s")
                    
                    # If we're getting close to the time limit, log a warning
                    remaining_time = end_time_limit - current_time
                    if remaining_time < 300:  # Less than 5 minutes left
                        logger.warning(f"Only {remaining_time:.0f}s remaining before timeout!")
                
                return True  # Return True to continue processing
            
            # Execute normalization with progress callback
            logger.info(f"Starting normalization with Tables: {', '.join(tables) if tables else 'ALL'} (skip_normalized={skip_normalized})")
            results = normalize_all_tenders(
                db_config,
                tables=tables,  # None means all tables
                batch_size=args.batch_size,
                limit_per_table=limit_per_table,
                progress_callback=progress_callback,
                skip_normalized=skip_normalized
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