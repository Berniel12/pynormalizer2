import argparse
import os
import logging
from pynormalizer.db.db_client import DBClient
from pynormalizer.normalizers.normalizer import get_normalizer, normalize_single_tender
from pynormalizer.normalizers.base import normalize_all_tenders
from pynormalizer.normalizers import TABLE_MAPPING
from pynormalizer.utils.logger import logger
from pynormalizer.utils.apify_utils import get_apify_input

def main():
    """Main entry point for the normalizer."""
    try:
        # Set up argument parser
        parser = argparse.ArgumentParser(description='Normalize tender data')
        parser.add_argument('--tables', type=str, help='Comma-separated list of tables to normalize')
        parser.add_argument('--limit', type=int, default=5000, help='Maximum number of tenders to normalize per table')
        parser.add_argument('--skip-normalized', action='store_true', default=True, help='Skip already normalized tenders')
        parser.add_argument('--process-all', action='store_true', default=False, help='Process all tenders, regardless of normalization status')
        parser.add_argument('--single-id', type=str, help='Process a single tender by ID')
        parser.add_argument('--single-table', type=str, help='Table name for single tender processing')
        
        # Parse arguments
        args = parser.parse_args()
        
        # Check if we're getting tables from environment/apify input
        apify_input = get_apify_input()
        
        # Get tables from arguments or environment
        tables = None
        if args.tables:
            tables = args.tables.split(',')
            tables = [table.strip() for table in tables]
        elif apify_input and 'tables' in apify_input and apify_input['tables']:
            tables = apify_input['tables'].split(',')
            tables = [table.strip() for table in tables]
            
        # Log configuration
        logger.info(f"Starting normalization with Tables: {tables if tables else 'ALL'} (skip_normalized={args.skip_normalized})")
        
        # Check if Supabase environment variables are set
        for var in ['SUPABASE_DB_HOST', 'SUPABASE_DB_USER', 'SUPABASE_DB_PASSWORD', 'SUPABASE_DB_NAME']:
            if not os.environ.get(var):
                logger.error(f"Environment variable {var} is not set!")
                return 1
        
        # Process a single tender if specified
        if args.single_id and args.single_table:
            logger.info(f"Processing single tender {args.single_id} from {args.single_table}")
            db_client = DBClient()
            query = f"SELECT * FROM {args.single_table} WHERE id = %s LIMIT 1"
            results = db_client._execute_query(query, (args.single_id,))
            
            if not results or len(results) == 0:
                logger.error(f"No tender found with ID {args.single_id} in table {args.single_table}")
                return 1
                
            tender_data = results[0]
            normalizer_id = TABLE_MAPPING.get(args.single_table)
            
            if not normalizer_id:
                logger.error(f"No normalizer found for table {args.single_table}")
                return 1
                
            normalizer = get_normalizer(normalizer_id)
            
            if not normalizer:
                logger.error(f"Normalizer {normalizer_id} is not available")
                return 1
                
            result = normalize_single_tender(
                tender_data=tender_data,
                table=args.single_table,
                normalizer=normalizer,
                db_client=db_client
            )
            
            logger.info(f"Normalization result: {result}")
            return 0
        
        # Process multiple tenders
        stats = normalize_all_tenders(
            tables=tables,  # Make sure this is a list or None
            limit=args.limit,
            skip_normalized=args.skip_normalized,
            process_all=args.process_all
        )
        
        # Log statistics
        logger.info(f"Normalization complete!")
        logger.info(f"Tables processed: {stats['tables_processed']}")
        logger.info(f"Total tenders processed: {stats['total_processed']}")
        logger.info(f"Total tenders normalized: {stats['total_normalized']}")
        logger.info(f"Total tenders failed: {stats['total_failed']}")
        logger.info(f"Time taken: {stats['time_taken']:.2f} seconds")
        
        if stats['errors']:
            for error in stats['errors'][:10]:  # Only show first 10 errors
                logger.error(f"Error: {error}")
            
            if len(stats['errors']) > 10:
                logger.error(f"... and {len(stats['errors']) - 10} more errors")
        
        # Return success code
        return 0
        
    except Exception as e:
        logger.error(f"Unhandled exception in main: {str(e)}")
        logger.exception(e)
        return 1

if __name__ == "__main__":
    exit(main()) 