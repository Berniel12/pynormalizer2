#!/usr/bin/env python3
"""
Entry point script for Apify that:
1. Runs the country normalization fix script
2. Then runs the main normalization process
"""
import os
import sys
import logging
import subprocess
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("apify_entry.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point that runs both scripts in sequence.
    """
    start_time = os.path.basename(__file__)
    logger.info(f"Starting {start_time}")
    
    # Parse command-line arguments to pass through to apify_normalize.py
    parser = argparse.ArgumentParser(description="Run country fix and normalization on Apify")
    parser.add_argument("--test", action="store_true", help="Run in test mode (process fewer records)")
    parser.add_argument("--tables", type=str, nargs="*", help="Specific tables to process")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for processing")
    parser.add_argument("--limit", type=int, help="Maximum number of records to process per table")
    parser.add_argument("--skip-fix", action="store_true", help="Skip the country normalization fix")
    args = parser.parse_args()
    
    try:
        # Check if Supabase environment variables are set
        if not os.environ.get("SUPABASE_URL") or not os.environ.get("SUPABASE_KEY"):
            logger.error("Supabase environment variables not set. Please set SUPABASE_URL and SUPABASE_KEY.")
            sys.exit(1)
        
        # 1. Run country normalization fix first (unless skipped)
        if not args.skip_fix:
            logger.info("Running country normalization fix...")
            fix_result = subprocess.run(
                ["python", "fix_country_normalization.py", "--batch-size", str(args.batch_size or 100)],
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Country fix exit code: {fix_result.returncode}")
            logger.info(f"Country fix output:\n{fix_result.stdout}")
            if fix_result.stderr:
                logger.warning(f"Country fix stderr:\n{fix_result.stderr}")
        else:
            logger.info("Skipping country normalization fix as requested")
        
        # 2. Run main normalization process
        logger.info("Running main normalization process...")
        
        # Build command for apify_normalize.py with all relevant arguments
        normalize_cmd = ["python", "apify_normalize.py"]
        if args.test:
            normalize_cmd.append("--test")
        if args.tables:
            normalize_cmd.extend(["--tables"] + args.tables)
        if args.batch_size:
            normalize_cmd.extend(["--batch-size", str(args.batch_size)])
        if args.limit:
            normalize_cmd.extend(["--limit", str(args.limit)])
        
        # Run the normalization process
        normalize_result = subprocess.run(
            normalize_cmd,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"Normalization exit code: {normalize_result.returncode}")
        logger.info(f"Normalization output:\n{normalize_result.stdout}")
        if normalize_result.stderr:
            logger.warning(f"Normalization stderr:\n{normalize_result.stderr}")
        
        logger.info("Both processes completed successfully")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Process failed with exit code {e.returncode}")
        logger.error(f"Output: {e.stdout}")
        logger.error(f"Error: {e.stderr}")
        sys.exit(e.returncode)
    except Exception as e:
        logger.exception(f"Error in entry script: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 