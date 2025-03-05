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
    
    # Set limit for test mode
    if args.test:
        logger.info("Running in TEST mode with 2 records per table")
        limit = 2
    else:
        limit = args.limit
    
    # Run normalization
    try:
        logger.info(f"Starting normalization process...")
        if limit:
            logger.info(f"Processing up to {limit} records per table")
        
        results = normalize_all_tenders(db_config, args.tables, args.batch_size, limit)
        
        # Print summary
        total = sum(results.values())
        logger.info("\nNormalization Results:")
        logger.info("=====================")
        for table, count in results.items():
            logger.info(f"{table}: {count} tenders processed")
        logger.info(f"Total: {total} tenders processed")
        
        # Save report if output file specified
        if args.output:
            report = {
                "timestamp": datetime.utcnow().isoformat(),
                "duration_seconds": time.time() - start_time,
                "total_processed": total,
                "results_by_table": results,
                "limit_per_table": limit,
                "batch_size": args.batch_size
            }
            
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Normalization report saved to {args.output}")
        
    except Exception as e:
        logger.exception(f"Error during normalization: {e}")
    finally:
        elapsed = time.time() - start_time
        logger.info(f"Process completed in {elapsed:.2f} seconds")

if __name__ == "__main__":
    main() 