import time
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.core.limiter import limiter
from app.core.database import supabase
from app.core.security import get_current_user
from app.models.brief import BriefParseRequest, BriefScopeRequest, BriefProposalRequest
from app.agents.brief_parser import parse_brief, BriefParserOutput
from app.agents.scope_advisor import advise_scope, ScopeAdvisorOutput
from app.agents.proposal_drafter import draft_proposal, ProposalDrafterOutput

router = APIRouter(prefix="/brief", tags=["brief"])

def log_agent_error(user_id: str, agent_name: str, endpoint: str, error_message: str, input_snapshot: str):
    """
    Utility function to log agent execution errors to Supabase.
    """
    try:
        supabase.table("error_logs").insert({
            "user_id": user_id,
            "agent_name": agent_name,
            "endpoint": endpoint,
            "error_message": error_message,
            "input_snapshot": input_snapshot[:500]
        }).execute()
    except Exception as log_err:
        # Prevent logging errors from bubbling up and hiding the primary issue
        print(f"Error logging failed: {str(log_err)}")

def run_agent_with_backoff(agent_func, *args, max_retries: int = 3, initial_delay: float = 2.0, **kwargs):
    """
    Helper to execute an agent call with up to 3 automatic retries and exponential backoff.
    Binds a fresh, non-running event loop to the current worker thread to avoid Uvicorn loop conflicts.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    last_exception = None
    try:
        for attempt in range(max_retries):
            try:
                return agent_func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    # Exponential backoff: 2s -> 4s -> 8s
                    sleep_time = initial_delay * (2 ** attempt)
                    time.sleep(sleep_time)
        raise last_exception
    finally:
        loop.close()

@router.post("/parse", response_model=BriefParserOutput)
@limiter.limit("60/minute")
def api_parse_brief(
    request: Request,
    brief_data: BriefParseRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Parses a raw text client brief and extracts structured parameters.
    """
    try:
        # Run agent task with exponential backoff
        parsed_result = run_agent_with_backoff(parse_brief, brief_data.brief_text)
        return parsed_result
    except Exception as e:
        error_msg = str(e)
        # Log failure to error_logs table
        log_agent_error(
            user_id=current_user["id"],
            agent_name="brief-parser",
            endpoint="/api/v1/brief/parse",
            error_message=error_msg,
            input_snapshot=brief_data.brief_text
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent is taking longer than expected. We'll retry automatically. Error: {error_msg}"
        )

@router.post("/scope", response_model=ScopeAdvisorOutput)
@limiter.limit("60/minute")
def api_scope_brief(
    request: Request,
    scope_data: BriefScopeRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Suggests scope breakdowns, timelines, pricing, and risk flags for the brief.
    Injects context from the user's past completed projects (RAG-lite).
    """
    user_id = current_user["id"]
    past_projects_context = "No completed past projects found for this freelancer."

    # RAG-lite: Query last 5 completed projects from this user
    try:
        projects_query = supabase.table("projects")\
            .select("title, value_inr, scope, deadline")\
            .eq("user_id", user_id)\
            .eq("status", "complete")\
            .limit(5)\
            .execute()
        
        if projects_query.data:
            formatted_projects = []
            for proj in projects_query.data:
                title = proj.get("title", "N/A")
                value = proj.get("value_inr", "N/A")
                deadline = proj.get("deadline", "N/A")
                scope_data_dict = proj.get("scope") or {}
                scope_tasks = ", ".join(scope_data_dict.get("scope_breakdown", [])) if isinstance(scope_data_dict, dict) else "N/A"
                
                formatted_projects.append(
                    f"- Project Name: {title}\n"
                    f"  Suggested Price: {value} INR\n"
                    f"  Timeline Completed: {deadline}\n"
                    f"  Tasks Breakdowns: {scope_tasks}"
                )
            past_projects_context = "\n\n".join(formatted_projects)
    except Exception as db_err:
        # If DB query fails, continue without history context
        print(f"RAG-lite past project context search failed: {str(db_err)}")

    try:
        # Run agent task with exponential backoff
        scoped_result = run_agent_with_backoff(
            advise_scope,
            brief_summary=scope_data.brief_summary,
            deliverables=scope_data.deliverables,
            project_type=scope_data.project_type,
            past_projects_context=past_projects_context
        )
        return scoped_result
    except Exception as e:
        error_msg = str(e)
        input_desc = f"Type: {scope_data.project_type} | Summary: {scope_data.brief_summary}"
        # Log failure to error_logs table
        log_agent_error(
            user_id=user_id,
            agent_name="scope-advisor",
            endpoint="/api/v1/brief/scope",
            error_message=error_msg,
            input_snapshot=input_desc
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent is taking longer than expected. We'll retry automatically. Error: {error_msg}"
        )

@router.post("/proposal", response_model=ProposalDrafterOutput)
@limiter.limit("60/minute")
def api_proposal_brief(
    request: Request,
    proposal_data: BriefProposalRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Drafts a client-ready proposal with a subject line and body copy.
    """
    user_id = current_user["id"]
    user_name = current_user.get("name") or "Freelancer"
    user_upi = current_user.get("upi_id") or ""

    try:
        # Run agent task with exponential backoff
        proposal_result = run_agent_with_backoff(
            draft_proposal,
            project_title=proposal_data.project_title,
            client_name=proposal_data.client_name,
            scope_breakdown=proposal_data.scope_breakdown,
            timeline_days=proposal_data.timeline_days,
            price_inr=proposal_data.price_inr,
            deliverables=proposal_data.deliverables,
            user_name=user_name,
            user_upi=user_upi
        )
        return proposal_result
    except Exception as e:
        error_msg = str(e)
        input_desc = f"Title: {proposal_data.project_title} | Client: {proposal_data.client_name}"
        # Log failure to error_logs table
        log_agent_error(
            user_id=user_id,
            agent_name="proposal-drafter",
            endpoint="/api/v1/brief/proposal",
            error_message=error_msg,
            input_snapshot=input_desc
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent is taking longer than expected. We'll retry automatically. Error: {error_msg}"
        )

