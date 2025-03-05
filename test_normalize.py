#!/usr/bin/env python3
"""
Test script for normalizing 2 tenders from each source.
This is useful for evaluating the normalization quality without processing the full dataset.
"""
import os
import logging
import time
import json
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
        logging.FileHandler("test_normalize.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Run the test normalization process."""
    start_time = time.time()
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Test tender data normalization with a small sample")
    parser.add_argument("--tables", type=str, nargs="*", help="Specific tables to process (default: all)")
    parser.add_argument("--limit", type=int, default=2, help="Number of records per source (default: 2)")
    parser.add_argument("--output", type=str, help="Output file for normalization report")
    args = parser.parse_args()
    
    try:
        # Check if Supabase environment variables are set
        if not os.environ.get("SUPABASE_URL") or not os.environ.get("SUPABASE_KEY"):
            logger.error("Supabase environment variables not set. Please set SUPABASE_URL and SUPABASE_KEY.")
            return
        
        # Log test mode
        logger.info(f"Starting test normalization with {args.limit} records per source")
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
        
        # Use empty config for Supabase
        db_config = {}
        
        # Run normalization with limit
        results = normalize_all_tenders(
            db_config,
            tables=args.tables,
            batch_size=10,
            limit_per_table=args.limit
        )
        
        # Print summary
        total_processed = sum(results.values())
        logger.info(f"Test normalization complete. Processed {total_processed} tenders.")
        for table_name, count in results.items():
            logger.info(f"  {table_name}: {count} tenders processed")
        
        # Save report if output file specified
        if args.output:
            report = {
                "timestamp": datetime.utcnow().isoformat(),
                "duration_seconds": time.time() - start_time,
                "total_processed": total_processed,
                "results_by_table": results,
                "limit_per_table": args.limit
            }
            
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Test report saved to {args.output}")
        
    except Exception as e:
        logger.exception(f"Error during test normalization: {e}")
    finally:
        # Log completion time
        elapsed = time.time() - start_time
        logger.info(f"Test completed in {elapsed:.2f} seconds")

if __name__ == "__main__":
    main() 