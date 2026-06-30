from pydantic import BaseModel, Field
from typing import Optional, List, Any

class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Title of the project")
    client_id: Optional[str] = Field(None, description="The client UUID associated with the project")
    status: Optional[str] = Field("scoping", description="Project status: scoping, active, complete, inactive")
    brief_text: Optional[str] = Field(None, description="The client brief description")
    scope: Optional[Any] = Field(None, description="JSON object containing scope advisor breakdown and pricing analysis")
    deliverables: Optional[List[str]] = Field(None, description="Project deliverables checklist")
    value_inr: Optional[int] = Field(None, description="Total project contract value in INR")
    deadline: Optional[str] = Field(None, description="Date in YYYY-MM-DD format")

class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    client_id: Optional[str] = None
    status: Optional[str] = None
    brief_text: Optional[str] = None
    scope: Optional[Any] = None
    deliverables: Optional[List[str]] = None
    value_inr: Optional[int] = None
    deadline: Optional[str] = None
