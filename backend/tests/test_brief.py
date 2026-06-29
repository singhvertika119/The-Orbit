from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
from app.core.security import get_current_user
from app.agents.brief_parser import BriefParserOutput
from app.agents.scope_advisor import ScopeAdvisorOutput

client = TestClient(app)

# Mock user credentials for dependency injection
async def mock_get_current_user():
    return {"id": "8bbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb", "email": "test@gig.ai"}

# Register dependency override for testing
app.dependency_overrides[get_current_user] = mock_get_current_user

def test_parse_brief_input_validation():
    """
    Ensure the brief parser rejects text inputs under 50 characters with a 422 error.
    """
    short_brief = "Short client brief."
    res = client.post("/api/v1/brief/parse", json={"brief_text": short_brief})
    assert res.status_code == 422
    assert "brief_text" in res.text

@patch("app.api.v1.brief.parse_brief")
def test_parse_brief_success(mock_parse):
    """
    Ensure the parsing endpoint completes successfully when provided valid inputs.
    """
    mock_output = BriefParserOutput(
        project_type="Web App",
        deliverables=["User Authentication", "Dashboard View", "Database setup"],
        timeline_signals="Approx 4 weeks",
        budget_signals="Under 50,000 INR",
        ambiguities=["No mention of cloud provider or hosting preference."],
        clarifying_questions=["Do you have a preferred hosting provider (e.g. AWS, Vercel)?"]
    )
    mock_parse.return_value = mock_output

    valid_brief = (
        "Client wants a responsive full-stack website with dashboard, "
        "authentication, database setup, and analytics. Timeline is around a month."
    )
    assert len(valid_brief) >= 50

    res = client.post("/api/v1/brief/parse", json={"brief_text": valid_brief})
    assert res.status_code == 200
    data = res.json()
    assert data["project_type"] == "Web App"
    assert "Dashboard View" in data["deliverables"]
    assert data["budget_signals"] == "Under 50,000 INR"

@patch("app.api.v1.brief.advise_scope")
def test_scope_brief_success(mock_advise):
    """
    Ensure the scope advisor returns the correct estimated parameters.
    """
    mock_output = ScopeAdvisorOutput(
        scope_breakdown=["Phase 1: DB design", "Phase 2: Auth", "Phase 3: Dashboard API"],
        timeline_days=28,
        price_inr=45000,
        price_rationale="Based on full-stack app requirements and database complexity.",
        risk_flags=["Scope creep on dashboard filters"]
    )
    mock_advise.return_value = mock_output

    payload = {
        "brief_summary": "Full-stack analytics app with user dashboard.",
        "deliverables": ["User Authentication", "Dashboard View", "Database setup"],
        "project_type": "Web App"
    }

    res = client.post("/api/v1/brief/scope", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["timeline_days"] == 28
    assert data["price_inr"] == 45000
    assert "Phase 2: Auth" in data["scope_breakdown"]
