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
    Add all missing columns to the unified_tenders table through Apify
    """
    # Get Supabase credentials from Apify environment
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("❌ SUPABASE_URL or SUPABASE_KEY environment variables are not set!")
        return
    
    logger.info(f"Using Supabase URL: {supabase_url}")
    logger.info("Attempting to add missing columns to unified_tenders table...")
    
    try:
        # Initialize Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Check if we can connect to the database
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
        
        # Add all missing columns
        sql = """
        DO $$
        BEGIN
            -- Add the category column if it doesn't exist
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
            
            -- Add the contact column if it doesn't exist
            IF NOT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'unified_tenders' 
                AND column_name = 'contact'
            ) THEN
                ALTER TABLE unified_tenders ADD COLUMN contact JSONB;
                RAISE NOTICE 'Added contact column';
            ELSE
                RAISE NOTICE 'Contact column already exists';
            END IF;
            
            -- Add the published_at column if it doesn't exist
            IF NOT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'unified_tenders' 
                AND column_name = 'published_at'
            ) THEN
                ALTER TABLE unified_tenders ADD COLUMN published_at TIMESTAMP WITH TIME ZONE;
                RAISE NOTICE 'Added published_at column';
            ELSE
                RAISE NOTICE 'published_at column already exists';
            END IF;
            
            -- Add the updated_at column if it doesn't exist
            IF NOT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'unified_tenders' 
                AND column_name = 'updated_at'
            ) THEN
                ALTER TABLE unified_tenders ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE;
                RAISE NOTICE 'Added updated_at column';
            ELSE
                RAISE NOTICE 'updated_at column already exists';
            END IF;
            
            -- Add the created_at column if it doesn't exist
            IF NOT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'unified_tenders' 
                AND column_name = 'created_at'
            ) THEN
                ALTER TABLE unified_tenders ADD COLUMN created_at TIMESTAMP WITH TIME ZONE;
                RAISE NOTICE 'Added created_at column';
            ELSE
                RAISE NOTICE 'created_at column already exists';
            END IF;
            
            -- Add the end_date column if it doesn't exist
            IF NOT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'unified_tenders' 
                AND column_name = 'end_date'
            ) THEN
                ALTER TABLE unified_tenders ADD COLUMN end_date TIMESTAMP WITH TIME ZONE;
                RAISE NOTICE 'Added end_date column';
            ELSE
                RAISE NOTICE 'end_date column already exists';
            END IF;
            
            -- Add the region column if it doesn't exist
            IF NOT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'unified_tenders' 
                AND column_name = 'region'
            ) THEN
                ALTER TABLE unified_tenders ADD COLUMN region TEXT;
                RAISE NOTICE 'Added region column';
            ELSE
                RAISE NOTICE 'region column already exists';
            END IF;
            
            -- Add the value column if it doesn't exist
            IF NOT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'unified_tenders' 
                AND column_name = 'value'
            ) THEN
                ALTER TABLE unified_tenders ADD COLUMN value NUMERIC;
                RAISE NOTICE 'Added value column';
            ELSE
                RAISE NOTICE 'value column already exists';
            END IF;
            
            -- Add the industry column if it doesn't exist
            IF NOT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'unified_tenders' 
                AND column_name = 'industry'
            ) THEN
                ALTER TABLE unified_tenders ADD COLUMN industry TEXT;
                RAISE NOTICE 'Added industry column';
            ELSE
                RAISE NOTICE 'industry column already exists';
            END IF;
            
            -- Add the cpv_codes column if it doesn't exist
            IF NOT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'unified_tenders' 
                AND column_name = 'cpv_codes'
            ) THEN
                ALTER TABLE unified_tenders ADD COLUMN cpv_codes TEXT[];
                RAISE NOTICE 'Added cpv_codes column';
            ELSE
                RAISE NOTICE 'cpv_codes column already exists';
            END IF;
            
            -- Add the sectors column if it doesn't exist
            IF NOT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'unified_tenders' 
                AND column_name = 'sectors'
            ) THEN
                ALTER TABLE unified_tenders ADD COLUMN sectors TEXT[];
                RAISE NOTICE 'Added sectors column';
            ELSE
                RAISE NOTICE 'sectors column already exists';
            END IF;
            
            -- Add the original_language column if it doesn't exist
            IF NOT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'unified_tenders' 
                AND column_name = 'original_language'
            ) THEN
                ALTER TABLE unified_tenders ADD COLUMN original_language TEXT;
                RAISE NOTICE 'Added original_language column';
            ELSE
                RAISE NOTICE 'original_language column already exists';
            END IF;
            
            -- Add the documents column if it doesn't exist
            IF NOT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'unified_tenders' 
                AND column_name = 'documents'
            ) THEN
                ALTER TABLE unified_tenders ADD COLUMN documents JSONB;
                RAISE NOTICE 'Added documents column';
            ELSE
                RAISE NOTICE 'documents column already exists';
            END IF;
            
            -- Add the keywords column if it doesn't exist
            IF NOT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'unified_tenders' 
                AND column_name = 'keywords'
            ) THEN
                ALTER TABLE unified_tenders ADD COLUMN keywords TEXT[];
                RAISE NOTICE 'Added keywords column';
            ELSE
                RAISE NOTICE 'keywords column already exists';
            END IF;
            
            -- Add the web_url column if it doesn't exist
            IF NOT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'unified_tenders' 
                AND column_name = 'web_url'
            ) THEN
                ALTER TABLE unified_tenders ADD COLUMN web_url TEXT;
                RAISE NOTICE 'Added web_url column';
            ELSE
                RAISE NOTICE 'web_url column already exists';
            END IF;
            
            -- Add the funding_source column if it doesn't exist
            IF NOT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'unified_tenders' 
                AND column_name = 'funding_source'
            ) THEN
                ALTER TABLE unified_tenders ADD COLUMN funding_source TEXT;
                RAISE NOTICE 'Added funding_source column';
            ELSE
                RAISE NOTICE 'funding_source column already exists';
            END IF;
            
            -- Add the data_source column if it doesn't exist
            IF NOT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'unified_tenders' 
                AND column_name = 'data_source'
            ) THEN
                ALTER TABLE unified_tenders ADD COLUMN data_source TEXT;
                RAISE NOTICE 'Added data_source column';
            ELSE
                RAISE NOTICE 'data_source column already exists';
            END IF;
            
            -- Add the data_quality_score column if it doesn't exist
            IF NOT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'unified_tenders' 
                AND column_name = 'data_quality_score'
            ) THEN
                ALTER TABLE unified_tenders ADD COLUMN data_quality_score NUMERIC;
                RAISE NOTICE 'Added data_quality_score column';
            ELSE
                RAISE NOTICE 'data_quality_score column already exists';
            END IF;
            
            -- Add the nuts_codes column if it doesn't exist
            IF NOT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'unified_tenders' 
                AND column_name = 'nuts_codes'
            ) THEN
                ALTER TABLE unified_tenders ADD COLUMN nuts_codes TEXT[];
                RAISE NOTICE 'Added nuts_codes column';
            ELSE
                RAISE NOTICE 'nuts_codes column already exists';
            END IF;
            
            -- Add the source_url column if it doesn't exist
            IF NOT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'unified_tenders' 
                AND column_name = 'source_url'
            ) THEN
                ALTER TABLE unified_tenders ADD COLUMN source_url TEXT;
                RAISE NOTICE 'Added source_url column';
            ELSE
                RAISE NOTICE 'source_url column already exists';
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