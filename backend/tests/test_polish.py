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

@patch("app.api.v1.invoices.supabase")
def test_get_invoice_pdf_cache_hit(mock_db):
    """
    Tests that the PDF route returns the cached signed URL directly from Supabase Storage.
    """
    mock_invoice_res = MagicMock(data=[{
        "id": "inv-123",
        "invoice_number": "GIG-2026-VS-001",
        "amount_inr": 20000,
        "gst_amount": 3600,
        "total_inr": 23600,
        "milestone_title": "Milestone A",
        "project_title": "Project A",
        "client_name": "Client A",
        "client_email": "client@example.com",
        "due_date": "2026-07-15",
        "created_at": "2026-07-01T00:00:00Z"
    }])
    mock_db.table().select().eq().eq().execute.return_value = mock_invoice_res

    # Mock storage client cache hit
    mock_db.storage.from_().create_signed_url.return_value = {
        "signedURL": "https://supabase.com/storage/v1/object/sign/invoices/inv-123.pdf?token=abc"
    }

    res = client.get("/api/v1/invoices/inv-123/pdf")
    assert res.status_code == 200
    data = res.json()
    assert data["pdf_url"] == "https://supabase.com/storage/v1/object/sign/invoices/inv-123.pdf?token=abc"
    assert data["cached"] is True

@patch("app.api.v1.invoices.supabase")
def test_get_invoice_pdf_cache_miss_and_generate(mock_db):
    """
    Tests that if the PDF is not cached, the endpoint compiles a new PDF via WeasyPrint,
    uploads it to Supabase Storage, and returns a fresh signed URL.
    """
    mock_invoice_res = MagicMock(data=[{
        "id": "inv-123",
        "invoice_number": "GIG-2026-VS-001",
        "amount_inr": 20000,
        "gst_amount": 3600,
        "total_inr": 23600,
        "milestone_title": "Milestone A",
        "project_title": "Project A",
        "client_name": "Client A",
        "client_email": "client@example.com",
        "due_date": "2026-07-15",
        "created_at": "2026-07-01T00:00:00Z"
    }])
    # Mock selects: select invoice, then select user profile
    mock_db.table().select().eq().eq().execute.return_value = mock_invoice_res
    mock_db.table().select().eq().execute.return_value = MagicMock(data=[{
        "id": "8bbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb",
        "name": "Vertika Singh",
        "email": "test@gig.ai",
        "upi_id": "vertika@upi"
    }])

    # Configure storage behavior directly on mock_db
    mock_bucket = MagicMock()
    mock_bucket.create_signed_url.side_effect = [
        Exception("Cache miss"), # cache check
        {"signedURL": "https://supabase.com/storage/v1/object/sign/invoices/inv-123.pdf?token=new"} # after upload
    ]
    mock_bucket.upload.return_value = {"path": "inv-123.pdf"}
    mock_db.storage.from_.return_value = mock_bucket

    res = client.get("/api/v1/invoices/inv-123/pdf")
    assert res.status_code == 200
    data = res.json()
    assert data["pdf_url"] == "https://supabase.com/storage/v1/object/sign/invoices/inv-123.pdf?token=new"
    assert data["cached"] is False
    # Ensure PDF upload was called
    mock_bucket.upload.assert_called_once()

def test_rate_limiting_registration():
    """
    Verifies that SlowAPI rate limiting state is correctly configured on the FastAPI app.
    """
    from slowapi.errors import RateLimitExceeded
    assert hasattr(app.state, "limiter")
    # Verify rate limit exceeded handler is mapped
    assert RateLimitExceeded in app.exception_handlers

