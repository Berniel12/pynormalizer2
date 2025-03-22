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
                    WHERE id::text NOT IN %s
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

def upsert_unified_tender(conn, tender: UnifiedTender):
    """
    Insert or update a unified tender record.
    
    Args:
        conn: Database connection or Supabase client
        tender: UnifiedTender instance
    """
    # Convert Pydantic model to dict
    data = tender.model_dump()
    
    # Set normalized_at if not already set
    if not data.get("normalized_at"):
        from datetime import datetime
        data["normalized_at"] = datetime.utcnow()
    
    # Check if using Supabase
    if SUPABASE_AVAILABLE and isinstance(conn, Client):
        # Remove fields that don't exist in the database schema
        if 'tags' in data:
            del data['tags']
        
        # Generate a UUID for the id field if it's not set
        if not data.get("id"):
            data["id"] = str(uuid.uuid4())
            
        # Convert datetime objects to ISO format strings for JSON serialization
        data_json_safe = json.loads(json.dumps(data, cls=DateTimeEncoder))
        
        # First check if a record with this source_table and source_id already exists
        source_table = data.get("source_table")
        source_id = data.get("source_id")
        
        if source_table and source_id:
            # Query to check if the record already exists
            existing_record = conn.table("unified_tenders").select("id").eq("source_table", source_table).eq("source_id", source_id).execute()
            
            if existing_record and existing_record.data and len(existing_record.data) > 0:
                # Record exists, update it
                record_id = existing_record.data[0]["id"]
                response = conn.table("unified_tenders").update(data_json_safe).eq("id", record_id).execute()
            else:
                # Record doesn't exist, insert a new one
                response = conn.table("unified_tenders").insert(data_json_safe).execute()
        else:
            # Missing source_table or source_id, just insert
            response = conn.table("unified_tenders").insert(data_json_safe).execute()
        
        return response
    
    # Otherwise use direct PostgreSQL connection
    # We'll explicitly list all columns used in insert
    insert_sql = """
    INSERT INTO unified_tenders (
        title,
        description,
        tender_type,
        status,
        publication_date,
        deadline_date,
        country,
        city,
        organization_name,
        organization_id,
        buyer,
        project_name,
        project_id,
        project_number,
        sector,
        estimated_value,
        currency,
        contact_name,
        contact_email,
        contact_phone,
        contact_address,
        url,
        document_links,
        language,
        notice_id,
        reference_number,
        procurement_method,
        original_data,
        source_table,
        source_id,
        normalized_by,
        title_english,
        description_english,
        organization_name_english,
        buyer_english,
        project_name_english,
        normalized_at,
        fallback_reason,
        normalized_method,
        processing_time_ms
    )
    VALUES (
        %(title)s,
        %(description)s,
        %(tender_type)s,
        %(status)s,
        %(publication_date)s,
        %(deadline_date)s,
        %(country)s,
        %(city)s,
        %(organization_name)s,
        %(organization_id)s,
        %(buyer)s,
        %(project_name)s,
        %(project_id)s,
        %(project_number)s,
        %(sector)s,
        %(estimated_value)s,
        %(currency)s,
        %(contact_name)s,
        %(contact_email)s,
        %(contact_phone)s,
        %(contact_address)s,
        %(url)s,
        %(document_links)s,
        %(language)s,
        %(notice_id)s,
        %(reference_number)s,
        %(procurement_method)s,
        %(original_data)s,
        %(source_table)s,
        %(source_id)s,
        %(normalized_by)s,
        %(title_english)s,
        %(description_english)s,
        %(organization_name_english)s,
        %(buyer_english)s,
        %(project_name_english)s,
        %(normalized_at)s,
        %(fallback_reason)s,
        %(normalized_method)s,
        %(processing_time_ms)s
    )
    ON CONFLICT (source_table, source_id)
    DO UPDATE SET
        title = EXCLUDED.title,
        description = EXCLUDED.description,
        tender_type = EXCLUDED.tender_type,
        status = EXCLUDED.status,
        publication_date = EXCLUDED.publication_date,
        deadline_date = EXCLUDED.deadline_date,
        country = EXCLUDED.country,
        city = EXCLUDED.city,
        organization_name = EXCLUDED.organization_name,
        organization_id = EXCLUDED.organization_id,
        buyer = EXCLUDED.buyer,
        project_name = EXCLUDED.project_name,
        project_id = EXCLUDED.project_id,
        project_number = EXCLUDED.project_number,
        sector = EXCLUDED.sector,
        estimated_value = EXCLUDED.estimated_value,
        currency = EXCLUDED.currency,
        contact_name = EXCLUDED.contact_name,
        contact_email = EXCLUDED.contact_email,
        contact_phone = EXCLUDED.contact_phone,
        contact_address = EXCLUDED.contact_address,
        url = EXCLUDED.url,
        document_links = EXCLUDED.document_links,
        language = EXCLUDED.language,
        notice_id = EXCLUDED.notice_id,
        reference_number = EXCLUDED.reference_number,
        procurement_method = EXCLUDED.procurement_method,
        original_data = EXCLUDED.original_data,
        normalized_by = EXCLUDED.normalized_by,
        title_english = EXCLUDED.title_english,
        description_english = EXCLUDED.description_english,
        organization_name_english = EXCLUDED.organization_name_english,
        buyer_english = EXCLUDED.buyer_english,
        project_name_english = EXCLUDED.project_name_english,
        normalized_at = EXCLUDED.normalized_at,
        fallback_reason = EXCLUDED.fallback_reason,
        normalized_method = EXCLUDED.normalized_method,
        processing_time_ms = EXCLUDED.processing_time_ms
    ;
    """

    with conn.cursor() as cur:
        cur.execute(insert_sql, data) 