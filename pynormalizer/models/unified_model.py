from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, validator, Field
from datetime import datetime, date
from enum import Enum
import json
import re

class TenderStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    AWARDED = "awarded"
    CANCELLED = "cancelled"
    DRAFT = "draft"
    PENDING = "pending"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    REQUIRED = "required"
    ALLOWED = "allowed"

class ProcurementMethod(str, Enum):
    OPEN = "open"
    SELECTIVE = "selective"
    LIMITED = "limited"
    DIRECT = "direct"
    SOLE_SOURCE = "sole-source"
    NEGOTIATED = "negotiated"
    COMPETITIVE = "competitive"
    FRAMEWORK = "framework"
    TWO_STAGE = "two-stage"
    QUALIFICATION = "qualification"
    QUALITY_COST = "quality-cost"
    FIXED_BUDGET = "fixed-budget"
    LOWEST_PRICE = "lowest-price"
    OTH_SINGLE = "oth-single"
    NEG_W_CALL = "neg-w-call"
    RESTRICTED = "restricted"

class UnifiedTender(BaseModel):
    """
    Unified tender model that normalizes data from various sources.
    """
    # Core fields
    id: Optional[str] = None
    title: Optional[str] = None
    title_english: Optional[str] = None
    description: Optional[str] = None
    description_english: Optional[str] = None
    source_id: Optional[str] = None
    source_url: Optional[str] = None
    source_table: Optional[str] = None
    
    # Dates
    published_at: Optional[Union[datetime, str]] = None
    updated_at: Optional[Union[datetime, str]] = None
    deadline: Optional[Union[datetime, str]] = None
    normalized_at: Optional[Union[datetime, str]] = None
    created_at: Optional[Union[datetime, str]] = None
    end_date: Optional[Union[datetime, str]] = None
    
    # Organizational info
    organization_name: Optional[str] = None
    organization_id: Optional[str] = None
    buyer: Optional[str] = None
    project_name: Optional[str] = None
    project_id: Optional[str] = None
    project_number: Optional[str] = None
    contact: Optional[Union[str, Dict[str, Any]]] = None
    
    # Location info
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    nuts_codes: Optional[List[str]] = None
    
    # Financial info
    financial_info: Optional[str] = None
    value: Optional[float] = None
    currency: Optional[str] = None
    
    # Categorization
    category: Optional[str] = None
    industry: Optional[str] = None
    cpv_codes: Optional[List[str]] = None
    sectors: Optional[List[str]] = None
    
    # Status info
    status: Optional[TenderStatus] = None
    procurement_method: Optional[ProcurementMethod] = None
    tender_type: Optional[str] = None
    
    # Additional data
    original_language: Optional[str] = None
    language: Optional[str] = None  # For backward compatibility
    original_data: Optional[Union[str, Dict[str, Any]]] = None
    documents: Optional[List[Dict[str, Any]]] = None
    keywords: Optional[List[str]] = None
    
    # Additional standardized fields
    web_url: Optional[str] = None
    funding_source: Optional[str] = None
    data_source: Optional[str] = None
    data_quality_score: Optional[float] = None

    # Processing info
    normalized_by: Optional[str] = None
    normalized_method: Optional[str] = None
    processed_at: Optional[Union[datetime, str]] = None
    processing_time_ms: Optional[int] = None
    fallback_reason: Optional[str] = None

    class Config:
        use_enum_values = True
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

    @validator('published_at', 'updated_at', 'deadline', 'normalized_at', 'created_at', 'end_date', 'processed_at', pre=True)
    def parse_datetime(cls, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            # For date strings with just the date, parse and convert to datetime
            if re.match(r'^\d{4}-\d{2}-\d{2}$', value):
                dt = datetime.strptime(value, '%Y-%m-%d')
                return dt
            # Try parsing as ISO format
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                # Try parsing other common formats
                try:
                    return datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
                except (ValueError, TypeError):
                    try:
                        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                    except (ValueError, TypeError):
                        # As a last resort, return the string
                        return value
        return value

    @validator('original_data', pre=True)
    def ensure_json_string(cls, value):
        """Ensure that original_data is stored as a JSON string."""
        if value is None:
            return None
        if isinstance(value, dict):
            return json.dumps(value)
        if isinstance(value, str):
            try:
                # Validate it's valid JSON by parsing and re-serializing
                return json.dumps(json.loads(value))
            except json.JSONDecodeError:
                # If it's not valid JSON, store it as-is
                return value
        return json.dumps(value) 