from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

class LeadForm(BaseModel):
    """Lead form submission model"""
    name: str = Field(..., min_length=1, max_length=100, description="Customer name")
    company: str = Field(..., min_length=1, max_length=200, description="Organization name")
    email: str = Field(default="", max_length=100, description="Email address")
    phone: Optional[str] = Field(default="", max_length=20, description="Phone number")
    
    requirement_type: str = Field(default="General Inquiry", description="Requirement types")
    
    customer_type: str = Field(default="Other", description="Type of customer")
    other_customer_type: Optional[str] = Field(default="", max_length=100, description="Custom customer type")
    
    message: Optional[str] = Field(default="", max_length=1000, description="Additional details")
    source: str = Field(default="web_form", description="Source of the lead")
    image_url: Optional[str] = Field(None, description="URL or base64 of captured image")
    
    @field_validator('customer_type')
    @classmethod
    def validate_customer_type(cls, v: str) -> str:
        valid_types = ["End_Customer", "Distributor", "Manufacturer", "Other"]
        if v not in valid_types:
            return "Other"
        return v
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not v or v.strip() == '':
            return ''
        if '@' not in v or '.' not in v:
            return ''
        return v

class LeadResponse(BaseModel):
    id: int
    message: str
    status: str

class LeadUpdate(BaseModel):
    status: str = Field(..., description="Lead status: new, contacted, converted, closed")

class LeadsFilter(BaseModel):
    lead_type: Optional[str] = None
    status: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None
    limit: int = 100
    offset: int = 0