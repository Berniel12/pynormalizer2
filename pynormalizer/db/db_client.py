from typing import List, Dict, Any, Optional, Tuple
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from pynormalizer.utils.logger import logger

class DBClient:
    """Client for interacting with the database."""
    
    def __init__(self, connection_params=None):
        """Initialize the DB client with connection parameters."""
        # Use provided connection parameters or get from environment
        self.connection_params = connection_params or {
            'host': os.environ.get('SUPABASE_DB_HOST'),
            'port': os.environ.get('SUPABASE_DB_PORT', '5432'),
            'user': os.environ.get('SUPABASE_DB_USER'),
            'password': os.environ.get('SUPABASE_DB_PASSWORD'),
            'dbname': os.environ.get('SUPABASE_DB_NAME')
        }
        self.conn = None
        
    def _get_connection(self):
        """Get a connection to the database."""
        if not self.conn or self.conn.closed:
            try:
                self.conn = psycopg2.connect(**self.connection_params)
            except Exception as e:
                logger.error(f"Error connecting to database: {str(e)}")
                raise
        return self.conn
    
    def _execute_query(self, query, params=None, fetch=True):
        """Execute a query and return the results."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params or {})
                if fetch:
                    return cursor.fetchall()
                conn.commit()
                return None
        except Exception as e:
            conn.rollback()
            logger.error(f"Query execution error: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
    
    def fetch_all_rows(self, table: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """Fetch all rows from a table with a limit."""
        query = f"""
            SELECT * FROM {table}
            LIMIT %s
        """
        return self._execute_query(query, (limit,))
    
    def fetch_unnormalized_rows(
        self, 
        table: str, 
        limit: int = 1000, 
        skip_normalized: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Fetch rows from a table that haven't been normalized yet.
        
        Args:
            table: The table to fetch rows from
            limit: Maximum number of rows to fetch
            skip_normalized: Whether to skip already normalized rows
            
        Returns:
            List of rows as dictionaries
        """
        # Get ID column name and type from table
        schema_query = f"""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = %s AND column_name = 'id'
        """
        id_info = self._execute_query(schema_query, (table,))
        
        # Set default ID column and type if not found
        id_column = 'id'
        id_type = 'uuid'
        
        if id_info and len(id_info) > 0:
            id_column = id_info[0]['column_name']
            id_type = id_info[0]['data_type']
        
        # Construct the query
        base_query = f"""
            SELECT t.* 
            FROM {table} t
        """
        
        # Only add skip_normalized condition if requested
        if skip_normalized:
            # Handle potential type conversion between source table and unified_tenders
            type_cast = ''
            if id_type.lower() in ('integer', 'bigint', 'numeric'):
                # Convert numeric IDs to text for comparison
                type_cast = '::text'
            
            # Add condition to exclude normalized rows
            base_query += f"""
                WHERE NOT EXISTS (
                    SELECT 1 
                    FROM unified_tenders u 
                    WHERE u.source_table = %s 
                    AND u.source_id = t.{id_column}{type_cast}
                )
            """
            params = (table, limit)
        else:
            params = (limit,)
        
        # Add limit
        base_query += """
            LIMIT %s
        """
        
        try:
            rows = self._execute_query(base_query, params)
            logger.info(f"Fetched {len(rows)} unnormalized rows from {table}")
            return rows
        except Exception as e:
            logger.error(f"Error fetching unnormalized rows from {table}: {str(e)}")
            # Fallback to simpler query if the above fails
            fallback_query = f"""
                SELECT * FROM {table}
                LIMIT %s
            """
            logger.info(f"Using fallback query for {table}")
            return self._execute_query(fallback_query, (limit,))
    
    def save_normalized_tender(self, tender_data: Dict[str, Any]) -> bool:
        """
        Save a normalized tender to the unified_tenders table.
        
        Args:
            tender_data: Dictionary with tender data
            
        Returns:
            True if successful, False otherwise
        """
        # Map the model fields to database column names
        field_mapping = {
            'published_at': 'publication_date',
            'deadline': 'deadline_date',
            'value': 'estimated_value',
            'web_url': 'url',
            'original_language': 'language',
            'normalized_method': None,  # Skip this field as it doesn't exist in the DB
            'category': None,  # Skip this field as it doesn't exist in the DB
            'industry': None,  # Skip this field as it doesn't exist in the DB
            'cpv_codes': None,  # Skip this field as it doesn't exist in the DB
            'sectors': None,  # Skip this field as it doesn't exist in the DB
            'data_source': None,  # Skip this field as it doesn't exist in the DB
            'data_quality_score': None,  # Skip this field as it doesn't exist in the DB
            'nuts_codes': None,  # Skip this field as it doesn't exist in the DB
            'documents': 'document_links',  # Map to document_links
        }
        
        # Create a new dictionary with the mapped fields
        mapped_data = {}
        for key, value in tender_data.items():
            # Skip None values to avoid overwriting existing data with NULL
            if value is None:
                continue
                
            # Map the field if needed
            db_field = field_mapping.get(key)
            
            # If this field should be skipped (doesn't exist in DB)
            if db_field is None and key in field_mapping:
                continue
                
            # Use the mapped field name or the original name
            field_name = db_field if db_field else key
            
            # Add to the mapped data
            mapped_data[field_name] = value
        
        # Extract fields and values
        fields = []
        values = []
        placeholders = []
        
        # Handle original_data field - ensure it's JSON
        if 'original_data' in mapped_data and isinstance(mapped_data['original_data'], dict):
            mapped_data['original_data'] = json.dumps(mapped_data['original_data'])
            
        # Handle document_links field - ensure it's JSON
        if 'document_links' in mapped_data and isinstance(mapped_data['document_links'], list):
            mapped_data['document_links'] = json.dumps(mapped_data['document_links'])
        
        # Process each field
        for i, (key, value) in enumerate(mapped_data.items()):
            fields.append(key)
            values.append(value)
            placeholders.append(f"%s")
        
        # Construct query
        query = f"""
            INSERT INTO unified_tenders ({', '.join(fields)})
            VALUES ({', '.join(placeholders)})
            ON CONFLICT (source_table, source_id) 
            DO UPDATE SET 
                {', '.join([f"{field} = EXCLUDED.{field}" for field in fields if field not in ['source_table', 'source_id']])},
                processed_at = CURRENT_TIMESTAMP
        """
        
        try:
            self._execute_query(query, values, fetch=False)
            return True
        except Exception as e:
            logger.error(f"Error saving normalized tender: {str(e)}")
            return False
    
    def close(self):
        """Close the database connection."""
        if self.conn and not self.conn.closed:
            self.conn.close() 