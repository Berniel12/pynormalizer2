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
        # Check for required environment variables
        required_vars = ['SUPABASE_DB_HOST', 'SUPABASE_DB_USER', 'SUPABASE_DB_PASSWORD', 'SUPABASE_DB_NAME']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars and not connection_params:
            missing_str = ', '.join(missing_vars)
            logger.warning(f"Missing required environment variables: {missing_str}")
            
        # Use provided connection parameters or get from environment
        self.connection_params = connection_params or {
            'host': os.environ.get('SUPABASE_DB_HOST', 'localhost'),
            'port': os.environ.get('SUPABASE_DB_PORT', '5432'),
            'user': os.environ.get('SUPABASE_DB_USER', 'postgres'),
            'password': os.environ.get('SUPABASE_DB_PASSWORD', ''),
            'dbname': os.environ.get('SUPABASE_DB_NAME', 'postgres')
        }
        
        # Log connection info (without sensitive data)
        logger.info(f"Database client initialized with host={self.connection_params['host']}, port={self.connection_params['port']}, user={self.connection_params['user']}, dbname={self.connection_params['dbname']}")
        
        self.conn = None
        
    def _get_connection(self):
        """Get a connection to the database."""
        if not self.conn or self.conn.closed:
            try:
                self.conn = psycopg2.connect(**self.connection_params)
                logger.info("Successfully connected to the database")
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
        id_type = 'unknown'
        
        if id_info and len(id_info) > 0:
            id_column = id_info[0]['column_name']
            id_type = id_info[0]['data_type'].lower()
            
        logger.info(f"Table {table} has ID column '{id_column}' of type '{id_type}'")
        
        # Construct the query
        base_query = f"""
            SELECT t.* 
            FROM {table} t
        """
        
        # Only add skip_normalized condition if requested
        if skip_normalized:
            # Always cast source_id to text for comparison, regardless of type
            # This ensures string vs. numeric comparisons work properly
            base_query += f"""
                WHERE NOT EXISTS (
                    SELECT 1 
                    FROM unified_tenders u 
                    WHERE u.source_table = %s 
                    AND u.source_id = t.{id_column}::text
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
        # Ensure source_id is always a string
        if 'source_id' in tender_data and tender_data['source_id'] is not None:
            tender_data['source_id'] = str(tender_data['source_id'])
        
        # Map the model fields to database column names
        field_mapping = {
            # Fields that exist in the DB with different names
            'publication_date': 'published_at',  # Reverse mapping to match our DB schema
            'deadline_date': 'deadline',  # Reverse mapping to match our DB schema
            'estimated_value': 'value',  # Reverse mapping to match our DB schema
            'url': 'source_url',  # Map URL fields appropriately
            'document_links': 'documents',  # Map document fields
            
            # Special handling fields
            'web_url': 'web_url', 
            
            # Fields to normalize
            'language': 'original_language'  # Legacy field mapping
        }
        
        # Create a new dictionary with the mapped fields
        mapped_data = {}
        for key, value in tender_data.items():
            # Skip None values to avoid overwriting existing data with NULL
            if value is None:
                continue
                
            # If the key is in our mapping and needs to be renamed
            if key in field_mapping:
                if field_mapping[key] is None:
                    # Skip fields mapped to None
                    continue
                else:
                    # Use the mapped field name
                    mapped_field = field_mapping[key]
                    mapped_data[mapped_field] = value
            else:
                # Use the original field name
                mapped_data[key] = value
        
        # Extract fields and values
        fields = []
        values = []
        placeholders = []
        
        # Handle JSONB fields - ensure they're JSON strings
        jsonb_fields = ['original_data', 'documents', 'contact']
        for field in jsonb_fields:
            if field in mapped_data:
                if isinstance(mapped_data[field], (dict, list)):
                    mapped_data[field] = json.dumps(mapped_data[field])
        
        # Handle array fields - ensure they're proper arrays
        array_fields = ['cpv_codes', 'nuts_codes', 'sectors', 'keywords']
        for field in array_fields:
            if field in mapped_data:
                # If it's a string, try to parse it as JSON
                if isinstance(mapped_data[field], str):
                    try:
                        # Try to parse as JSON
                        parsed = json.loads(mapped_data[field])
                        if isinstance(parsed, list):
                            mapped_data[field] = parsed
                    except:
                        # If not valid JSON, split by commas
                        mapped_data[field] = [item.strip() for item in mapped_data[field].split(',')]
                
                # Ensure it's a valid array
                if not isinstance(mapped_data[field], list):
                    mapped_data[field] = [str(mapped_data[field])]
        
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
                updated_at = CURRENT_TIMESTAMP
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