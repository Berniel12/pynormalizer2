import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Any, Optional
from pynormalizer.models.unified_model import UnifiedTender
import json
from datetime import datetime
import uuid

# Try to import supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

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
        raise ImportError(
            "Supabase client not available. Please install with: pip install supabase"
        )
    
    # Get environment variables
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError(
            "Supabase URL and key must be set as environment variables: "
            "SUPABASE_URL and SUPABASE_KEY"
        )
    
    # Create client
    return create_client(supabase_url, supabase_key)

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