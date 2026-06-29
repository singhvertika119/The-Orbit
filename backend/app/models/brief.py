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
