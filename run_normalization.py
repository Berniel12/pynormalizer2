#!/usr/bin/env python3
"""
Simple script to run the normalization process from the command line.
"""
import os
import json
import argparse
import logging
import time
from datetime import datetime

from pynormalizer.main import normalize_all_tenders
from pynormalizer.utils.translation import setup_translation_models, get_supported_languages

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("run_normalization.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Run the normalization process."""
    start_time = time.time()
    
    parser = argparse.ArgumentParser(description="Normalize tender data from multiple sources")
    parser.add_argument("--config", type=str, default="config.json", help="Path to database config JSON file")
    parser.add_argument("--tables", type=str, nargs="*", help="Specific tables to process")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")
    parser.add_argument("--limit", type=int, help="Maximum number of records to process per table")
    parser.add_argument("--test", action="store_true", help="Run in test mode (2 records per table)")
    parser.add_argument("--output", type=str, help="Output file for normalization report")
    parser.add_argument("--full", action="store_true", help="Process all tenders from all sources")
    
    args = parser.parse_args()
    
    # Check for Apify environment variables first
    apify_input = os.environ.get("APIFY_INPUT_JSON")
    
    # Variables for configuration
    tables = args.tables
    test_mode = args.test
    limit_value = args.limit
    
    # Check if running on Apify and parse input
    if apify_input:
        try:
            logger.info("Reading input from Apify environment")
            apify_config = json.loads(apify_input)
            
            # Get source name (table)
            source_name = apify_config.get("sourceName")
            if source_name and source_name.strip():
                tables = [source_name.strip()]
                logger.info(f"Processing specific source from Apify input: {source_name}")
            
            # Get test mode setting
            test_mode = apify_config.get("testMode", False)
            
            # Get limit
            if "limit" in apify_config and apify_config["limit"] is not None:
                limit_value = apify_config["limit"]
                logger.info(f"Using limit from Apify input: {limit_value}")
        except Exception as e:
            logger.error(f"Error parsing Apify input: {e}")
    
    # Check for database connection environment variables
    if os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_KEY"):
        logger.info("Using Supabase connection from environment variables")
        db_config = {}  # Empty config will trigger env var usage
    else:
        # Load database config from file
        try:
            with open(args.config, 'r') as f:
                db_config = json.load(f)
            logger.info(f"Loaded database config from {args.config}")
        except FileNotFoundError:
            logger.error(f"Config file not found: {args.config}")
            logger.info("Please create a config.json file, specify a different config file with --config, or set SUPABASE_URL and SUPABASE_KEY environment variables")
            return
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in config file: {args.config}")
            return
    
    # Initialize translation models
    try:
        logger.info("Initializing translation models...")
        setup_translation_models()
        
        # Log supported languages
        supported_langs = get_supported_languages()
        logger.info(f"Supported languages for translation: {', '.join(supported_langs.keys())}")
    except Exception as e:
        logger.warning(f"Translation model initialization failed: {e}")
        logger.warning("Continuing with fallback translation methods")
    
    # Set limit based on mode
    if test_mode:
        # Use 3 records per table in test mode as per Apify config
        limit = 3
        logger.info(f"TEST MODE: Processing {limit} records per table")
    elif limit_value is not None:
        # Use specified limit
        limit = limit_value
        logger.info(f"Processing up to {limit} records per table")
    else:
        # Default to full processing (no limit)
        limit = None
        logger.info("FULL MODE: Processing all records (no limit)")
    
    # Set batch size for progress reporting
    batch_size = 100  # Always report every 100 tenders for consistency
    
    # Run normalization
    try:
        logger.info(f"Starting normalization process...")
        
        results = normalize_all_tenders(db_config, tables, batch_size, limit)
        
        # Print summary
        total = sum(results.values())
        logger.info("\nNormalization Complete Summary:")
        logger.info("==============================")
        for table, count in results.items():
            logger.info(f"{table}: {count} tenders processed")
        logger.info(f"Total: {total} tenders processed")
        
        # Save report if output file specified
        output_file = args.output
        if not output_file and os.environ.get("APIFY_DEFAULT_DATASET_ID"):
            # If running on Apify, create a timestamped output file
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_file = f"normalization_report_{timestamp}.json"
        
        if output_file:
            report = {
                "timestamp": datetime.utcnow().isoformat(),
                "duration_seconds": time.time() - start_time,
                "total_processed": total,
                "results_by_table": results,
                "limit_per_table": limit,
                "batch_size": batch_size
            }
            
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Normalization report saved to {output_file}")
        
    except Exception as e:
        logger.exception(f"Error during normalization: {e}")
    finally:
        elapsed = time.time() - start_time
        logger.info(f"Process completed in {elapsed:.2f} seconds")

if __name__ == "__main__":
    main() 