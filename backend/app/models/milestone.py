from pydantic import BaseModel, Field
from typing import Optional

class MilestoneCreate(BaseModel):
    project_id: str = Field(..., description="Associated project UUID")
    title: str = Field(..., min_length=1, description="Milestone title")
    description: Optional[str] = Field(None, description="Detailed description")
    amount_inr: int = Field(..., gt=0, description="Amount in INR")
    due_date: Optional[str] = Field(None, description="Due date in YYYY-MM-DD format")

class MilestoneUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    amount_inr: Optional[int] = Field(None, gt=0)
    due_date: Optional[str] = None
    status: Optional[str] = Field(None, description="pending or complete")
