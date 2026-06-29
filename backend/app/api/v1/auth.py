from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from app.core.database import supabase
from app.core.security import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    upi_id: Optional[str] = None
    gst_number: Optional[str] = None
    bank_details: Optional[str] = None

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Returns the current authenticated user's profile details from public.users.
    """
    return current_user

@router.patch("/profile")
async def update_profile(
    profile_data: ProfileUpdate, 
    current_user: dict = Depends(get_current_user)
):
    """
    Updates the current user's profile and marks them as onboarded.
    """
    update_fields = {}
    if profile_data.name is not None:
        update_fields["name"] = profile_data.name
    if profile_data.upi_id is not None:
        update_fields["upi_id"] = profile_data.upi_id
    if profile_data.gst_number is not None:
        update_fields["gst_number"] = profile_data.gst_number
    if profile_data.bank_details is not None:
        update_fields["bank_details"] = profile_data.bank_details
        
    # Mark onboarded as True upon editing profile (part of onboarding flow)
    update_fields["onboarded"] = True
    
    try:
        res = supabase.table("users").update(update_fields).eq("id", current_user["id"]).execute()
        if not res.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile record in database."
            )
        return res.data[0]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update profile: {str(e)}"
        )
