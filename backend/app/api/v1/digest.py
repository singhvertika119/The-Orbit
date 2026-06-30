import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.core.database import supabase
from app.core.security import get_current_user
from app.agents.digest_writer import write_digest

from app.api.v1.brief import run_agent_with_backoff, log_agent_error

router = APIRouter(prefix="/digest", tags=["digest"])

@router.get("/today")
async def get_today_digest(
    refresh: bool = Query(False, description="Force regenerates a fresh digest run instead of loading cache"),
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieves the daily morning briefing for the freelancer.
    Checks the digest cache first, and runs the digest-writer agent
    on cache miss or forced refresh.
    """
    user_id = current_user["id"]
    user_name = current_user.get("name") or "Freelancer"

    # 1. Attempt to load from cache
    if not refresh:
        try:
            cached_res = supabase.table("digest_cache").select("content").eq("user_id", user_id).execute()
            if cached_res.data:
                return {
                    "digest_text": cached_res.data[0]["content"],
                    "cached": True
                }
        except Exception as cache_err:
            print(f"Digest cache query failed: {str(cache_err)}")

    # 2. Cache miss or forced refresh: Aggregate dashboard metrics
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    five_days_ago_str = (datetime.date.today() - datetime.timedelta(days=5)).strftime("%Y-%m-%d")

    try:
        # A. Count active projects
        active_projects = supabase.table("projects").select("id", count="exact").eq("user_id", user_id).eq("status", "active").execute()
        active_count = active_projects.count or 0

        # B. Query milestones due today
        due_today = supabase.table("milestones").select("title").eq("user_id", user_id).eq("status", "pending").eq("due_date", today_str).execute()
        due_today_list = [m["title"] for m in due_today.data] if due_today.data else []

        # C. Query overdue milestones
        overdue_mils = supabase.table("milestones").select("title, due_date").eq("user_id", user_id).eq("status", "pending").lt("due_date", today_str).execute()
        overdue_mil_list = [f"{m['title']} (due {m['due_date']})" for m in overdue_mils.data] if overdue_mils.data else []

        # D. Query overdue invoices
        overdue_invs = supabase.table("invoices").select("client_name, project_title, total_inr, due_date").eq("user_id", user_id).in_("payment_status", ["sent", "overdue"]).lt("due_date", today_str).execute()
        overdue_invoice_list = []
        if overdue_invs.data:
            for inv in overdue_invs.data:
                try:
                    due_date = datetime.datetime.strptime(inv["due_date"], "%Y-%m-%d").date()
                    days_over = (datetime.date.today() - due_date).days
                except Exception:
                    days_over = 1
                
                overdue_invoice_list.append({
                    "client_name": inv.get("client_name") or "Client",
                    "project_title": inv.get("project_title") or "Project",
                    "total_inr": int(float(inv.get("total_inr") or 0)),
                    "days_overdue": days_over
                })

        # E. Count pending proposals
        pending_props = supabase.table("projects").select("id", count="exact").eq("user_id", user_id).eq("status", "scoping").execute()
        pending_props_count = pending_props.count or 0

        # F. Find inactive projects (updated_at older than 5 days)
        inactive_projects = supabase.table("projects").select("title").eq("user_id", user_id).eq("status", "active").lt("updated_at", five_days_ago_str).execute()
        inactive_list = [p["title"] for p in inactive_projects.data] if inactive_projects.data else []

    except Exception as db_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database aggregation failed: {str(db_err)}"
        )

    # 3. Call digest-writer agent with backoff retries
    try:
        digest_output = run_agent_with_backoff(
            write_digest,
            user_name=user_name,
            active_projects_count=active_count,
            milestones_due_today=due_today_list,
            overdue_milestones=overdue_mil_list,
            overdue_invoices=overdue_invoice_list,
            pending_proposals_count=pending_props_count,
            inactive_projects=inactive_list
        )
        digest_text = digest_output.digest_text
    except Exception as agent_err:
        error_msg = str(agent_err)
        input_desc = f"Active Projects: {active_count} | Overdue Milestones: {len(overdue_mil_list)}"
        
        # Log failure to error logs table
        log_agent_error(
            user_id=user_id,
            agent_name="digest-writer",
            endpoint="/api/v1/digest/today",
            error_message=error_msg,
            input_snapshot=input_desc
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent is taking longer than expected. We'll retry automatically. Error: {error_msg}"
        )

    # 4. Upsert generated content to the database cache table
    try:
        supabase.table("digest_cache").upsert({
            "user_id": user_id,
            "content": digest_text
        }).execute()
    except Exception as cache_err:
        print(f"Failed to cache digest: {str(cache_err)}")

    return {
        "digest_text": digest_text,
        "cached": False
    }
