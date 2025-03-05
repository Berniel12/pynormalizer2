from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date, datetime

class ADBTender(BaseModel):
    id: int
    type: str
    country: str
    notice_title: str
    project_name: str
    project_number: str
    publication_date: date
    due_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    db_reference: Optional[str] = None
    sector: Optional[str] = None
    loan_number: Optional[str] = None
    contractor: Optional[str] = None
    contract_amount: Optional[str] = None
    project_id: Optional[str] = None
    borrower_bid_no: Optional[str] = None
    description: Optional[str] = None
    pdf_url: Optional[str] = None
    pdf_content: Optional[str] = None


class AFDTender(BaseModel):
    id: int
    notice_id: str
    notice_title: Optional[str] = None
    country: Optional[str] = None
    city_locality: Optional[str] = None
    publication_date: Optional[str] = None
    deadline: Optional[str] = None
    agency: Optional[str] = None
    buyer: Optional[str] = None
    original_language: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    services: Optional[List[str]] = None
    url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    notice_content: str  # "NO CONTENT" default in DB, but never null


class AFDBTender(BaseModel):
    id: int
    title: Optional[str] = None
    tender_type: Optional[str] = None
    country: Optional[str] = None
    publication_date: Optional[str] = None
    description: Optional[str] = None
    url: str
    document_links: Optional[Dict[str, Any]] = None
    created_at: datetime
    closing_date: Optional[date] = None
    status: Optional[str] = None
    sector: Optional[str] = None
    project_id: Optional[str] = None
    estimated_value: Optional[float] = None
    currency: Optional[str] = None
    project_name: Optional[str] = None
    is_multinational: Optional[bool] = None


class AIIBTender(BaseModel):
    id: int
    date: Optional[str] = None
    member: Optional[str] = None
    project_notice: Optional[str] = None
    sector: Optional[str] = None
    type: Optional[str] = None
    pdf_content: Optional[str] = None


class IADBTender(BaseModel):
    project_number: str
    type: Optional[str] = None
    country: Optional[str] = None
    notice_title: Optional[str] = None
    project_name: Optional[str] = None
    publication_date: Optional[date] = None
    pue_date: Optional[date] = None
    url: Optional[str] = None
    url_pdf: Optional[str] = None


class SamGovTender(BaseModel):
    opportunity_id: str
    solicitation_number: Optional[str] = None
    opportunity_title: Optional[str] = None
    opportunity_type: Optional[str] = None
    publish_date: Optional[datetime] = None
    response_date: Optional[datetime] = None
    description: Optional[str] = None
    opportunity_status: Optional[str] = None
    classification_code: Optional[str] = None
    naics_code: Optional[str] = None
    set_aside: Optional[str] = None
    place_of_performance: Optional[Dict] = None
    organization_id: Optional[str] = None
    opportunity_created_date: Optional[datetime] = None
    opportunity_modified_date: Optional[datetime] = None
    org_key: int
    contacts: Optional[Dict] = None


class TEDEuTender(BaseModel):
    id: int
    publication_number: str
    change_notice_version_identifier: Optional[str] = None
    procedure_type: Optional[str] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    publication_date: Optional[date] = None
    deadline_date: Optional[date] = None
    language: Optional[str] = None
    organisation_id: Optional[str] = None
    organisation_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_url: Optional[str] = None
    notice_status: Optional[str] = None
    notice_type: Optional[str] = None
    notice_identifier: Optional[str] = None
    modification_date: Optional[datetime] = None
    document_id: Optional[str] = None
    lots: Optional[Any] = None
    is_corrigendum: Optional[bool] = None
    additional_information: Optional[str] = None
    links: Optional[Any] = None


class UNGMTender(BaseModel):
    id: int
    title: str
    status: Optional[str] = None
    reference: Optional[str] = None
    beneficiary_countries: Optional[str] = None
    registration_level: Optional[str] = None
    published_on: Optional[str] = None
    deadline_on: Optional[str] = None
    description: Optional[str] = None
    documents: Optional[Dict] = None
    contacts: Optional[Dict] = None
    sustainability: Optional[Dict] = None
    links: Optional[Dict] = None
    unspscs: Optional[Dict] = None
    revisions: Optional[Dict] = None
    countries: Optional[Dict] = None
    created_at: datetime
    updated_at: datetime


class WBTender(BaseModel):
    id: str
    title: Optional[str] = None
    country: Optional[str] = None
    publication_date: Optional[datetime] = None
    deadline: Optional[datetime] = None
    tender_type: Optional[str] = None
    description: Optional[str] = None
    document_links: Optional[dict] = None
    url: Optional[str] = None
    bid_reference_no: Optional[str] = None
    contact_email: Optional[str] = None
    contact_organization: Optional[str] = None
    notice_type: Optional[str] = None
    notice_status: Optional[str] = None
    submission_deadline_time: Optional[str] = None
    project_ctry_name: Optional[str] = None
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    procurement_group: Optional[str] = None
    procurement_method_code: Optional[str] = None
    procurement_method: Optional[str] = None
    contact_address: Optional[str] = None
    contact_ctry_name: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    submission_date: Optional[datetime] = None
    notice_text: Optional[str] = None
    procurement_method_name: Optional[str] = None 