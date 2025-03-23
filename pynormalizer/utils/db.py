import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Any, Optional
from pynormalizer.models.unified_model import UnifiedTender
import json
from datetime import datetime
import uuid
import logging
import traceback
import sys

# Configure logger
logger = logging.getLogger(__name__)

# Try to import supabase with better error handling
SUPABASE_AVAILABLE = False
SUPABASE_ERROR = None
try:
    # First try the standard import
    try:
        from supabase import create_client, Client
        SUPABASE_AVAILABLE = True
        logger.info("✅ Successfully imported supabase using standard import")
    except ImportError as e:
        # If standard import fails, try alternatives
        try:
            sys.path.append(os.path.join(os.getcwd(), 'site-packages'))
            from supabase import create_client, Client
            SUPABASE_AVAILABLE = True
            logger.info("✅ Successfully imported supabase from site-packages")
        except ImportError as e2:
            SUPABASE_ERROR = f"Standard import error: {e}, Alternative import error: {e2}"
            logger.error(f"❌ Failed to import supabase: {SUPABASE_ERROR}")
            logger.error(f"Python path: {sys.path}")
            logger.error(f"Traceback: {traceback.format_exc()}")
except Exception as e:
    SUPABASE_ERROR = str(e)
    logger.error(f"❌ Unexpected error importing supabase: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def get_supabase_client() -> Optional["Client"]:
    """
    Get a Supabase client using environment variables.
    
    Returns:
        Supabase client or None if not available
    """
    if not SUPABASE_AVAILABLE:
        error_details = f": {SUPABASE_ERROR}" if SUPABASE_ERROR else ""
        raise ImportError(
            f"Supabase client not available{error_details}. "
            "Please install with: pip install supabase"
        )
    
    # Get environment variables
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError(
            "Supabase URL and key must be set as environment variables: "
            "SUPABASE_URL and SUPABASE_KEY"
        )
    
    try:
        # Create client
        return create_client(supabase_url, supabase_key)
    except Exception as e:
        logger.error(f"❌ Failed to create Supabase client: {e}")
        logger.error(f"Supabase URL: {supabase_url[:10]}...")  # Show only part of the URL for security
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def get_connection(db_config: Dict[str, Any]):
    """
    Get a connection to the database.
    
    Args:
        db_config: Database configuration
        
    Returns:
        Database connection or Supabase client
    """
    # Check if using Supabase (environment variables take precedence)
    if os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_KEY"):
        return get_supabase_client()
    
    # Otherwise use direct PostgreSQL connection
    conn = psycopg2.connect(
        dbname=db_config["dbname"],
        user=db_config["user"],
        password=db_config["password"],
        host=db_config["host"],
        port=db_config.get("port", 5432)
    )
    conn.autocommit = True
    return conn

def fetch_rows(conn, table_name: str) -> List[Dict[str, Any]]:
    """
    Fetch all rows from a table.
    
    Args:
        conn: Database connection or Supabase client
        table_name: Name of the table
        
    Returns:
        List of rows as dictionaries
    """
    # Check if using Supabase
    if SUPABASE_AVAILABLE and isinstance(conn, Client):
        response = conn.table(table_name).select("*").execute()
        if hasattr(response, 'data'):
            return response.data
        return response
    
    # Otherwise use direct PostgreSQL connection
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(f"SELECT * FROM {table_name};")
        return cur.fetchall()

def fetch_unnormalized_rows(conn, table_name: str, skip_normalized: bool = True, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Fetch rows from a source table that haven't been normalized yet.
    
    Args:
        conn: Database connection or Supabase client
        table_name: Name of the source table
        skip_normalized: Whether to skip already normalized records
        limit: Maximum number of rows to fetch
        
    Returns:
        List of unnormalized rows
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Check if using Supabase
        if SUPABASE_AVAILABLE and isinstance(conn, Client):
            if skip_normalized:
                # First get IDs of already normalized records for this source table
                normalized_response = conn.table("unified_tenders") \
                    .select("source_id") \
                    .eq("source_table", table_name) \
                    .not_.is_("normalized_at", "null") \
                    .execute()
                
                if hasattr(normalized_response, 'data'):
                    normalized_ids = [str(row["source_id"]) for row in normalized_response.data]
                else:
                    normalized_ids = [str(row["source_id"]) for row in normalized_response]
                
                logger.info(f"Found {len(normalized_ids)} already normalized records for {table_name}")
                
                if normalized_ids:
                    # Fetch unnormalized records using not.in_
                    query = conn.table(table_name).select("*")
                    if limit:
                        query = query.limit(limit)
                    
                    # Split into chunks of 100 for the .not_.in_ filter
                    # as Supabase has limits on array size in filters
                    chunk_size = 100
                    all_results = []
                    
                    for i in range(0, len(normalized_ids), chunk_size):
                        chunk = normalized_ids[i:i + chunk_size]
                        chunk_response = query.not_.in_("id", chunk).execute()
                        if hasattr(chunk_response, 'data'):
                            all_results.extend(chunk_response.data)
                        else:
                            all_results.extend(chunk_response)
                    
                    logger.info(f"Fetched {len(all_results)} unnormalized records from {table_name}")
                    return all_results
            
            # If no normalized records found or skip_normalized is False, fetch all records
            query = conn.table(table_name).select("*")
            if limit:
                query = query.limit(limit)
            
            response = query.execute()
            if hasattr(response, 'data'):
                result = response.data
            else:
                result = response
            
            logger.info(f"Fetched {len(result)} records from {table_name}")
            return result
        
        # Otherwise use direct PostgreSQL connection
        # First get IDs of already normalized records for this source table
        normalized_ids = []
        if skip_normalized:
            query = """
                SELECT source_id 
                FROM unified_tenders 
                WHERE source_table = %s 
                AND normalized_at IS NOT NULL
            """
            with conn.cursor() as cur:
                cur.execute(query, (table_name,))
                normalized_ids = [str(row[0]) for row in cur.fetchall()]
            
            logger.info(f"Found {len(normalized_ids)} already normalized records for {table_name}")
            
            if normalized_ids:
                # Fetch unnormalized records
                query = f"""
                    SELECT * FROM {table_name} 
                    WHERE CAST(id AS TEXT) NOT IN %s
                    {f'LIMIT {limit}' if limit else ''}
                """
                with conn.cursor() as cur:
                    cur.execute(query, (tuple(normalized_ids),))
                    rows = cur.fetchall()
                    
                    # Convert to list of dicts
                    columns = [desc[0] for desc in cur.description]
                    result = [dict(zip(columns, row)) for row in rows]
                    
                    logger.info(f"Fetched {len(result)} unnormalized records from {table_name}")
                    return result
        
        # If no normalized records found or skip_normalized is False, fetch all records
        query = f"""
            SELECT * FROM {table_name}
            {f'LIMIT {limit}' if limit else ''}
        """
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            
            # Convert to list of dicts
            columns = [desc[0] for desc in cur.description]
            result = [dict(zip(columns, row)) for row in rows]
            
            logger.info(f"Fetched {len(result)} records from {table_name}")
            return result
            
    except Exception as e:
        logger.error(f"Error fetching unnormalized rows from {table_name}: {e}")
        raise

def ensure_unique_constraint(conn):
    """
    Ensure the unified_tenders table has a unique constraint on (source_table, source_id).
    
    Args:
        conn: Database connection or Supabase client
    """
    # Check if using Supabase
    if SUPABASE_AVAILABLE and isinstance(conn, Client):
        # For Supabase, we'll trust that the constraint exists
        # We can't create it through the API
        # You should set this up in the Supabase dashboard or via migrations
        print("Using Supabase: please ensure the unique constraint exists on (source_table, source_id)")
        return
    
    # Otherwise use direct PostgreSQL connection
    with conn.cursor() as cur:
        # Check if the constraint already exists
        cur.execute("""
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'unique_source'
        """)
        exists = cur.fetchone()
        
        if not exists:
            # Add the constraint
            cur.execute("""
            ALTER TABLE unified_tenders
            ADD CONSTRAINT unique_source UNIQUE (source_table, source_id);
            """)
            print("Added unique constraint on (source_table, source_id)")

def save_unified_tender(tender):
    """Save a unified tender to the database."""
    try:
        client = get_supabase_client()
        
        # If client is None, log error and return
        if not client:
            logger.error("Could not get Supabase client")
            return False
            
        # Check if tender already exists
        existingIds = client.table("unified_tenders") \
            .select("id") \
            .eq("source_table", tender.source_table) \
            .eq("source_id", tender.source_id) \
            .execute()
            
        record_to_save = tender.dict()
        
        # Handle the documents column issue - remove if it doesn't exist in the database schema
        # This is a temporary fix until the database schema is updated
        if 'documents' in record_to_save:
            document_links = record_to_save.pop('documents')
            # If document_links exists and we have a structure, add the URLs to document_links
            if document_links and isinstance(document_links, list) and 'document_links' in record_to_save:
                if not record_to_save['document_links']:
                    record_to_save['document_links'] = []
                    
                # Add document URLs to document_links if they're not already there
                doc_urls = set()
                if isinstance(record_to_save['document_links'], list):
                    for link in record_to_save['document_links']:
                        if isinstance(link, dict) and 'url' in link:
                            doc_urls.add(link['url'])
                
                # Add new document URLs
                for doc in document_links:
                    if isinstance(doc, dict) and 'url' in doc and doc['url'] not in doc_urls:
                        record_to_save['document_links'].append(doc)
        
        # Convert any datetime objects to strings for serialization
        for key, value in record_to_save.items():
            if isinstance(value, datetime):
                record_to_save[key] = value.isoformat()
                
        # If tender exists, update it, otherwise insert it
        if existingIds.data and len(existingIds.data) > 0:
            existing_id = existingIds.data[0]['id']
            
            response = client.table("unified_tenders") \
                .update(record_to_save) \
                .eq("id", existing_id) \
                .execute()
                
            if response.data:
                logger.info(f"Updated unified tender {existing_id} in the database")
                return True
            else:
                logger.error(f"Error updating unified tender {existing_id}: {response}")
                return False
        else:
            response = client.table("unified_tenders") \
                .insert(record_to_save) \
                .execute()
                
            if response.data:
                logger.info(f"Inserted unified tender {tender.id} into the database")
                return True
            else:
                logger.error(f"Error inserting unified tender: {response}")
                return False
    
    except Exception as e:
        logger.error(f"Error saving unified tender to database: {str(e)}")
        return False 