from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.core.security import get_current_user

client = TestClient(app)

# Override JWT authentication for testing
async def mock_get_current_user():
    return {
        "id": "8bbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb",
        "email": "test@gig.ai",
        "name": "Vertika Singh"
    }

app.dependency_overrides[get_current_user] = mock_get_current_user

# ==================== CLIENTS CRUD TESTS ====================

@patch("app.api.v1.clients.supabase")
def test_list_clients_success(mock_db):
    """
    Test listing clients. Returns list of clients for the authenticated user.
    """
    mock_response = MagicMock()
    mock_response.data = [
        {"id": "client-1", "name": "Client A", "user_id": "8bbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb"},
        {"id": "client-2", "name": "Client B", "user_id": "8bbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb"}
    ]
    mock_db.table().select().eq().order().execute.return_value = mock_response

    res = client.get("/api/v1/clients")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    assert data[0]["name"] == "Client A"

@patch("app.api.v1.clients.supabase")
def test_create_client_success(mock_db):
    """
    Test registering a new client.
    """
    mock_response = MagicMock()
    mock_response.data = [{"id": "client-3", "name": "New Client", "email": "new@example.com"}]
    mock_db.table().insert().execute.return_value = mock_response

    payload = {"name": "New Client", "email": "new@example.com"}
    res = client.post("/api/v1/clients/", json=payload)
    assert res.status_code == 201
    assert res.json()["name"] == "New Client"

@patch("app.api.v1.clients.supabase")
def test_get_client_ownership_ok(mock_db):
    """
    Test fetching a client ID owned by the user.
    """
    mock_response = MagicMock()
    mock_response.data = [{"id": "client-1", "name": "Client A", "user_id": "8bbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb"}]
    mock_db.table().select().eq().eq().execute.return_value = mock_response

    res = client.get("/api/v1/clients/client-1")
    assert res.status_code == 200
    assert res.json()["name"] == "Client A"

@patch("app.api.v1.clients.supabase")
def test_get_client_ownership_fail(mock_db):
    """
    Test fetching a client ID not owned by the user. Returns 404.
    """
    mock_response = MagicMock()
    mock_response.data = []  # Not found under user context
    mock_db.table().select().eq().eq().execute.return_value = mock_response

    res = client.get("/api/v1/clients/client-not-owned")
    assert res.status_code == 404
    assert res.json()["detail"] == "Client not found"


# ==================== PROJECTS CRUD TESTS ====================

@patch("app.api.v1.projects.supabase")
def test_list_projects_success(mock_db):
    """
    Test listing projects with linked client details.
    """
    mock_response = MagicMock()
    mock_response.data = [
        {"id": "proj-1", "title": "Tutoring App", "clients": {"name": "Priya", "email": "priya@example.com"}}
    ]
    mock_db.table().select().eq().order().execute.return_value = mock_response

    res = client.get("/api/v1/projects")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["title"] == "Tutoring App"
    assert data[0]["clients"]["name"] == "Priya"


# ==================== MILESTONES CRUD TESTS ====================

@patch("app.api.v1.milestones.supabase")
def test_list_milestones_success(mock_db):
    """
    Test listing milestones. Verifies parent project ownership.
    """
    mock_proj_res = MagicMock(data=[{"id": "proj-1"}])
    mock_mil_res = MagicMock(data=[
        {"id": "mil-1", "title": "Database Design", "status": "pending"}
    ])
    # Database calls sequence: project check, then milestones select with order()
    mock_chain = mock_db.table().select().eq().eq()
    mock_chain.order.return_value = mock_chain
    mock_chain.execute.side_effect = [mock_proj_res, mock_mil_res]


    res = client.get("/api/v1/milestones?project_id=proj-1")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["title"] == "Database Design"

@patch("app.api.v1.milestones.supabase")
def test_complete_milestone_success(mock_db):
    """
    Test milestone complete PATCH endpoint. Marks milestone as complete
    and sets completed_at timestamp.
    """
    mock_check_res = MagicMock(data=[{"id": "mil-1"}])
    mock_update_res = MagicMock(data=[{
        "id": "mil-1",
        "title": "Database Design",
        "status": "complete",
        "completed_at": "2026-06-30T19:00:00Z"
    }])
    # Database calls sequence: check ownership, then update
    mock_db.table().select().eq().eq().execute.return_value = mock_check_res
    mock_db.table().update().eq().eq().execute.return_value = mock_update_res

    res = client.patch("/api/v1/milestones/mil-1/complete")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "complete"
    assert data["completed_at"] == "2026-06-30T19:00:00Z"


# ==================== INVOICES CRUD TESTS ====================

@patch("app.api.v1.invoices.supabase")
def test_mark_invoice_as_paid_success(mock_db):
    """
    Test marking an invoice as paid. Updates payment status and paid_at.
    """
    mock_check_res = MagicMock(data=[{"id": "inv-1"}])
    mock_update_res = MagicMock(data=[{
        "id": "inv-1",
        "payment_status": "paid",
        "paid_at": "2026-06-30T19:00:00Z"
    }])
    mock_db.table().select().eq().eq().execute.return_value = mock_check_res
    mock_db.table().update().eq().eq().execute.return_value = mock_update_res

    res = client.patch("/api/v1/invoices/inv-1/paid")
    assert res.status_code == 200
    data = res.json()
    assert data["payment_status"] == "paid"
    assert data["paid_at"] == "2026-06-30T19:00:00Z"
