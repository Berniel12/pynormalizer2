#!/usr/bin/env python
import os
import logging
import requests
from supabase import create_client, Client

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Add the missing category column to the unified_tenders table through Apify
    """
    # Get Supabase credentials from Apify environment
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("❌ SUPABASE_URL or SUPABASE_KEY environment variables are not set!")
        return
    
    logger.info(f"Using Supabase URL: {supabase_url}")
    logger.info("Attempting to add category column to unified_tenders table...")
    
    try:
        # Initialize Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Check if column exists first
        result = supabase.table("unified_tenders").select("id").limit(1).execute()
        if result.error:
            logger.error(f"Error connecting to Supabase: {result.error}")
            return
        
        logger.info("Successfully connected to Supabase")
        
        # Execute SQL directly through REST API
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json"
        }
        
        sql_endpoint = f"{supabase_url}/rest/v1/rpc/execute_sql"
        
        # Add the column if it doesn't exist
        sql = """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'unified_tenders' 
                AND column_name = 'category'
            ) THEN
                ALTER TABLE unified_tenders ADD COLUMN category TEXT;
                RAISE NOTICE 'Added category column';
            ELSE
                RAISE NOTICE 'Category column already exists';
            END IF;
        END
        $$;
        
        -- Reload the PostgREST schema cache
        NOTIFY pgrst, 'reload schema';
        """
        
        response = requests.post(
            sql_endpoint,
            headers=headers,
            json={"query": sql}
        )
        
        if response.status_code == 200:
            logger.info("✅ Schema update executed successfully")
            logger.info("✅ Schema cache reloaded")
        else:
            logger.error(f"Error updating schema: {response.status_code} - {response.text}")
            
    except Exception as e:
        logger.error(f"Error updating schema: {e}")

if __name__ == "__main__":
    main() 