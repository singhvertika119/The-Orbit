from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.core.security import get_current_user
from app.agents.proposal_drafter import ProposalDrafterOutput
from app.agents.followup_writer import FollowupWriterOutput
from app.agents.digest_writer import DigestWriterOutput

client = TestClient(app)

# Override JWT authentication for testing
async def mock_get_current_user():
    return {
        "id": "8bbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb",
        "email": "test@gig.ai",
        "name": "Vertika Singh",
        "upi_id": "vertika@upi"
    }

app.dependency_overrides[get_current_user] = mock_get_current_user

@patch("app.api.v1.brief.draft_proposal")
def test_proposal_brief_success(mock_draft):
    """
    Test proposal generation with valid details.
    """
    mock_draft.return_value = ProposalDrafterOutput(
        subject_line="Project Proposal — Tutoring booking dashboard",
        proposal_text="Problem restatement...\nApproach...\nInvestment..."
    )

    payload = {
        "project_title": "Tutoring booking dashboard",
        "client_name": "Priya Sharma",
        "scope_breakdown": ["Database Design", "Auth", "Calendar Integration"],
        "timeline_days": 21,
        "price_inr": 35000,
        "deliverables": ["Design Layout", "Frontend dashboard", "API integration"]
    }

    res = client.post("/api/v1/brief/proposal", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["subject_line"] == "Project Proposal — Tutoring booking dashboard"
    assert "Problem restatement" in data["proposal_text"]

@patch("app.api.v1.invoices.supabase")
@patch("app.api.v1.invoices.write_followup")
def test_trigger_manual_followup_success(mock_write, mock_db):
    """
    Test manual follow-up reminder endpoint.
    Retrieves the invoice from the database, computes the overdue duration,
    and runs the follow-up agent.
    """
    # Mock database responses
    mock_response = MagicMock()
    mock_response.data = [{
        "id": "d8888888-8888-8888-8888-888888888888",
        "client_name": "Rahul Sharma",
        "project_title": "Clothing Business Dashboard",
        "milestone_title": "Project Kickoff",
        "total_inr": 35400,
        "due_date": "2026-06-25",  # Overdue
        "user_id": "8bbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb"
    }]
    mock_db.table().select().eq().eq().execute.return_value = mock_response

    mock_write.return_value = FollowupWriterOutput(
        subject_line="Payment Reminder: Project Kickoff invoice",
        message_body="Hi Rahul, hope you are well. Just following up..."
    )

    res = client.post("/api/v1/invoices/d8888888-8888-8888-8888-888888888888/followup")
    assert res.status_code == 200
    data = res.json()
    assert data["subject_line"] == "Payment Reminder: Project Kickoff invoice"
    assert "Hi Rahul" in data["message_body"]

@patch("app.api.v1.digest.supabase")
def test_get_today_digest_cache_hit(mock_db):
    """
    Test that the digest route retrieves the cached morning briefing if it exists.
    """
    mock_response = MagicMock()
    mock_response.data = [{
        "content": "Good morning, Vertika. Here is your daily cached update."
    }]
    mock_db.table().select().eq().execute.return_value = mock_response

    res = client.get("/api/v1/digest/today")
    assert res.status_code == 200
    data = res.json()
    assert data["digest_text"] == "Good morning, Vertika. Here is your daily cached update."
    assert data["cached"] is True

@patch("app.api.v1.digest.supabase")
@patch("app.api.v1.digest.write_digest")
def test_get_today_digest_cache_miss(mock_write, mock_db):
    """
    Test that a cache miss (or force refresh) aggregates workspace stats
    and generates a new digest via the digest-writer agent.
    """
    mock_cache_res = MagicMock()
    mock_cache_res.data = []  # Cache is empty

    mock_project_res = MagicMock()
    mock_project_res.count = 2  # Active projects

    mock_milestones_res = MagicMock()
    mock_milestones_res.data = [{"title": "Complete Design"}]  # Due today

    mock_overdue_milestones_res = MagicMock()
    mock_overdue_milestones_res.data = []

    mock_invoices_res = MagicMock()
    mock_invoices_res.data = []

    mock_proposals_res = MagicMock()
    mock_proposals_res.count = 1

    mock_inactive_res = MagicMock()
    mock_inactive_res.data = []

    # Mock sequence of database queries executed by the route
    mock_db.table().select().eq().execute.side_effect = [
        mock_cache_res,             # Cache check
        mock_project_res,           # Active projects count
        mock_milestones_res,         # Milestones due today
        mock_overdue_milestones_res, # Overdue milestones
        mock_invoices_res,           # Overdue invoices
        mock_proposals_res,          # Pending proposals
        mock_inactive_res,           # Inactive projects list
        MagicMock()                 # Cache upsert stub
    ]

    mock_write.return_value = DigestWriterOutput(
        digest_text="Good morning, Vertika. Here is your newly generated workspace digest."
    )

    # Force a refresh to simulate cache miss
    res = client.get("/api/v1/digest/today?refresh=true")
    assert res.status_code == 200
    data = res.json()
    assert data["digest_text"] == "Good morning, Vertika. Here is your newly generated workspace digest."
    assert data["cached"] is False
