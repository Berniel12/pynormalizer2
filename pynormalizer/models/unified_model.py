from pydantic import BaseModel, Field
from typing import Optional, Any, List
from datetime import datetime

class UnifiedTender(BaseModel):
    id: Optional[str] = Field(None, description="UUID from DB")
    title: str
    description: Optional[str] = None
    tender_type: Optional[str] = None
    status: Optional[str] = None
    publication_date: Optional[datetime] = None
    deadline_date: Optional[datetime] = None
    country: Optional[str] = None
    city: Optional[str] = None
    organization_name: Optional[str] = None
    organization_id: Optional[str] = None
    buyer: Optional[str] = None
    project_name: Optional[str] = None
    project_id: Optional[str] = None
    project_number: Optional[str] = None
    sector: Optional[str] = None
    estimated_value: Optional[float] = None
    currency: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_address: Optional[str] = None
    url: Optional[str] = None
    document_links: Optional[Any] = None
    language: Optional[str] = None
    notice_id: Optional[str] = None
    reference_number: Optional[str] = None
    procurement_method: Optional[str] = None
    original_data: Optional[Any] = None
    source_table: str
    source_id: str
    processed_at: Optional[datetime] = None
    normalized_by: Optional[str] = None
    title_english: Optional[str] = None
    description_english: Optional[str] = None
    organization_name_english: Optional[str] = None
    buyer_english: Optional[str] = None
    project_name_english: Optional[str] = None
    normalized_at: Optional[datetime] = None
    fallback_reason: Optional[str] = None
    normalized_method: Optional[str] = None
    processing_time_ms: Optional[int] = None
    tags: Optional[List[str]] = None 