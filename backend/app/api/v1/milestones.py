import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.core.database import supabase
from app.core.security import get_current_user
from app.models.milestone import MilestoneCreate, MilestoneUpdate

router = APIRouter(prefix="/milestones", tags=["milestones"])

@router.get("/")
async def list_milestones(
    project_id: str = Query(..., description="Filter milestones by project UUID"),
    current_user: dict = Depends(get_current_user)
):
    """
    Lists all milestones for a project, enforcing project ownership checks.
    """
    user_id = current_user["id"]
    try:
        # Check project ownership first
        proj = supabase.table("projects").select("id").eq("id", project_id).eq("user_id", user_id).execute()
        if not proj.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied"
            )

        res = supabase.table("milestones")\
            .select("*")\
            .eq("project_id", project_id)\
            .eq("user_id", user_id)\
            .order("created_at", desc=False)\
            .execute()
        return res.data
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query failed: {str(e)}"
        )

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_milestone(
    milestone_data: MilestoneCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Creates a new milestone for a project. Verifies project ownership.
    """
    user_id = current_user["id"]
    try:
        # Verify project ownership
        proj = supabase.table("projects").select("id").eq("id", milestone_data.project_id).eq("user_id", user_id).execute()
        if not proj.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent project not found or access denied"
            )

        payload = milestone_data.model_dump()
        payload["user_id"] = user_id
        res = supabase.table("milestones").insert(payload).execute()
        if not res.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to insert milestone record into database."
            )
        return res.data[0]
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create milestone: {str(e)}"
        )

@router.patch("/{milestone_id}")
async def update_milestone(
    milestone_id: str,
    milestone_data: MilestoneUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Updates milestone details. Verifies ownership.
    """
    user_id = current_user["id"]
    update_payload = {k: v for k, v in milestone_data.model_dump().items() if v is not None}
    
    try:
        # Verify milestone ownership
        check = supabase.table("milestones").select("id").eq("id", milestone_id).eq("user_id", user_id).execute()
        if not check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Milestone not found"
            )

        res = supabase.table("milestones").update(update_payload).eq("id", milestone_id).eq("user_id", user_id).execute()
        return res.data[0]
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update milestone: {str(e)}"
        )

@router.delete("/{milestone_id}")
async def delete_milestone(
    milestone_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Deletes a milestone. Verifies ownership.
    """
    user_id = current_user["id"]
    try:
        # Verify milestone ownership
        check = supabase.table("milestones").select("id").eq("id", milestone_id).eq("user_id", user_id).execute()
        if not check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Milestone not found"
            )

        supabase.table("milestones").delete().eq("id", milestone_id).eq("user_id", user_id).execute()
        return {"status": "success", "message": "Milestone deleted"}
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete milestone: {str(e)}"
        )

@router.patch("/{milestone_id}/complete")
async def complete_milestone(
    milestone_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Completes a milestone: sets status to complete, sets completed_at timestamp,
    and fires the background Celery invoice creation task.
    """
    user_id = current_user["id"]
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    try:
        # Verify ownership
        check = supabase.table("milestones").select("id").eq("id", milestone_id).eq("user_id", user_id).execute()
        if not check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Milestone not found"
            )

        # Update milestones record
        res = supabase.table("milestones").update({
            "status": "complete",
            "completed_at": now_iso
        }).eq("id", milestone_id).eq("user_id", user_id).execute()
        
        updated_milestone = res.data[0]

        # Trigger background Celery job for automatic invoice drafting
        try:
            from app.tasks.invoices import invoice_on_milestone_complete
            invoice_on_milestone_complete.delay(milestone_id, user_id)
        except ImportError:
            # Fallback output for logging during local development
            print(f"[Placeholder] Delaying invoice creation task for milestone: {milestone_id}")

        return updated_milestone
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to complete milestone: {str(e)}"
        )
