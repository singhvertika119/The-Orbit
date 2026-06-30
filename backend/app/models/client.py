from pydantic import BaseModel, Field
from typing import Optional

class ClientCreate(BaseModel):
    name: str = Field(..., min_length=1, description="The name of the client")
    email: Optional[str] = Field(None, description="Optional email address")
    phone: Optional[str] = Field(None, description="Optional phone number")
    platform: Optional[str] = Field(None, description="Platform source (e.g. upwork, direct, referral)")
    company: Optional[str] = Field(None, description="Client company or organization")
    notes: Optional[str] = Field(None, description="Internal notes about the client")

class ClientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    email: Optional[str] = None
    phone: Optional[str] = None
    platform: Optional[str] = None
    company: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = Field(None, description="Client status (active or inactive)")
