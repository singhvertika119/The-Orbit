import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import supabase
from app.core.security import get_current_user
from app.agents.followup_writer import write_followup, FollowupWriterOutput
from app.api.v1.brief import run_agent_with_backoff, log_agent_error

router = APIRouter(prefix="/invoices", tags=["invoices"])

@router.get("/")
async def list_invoices(current_user: dict = Depends(get_current_user)):
    """
    Lists all invoices belonging to the authenticated user.
    """
    user_id = current_user["id"]
    try:
        res = supabase.table("invoices")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .execute()
        return res.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query failed: {str(e)}"
        )

@router.get("/{invoice_id}")
async def get_invoice(
    invoice_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Fetches details for a single invoice. Verifies user ownership.
    """
    user_id = current_user["id"]
    try:
        res = supabase.table("invoices")\
            .select("*")\
            .eq("id", invoice_id)\
            .eq("user_id", user_id)\
            .execute()
        if not res.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        return res.data[0]
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query failed: {str(e)}"
        )

@router.patch("/{invoice_id}/paid")
async def mark_invoice_as_paid(
    invoice_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Marks an invoice as paid. Sets the paid_at timestamp to now.
    Verifies user ownership.
    """
    user_id = current_user["id"]
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    try:
        # Check ownership first
        check = supabase.table("invoices").select("id").eq("id", invoice_id).eq("user_id", user_id).execute()
        if not check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
            
        res = supabase.table("invoices").update({
            "payment_status": "paid",
            "paid_at": now_iso
        }).eq("id", invoice_id).eq("user_id", user_id).execute()
        
        return res.data[0]
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update invoice: {str(e)}"
        )

@router.post("/{invoice_id}/followup", response_model=FollowupWriterOutput)
async def trigger_manual_followup(
    invoice_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Manually triggers the followup-writer agent to draft a reminder
    for a specific invoice. Verifies owner tenancy before execution.
    """
    user_id = current_user["id"]
    
    # 1. Retrieve invoice details
    try:
        res = supabase.table("invoices").select("*").eq("id", invoice_id).eq("user_id", user_id).execute()
        if not res.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found or access denied"
            )
        invoice = res.data[0]
    except HTTPException as http_err:
        raise http_err
    except Exception as db_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch invoice details: {str(db_err)}"
        )

    # 2. Extract context values
    client_name = invoice.get("client_name") or "Client"
    project_title = invoice.get("project_title") or "Project"
    milestone_title = invoice.get("milestone_title") or "Milestone"
    total_amount = int(float(invoice.get("total_inr") or 0))
    
    # Calculate days overdue based on invoice due date
    due_date_str = invoice.get("due_date")
    if not due_date_str:
        days_overdue = 1
    else:
        try:
            # Parse due date (standard YYYY-MM-DD DATE format)
            due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d").date()
            today = datetime.date.today()
            days_overdue = (today - due_date).days
        except Exception:
            days_overdue = 1

    # 3. Execute agent task with exponential backoff
    try:
        followup_draft = run_agent_with_backoff(
            write_followup,
            client_name=client_name,
            project_title=project_title,
            total_amount=total_amount,
            days_overdue=days_overdue,
            milestone_title=milestone_title
        )
        return followup_draft
    except Exception as e:
        error_msg = str(e)
        input_desc = f"Invoice ID: {invoice_id} | Days Overdue: {days_overdue}"
        
        # Log failure to error logs table
        log_agent_error(
            user_id=user_id,
            agent_name="followup-writer",
            endpoint=f"/api/v1/invoices/{invoice_id}/followup",
            error_message=error_msg,
            input_snapshot=input_desc
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent is taking longer than expected. We'll retry automatically. Error: {error_msg}"
        )
