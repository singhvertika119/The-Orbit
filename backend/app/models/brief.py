from pydantic import BaseModel, Field
from typing import List

class BriefParseRequest(BaseModel):
    brief_text: str = Field(
        ..., 
        min_length=50, 
        description="The raw unstructured client brief message (minimum 50 characters)."
    )

class BriefScopeRequest(BaseModel):
    brief_summary: str = Field(
        ..., 
        description="Summary description of the brief details."
    )
    deliverables: List[str] = Field(
        ..., 
        description="List of project deliverables extracted from the brief."
    )
    project_type: str = Field(
        ..., 
        description="Identified project category (e.g. Website development)."
    )

class BriefProposalRequest(BaseModel):
    project_title: str = Field(..., description="Title of the project")
    client_name: str = Field(..., description="Name of the client")
    scope_breakdown: List[str] = Field(..., description="Task or phase breakdown for the project")
    timeline_days: int = Field(..., description="Estimated timeline in calendar days")
    price_inr: int = Field(..., description="Price in INR")
    deliverables: List[str] = Field(..., description="Project deliverables list")
    project_id: str = Field(None, description="Optional UUID of the project if already saved in database")

